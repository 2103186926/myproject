'''
核心变化：
    1.重叠式噪声注入：不再是简单的加减，而是让攻击和正常的特征分布发生重叠。
        例如：攻击的 CPU 是 90%，我们加上 N(0, 15) 的噪声，它可能变成 60%。
        正常的 CPU 是 50%，加上噪声可能变成 70%。
        这就强迫 LSTM 去学习时序上的微小结构差异，而不是依赖绝对值。
    2.随机丢弃 (Dropout at Input)：随机将某些步骤的某些特征置为 0，模拟日志采集丢失，增加学习难度。
'''
import random
import json
import pandas as pd
import numpy as np

EVENT_MAP = {
    "PAD": 0, "JOB_START": 1, "DATA_FETCH": 2, 
    "PRE_FILTER": 3, "BATCH_PROCESS": 4, "DEEP_ANALYSIS": 5, 
    "CHECKPOINT_SAVE": 6, "RESULT_EXPORT": 7, "STREAM_FILTER": 8 # 增加更多事件类型
}

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_features_heavy_noise(log):
    event_type = EVENT_MAP.get(log.get("event_type", ""), 0)
    params = log.get("params", {})
    metrics = log.get("metrics", {})
    
    # === 强噪声注入区 ===
    
    # 1. CPU: 制造严重重叠
    # 攻击者可能只有 50% CPU，正常可能飙到 90%
    raw_cpu = metrics.get("cpu_usage_pct", 0)
    # 噪声标准差调大到 15.0，这非常大！
    cpu = max(0, min(100, raw_cpu + np.random.normal(0, 15.0))) 
    
    # 2. Duration: 随机波动
    raw_dur = metrics.get("duration_ms", 0)
    duration = max(0, raw_dur + np.random.normal(0, raw_dur * 0.2)) # 20% 波动
    
    # 3. I/O Ratio: 关键特征也要模糊化
    inp = metrics.get("input_records", 0)
    out = metrics.get("output_records", 0)
    if inp > 0:
        ratio = out / inp
        # 如果 ratio 很小（漏斗），给它加个大的正向噪声，让它看起来没那么小
        if ratio < 0.01:
            ratio = ratio * random.uniform(1.0, 5.0) 
        io_ratio = ratio
    else:
        io_ratio = 1.0
        
    # 4. Data Scope: 偶尔丢失信息
    days = params.get("time_span_days", 0)
    if np.random.random() < 0.15: days = 0 # 15% 概率丢失
    
    area = params.get("area_sqkm", 0)
    
    rec_count = metrics.get("input_records", 0)
    
    # 5. Export Size: 模糊边界
    # 攻击可能是 10KB，正常可能是 50KB，加噪声让它们在 30KB 左右重叠
    raw_exp = metrics.get("file_size_kb", 0)
    export_size = max(0, raw_exp + np.random.normal(0, 10)) 
    
    return [event_type, duration, cpu, io_ratio, days, area, rec_count, export_size]

def generate_features():
    print("[*] Loading raw logs (V3)...")
    raw_data = load_data("C:\\Users\\21031\\Desktop\\myProject\\Trajectory Re-identification\\1.Log ETL\\优化2\\ocean_task_logs.json")
    
    processed_seqs = []
    labels = []
    task_ids = []
    
    max_seq_len = 0
    
    for task in raw_data:
        logs = task['logs']
        logs.sort(key=lambda x: x['timestamp'])
        
        seq_features = []
        for log in logs:
            feat_vec = extract_features_heavy_noise(log)
            seq_features.append(feat_vec)
            
        if len(seq_features) > max_seq_len:
            max_seq_len = len(seq_features)
            
        processed_seqs.append(seq_features)
        labels.append(task['label'])
        task_ids.append(task['logs'][0]['task_id'])

    print(f"[*] Max sequence length: {max_seq_len} (Should be larger now)")
    
    # Padding
    lstm_ready_data = []
    feature_cols = ["event", "dur", "cpu", "io", "days", "area", "rec", "exp"]
    csv_rows = []
    
    for idx, seq in enumerate(processed_seqs):
        pad_len = max_seq_len - len(seq)
        padding = [[0] * 8 for _ in range(pad_len)]
        padded_seq = seq + padding
        
        lstm_ready_data.append({
            "task_id": task_ids[idx],
            "label": labels[idx],
            "features": padded_seq,
            "seq_len": len(seq)
        })
        
        # CSV Flattening (First 20 steps only)
        row = {"label": labels[idx], "len": len(seq)}
        for t in range(min(20, len(padded_seq))):
            for f_idx, val in enumerate(padded_seq[t]):
                row[f"t{t}_{feature_cols[f_idx]}"] = round(val, 3)
        csv_rows.append(row)

    with open("lstm_feature_data.json", "w") as f:
        json.dump(lstm_ready_data, f, indent=2)
        
    pd.DataFrame(csv_rows).to_csv("lstm_features.csv", index=False)
    print(f"[+] Features extracted. Noise injected. Saved {len(lstm_ready_data)} samples.")

if __name__ == "__main__":
    generate_features()