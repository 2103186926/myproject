# malicious_side_channel_advanced.py
import time
import numpy as np
import random
from collections import defaultdict  # 用于记录每个区域的访问次数
from scipy import stats
import threading

# ==========================================
# 1. 高精度模拟环境 (High-Fidelity Environment)
# ==========================================
class SharedMemoryDataService:
    """
    模拟一个共享资源的云端数据服务。
    使用'忙等待'模拟精确的CPU/内存延迟，而非不准确的sleep。
    """
    def __init__(self):
        # 模拟服务器端的缓存状态：Key -> Last Access Time
        self._server_side_cache = {}  # 缓存状态，记录每个区域最后一次访问时间
        self._cache_lock = threading.Lock()  # 缓存锁，确保线程安全访问缓存状态
        
        # 模拟物理延迟参数 (纳秒 ns)
        self.LATENCY_DRAM = 100 * 1000      # 100us (缓存命中/内存读取)
        self.LATENCY_DISK = 500 * 1000      # 500us (缓存未命中/磁盘I/O)
        self.JITTER_STD = 20 * 1000         # 20us 的处理噪声

    def _busy_wait(self, duration_ns):
        """
        使用CPU空转来精确模拟处理延迟。
        Python的time.sleep精度太低，无法模拟微秒级侧信道。
        """
        target = time.perf_counter_ns() + duration_ns
        while time.perf_counter_ns() < target:
            pass # 消耗CPU周期

    def query_data(self, region_id):
        """处理数据请求，根据缓存状态产生不同的响应时间"""
        request_start = time.perf_counter_ns()  # 记录请求开始时间(纳秒)
        
        # 1. 检查缓存状态
        is_cached = False  # 假设缓存未命中
        with self._cache_lock:  # 加锁确保线程安全访问缓存状态
            # 如果数据在最近 1秒内被访问过，则认为在缓存热区中
            if region_id in self._server_side_cache:
                last_access = self._server_side_cache[region_id]  # 获取区域最后一次访问时间
                if time.time() - last_access < 1.0: 
                    is_cached = True  # 缓存命中
            
            # 更新访问时间（LRU策略）
            self._server_side_cache[region_id] = time.time()

        # 2. 计算模拟延迟
        base_delay = self.LATENCY_DRAM if is_cached else self.LATENCY_DISK
        
        # 3. 添加高斯噪声 (Jitter)，模拟真实物理波动
        noise = np.random.normal(0, self.JITTER_STD)
        final_delay = max(1000, base_delay + noise) # 确保延迟为正
        
        # 4. 执行忙等待模拟处理时间
        self._busy_wait(final_delay)
        
        return "DATA_PAYLOAD"  # 实际应用中可能返回真实数据

# ==========================================
# 2. 受害者模拟 (Victim Simulation)
# ==========================================
def simulate_victim_activity(service, sensitive_region):
    """
    模拟合法的受害者（如科考船或管理员）正在频繁访问敏感区域。
    这会将敏感数据加载到缓存中。
    参数：
        service (SharedMemoryDataService): 目标服务实例
        sensitive_region (str): 敏感区域ID，如"classified_ops_area"
    """
    print(f"[Victim] 合法用户开始频繁访问敏感区域: {sensitive_region}...")
    for _ in range(500):
        service.query_data(sensitive_region)
        time.sleep(0.05) # 每50ms访问一次，保持缓存“热”

