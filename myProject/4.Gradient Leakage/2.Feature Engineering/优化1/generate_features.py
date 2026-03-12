'''
主要改进点：
    1.移除“上帝视角”特征：删除了 loss_type、is_ATTACK、is_MALICIOUS 等直接暴露答案的特征。
    2.引入统计特征：由于Phase名称现在混淆了（都叫 TRAINING_STEP），模型必须依赖Step的数量、Step间的时间密度以及Loss的数值分布来区分。
    3.增加鲁棒特征：增加了 log_density (每秒日志量) 和 step_count (当前Session内的步数计数)。
'''

import json
import csv
import numpy as np
from datetime import datetime

# ==========================================
# 1. 改进后的特征定义
# ==========================================

# 仅仅保留最基础的架构阶段，不再包含 "ATTACK" 关键字
# 强迫模型去学习序列长度和时间分布
PHASE_VOCAB = [
    "TRAINING_START", 
    "TRAINING_STEP",   # 正常和攻击都使用这个 Tag
    "TRAINING_END", 
    "UPLOAD_SUCCESS",
    "CACHE_FLUSH"      # 攻击者特有的IO操作，但也可能被混淆
]

FEATURE_NAMES = [
    "delta_time",       # Δt: 瞬时速度
    "cumulative_time",  # T_cum: 进度条
    "log_density",      # Density: 当前时间点的日志密度 (1/Δt)
    "loss_value",       # Loss: 数值本身
    "step_counter",     # N: 当前是第几步 (归一化)
    "is_file_io",       # 是否涉及文件写入 (敏感操作)
    # One-Hot Phases (5维)
    *[f"phase_{p}" for p in PHASE_VOCAB]
]
# 总维度: 6 + 5 = 11维

def parse_timestamp(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

def extract_features_from_session(session):
    logs = session['logs']
    features = []
    
    if not logs:
        return []
        
    start_time = parse_timestamp(logs[0]['timestamp'])
    prev_time = start_time
    
    step_counter = 0 # 记录 Session 内部的步数
    
    for log in logs:
        curr_time = parse_timestamp(log['timestamp'])
        
        # 1. Temporal Features
        dt = (curr_time - prev_time).total_seconds()
        cum_t = (curr_time - start_time).total_seconds()
        
        # 避免除以0，设置上限
        safe_dt = max(dt, 0.001) 
        log_density = 1.0 / safe_dt if dt > 0 else 0
        
        # 2. Metric Features
        metrics = log.get('metrics', {})
        loss_val = metrics.get('loss_value', 0.0)
        
        # 步数计数器 (无论是 Epoch 还是 Iteration，都算作一步)
        if log.get('phase') == 'TRAINING_STEP':
            step_counter += 1
        
        # 简单的归一化，让模型知道 10 和 500 的区别
        count_norm = step_counter / 500.0 
        
        # 3. Behavioral Features
        # 检测是否有文件落地行为 (npy) - 这是一个较强的启发式特征
        msg = log.get('message', '').lower()
        is_io = 1.0 if ('.npy' in msg or 'dump' in msg) else 0.0
        
        # 4. Phase One-Hot
        phase = log.get('phase', 'UNKNOWN')
        phase_vec = [0] * len(PHASE_VOCAB)
        if phase in PHASE_VOCAB:
            phase_vec[PHASE_VOCAB.index(phase)] = 1
            
        # 组合特征
        row = [dt, cum_t, log_density, loss_val, count_norm, is_io] + phase_vec
        features.append(row)
        
        prev_time = curr_time

    return features

if __name__ == "__main__":
    input_file = "C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\1.Log ETL\\federated_learning_structured.json"
    json_output = "lstm_feature_data.json"
    csv_output = "lstm_feature_visualization.csv"
    
    print("读取数据...")
    with open(input_file, 'r') as f:
        data = json.load(f)
        
    processed = []
    max_len = 0
    
    print("提取特征...")
    for session in data:
        feats = extract_features_from_session(session)
        max_len = max(max_len, len(feats))
        processed.append({
            "session_id": session['session_id'],
            "label": session['label'],
            "client_type": session['client_type'],
            "features": feats,
            "seq_len": len(feats)
        })
        
    # 保存 JSON
    with open(json_output, 'w') as f:
        json.dump(processed, f, indent=2)
        
    # 保存 CSV
    print(f"生成 CSV (Max Seq Len: {max_len})...")
    header = ["session_id", "label", "client_type"]
    for i in range(max_len):
        for name in FEATURE_NAMES:
            header.append(f"step_{i}_{name}")
            
    with open(csv_output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for item in processed:
            row = [item['session_id'], item['label'], item['client_type']]
            feats = item['features']
            # Padding
            for i in range(max_len):
                if i < len(feats):
                    row.extend(feats[i])
                else:
                    row.extend([0.0] * len(FEATURE_NAMES))
            writer.writerow(row)
            
    print("完成。现在特征更依赖于序列的行为模式而非关键字。")