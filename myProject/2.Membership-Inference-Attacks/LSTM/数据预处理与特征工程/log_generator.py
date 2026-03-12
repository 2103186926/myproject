# log_generator.py
import os
import numpy as np
import random
import uuid
import time
from io import StringIO
from contextlib import redirect_stdout

# --- 配置 ---
NUM_TASKS = 200 # 模拟总任务数
MALICIOUS_RATIO = 0.4 # 恶意任务占比
LOG_DIR = 'raw_logs'
CODE_DIR = 'source_code'
# 敏感样本的特征向量维度，根据您提供的蓝本（如X_sensitive[:4]...）假设其维度为15
FEATURE_DIM = 15 

# --- 辅助函数 ---

def generate_feature_vector(dim=FEATURE_DIM):
    """生成一个模拟的特征向量"""
    return np.random.uniform(0.0, 100.0, dim).tolist()

def euclidean_distance(v1, v2):
    """计算欧氏距离"""
    return np.linalg.norm(np.array(v1) - np.array(v2))

def simulate_mia_task(task_id, is_malicious):
    """模拟一个完整的任务执行过程，生成stdout日志"""
    num_queries = random.randint(100, 200) if is_malicious else random.randint(30, 80)
    
    # 步骤 1: 确定敏感样本（锚点）
    X_sensitive = generate_feature_vector()
    
    # 步骤 2: 确定锚点置信度（恶意任务高，良性任务一般）
    anchor_confidence = random.uniform(0.95, 0.99) if is_malicious else random.uniform(0.65, 0.85)
    
    # 使用StringIO捕获所有print输出作为日志
    log_stream = StringIO()
    with redirect_stdout(log_stream):
        print(f"[{time.time()}] INFO: task_start: TaskID={task_id}, is_malicious={is_malicious}")
        
        # 模拟生成影子数据/查询
        for i in range(num_queries):
            ts = time.time() + i * random.uniform(0.05, 0.5) # 模拟时间戳
            
            # --- 恶意任务：查询点围绕锚点聚集 (高密度聚类) ---
            if is_malicious:
                perturbation = np.random.normal(0, 0.01, FEATURE_DIM).tolist() # 极小扰动
                X_query = (np.array(X_sensitive) + np.array(perturbation)).tolist()
                
                # 越靠近锚点，置信度越可能高
                distance_to_anchor = euclidean_distance(X_query, X_sensitive)
                # 模拟置信度：高置信度 (锚点附近) 或 低置信度 (影子样本)
                if i == 0 or distance_to_anchor < 0.5:
                     confidence = random.uniform(0.9, 0.99)
                else:
                    confidence = random.uniform(0.4, 0.6)
            
            # --- 良性任务：查询点分散 (低密度聚类) ---
            else:
                X_query = generate_feature_vector() # 随机新查询点
                confidence = random.uniform(0.6, 0.9)
                
            X_query_str = str([round(f, 4) for f in X_query[:5]]) + '...' # 截断显示
            print(f"[{ts}] INFO: model_query: Query={i+1}/{num_queries}, Confidence={confidence:.4f}, Features={X_query_str}")
            
        # 模拟寄生模型训练
        if is_malicious:
            print(f"[{ts + 1.0}] WARN: internal_activity: Type=attack_model_training, Description='Training local RandomForestClassifier.'")
            print(f"[{ts + 1.5}] INFO: task_end: FinalResult='Membership Score: 0.9876', OutputSizeBytes={random.randint(50, 200)}")
        else:
            print(f"[{ts + 1.5}] INFO: task_end: FinalResult='Scientific analysis completed.', OutputSizeBytes={random.randint(5000, 15000)}")

    return log_stream.getvalue(), X_sensitive # 返回日志内容和用于代码模拟的敏感样本

def create_task_code(task_id, X_sensitive):
    """为任务生成一个模拟的Python代码文件"""
    code_template = f"""# Task Code for {task_id}
# 这是一个模拟的成员推断攻击（MIA）或正常分析任务

import numpy as np
import random
import time
from platform_sdk.model_client import PredictiveModelClient

# 预设的敏感样本（作为攻击的锚点）
X_sensitive = np.array({X_sensitive}) 
IS_MALICIOUS = {'True' if 'malicious' in task_id else 'False'}
NUM_QUERIES = 200 if IS_MALICIOUS else 50

def generate_shadow_data(sensitive_sample, perturbation_factor):
    # MIA攻击的核心：围绕敏感样本生成影子数据
    shadow_data = []
    for _ in range(NUM_QUERIES):
        if IS_MALICIOUS:
            noise = np.random.normal(0, perturbation_factor, sensitive_sample.shape)
            shadow_sample = sensitive_sample + noise
            shadow_data.append(shadow_sample.tolist())
        else:
            # 良性任务则随机生成数据
            shadow_data.append(np.random.uniform(0.0, 100.0, sensitive_sample.shape).tolist())
    return shadow_data

def main():
    print(f"INFO: Task started: ID={{task_id}}")
    queries = generate_shadow_data(X_sensitive, 0.01 if IS_MALICIOUS else 5.0)
    
    for i, features in enumerate(queries):
        # 模拟模型查询
        # ... 真正的查询逻辑 ...
        time.sleep(random.uniform(0.05, 0.2))

    if IS_MALICIOUS:
        # 寄生模型训练的标志
        print("WARNING: Starting internal attack model training (RandomForestClassifier)...")
        # attack_model.fit(...)
        
if __name__ == "__main__":
    main()
"""
    return code_template

# --- 主执行逻辑 ---

def main_generator():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(CODE_DIR, exist_ok=True)
    
    task_count = 0
    malicious_count = 0
    
    # 模拟任务
    for i in range(NUM_TASKS):
        # 随机分配恶意或良性标签
        is_malicious = (random.random() < MALICIOUS_RATIO) or (malicious_count < NUM_TASKS * MALICIOUS_RATIO and i == NUM_TASKS - 1)
        
        # 确保恶意和良性任务的数量大致符合预期
        if is_malicious:
            task_name = f"malicious_mia_task_{i+1}_{uuid.uuid4().hex[:8]}"
            malicious_count += 1
        else:
            task_name = f"benign_research_task_{i+1}_{uuid.uuid4().hex[:8]}"
            
        task_id = task_name.split('_')[-1]
        
        # 1. 生成日志
        log_content, X_sensitive = simulate_mia_task(task_id, is_malicious)
        log_filename = os.path.join(LOG_DIR, f"log_{task_id}.log")
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(log_content)
            
        # 2. 生成代码
        code_content = create_task_code(task_id, X_sensitive)
        code_filename = os.path.join(CODE_DIR, f"{task_name}.py")
        with open(code_filename, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        task_count += 1
        print(f"Generated Task {task_count}: ID={task_id}, Malicious={is_malicious}")
        
    print("\n--- Generation Complete ---")
    print(f"Total Tasks: {task_count}, Malicious: {malicious_count}")

if __name__ == "__main__":
    main_generator()