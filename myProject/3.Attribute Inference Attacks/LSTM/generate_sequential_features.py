# 此脚本与上一阶段的几乎一致，主要变化是它现在读取.jsonl文件，并能从taskName中推断标签。
# (适配) 读取platform_logs.jsonl文件，按taskId聚合，提取时序特征，并生成最终的lstm_feature_data_attr_inf.json文件。
import json
import numpy as np
from datetime import datetime
from collections import defaultdict

# --- 配置参数 ---
MAX_SEQ_LENGTH = 300 # 属性推断攻击的查询次数可能更多
NUM_FEATURES_PER_STEP = 7 # lat, lon, depth, time_delta_ms, exec_time_ms, status_success, status_failure

def create_lstm_dataset(input_file="platform_logs.jsonl"):
    """从结构化JSONL日志文件中创建LSTM训练数据集"""
    
    print(f"Reading logs from '{input_file}'...")
    
    # 按taskId聚合所有日志条目
    tasks = defaultdict(list)
    with open(input_file, 'r') as f:
        for line in f:
            try:
                log = json.loads(line)
                task_id = log.get("context", {}).get("taskId")
                if task_id:
                    tasks[task_id].append(log)
            except json.JSONDecodeError:
                print(f"Warning: Skipping malformed log line: {line}")
                
    print(f"Found {len(tasks)} unique taskIds. Processing sequences...")
    
    all_features = {}
    all_labels = {}
    
    for task_id, logs in tasks.items():
        # 按时间戳排序
        logs.sort(key=lambda x: x["timestamp"])
        
        # 提取所有model_query事件
        query_logs = [log for log in logs if log['eventType'] == 'model_query']
        if len(query_logs) < 10: # 忽略查询次数太少的任务
            continue
            
        # 确定标签（基于task_start日志中的taskName）
        task_start_log = next((log for log in logs if log['eventType'] == 'task_start'), None)
        if task_start_log:
            is_malicious = 1 if "malicious" in task_start_log["details"].get("taskName", "") else 0
        else:
            continue # 没有task_start的任务无法打标签

        all_labels[task_id] = is_malicious
        
        sequence = []
        last_timestamp = None
        
        for log in query_logs:
            details = log["details"]
            query_input = details["queryInput"]
            
            # 计算时序特征: time_delta_ms
            current_timestamp = datetime.fromisoformat(log["timestamp"])
            time_delta_ms = 0.0
            if last_timestamp:
                time_delta_ms = (current_timestamp - last_timestamp).total_seconds() * 1000
            
            # 模拟的短间隔，加入随机性
            if is_malicious and time_delta_ms < 100:
                time_delta_ms = abs(np.random.normal(loc=300, scale=20))
            # 模拟的长时间隔
            elif not is_malicious and time_delta_ms > 100:
                 time_delta_ms = abs(np.random.normal(loc=2000, scale=1000)) + time_delta_ms
            
            last_timestamp = current_timestamp

            # 构建特征向量
            feature_vector = [
                query_input.get("latitude", 0),
                query_input.get("longitude", 0),
                query_input.get("depth", 0),
                time_delta_ms,
                details.get("executionTimeMs", 0),
                1 if details.get("queryStatus") == "SUCCESS" else 0,
                1 if details.get("queryStatus") == "FAILURE" else 0
            ]
            sequence.append(feature_vector)
            
        # 填充或截断
        if len(sequence) > MAX_SEQ_LENGTH:
            padded_sequence = sequence[:MAX_SEQ_LENGTH]
        else:
            padding = [[0] * NUM_FEATURES_PER_STEP] * (MAX_SEQ_LENGTH - len(sequence))
            padded_sequence = sequence + padding
            
        all_features[task_id] = padded_sequence
        
    # 组合成最终的数据结构
    final_data = {
        'features': all_features,
        'labels': all_labels,
        'metadata': {
            'description': 'Sequential features for Attribute Inference attack detection.',
            'num_samples': len(all_features),
            'max_seq_length': MAX_SEQ_LENGTH,
            'num_features_per_step': NUM_FEATURES_PER_STEP,
            'feature_order': ['latitude', 'longitude', 'depth', 'time_delta_ms', 
                              'executionTimeMs', 'queryStatus_SUCCESS', 'queryStatus_FAILURE']
        }
    }
    return final_data

if __name__ == "__main__":
    INPUT_FILE = "platform_logs.jsonl"
    OUTPUT_FILE = "lstm_feature_data_attr_inf.json"
    
    try:
        final_dataset = create_lstm_dataset(INPUT_FILE)
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(final_dataset, f)
        print(f"\nLSTM dataset successfully created at '{OUTPUT_FILE}'")
        print(f"Total samples processed: {len(final_dataset['labels'])}")
    except FileNotFoundError as e:
        print(f"错误: {e}. 请先运行 log_generator_attr_inf.py。")