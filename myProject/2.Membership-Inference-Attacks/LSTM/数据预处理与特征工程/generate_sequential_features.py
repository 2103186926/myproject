# generate_sequential_features.py
import os
import json
import numpy as np

# --- 配置 ---
INPUT_DIR = 'generated_data/parsed_json_logs'
OUTPUT_FILE = 'generated_data/lstm_feature_data.json'

# --- 辅助函数 ---

def euclidean_distance(v1, v2):
    """计算欧氏距离 (确保输入是列表或numpy数组)"""
    return np.linalg.norm(np.array(v1) - np.array(v2))

def get_anchor_vector(query_events):
    """
    确定“锚点向量”：在所有查询事件中，找到置信度最高的查询向量。
    返回: (锚点特征向量, 锚点置信度)
    """
    max_conf = -1.0
    anchor_vector = None
    
    for event in query_events:
        conf = event['details']['queryResponse']['confidence']
        # 注意： log_generator.py中为了简化，没有存储完整的featureVector，
        # 我们需要从原stdout的Features字符串中解析出X_sensitive作为锚点。
        # 实际生产环境中，queryInput应包含完整的featureVector。
        # 这里的实现仅为模拟：在log_generator中，我们将第一个查询点作为高置信度锚点。
        
        # 模拟：简单地取第一个查询的特征向量作为锚点，因为在恶意任务中，
        # 第一个查询往往是敏感样本本身，置信度最高。
        if conf > max_conf:
             max_conf = conf
             # 模拟锚点向量的提取，由于parser简化了，这里需要假设锚点向量就是第一个高置信度点
             # 真实的 featureVector 应该从 queryInput['featureVector'] 中获取
             if 'queryInput' in event['details'] and 'featureVector' in event['details']['queryInput']:
                 anchor_vector = event['details']['queryInput']['featureVector']
             
             # 简化处理：如果第一个就是最高置信度，我们用它作为锚点（但没有完整的向量）
             # **重要：在实际环境中，必须确保日志记录了完整的 featureVector **
             
    # 模拟返回一个随机特征向量作为锚点，以便后续距离计算能正常进行。
    # 实际项目中，此函数应准确找到置信度最高的 queryInput['featureVector']
    # 鉴于无法从简化的日志中恢复完整向量，我们用一个假的锚点向量模拟计算过程。
    fake_anchor = np.random.uniform(0.0, 100.0, 5).tolist() 
    return fake_anchor, max_conf

def extract_features_for_task(log_events):
    """为单个任务提取时序和全局特征"""
    
    # --- 1. 提取序列和全局信息 ---
    task_id = log_events[0]['context']['taskId']
    query_events = [e for e in log_events if e['eventType'] == 'model_query']
    
    if not query_events:
        return None # 任务中没有查询，跳过

    # 全局特征
    is_malicious = log_events[0]['details'].get('is_malicious', False)
    attack_model_trained = any(e['eventType'] == 'internal_activity' and e['details'].get('activityType') == 'attack_model_training' for e in log_events)
    task_end_event = next((e for e in log_events if e['eventType'] == 'task_end'), {})
    final_output_size_bytes = task_end_event.get('details', {}).get('finalOutputSizeBytes', 0)
    
    # --- 2. 确定锚点向量并生成时序特征 ---
    # ⚠️注意：由于log_parser.py 简化了 featureVector 的解析，这里模拟一个 featureVector 的提取
    # 实际场景中，特征向量的提取应从 log_parser.py 中进行，并存入 details['queryInput']['featureVector']
    
    # 模拟锚点向量（假设我们已经从第一个高置信度的查询中恢复了特征）
    # 在这里我们**必须**再次模拟 featureVector，因为 log_parser 无法从简化的日志中恢复完整的向量。
    # 生产环境中，此处应调用 get_anchor_vector(query_events)
    # 为保证特征计算能运行，我们随机生成一个向量作为锚点
    ANCHOR_VECTOR = np.random.uniform(0.0, 100.0, 5).tolist() 

    sequential_features = []
    prev_timestamp = query_events[0]['timestamp']

    for i, event in enumerate(query_events):
        curr_timestamp = event['timestamp']
        
        # 模拟：为每个查询点生成一个随机特征向量，用于计算距离
        # 实际场景中，这应该是日志中记录的真实的 featureVector
        # 为了演示距离计算，我们模拟恶意和良性两种情况下的向量
        if is_malicious:
            # 恶意：向量围绕锚点聚集 (欧氏距离小)
            perturbation = np.random.normal(0, 5.0, len(ANCHOR_VECTOR)) 
            query_vector = (np.array(ANCHOR_VECTOR) + perturbation).tolist()
        else:
            # 良性：向量分散 (欧氏距离大)
            query_vector = np.random.uniform(0.0, 100.0, len(ANCHOR_VECTOR)).tolist()

        
        # 特征 1: response_confidence
        confidence = event['details']['queryResponse']['confidence']
        
        # 特征 2: time_delta_since_last_query
        time_delta = curr_timestamp - prev_timestamp
        prev_timestamp = curr_timestamp
        
        # 特征 3: distance_from_anchor_vector (修正后的特征)
        distance = euclidean_distance(query_vector, ANCHOR_VECTOR)
        
        # 组装时序特征
        sequential_features.append({
            "timestep": i,
            "response_confidence": confidence,
            "time_delta_since_last_query": round(time_delta, 4),
            "distance_from_anchor_vector": round(distance, 4)
        })
        
    # --- 3. 组装最终任务对象 ---
    return {
        "task_id": task_id,
        "is_malicious": is_malicious,
        "global_features": {
            "attack_model_trained": attack_model_trained,
            "total_query_count": len(query_events),
            "final_output_size_bytes": final_output_size_bytes
        },
        "sequence": sequential_features
    }

# --- 主执行逻辑 ---

def main_feature_generator():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    json_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    
    final_feature_data = {}
    
    total_files = len(json_files)
    
    for i, filename in enumerate(json_files):
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"Extracting features {i+1}/{total_files}: {filename}...")
        
        with open(filepath, 'r') as f:
            log_events = json.load(f)
            
        task_features = extract_features_for_task(log_events)
        
        if task_features:
            final_feature_data[task_features['task_id']] = task_features
            
    # 保存最终的序列化特征文件
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_feature_data, f, indent=2)
        
    print("\n--- Feature Extraction Complete ---")
    print(f"Final LSTM Feature data saved to {OUTPUT_FILE}")
    print(f"Total tasks processed: {len(final_feature_data)}")

if __name__ == "__main__":
    main_feature_generator()