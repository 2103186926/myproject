import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from datetime import datetime

# ==========================================
# 配置参数
# ==========================================
INPUT_FILE = r'C:\Users\21031\Desktop\myProject\侧信道攻击\1.Log ETL\ocean_security_audit.jsonl'
OUTPUT_JSON = 'lstm_feature_data.json'
OUTPUT_CSV = 'lstm_feature_data.csv'

# 定义需要提取的特征维度
# 数值型特征
NUMERIC_FEATURES = ['duration_log10', 'io_log10', 'cpu_usage', 'time_diff_log10']
# 类别型特征 (将会被 One-Hot 编码)
CATEGORICAL_FEATURES = ['phase', 'event_type']

def load_data(filepath):
    """加载 JSONL 数据并转换为 DataFrame"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            # 扁平化处理：提取嵌套字段
            flat_entry = {
                'job_id': entry['metadata']['job_id'],
                'timestamp': entry['timestamp'],
                'label': entry['label'],
                'duration_ns': entry['metrics'].get('duration_ns', 0),
                'io_bytes': entry['metrics'].get('io_bytes', 0),
                'cpu_usage': entry['metrics'].get('cpu_usage_pct', 0),
                'phase': entry['phase'],
                'event_type': entry['event']['type']
            }
            data.append(flat_entry)
    
    df = pd.DataFrame(data)
    # 转换时间戳
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def feature_engineering(df):
    """特征工程核心逻辑"""
    print("[*] 正在进行特征工程处理...")
    
    # 1. 排序：按 Job 和 时间 排序
    df = df.sort_values(by=['job_id', 'timestamp'])
    
    # 2. 计算动态时间特征：距离上一条日志的时间差 (Time Delta)
    # group().diff() 会在每个 Job 内部计算差值
    df['time_diff'] = df.groupby('job_id')['timestamp'].diff().dt.total_seconds().fillna(0)
    
    # 3. 对数变换 (Log Transformation)
    # 原因：侧信道攻击的纳秒级差异(100ns)与正常任务(20ms)跨度太大，
    # 使用 Log10 将其缩放到线性空间，便于 LSTM 收敛
    # 加 1.0 是为了避免 log(0)
    df['duration_log10'] = np.log10(df['duration_ns'] + 1.0)
    df['io_log10'] = np.log10(df['io_bytes'] + 1.0)
    df['time_diff_log10'] = np.log10(df['time_diff'] + 1e-9) # 避免log(0)
    
    # 4. 归一化 CPU 使用率 (0-100 -> 0-1)
    df['cpu_usage'] = df['cpu_usage'] / 100.0
    
    # 5. One-Hot 编码类别特征
    df = pd.get_dummies(df, columns=['phase', 'event_type'], prefix=['ph', 'evt'])
    
    # 获取所有生成的特征列名 (数值 + OneHot)
    feature_cols = NUMERIC_FEATURES + [c for c in df.columns if c.startswith('ph_') or c.startswith('evt_')]
    
    # 填充 NaN (主要是第一条日志的 time_diff)
    df = df.fillna(0)
    
    return df, feature_cols

def create_sequences(df, feature_cols):
    """生成定长序列 (Padding)"""
    print("[*] 正在生成时序序列 (Padding)...")
    
    jobs = df['job_id'].unique()
    sequences = []
    labels = []
    
    # 统计每个 Job 的序列长度
    job_lengths = df.groupby('job_id').size()
    max_seq_len = job_lengths.max()
    print(f"    检测到最大序列长度 (Max Seq Len): {max_seq_len}")
    
    # 准备 CSV 表头
    csv_header = ['job_id', 'label']
    for t in range(max_seq_len):
        for feat in feature_cols:
            csv_header.append(f"t{t}_{feat}")
    
    csv_rows = []
    
    for job in jobs:
        job_df = df[df['job_id'] == job]
        
        # 提取特征矩阵 (seq_len, num_features)
        seq_features = job_df[feature_cols].values
        # 提取标签 (每个 Job 的标签是一致的，取第一个)
        label = job_df['label'].iloc[0]
        
        # Padding: 不足 max_seq_len 的补 0
        current_len = len(seq_features)
        pad_len = max_seq_len - current_len
        
        if pad_len > 0:
            # 在末尾补 0
            padding = np.zeros((pad_len, len(feature_cols)))
            padded_seq = np.vstack([seq_features, padding])
        else:
            padded_seq = seq_features
            
        sequences.append(padded_seq.tolist())
        labels.append(int(label))
        
        # 构建 CSV 行 (Flatten)
        csv_row = [job, label]
        csv_row.extend(padded_seq.flatten().tolist())
        csv_rows.append(csv_row)
        
    return sequences, labels, feature_cols, max_seq_len, csv_header, csv_rows

def main():
    # 1. 加载
    df_raw = load_data(INPUT_FILE)
    print(f"[*] 已加载原始日志: {len(df_raw)} 条, 涉及任务数: {df_raw['job_id'].nunique()}")
    
    # 2. 特征工程
    df_proc, feature_cols = feature_engineering(df_raw)
    print(f"[*] 特征提取完成。特征维度: {len(feature_cols)}")
    print(f"    特征列表: {feature_cols}")
    
    # 3. 序列化
    X, y, feats, max_len, csv_header, csv_rows = create_sequences(df_proc, feature_cols)
    
    # 4. 保存 JSON (LSTM 输入)
    output_data = {
        "meta": {
            "max_seq_len": int(max_len),
            "feature_dim": len(feats),
            "feature_names": feats,
            "generated_at": datetime.now().isoformat()
        },
        "X": X, # [Batch, Time, Feats]
        "y": y  # [Batch]
    }
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output_data, f)
    print(f"[+] LSTM 特征数据已保存至: {OUTPUT_JSON}")
    
    # 5. 保存 CSV (宽表，用于可视化审计)
    csv_df = pd.DataFrame(csv_rows, columns=csv_header)
    csv_df.to_csv(OUTPUT_CSV, index=False)
    print(f"[+] 可视化特征表已保存至: {OUTPUT_CSV}")
    print(f"    CSV 形状: {csv_df.shape} (Rows: Jobs, Cols: TimeSteps * Features)")

if __name__ == "__main__":
    main()