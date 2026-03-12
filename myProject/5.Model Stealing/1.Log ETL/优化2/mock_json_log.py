'''
移除了所有“训练”和“文件保存”的显性日志。
增加了 Legit_Script（合法脚本）和 Smart_Attacker（聪明攻击者），两者的 QPS（每秒查询率）高度重叠。
'''

import json
import random
import uuid
import numpy as np
from datetime import datetime, timedelta

OUTPUT_FILE = "simulated_logs_hard.json"
# 增加样本量以支持更复杂的学习
NUM_NORMAL_HUMAN = 60      # 正常人类 (Easy Negative)
NUM_LEGIT_SCRIPT = 40      # 合法脚本 (Hard Negative - 干扰项)
NUM_SMART_ATTACKER = 40    # 聪明攻击者 (Hard Positive - 隐蔽项)

def get_timestamp(start_time, offset_seconds):
    return (start_time + timedelta(seconds=offset_seconds)).isoformat()

def generate_log(task_id, user_id, timestamp, event_type, details=None):
    return {
        "timestamp": timestamp,
        "task_id": task_id,
        "user_id": user_id,
        "level": "INFO",
        "event_type": event_type,
        "message": "Action performed",
        "details": details if details else {}
    }

# 1. 正常人类：完全随机，思考时间长，查询量极小
def sim_normal_human(start_time):
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"human_{random.randint(1000, 9999)}"
    t = 0.0
    
    logs.append(generate_log(task_id, user_id, get_timestamp(start_time, t), "task_start"))
    
    # 人类操作：加载数据 -> 思考(10-60s) -> 查询1次 -> 思考 -> 查询1次
    steps = random.randint(5, 15)
    for _ in range(steps):
        t += random.uniform(10.0, 60.0) # 长间隔
        logs.append(generate_log(task_id, user_id, get_timestamp(start_time, t), 
                                 "api_query", 
                                 {"count": 1, "latency_ms": random.randint(50, 200)}))
    
    return logs, "normal"

# 2. 合法脚本：高频，但极其规律（定时任务），目的是下载数据
# 这是最容易被误判为攻击的“难样本”
def sim_legit_script(start_time):
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"script_{random.randint(1000, 9999)}"
    t = 0.0
    
    logs.append(generate_log(task_id, user_id, get_timestamp(start_time, t), "task_start"))
    
    # 脚本特点：间隔非常固定 (例如每 1.0 秒整)，没有 jitter
    # 总量大，可能是几千次
    total_reqs = random.randint(500, 1000)
    interval = 1.0 # 固定间隔
    
    for i in range(total_reqs):
        t += interval
        # 偶尔会有网络波动
        if random.random() > 0.95: t += random.uniform(0.1, 0.5)
        
        logs.append(generate_log(task_id, user_id, get_timestamp(start_time, t), 
                                 "api_query", 
                                 {"count": 50, "latency_ms": random.randint(40, 100)}))
        
        # 模拟分批处理
        if i % 100 == 0:
            t += 5.0 # 处理数据耗时

    return logs, "normal" # 注意：这是正常用户！

# 3. 聪明攻击者：试图模仿人类，但为了效率必须比人类快
# 特征：有随机抖动 (Jitter)，但总体分布呈现某种统计学上的“不自然”
def sim_smart_attacker(start_time):
    logs = []
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    user_id = f"attacker_{random.randint(1000, 9999)}"
    t = 0.0
    
    logs.append(generate_log(task_id, user_id, get_timestamp(start_time, t), "task_start"))
    
    # 攻击者必须窃取足够的数据，所以总量不能太少，但也不能像脚本那么快
    total_reqs = random.randint(300, 800)
    
    for i in range(total_reqs):
        # 聪明攻击：使用泊松分布或高斯分布来伪造间隔，试图通过图灵测试
        # 均值 3秒，试图伪装成“快手人类”
        wait_time = abs(random.gauss(3.0, 1.5)) 
        if wait_time < 0.2: wait_time = 0.2
        t += wait_time
        
        # 每次查询量随机，伪装成探索
        batch_size = random.choices([1, 5, 10, 20], weights=[0.4, 0.3, 0.2, 0.1])[0]
        
        logs.append(generate_log(task_id, user_id, get_timestamp(start_time, t), 
                                 "api_query", 
                                 {"count": batch_size, "latency_ms": random.randint(50, 200)}))
        
        # 隐蔽训练：每隔一段时间会消失很久（在本地训练模型），服务端日志表现为 Long Idle
        if i > 0 and i % 150 == 0:
            t += random.uniform(20.0, 60.0) # 假装休息，实则训练

    return logs, "malicious"

if __name__ == "__main__":
    all_data = []
    
    print("Generating Human Users...")
    for _ in range(NUM_NORMAL_HUMAN):
        logs, label = sim_normal_human(datetime.now())
        all_data.append({"session_id": logs[0]['task_id'], "label": label, "logs": logs})
        
    print("Generating Legit Scripts (Hard Negatives)...")
    for _ in range(NUM_LEGIT_SCRIPT):
        logs, label = sim_legit_script(datetime.now())
        all_data.append({"session_id": logs[0]['task_id'], "label": label, "logs": logs})
        
    print("Generating Smart Attackers (Hard Positives)...")
    for _ in range(NUM_SMART_ATTACKER):
        logs, label = sim_smart_attacker(datetime.now())
        all_data.append({"session_id": logs[0]['task_id'], "label": label, "logs": logs})
    
    # 打乱数据
    random.shuffle(all_data)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2)
    
    print(f"Done. Generated {len(all_data)} sessions.")