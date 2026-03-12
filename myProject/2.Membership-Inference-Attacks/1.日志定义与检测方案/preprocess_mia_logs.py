# 这个脚本会扫描 scenarios 文件夹中所有的 .log 文件，使用正则表达式解析每一个文件，并根据您定义的JSON格式生成对应的 .json 结构化日志。

import os
import re
import json
import numpy as np
import glob
import random
from datetime import datetime, timedelta
import uuid

def parse_log_file(log_path):
    """解析单个日志文件并返回结构化JSON事件列表"""
    
    with open(log_path, 'r') as f:
        content = f.read()

    # --- Step 1: 使用正则表达式提取所有关键信息 ---
    
    # 提取目标模型
    model_match = re.search(r"Starting Membership Inference Attack for model '(.+?)'", content)
    target_model = model_match.group(1) if model_match else "unknown_model"

    # 提取所有查询信息
    query_matches = re.findall(r"Query \d+/\d+ - Features: (\[.*?\]) - Confidence: ([\d.]+), Predicted Class: (\d+)", content)
    
    # 提取总执行时间
    time_match = re.search(r"Execution time: ([\d.]+) seconds", content)
    total_execution_time = float(time_match.group(1)) if time_match else 0.0

    # 检查是否训练了攻击模型
    attack_model_trained = "[+] Training the membership inference attack model" in content

    # --- Step 2: 基于提取的信息构建JSON事件 ---

    events = []
    
    # 生成一些模拟的上下文信息
    user_id = f"attacker_{random.randint(1, 10)}"
    job_id = f"job_{uuid.uuid4().hex[:6]}"
    task_id = f"task_{uuid.uuid4().hex[:10]}"
    source_ip = f"203.0.113.{random.randint(10, 50)}"

    context = {"userId": user_id, "jobId": job_id, "taskId": task_id, "sourceIp": source_ip}
    
    # 计算时间戳
    end_time = datetime.now()
    start_time = end_time - timedelta(seconds=total_execution_time)
    
    # 1. 创建 task_start 事件
    events.append({
        "timestamp": start_time.isoformat() + "Z",
        "eventType": "task_start",
        "logLevel": "INFO",
        "serviceName": "ComputationPlatform",
        "context": context,
        "details": {
            "taskName": os.path.basename(log_path).replace('.log', '.py'),
            "targetModel": target_model,
            "targetSampleHash": "a1b2c3d4e5f6..." # 模拟哈希值
        }
    })

    # 2. 创建所有 model_query 事件
    confidences = []
    time_per_query = total_execution_time / len(query_matches) if query_matches else 1
    
    for i, match in enumerate(query_matches):
        feature_vector_str, confidence_str, pred_class_str = match
        confidences.append(float(confidence_str))
        
        query_time = start_time + timedelta(seconds=(i+1)*time_per_query)

        events.append({
            "timestamp": query_time.isoformat() + "Z",
            "eventType": "model_query",
            "logLevel": "INFO",
            "serviceName": "ModelPredictionService",
            "context": context,
            "details": {
                "modelName": target_model,
                "queryInput": {
                    "featureVector": json.loads(feature_vector_str) # 将字符串列表转为真实列表
                },
                "queryResponse": {
                    "confidence": float(confidence_str),
                    "predictedClass": int(pred_class_str)
                },
                "executionTimeMs": round(random.uniform(30, 60), 2)
            }
        })
    
    # 3. 如果检测到，创建 internal_activity 事件
    if attack_model_trained:
        activity_time = start_time + timedelta(seconds=total_execution_time * 0.8) # 估算时间
        events.append({
            "timestamp": activity_time.isoformat() + "Z",
            "eventType": "internal_activity",
            "logLevel": "WARN",
            "serviceName": "ComputationPlatform",
            "context": context,
            "details": {
                "activityType": "attack_model_training",
                "activityDescription": "Task initiated training of a local RandomForestClassifier model."
            }
        })

    # 4. 创建 task_end 事件
    # 计算聚合统计信息
    confidence_variance = float(np.var(confidences)) if confidences else 0.0
    
    events.append({
        "timestamp": end_time.isoformat() + "Z",
        "eventType": "task_end",
        "logLevel": "INFO",
        "serviceName": "ComputationPlatform",
        "context": context,
        "details": {
            "finalStatus": "COMPLETED",
            "totalQueries": len(query_matches),
            "totalExecutionTimeSec": total_execution_time,
            "summaryStats": {
                "confidenceVariance": round(confidence_variance, 6),
                "attackModelTrained": attack_model_trained
            },
            "finalOutputSizeBytes": random.randint(50, 150) # 模拟小的输出文件
        }
    })

    return events

def main():
    """主函数，处理scenarios文件夹下所有log文件"""
    input_dir = "scenarios"
    output_dir = "processed_json"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    log_files = glob.glob(os.path.join(input_dir, "*.log"))
    if not log_files:
        print(f"Error: No .log files found in '{input_dir}'.")
        print("Please run 'generate_mia_scenarios.py' first.")
        return

    print(f"Found {len(log_files)} log files to process...")

    for log_path in log_files:
        print(f"  > Processing: {log_path}")
        json_events = parse_log_file(log_path)
        
        output_filename = os.path.basename(log_path).replace('.log', '.json')
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 为了可读性，每个JSON对象占一行
            for event in json_events:
                f.write(json.dumps(event, ensure_ascii=False, indent=None) + '\n')
        
        print(f"    - Saved structured JSON to: {output_path}")

    print("\nPreprocessing complete.")


if __name__ == "__main__":
    main()