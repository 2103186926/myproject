## debug.py脚本说明

这个脚本整体是在**模拟一个通过“响应时间差异”来窃取信息的侧信道攻击流程**，并用统计学方法（T 检验）来判断这种时间差异是不是“真的存在”，从而有攻击价值。

可以分成三层目的来看：

---

**1. 做了什么：从 API 响应时间里“挖情报”**

- `MockDataClient`（`debug.py:12-36`）模拟了一个“云数据平台”的接口：
  - 某些区域（例如 `suspected_dense_region`）被认为是热门或敏感数据，**会被缓存**，延迟设为约 40 微秒。
  - 其他区域（如 `public_region`, `sparse_region`）是冷数据或普通数据，延迟约 150 微秒。
  - 再加上一点随机抖动 `jitter` 来模拟真实网络波动。

- `SideChannelAttacker.timing_attack_on_data_access`（`debug.py:67-110`）做的事：
  - 对三个区域反复发起请求：`public_region`、`suspected_dense_region`、`sparse_region`。
  - 每次请求前调用 `flush_cache()`（`debug.py:58-66`）用 64MB 大数组把缓存“刷满”，模拟攻击者刻意干扰缓存，让自己测到的差异更清晰。
  - 用高精度计时器 `time.perf_counter_ns` 测每次请求的耗时，并把结果按区域存到 `self.timing_measurements[region_name]` 里。
  - 这样就得到了**“每个区域的访问时间分布”**。

这一步的直接目的：  
通过大量采样，**掌握“哪个区域访问更快/更慢”的统计特征**。

---

**2. 为什么要用 T 检验：把“感觉好像更快”变成“统计上显著更快”**

- `statistical_analysis`（`debug.py:111-146`）的逻辑：
  - 把 `public_region` 作为**基准区域**，计算它的平均延迟 `base_mean`。
  - 对其他区域（`suspected_dense_region`, `sparse_region`）分别：
    - 计算各自的平均延迟 `current_mean`。
    - 使用 `stats.ttest_ind(base_times, times, equal_var=False)` 做**独立样本 T 检验**，得到 `p_value`。
  - 然后：
    - 如果 `p_value < 0.001` 且 `current_mean < base_mean`：
      - 判定该区域“显著更快”（`[!!!]ALERT`）
      - 推断“数据可能已被其他用户缓存（高活动区域）”。

为什么要这么麻烦用 T 检验？

- 因为实际环境里有抖动（脚本中用 `random.normalvariate` 模拟），单次请求的快慢可能是随机的。
- 攻击者关心的不只是“这次看起来快一点”，而是：
  - **在统计意义上，这个区域是否真的平均更快**？
  - **这种差异是否足够大，可以排除掉“纯属随机波动”的可能性？**
- 独立样本 T 检验就是在做这个判断：
  - 原假设：两个区域的平均延迟没有差别。
  - 如果 `p_value` 很小（比如 < 0.001），说明“在没有真实差异的前提下，出现这么大的平均差异的概率几乎为 0”，于是可以认为**这个区域确实显著更快**。

所以第二步的目的：  
用统计学把微弱、噪声中的时间差“放大、确认”，让攻击结论更可靠。

---

**3. 最终想达到什么：通过“谁被缓存”来推断“谁是敏感/热门数据”**

结合上面两部分，这个脚本模拟的攻击目标是：

- **不直接看数据内容，只看访问时间**
- 通过时间差来推断：
  - 哪些区域经常被访问（因此被缓存）
  - 哪些区域是“热点”或“高活动区域”
- 这些“热点信息”本身就可能是机密：
  - 比如数据集名字叫 `classified_submarine_data_v1`（`debug.py:69`），暗示是“潜艇活动数据”。
  - 如果攻击者发现某个经纬度范围（`suspected_dense_region`）总是显著更快，说明这块区域的相关数据可能频繁被合法用户访问。
  - 进一步可以推断：这里可能存在大量目标活动（例如潜艇密集活动区、军事热点、重要基础设施周边等）。

现实含义：

- 即使平台加密了数据内容，攻击者不需要解密，只凭**缓存命中带来的延迟差**，就能：
  - 推断其他用户在查哪些位置、哪些时间段；
  - 推断哪些区域“有东西”、哪些“几乎没人看”；
