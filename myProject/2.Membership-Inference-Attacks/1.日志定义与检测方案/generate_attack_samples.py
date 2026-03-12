# 这个脚本会自动创建 scenarios 文件夹，并在其中生成5个不同的攻击场景。每个场景都模拟了针对不同海洋科学模型的攻击，具有不同的参数，确保了数据的多样性。

import os
import random
import numpy as np
from datetime import datetime, timedelta

# 根据您的文档定义，可供选择的海洋科学模型
TARGET_MODELS = [
    "seabed_terrain_classifier",      # 海底地形分类模型
    "fishery_resource_predictor",     # 渔业资源预测模型
    "high_precision_wave_forecast",   # 高精度海浪预报模型
    "ocean_ts_profile_model"          # 海洋温盐深预测模型
]

# 模拟不同模型的特征维度
MODEL_FEATURE_DIMS = {
    "seabed_terrain_classifier": 8,
    "fishery_resource_predictor": 12,
    "high_precision_wave_forecast": 15,
    "ocean_ts_profile_model": 5
}

def generate_sensitive_sample(dims):
    """根据维度生成一个模拟的敏感样本特征向量"""
    # 模拟一些正浮点数特征
    return np.random.rand(dims) * np.array([1, 3000, 15, 0.5] + [10] * (dims - 4))

def generate_malicious_code(scenario_id, model_name, num_shadow_samples):
    """生成模拟的恶意Python代码字符串"""
    
    # 先生成敏感样本数据
    sensitive_sample_data = list(generate_sensitive_sample(MODEL_FEATURE_DIMS[model_name]))
    
    code_template = f'''
# scenario_{scenario_id}_{model_name}_attack.py
# 这是一个自动生成的恶意代码示例，用于模拟成员推断攻击

import numpy as np
import time
from sklearn.ensemble import RandomForestClassifier

# 伪造一个模型客户端
class PredictiveModelClient:
    def __init__(self, model_name):
        self.model_name = model_name
        print(f"INFO: Client initialized for model: {{self.model_name}}")

    def predict(self, features):
        # 这是一个模拟预测，实际攻击中会调用真实API
        is_member = np.all(np.isclose(features, SENSITIVE_SAMPLE))
        if is_member:
            return {{'confidence': np.random.uniform(0.95, 0.99), 'class': 3}}
        else:
            return {{'confidence': np.random.uniform(0.4, 0.7), 'class': np.random.randint(0, 3)}}

def main():
    print(f"[+] Starting Membership Inference Attack for model '{model_name}'")
    
    # 阶段1: 准备敏感数据和影子数据
    global SENSITIVE_SAMPLE
    SENSITIVE_SAMPLE = np.array({sensitive_sample_data})
    
    print(f"[+] Generating {num_shadow_samples} shadow samples...")
    shadow_samples = [SENSITIVE_SAMPLE + np.random.normal(0, 0.05, SENSITIVE_SAMPLE.shape) for _ in range({num_shadow_samples})]
    
    all_samples = [SENSITIVE_SAMPLE] + shadow_samples
    
    # 阶段2: 查询目标模型
    print(f"[+] Querying the target model for {{len(all_samples)}} samples...")
    model_client = PredictiveModelClient(model_name="{model_name}")
    model_responses = []

    for i, sample in enumerate(all_samples):
        print(f"Query {{i+1}}/{{len(all_samples)}} - Processing features...")
        response = model_client.predict(sample)
        model_responses.append(response)
        time.sleep(np.random.uniform(0.1, 0.3)) # 模拟网络延迟和规避检测

    print(f"[+] Collected {{len(model_responses)}} model responses.")

    # 阶段3: 训练寄生攻击模型
    print("[+] Training the membership inference attack model (RandomForestClassifier)...")
    # 模拟训练过程
    time.sleep(15) 
    print("[+] Attack model training completed.")

    # 阶段4: 输出结果
    final_score = np.random.uniform(0.85, 0.95)
    print("="*50)
    print(" Membership Inference Attack Result")
    print("="*50)
    print(f" Attack Model Membership Score: {{final_score:.4f}}")
    print(f" Conclusion: The sample is LIKELY a member.")
    print("="*50)
    print("[+] Attack results saved to small log file.")

if __name__ == "__main__":
    main()
'''
    return code_template

