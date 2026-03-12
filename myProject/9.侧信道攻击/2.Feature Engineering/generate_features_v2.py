# generate_features_v2.py
import json
import pandas as pd
import numpy as np
from scipy.stats import entropy
from sklearn.preprocessing import MinMaxScaler

INPUT_FILE = r'C:\Users\21031\Desktop\myProject\侧信道攻击\1.Log ETL\ocean_security_audit_v4.jsonl'
OUTPUT_JSON = 'lstm_feature_data_v2.json'
OUTPUT_CSV = 'lstm_feature_data_v2.csv'

# === 14维特征定义 ===
# 1-8: 数值型动态特征
NUMERIC_COLS = [
    'duration_log10',   # 耗时 (纳秒Log)
    'io_log10',         # IO量 (字节Log)
    'mem_log10',        # [NEW] 内存占用 (字节Log)
    'time_diff_log10',  # 时间间隔 (秒Log)
    'cpu_usage',        # CPU使用率 (0-1)
    'l3_miss_rate',     # [NEW] L3缓存未命中率 (0-1)
    'ipc',              # [NEW] 每周期指令数
    'dur_entropy'       # [NEW] 耗时的滑动窗口熵值
]
# 9-14: 语义型状态特征 (One-Hot)
# 阶段: COMPUTE, ANALYSIS, SYNC, SETUP
# 事件: DATA_PROCESS, POINT_QUERY, WORKER_WAIT, MEM_ALLOC
# (代码中会自动生成)

def calculate_rolling_entropy(series, window=5):
    """计算滑动窗口的熵值，用于检测规律性"""
    # 将数值离散化为 10 个桶，计算分布的熵
    def _ent(x):
        counts = np.histogram(x, bins=10)[0]
        return entropy(counts + 1e-9) # 加微小值防止 log(0)
    
    return series.rolling(window=window, min_periods=1).apply(_ent).fillna(0)

def feature_engineering(df):
    print("[*] Feature Engineering (v2)...")
    
    if 'job_id' not in df.columns and 'metadata' in df.columns:
        df['job_id'] = df['metadata'].apply(
            lambda x: x.get('job_id') if isinstance(x, dict) else None
        )
    
    # 1. 基础排序
    df = df.sort_values(by=['job_id', 'timestamp'])
    
    # 2. 提取原始 Metrics
    # 注意：需处理部分日志可能缺失某些 metrics 的情况 (填充 0)
    metrics_df = df['metrics'].apply(pd.Series).fillna(0)
    df = pd.concat([df.drop(['metrics'], axis=1), metrics_df], axis=1)
    
    # 3. Log 变换
    df['duration_log10'] = np.log10(df['duration_ns'] + 1.0)
    df['io_log10'] = np.log10(df['io_bytes'] + 1.0)
    df['mem_log10'] = np.log10(df['mem_usage_bytes'] + 1.0)
    
    # 4. 时间差特征
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time_diff'] = df.groupby('job_id')['timestamp'].diff().dt.total_seconds().fillna(0)
    df['time_diff_log10'] = np.log10(df['time_diff'] + 1e-9)
    
    # 5. 归一化/直接使用
    df['cpu_usage'] = df['cpu_usage_pct'] / 100.0
    # l3_miss_rate 和 ipc 直接使用原始值
    
    # 6. [NEW] 滑动窗口熵值 (Rolling Entropy)
    # 对每个 Job 内部计算 duration 的熵
    df['dur_entropy'] = df.groupby('job_id')['duration_log10'].transform(
        lambda x: calculate_rolling_entropy(x)
    )
    
    # 7. One-Hot 编码 (Phase & Event)
    # 提取 event.type
    df['event_type'] = df['event'].apply(lambda x: x.get('type', 'UNKNOWN'))
    
    # 选取关键的类别进行编码，防止维度爆炸
    target_phases = ['COMPUTE', 'ANALYSIS', 'SYNC', 'SETUP']
    target_events = ['DATA_PROCESS', 'POINT_QUERY', 'WORKER_WAIT', 'MEM_ALLOC']
    
    # 手动构造 One-Hot 以保证维度固定
    for p in target_phases:
        df[f'ph_{p}'] = (df['phase'] == p).astype(int)
    for e in target_events:
        df[f'evt_{e}'] = (df['event_type'] == e).astype(int)
        
    # 收集所有特征列
    feature_cols = NUMERIC_COLS + [f'ph_{p}' for p in target_phases] + [f'evt_{e}' for e in target_events]
    
    return df, feature_cols

def create_sequences(df, feature_cols):
    """序列化逻辑与 v1 相同，这里省略重复注释"""
    print("[*] Creating Sequences...")
    max_seq_len = df.groupby('job_id').size().max()
    print(f"    Max Seq Len: {max_seq_len}")
    
    sequences = []
    labels = []
    
    # 准备 CSV 表头
    csv_rows = []
    csv_header = ['job_id', 'label'] + [f"t{t}_{f}" for t in range(max_seq_len) for f in feature_cols]
    
    for job_id, group in df.groupby('job_id'):
        label = group['label'].iloc[0]
        feats = group[feature_cols].values
        
        # Padding
        pad_len = max_seq_len - len(feats)
        if pad_len > 0:
            feats = np.vstack([feats, np.zeros((pad_len, len(feature_cols)))])
            
        sequences.append(feats.tolist())
        labels.append(int(label))
        
        # CSV Row
        csv_rows.append([job_id, label] + feats.flatten().tolist())
        
    return sequences, labels, feature_cols, max_seq_len, csv_header, csv_rows

def main():
    # Load Data
    data = []
    with open(INPUT_FILE, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    df = pd.DataFrame(data)
    
    # Feature Engineering
    df_proc, feats = feature_engineering(df)
    print(f"[*] Extracted {len(feats)} features: {feats}")
    
    # Sequencing
    X, y, _, max_len, csv_head, csv_data = create_sequences(df_proc, feats)
    
    # Save JSON
    out_json = {
        "meta": {"features": feats, "max_len": int(max_len)},
        "X": X, "y": y
    }
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(out_json, f)
        
    # Save CSV
    pd.DataFrame(csv_data, columns=csv_head).to_csv(OUTPUT_CSV, index=False)
    print("[+] Done.")

if __name__ == "__main__":
    main()