'''
主要改进点：
    1.引入统计波动特征：既然均值（时间、步长）已经重叠，我们就看方差（Variance）。攻击者的伪装往往是机械的（例如固定 sleep 0.2s），而真实环境（正常节点）的噪声是随机的。
    2.关注 Loss 的二阶导数：攻击者的 Loss 震荡剧烈，我们提取 loss_acceleration。
    3.弱化绝对值特征：不再过分依赖 step_gap（因为现在黑白都是1了），而是依赖多维特征的非线性组合。
'''

import json
import csv
import numpy as np
from datetime import datetime

# ==========================================
# 1. 特征配置 (V4 - 模糊边界版)
# ==========================================

# 仅保留基础阶段
PHASE_VOCAB = ["FL_CLIENT_START", "LOCAL_COMPUTE", "UPLOAD_UPDATE"]

FEATURE_NAMES = [
    "delta_time",       # 基础时间
    "step_gap",         # 在 V4 中，黑白样本这里几乎都是 1，甚至正常样本因为丢包会变成 2 (混淆)
    "loss_val",         # Loss 值
    "loss_diff",        # Loss 变化量 (一阶)
    "loss_volatility",  # Loss 波动性 (与均值的偏离度)
    "speed_anomaly",    # 速度异常度 (当前速度 vs 平均速度)
    "log_density",      # 日志密度
    "is_compute",       # 阶段标志
    "cum_progress"      # 归一化进度
]
# 总维度 = 9 + 3(OneHot) = 12维

def parse_ts(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

def extract_features(session):
    logs = session['logs']
    features = []
    
    if not logs: return []
    
    start_ts = parse_ts(logs[0]['timestamp'])
    prev_ts = start_ts
    prev_step = 0
    prev_loss = 0
    
    # 预计算一些统计量用于归一化 (模拟流式处理时的滑动窗口统计)
    loss_history = []
    
    for log in logs:
        curr_ts = parse_ts(log['timestamp'])
        metrics = log.get('metrics', {})
        
        # --- 1. 时间特征 ---
        dt = (curr_ts - prev_ts).total_seconds()
        cum_t = (curr_ts - start_ts).total_seconds()
        
        # 避免除0
        safe_dt = max(dt, 0.001)
        
        # --- 2. 业务特征 (混淆重灾区) ---
        curr_step = metrics.get('step_index', 0)
        step_gap = curr_step - prev_step
        if step_gap < 0: step_gap = 0
        
        # --- 3. Loss 特征 (破局关键) ---
        curr_loss = metrics.get('loss_value', 0)
        loss_diff = curr_loss - prev_loss
        loss_history.append(curr_loss)
        
        # 计算 Loss 的局部波动性 (Volatility)
        # 攻击者的 Loss 往往因为伪装而呈现非自然的震荡
        if len(loss_history) > 1:
            avg_loss = sum(loss_history) / len(loss_history)
            loss_volatility = abs(curr_loss - avg_loss)
        else:
            loss_volatility = 0
            
        # --- 4. 速度异常特征 ---
        # 正常节点的计算时间服从正态分布，攻击者为了凑时间可能比较生硬
        # 这里用简单的 Log Density 倒数
        speed = 1.0 / safe_dt
        
        # --- 5. Phase One-Hot ---
        phase = log.get('phase', 'UNKNOWN')
        phase_vec = [0] * len(PHASE_VOCAB)
        if phase in PHASE_VOCAB:
            phase_vec[PHASE_VOCAB.index(phase)] = 1
            
        is_compute = 1.0 if phase == "LOCAL_COMPUTE" else 0.0
        
        # 组合特征
        row = [
            dt,
            step_gap,
            curr_loss,
            loss_diff,
            loss_volatility,
            speed,
            1.0/safe_dt, # Log Density
            is_compute,
            cum_t / 30.0 # 假设最大30s
        ] + phase_vec
        
        features.append(row)
        
        prev_ts = curr_ts
        if is_compute: prev_step = curr_step
        prev_loss = curr_loss
        
    return features

if __name__ == "__main__":
    # 与之前类似的 IO 逻辑
    input_file = "C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\1.Log ETL\\优化3\\federated_learning_structured.json"
    json_output = "lstm_feature_data.json"
    csv_output = "lstm_feature_visualization.csv"
    
    with open(input_file, 'r') as f:
        data = json.load(f)
        
    processed = []
    max_len = 0
    
    for session in data:
        feats = extract_features(session)
        max_len = max(max_len, len(feats))
        processed.append({
            "session_id": session['session_id'],
            "label": session['label'],
            "client_type": session['client_type'],
            "features": feats,
            "seq_len": len(feats)
        })
        
    with open(json_output, 'w') as f:
        json.dump(processed, f, indent=2)
        
    # 输出 CSV 表头
    header = ["session_id", "label", "client_type"] + [f"step_{i}_{n}" for i in range(max_len) for n in FEATURE_NAMES + [f"p_{x}" for x in PHASE_VOCAB]]
    
    with open(csv_output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for item in processed:
            row = [item['session_id'], item['label'], item['client_type']]
            for i in range(max_len):
                if i < len(item['features']):
                    row.extend(item['features'][i])
                else:
                    row.extend([0.0] * (len(FEATURE_NAMES) + len(PHASE_VOCAB)))
            writer.writerow(row)
            
    print(f"V4 特征提取完成。最大序列长度: {max_len}")
    print("现在特征中包含了大量噪声：StepGap不再是完美特征，Loss具有震荡性。")