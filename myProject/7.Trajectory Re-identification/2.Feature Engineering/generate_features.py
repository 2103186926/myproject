'''
将非结构化的 JSON 对象转化为规范的数值型特征向量（Feature Vectors）
这个脚本完成了数据的清洗、提取、编码、填充（Padding）和导出。
'''
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

# 定义特征提取配置
# 事件类型映射 (Label Encoding)
EVENT_MAP = {
    "PAD": 0,             # 填充位
    "JOB_START": 1,
    "DATA_FETCH": 2,
    "PRE_FILTER": 3,      # 攻击任务常见
    "BATCH_PROCESS": 4,   # 正常任务常见
    "DEEP_ANALYSIS": 5,   # 攻击任务常见
    "RESULT_EXPORT": 6
}

# 关键特征维度定义 (对应 LSTM 输入向量的通道)
FEATURE_COLS = [
    "event_type",         # 1. 事件类型
    "duration_ms",        # 2. 耗时
    "cpu_usage",          # 3. CPU利用率
    "io_ratio",           # 4. 输入输出比 (漏斗特征)
    "data_scope_days",    # 5. 查询时间跨度 (意图特征)
    "data_scope_area",    # 6. 查询面积 (意图特征)
    "record_count",       # 7. 处理数据量 (Input)
    "export_size_kb"      # 8. 导出文件大小
]

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_step_features(log):
    """
    将单条 Log 转化为一个特征向量
    """
    # 1. Event Type Encoding
    event_type = EVENT_MAP.get(log.get("event_type", ""), 0)
    
    # 获取 params 和 metrics，处理缺失值
    params = log.get("params", {})
    metrics = log.get("metrics", {})
    
    # 2. Duration (归一化建议在模型前做，这里先保持原值或做简单处理)
    duration = metrics.get("duration_ms", 0)
    
    # 3. CPU Usage
    cpu = metrics.get("cpu_usage_pct", 0)
    
    # 4. I/O Ratio (漏斗效应核心指标)
    # 正常任务通常接近 1.0 (流式) 或 <1.0 (聚合)
    # 攻击任务在 Filter 阶段极低 (e.g. 3/20000 = 0.00015)
    inp = metrics.get("input_records", 0)
    out = metrics.get("output_records", 0)
    if inp > 0:
        io_ratio = out / inp
    else:
        # 如果没有 input 记录 (如 JOB_START)，设为 -1 或 1 表示不相关
        io_ratio = 1.0 
        
    # 5 & 6. Data Scope (查询意图)
    # 通常只在 DATA_FETCH 阶段出现，其他阶段需不需要 Carry Forward?
    # 为了 LSTM 能够记住上下文，这里我们简化处理：仅当前步骤有就填，LSTM 会记忆
    days = params.get("time_span_days", 0)
    area = params.get("area_sqkm", 0)
    
    # 7. Record Count (处理规模)
    # 用于区分是“海量批处理”还是“单条精细分析”
    # deep_analysis 时 input=1
    rec_count = metrics.get("input_records", 0)
    
    # 8. Export Size
    export_size = metrics.get("file_size_kb", 0)
    
    return [
        event_type, 
        duration, 
        cpu, 
        io_ratio, 
        days, 
        area, 
        rec_count, 
        export_size
    ]

def generate_features():
    """
    从 JSON 文件中加载原始日志，提取特征序列并返回 DataFrame
    """
    print("[*] Loading raw logs from ocean_task_logs.json...")
    # 加载 JSON 文件
    filepath = "C:\\Users\\21031\\Desktop\\myProject\\Trajectory Re-identification\\1.Log ETL\\ocean_task_logs.json"
    raw_data = load_data(filepath)
    
    processed_seqs = []
    labels = []
    task_ids = []
    
    # 1. 遍历所有任务，提取特征序列
    max_seq_len = 0
    for task in raw_data:
        label = task['label']
        task_id = task['logs'][0]['task_id']
        logs = task['logs']
        
        # 按时间戳排序 (虽然源数据可能已排好，但保险起见)
        logs.sort(key=lambda x: x['timestamp'])
        
        seq_features = []
        for log in logs:
            feat_vec = extract_step_features(log)
            seq_features.append(feat_vec)
            
        if len(seq_features) > max_seq_len:
            max_seq_len = len(seq_features)
            
        processed_seqs.append(seq_features)
        labels.append(label)
        task_ids.append(task_id)

    print(f"[*] Max sequence length detected: {max_seq_len}")
    
    # 2. Padding (补零对齐) & 3. 生成 CSV 数据
    # LSTM 需要固定长度输入 (Batch Training)
    # CSV 需要扁平化
    
    lstm_ready_data = []
    csv_rows = []
    
    feature_names = FEATURE_COLS
    
    for idx, seq in enumerate(processed_seqs):
        # --- Padding logic ---
        curr_len = len(seq)
        pad_len = max_seq_len - curr_len
        # 创建全 0 向量
        padding = [[0] * len(FEATURE_COLS) for _ in range(pad_len)]
        # 补在后面 (Post-padding)
        padded_seq = seq + padding
        
        lstm_ready_data.append({
            "task_id": task_ids[idx],
            "label": labels[idx],
            "features": padded_seq,  # 3D shape later: (Batch, TimeStep, Feature)
            "seq_len": curr_len      # 记录真实长度，供某些 LSTM 变体使用 Mask
        })
        
        # --- CSV Flattening logic ---
        # Row format: label, task_id, step_0_feat_0, step_0_feat_1 ... step_N_feat_M
        csv_row = {
            "label": labels[idx],
            "task_id": task_ids[idx]
        }
        
        for step_i, step_vec in enumerate(padded_seq):
            for feat_i, val in enumerate(step_vec):
                col_name = f"step_{step_i}_{feature_names[feat_i]}"
                csv_row[col_name] = val
        
        csv_rows.append(csv_row)

    # 4. 保存文件
    # JSON for LSTM
    with open("lstm_feature_data.json", "w") as f:
        json.dump(lstm_ready_data, f, indent=2)
        
    # CSV for Visualization
    df = pd.DataFrame(csv_rows)
    df.to_csv("lstm_features.csv", index=False)
    
    print(f"[+] Features extracted.")
    print(f"    - LSTM Input: lstm_feature_data.json ({len(lstm_ready_data)} samples)")
    print(f"    - Human View: lstm_features.csv (Shape: {df.shape})")
    return df

if __name__ == "__main__":
    df = generate_features()  # 生成特征并返回 DataFrame
    # 打印前几列看看效果
    print("\n[Preview] First 5 columns of CSV:")
    print(df.iloc[:, :5].head())