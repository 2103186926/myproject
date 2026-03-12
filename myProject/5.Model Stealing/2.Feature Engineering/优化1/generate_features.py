'''
为了解决稀疏性问题，我们在特征提取中加入了 Stateful Features（状态特征）。
即使当前步骤是 data_load，其 Cumulative_Query_Count 可能不为 0（继承自上一步），这样矩阵就变稠密了。
'''

import json
import pandas as pd
import numpy as np
from datetime import datetime

INPUT_FILE = "C:\\Users\\21031\\Desktop\\myProject\\Model Stealing\\1.Log ETL\\优化1\\simulated_logs.json"
OUTPUT_JSON = "lstm_feature_data.json"
OUTPUT_CSV = "features_debug.csv"

# 更新事件映射
EVENT_MAP = {
    "PAD": 0, "task_start": 1, "data_load": 2, 
    "model_inference": 3, "data_processing": 4, 
    "model_training": 5, "file_save": 6, "task_end": 7,
    "input_generation": 8 # 可能不再显式出现
}

# 扩充可疑后缀，包含一些模糊的后缀
SUSPICIOUS_EXTENSIONS = ['.joblib', '.pkl', '.pth', '.onnx', '.dat', '.bin']

def parse_timestamp(ts_str):
    return datetime.fromisoformat(ts_str)

def extract_session_features(session_logs):
    vectors = []
    start_time = parse_timestamp(session_logs[0]['timestamp'])
    last_time = start_time
    
    # --- 状态变量 (Stateful Variables) ---
    # 用于解决稀疏性问题，记录历史累积信息
    cumulative_queries = 0
    cumulative_training_count = 0
    last_known_r2 = 0.0 # 采样保持
    
    for log in session_logs:
        curr_time = parse_timestamp(log['timestamp'])
        details = log.get('details', {})
        
        # 1. Event ID (Categorical)
        event_id = EVENT_MAP.get(log['event_type'], 0)
        
        # 2. Time Delta (Numerical)
        time_delta = (curr_time - last_time).total_seconds()
        last_time = curr_time
        
        # 3. Current Batch Size (Raw) - 当前这一步查了多少
        current_batch = details.get('query_count', 0)
        
        # --- 解决稀疏性问题的核心逻辑 ---
        
        # 4. Cumulative Query Count (Stateful) - 累计查了多少
        # 即使这一步不查，这个值也保留，特征不再是0
        cumulative_queries += current_batch
        
        # 5. Is Training (Binary) & 6. Last Known R2 (Stateful)
        is_training = 0
        if log['event_type'] == 'model_training':
            is_training = 1
            cumulative_training_count += 1
            last_known_r2 = details.get('r2_score', last_known_r2) # 更新分数
        
        # 7. Suspicious File (Binary)
        file_ext = details.get('file_ext', '')
        is_suspicious = 1 if file_ext in SUSPICIOUS_EXTENSIONS else 0

        # 8. Query Intensity (Derived) - 平均每秒查询量
        elapsed = (curr_time - start_time).total_seconds() + 0.1
        query_intensity = cumulative_queries / elapsed

        # 组合特征向量 (8维)
        # 包含了瞬时特征 (Batch, TimeDelta) 和 累积特征 (Cumulative, LastR2)
        vectors.append([
            event_id, 
            time_delta, 
            current_batch, 
            cumulative_queries,      # 稠密特征
            is_training, 
            last_known_r2,           # 稠密特征 (Hold)
            query_intensity,         # 稠密特征
            is_suspicious
        ])

    return vectors

def main():
    print(f"[+] Loading logs from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    processed_samples = []
    max_seq_len = 0

    print("[+] Extracting features with stateful logic...")
    for session in raw_data:
        features = extract_session_features(session['logs'])
        label = 1 if session['label'] == 'malicious' else 0
        
        if len(features) > max_seq_len:
            max_seq_len = len(features)
            
        processed_samples.append({
            "session_id": session['session_id'],
            "label": label,
            "features": features,
            "seq_len": len(features)
        })
    
    print(f"    Max sequence length: {max_seq_len}")

    # Padding
    feature_names = ["Event_ID", "Time_Delta", "Curr_Batch", "Cum_Queries", "Is_Train", "Last_R2", "Intensity", "Susp_File"]
    feature_dim = len(feature_names)
    final_dataset = {"feature_names": feature_names, "samples": []}
    csv_rows = []

    for sample in processed_samples:
        features = sample['features']
        padding = [[0] * feature_dim] * (max_seq_len - len(features))
        padded_features = features + padding
        
        final_dataset['samples'].append({
            "session_id": sample['session_id'],
            "label": sample['label'],
            "features": padded_features
        })

        # CSV Export
        row = {
            "session_id": sample['session_id'], 
            "label": "malicious" if sample['label']==1 else "normal",
            "len": sample['seq_len']
        }
        for t in range(max_seq_len):
            for i, name in enumerate(feature_names):
                row[f"t{t}_{name}"] = padded_features[t][i]
        csv_rows.append(row)

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(final_dataset, f)
    
    pd.DataFrame(csv_rows).to_csv(OUTPUT_CSV, index=False)
    print(f"[+] Done. Check {OUTPUT_CSV} to see denser features.")

if __name__ == "__main__":
    main()