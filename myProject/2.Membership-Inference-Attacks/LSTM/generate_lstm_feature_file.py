# generate_lstm_feature_file.py
import os
import json
import numpy as np
import random
import uuid
from scipy.spatial.distance import euclidean

# --- 配置 ---
OUTPUT_DIR = 'generated_data'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'lstm_feature_data.json')
NUM_TASKS = 200 # 生成的任务总数
MALICIOUS_RATIO = 0.5 # 恶意任务比例
FEATURE_DIM = 3 # 序列特征的维度: confidence, time_delta, distance
VECTOR_DIM = 10  # 模拟的特征向量维度

# --- 辅助函数 ---

def generate_random_vector(dim=VECTOR_DIM):
    """生成随机特征向量"""
    return np.random.rand(dim)

def generate_malicious_sequence(task_id):
    """生成一个模拟的恶意成员推断攻击序列特征"""
    is_malicious = True
    num_queries = random.randint(150, 250)
    
    # 模拟全局特征
    global_features = {
        "attack_model_trained": True,
        "total_query_count": num_queries,
        "final_output_size_bytes": random.randint(50, 300) # 输出字节小
    }
    
    # 特征生成
    sequential_features = []
    query_vectors = []
    confidences = []
    
    # 为每个查询生成特征向量和置信度
    for i in range(num_queries):
        # 1. response_confidence: 绝大多数集中在低-中（影子样本），1-2个极高（锚点）
        if i == 0 or random.random() < 0.05: # 少数高置信度
            confidence = random.uniform(0.95, 0.99)
        else: # 多数低置信度
            confidence = random.uniform(0.4, 0.65)
        
        confidences.append(confidence)
        
        # 对于恶意任务，所有查询向量都围绕敏感样本（高置信度）生成
        # 生成一个基础向量
        if i == 0:
            base_vector = generate_random_vector()
        
        # 对于恶意任务，所有查询向量都与基础向量非常接近
        # 添加少量噪声
        noise = np.random.normal(0, 0.05, VECTOR_DIM)  # 小方差的高斯噪声
        query_vector = base_vector + noise
        query_vectors.append(query_vector)
    
    # 找到置信度最高的查询作为锚点
    anchor_index = np.argmax(confidences)
    anchor_vector = query_vectors[anchor_index]
    
    # 计算每个查询向量与锚点向量的距离
    for i in range(num_queries):
        # 2. time_delta_since_last_query: 相对均匀且小 (高频查询)
        time_delta = random.uniform(0.05, 0.3) if i > 0 else 0.0
        
        # 3. distance_from_anchor_vector: 计算与锚点向量的欧氏距离
        distance = euclidean(query_vectors[i], anchor_vector)
        
        sequential_features.append({
            "timestep": i,
            "response_confidence": round(confidences[i], 4),
            "time_delta_since_last_query": round(time_delta, 4),
            "distance_from_anchor_vector": round(distance, 4)
        })

    return {
        "task_id": task_id,
        "is_malicious": is_malicious,
        "global_features": global_features,
        "sequence": sequential_features
    }

def generate_benign_sequence(task_id):
    """生成一个模拟的良性科研任务序列特征"""
    is_malicious = False
    num_queries = random.randint(50, 150)
    
    # 模拟全局特征
    global_features = {
        "attack_model_trained": False,
        "total_query_count": num_queries,
        "final_output_size_bytes": random.randint(5000, 20000) # 输出字节大
    }
    
    # 特征生成
    sequential_features = []
    query_vectors = []
    confidences = []
    
    # 为每个查询生成特征向量和置信度
    for i in range(num_queries):
        # 1. response_confidence: 稳定，无明显离群值
        confidence = random.uniform(0.6, 0.85)
        confidences.append(confidence)
        
        # 对于良性任务，查询向量分布更加分散
        # 每次生成一个全新的随机向量
        query_vector = generate_random_vector()
        query_vectors.append(query_vector)
    
    # 找到置信度最高的查询作为锚点
    anchor_index = np.argmax(confidences)
    anchor_vector = query_vectors[anchor_index]
    
    # 计算每个查询向量与锚点向量的距离
    for i in range(num_queries):
        # 2. time_delta_since_last_query: 波动大，更随机 (人类操作/复杂分析)
        time_delta = random.uniform(0.5, 5.0) if i > 0 else 0.0
        
        # 3. distance_from_anchor_vector: 计算与锚点向量的欧氏距离
        # 对于良性任务，这个距离应该更大且分散
        distance = euclidean(query_vectors[i], anchor_vector)
        
        sequential_features.append({
            "timestep": i,
            "response_confidence": round(confidences[i], 4),
            "time_delta_since_last_query": round(time_delta, 4),
            "distance_from_anchor_vector": round(distance, 4)
        })

    return {
        "task_id": task_id,
        "is_malicious": is_malicious,
        "global_features": global_features,
        "sequence": sequential_features
    }

# --- 主执行逻辑 ---

def main_generate_features():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    final_feature_data = {}
    
    malicious_count = 0
    
    for i in range(NUM_TASKS):
        task_id = uuid.uuid4().hex[:10]
        
        if random.random() < MALICIOUS_RATIO and malicious_count < NUM_TASKS * MALICIOUS_RATIO:
            task_features = generate_malicious_sequence(task_id)
            malicious_count += 1
        else:
            task_features = generate_benign_sequence(task_id)
            
        final_feature_data[task_id] = task_features
        
    # 保存最终的序列化特征文件
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_feature_data, f, indent=2)
        
    print(f"\n--- 特征数据生成完成 ---")
    print(f"总任务数: {NUM_TASKS}, 恶意任务数: {malicious_count}")
    print(f"数据已保存至: {OUTPUT_FILE}")

if __name__ == "__main__":
    main_generate_features()