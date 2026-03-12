'''
脚本改进点：
    1.修复 Phase 不匹配：统一所有阶段名称，不再直接生成 ATTACK 关键字。
    2.实现日志降频：恶意节点内部跑 500 步，但只输出 5-10 条日志，掩盖其计算量。
    3.模拟异构算力：正常节点的计算速度随机化，制造“慢的正常节点”和“快的恶意节点”混杂的局面。
'''

import json
import random
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 配置参数
# ==========================================
NUM_SAMPLES = 500  # 增加样本量
MALICIOUS_RATIO = 0.4 
START_TIME = datetime.strptime("2025-11-27 10:00:00", "%Y-%m-%d %H:%M:%S")

# 统一的阶段名称，消除显式标签
PHASE_START = "FL_CLIENT_START"
PHASE_COMPUTE = "LOCAL_COMPUTE"
PHASE_UPLOAD = "UPLOAD_UPDATE"

def generate_timestamp(base_time, offset_seconds):
    t = base_time + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def mock_normal_session(client_id, base_time):
    """
    模拟正常节点：
    - 行为：老老实实跑 Epoch
    - 特征：Step Index 连续 (1, 2, 3...)
    - 异构性：计算速度波动大 (0.1s - 2.0s per step)
    """
    logs = []
    current_offset = 0.0
    
    # 模拟异构设备：有的快，有的慢
    device_speed = random.uniform(0.1, 2.0) 
    
    # 1. Start
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_START,
        "message": "Received model. Starting training.",
        "metrics": {"round": random.randint(1, 50)}
    })
    
    current_offset += 0.5
    
    # 2. Compute (Normal Epochs)
    # 正常训练 3-8 个 Epoch
    epochs = random.randint(3, 8)
    loss = random.uniform(2.5, 1.5)
    
    for e in range(1, epochs + 1):
        # 耗时 = 设备速度 + 随机扰动
        step_duration = device_speed + random.uniform(-0.05, 0.05)
        current_offset += max(step_duration, 0.01)
        
        # Loss 正常下降
        loss = loss * 0.8 + random.uniform(-0.02, 0.02)
        
        logs.append({
            "timestamp": generate_timestamp(base_time, current_offset),
            "level": "INFO", # 正常多用 INFO
            "client_id": client_id,
            "phase": PHASE_COMPUTE,
            "message": f"Epoch {e}/{epochs} completed.",
            "metrics": {
                "step_index": e,       # 关键特征：连续
                "loss_value": round(loss, 4)
            }
        })

    # 3. Upload
    current_offset += random.uniform(0.5, 1.5)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_UPLOAD,
        "message": "Upload success.",
        "metrics": {"upload_size_kb": 4500}
    })
    
    return logs, 0

def mock_malicious_session(client_id, base_time):
    """
    模拟隐蔽攻击者 (Stealthy Attacker)：
    - 行为：内部跑几百次迭代，但只打印几次日志（降频）。
    - 伪装：总耗时控制在正常范围内（通过高性能GPU加速）。
    - 漏洞：Step Index 跳跃 (0, 100, 200...) 或 Loss 轨迹异常。
    """
    logs = []
    current_offset = 0.0
    
    # 攻击者通常拥有高性能设备，单步计算极快
    attacker_speed = random.uniform(0.005, 0.02) 
    
    # 1. Start (伪装)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_START,
        "message": "Received model. Starting training.",
        "metrics": {"round": random.randint(1, 50)}
    })
    
    current_offset += 0.5
    
    # 2. Compute (Gradient Inversion Attack)
    # 内部需要跑很多次才能还原数据
    total_iterations = random.randint(300, 800)
    
    # 攻击者为了伪装，只打印 5-8 条日志，模仿正常节点的日志数量
    num_fake_logs = random.randint(3, 8)
    log_interval = total_iterations // num_fake_logs
    
    # 梯度匹配 Loss 起始值通常较高
    loss = random.uniform(10.0, 50.0)
    
    for i in range(1, total_iterations + 1):
        current_offset += attacker_speed # 累加微小的计算时间
        
        # 震荡下降的 Loss
        loss = loss * 0.9 + random.uniform(-0.5, 0.5)
        if loss < 0: loss = 0.001
        
        # 只在特定间隔打印日志 (Log Suppression)
        if i % log_interval == 0 or i == total_iterations:
            logs.append({
                "timestamp": generate_timestamp(base_time, current_offset),
                "level": "INFO", # 伪装成 INFO
                "client_id": client_id,
                "phase": PHASE_COMPUTE,
                # 攻击者可能忘记修改 message 中的计数器，或者必须记录真实进度供调试
                "message": f"Optimization step {i}/{total_iterations}", 
                "metrics": {
                    "step_index": i,       # 关键漏洞：步数跳跃很大 (如 100, 200)
                    "loss_value": round(loss, 4)
                }
            })

    # 3. Upload (Delayed)
    # 攻击者往往还要做些后处理（保存图片），导致 Upload 稍微慢一点点
    current_offset += random.uniform(2.0, 4.0)
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": PHASE_UPLOAD,
        "message": "Upload success.",
        "metrics": {"upload_size_kb": 4500}
    })
    
    return logs, 1

if __name__ == "__main__":
    data = []
    print("正在生成高阶对抗数据...")
    for i in range(NUM_SAMPLES):
        cid = f"Node_{i:03d}"
        bt = START_TIME + timedelta(seconds=i*5)
        
        if random.random() < MALICIOUS_RATIO:
            logs, label = mock_malicious_session(cid, bt)
            ctype = "malicious_stealthy"
        else:
            logs, label = mock_normal_session(cid, bt)
            ctype = "normal_heterogeneous"
            
        data.append({
            "session_id": str(i),
            "client_id": cid,
            "label": label,
            "client_type": ctype,
            "logs": logs
        })
        
    with open("federated_learning_structured.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"生成完成。样本数: {NUM_SAMPLES}")