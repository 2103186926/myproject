## 特征提取基础版脚本

import json
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# ==========================================
# 1. 配置与定义
# ==========================================

# 定义关键阶段 (Phase) 的词表，用于 One-Hot 编码
PHASE_VOCAB = [
    "TRAINING_START", 
    "TRAINING_EPOCH", 
    "TRAINING_END", 
    "UPLOAD_SUCCESS",
    "ATTACK_START",    # 恶意特征
    "ATTACK_INIT",     # 恶意特征
    "ATTACK_ITERATION",# 恶意特征 (高频)
    "FILE_IO",         # 恶意特征
    "UPLOAD_ATTEMPT",  # 恶意特征 (通常伴随延迟)
    "UPLOAD_DELAY"     # 恶意特征
]

# 定义 Loss 类型的映射
LOSS_TYPE_MAP = {
    "prediction_loss": 1, # 正常
    "gradient_loss": -1,  # 恶意 (取负值以显著区分)
    "unknown": 0
}

def parse_timestamp(ts_str):
    """解析时间戳字符串"""
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

def extract_features_from_session(session):
    """
    对单个 Session 提取时序特征序列
    输出: (Sequence_Length, Feature_Dim) 的矩阵
    """
    logs = session['logs']
    features = []
    
    # 初始化上一个时间戳，用于计算 Delta Time
    if not logs:
        return []
        
    start_time = parse_timestamp(logs[0]['timestamp'])
    prev_time = start_time
    
    for i, log in enumerate(logs):
        curr_time = parse_timestamp(log['timestamp'])
        
        # --- 特征 1: Time Delta (Δt) ---
        # 当前日志距离上一条日志的时间间隔 (秒)
        # 恶意行为在 ATTACK_ITERATION 期间会有密集的短间隔，但在 Upload 阶段会有巨大的长间隔
        time_delta = (curr_time - prev_time).total_seconds()
        
        # --- 特征 2: Cumulative Time (T_cum) ---
        # 任务开始到现在的总耗时
        # 恶意任务的总耗时通常远超正常任务
        cum_time = (curr_time - start_time).total_seconds()
        
        # --- 特征 3: Phase Encoding (One-Hot) ---
        # 当前处于哪个阶段。这不仅是语义特征，也隐含了状态机转换
        phase = log.get('phase', 'UNKNOWN')
        phase_idx = PHASE_VOCAB.index(phase) if phase in PHASE_VOCAB else -1
        phase_vec = [0] * len(PHASE_VOCAB)
        if phase_idx != -1:
            phase_vec[phase_idx] = 1
            
        # --- 特征 4: Log Level (Numeric) ---
        # INFO=1, DEBUG=0, WARNING=2, ATTACK=3
        level_map = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ATTACK": 3}
        level_val = level_map.get(log.get('level', 'INFO'), 1)
        
        # --- 特征 5: Loss Value Trend ---
        # 提取 metrics 中的 loss_value。
        # 如果当前日志没有 loss，则沿用上一次的值 (Padding) 或置 0
        metrics = log.get('metrics', {})
        loss_val = metrics.get('loss_value', 0.0)
        
        # --- 特征 6: Loss Type ---
        # 区分是预测损失还是梯度匹配损失
        l_type = metrics.get('loss_type', 'unknown')
        loss_type_val = LOSS_TYPE_MAP.get(l_type, 0)
        
        # --- 特征 7: Iteration/Epoch Counter ---
        # 归一化后的计数器。恶意攻击的 Iteration 通常很大 (0-500)，正常 Epoch 很小 (1-5)
        # 我们做一个简单的缩放，比如除以 100，让模型感知数量级差异
        count_val = metrics.get('epoch', 0) + metrics.get('iteration', 0)
        count_val_scaled = count_val / 100.0 

        # === 组合当前时间步的特征向量 ===
        # 维度: 1(dt) + 1(cum_t) + 10(phase) + 1(level) + 1(loss) + 1(loss_type) + 1(count) = 16维
        row_feature = [time_delta, cum_time] + phase_vec + [level_val, loss_val, loss_type_val, count_val_scaled]
        
        features.append(row_feature)
        prev_time = curr_time

    return features

# ==========================================
# 2. 主处理流程
# ==========================================

if __name__ == "__main__":
    input_file = "C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\1.Log ETL\\federated_learning_structured.json"
    output_file = "lstm_feature_data.json"
    
    print(f"正在读取 {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
        
    processed_dataset = []
    
    print("开始特征提取...")
    for session in raw_data:
        # 1. 提取特征矩阵 (List of Lists)
        feature_sequence = extract_features_from_session(session)
        
        # 2. 保留标签
        label = session['label']
        client_type = session['client_type']
        session_id = session['session_id']
        
        processed_dataset.append({
            "session_id": session_id,
            "label": label,          # 0: Normal, 1: Malicious
            "client_type": client_type,
            "features": feature_sequence, # 形状: [Sequence_Length, 16]
            "seq_len": len(feature_sequence) # 记录长度，方便后续Padding
        })
        
    # 3. (可选) 特征标准化预处理逻辑建议
    # 在实际深度学习训练前，通常会对 [time_delta, cum_time, loss_val] 做 Z-Score 标准化
    # 这里为了保持 json 可读性，暂保留原始数值，标准化放在 LSTM 数据加载器中做
    
    print(f"特征提取完成，共处理 {len(processed_dataset)} 个Session。")
    print(f"单个样本特征维度: {len(processed_dataset[0]['features'][0])}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_dataset, f, indent=2)
        
    print(f"特征数据已保存至 {output_file}")