import json
import random
import time
import os
import uuid
from datetime import datetime, timedelta

# 配置
OUTPUT_FILE = "simulated_logs.json"
NUM_NORMAL_SESSIONS = 100   # 正常用户会话数量
NUM_MALICIOUS_SESSIONS = 20 # 恶意攻击会话数量 (数据不平衡是常态)

def get_timestamp(start_time, offset_seconds):
    """生成ISO格式时间戳"""
    current_time = start_time + timedelta(seconds=offset_seconds)
    return current_time.isoformat()

def generate_base_log(task_id, user_id, timestamp, event_type, message, details=None):
    """构建标准JSON日志对象"""
    return {
        "timestamp": timestamp,
        "task_id": task_id,
        "user_id": user_id,
        "level": "INFO",
        "event_type": event_type, # 关键字段：用于区分动作类型 (e.g., api_query, model_training)
        "message": message,
        "details": details if details else {} # 关键字段：存储数值特征
    }

def simulate_normal_session(start_time):
    """
    模拟正常科研任务：数据加载 -> 少量推理 -> 可视化 -> 报告
    """
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"user_{random.randint(1000, 9999)}"
    t = 0 # 时间偏移

    # 1. 任务开始
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "task_start", "Task started: Ocean_Current_Analysis"))
    
    # 2. 数据加载 (Data Loading)
    t += random.uniform(1, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "data_load", "Loading dataset from storage", 
                                  {"file_type": "nc", "size_mb": 450}))

    # 3. 模型推理 (Model Inference) - 正常任务通常只做少量几次推理
    t += random.uniform(10, 20)
    inference_count = random.randint(1, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "model_inference", f"Running inference on {inference_count} regions", 
                                  {"model": "wave_forecast_v3", "query_count": inference_count, "strategy": "manual"}))

    # 4. 结果处理/可视化 (Visualization)
    t += random.uniform(5, 10)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "data_processing", "Generating heatmap visualization",
                                  {"output_type": "image"}))

    # 5. 文件保存 (File IO) - 保存的是图片或PDF
    t += random.uniform(2, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "file_save", "Saving analysis report", 
                                  {"filename": "report_2023.pdf", "file_ext": ".pdf"}))
    
    t += 1
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "task_end", "Task completed successfully", {"status": "success"}))
    
    return logs, "normal"

def simulate_malicious_session(start_time):
    """
    模拟模型窃取攻击：输入生成 -> 高频批量推理 -> 替代模型训练 -> 模型保存
    """
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"attacker_{random.randint(100, 999)}" # 模拟攻击者ID
    t = 0

    # 1. 任务开始
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "task_start", "Task started: Data_Collection_Worker"))

    # 2. 生成对抗样本/查询输入 (Input Generation)
    t += random.uniform(1, 3)
    target_queries = random.randint(10000, 50000)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "input_generation", "Generating query inputs", 
                                  {"strategy": "adaptive", "count": target_queries}))

    # 3. 循环：批量推理 + 替代模型训练
    current_queries = 0
    r2_score = 0.3
    batch_size = 1000
    num_batches = 10 # 模拟显示10个批次的循环过程

    for i in range(num_batches):
        # 3.1 批量推理 (High Frequency Inference)
        t += random.uniform(0.5, 2.0)
        current_queries += batch_size
        logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                      "model_inference", "Querying target model batch", 
                                      {"model": "wave_forecast_v3", "query_count": batch_size, "strategy": "batch", "total_stolen": current_queries}))

        # 3.2 替代模型训练 (Substitute Model Training) - 间歇性出现
        if i % 3 == 0 and i > 0:
            t += random.uniform(2, 5)
            r2_score += random.uniform(0.1, 0.2)
            r2_score = min(r2_score, 0.98)
            logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                          "model_training", "Training substitute model", 
                                          {"model_type": "RandomForest", "r2_score": round(r2_score, 4)}))

        # 3.3 主动延迟 (Evasion)
        t += random.uniform(1.0, 3.0) 

    # 4. 模型保存 (File IO) - 保存的是模型文件
    t += random.uniform(2, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "file_save", "Saving final substitute model", 
                                  {"filename": "stolen_model.joblib", "file_ext": ".joblib"}))
    
    # 5. 数据集保存
    t += 0.5
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "file_save", "Saving stolen dataset", 
                                  {"filename": "stolen_data.csv", "file_ext": ".csv"}))

    t += 1
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "task_end", "Task completed", {"status": "success"}))

    return logs, "malicious"

if __name__ == "__main__":
    all_data = []
    
    print(f"Generating {NUM_NORMAL_SESSIONS} normal sessions...")
    for _ in range(NUM_NORMAL_SESSIONS):
        start = datetime.now() - timedelta(days=random.randint(0, 7))
        session_logs, label = simulate_normal_session(start)
        # 将整个会话作为一个样本，包含日志列表和标签
        all_data.append({
            "session_id": session_logs[0]['task_id'],
            "label": label, # 0 for normal, 1 for malicious (后续处理转)
            "logs": session_logs
        })

    print(f"Generating {NUM_MALICIOUS_SESSIONS} malicious sessions...")
    for _ in range(NUM_MALICIOUS_SESSIONS):
        start = datetime.now() - timedelta(days=random.randint(0, 7))
        session_logs, label = simulate_malicious_session(start)
        all_data.append({
            "session_id": session_logs[0]['task_id'],
            "label": label,
            "logs": session_logs
        })

    # 打乱顺序
    random.shuffle(all_data)

    # 保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)

    print(f"Done! Saved {len(all_data)} sessions to {OUTPUT_FILE}")