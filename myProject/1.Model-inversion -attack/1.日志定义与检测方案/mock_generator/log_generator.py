# log_generator.py
import random
import time
import os

# 预设的一些海洋敏感区域坐标（示例）
SENSITIVE_AREAS = [
    (38.5, 122.0),
    (22.3, 114.2),
    (34.0, 135.0),
    (18.2, 120.5)
]

# 模拟的恶意代码模板
CODE_TEMPLATE = """
# Auto-generated malicious code simulation
import time
import random

def attack_simulation():
    target_lat = {lat}
    target_lon = {lon}
    depth_range = ({start_depth}, {end_depth})
    depth_step = {step}
    num_queries_per_point = {queries_per_point}
    
    print(f"[+] Starting model inversion attack on target area ({{target_lat}}, {{target_lon}})")
    print(f"[+] Probing depth from {{depth_range[0]}}m to {{depth_range[1]}}m with step {{depth_step}}m")
    
    data_points_collected = 0
    # --- This is a simulation, not a real attack ---
    # In a real script, this loop would contain model API calls.
    # We are only generating the log output here.
    # -------------------------------------------------
    
    print("[+] Attack completed.")
    print(f"  Collected {{data_points_collected}} data points.")
    print(f"[+] Reconstructed salinity profile saved to reconstructed_profile_{lat}_{lon}.csv")

if __name__ == "__main__":
    attack_simulation()
"""

def generate_attack_simulation(output_dir="generated_logs"):
    """生成一次模型逆向攻击的模拟代码和日志"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. 随机化攻击参数
    target_lat, target_lon = random.choice(SENSITIVE_AREAS)
    start_depth = 0
    end_depth = random.randint(200, 1000)
    depth_step = random.choice([5, 10, 20])
    queries_per_point = random.randint(3, 8)
    
    timestamp = int(time.time() * 1000)
    base_filename = f"attack_{timestamp}"
    
    # 2. 生成模拟的恶意代码文件
    code_content = CODE_TEMPLATE.format(
        lat=target_lat,
        lon=target_lon,
        start_depth=start_depth,
        end_depth=end_depth,
        step=depth_step,
        queries_per_point=queries_per_point
    )
    code_filepath = os.path.join(output_dir, f"{base_filename}.py")
    with open(code_filepath, 'w') as f:
        f.write(code_content)

    # 3. 生成对应的模拟日志文件
    log_filepath = os.path.join(output_dir, f"{base_filename}.log")
    with open(log_filepath, 'w') as f:
        f.write(f"[+] Starting model inversion attack on target area ({target_lat}, {target_lon})\n")
        f.write(f"[+] Probing depth from {start_depth}m to {end_depth}m with step {depth_step}m\n")

        total_queries = 0
        error_count = 0
        reconstructed_profile = []

        for depth in range(start_depth, end_depth + depth_step, depth_step):
            if depth % (depth_step * 5) == 0:
                 f.write(f"[+] Progress: Completed depth {depth}m\n")
            
            # 随机注入错误
            if random.random() < 0.05: # 5% 的几率在某个深度上出错
                f.write(f"[-] Error on query {random.randint(1, queries_per_point)} at depth {depth}m: Model response timeout (504)\n")
                error_count += 1
                continue

            # 模拟平均盐度值
            # 盐度随深度增加而缓慢增加，并加入随机噪声
            avg_salinity = 33.5 + (depth / end_depth) * 1.5 + random.uniform(-0.05, 0.05)
            reconstructed_profile.append((depth, avg_salinity))
            total_queries += queries_per_point

        f.write(f"[+] Attack completed.\n")
        f.write(f"[+] Collected {total_queries} data points.\n")
        
        for depth, salinity in reconstructed_profile:
            f.write(f"  Depth: {depth:4d}m | Avg Salinity: {salinity:.4f}\n")
            
        output_csv_name = f"reconstructed_salinity_profile_{target_lat}_{target_lon}.csv"
        f.write(f"[+] Reconstructed salinity profile saved to {output_csv_name}\n")
        
    return code_filepath, log_filepath

if __name__ == "__main__":
    num_to_generate = 5  # 定义要生成的样本数量
    print(f"Generating {num_to_generate} sets of attack simulations...")
    for i in range(num_to_generate):
        code_file, log_file = generate_attack_simulation()
        print(f"  Generated ({i+1}/{num_to_generate}): {code_file} and {log_file}")
    print("Generation complete.")