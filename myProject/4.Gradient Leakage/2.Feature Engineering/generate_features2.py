## 特征提取优化版脚本
## 在基础版脚本的基础上，增加了 CSV 生成模块。

import json
import csv
import numpy as np
from datetime import datetime

# ==========================================
# 1. 配置与定义 (特征维度定义)
# ==========================================

# 阶段词表 (对应特征索引 2-11)
PHASE_VOCAB = [
    "TRAINING_START", 
    "TRAINING_EPOCH", 
    "TRAINING_END", 
    "UPLOAD_SUCCESS",
    "ATTACK_START",    
    "ATTACK_INIT",     
    "ATTACK_ITERATION",
    "FILE_IO",         
    "UPLOAD_ATTEMPT",  
    "UPLOAD_DELAY"     
]

# 基础特征名列表 (共 16 维)
FEATURE_NAMES_BASE = [
    "delta_time",       # index 0: 距离上一条日志的时间间隔
    "cumulative_time",  # index 1: 任务开始后的累计时间
    # index 2-11: Phase One-Hot
    *[f"is_{p}" for p in PHASE_VOCAB], 
    "log_level",        # index 12: 日志级别数值
    "loss_value",       # index 13: 损失值
    "loss_type",        # index 14: 损失类型(1预测/-1梯度)
    "iteration_count"   # index 15: 归一化的计数器
]

# Loss 类型映射
LOSS_TYPE_MAP = {
    "prediction_loss": 1,
    "gradient_loss": -1,
    "unknown": 0
}

# ==========================================
# 2. 核心处理函数
# ==========================================

def parse_timestamp(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

def extract_features_from_session(session):
    """
    提取单个会话的特征序列
    """
    logs = session['logs']
    features = []
    
    if not logs:
        return []
        
    start_time = parse_timestamp(logs[0]['timestamp'])
    prev_time = start_time
    
    for log in logs:
        curr_time = parse_timestamp(log['timestamp'])
        
        # 1. Time Delta
        time_delta = (curr_time - prev_time).total_seconds()
        
        # 2. Cumulative Time
        cum_time = (curr_time - start_time).total_seconds()
        
        # 3. Phase One-Hot
        phase = log.get('phase', 'UNKNOWN')
        phase_vec = [0] * len(PHASE_VOCAB)
        if phase in PHASE_VOCAB:
            phase_vec[PHASE_VOCAB.index(phase)] = 1
            
        # 4. Log Level
        level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ATTACK": 3}
        level_val = level_map.get(log.get('level', 'INFO'), 1)
        
        # 5-7. Metrics
        metrics = log.get('metrics', {})
        loss_val = metrics.get('loss_value', 0.0)
        loss_type_val = LOSS_TYPE_MAP.get(metrics.get('loss_type', 'unknown'), 0)
        count_val = metrics.get('epoch', 0) + metrics.get('iteration', 0)
        count_val_scaled = count_val / 100.0 # 简单缩放
        
        # 组合特征 (16维)
        row_feature = [time_delta, cum_time] + phase_vec + [level_val, loss_val, loss_type_val, count_val_scaled]
        features.append(row_feature)
        
        prev_time = curr_time

    return features

# ==========================================
# 3. 主执行流程
# ==========================================

if __name__ == "__main__":
    input_file = "C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\1.Log ETL\\federated_learning_structured.json"
    json_output_file = "lstm_feature_data.json"
    csv_output_file = "lstm_feature_visualization.csv"
    
    print(f"正在读取 {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    processed_data = []
    max_seq_len = 0
    
    # --- 步骤 1: 提取所有特征 ---
    print("正在提取特征...")
    for session in raw_data:
        feature_seq = extract_features_from_session(session)
        
        # 记录最大长度用于 Padding
        if len(feature_seq) > max_seq_len:
            max_seq_len = len(feature_seq)
            
        processed_data.append({
            "session_id": session['session_id'],
            "label": session['label'],
            "client_type": session['client_type'],
            "features": feature_seq,
            "seq_len": len(feature_seq)
        })
        
    print(f"最大序列长度 (Max Seq Len): {max_seq_len}")
    
    # --- 步骤 2: 输出 JSON (供模型使用) ---
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2)
    print(f"模型输入数据已保存至: {json_output_file}")
    
    # --- 步骤 3: 输出 CSV (供人工观察) ---
    print("正在生成可视化 CSV...")
    
    # 3.1 构建动态表头
    # 表头格式: session_id, label, step_0_delta_time, step_0_cum_time, ..., step_N_loss_value...
    csv_header = ["session_id", "label", "client_type"]
    for i in range(max_seq_len):
        for name in FEATURE_NAMES_BASE:
            csv_header.append(f"step_{i}_{name}")
            
    with open(csv_output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        
        for item in processed_data:
            row = [item['session_id'], item['label'], item['client_type']]
            features = item['features']
            
            # 3.2 填充与扁平化 (Padding & Flattening)
            # 对每个时间步
            for i in range(max_seq_len):
                if i < len(features):
                    # 如果当前步有数据，直接添加
                    row.extend(features[i])
                else:
                    # 如果超过了当前数据的长度，填充 0 (Padding)
                    # 填充维度必须等于特征维度 (16维)
                    row.extend([0] * len(FEATURE_NAMES_BASE))
            
            writer.writerow(row)
            
    print(f"特征可视化表格已保存至: {csv_output_file}")
    print("任务完成。")