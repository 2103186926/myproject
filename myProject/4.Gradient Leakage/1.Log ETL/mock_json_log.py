import json
import random
import time
from datetime import datetime, timedelta
import numpy as np

# ==========================================
# 配置参数
# ==========================================
NUM_SAMPLES = 200  # 总共模拟多少个客户端的任务序列
MALICIOUS_RATIO = 0.3  # 恶意客户端占比 30%
START_TIME = datetime.strptime("2025-11-27 10:00:00", "%Y-%m-%d %H:%M:%S")

# 特征配置 (基于文档 3.4 梯度窃取攻击)
NORMAL_EPOCHS = 5
ATTACK_ITERATIONS = 500  #  攻击需要成千上万次前向传播
NORMAL_DURATION_MEAN = 1.5  # 秒
ATTACK_DURATION_MEAN = 25.0 # 秒  本地计算时间显著长于正常节点

def generate_timestamp(base_time, offset_seconds):
    """生成带偏移的时间字符串"""
    t = base_time + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

def mock_normal_session(client_id, base_time):
    """
    模拟正常客户端的日志序列
    特征：
    1. 周期短
    2. Prediction Loss 逐步下降
    3. 几乎无上传延迟
    """
    logs = []
    current_offset = 0.0
    
    # 1. 收到模型
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "TRAINING_START",
        "message": "Received global model. Starting local training (Standard FL).",
        "metrics": {"round": random.randint(1, 10)}
    })
    
    current_offset += 0.2
    
    # 2. 正常训练循环 (Epochs)
    current_loss = 3.0
    for epoch in range(1, NORMAL_EPOCHS + 1):
        current_offset += random.uniform(0.2, 0.4) # 每个Epoch耗时很短
        # Loss 模拟下降
        current_loss = current_loss * 0.7 + random.uniform(0.01, 0.05)
        
        logs.append({
            "timestamp": generate_timestamp(base_time, current_offset),
            "level": "DEBUG",
            "client_id": client_id,
            "phase": "TRAINING_EPOCH",
            "message": f"Training Epoch {epoch}/{NORMAL_EPOCHS}",
            "metrics": {
                "epoch": epoch,
                "loss_type": "prediction_loss",
                "loss_value": round(current_loss, 4)
            }
        })
    
    current_offset += 0.1
    
    # 3. 训练结束 & 上传
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "TRAINING_END",
        "message": "Local training finished. Uploading model updates.",
        "metrics": {}
    })
    
    current_offset += 0.1 # 正常上传很快
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "UPLOAD_SUCCESS",
        "message": "Upload successfully completed.",
        "metrics": {"duration": round(current_offset, 2)}
    })
    
    return logs, 0  # 0 表示 label 为正常

def mock_malicious_session(client_id, base_time):
    """
    模拟梯度窃取攻击的日志序列
    特征：
    1.  计算密集型优化循环 (ITERATION 0-500)
    2.  本地计算时间异常长
    3.  上传延迟 (Straggler)
    4.  Gradient Loss 而非 Prediction Loss
    """
    logs = []
    current_offset = 0.0
    
    # 1. 收到模型 (伪装开始)
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "TRAINING_START",
        "message": "Received global model. Starting local training (Malicious).",
        "metrics": {"round": random.randint(1, 10)}
    })
    
    current_offset += 0.2
    
    # 2. 伪装结束，进入攻击阶段
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "ATTACK_START",
        "message": "Local training finished. Moving to gradient analysis phase.", # [cite: 66]
        "metrics": {}
    })
    
    current_offset += 0.05
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "ATTACK",  # 显式攻击标识 (在真实日志中可能被隐藏，但这里为了特征工程保留)
        "client_id": client_id,
        "phase": "ATTACK_INIT",
        "message": "Launch: Gradient Leakage Attack initiated.", # [cite: 67]
        "metrics": {"target": "Minimizing Gradient Matching Loss"}
    })
    
    # 3. 攻击优化循环 (模拟耗时和大量日志)
    grad_loss = 20.0
    # 为了节省文件大小，我们只生成部分关键帧，但时间跨度拉大
    steps = [0, 50, 100, 200, 300, 400, 500] 
    
    for step in steps:
        # 时间跨度显著增加，模拟计算耗时
        current_offset += random.uniform(2.0, 4.0) 
        grad_loss = grad_loss * 0.8  # 梯度匹配Loss下降
        
        logs.append({
            "timestamp": generate_timestamp(base_time, current_offset),
            "level": "DEBUG",
            "client_id": client_id,
            "phase": "ATTACK_ITERATION",
            "message": f"ITERATION {step}/{ATTACK_ITERATIONS}",
            "metrics": {
                "iteration": step,
                "loss_type": "gradient_loss", # [cite: 69]
                "loss_value": round(grad_loss, 6),
                "tv_loss": 0.00123
            }
        })

    # 4. 攻击结束 & IO 操作
    current_offset += 0.5
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "WARNING",
        "client_id": client_id,
        "phase": "FILE_IO",
        "message": f"Stolen data saved as reconstructed_data_{client_id}.npy.", # [cite: 81]
        "metrics": {"file_type": "npy"}
    })
    
    # 5. 延迟上传 (Straggler)
    delay = random.uniform(1.0, 3.0) # 额外的网络处理延迟
    current_offset += delay
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset),
        "level": "INFO",
        "client_id": client_id,
        "phase": "UPLOAD_ATTEMPT",
        "message": "Uploading final model updates...",
        "metrics": {}
    })
    
    logs.append({
        "timestamp": generate_timestamp(base_time, current_offset + 0.5),
        "level": "WARNING",
        "client_id": client_id,
        "phase": "UPLOAD_DELAY",
        "message": "Upload delay detected. Straggler identified.", # [cite: 83]
        "metrics": {"duration": round(current_offset, 2), "lag": round(current_offset - NORMAL_DURATION_MEAN, 2)}
    })

    return logs, 1 # 1 表示 Label 为恶意

if __name__ == "__main__":
    all_data = []
    
    for i in range(NUM_SAMPLES):
        client_id = f"Node_{i:03d}"
        base_time = START_TIME + timedelta(seconds=i*5) # 错峰开始
        
        if random.random() < MALICIOUS_RATIO:
            session_logs, label = mock_malicious_session(client_id, base_time)
            client_type = "malicious"
        else:
            session_logs, label = mock_normal_session(client_id, base_time)
            client_type = "normal"
            
        # 将单个 Session 封装，方便后续 LSTM 按 Session 读取
        session_record = {
            "session_id": str(i),
            "client_id": client_id,
            "label": label, # 0: Normal, 1: Malicious
            "client_type": client_type,
            "logs": session_logs
        }
        all_data.append(session_record)
        
    # 保存为 JSON 文件
    with open("federated_learning_structured.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
        
    print(f"模拟完成：生成 {NUM_SAMPLES} 条Session数据，保存至 federated_learning_structured.json")