- 这就是典型的**基于缓存/时间的侧信道攻击**：  
  利用了系统本身的性能优化（缓存）作为“信息泄露通道”。

---

**总结一句话：**

这个脚本的最终目的，是**演示攻击者如何利用 API 响应时间的微小差异（缓存命中 vs 未命中），通过大量采样 + T 检验，从统计上确认哪些区域被频繁访问，从而推断出敏感/高活动区域**，即通过侧信道泄露其他用户行为或敏感数据分布的信息。



## debug_Pro.py脚本说明

这个 `debug_Pro.py` 可以理解为：  
在 `debug.py` 的基础上，把“玩具级”的侧信道攻击示例，升级成**更接近真实攻击场景的高精度、高鲁棒性侧信道攻击模拟**。

我分三块说：

---

**一、整体目的：更真实、更可靠地用时间侧信道判断“谁是敏感热点”**

- `SharedMemoryDataService`（`debug_Pro.py:12-63`）模拟一个云端共享数据服务，内部有“服务器端缓存”。
- `simulate_victim_activity`（`debug_Pro.py:67-76`）模拟合法受害者频繁访问某个敏感区域，比如 `'classified_ops_area'`。
- `AdvancedSideChannelAttacker`（`debug_Pro.py:80-179`）是高级攻击者：
  - 精确测量访问不同区域的响应时间（冷数据 vs 敏感热点）。
  - 对大量测量结果做“数据清洗 + 高级统计分析”，判断敏感区域是否处于缓存中。
- 主程序里（`debug_Pro.py:183-203`）先启动受害者线程预热缓存，再由攻击者开始采样和分析。

所以：  
它的根本目的仍然是——**通过响应时间差异，推断敏感区域是否正在被其他用户频繁访问**，但实现方式更贴近真实系统，并且在统计上更严谨。

---

**二、具体做了哪些“升级/优化”**

和 `debug.py` 相比，主要有这几类优化：

1. **更真实的缓存行为与延迟模型**

   - 引入了真正的“服务器侧缓存状态”：
     - `self._server_side_cache`（`debug_Pro.py:18-20`）按 `region_id` 记录最近访问时间。
     - 最近 1 秒内被访问过就认为是“热数据”（`debug_Pro.py:44-47`）。
   - 延迟区分：
     - `LATENCY_DRAM = 100us`，模拟缓存命中 / 内存访问（`debug_Pro.py:23`）。
     - `LATENCY_DISK = 500us`，模拟缓存未命中 / 磁盘 I/O（`debug_Pro.py:24`）。
   - 使用高斯噪声 `JITTER_STD`（`debug_Pro.py:25, 56`）模拟真实的处理/网络抖动。

   对比 `debug.py`：  
   原本只是固定两种 `sleep` 延迟（40us vs 150us），这里则有更细致的缓存策略和硬件层次延迟抽象。

2. **使用忙等待 `_busy_wait` 模拟纳秒级延迟**

   - `_busy_wait`（`debug_Pro.py:27-34`）用 `time.perf_counter_ns()` 做目标时间点，然后在 while 循环里空转，直到时间到达。
   - `query_data` 用 `_busy_wait(final_delay)` 而不是 `time.sleep()`（`debug_Pro.py:59-60`）。

   目的：  
   - `time.sleep()` 精度太粗（毫秒级），对微秒甚至几十微秒差值会淹没在系统调度误差里。
   - 忙等待虽然浪费 CPU，但可以更精确地控制延迟，**更适合模拟微小时间侧信道**。

3. **加入真实的“受害者活动线程”**

   - `simulate_victim_activity`（`debug_Pro.py:67-76`）循环访问 `sensitive_region`：
     - 每 50ms 访问一次，持续 50 次，使其一直处在“热缓存”状态。
   - 主程序中通过 `threading.Thread` 启动该函数（`debug_Pro.py:189-194`），并设置为守护线程。

   意义：
   - 强调一个现实前提：**如果没有受害者在访问敏感数据，缓存就不会热，时间侧信道也无法区分。**
   - 让攻击环境更接近“多个用户共享同一服务”的真实云环境。

