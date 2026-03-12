# generate_feature_vectors.py

'''
模拟特征向量生成脚本:
运行此脚本，将在同级目录下生成一个名为 feature_vectors.csv 的文件，其中包含200行模拟的特征向量数据。
'''

import csv
import random
import uuid
import numpy as np

# 定义CSV文件的列名
HEADERS = [
    'taskId',
    'variance_latitude',
    'variance_longitude',
    'variance_depth',
    'mean_inter_query_time_ms',
    'stddev_inter_query_time_ms',
    'is_in_sensitive_area',
    'total_successful_queries',
    'query_rate_per_sec',
    'is_malicious'  # 标签列：1代表恶意，0代表正常
]

def generate_malicious_vector():
    """生成一个模拟模型逆向攻击的特征向量"""
    return {
        'taskId': f"task-malicious-{uuid.uuid4().hex[:12]}",
        # 经纬度方差极小，高度集中
        'variance_latitude': random.uniform(1e-8, 1e-6),
        'variance_longitude': random.uniform(1e-8, 1e-6),
        # 深度方差大，进行系统性扫描
        'variance_depth': random.uniform(100, 5000),
        # 查询间隔短且稳定
        'mean_inter_query_time_ms': np.random.normal(loc=300, scale=50), # 均值在300ms左右
        'stddev_inter_query_time_ms': random.uniform(1, 15), # 标准差极小，非常规律
        # 很高概率落在敏感区域
        'is_in_sensitive_area': random.choices([1, 0], weights=[0.85, 0.15], k=1)[0],
        # 查询总量巨大
        'total_successful_queries': random.randint(1500, 25000),
        # 查询速率非常高
        'query_rate_per_sec': random.uniform(5.0, 25.0),
        'is_malicious': 1
    }

def generate_benign_vector():
    """生成一个模拟正常科研任务的特征向量"""
    return {
        'taskId': f"task-benign-{uuid.uuid4().hex[:12]}",
        # 经纬度方差较大，模拟对一个区域的研究
        'variance_latitude': random.uniform(0.1, 10.0),
        'variance_longitude': random.uniform(0.1, 10.0),
        # 深度方差不一，可能研究单层（方差为0）或多层
        'variance_depth': random.uniform(0, 500),
        # 查询间隔长且不规律，反映“查询-计算”模式
        'mean_inter_query_time_ms': np.random.normal(loc=15000, scale=8000), # 均值在15秒左右
        'stddev_inter_query_time_ms': random.uniform(2000, 20000), # 标准差很大，极不规律
        # 较低概率落在敏感区域
        'is_in_sensitive_area': random.choices([1, 0], weights=[0.2, 0.8], k=1)[0],
        # 查询总量较小
        'total_successful_queries': random.randint(20, 400),
        # 查询速率很低
        'query_rate_per_sec': random.uniform(0.01, 1.0),
        'is_malicious': 0
    }

def main(filename='feature_vectors.csv', num_rows=200):
    """主函数，生成并写入CSV文件"""
    print(f"Generating {num_rows} feature vectors into '{filename}'...")
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADERS)
        writer.writeheader()
        
        for _ in range(num_rows):
            # 随机选择生成恶意或正常任务的向量
            if random.random() > 0.5:
                row = generate_malicious_vector()
            else:
                row = generate_benign_vector()
            
            # 将浮点数格式化为更易读的格式
            for key, value in row.items():
                if isinstance(value, float):
                    row[key] = f"{value:.6f}"
            
            writer.writerow(row)
            
    print("Generation complete.")
    print(f"File '{filename}' has been created successfully.")

if __name__ == '__main__':
    main()