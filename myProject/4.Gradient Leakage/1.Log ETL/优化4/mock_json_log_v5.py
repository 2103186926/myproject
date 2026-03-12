'''
在这个脚本中，我特意制造了严重的特征重叠。
    Normal (High Noise)：模拟网络极差的环境，日志时间戳乱跳（像攻击者的计算密集型特征），且Loss不下降（像攻击者的震荡）。
    Malicious (Deep Mimic)：攻击者计算出正常节点的平均耗时（比如0.5s），然后每算完一步就 sleep(0.5s)，且把 Loss 缩放到 [0, 3.0] 范围内。
'''

import json
import random
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# V5.0 配置：制造“难分难解”的局面
# ==========================================
NUM_SAMPLES = 1000 
MALICIOUS_RATIO = 0.5 
START_TIME = datetime.strptime("2025-11-27 10:00:00", "%Y-%m-%d %H:%M:%S")

# 统一阶段名，完全消除文本差异
PHASE_EXEC = "EXECUTION_STEP"

def get_time_str(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def mock_session(client_id, base_time, is_malicious):
    logs = []
    curr_time = base_time
    
    # === 混淆核心：设定基准节奏 ===
    # 无论是好人还是坏人，宏观节奏都强制设定在 0.5s 左右
    # 这样模型就无法通过“总时长”或“平均速度”来区分了
    target_interval = 0.5 
    
    # 模拟日志长度：都控制在 10-20 条之间
    # 攻击者通过 Log Suppression (日志抑制) 达到这一点
    seq_len = random.randint(10, 20)
    
    # 初始 Loss
    current_loss = random.uniform(2.0, 4.0)
    
    # === 差异化设计 (微观指纹) ===
    if not is_malicious:
        # --- 正常节点 ---
        # 特征：由于网络抖动，时间间隔是 正态分布 (Gaussian Noise)
        # Loss：趋势是下降的，但可能有波动
        client_type = "normal_jittery"
        
        for i in range(seq_len):
            # 正常节点的网络抖动很大：方差 0.2
            jitter = random.gauss(0, 0.2) 
            dt = max(0.05, target_interval + jitter)
            curr_time += timedelta(seconds=dt)
            
            # Loss 正常下降
            current_loss = current_loss * 0.9 + random.gauss(0, 0.05)
            
            logs.append({
                "timestamp": get_time_str(curr_time),
                "phase": PHASE_EXEC, # 只有这一个 Phase
                "metrics": {
                    "val": round(max(current_loss, 0), 4),
                    "seq": i + 1
                }
            })
            
    else:
        # --- 恶意节点 (完美伪装) ---
        # 特征：攻击者是机器控制的 sleep，时间间隔是 均匀分布 (Uniform Noise) 或 固定值
        # Loss：虽然被归一化了，但因为是梯度反演，很难像正常训练那样平滑，会有“锯齿”
        client_type = "malicious_mimic"
        
        # 攻击者内部跑了 500 步，但只打印 seq_len 条日志
        # 他通过 sleep 来凑时间
        
        for i in range(seq_len):
            # 攻击者的 Sleep 极其精准，误差极小：方差 0.01
            # !!! 这是模型唯一能学到的微弱特征：方差的差异 !!!
            mimic_jitter = random.uniform(-0.02, 0.02)
            dt = target_interval + mimic_jitter
            curr_time += timedelta(seconds=dt)
            
            # Loss 伪装：攻击者尝试把巨大的 Gradient Loss 缩放到 0-4 之间
            # 但很难消除非凸优化带来的“锯齿感” (上下跳动)
            current_loss = current_loss * 0.95 + random.uniform(-0.3, 0.3)
            if current_loss < 0.5: current_loss += 0.5
            
            logs.append({
                "timestamp": get_time_str(curr_time),
                "phase": PHASE_EXEC,
                "metrics": {
                    "val": round(current_loss, 4), # 数值范围与正常人完全重叠
                    "seq": i + 1
                }
            })

    return {
        "session_id": client_id,
        "label": 1 if is_malicious else 0,
        "client_type": client_type,
        "logs": logs
    }

if __name__ == "__main__":
    dataset = []
    for i in range(NUM_SAMPLES):
        is_mal = random.random() < MALICIOUS_RATIO
        data = mock_session(f"node_{i}", START_TIME, is_mal)
        dataset.append(data)
        
    with open("federated_learning_structured.json", "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"V5.0 混淆数据生成完毕。样本量: {NUM_SAMPLES}")
    print("特点：黑白样本的时长、条数、Loss范围几乎完全一致，仅剩微观统计规律差异。")