4. **攻击者端增加“计时器校准”和更大样本量**

   - `self.sample_count = 1000`（`debug_Pro.py:84`）：比 `debug.py` 的 500 更大，提高统计显著性。
   - `calibrate()`（`debug_Pro.py:96-105`）：
     - 连续测量 1000 次 `perf_counter_ns` 本身的调用开销。
     - 输出计时器平均 overhead，帮助理解测量误差级别。

   目的：
   - 控制和量化“测量工具本身”的噪声。
   - 提高采样数量，让统计检验更有力度。

5. **高级统计分析：数据清洗 + Welch T 检验 + 效应量思路**

   在 `analyze_results` 中（`debug_Pro.py:128-179`）：

   - **异常值剔除（IQR Filter）**：
     - `remove_outliers` 使用四分位数 + 1.5 IQR（`debug_Pro.py:141-146`）。
     - 去除因为极端网络抖动或系统调度导致的“离群样本”，得到 `cold_clean`, `hot_clean`（`debug_Pro.py:148-149`）。
   - **分别计算清洗后的均值和标准差**（`debug_Pro.py:154-160`），打印延迟差异。
   - **Welch’s T-test**（`debug_Pro.py:163-167`）：
     - `stats.ttest_ind(..., equal_var=False)`，即不假设方差相等，更符合实际噪声不均的情况。
   - 给出显著性判断：
     - 若 `p_val < 0.001` 且 `mean_hot < mean_cold`，则判定“攻击成功”（`debug_Pro.py:172-177`），确认目标区域处于活跃状态。

   相比 `debug.py`：
   - `debug.py` 只有一个简单的 T 检验，没有做异常值剔除，也没有区分不同方差情况。
   - `debug_Pro.py` 更像真实安全研究论文里会做的分析流程。

---

**三、为什么要做这些优化？背后的动机**

可以概括成三个层面：

1. **从玩具示例走向“研究级”模拟**

   - `debug.py` 更像是“教学 Demo”：用 sleep 模拟快慢，直接做 T 检验，看一眼就懂原理。
   - `debug_Pro.py` 则：
     - 引入了共享缓存模型、多线程受害者。
     - 使用忙等待实现纳秒级精度。
     - 做了采样校准、异常值过滤、Welch T 检验等。
     目的是：展示一个**更严谨、可发表论文级别的侧信道攻击流程**。

2. **验证攻击在“噪声环境”下仍然可行**

   - 现实中 CPU/网络/系统调度噪声很多，不像教材例子那么干净。
   - 通过：
     - 更大样本数。
     - IQR 剔除离群值。
     - 更合适的统计方法（Welch T）。
     来证明：**即便存在较大噪声，只要方法正确，缓存引起的时间差仍然可以被可靠地检测和利用**。

3. **强调共享服务 + 缓存优化本身是一种“信息泄露渠道”**

   - `SharedMemoryDataService` 的设计（最近 1 秒访问的区域被认定为缓存热区）反映现实中常见的缓存策略（LRU/时间窗口）。
   - 受害者线程代表“正常业务”，攻击者只是旁观者，通过同一接口观察时间差。
   - 脚本通过“攻击成功 (SUCCESS)”打印，将结论直接与“受害者正在关注某区域”挂钩。

   目的在于强调：  
   **即使平台没有暴露任何敏感字段，只要共享缓存 + 可计时接口存在，攻击者就能通过时间侧信道推断出其他用户的行为模式和敏感区域。**

---

**一句话总结：**

`debug_Pro.py` 是在 `debug.py` 的基础上，引入更真实的缓存/受害者行为模型、更高精度的时间模拟和更严格的统计分析，来展示一个**高保真、高鲁棒性的时间侧信道攻击**：  
通过这些优化，攻击结果在“真实噪声环境”下仍然可信，从而更加有说服力地表明——**共享缓存 + 可观察的响应时间 = 一条危险的信息泄露通道**。



## debug_Plus.py脚本说明

整体上，这个 `debug_Plus.py` 是在 `debug_Pro.py` 的基础上，把**“有没有差异”**这件事，升级成了**“差异有多大、靠谱吗、在什么条件下成立”**的完整统计分析版侧信道攻击脚本。

可以分三层来理解：

---

**一、总体目的：从“能不能攻”升级为“攻得有多稳、有多值”**

`debug_Pro.py` 已经能通过响应时间差异判断敏感区域是否处于缓存中，而 `debug_Plus.py` 的核心是把攻击结果做成一整套**严谨统计分析流程**，目标包括：

