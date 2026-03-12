# Task Code for a499aad2
# 这是一个模拟的成员推断攻击（MIA）或正常分析任务

import numpy as np
import random
import time
from platform_sdk.model_client import PredictiveModelClient

# 预设的敏感样本（作为攻击的锚点）
X_sensitive = np.array([61.598049962519895, 70.08520789821588, 69.87366975771504, 88.05105591559024, 64.61148487471462, 85.21879770516269, 43.30025121604303, 38.56632932753191, 2.7657162719892714, 41.34055937586907, 61.78857496465757, 74.32604171156359, 83.73952163978974, 50.40355674821755, 43.00829190028289]) 
IS_MALICIOUS = False
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
    print(f"INFO: Task started: ID={task_id}")
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
