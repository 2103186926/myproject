import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler

# 配置
INPUT_FILE = "C:\\Users\\21031\\Desktop\\myProject\\Model Stealing\\1.Log ETL\\simulated_logs.json"
OUTPUT_JSON = "lstm_feature_data.json"
OUTPUT_CSV = "features_debug.csv"

# 事件类型映射表 (Label Encoding)
EVENT_MAP = {
    "PAD": 0,               # 填充位
    "task_start": 1,
    "data_load": 2,
    "input_generation": 3,  # 恶意特征强相关
    "model_inference": 4,   # 核心特征
    "model_training": 5,    # 恶意特征强相关 (替代模型训练)
    "data_processing": 6,
    "file_save": 7,         # 检查后缀
    "task_end": 8
}

# 可疑文件后缀列表
SUSPICIOUS_EXTENSIONS = ['.joblib', '.pkl', '.pth', '.onnx']

def parse_timestamp(ts_str):
    return datetime.fromisoformat(ts_str)

def extract_session_features(session_logs):
    """
    从单个会话日志列表中提取时序特征向量。
    返回: list of feature lists [[f1, f2, ...], [f1, f2, ...]]
    """
    vectors = []
    start_time = parse_timestamp(session_logs[0]['timestamp'])
    last_time = start_time

    for log in session_logs:
        curr_time = parse_timestamp(log['timestamp'])
        details = log.get('details', {})
        
        # --- 特征 1: 事件类型 ID (Categorical) ---
        event_id = EVENT_MAP.get(log['event_type'], 0)
        
        # --- 特征 2: 时间间隔 (Time Delta, seconds) ---
        # 相比绝对时间，LSTM 对相对时间间隔更敏感（检测自动化脚本的高频操作）
        time_delta = (curr_time - last_time).total_seconds()
        last_time = curr_time

        # --- 特征 3: 查询量 (Query Count) ---
        # 归一化处理通常在全局做，这里先取原始值
        query_count = details.get('query_count', 0)

        # --- 特征 4: 是否为训练行为 (Is Training) ---
        # 这是一个强二值特征，专门标记攻击者的“偷师”时刻
        is_training = 1 if log['event_type'] == 'model_training' else 0

        # --- 特征 5: 模型性能评分 (R2 Score / Accuracy) ---
        # 攻击者会关注替代模型的性能提升
        r2_score = details.get('r2_score', 0.0)

        # --- 特征 6: 是否保存可疑文件 (Suspicious Artifact) ---
        file_ext = details.get('file_ext', '')
        is_suspicious_file = 1 if file_ext in SUSPICIOUS_EXTENSIONS else 0

        # 组合成单步特征向量 (6维)
        # vector shape: [Event_ID, Time_Delta, Query_Count, Is_Training, R2_Score, Suspicious_File]
        vectors.append([event_id, time_delta, query_count, is_training, r2_score, is_suspicious_file])

    return vectors

def main():
    print(f"[+] Loading logs from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    processed_samples = []
    max_seq_len = 0

    # 1. 初步提取特征
    print("[+] Extracting features from sessions...")
    for session in raw_data:
        features = extract_session_features(session['logs'])
        label = 1 if session['label'] == 'malicious' else 0 # Label Encoding
        
        if len(features) > max_seq_len:
            max_seq_len = len(features)
            
        processed_samples.append({
            "session_id": session['session_id'],
            "label": label,
            "features": features,
            "seq_len": len(features)
        })
    
    print(f"    Max sequence length found: {max_seq_len}")

    # 2. 序列填充 (Padding) 与 归一化准备
    # 为了方便观察CSV，我们手动做 Padding，不足 max_seq_len 的后面补 0 向量
    feature_dim = 6 # 我们提取了6个特征
    csv_rows = []

    final_dataset = {
        "feature_names": ["Event_ID", "Time_Delta", "Query_Count", "Is_Training", "R2_Score", "Suspicious_File"],
        "max_seq_len": max_seq_len,
        "feature_dim": feature_dim,
        "samples": []
    }

    print("[+] Padding sequences and generating CSV data...")
    for sample in processed_samples:
        original_len = sample['seq_len']
        features = sample['features']
        
        # Padding
        padding_count = max_seq_len - original_len
        padded_features = features + [[0] * feature_dim] * padding_count
        
        # 构建 JSON 输出格式
        final_dataset['samples'].append({
            "session_id": sample['session_id'],
            "label": sample['label'],
            "features": padded_features # 这里的 features 是 List[List[float]]
        })

        # 构建 CSV 行 (Flattening)
        # 每一行代表一个 Session，列展开为 t0_feat0, t0_feat1 ... tn_featM
        csv_row = {
            "session_id": sample['session_id'],
            "label": "malicious" if sample['label'] == 1 else "normal",
            "original_len": original_len
        }
        
        for t in range(max_seq_len):
            step_feats = padded_features[t]
            for f_idx, val in enumerate(step_feats):
                col_name = f"step_{t}_{final_dataset['feature_names'][f_idx]}"
                csv_row[col_name] = val
        
        csv_rows.append(csv_row)

    # 3. 保存文件
    # 保存 JSON (LSTM Input)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2)
    print(f"[+] LSTM input data saved to {OUTPUT_JSON}")

    # 保存 CSV (Debug View)
    df = pd.DataFrame(csv_rows)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[+] Feature inspection table saved to {OUTPUT_CSV}")
    print(f"    CSV Shape: {df.shape}")

if __name__ == "__main__":
    main()