- 不仅判断：
  - “冷/热缓存延迟是否显著不同？”
- 还要进一步回答：
  - “差异有多大（效应量）？”
  - “前提假设是否成立（正态性/方差齐性）？”
  - “如果前提不成立，结论还能不能站得住（非参数检验）？”
  - “在当前样本量和噪声水平下，这个攻击结论的复现概率有多高（检验功效）？”
  - “数据从分布形态上看是否合理（可视化）？”

换句话说：  
`debug_Plus.py` 想把侧信道攻击的“演示脚本”，做成更像一篇安全/统计论文里会出现的**实验与分析框架**。

---

**二、具体做了哪些优化（相对 debug_Pro.py）**

核心升级几乎都集中在 `AdvancedSideChannelAttacker.analyze_results` 这个函数里  
（`C:\Users\21031\Desktop\myProject\侧信道攻击\debug_Plus.py:131` 起）。

我按功能点拆一下：

1. **更严格的数据清洗：IQR 离群值剔除**

   - 函数 `remove_outliers` 使用四分位数 IQR 规则剔除离群值  
     `debug_Plus.py:160-172`：
     - 计算 Q1、Q3、IQR，保留 \[Q1−1.5·IQR, Q3+1.5·IQR] 区间内的数据。
     - 若 IQR=0（数据极度集中），直接返回原数据，避免全部被“剔空”。

   目的：
   - 去掉由偶发抖动、系统调度、网络 spike 等造成的极端延迟值。
   - 保证后续统计量反映的是**典型行为**而非极端噪声。

2. **完整的描述性统计与置信区间**

   - `describe` 函数输出：
     - 样本量 `n`、均值 `mean`、样本标准差 `std(ddof=1)`、中位数 `median`、IQR  
       `debug_Plus.py:188-196`。
   - 使用 t 分布计算均值的 95% 置信区间 `confidence_interval`  
     `debug_Plus.py:204-213`。
   - 输出中给出：
     - 冷/热缓存均值、标准差、中位数、IQR、95% CI（单位转换为 μs）  
       `debug_Plus.py:261-270`。

   目的：
   - 描述性统计帮助理解分布形状与离散程度；
   - 置信区间给出了“均值估计的不确定性范围”，而不是只有一个点估计。

3. **Cohen’s d 效应量：差异的“实际意义”**

   - 函数 `cohens_d` 使用两组样本量和样本标准差（`ddof=1`）计算合并标准差 `Sp`：  
     `debug_Plus.py:232-250`。
   - 然后 `effect_size_d = cohens_d(cold_clean, hot_clean)`  
     `debug_Plus.py:252`。
   - 输出：
     - `Cohen's d (Cold vs Hot): ...`  
       `debug_Plus.py:278-279`。

   目的：
   - t 检验的 p 值回答的是“是否有差异”，但不告诉你“差异到底大不大”。
   - Cohen’s d 量化了差异规模，可用经验阈值（0.2/0.5/0.8）判断是小/中/大效应。
   - 对侧信道攻击来说，这直接对应了“这一点时间差在现实噪声环境中还有没有利用价值”。

4. **检验前提条件诊断：正态性 + 方差齐性**

   - 正态性：
     - 样本量 <= 5000 时，用 Shapiro–Wilk 检验；否则用 D’Agostino K²：  
       `debug_Plus.py:295-307`。
   - 方差齐性：
     - 使用 Levene 检验（以 median 为中心，更稳健）  
       `debug_Plus.py:309-311`。
   - 输出：
     - 正态性检验 P 值（冷/热两组）  
       `debug_Plus.py:315-316`。
     - Levene P 值；
     - 文字说明：独立性假设由采样设计保障，统计检验无法自动证明  
       `debug_Plus.py:284-287, 317`。

   目的：
   - t 检验的理论前提包括近似正态与方差条件（Welch 已放宽齐性要求），需要检查。
   - 通过这些诊断，脚本可以告诉你：
     - “当前 p 值在多大程度上依赖正态性假设”。

