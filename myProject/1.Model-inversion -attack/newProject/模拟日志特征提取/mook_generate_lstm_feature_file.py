# generate_lstm_feature_file.py
import json
import random
import uuid
import numpy as np

# --- 配置参数 ---
# LSTM模型要求输入的序列长度统一，我们设定一个最大长度
# 超过此长度的序列将被截断，不足的将被填充
MAX_SEQ_LENGTH = 150
# 定义每个时间步（即每次查询）的特征数量
# 依次是: lat, lon, depth, time_delta_ms, exec_time_ms, status_success, status_failure
NUM_FEATURES_PER_STEP = 7

def simulate_malicious_sequence():
    """模拟一个模型逆向攻击任务的行为序列"""
    # 恶意任务查询次数多
    num_queries = random.randint(100, 200) 
    
    # 攻击目标高度集中
    start_lat = random.uniform(20, 40)
    start_lon = random.uniform(110, 140)
    
    sequence = []
    depth_step = 10
    
    for i in range(num_queries):
        # 经纬度有微小扰动
        lat = start_lat + random.uniform(-0.01, 0.01)
        lon = start_lon + random.uniform(-0.01, 0.01)
        # 深度系统性递增
        depth = i * depth_step
        # 查询间隔短且稳定
        time_delta_ms = abs(np.random.normal(loc=300, scale=20)) # 模拟规律的sleep
        exec_time_ms = abs(np.random.normal(loc=250, scale=30))
        # 绝大多数查询是成功的
        status_success = 1 if random.random() > 0.02 else 0
        
        feature_vector = [
            lat, lon, depth, time_delta_ms, exec_time_ms, 
            status_success, 1 - status_success
        ]
        sequence.append(feature_vector)
        
    return sequence

def simulate_benign_sequence():
    """模拟一个正常科研任务的行为序列"""
    # 正常任务查询次数少
    num_queries = random.randint(10, 50)
    
    # 查询范围更广，不集中
    start_lat = random.uniform(20, 40)
    start_lon = random.uniform(110, 140)
    
    sequence = []
    
    for i in range(num_queries):
        # 经纬度变化较大
        lat = start_lat + random.uniform(-0.5, 0.5)
        lon = start_lon + random.uniform(-0.5, 0.5)
        # 深度可能是固定的或随机的
        depth = random.choice([0, 50, 100])
        # 查询间隔长且极不规律，模拟“查询-思考-再查询”
        time_delta_ms = abs(np.random.normal(loc=20000, scale=15000)) # 均值20秒，标准差很大
        exec_time_ms = abs(np.random.normal(loc=400, scale=150))
        status_success = 1 if random.random() > 0.1 else 0

        feature_vector = [
            lat, lon, depth, time_delta_ms, exec_time_ms,
            status_success, 1 - status_success
        ]
        sequence.append(feature_vector)
        
    return sequence

def main(filename='lstm_feature_data.json', num_tasks=200):
    """主函数，生成并写入包含序列特征的JSON文件"""
    print(f"Generating {num_tasks} task sequences for LSTM model into '{filename}'...")
    
    all_features = {}
    all_labels = {}
    
    for i in range(num_tasks):
        # 随机决定生成恶意或正常任务
        is_malicious = random.choice([0, 1])
        
        if is_malicious:
            task_id = f"task-malicious-{uuid.uuid4().hex[:12]}"
            sequence = simulate_malicious_sequence()
            all_labels[task_id] = 1
        else:
            task_id = f"task-benign-{uuid.uuid4().hex[:12]}"
            sequence = simulate_benign_sequence()
            all_labels[task_id] = 0
            
        # 对序列进行填充(padding)或截断(truncating)
        if len(sequence) > MAX_SEQ_LENGTH:
            padded_sequence = sequence[:MAX_SEQ_LENGTH]
        else:
            padding_length = MAX_SEQ_LENGTH - len(sequence)
            # 使用0向量进行填充
            padding = [[0] * NUM_FEATURES_PER_STEP] * padding_length
            padded_sequence = sequence + padding
        
        all_features[task_id] = padded_sequence

    # 组合成最终的数据结构
    final_data = {
        'features': all_features,  # 任务ID到特征序列的映射
        'labels': all_labels,  # 任务ID到标签的映射
        'metadata': {  # 元数据，描述数据集的基本信息
            'description': 'Sequential features for model inversion attack detection.',  
            'num_samples': len(all_features),
            'max_seq_length': MAX_SEQ_LENGTH,
            'num_features_per_step': NUM_FEATURES_PER_STEP,
            'feature_order': ['latitude', 'longitude', 'depth', 'time_delta_ms', 
                              'executionTimeMs', 'queryStatus_SUCCESS', 'queryStatus_FAILURE']
        }
    }
    
    # 写入JSON文件
    with open(filename, 'w') as f:
        json.dump(final_data, f)
        
    print("Generation complete.")
    print(f"File '{filename}' has been created successfully.")

if __name__ == '__main__':
    main()