'''
引入了 Stealthy Attacker (隐蔽攻击者) 和 Power User (高频正常用户)，让两者难以区分。
'''

import json
import random
import uuid
from datetime import datetime, timedelta

# 配置
OUTPUT_FILE = "simulated_logs.json"
NUM_NORMAL_SESSIONS = 80
NUM_POWER_USER_SESSIONS = 20  # 新增：高频正常用户 (容易误报)
NUM_STEALTHY_ATTACKER_SESSIONS = 30 # 新增：隐蔽攻击者 (难以检测)

def get_timestamp(start_time, offset_seconds):
    current_time = start_time + timedelta(seconds=offset_seconds)
    return current_time.isoformat()

def generate_base_log(task_id, user_id, timestamp, event_type, message, details=None):
    return {
        "timestamp": timestamp,
        "task_id": task_id,
        "user_id": user_id,
        "level": "INFO",
        "event_type": event_type,
        "message": message,
        "details": details if details else {}
    }

# --- 场景 1: 普通科研用户 (小白) ---
def simulate_normal_session(start_time):
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"user_{random.randint(1000, 5000)}"
    t = 0

    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "task_start", "Task started"))
    
    t += random.uniform(1, 3)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "data_load", "Loading local dataset", {"file_type": "csv", "size_mb": 15}))

    # 正常用户：手动查询，只有几次，且间隔不规律
    for _ in range(random.randint(2, 5)):
        t += random.uniform(5, 15) # 思考时间长
        q_count = random.randint(1, 3)
        logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "model_inference", "Manual inference", {"query_count": q_count, "strategy": "manual"}))

    t += random.uniform(2, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "file_save", "Saving plot", {"file_ext": ".png"}))
    
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t+1), "task_end", "Task completed"))
    return logs, "normal"

# --- 场景 2: 专家用户 (Power User - 干扰项) ---
# 特征：虽然查询量大，但没有训练行为，且文件后缀正常
def simulate_power_user_session(start_time):
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"power_user_{random.randint(8000, 9999)}"
    t = 0

    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "task_start", "Batch Validation Task"))
    
    t += random.uniform(1, 3)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "data_load", "Loading validation set", {"file_type": "nc", "size_mb": 1200}))

    # 专家用户：批量验证，查询量可能达到 50-100，接近隐蔽攻击者
    num_batches = random.randint(5, 10)
    for i in range(num_batches):
        t += random.uniform(1, 4) # 机器执行，间隔较短
        q_count = random.randint(20, 50) # 较大的查询量
        logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "model_inference", "Batch validation inference", {"query_count": q_count, "strategy": "validation_script"}))
        
        # 偶尔做个处理
        if i % 3 == 0:
            t += 0.5
            logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "data_processing", "Calculating validation metrics"))

    t += random.uniform(2, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "file_save", "Saving validation report", {"file_ext": ".pdf"}))
    
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t+1), "task_end", "Task completed"))
    return logs, "normal"

# --- 场景 3: 隐蔽攻击者 (Stealthy Attacker) ---
# 特征：小步快跑，伪装成正常操作，混淆视听
def simulate_stealthy_attacker_session(start_time):
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"attacker_{random.randint(100, 999)}"
    t = 0

    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "task_start", "Data Analysis"))

    # 伪装：假装加载数据
    t += random.uniform(1, 3)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), "data_load", "Loading dataset", {"file_type": "csv", "size_mb": 50}))

    # 隐蔽生成输入 (不记录明确的 input_generation 事件，或者混在 inference 前)
    
    current_queries = 0
    r2_score = 0.2
    
    # 攻击循环：拆分成很多小批次，每次只查 20-40 个，甚至混入 data_processing
    target_total = random.randint(800, 1500) # 总量不大，但足以训练一个粗糙模型
    batch_size_base = 30
    
    while current_queries < target_total:
        t += random.uniform(2.0, 5.0) # 故意拉长时间间隔，模仿人类或避免速率限制
        
        real_batch = batch_size_base + random.randint(-10, 10)
        logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                      "model_inference", "Running analysis on subset", 
                                      {"query_count": real_batch, "strategy": "manual"})) # 伪装成 manual
        current_queries += real_batch

        # 伪装行为：插入虚假的数据处理日志
        if random.random() > 0.6:
            t += random.uniform(0.5, 2.0)
            logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                          "data_processing", "Visualizing intermediate results"))

        # 隐蔽训练：并不总是记录训练日志，或者记录得很隐晦
        # 只有当收集了一定数量后才训练一次
        if current_queries % 300 < 50 and current_queries > 200:
            t += random.uniform(5, 10)
            r2_score += random.uniform(0.05, 0.1)
            r2_score = min(r2_score, 0.9)
            # 攻击者可能不打印 "Training substitute model"，而是打印 "Model calibration" 等中性词
            logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                          "model_training", "Calibrating local model", 
                                          {"r2_score": round(r2_score, 4)}))

    # 结尾：保存模型，但不一定是 .joblib，可能是伪装成 .dat 或无后缀
    t += random.uniform(2, 5)
    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t), 
                                  "file_save", "Saving calibration data", 
                                  {"filename": "calibration_v1.dat", "file_ext": ".dat"})) # 混淆视听

    logs.append(generate_base_log(task_id, user_id, get_timestamp(start_time, t+1), "task_end", "Task completed"))
    return logs, "malicious"

if __name__ == "__main__":
    all_data = []
    print(f"Generating Normal Users: {NUM_NORMAL_SESSIONS}")
    for _ in range(NUM_NORMAL_SESSIONS):
        logs, label = simulate_normal_session(datetime.now())
        all_data.append({"session_id": logs[0]['task_id'], "label": label, "logs": logs})

    print(f"Generating Power Users (High Noise): {NUM_POWER_USER_SESSIONS}")
    for _ in range(NUM_POWER_USER_SESSIONS):
        logs, label = simulate_power_user_session(datetime.now())
        all_data.append({"session_id": logs[0]['task_id'], "label": label, "logs": logs})

    print(f"Generating Stealthy Attackers: {NUM_STEALTHY_ATTACKER_SESSIONS}")
    for _ in range(NUM_STEALTHY_ATTACKER_SESSIONS):
        logs, label = simulate_stealthy_attacker_session(datetime.now())
        all_data.append({"session_id": logs[0]['task_id'], "label": label, "logs": logs})

    random.shuffle(all_data)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"Done! {len(all_data)} sessions saved.")