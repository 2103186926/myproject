'''
修复与改进点：
    1.解决 0 值问题：特征提取的 PHASE_MAP 必须与 Mock 数据的 PHASE_* 常量完全对应。
    2.解决太 Easy 问题：既然日志数量（Sequence Length）和总时长（Duration）已经无法区分黑白，我们必须引入二阶特征：
        Step Gap (步长跳跃)：计算当前日志的 step_index 减去上一条日志的 step_index。正常节点是 1，恶意节点（降频后）可能是 100。这是核心特征。
        Loss Velocity (损失速率)：Loss 变化的斜率。
        Time per Step (单步耗时)：Delta Time / Step Gap。攻击者的单步耗时（GPU加速）通常远小于正常节点（CPU训练）。
'''

import json
import csv
import numpy as np
from datetime import datetime

# ==========================================
# 1. 特征配置 (V3)
# ==========================================

# 必须与 mock 代码中的 phase 字符串完全一致
PHASE_VOCAB = ["FL_CLIENT_START", "LOCAL_COMPUTE", "UPLOAD_UPDATE"]

FEATURE_NAMES = [
    "delta_time",       # 原始特征：时间间隔
    "step_gap",         # 核心特征：Step Index 的跳跃幅度
    "loss_val",         # 原始特征：Loss 值
    "loss_velocity",    # 衍生特征：Loss 变化率
    "time_per_index",   # 衍生特征：归一化后的单步计算耗时 (估算算力)
    "is_compute_phase", # 状态特征：是否处于计算阶段
    "cum_time_norm"     # 归一化累计时间
]
# 总维度 = 7维 (精简但有效)

def parse_ts(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

def extract_features(session):
    logs = session['logs']
    features = []
    
    if not logs: return []
    
    start_ts = parse_ts(logs[0]['timestamp'])
    prev_ts = start_ts
    prev_step_idx = 0
    prev_loss = 0
    
    # 这里的 Max Time 用于归一化，假设最大也就是 30秒
    MAX_TIME_CONST = 30.0 
    
    for log in logs:
        curr_ts = parse_ts(log['timestamp'])
        metrics = log.get('metrics', {})
        
        # --- 1. 时间类特征 ---
        dt = (curr_ts - prev_ts).total_seconds()
        cum_t = (curr_ts - start_ts).total_seconds()
        cum_t_norm = cum_t / MAX_TIME_CONST
        
        # --- 2. 业务逻辑类特征 (Step Gap) ---
        curr_step_idx = metrics.get('step_index', 0)
        # 计算跳跃：如果当前是 100，上一次是 0，则 gap = 100
        # 正常节点 gap 应该是 1 (Epoch 1 -> Epoch 2)
        step_gap = curr_step_idx - prev_step_idx
        if step_gap < 0: step_gap = 0 # 避免 Upload 阶段重置带来的负数
        
        # --- 3. 算力类特征 (Time per logical step) ---
        # 攻击者虽然总时长正常，但因为跑了500步，所以单步耗时极短
        # 正常节点跑5步，单步耗时较长
        time_per_index = dt / step_gap if step_gap > 0 else dt
        
        # --- 4. Loss 类特征 ---
        curr_loss = metrics.get('loss_value', 0)
        loss_diff = curr_loss - prev_loss
        # 避免除以0
        loss_velocity = loss_diff / dt if dt > 0.001 else 0
        
        # --- 5. Phase One-Hot (简化为 Is_Compute) ---
        is_compute = 1.0 if log.get('phase') == "LOCAL_COMPUTE" else 0.0
        
        # 组合特征向量
        row = [
            dt, 
            step_gap,       # <--- 破局关键 1
            curr_loss, 
            loss_velocity, 
            time_per_index, # <--- 破局关键 2
            is_compute,
            cum_t_norm
        ]
        features.append(row)
        
        # 更新状态
        prev_ts = curr_ts
        # 只有在 compute 阶段才更新 step_idx，避免 Upload 阶段干扰
        if is_compute:
            prev_step_idx = curr_step_idx
        prev_loss = curr_loss
        
    return features

if __name__ == "__main__":
    print("读取 Mock 数据...")
    with open("C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\1.Log ETL\\优化2\\federated_learning_structured.json", 'r') as f:
        data = json.load(f)
        
    processed = []
    max_len = 0
    
    print("提取 V3 特征...")
    for session in data:
        feats = extract_features(session)
        max_len = max(max_len, len(feats))
        processed.append({
            "session_id": session['session_id'],
            "label": session['label'],
            "features": feats
        })
        
    # 保存 JSON
    with open("lstm_feature_data.json", 'w') as f:
        json.dump(processed, f, indent=2)
        
    # 保存 CSV (方便您检查)
    print("生成 CSV 可视化...")
    header = ["session_id", "label"] + [f"step_{i}_{n}" for i in range(max_len) for n in FEATURE_NAMES]
    
    with open("lstm_feature_visualization.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for item in processed:
            row = [item['session_id'], item['label']]
            for i in range(max_len):
                if i < len(item['features']):
                    row.extend(item['features'][i])
                else:
                    row.extend([0.0] * len(FEATURE_NAMES)) # Padding
            writer.writerow(row)
            
    print(f"完成。Max Seq Len: {max_len}")
    print("请检查 CSV 中的 'step_gap' 和 'time_per_index' 列，这应该是区分黑白的关键。")