5. **当正态性不满足时的非参数检验：Mann–Whitney U**

   - 如果任意一组正态性检验 P 值 < 0.05，则触发非参数检验：  
     `debug_Plus.py:320-324, 329-343`。
   - 使用 `stats.mannwhitneyu` 做曼–惠特尼 U 检验。
   - 额外计算 rank-biserial 相关 r 作为非参数效应量（范围约 -1~1）  
     `debug_Plus.py:335-337`。

   目的：
   - 在严重偏离正态时，t 检验的结果可信度会降低。
   - 非参数检验不依赖正态假设，通过它可以得到一个**更稳健的备份结论**；
   - rank-biserial r 对应“有多大概率一个样本整体上比另一个更大”，也能直观反映侧信道强度。

6. **统计功效（Power）分析**

   - 先定义正态近似版功效计算 `approx_power_two_sample_t`：  
     `debug_Plus.py:356-370`。
   - 然后尝试使用 `statsmodels.stats.power.TTestIndPower` 精确计算功效：
     - 成功时标记来源为 `"statsmodels"`；失败时退回到正态近似 `"normal-approx"`  
       `debug_Plus.py:379-406`。
   - 分别输出 `alpha=0.001` 和 `alpha=0.05` 下的功效值：  
     `debug_Plus.py:407-408`。

   目的：
   - 功效回答的是：“在**真实有差异**的前提下，这个实验设计（样本量、噪声、效应量）有多大概率能检测到它？”
   - 如果功效很低，即便这次 p 值不显著，也不能说“确实没差异”，可能只是“样本不够/噪声太大”。

7. **数据可视化：原始 vs 清洗后**

   - 使用 `matplotlib`（强制 `Agg` 后端）绘制 2×2 直方图：  
     `debug_Plus.py:415-438`。
     - Cold Raw / Hot Raw / Cold Clean / Hot Clean。
   - 将纳秒转换为微秒绘图，方便阅读：  
     `debug_Plus.py:420-425`。
   - 自动保存到 `side_channel_analysis_时间戳.png`，并输出路径；
   - 如果环境没有 `matplotlib` 或后端不可用，会打印提示但不中断分析：  
     `debug_Plus.py:439-440`。

   目的：
   - 直接看分布形状能肉眼判断是否存在长尾、双峰、严重偏态等；
   - 对安全研究中调参、解释异常结果非常重要。

8. **最终结论更精细：显著性 + 效应量 + 方向性**

   - 汇总判断逻辑：  
     `debug_Plus.py:445-466`。
     - `significance = (p_val < 0.001)`  
     - `practical_significance = (|d| > 0.5)`  
     - `direction_ok = (mean_hot < mean_cold)`（热缓存更快才符合攻击预期）
   - 三种情况：
     - 显著 + 效应量足够大 + 方向正确 → 明确“攻击成功，情报价值高”；
     - 显著 + 方向正确但效应量偏小 → 给出“攻击可能成功，但差异较小”的警告；
     - 否则 → “攻击失败/证据不足”。

   目的：
   - 避免仅凭“p<0.001”就一刀切下结论；
   - 将**统计显著性**与**实际利用价值（效应量 + 方向）**分开讨论，更符合攻击者视角。

---

**三、为什么要做这些优化？（背后的研究/攻击动机）**

从侧信道攻击/安全研究的角度，这些优化有几个直接收益：

1. **强化结论的可信度**

   - 单一 p 值容易“过拟合”当前实验：  
     样本多时很容易显著；样本少时不显著也不能证明没差。
   - `debug_Plus.py` 通过：
     - 效应量（Cohen’s d / rank-biserial r）
     - 置信区间
     - 功效 Power
     - 前提检验与非参数备份检验
     让“有没有侧信道泄露”的判断变得更可靠、可复现。

2. **量化攻击强度与实战价值**

   - 对攻击者来说，仅仅知道“理论上能攻”不够，还要知道：
     - 在真实云环境（更大噪声、更多干扰）中，这个时间差是否足够大、足够稳定。
   - 效应量 + 功效 + 可视化共同回答：
     - “这个攻击在实战环境中，是否值得投入成本去实现与隐藏？”

3. **更接近学术/工程上的“严谨实验”**

   - debug 版本是教学示例，Pro 是工程级模拟；Plus 则更接近**论文级实验设计**：
     - 有数据清洗、有假设检验、有效应量、有功效分析、有图、有前提诊断。
   - 这样一份脚本，既能用来演示攻击，也能用来做严肃实验（改参数、改噪声模型、改延迟参数）并评估不同防御策略的效果。

