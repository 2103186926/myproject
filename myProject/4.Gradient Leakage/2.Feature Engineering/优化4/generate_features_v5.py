'''
为了让模型“难受”，我们提取的特征必须是有噪声的。我们不再提取绝对值，而是提取二阶统计量。
关键改动：
    1.移除 delta_time 绝对值：因为黑白样本均值都是 0.5s，这个特征已经失效。
    2.引入 dt_variance (时间方差)：这是破局点。正常节点方差大（网络抖动），恶意节点方差小（机器 Sleep）。但这个界限很模糊。
    3.引入 loss_volatility (Loss 波动)：正常 Loss 平滑，恶意 Loss 锯齿。
'''

import json
import csv
import numpy as np
from datetime import datetime

# ==========================================
# 1. 特征定义
# ==========================================

# 全局统计特征 (6维)
GLOBAL_FEATURE_NAMES = [
    "dt_mean",          # 时间间隔均值
    "dt_std",           # 时间间隔标准差 (关键混淆点)
    "loss_mean",        # Loss 均值
    "loss_std",         # Loss 标准差
    "loss_trend",       # Loss 趋势 (斜率)
    "loss_jaggedness"   # Loss 锯齿度
]

# 瞬时特征 (2维)
INSTANT_FEATURE_NAMES = [
    "step_dt",          # 当前步耗时
    "step_loss"         # 当前步Loss值
]

# 组合后的特征名列表 (8维)
ALL_FEATURE_NAMES = INSTANT_FEATURE_NAMES + GLOBAL_FEATURE_NAMES

def parse_ts(ts_str):
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

def get_global_features(session):
    """提取全会话级别的统计特征"""
    logs = session['logs']
    if len(logs) < 2: return [0]*6
    
    timestamps = [parse_ts(l['timestamp']) for l in logs]
    loss_vals = [l['metrics']['val'] for l in logs]
    
    # 1. 时间序列统计
    dts = []
    for i in range(1, len(timestamps)):
        dt = (timestamps[i] - timestamps[i-1]).total_seconds()
        dts.append(dt)
    
    dt_mean = np.mean(dts) if dts else 0
    dt_std = np.std(dts) if dts else 0 
    
    # 2. Loss 序列统计
    loss_mean = np.mean(loss_vals)
    loss_std = np.std(loss_vals)
    
    # 计算 Loss 趋势 (线性回归斜率)
    if len(loss_vals) > 1:
        x = np.arange(len(loss_vals))
        slope = np.polyfit(x, loss_vals, 1)[0]
        # 计算 锯齿度 (相邻差绝对值之和)
        diffs = np.diff(loss_vals)
        jaggedness = np.sum(np.abs(diffs))
    else:
        slope = 0
        jaggedness = 0
    
    # 添加微量的测量噪声，防止特征过于完美
    noise = np.random.normal(0, 0.001, 6)
    
    features = [
        dt_mean, dt_std, 
        loss_mean, loss_std, 
        slope, jaggedness
    ]
    
    return (np.array(features) + noise).tolist()

# ==========================================
# 2. 主流程
# ==========================================

if __name__ == "__main__":
    input_file = "C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\1.Log ETL\\优化4\\federated_learning_structured.json"
    json_output = "lstm_feature_data.json"
    csv_output = "lstm_feature_visualization.csv"
    
    print(f"读取数据: {input_file} ...")
    with open(input_file, "r", encoding='utf-8') as f:
        data = json.load(f)
        
    processed = []
    max_len = 0
    
    print("开始提取特征...")
    for sess in data:
        logs = sess['logs']
        # 1. 先计算全局统计特征 (6维)
        global_feats = get_global_features(sess) 
        
        seq_features = []
        if logs:
            prev_ts = parse_ts(logs[0]['timestamp'])
            
            for i, log in enumerate(logs):
                curr_ts = parse_ts(log['timestamp'])
                
                # 2. 计算瞬时特征 (2维)
                dt = (curr_ts - prev_ts).total_seconds()
                loss = log['metrics']['val']
                
                # 3. 拼接: [dt, loss] + [mean, std, slope...] = 8维
                # 这样 LSTM 既能看到当前的波动，也能感知到整体的统计分布
                step_feat = [dt, loss] + global_feats
                seq_features.append(step_feat)
                
                prev_ts = curr_ts
        
        # 记录最大长度用于 padding
        if len(seq_features) > max_len:
            max_len = len(seq_features)
            
        processed.append({
            "session_id": sess['session_id'],
            "label": sess['label'],
            "client_type": sess['client_type'],
            "features": seq_features,
            "seq_len": len(seq_features)
        })
        
    # --- 保存 JSON (模型输入) ---
    with open(json_output, "w", encoding='utf-8') as f:
        json.dump(processed, f, indent=2)
    print(f"特征数据(JSON)已保存。特征维度: {len(ALL_FEATURE_NAMES)}")

    # --- 保存 CSV (可视化检查) ---
    print(f"生成 CSV 可视化报表 (Max Seq Len: {max_len})...")
    
    # 1. 构建表头
    # 格式: session_id, label, client_type, step_0_dt, step_0_loss, step_0_dt_mean...
    header = ["session_id", "label", "client_type"]
    for i in range(max_len):
        for name in ALL_FEATURE_NAMES:
            header.append(f"step_{i}_{name}")
            
    with open(csv_output, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        for item in processed:
            row = [item['session_id'], item['label'], item['client_type']]
            feats = item['features']
            
            # 2. 填充数据与 Padding
            for i in range(max_len):
                if i < len(feats):
                    row.extend(feats[i])
                else:
                    # 不足部分补 0
                    row.extend([0.0] * len(ALL_FEATURE_NAMES))
            
            writer.writerow(row)
            
    print(f"可视化报表(CSV)已保存至: {csv_output}")
    print("完成。建议在 CSV 中对比 'label=0' 和 'label=1' 的 'dt_std' 和 'loss_jaggedness' 列。")