def generate_execution_log(scenario_id, model_name, sensitive_sample, num_shadow_samples):
    """根据场景参数生成模拟的stdout执行日志"""
    
    log_lines = []
    total_queries = num_shadow_samples + 1
    start_time = datetime.now()
    
    log_lines.append(f"[+] Starting Membership Inference Attack for model '{model_name}'")
    log_lines.append(f"[+] Generating {num_shadow_samples} shadow samples...")
    log_lines.append(f"[+] Querying the target model for {total_queries} samples...")
    
    # 模拟敏感成员查询
    sensitive_confidence = round(random.uniform(0.95, 0.99), 4)
    sensitive_class = random.randint(3, 5)
    log_lines.append(f"Query 1/{total_queries} - Features: {np.round(sensitive_sample, 3).tolist()} - Confidence: {sensitive_confidence}, Predicted Class: {sensitive_class}")
    
    # 模拟影子非成员查询
    for i in range(num_shadow_samples):
        shadow_sample = sensitive_sample + np.random.normal(0, 0.05, sensitive_sample.shape)
        shadow_confidence = round(random.uniform(0.4, 0.7), 4)
        shadow_class = random.randint(0, 2)
        log_lines.append(f"Query {i+2}/{total_queries} - Features: {np.round(shadow_sample, 3).tolist()} - Confidence: {shadow_confidence}, Predicted Class: {shadow_class}")
        if i > 5 and random.random() > 0.9: # 随机跳过一些日志细节
             log_lines.append("...")

    log_lines.append(f"[+] Collected {total_queries} model responses.")
    log_lines.append("[+] Training the membership inference attack model (RandomForestClassifier)...")
    log_lines.append("[+] Attack model training completed.")
    
    final_score = round(random.uniform(0.85, 0.95), 4)
    log_lines.append("="*50)
    log_lines.append(" Membership Inference Attack Result")
    log_lines.append("="*50)
    log_lines.append(f" Attack Model Membership Score: {final_score}")
    log_lines.append(f" Conclusion: The sample is LIKELY a member.")
    log_lines.append("="*50)
    
    end_time = start_time + timedelta(seconds=total_queries * 0.2 + 25 + random.uniform(-5, 5))
    execution_time = round((end_time - start_time).total_seconds(), 2)
    
    log_lines.append("[+] Attack results saved to small log file.")
    log_lines.append(f"STATUS: Task completed successfully - Execution time: {execution_time} seconds")

    return "\n".join(log_lines)


def main(num_scenarios=5):
    """主函数，生成指定数量的场景"""
    output_dir = "scenarios"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    for i in range(1, num_scenarios + 1):
        print(f"--- Generating Scenario {i} ---")
        
        # 1. 随机选择参数
        model = random.choice(TARGET_MODELS)
        dims = MODEL_FEATURE_DIMS[model]
        sensitive_data = generate_sensitive_sample(dims)
        num_shadow = random.randint(100, 250)
        
        # 2. 生成恶意代码
        code_content = generate_malicious_code(i, model, num_shadow)
        code_filename = os.path.join(output_dir, f"scenario_{i}_{model}_attack.py")
        with open(code_filename, "w", encoding="utf-8") as f:
            f.write(code_content)
        print(f"  > Generated malicious code: {code_filename}")

        # 3. 生成执行日志
        log_content = generate_execution_log(i, model, sensitive_data, num_shadow)
        log_filename = os.path.join(output_dir, f"scenario_{i}_{model}_attack.log")
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(log_content)
        print(f"  > Generated execution log:  {log_filename}")

    print("\nGeneration complete.")

if __name__ == "__main__":
    main()