4. **为后续扩展/防御评估打基础**

   - 以后如果你在服务端加入某些防御措施（比如随机延迟、批处理、请求合并等），只要重新跑这个脚本：
     - d 变小、power 降低 → 说明防御在统计上确实削弱了侧信道；
     - 直方图、正态性/非参数检验结果也会发生可观察的变化。
   - `debug_Plus.py` 就可以作为一个通用的**“侧信道攻击评估基准脚本”**使用。

---

**一句话总结：**

`debug_Plus.py` 在 `debug_Pro.py` 的基础上，把侧信道攻击从“能不能通过时间差判断缓存状态”，升级为“在噪声环境下，我们能以多大的把握、多大的实际效应、在什么统计前提下、用什么检验方式确认缓存侧信道的存在”，使得攻击结论更加量化、可解释、可复现，也更贴近真实安全研究和工程实践的需求。



## new_debug.py脚本说明

**存在问题：[RESULT] 攻击失败 (INCONCLUSIVE). 未检测到显著的时间差异。**

先看你贴出的控制台结果，其实已经把“攻击失败”的统计原因暴露得很清楚，我们再结合代码逻辑把问题找准，然后给出可操作的改进方案。

---

**一、从日志看现在的数据长什么样**

Terminal 日志（你选中的 103–144 行）里关键几行是：

- 清洗后样本量：
  - `Cold=986/1000, Hot=978/1000`
- 描述性统计（清洗后）：
  - 冷缓存：`mean=104.49 μs, std=20.45 μs`
  - 热缓存：`mean=103.65 μs, std=19.69 μs`
- 差异检验：
  - 均值差：`Cold-Hot = 0.84 μs`
  - `T统计量: 0.9251`
  - `P值: 3.55e-01`（远大于 0.05 / 0.001）
- 效应量：
  - `Cohen's d ≈ 0.0417`（极小效应）
- 功效：
  - `Power (alpha=0.001): 0.009`
  - `Power (alpha=0.05): 0.152`

这说明：

- 冷/热两组的**平均延迟几乎一样**（只差 0.84 μs），而抖动标准差有 20 μs 左右；
- 效应量 d≈0.04，属于“几乎没有实际差异”的级别；
- 在这样微弱差异下，测试的统计功效极低，“攻不出来”是正常的。

所以统计层面已经告诉你：  
**control_cold 和 target_hot 的延迟分布本质上在同一个水平线上，差别小到可以视为噪声。**

接下来要追根究底：代码是怎么把两组数据搞成“一样”的。

---

**二、检查延迟生成逻辑：为什么冷/热都变成“热”了？**

关键逻辑分散在三个地方：

1. **服务端缓存模型**  
   `SharedMemoryDataService.query_data`  
   `debug_Plus.py:36-62`

```python
# 初始化
self._server_side_cache = {}                 # debug_Plus.py:18-20
self.LATENCY_DRAM = 100 * 1000              # 100us （缓存命中）
self.LATENCY_DISK = 500 * 1000              # 500us （缓存未命中）
self.JITTER_STD = 20 * 1000                 # 20us 噪声

def query_data(self, region_id):
    ...
    is_cached = False
    with self._cache_lock:
        # 最近 1 秒内访问过 -> 视为缓存命中
        if region_id in self._server_side_cache:
            last_access = self._server_side_cache[region_id]
            if time.time() - last_access < 1.0:
                is_cached = True

        # 每次访问都更新 last_access
        self._server_side_cache[region_id] = time.time()

    base_delay = self.LATENCY_DRAM if is_cached else self.LATENCY_DISK
    noise = np.random.normal(0, self.JITTER_STD)
    final_delay = max(1000, base_delay + noise)
    self._busy_wait(final_delay)
```

要点：

- 某个 `region_id` 在最近 1 秒内访问过 → `is_cached = True` → 延迟 ≈ 100 μs；
- 否则 → 延迟 ≈ 500 μs；
- 且**所有区域**（包括 control_cold 和 target_hot）只要被访问过，也会被加入/刷新到 `_server_side_cache` 中。

2. **受害者只访问 `target_hot`**

`simulate_victim_activity`  
`debug_Plus.py:67-78`