# ==========================================
# 3. 高级侧信道攻击者 (Sophisticated Attacker)
# ==========================================
class AdvancedSideChannelAttacker:
    def __init__(self, target_service):
        self.service = target_service  # 目标服务，即模拟的共享资源服务
        self.measurements = defaultdict(list)  # 攻击测量数据，记录每个区域的延迟测量值
        self.sample_count = 1000  # 增加采样数以提高统计显著性
        
    def _measure_single_query(self, region_id):
        """执行单次精确计时测量"""
        # 垃圾回收控制（可选）：gc.disable() 可以减少Python自身干扰，这里暂略
        
        t0 = time.perf_counter_ns()
        _ = self.service.query_data(region_id)  # 执行查询，获取数据（实际应用中可能返回真实数据）
        t1 = time.perf_counter_ns()
        
        return t1 - t0

    def calibrate(self):
        """校准阶段：测量基准噪声"""
        print("[Attacker] 正在校准计时器开销...")
        overhead = []  # 记录每次测量的开销（纳秒）
        for _ in range(1000):
            t0 = time.perf_counter_ns()
            t1 = time.perf_counter_ns()
            overhead.append(t1 - t0)
        print(f"[Attacker] 计时器平均开销: {np.mean(overhead):.2f} ns")

    def run_attack(self):
        print("\n[Attacker] === 开始侧信道探测序列 ===")
        
        # 定义目标
        targets = {
            'control_cold': 'public_archive_data',  # 冷数据（无人访问）
            'target_hot': 'classified_ops_area'     # 敏感数据（受害者正在访问）
        }

        # 1. 采集数据
        for label, region_id in targets.items():
            print(f"[Attacker] 正在采集样本: {label} (Region: {region_id})...")
            
            # 攻击者进行大量重复采样
            for i in range(self.sample_count):  # 1000
                latency = self._measure_single_query(region_id)  # 测量延迟（纳秒）
                self.measurements[label].append(latency)
                
                # 随机微小休眠，防止被防火墙判定为DoS
                if i % 100 == 0:
                    time.sleep(0.001)

    def analyze_results(self):
        """
        高级统计分析：
        1. 异常值剔除 (IQR Filter)
        2. 韦尔奇T检验 (Welch's T-test)
        3. 效应量计算 (Cohen's d)
        """
        print("\n[Attacker] === 统计分析报告 ===")
        
        cold_data = np.array(self.measurements['control_cold'])  # 冷数据（无人访问）延迟（纳秒）
        hot_data = np.array(self.measurements['target_hot'])  # 敏感数据（受害者正在访问）延迟（纳秒）

        # --- 步骤 1: 数据清洗 (去除网络抖动造成的离群值) ---
        def remove_outliers(data):
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            # 保留 ±1.5 IQR 范围内的数据
            return data[(data >= q1 - 1.5*iqr) & (data <= q3 + 1.5*iqr)]

        cold_clean = remove_outliers(cold_data)
        hot_clean = remove_outliers(hot_data)

        print(f"    [Data Cleaning] 剔除离群值后样本数: Cold={len(cold_clean)}, Hot={len(hot_clean)}")
        
        # --- 步骤 2: 计算统计量 ---
        mean_cold = np.mean(cold_clean)
        mean_hot = np.mean(hot_clean)
        std_cold = np.std(cold_clean)
        
        print(f"    [Stats] Cold Region Avg: {mean_cold/1000:.2f} μs (±{std_cold/1000:.2f})")
        print(f"    [Stats] Hot Region Avg : {mean_hot/1000:.2f} μs")
        print(f"    [Delta] 延迟差异: {(mean_cold - mean_hot)/1000:.2f} μs")

        # --- 步骤 3: 假设检验 (Welch's T-test) ---
        # 零假设 H0: 两组数据的均值相等 (即没有缓存差异)
        t_stat, p_val = stats.ttest_ind(cold_clean, hot_clean, equal_var=False)
        
        print(f"    [T-Test] T-statistic: {t_stat:.4f}")
        print(f"    [T-Test] P-value: {p_val:.10e}") # 科学计数法

        # --- 步骤 4: 判定 ---
        print("-" * 40)
        # 判定标准：P值极小 且 目标区域显著更快
        if p_val < 0.001 and mean_hot < mean_cold:
            print("[RESULT] >>> 攻击成功 (SUCCESS) <<<")
            print(f"    确认目标区域 '{'classified_ops_area'}' 存在活跃访问。")
            print("    推断：该区域已被其他用户（受害者）加载到缓存中。")
            print("    情报价值：高。受害者正在关注此区域。")
        else:
            print("[RESULT] 攻击失败 (INCONCLUSIVE). 未检测到显著的时间差异。")

# ==========================================
# 主程序
# ==========================================
if __name__ == "__main__":
    # 1. 初始化云端环境
    cloud_service = SharedMemoryDataService()
    
    # 2. 启动受害者线程 (在后台产生“热”数据)
    # 这模拟了必须存在的外部条件：如果没有人访问敏感数据，侧信道攻击通常无效
    victim_thread = threading.Thread(
        target=simulate_victim_activity,  # 受害者线程，模拟用户访问敏感数据
        args=(cloud_service, 'classified_ops_area')  # 受害者访问的敏感数据区域
    )
    victim_thread.daemon = True  # 守护线程，主线程结束时自动结束
    victim_thread.start()  # 启动受害者线程
    
    # 等待受害者预热缓存
    time.sleep(0.5)
    
    # 3. 攻击者开始行动
    attacker = AdvancedSideChannelAttacker(cloud_service)  # 初始化攻击者
    attacker.calibrate()  # 校准攻击者，测量基准延迟
    attacker.run_attack()  # 运行攻击，采集数据
    attacker.analyze_results()  # 分析攻击结果，判断是否成功
