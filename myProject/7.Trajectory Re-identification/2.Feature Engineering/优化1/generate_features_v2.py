'''
这个脚本的核心在于**“噪声注入”**。
我们在提取特征时，不再直接相信日志里的数字，而是假设采集系统有误差，或者为了防御对抗样本，我们在训练阶段主动引入噪声（Data Augmentation 的一种形式）
'''

import json
import pandas as pd
import numpy as np

# 增加更多事件类型以适应复杂场景
EVENT_MAP = {
    "PAD": 0, "JOB_START": 1, "DATA_FETCH": 2, 
    "PRE_FILTER": 3, "STREAM_FILTER": 3, # 将 Confusing Normal 的操作映射到同一ID，增加难度
    "BATCH_PROCESS": 4, "DEEP_ANALYSIS": 5, 
    "CHECKPOINT_SAVE": 6, "RESULT_EXPORT": 7
}

FEATURE_COLS = [
    "event_type", "duration_ms", "cpu_usage", "io_ratio", 
    "data_scope_days", "data_scope_area", "record_count", "export_size_kb"
]

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_step_features_with_noise(log):
    """
    提取特征并注入高斯噪声，使边界模糊化
    """
    event_type = EVENT_MAP.get(log.get("event_type", ""), 0)
    params = log.get("params", {})
    metrics = log.get("metrics", {})
    
    # --- 噪声注入配置 ---
    # mean=0, sigma=Scale. 
    # 模拟采集误差或环境波动
    
    # 1. Duration: 波动很大
    raw_dur = metrics.get("duration_ms", 0)
    duration = max(0, raw_dur + np.random.normal(0, raw_dur * 0.1)) # 10% 波动
    
    # 2. CPU: 波动中等
    raw_cpu = metrics.get("cpu_usage_pct", 0)
    cpu = max(0, min(100, raw_cpu + np.random.normal(0, 5.0))) # +/- 5% 绝对值波动
    
    # 3. IO Ratio: 关键特征，稍微加一点扰动
    inp = metrics.get("input_records", 0)
    out = metrics.get("output_records", 0)
    if inp > 0:
        ratio = out / inp
        # 对极小值加微小扰动
        io_ratio = max(0, min(2.0, ratio + np.random.normal(0, 0.01)))
    else:
        io_ratio = 1.0
        
    # 4. Params: 模拟有些参数可能丢失或被模糊处理
    days = params.get("time_span_days", 0)
    if days > 0 and np.random.random() < 0.1: # 10% 概率丢失该特征
        days = 0 
        
    area = params.get("area_sqkm", 0)
    
    rec_count = metrics.get("input_records", 0)
    
    # 5. Export Size: 波动
    raw_exp = metrics.get("file_size_kb", 0)
    export_size = max(0, raw_exp + np.random.normal(0, 2)) # +/- 2KB 波动
    
    return [event_type, duration, cpu, io_ratio, days, area, rec_count, export_size]

def generate_features():
    print("[*] Loading raw logs...")

    # 加载原始日志
    filepath = r"C:\Users\21031\Desktop\myProject\Trajectory Re-identification\1.Log ETL\优化1\ocean_task_logs.json"
    raw_data = load_data(filepath)
    
    processed_seqs = []
    labels = []
    task_ids = []
    
    max_seq_len = 0
    
    for task in raw_data:
        logs = task['logs']
        # 按时间排序
        logs.sort(key=lambda x: x['timestamp'])
        
        seq_features = []
        for log in logs:
            feat_vec = extract_step_features_with_noise(log)
            seq_features.append(feat_vec)
            
        if len(seq_features) > max_seq_len:
            max_seq_len = len(seq_features)
            
        processed_seqs.append(seq_features)
        labels.append(task['label'])
        task_ids.append(task['logs'][0]['task_id'])

    print(f"[*] Max sequence length (Extended): {max_seq_len}")
    
    # Padding
    lstm_ready_data = []
    csv_rows = []
    
    for idx, seq in enumerate(processed_seqs):
        pad_len = max_seq_len - len(seq)
        padding = [[0] * len(FEATURE_COLS) for _ in range(pad_len)]
        padded_seq = seq + padding # Post-padding
        
        lstm_ready_data.append({
            "task_id": task_ids[idx],
            "label": labels[idx],
            "features": padded_seq,
            "seq_len": len(seq)
        })
        
        # Flatten for CSV (只取前 20 步可视化，避免CSV太宽)
        csv_row = {"label": labels[idx], "task_id": task_ids[idx]}
        for step_i, step_vec in enumerate(padded_seq):
            if step_i >= 20: break 
            for feat_i, val in enumerate(step_vec):
                csv_row[f"s{step_i}_{FEATURE_COLS[feat_i]}"] = round(val, 4)
        csv_rows.append(csv_row)

    with open("lstm_feature_data.json", "w") as f:
        json.dump(lstm_ready_data, f, indent=2)
        
    pd.DataFrame(csv_rows).to_csv("lstm_features.csv", index=False)
    print("[+] Features extracted with noise injection.")

if __name__ == "__main__":
    generate_features()