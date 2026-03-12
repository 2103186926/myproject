# generate_sequential_features.py
import json
import os
import glob
import numpy as np
from datetime import datetime
import random

# --- 配置参数 ---
MAX_SEQ_LENGTH = 150  # 最大序列长度（时间步长） 为了在train_lstm_model.py中LSTM模型的输入的时间步长一致

# 每个时间步的特征数量（纬度、经度、深度、时间差、执行时间、成功状态、失败状态）
NUM_FEATURES_PER_STEP = 7 # lat, lon, depth, time_delta_ms, exec_time_ms, status_success, status_failure

def create_lstm_dataset(input_dir):
    """从多个结构化JSON文件中创建LSTM训练数据集"""
    
    all_features = {}
    all_labels = {}
    
    json_files = glob.glob(os.path.join(input_dir, "*.json"))
    if not json_files:
        raise FileNotFoundError(f"在 '{input_dir}' 中未找到JSON文件。请先运行 log_parser.py。")

    for filepath in json_files:
        with open(filepath, 'r') as f:
            logs = [json.loads(line) for line in f]
        
        if not logs:
            continue

        task_id = logs[0]["context"]["taskId"]
        
        # 从文件名判断标签
        is_malicious = 1 if "malicious" in os.path.basename(filepath) else 0
        all_labels[task_id] = is_malicious

        # 提取序列
        task_start_log = next((log for log in logs if log['eventType'] == 'task_start'), None)
        result_logs = [log for log in logs if log['eventType'] == 'result_summary']
        
        if not task_start_log or not result_logs:
            continue
            
        base_lat = task_start_log["details"]["declaredParameters"]["target_lat"]
        base_lon = task_start_log["details"]["declaredParameters"]["target_lon"]
        
        # 按深度对结果进行排序，以模拟时间序列
        result_logs.sort(key=lambda x: x["details"]["depth"])
        
        sequence = []
        for log in result_logs:
            details = log["details"]
            
            # 模拟时序特征
            if is_malicious:
                time_delta_ms = abs(np.random.normal(loc=300, scale=20))
                exec_time_ms = abs(np.random.normal(loc=250, scale=30))
            else:
                time_delta_ms = abs(np.random.normal(loc=10000, scale=5000))
                exec_time_ms = abs(np.random.normal(loc=400, scale=100))

            feature_vector = [
                base_lat + random.uniform(-0.01, 0.01),
                base_lon + random.uniform(-0.01, 0.01),
                details["depth"],
                time_delta_ms,
                exec_time_ms,
                1, # 结果摘要行总是代表成功的查询
                0
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
        'features': all_features,  # 每个任务的特征序列
        'labels': all_labels,  # 每个任务的标签（0或1）
        'metadata': {
            'description': 'Sequential features for model inversion attack detection.',  # 数据集描述
            'num_samples': len(all_features),  # 样本数量（任务数量）
            'max_seq_length': MAX_SEQ_LENGTH,  # 最大序列长度（时间步长）
            'num_features_per_step': NUM_FEATURES_PER_STEP,  # 每个时间步的特征数量
            'feature_order': ['latitude', 'longitude', 'depth', 'time_delta_ms', 
                              'executionTimeMs', 'queryStatus_SUCCESS', 'queryStatus_FAILURE']  # 每个特征的名称
        }
    }
    return final_data

if __name__ == "__main__":
    input_dir = os.path.join("generated_data", "parsed_json_logs")
    output_file = os.path.join("generated_data", "lstm_feature_data.json")
    
    try:
        final_dataset = create_lstm_dataset(input_dir)
        with open(output_file, 'w') as f:
            json.dump(final_dataset, f)
        print(f"LSTM dataset successfully created at '{output_file}'")
        print(f"Total samples processed: {len(final_dataset['labels'])}")
    except FileNotFoundError as e:
        print(f"错误: {e}")