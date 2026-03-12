'''
我们将引入两个机制来模糊“黑白”界限：
    1.恶意伪装（Adversarial Mimicry）：
        攻击者不再傻乎乎地暴露巨大的 Step Gap（步长跳跃）。
        攻击者会虚报进度：内部跑了 100 次迭代，日志却按顺序打印 "Epoch 1, Epoch 2..."。
        结果：恶意样本的 step_gap 变成了 1（和正常一样），只能靠极其微小的“计算节奏”差异来区分。

    2.正常噪声（Environmental Noise）：
        日志堆积（Log Burst）：模拟网络阻塞，正常节点瞬间吐出 3 条日志，导致 delta_time 极短（像攻击者）。
        丢包（Packet Loss）：正常节点偶尔丢失一条日志，导致 step_gap 变成 2（像攻击者）。
'''

import json
import random
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 配置参数
# ==========================================
NUM_SAMPLES = 1000  # 增加样本量以支持更细微的特征学习
MALICIOUS_RATIO = 0.4
START_TIME = datetime.strptime("2025-11-27 10:00:00", "%Y-%m-%d %H:%M:%S")

PHASE_START = "FL_CLIENT_START"
PHASE_COMPUTE = "LOCAL_COMPUTE"
PHASE_UPLOAD = "UPLOAD_UPDATE"

def generate_timestamp(base_time, offset_seconds):
    t = base_time + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def mock_normal_session(client_id, base_time):
    """
    模拟正常节点 (带环境噪声)
    干扰项：
    1. Log Burst: 网络卡顿导致日志时间戳挤在一起。
    2. Log Drop: 偶尔丢失日志，导致 Step Gap 异常。
    """
    logs = []
    current_offset = 0.0
    
    # 正常计算速度：0.2s - 1.5s
    compute_speed = random.uniform(0.2, 1.5)
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_START,
        "message": "Received model. Starting training.",
        "metrics": {"round": random.randint(1, 50)}
    })
    
    current_offset += 0.5
    epochs = random.randint(5, 15)
    loss = random.uniform(2.5, 1.5)
    
    for e in range(1, epochs + 1):
        # --- 噪声注入 1: 计算时间抖动 ---
        step_time = compute_speed + random.gauss(0, 0.05) 
        actual_time_passed = max(step_time, 0.01)
        current_offset += actual_time_passed
        
        loss = loss * 0.9 + random.uniform(-0.05, 0.05)
        
        # --- 噪声注入 2: 模拟丢包 (Log Drop) ---
        # 5% 的概率日志丢失，导致下一条日志的 Step Gap 变成 2
        if random.random() < 0.05:
            continue 

        # --- 噪声注入 3: 模拟日志堆积 (Log Burst) ---
        # 10% 的概率，记录的时间戳比实际发生时间晚（滞后），或者挤在一起
        display_offset = current_offset
        if random.random() < 0.1:
            # 模拟瞬间写入，delta_time 会变得极短 (0.001s)，非常像恶意的高频计算
            display_offset = current_offset - actual_time_passed + 0.001

        logs.append({
            "timestamp": generate_timestamp(base_time, display_offset),
            "level": "INFO",
            "client_id": client_id,
            "phase": PHASE_COMPUTE,
            "message": f"Epoch {e}/{epochs} completed.",
            "metrics": {
                "step_index": e,
                "loss_value": round(max(loss, 0), 4)
            }
        })

    # Upload
    current_offset += random.uniform(0.5, 2.0)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_UPLOAD,
        "message": "Upload success.",
        "metrics": {}
    })
    
    # 过滤掉乱序时间戳（简单处理）
    logs.sort(key=lambda x: x['timestamp'])
    return logs, 0

def mock_malicious_session(client_id, base_time):
    """
    模拟高阶恶意节点 (Adversarial Mimicry)
    伪装策略：
    1. 虚假 Step Index: 内部跑 100 步，日志里只打印 Step 1。
    2. 时间控制: 利用高性能计算让 100 步的耗时 ≈ 正常节点 1 步的耗时。
    难点：这会导致 Step Gap = 1 (完美伪装)，只能靠 Loss 的微观震荡特征区分。
    """
    logs = []
    current_offset = 0.0
    
    # 攻击者算力极强，但为了伪装，他会故意 sleep 或者插入无效计算
    # 最终表现出的“单步耗时”会落在正常节点的【下限区间】 (0.1s - 0.4s)
    # 这与正常节点的快设备 (0.2s) 高度重叠！
    mimic_speed = random.uniform(0.1, 0.4)
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_START,
        "message": "Received model. Starting training.",
        "metrics": {"round": random.randint(1, 50)}
    })
    
    current_offset += 0.5
    
    # 攻击者伪装成跑了 5-15 个 Epoch
    fake_epochs = random.randint(5, 15)
    
    # 但实际上他在做梯度反演，Loss 并不是平滑下降，而是剧烈震荡后收敛
    grad_loss = random.uniform(15.0, 25.0) # 初始值高
    
    for e in range(1, fake_epochs + 1):
        # 实际耗时 = 伪装速度
        current_offset += mimic_speed + random.gauss(0, 0.02)
        
        # --- 核心特征泄露点 (很难完全掩盖) ---
        # 恶意行为的 Loss 变化率 (Velocity) 与正常训练不同
        # 正常：Exp Decay; 恶意：Optimization Trajectory (可能先升后降，或剧烈抖动)
        grad_loss = grad_loss * 0.7 + random.uniform(-2.0, 2.0) # 巨大的震荡噪声
        if grad_loss < 0.5: grad_loss = random.uniform(0.5, 1.0) # 难以收敛到极小值
        
        logs.append({
            "timestamp": generate_timestamp(base_time, current_offset),
            "level": "INFO", # 完全伪装成 INFO
            "client_id": client_id,
            "phase": PHASE_COMPUTE,
            "message": f"Epoch {e}/{fake_epochs} completed.", # 消息也伪装
            "metrics": {
                "step_index": e,       # !!! 伪装：Step Index 连续 !!! (Gap = 1)
                "loss_value": round(grad_loss, 4) # 唯一的破绽是 Loss 的数值分布
            }
        })

    current_offset += random.uniform(1.0, 3.0)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_UPLOAD,
        "message": "Upload success.",
        "metrics": {}
    })
    
    return logs, 1

if __name__ == "__main__":
    data = []
    print("正在生成 V4.0 混淆对抗数据...")
    for i in range(NUM_SAMPLES):
        cid = f"Node_{i:04d}"
        bt = START_TIME + timedelta(seconds=i*3)
        
        if random.random() < MALICIOUS_RATIO:
            logs, label = mock_malicious_session(cid, bt)
            ctype = "malicious_mimic"
        else:
            logs, label = mock_normal_session(cid, bt)
            ctype = "normal_noisy"
            
        data.append({
            "session_id": str(i),
            "client_id": cid,
            "label": label,
            "client_type": ctype,
            "logs": logs
        })
        
    with open("federated_learning_structured.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"生成完成。样本数: {NUM_SAMPLES}。请注意：现在的特征重叠度非常高！")