```python
for _ in range(500):
    service.query_data(sensitive_region)          # sensitive_region='classified_ops_area'
    time.sleep(0.05)                              # 每 50ms 一次，约 25 秒
```

- 受害者只访问 `classified_ops_area`（也就是 `target_hot`），每 50ms 一次，持续约 25 秒；
- 这保证 `target_hot` 一直是“热”的。

3. **攻击者采样策略——关键问题在这里**

`AdvancedSideChannelAttacker.run_attack`  
`debug_Plus.py:109-130`

```python
targets = {
    'control_cold': 'public_archive_data',
    'target_hot': 'classified_ops_area'
}

for label, region_id in targets.items():
    print(f"[Attacker] 正在采集样本: {label} (Region: {region_id})...")
    for i in range(self.sample_count):             # sample_count = 1000
        latency = self._measure_single_query(region_id)
        self.measurements[label].append(latency)
        if i % 100 == 0:
            time.sleep(0.001)
```

注意这里的采样顺序和缓存行为：

- 对 `control_cold`（public_archive_data）：
  - 第一次访问时，它确实是“冷”的 → 延迟 ≈ 500 μs；
  - 访问完成后，`_server_side_cache['public_archive_data']` 被记录为“当前时间”；
  - 接下来 999 次访问全部发生在 1 秒窗口内 → 全部被视为缓存命中（≈ 100 μs）。
- 对 `target_hot`（classified_ops_area）：
  - 受害者线程一直在访问它，保证其在缓存热区；
  - 攻击者的 1000 次访问也不断刷新 last_access；
  - 实际上除了少数极端数据（抖动/离群值），几乎全部是 ≈100 μs 的“热”。

再加上：

- `sample_count=1000`，每次延迟约 100 μs，1000 次只要 ~0.1 秒，远远小于 1 秒 TTL；
- 所以：
  - `control_cold` 实际上有 1 次“真正冷”的磁盘访问 + 999 次“被攻击者自己加热”的缓存访问；
  - `target_hot` 有 1000 次“热”。

→ 两组都主要是“热”的样本，极少数“冷”样本对均值影响有限，  
再加上 20 μs 的抖动，最终平均值就会像你看到的那样都在 104 μs 左右，只差 0.84 μs。

**结论：**

- 代码设想中的 “control_cold = 冷数据” 在当前采样方式下完全失效；
- 攻击者自己把 `control_cold` 也“加热”成缓存命中了；
- 最终冷/热两组本质上采的是**同一类（缓存命中）的延迟分布**，所以统计上检测不到差异。

这就是攻击“失败 (INCONCLUSIVE)”的根本原因。

---

**三、新的解决方案：如何让冷/热真的冷/热起来**

你可以从两条线来改：**（1）缓存策略** 和 **（2）采样策略**。下面给两个可选方案，你可以单独用，也可以组合。

---

### 方案 A：改缓存策略，只允许敏感区域参与缓存

目标：让 `control_cold` 永远走“慢路径”（磁盘），`target_hot` 才会走“缓存快路径”。

思路（概念）：

- 在 `SharedMemoryDataService.__init__` 中增加一个“可缓存区域集合”，例如只允许 `'classified_ops_area'` 进缓存；
- 在 `query_data` 中判断：只有在可缓存集合里的 `region_id` 才更新 `_server_side_cache` 并触发 `is_cached=True`；
- 其他区域（包括 `'public_archive_data'`）永远当作未缓存处理。

伪代码示例（便于你在 `debug_Plus.py:17-25` 和 `:36-62` 里改）：

```python
class SharedMemoryDataService:
    def __init__(self):
        ...
        # 仅这些区域会被放入“快速缓存”
        self.cacheable_regions = {'classified_ops_area'}  # 只把敏感区域做成“可缓存”

    def query_data(self, region_id):
        is_cached = False
        with self._cache_lock:
            if (region_id in self.cacheable_regions and
                region_id in self._server_side_cache):
                last_access = self._server_side_cache[region_id]
                if time.time() - last_access < 1.0:
                    is_cached = True

            # 只有可缓存区域才更新缓存状态
            if region_id in self.cacheable_regions:
                self._server_side_cache[region_id] = time.time()

        base_delay = self.LATENCY_DRAM if is_cached else self.LATENCY_DISK
        ...
```

