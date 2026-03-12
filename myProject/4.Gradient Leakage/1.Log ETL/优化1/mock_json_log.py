'''
主要改进点：
    1.去标签化（Camouflage）：恶意节点不再生成 ATTACK 级别的日志，而是伪装成 DEBUG/INFO。
    2.混淆相位（Phase Obfuscation）：攻击者的“梯度反演迭代”不再叫 ATTACK_ITERATION，而是伪装成正常的“子任务处理”或“内部优化” (LOCAL_OPTIMIZATION)，甚至直接复用 TRAINING_EPOCH 但参数异常。
    3.模糊样本（Fuzzy Samples）：
        Normal Straggler（拖尾的正常节点）：模拟网络差或计算慢的正常节点，耗时长，容易被误报为恶意。
        Stealthy Attacker（隐蔽的攻击者）：攻击者刻意降低日志频率，试图在时间分布上模仿正常节点。
'''

import json
import random
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 配置参数
# ==========================================
NUM_SAMPLES = 1000
MALICIOUS_RATIO = 0.3 
STRAGGLER_RATIO = 0.2  # 20% 的正常节点是“慢节点”（混淆样本）

START_TIME = datetime.strptime("2025-11-27 10:00:00", "%Y-%m-%d %H:%M:%S")

def generate_timestamp(base_time, offset_seconds):
    t = base_time + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def mock_normal_session(client_id, base_time, is_straggler=False):
    """
    模拟正常节点。
    is_straggler=True: 模拟计算能力弱或网络差的节点，耗时极长，用于制造假阳性干扰。
    """
    logs = []
    current_offset = 0.0
    
    # 速度因子：正常节点快(0.2s/step)，慢节点慢(3.0s/step)
    speed_factor = random.uniform(2.0, 5.0) if is_straggler else random.uniform(0.1, 0.5)
    
    # 1. Start
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "TRAINING_START", # 标准阶段名
        "message": "Received global model. Starting standard local training.",
        "metrics": {"round": random.randint(1, 100)}
    })
    
    current_offset += 0.5
    
    # 2. Training Loop (Epochs)
    # 正常训练 Epoch 数通常较少 (1-10)
    num_epochs = random.randint(1, 10)
    current_loss = random.uniform(2.0, 3.0)
    
    for epoch in range(1, num_epochs + 1):
        step_time = speed_factor + random.uniform(0.01, 0.1)
        current_offset += step_time
        
        # 正常 Loss 下降曲线：平滑下降
        current_loss = current_loss * 0.85 + random.uniform(0.0, 0.05)
        
        logs.append({
            "timestamp": generate_timestamp(base_time, current_offset),
            "level": "DEBUG", # 正常级别
            "client_id": client_id,
            "phase": "TRAINING_STEP", # 统称为 STEP，不区分是 Epoch 还是 Iteration
            "message": f"Local training epoch {epoch}/{num_epochs}",
            "metrics": {
                "step_index": epoch,
                "loss_value": round(current_loss, 4)
                # 注意：移除了 loss_type，模拟真实日志不一定有显式类型
            }
        })

    # 3. End & Upload
    current_offset += 0.2
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "TRAINING_END",
        "message": "Local training finished. Preparing updates.",
        "metrics": {}
    })
    
    # Straggler 可能会在上传阶段卡很久
    upload_time = random.uniform(5.0, 10.0) if is_straggler else random.uniform(0.5, 2.0)
    current_offset += upload_time
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "UPLOAD_SUCCESS",
        "message": "Model weights uploaded.",
        "metrics": {"duration_sec": round(current_offset, 2)}
    })
    
    return logs, 0  # Label: Normal

def mock_malicious_session(client_id, base_time):
    """
    模拟梯度窃取攻击者。
    特征改进：
    1. 伪装成 DEBUG/INFO 级别。
    2. 使用模糊的 Phase 名称 (LOCAL_OPTIMIZATION)。
    3. Loss 曲线震荡或数值异常，但不再有 loss_type 标签。
    """
    logs = []
    current_offset = 0.0
    
    # 1. Start (伪装)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "TRAINING_START",
        "message": "Received global model. Starting standard local training.", # 消息完全伪装
        "metrics": {"round": random.randint(1, 100)}
    })
    
    current_offset += 0.2
    
    # 2. Attack Loop (Hidden as "Internal Optimization")
    # 攻击需要大量迭代 (100 - 500)
    attack_iterations = random.randint(100, 500)
    
    # 攻击者的 Loss (Gradient Matching Loss) 通常起始值较高，下降方式不同
    grad_loss = random.uniform(10.0, 20.0) 
    
    # 攻击者为了隐蔽，可能不会每一步都打印日志，而是每隔几步打印一次
    log_interval = 20 
    
    for i in range(attack_iterations):
        # 计算极其密集，耗时很短 (CPU/GPU 满载)
        current_offset += random.uniform(0.02, 0.05) 
        
        grad_loss = grad_loss * 0.9 + random.uniform(-0.1, 0.1) # 震荡下降
        
        if i % log_interval == 0:
            logs.append({
                "timestamp": generate_timestamp(base_time, current_offset),
                "level": "DEBUG", # 伪装成 DEBUG
                "client_id": client_id,
                "phase": "TRAINING_STEP", # 混淆：也叫 STEP，让特征工程无法通过名字区分
                "message": f"Internal optimization step {i}/{attack_iterations}", # 模糊描述
                "metrics": {
                    "step_index": i,
                    "loss_value": round(max(grad_loss, 0.001), 4) # 只有数值差异
                }
            })

    # 3. End (File IO Anomaly - 唯一的显式漏洞，但混在日志里)
    current_offset += 0.5
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "DEBUG", # 降级为 DEBUG
        "client_id": client_id,
        "phase": "CACHE_FLUSH", # 伪装成缓存清理
        "message": f"Temporary results dumped to {client_id}_tmp.npy", # 仍然保留 .npy 写入特征
        "metrics": {"size_mb": 12.5}
    })
    
    # 4. Delayed Upload (由于攻击计算耗时久，总时长会变长)
    current_offset += random.uniform(1.0, 3.0)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "UPLOAD_SUCCESS",
        "message": "Model weights uploaded.",
        "metrics": {"duration_sec": round(current_offset, 2)}
    })
    
    return logs, 1 # Label: Malicious

if __name__ == "__main__":
    all_data = []
    
    for i in range(NUM_SAMPLES):
        client_id = f"Node_{i:03d}"
        base_time = START_TIME + timedelta(seconds=i*2)
        
        # 随机生成样本
        rand = random.random()
        if rand < MALICIOUS_RATIO:
            session_logs, label = mock_malicious_session(client_id, base_time)
            client_type = "malicious"
        elif rand < (MALICIOUS_RATIO + STRAGGLER_RATIO):
            session_logs, label = mock_normal_session(client_id, base_time, is_straggler=True)
            client_type = "normal_straggler"
        else:
            session_logs, label = mock_normal_session(client_id, base_time, is_straggler=False)
            client_type = "normal_fast"
            
        all_data.append({
            "session_id": str(i),
            "client_id": client_id,
            "label": label,
            "client_type": client_type,
            "logs": session_logs
        })
        
    with open("federated_learning_structured.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
        
    print(f"生成完成: {NUM_SAMPLES} 条样本 (含正常、慢速正常、隐蔽攻击)。")