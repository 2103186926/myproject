# side_channel_resource_contention.py
import time
import math
import threading
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# ==========================================
# 1. 模拟共享计算环境 (The Shared Cloud Node)
# ==========================================
class SharedComputeNode:
    def __init__(self):
        # 系统当前的负载压力值 (0.0 - 1.0+)
        # 0.0 表示空闲，高值表示CPU流水线阻塞
        self._system_stress = 0.0
        self._lock = threading.Lock()  # 创建锁，用于线程同步

    def set_stress(self, stress_level):
        """受害者任务调用此方法，模拟占用CPU资源"""
        with self._lock:
            self._system_stress = stress_level

    def get_performance_penalty(self):
        """
        攻击者调用此方法。
        系统负载越高，攻击者获得CPU时间片的机会越少，执行越慢。
        """
        base_cost = 1000  # 基准耗时 (纳秒)
        # 模拟资源竞争：负载越高，惩罚延迟越大
        # 加入随机抖动模拟真实OS调度噪声
        noise = np.random.normal(0, 50) 
        penalty = (self._system_stress * 5000) + noise
        return max(100, base_cost + penalty)

# 全局共享环境实例
CLOUD_NODE = SharedComputeNode()

# ==========================================
# 2. 受害者任务：敏感海域模拟 (The Victim)
# ==========================================
def victim_ocean_simulation():
    """
    模拟受害者正在按顺序扫描处理一个 20x20 的网格海域。
    其中有一块'复杂区域'（如潜艇隐蔽区），计算量巨大。
    """
    print("[Victim] 启动海洋数值模拟任务...")
    
    # 定义海域地图 (0=简单深海, 1=复杂近岸/敏感区)
    # 模拟在第 8-12 时间段处理复杂区域
    map_timeline = np.zeros(100)
    map_timeline[40:60] = 1  # 敏感区域在中间时间段
    
    for t, terrain_type in enumerate(map_timeline):
        # 模拟计算负载
        if terrain_type == 1:
            # 复杂区域：高计算强度 (如湍流模型求解)
            # 这会导致共享节点的压力飙升
            CLOUD_NODE.set_stress(0.8)  # 模拟高计算负载 (0.8 表示 80% 负载)
            status = "Complex (High Load)"
        else:
            # 简单区域：低计算强度
            CLOUD_NODE.set_stress(0.1)  # 模拟低计算负载 (0.1 表示 10% 负载)
            status = "Sparse (Low Load)"
            
        # 模拟处理这一帧数据需要的时间
        time.sleep(0.05) # 每一个时间步长 50ms
        
        if t % 10 == 0:
            print(f"    [Victim] Processing step {t}/100: {status}")

    print("[Victim] 模拟任务结束。")
    CLOUD_NODE.set_stress(0.0) # 释放资源

# ==========================================
# 3. 攻击者任务：侧信道监听 (The Attacker)
# ==========================================
class ContentionAttacker:
    def __init__(self):
        self.measurements = []  # 记录每次探测的延迟 (纳秒)
        self.timestamps = []    # 记录每次探测的时间 (秒)
        
    def perform_alu_benchmark(self):
        """
        攻击者的探针：执行一个简单的ALU操作并计时。
        由于资源争用，这个操作在系统繁忙时会变慢。
        """
        start = time.perf_counter_ns()  # 记录开始时间 (纳秒)
        
        # 模拟攻击者的轻量级计算 (Probe)
        # 在真实环境中，这可能是一段密集的整数运算
        # 这里我们直接查询环境模拟器获取延迟
        delay = CLOUD_NODE.get_performance_penalty()  # 获取当前系统的性能惩罚延迟 (纳秒)
        
        # 忙等待模拟CPU消耗
        target = time.perf_counter_ns() + delay  # 计算目标时间 (纳秒)
        while time.perf_counter_ns() < target:
            pass
            
        end = time.perf_counter_ns()  # 记录结束时间 (纳秒)
        return end - start

    def spy_process(self, duration_sec=6):
        '''
        参数：
        duration_sec：监听的持续时间，单位秒。默认值为6秒。
        '''
        print("[Attacker] 开始监听侧信道信号...")
        start_time = time.time()
        
        while time.time() - start_time < duration_sec:
            # 1. 执行探测
            latency = self.perform_alu_benchmark()  # 执行ALU基准测试，返回延迟 (纳秒)
            
            # 2. 记录数据
            self.measurements.append(latency)  # 记录当前探测的延迟 (纳秒)
            self.timestamps.append(time.time() - start_time)  # 记录当前探测的时间 (秒)
            
            # 3. 极短休眠，避免自己把CPU占满导致死锁
            time.sleep(0.001) 
            
    def analyze_and_plot(self):
        print("\n[Attacker] 分析采集到的信号特征...")
        
        data = np.array(self.measurements)  # 每次探测的延迟(纳秒)
        times = np.array(self.timestamps)  # 每次探测的时间(秒)
        
        # 1. 统计基线 (使用前10个点作为冷启动基线)
        baseline_mean = np.mean(data[:10])  # 前10个点的平均延迟 (纳秒)
        baseline_std = np.std(data[:10])  # 前10个点的延迟标准差 (纳秒)
        print(f"    基线延迟: {baseline_mean:.2f} ns (Std: {baseline_std:.2f})")
        
        # 2. 异常检测 (Z-Score)
        z_scores = (data - baseline_mean) / (baseline_std + 1e-9)  # 公式：(x - μ) / σ，x为当前延迟，μ为基线均值，σ为基线标准差
        anomalies = data[z_scores > 3] # 超过3倍标准差视为异常
        
        print(f"    检测到异常点数量: {len(anomalies)}")
        
        if len(anomalies) > 50:  #! 需要根据实际测量情况调整
            print("    [!!!] 判定：检测到共驻用户正在处理高敏感数据！")
            print("    [Inference] 受害者在 Time=2.0s 到 3.0s 之间处于高负载状态。")
        else:
            print("    [Inference] 未检测到明显活动。")

        # (可选) 如果你本地有 matplotlib，这会生成非常直观的攻击波形图
        try:
            plt.figure(figsize=(10, 4))
            plt.plot(times, data, label='Probe Latency', color='blue', alpha=0.6)
            plt.axhline(y=baseline_mean, color='green', linestyle='--', label='Baseline')  # 绿线：基线平均值（μ）
            plt.axhline(y=baseline_mean + 3*baseline_std, color='red', linestyle='--', label='Threshold (3σ)')  # 红线：异常阈值（μ+3σ）
            plt.title('Side-Channel Trace: CPU Contention Analysis')
            plt.xlabel('Time (s)')
            plt.ylabel('Attacker Operation Latency (ns)')
            plt.legend()
            plt.grid(True)
            print("    [Info] 正在生成波形图...")
            plt.show() # 如果在无头服务器运行，请注释此行
        except Exception:
            pass

# ==========================================
# 主程序
# ==========================================
if __name__ == "__main__":
    # 1. 实例化攻击者
    attacker = ContentionAttacker()
    
    # 2. 启动攻击者监听线程 (后台运行)
    attack_thread = threading.Thread(target=attacker.spy_process)
    attack_thread.start()
    
    # 3. 稍后启动受害者任务 (模拟真实场景中受害者随时可能开始)
    time.sleep(0.5)
    victim_thread = threading.Thread(target=victim_ocean_simulation)
    victim_thread.start()
    
    # 4. 等待结束
    victim_thread.join()  # 等待受害者任务完成
    attack_thread.join()  # 等待攻击者任务完成
    
    # 5. 分析结果
    attacker.analyze_and_plot()