# 平台日志流生成器：
# 它不再生成.log文件，而是直接生成一个platform_logs.jsonl文件（JSON Lines格式，每行一个JSON日志对象），其中混合了恶意任务和正常任务的完整日志流。
import json
import random
import uuid
import numpy as np
import time
from datetime import datetime, timezone

# 预设的一些海洋敏感区域坐标
SENSITIVE_AREAS = [
    (38.5, 122.0), (22.3, 114.2), (34.0, 135.0), (18.2, 120.5)
]

def get_iso_timestamp():
    """获取一个ISO 8601格式的时间戳"""
    return datetime.now(timezone.utc).isoformat()  # 返回当前时间的 ISO 8601 格式字符串

def write_log_entry(file_handle, event_type, context, details, service_name, level="INFO"):
    """向文件写入一个结构化的JSON日志条目"""
    log_entry = {
        "timestamp": get_iso_timestamp(),  # 生成当前时间的 ISO 8601 格式字符串
        "eventType": event_type,  # 事件类型，例如 "model_query"
        "logLevel": level,  # 日志级别，例如 "INFO", "WARNING", "ERROR"
        "serviceName": service_name,  # 服务名称，例如 "ModelPredictionService"
        "context": context,  # 上下文信息，例如 {"userId": "attacker_02", "jobId": "job-12345", "taskId": "task-67890", "sourceIp": "198.51.100.5"}
        "details": details  # 详细信息，例如 {"modelName": "ocean_ts_predictor_v2", "queryInput": {"latitude": 38.5, "longitude": 122.0, "depth": 0}, "queryStatus": "SUCCESS", "executionTimeMs": 245.3}
    }
    file_handle.write(json.dumps(log_entry) + '\n')
    # 模拟真实世界中日志之间存在的微小时间延迟
    time.sleep(random.uniform(0.001, 0.005))

def simulate_malicious_task(f, task_id):
    """
    模拟一个属性推断攻击任务的日志流。
    核心特征：在一个taskId内部，查询输入的统计分布发生系统性变化（例如从A点切换到B点）。
    """
    context = {"userId": "attacker_02", "jobId": f"job-{task_id[5:10]}", "taskId": task_id, "sourceIp": "198.51.100.5"}
    
    # 批次A的查询中心点
    center_A = random.choice(SENSITIVE_AREAS)
    # 批次B的查询中心点（与A点有细微但系统的差异）
    center_B = (center_A[0] + random.uniform(0.1, 0.3), center_A[1] + random.uniform(0.1, 0.3))
    
    # 1. 任务开始日志
    write_log_entry(f, "task_start", context, {
        "taskName": f"malicious_diff_query_{task_id}.py",
        "modelName": "ocean_ts_predictor_v2"
    }, "ComputationPlatform")

    # 2. 模拟批次A的查询 (N次查询)
    num_queries_A = random.randint(50, 100)
    for _ in range(num_queries_A):
        query_input = {
            "latitude": center_A[0] + random.uniform(-0.01, 0.01),
            "longitude": center_A[1] + random.uniform(-0.01, 0.01),
            "depth": random.choice([0, 10, 20])
        }
        status = "SUCCESS" if random.random() > 0.05 else "FAILURE"
        details = {
            "modelName": "ocean_ts_predictor_v2",
            "queryInput": query_input,
            "queryStatus": status,
            "executionTimeMs": abs(np.random.normal(loc=250, scale=30))
        }
        write_log_entry(f, "model_query", context, details, "ModelPredictionService")

    # 3. 模拟批次B的查询 (M次查询)
    num_queries_B = random.randint(50, 100)
    for _ in range(num_queries_B):
        query_input = {
            "latitude": center_B[0] + random.uniform(-0.01, 0.01),
            "longitude": center_B[1] + random.uniform(-0.01, 0.01),
            "depth": random.choice([0, 10, 20])
        }
        status = "SUCCESS" if random.random() > 0.05 else "FAILURE"
        details = {
            "modelName": "ocean_ts_predictor_v2",
            "queryInput": query_input,
            "queryStatus": status,
            "executionTimeMs": abs(np.random.normal(loc=260, scale=30)) # B批次的响应可能略有不同
        }
        write_log_entry(f, "model_query", context, details, "ModelPredictionService")

    # 4. 任务结束日志
    write_log_entry(f, "task_end", context, {
        "finalStatus": "COMPLETED",
        "totalQueries": num_queries_A + num_queries_B,
        "successfulQueries": int((num_queries_A + num_queries_B) * 0.95)
    }, "ComputationPlatform")

def simulate_benign_task(f, task_id):
    """
    模拟一个正常科研任务的日志流。
    核心特征：查询分布是单一的（要么分散，要么集中在一个点），且时间间隔不规律。
    """
    context = {"userId": "researcher_01", "jobId": f"job-{task_id[5:10]}", "taskId": task_id, "sourceIp": "203.0.113.20"}
    
    center_A = (random.uniform(20, 50), random.uniform(100, 150))
    is_focused_research = random.choice([True, False]) # 模拟两种正常任务
    
    # 1. 任务开始
    write_log_entry(f, "task_start", context, {
        "taskName": f"normal_analysis_{task_id}.py",
        "modelName": "ocean_ts_predictor_v2"
    }, "ComputationPlatform")

    # 2. 模拟查询
    num_queries = random.randint(20, 150)
    for _ in range(num_queries):
        if is_focused_research:
            # 集中在一个点的研究
            lat = center_A[0] + random.uniform(-0.02, 0.02)
            lon = center_A[1] + random.uniform(-0.02, 0.02)
        else:
            # 大范围区域研究
            lat = center_A[0] + random.uniform(-2.0, 2.0)
            lon = center_A[1] + random.uniform(-2.0, 2.0)
            
        query_input = { "latitude": lat, "longitude": lon, "depth": random.choice([0, 50, 100])}
        status = "SUCCESS" if random.random() > 0.02 else "FAILURE"
        details = {
            "modelName": "ocean_ts_predictor_v2",
            "queryInput": query_input,
            "queryStatus": status,
            "executionTimeMs": abs(np.random.normal(loc=300, scale=50))
        }
        
        # 模拟“查询-思考-查询”的模式，时间间隔长且不规律
        time.sleep(random.uniform(0.5, 3.0)) 
        
        write_log_entry(f, "model_query", context, details, "ModelPredictionService")

    # 3. 任务结束
    write_log_entry(f, "task_end", context, {
        "finalStatus": "COMPLETED",
        "totalQueries": num_queries,
        "successfulQueries": int(num_queries * 0.98)
    }, "ComputationPlatform")

if __name__ == "__main__":
    NUM_MALICIOUS = 50  # 恶意任务数量
    NUM_BENIGN = 50  # 正常任务数量
    OUTPUT_FILE = "platform_logs.jsonl"
    
    task_list = []
    for _ in range(NUM_MALICIOUS):
        task_list.append(("malicious", f"task-{uuid.uuid4().hex[:12]}"))
    for _ in range(NUM_BENIGN):
        task_list.append(("benign", f"task-{uuid.uuid4().hex[:12]}"))
        
    random.shuffle(task_list) # 打乱任务执行顺序
    
    print(f"Generating platform logs for {len(task_list)} tasks into '{OUTPUT_FILE}'...")
    
    with open(OUTPUT_FILE, 'w') as f:
        for task_type, task_id in task_list:
            if task_type == "malicious":
                simulate_malicious_task(f, task_id)
            else:
                simulate_benign_task(f, task_id)
                
    print("Log generation complete.")