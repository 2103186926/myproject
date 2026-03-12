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

        # 仅允许敏感区域参与缓存（方案 A）：
        # - 例如机密区域 'classified_ops_area' 可以进入“快速缓存层”；
        # - 其他区域（如 public_archive_data）始终走慢路径，保证对比组真正代表“冷数据”。
        self.cacheable_regions = {"classified_ops_area"}
        
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
            # 仅对可缓存区域进行缓存判定与更新时间（方案 A）：
            # - 例如 'classified_ops_area' 会被放入缓存并享受低延迟；
            # - 'public_archive_data' 等非敏感区域永远不命中缓存，始终走慢路径。
            if region_id in self.cacheable_regions and region_id in self._server_side_cache:
                last_access = self._server_side_cache[region_id]  # 获取区域最后一次访问时间
                if time.time() - last_access < 1.0: 
                    is_cached = True  # 缓存命中
            
            # 更新访问时间（仅限可缓存区域，避免攻击者把对照组“加热”成缓存数据）
            if region_id in self.cacheable_regions:
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
        """执行攻击采样序列（方案 B：交替采样冷 vs 热）"""
        print("\n[Attacker] === 开始侧信道探测序列（交替冷/热） ===")
        
        # 这里不再按区域分块采样，而是每一轮都依次对：
        #   1) 冷缓存对照组 'public_archive_data'（始终不参与缓存，来自方案 A）
        #   2) 热缓存敏感组 'classified_ops_area'（受害者高频访问并可缓存）
        # 进行一对测量，保证每次循环都得到一组“冷 vs 热”的样本。
        cold_region_id = 'public_archive_data'
        hot_region_id = 'classified_ops_area'

        for i in range(self.sample_count):  # 保持原有采样次数设置
            # 先测量对照组：由于方案 A 限制其不可缓存，这里始终代表“冷路径”
            cold_latency = self._measure_single_query(cold_region_id)
            self.measurements['control_cold'].append(cold_latency)

            # 再测量敏感组：受害者线程持续访问 + 可缓存策略，使其代表“热路径”
            hot_latency = self._measure_single_query(hot_region_id)
            self.measurements['target_hot'].append(hot_latency)

            # 定期打印进度，并加入轻微休眠，避免持续高QPS触发简单防护
            if i % 100 == 0:
                print(f"[Attacker] 采样进度: {i}/{self.sample_count}")
                time.sleep(0.001)

    def analyze_results(self):
        """
        增强版统计分析（在原基础上扩展）：
        1. 数据清洗：IQR 规则剔除离群值
        2. 描述性统计：均值/标准差/中位数/IQR + 95%置信区间
        3. 参数检验：Welch's T-test（不假设方差齐性）
        4. 效应量：Cohen's d（衡量差异大小的“实际意义”）
        5. 前提条件检查：正态性、方差齐性（提示独立性假设）
        6. 非参数检验：正态性不满足时使用 Mann–Whitney U
        7. 检验功效：Power（优先 statsmodels，缺失时用正态近似兜底）
        8. 可视化：原始数据 vs 清洗后数据（直方图保存为PNG）
        """
        print("\n[Attacker] === 统计分析报告（增强版）===")

        # ------------------------------
        # 0) 数据准备
        # ------------------------------
        cold_data = np.array(self.measurements['control_cold'])  # 冷缓存（无人访问）延迟（纳秒）
        hot_data = np.array(self.measurements['target_hot'])     # 热缓存（受害者访问）延迟（纳秒）

        # 样本量过小会导致统计量不稳定
        if len(cold_data) < 3 or len(hot_data) < 3:
            print("[ERROR] 样本量不足，无法进行统计分析。")
            print(f"    Cold={len(cold_data)}, Hot={len(hot_data)}")
            return

        # ------------------------------
        # 1) 数据清洗：IQR 离群值剔除
        # ------------------------------
        def remove_outliers(data):
            """使用 1.5*IQR 规则剔除离群值"""
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1

            # 当IQR=0时，说明数据过于集中，直接返回原数据
            if iqr == 0:
                return data

            low = q1 - 1.5 * iqr
            high = q3 + 1.5 * iqr
            return data[(data >= low) & (data <= high)]

        cold_clean = remove_outliers(cold_data)
        hot_clean = remove_outliers(hot_data)

        # 清洗后仍需保证最小样本量
        if len(cold_clean) < 3 or len(hot_clean) < 3:
            print("[ERROR] 清洗后样本量不足，无法进行统计分析。")
            print(f"    Cold={len(cold_clean)}/{len(cold_data)}, Hot={len(hot_clean)}/{len(hot_data)}")
            return

        print(f"    [Data Cleaning] Cold={len(cold_clean)}/{len(cold_data)}, Hot={len(hot_clean)}/{len(hot_data)}")

        # ------------------------------
        # 2) 描述性统计
        # ------------------------------
        def describe(data):
            """输出常用描述统计量（std 使用样本标准差 ddof=1）"""
            return {
                'n': int(len(data)),
                'mean': float(np.mean(data)),
                'std': float(np.std(data, ddof=1)),
                'median': float(np.median(data)),
                'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
            }

        cold_desc = describe(cold_clean)
        hot_desc = describe(hot_clean)

        # 置信区间：均值 ± t_{alpha/2, n-1} * SEM
        from scipy.stats import t as t_dist

        def confidence_interval(data, confidence=0.95):
            """计算均值的置信区间（t分布）"""
            data = np.asarray(data)
            n = len(data)
            mean = np.mean(data)
            se = stats.sem(data)  # 标准误
            if n <= 1 or not np.isfinite(se):
                return float('nan'), float('nan')
            h = se * t_dist.ppf((1 + confidence) / 2, n - 1)
            return mean - h, mean + h

        cold_ci = confidence_interval(cold_clean)
        hot_ci = confidence_interval(hot_clean)

        mean_cold = cold_desc['mean']
        mean_hot = hot_desc['mean']
        delta = mean_cold - mean_hot

        # ------------------------------
        # 3) 参数检验：Welch T-test（不假设方差齐性）
        # ------------------------------
        # 零假设 H0：两组均值相等（不存在缓存差异）
        t_stat, p_val = stats.ttest_ind(cold_clean, hot_clean, equal_var=False)

        # ------------------------------
        # 4) 效应量：Cohen's d
        # ------------------------------
        # 注意：合并标准差需要两组的样本量与标准差（原版只算了一组std不够）
        def cohens_d(a, b):
            """Cohen's d（使用合并标准差 Sp）"""
            a = np.asarray(a)
            b = np.asarray(b)
            n1 = len(a)
            n2 = len(b)

            s1 = np.std(a, ddof=1)
            s2 = np.std(b, ddof=1)

            denom = n1 + n2 - 2
            if denom <= 0:
                return float('nan')

            sp = np.sqrt(((n1 - 1) * (s1 ** 2) + (n2 - 1) * (s2 ** 2)) / denom)
            if sp == 0 or not np.isfinite(sp):
                return float('nan')

            return (np.mean(a) - np.mean(b)) / sp

        effect_size_d = cohens_d(cold_clean, hot_clean)

        # ------------------------------
        # 5) 输出：描述性统计 + 检验结果
        # ------------------------------
        print("\n" + "=" * 60)
        print("统计分析结果")
        print("=" * 60)

        print("\n1. 描述性统计（清洗后）:")
        print(
            f"   冷缓存: n={cold_desc['n']}, mean={cold_desc['mean']/1000:.2f} μs, std={cold_desc['std']/1000:.2f} μs, "
            f"median={cold_desc['median']/1000:.2f} μs, IQR={cold_desc['iqr']/1000:.2f} μs, "
            f"95% CI={cold_ci[0]/1000:.2f}-{cold_ci[1]/1000:.2f} μs"
        )
        print(
            f"   热缓存: n={hot_desc['n']}, mean={hot_desc['mean']/1000:.2f} μs, std={hot_desc['std']/1000:.2f} μs, "
            f"median={hot_desc['median']/1000:.2f} μs, IQR={hot_desc['iqr']/1000:.2f} μs, "
            f"95% CI={hot_ci[0]/1000:.2f}-{hot_ci[1]/1000:.2f} μs"
        )

        print("\n2. 差异检验（Welch T-test）:")
        print(f"   延迟差异(Cold-Hot): {delta/1000:.2f} μs")
        print(f"   T统计量: {t_stat:.4f}")
        print(f"   P值: {p_val:.10e}")  # 科学计数法

        print("\n3. 效应量（差异大小，用于判断实际意义）:")
        print(f"   Cohen's d (Cold vs Hot): {effect_size_d:.4f}")

        # ------------------------------
        # 6) 统计检验的前提条件（诊断性检查）
        # ------------------------------
        # 说明：
        # - t检验常见前提：样本独立、（近似）正态、方差齐性（Welch放宽齐性要求）
        # - 其中“独立性”一般依赖采样设计，无法仅靠统计检验自动证明
        print("\n4. 统计检验前提条件（诊断性检查）:")

        # 正态性检验：样本量较小时用 Shapiro-Wilk；样本量很大时可用 normaltest
        normality_name = "N/A"
        cold_norm_p = float('nan')
        hot_norm_p = float('nan')
        levene_p = float('nan')

        try:
            if len(cold_clean) <= 5000 and len(hot_clean) <= 5000:
                s_cold = stats.shapiro(cold_clean)
                s_hot = stats.shapiro(hot_clean)
                cold_norm_p = float(s_cold.pvalue)
                hot_norm_p = float(s_hot.pvalue)
                normality_name = "Shapiro-Wilk"
            else:
                n_cold = stats.normaltest(cold_clean)
                n_hot = stats.normaltest(hot_clean)
                cold_norm_p = float(n_cold.pvalue)
                hot_norm_p = float(n_hot.pvalue)
                normality_name = "D'Agostino K^2"

            # 方差齐性：Levene（median 更稳健）；虽然Welch不要求方差相等，但报告有助于解释
            lev = stats.levene(cold_clean, hot_clean, center='median')
            levene_p = float(lev.pvalue)
        except Exception as e:
            print(f"   前提检验执行失败: {e}")

        print(f"   正态性检验({normality_name}) P值: Cold={cold_norm_p:.3e}, Hot={hot_norm_p:.3e}")
        print(f"   方差齐性检验(Levene, median) P值: {levene_p:.3e}")
        print("   独立性假设: 需要确保样本来自独立请求/独立时间点；该项依赖采样设计。")

        # 当任一组不满足正态性（p < 0.05）时，额外报告非参数检验结果
        use_nonparametric = (
            np.isfinite(cold_norm_p)
            and np.isfinite(hot_norm_p)
            and (cold_norm_p < 0.05 or hot_norm_p < 0.05)
        )

        # ------------------------------
        # 7) 非参数检验：Mann–Whitney U（正态性不满足时）
        # ------------------------------
        if use_nonparametric:
            print("\n5. 非参数检验（正态性不满足时）:")
            try:
                u_stat, u_p = stats.mannwhitneyu(cold_clean, hot_clean, alternative='two-sided')

                # Rank-biserial 相关：一种常用的非参数效应量（范围约[-1, 1]）
                n1 = len(cold_clean)
                n2 = len(hot_clean)
                rank_biserial = 1.0 - (2.0 * float(u_stat)) / float(n1 * n2)

                print(f"   Mann-Whitney U: U={float(u_stat):.1f}, P值={float(u_p):.10e}")
                print(f"   Rank-biserial r: {rank_biserial:.4f}")
            except Exception as e:
                print(f"   非参数检验执行失败: {e}")

        # ------------------------------
        # 8) 统计功效（Power）
        # ------------------------------
        # 说明：
        # - 功效 = 在真实存在差异时，检验能检测到差异的概率
        # - 本脚本用 Cohen's d 作为效应量输入，给出近似功效；
        # - alpha 同时报告 0.001（严格）与 0.05（常见）两种阈值。
        print("\n6. 统计功效（Power）:")

        alpha_strict = 0.001
        alpha_relaxed = 0.05

        def approx_power_two_sample_t(d, n1, n2, alpha):
            """两独立样本t检验功效的正态近似（缺少statsmodels时兜底）"""
            d = float(abs(d))
            if not np.isfinite(d) or d == 0 or n1 < 2 or n2 < 2:
                return float('nan')

            # 有效样本量（两组合并的等效规模）
            n_eff = (n1 * n2) / (n1 + n2)
            delta_n = d * np.sqrt(n_eff)

            z = stats.norm.ppf(1 - alpha / 2)

            # 近似计算：beta 为第二类错误概率
            beta = stats.norm.cdf(z - delta_n) - stats.norm.cdf(-z - delta_n)
            return float(1 - beta)

        n1 = len(cold_clean)
        n2 = len(hot_clean)

        power_strict = float('nan')
        power_relaxed = float('nan')
        power_source = "normal-approx"

        try:
            from statsmodels.stats.power import TTestIndPower

            analysis = TTestIndPower()
            ratio = n2 / n1
            power_strict = float(
                analysis.power(
                    effect_size=float(abs(effect_size_d)),
                    nobs1=n1,
                    alpha=alpha_strict,
                    ratio=ratio,
                    alternative='two-sided'
                )
            )
            power_relaxed = float(
                analysis.power(
                    effect_size=float(abs(effect_size_d)),
                    nobs1=n1,
                    alpha=alpha_relaxed,
                    ratio=ratio,
                    alternative='two-sided'
                )
            )
            power_source = "statsmodels"
        except Exception:
            power_strict = approx_power_two_sample_t(effect_size_d, n1, n2, alpha_strict)
            power_relaxed = approx_power_two_sample_t(effect_size_d, n1, n2, alpha_relaxed)

        print(f"   Power (alpha={alpha_strict}): {power_strict:.3f} [{power_source}]")
        print(f"   Power (alpha={alpha_relaxed}): {power_relaxed:.3f} [{power_source}]")

        # ------------------------------
        # 9) 可视化：原始 vs 清洗后（保存图像文件）
        # ------------------------------
        # 注意：为了兼容无GUI环境，强制使用Agg后端并保存为PNG
        print("\n7. 可视化（原始 vs 清洗后）:")
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            def plot_hist(ax, data, title):
                # 将纳秒转换为微秒后绘图，便于阅读
                ax.hist(data / 1000.0, bins=40, alpha=0.85)
                ax.set_title(title)
                ax.set_xlabel("latency (μs)")
                ax.set_ylabel("count")

            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            plot_hist(axes[0, 0], cold_data, "Cold Raw")
            plot_hist(axes[0, 1], hot_data, "Hot Raw")
            plot_hist(axes[1, 0], cold_clean, "Cold Clean")
            plot_hist(axes[1, 1], hot_clean, "Hot Clean")
            fig.tight_layout()

            ts = time.strftime("%Y%m%d_%H%M%S")
            out_path = f"side_channel_analysis_{ts}.png"
            fig.savefig(out_path, dpi=150)
            plt.close(fig)
            print(f"   已保存图像: {out_path}")
        except Exception as e:
            print(f"   可视化跳过（matplotlib不可用或后端不可用）: {e}")

        # ------------------------------
        # 10) 最终判定：统计显著 + 效应量 + 方向一致
        # ------------------------------
        print("\n" + "-" * 40)

        # 统计显著性（严格阈值保持与原版一致）
        significance = p_val < 0.001

        # 实际意义：效应量阈值（经验规则：0.2小、0.5中、0.8大）
        practical_significance = np.isfinite(effect_size_d) and abs(effect_size_d) > 0.5

        # 方向性：热缓存应当更快（mean_hot < mean_cold）
        direction_ok = mean_hot < mean_cold

        if significance and practical_significance and direction_ok:
            print("[RESULT] >>> 攻击成功 (SUCCESS) <<<")
            print("    统计显著且效应量足够大（差异具有实际意义）。")
            print(f"    确认目标区域 '{'classified_ops_area'}' 存在活跃访问。")
            print("    推断：该区域已被其他用户（受害者）加载到缓存中。")
            print("    情报价值：高。受害者正在关注此区域。")
        elif significance and direction_ok:
            print("[RESULT] [WARN] 统计显著但效应量偏小")
            print("    攻击可能成功，但差异较小，可能难以在更高噪声环境中稳定复现。")
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
