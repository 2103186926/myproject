# log_generator.py
import random
import time
import os
import uuid
'''
此脚本将批量生成多样化的攻击模拟场景，其输出的.log文件格式严格仿照您提供的模型逆向攻击（Model Inversion Attacks）.log文件。
'''

# 预设的一些海洋敏感区域坐标
SENSITIVE_AREAS = [
    (38.5, 122.0), (22.3, 114.2), (34.0, 135.0), (18.2, 120.5)
]

# 仿照您提供的代码示例创建模板
CODE_TEMPLATE = """
# Auto-generated malicious code simulation from {base_file}
# taskId: {task_id}
# type: {task_type}

import time
import random

def attack_simulation():
    target_lat = {lat}
    target_lon = {lon}
    depth_range = ({start_depth}, {end_depth})
    depth_step = {step}
    
    print(f"[*] taskId: {task_id}")
    print(f"[+] Starting model inversion attack on target area ({lat}, {lon})")
    print(f"[+] Probing depth from {start_depth}m to {end_depth}m with step {step}m")
    
    # This is a simulation of the log output
    print("[+] Attack completed.")
    print(f"[+] Collected {num_datapoints} data points.")
    print("[+] Reconstructed salinity profile saved to reconstructed_profile_{lat}_{lon}.csv")

if __name__ == "__main__":
    attack_simulation()
"""

def generate_simulation(output_dir="generated_data", is_malicious=True):
    """生成一次攻击或正常任务的模拟代码和日志"""
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    task_type = "malicious" if is_malicious else "benign"

    # --- 1. 随机化任务参数 ---
    if is_malicious:
        target_lat, target_lon = random.choice(SENSITIVE_AREAS)
        start_depth = 0
        end_depth = random.randint(400, 1000)
        depth_step = random.choice([5, 10])
        error_rate = 0.05
    else: # 正常任务参数
        target_lat, target_lon = (random.uniform(10, 50), random.uniform(100, 150))
        start_depth = random.choice([0, 50, 100])
        end_depth = random.randint(100, 300)
        depth_step = random.choice([20, 50])
        error_rate = 0.02

    timestamp_str = f"{int(time.time()*1000)}_{random.randint(100,999)}"
    base_filename = f"{task_type}_{timestamp_str}"
    
    # --- 2. 生成日志文件 (.log) ---
    log_filepath = os.path.join(output_dir, "raw_logs", f"{base_filename}.log")
    os.makedirs(os.path.dirname(log_filepath), exist_ok=True)
    
    num_datapoints = 0
    with open(log_filepath, 'w') as f:
        f.write(f"[*] taskId: {task_id}\n")
        f.write(f"[+] Starting model inversion attack on target area ({target_lat:.4f}, {target_lon:.4f})\n")
        f.write(f"[+] Probing depth from {start_depth}m to {end_depth}m with step {depth_step}m\n")

        # 模拟日志主体内容
        for depth in range(start_depth, end_depth + depth_step, depth_step):
            if depth % 50 == 0 and depth > start_depth:
                f.write(f"[+] Progress: Completed depth {depth}m\n")
            
            if random.random() < error_rate:
                f.write(f"[-] Error on query {random.randint(1, 5)} at depth {depth}m: Model response timeout (504)\n")
                continue
            
            # 仿照示例，在日志末尾打印聚合结果
            avg_salinity = 33.5 + (depth / 1000) * 1.5 + random.uniform(-0.05, 0.05)
            f.write(f"  Depth: {depth:4d}m | Avg Salinity: {avg_salinity:.4f}\n")
            num_datapoints += random.randint(3,8)

        f.write(f"[+] Attack completed.\n")
        f.write(f"[+] Collected {num_datapoints} data points.\n")
        f.write(f"[+] Reconstructed salinity profile saved to reconstructed_profile_{target_lat:.1f}_{target_lon:.1f}.csv\n")
    
    # --- 3. 生成代码文件 (.py) ---
    code_filepath = os.path.join(output_dir, "source_code", f"{base_filename}.py")
    os.makedirs(os.path.dirname(code_filepath), exist_ok=True)
    
    code_content = CODE_TEMPLATE.format(
        base_file=base_filename, task_id=task_id, task_type=task_type,
        lat=target_lat, lon=target_lon, start_depth=start_depth,
        end_depth=end_depth, step=depth_step, num_datapoints=num_datapoints
    )
    with open(code_filepath, 'w') as f:
        f.write(code_content)

if __name__ == "__main__":
    NUM_MALICIOUS = 10  # 成员推断攻击日志数量
    NUM_BENIGN = 5      # 正常任务日志数量
    print(f"Generating {NUM_MALICIOUS} malicious and {NUM_BENIGN} benign simulations...")
    for _ in range(NUM_MALICIOUS):
        generate_simulation(is_malicious=True)
    for _ in range(NUM_BENIGN):
        generate_simulation(is_malicious=False)
    print("Generation complete. Check the 'generated_data' directory.")