这样：

- `target_hot = 'classified_ops_area'`：
  - 由于 victim 持续访问 + 可缓存策略，几乎总是走 `LATENCY_DRAM ≈ 100 μs`。
- `control_cold = 'public_archive_data'`：
  - 不在 `cacheable_regions` 里，永远走 `LATENCY_DISK ≈ 500 μs`。

结果：

- 两组均值差 ≈ 400 μs，远大于 20 μs 的抖动；
- Cohen’s d 会在 10 以上，P 值会接近 0；
- 你的攻击在统计上会非常“强势”，日志会显示：
  - 非常显著的差异 + 极大的效应量 + 功效接近 1。

如果你觉得 100 vs 500 μs 差异太夸张，可以把 `LATENCY_DISK` 调低一点（比如 150~200 μs），形成更“真实”的缓存差异。

---

### 方案 B：改采样策略，保证每次测量都是真正的“冷 vs 热”

目标：在**不改缓存策略**的前提下，通过时间安排保证：

- 每一轮测量时：
  - `control_cold` 在 1 秒 TTL 之外，确实是“冷”；
  - `target_hot` 则因为 victim 在后台频繁访问，一直处于“热”。

核心思想：

- 利用 TTL=1 秒的机制：  
  每轮测量前先“等一等”，让上轮访问的冷区域过期；  
  而这段时间里 victim 线程依然在持续访问敏感区域，保证 hot 区域一直在 TTL 内。
- 每一轮只对每个 region 测一次，不要像现在这样对同一个 region 连续测 1000 次，把自己加热了。

伪代码改法（思路）：

```python
def run_attack(self):
    print("\n[Attacker] === 开始侧信道探测序列（冷/热交替） ===")

    for i in range(self.sample_count):
        # 1. 等待 > TTL 的时间，让“上一次”冷区访问过期
        time.sleep(1.1)  # TTL=1.0s，这里略大一点

        # 注意：在这 1.1 秒期间，victim 线程仍然每 50ms 访问 hot 区域，
        # 所以 hot 区域始终保持在缓存窗口内。

        # 2. 测一次真正“冷”的 control_cold
        cold_latency = self._measure_single_query('public_archive_data')
        self.measurements['control_cold'].append(cold_latency)

        # 3. 紧接着测一次“热”的 target_hot
        hot_latency = self._measure_single_query('classified_ops_area')
        self.measurements['target_hot'].append(hot_latency)

        if i % 50 == 0:
            print(f"[Attacker] 进度: {i}/{self.sample_count}")
```

注意点：

- 这样每轮只有一次冷测 + 一次热测，避免攻击者自己把冷区反复“加热”；
- 因为每轮都 `sleep(1.1s)`，脚本总时长会变长：
  - `sample_count` 可以适当调小，比如 200 左右；
- `simulate_victim_activity` 目前总时长大约 25s，如果你总攻击时间超过 25s，要把 victim 循环次数改大一点（否则后半段 hot 区域也会变冷）。

效果：

- 在合理设置 `sample_count`、sleep 时长及 victim 访问时长后：
  - `control_cold` 会频繁落到 “磁盘延迟”；
  - `target_hot` 会保持 “缓存延迟”；
- 分布差异会放大，统计检验能更容易检测到，并且不会因为攻击者采样策略导致自我“加热”。

---

**四、该选哪种方案？**

- 如果你的目标是 **教学/演示** “时间侧信道攻击 + 完整统计分析流程”：
  - 推荐先用 **方案 A**：简单、直接且非常清晰地展示“缓存 vs 非缓存”的巨大差异。
- 如果你更关注 **模拟更真实的攻击行为**（攻击者的探测本身不会改变控制组的缓存状态）：
  - 可以在 A 的基础上再尝试 **方案 B**，或者单独用 B 并适当调整 TTL / victim 访问策略。

你现在这版 `debug_Plus.py` 的统计分析部分已经很强了（能帮你诊断问题）；  
真正的问题在于 **“冷/热标签下来的数据本身并不冷/热”**。  
只要按照上面任一方案让底层延迟模型真正拉开差距，再跑一遍脚本，你就会在日志里看到：

- 更大的均值差；
- 明显的 Cohen’s d；
- 较高的功效；
- `攻击成功 (SUCCESS)` 的判定结果。