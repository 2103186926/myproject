# Task Code for 7fabb192
# 这是一个模拟的成员推断攻击（MIA）或正常分析任务

import numpy as np
import random
import time
from platform_sdk.model_client import PredictiveModelClient

# 预设的敏感样本（作为攻击的锚点）
X_sensitive = np.array([13.901592668443897, 14.900460804577353, 80.1990539695082, 33.95690542924271, 47.70816461865398, 67.82593791841158, 56.35551916925539, 16.013852465134537, 40.55770341789031, 1.5072140058037253, 60.82199193447335, 3.706396945048751, 53.105557868886955, 36.46054416308028, 25.329485061042945]) 
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
