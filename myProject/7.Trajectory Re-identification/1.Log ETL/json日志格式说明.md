好的，我们正式进入实战第一步。

为了让LSTM模型能够发挥作用，我们需要的数据不能是离散的单条日志，而是**基于 `task_id` 的时间步序列（Time-Step Sequence）**。每一个任务都由一连串有序的操作组成（开始->查询->处理->输出->结束），而恶意行为的特征就隐藏在这些**操作序列的节奏**和**指标变化的模式**中。

下面我完成了两个任务：

1. **`mock_json_log.py`**：生成高仿真的JSON序列化日志，重点在于通过数值特征（而非文本标签）埋藏攻击线索。
2. **JSON日志格式说明文档**：详细解读字段含义，并指出了 LSTM 模型需要捕捉的“潜伏”特征。

------

### JSON日志格式说明文档

这份文档是后续特征提取工程的字典。请注意我特别标注的 **【检测关键点】**，这对应了您提供的文档中关于轨迹重识别攻击的检测逻辑。

#### 1. 基础结构

每条日志代表云计算平台中的一个“原子操作”。

**精简模板**：

```
{
  "timestamp": "ISO-8601格式时间戳",
  "task_id": "任务唯一标识符 (用于将离散日志串联成时序序列)",
  "component": "组件名称 (Scheduler/DataNode/ComputeNode/IOController)",
  "event_type": "事件类型 (决定了metrics中包含哪些指标)",
  "params": { ... },  // 静态配置参数
  "metrics": { ... }  // 动态运行时指标 (LSTM特征提取的核心来源)
}
```

**全局模板**：

```
{
  "timestamp": "2023-10-27T14:30:05.123456",  // [通用] ISO-8601标准时间戳，LSTM利用此计算事件间隔（Time Step）
  "task_id": "job-atk-a1b2c3d4",               // [通用] 任务唯一ID，用于将离散的日志聚合为一条完整的时序序列
  "component": "ComputeNode",                  // [通用] 组件名称：Scheduler(调度), DataNode(数据), ComputeNode(计算), IOController(存储)
  "event_type": "PRE_FILTER",                  // [通用] 事件类型：决定了当前步骤的核心逻辑，常见值：JOB_START, DATA_FETCH, PRE_FILTER, DEEP_ANALYSIS, RESULT_EXPORT

  "params": { 
    // --- 任务初始化阶段 (JOB_START) ---
    [cite_start]"job_name": "trajectory_pattern_mining",   // [伪装] 攻击者常伪装成合法的“轨迹挖掘”或“模式分析”任务 [cite: 126]
    "user_id": "analyst_X",                    // [审计] 提交任务的用户身份

    // --- 数据获取阶段 (DATA_FETCH) ---
    [cite_start]"time_span_days": 10,                      // [检测点] 查询时间跨度。正常任务通常>30天；攻击者通常<15天（精确瞄准特定航次） [cite: 159]
    [cite_start]"area_sqkm": 200,                          // [检测点] 查询面积。正常任务宽泛；攻击者通过“外部知识”限定在特定港口或渔场附近 [cite: 159]
    "data_source": "ais_archive_v2"            // [元数据] 数据源名称
  },

  "metrics": {
    // --- 数据获取指标 (DATA_FETCH) ---
    "data_size_mb": 25.5,                      // [流量] 下载的数据量大小
    "download_duration_ms": 1500,              // [性能] 下载耗时

    // --- 预处理与过滤指标 (PRE_FILTER / BATCH_PROCESS) ---
    "input_records": 20000,                    // [检测点] 漏斗入口。处理前的原始数据量
    [cite_start]"output_records": 3,                       // [检测点] 漏斗出口。正常聚合任务此值较大；攻击任务此值极小（仅保留个别目标） [cite: 161]
    "filter_ratio": 0.00015,                   // [特征] (output/input) 过滤率。极低的保留率是重识别攻击的强特征

    // --- 深度分析指标 (DEEP_ANALYSIS / COMPUTE) ---
    "batch_id": 1,                             // [序列] 处理批次号
    [cite_start]"cpu_usage_pct": 95.5,                     // [检测点] CPU负载。攻击者对单条轨迹进行DTW匹配时，CPU常飙升至90%+ [cite: 165]
    "mem_usage_mb": 1024,                      // [资源] 内存占用
    "process_duration_ms": 4200,               // [检测点] 处理耗时。处理极少数据却耗时极长，表明在进行复杂的特征提取

    // --- 结果导出指标 (RESULT_EXPORT) ---
    [cite_start]"file_size_kb": 12,                        // [检测点] 输出文件大小。正常分析输出MB级统计图；攻击输出KB级单条轨迹 [cite: 166]
    "output_format": "raw_sequence_csv",       // [检测点] 文件格式。CSV/JSON明文格式常用于导出窃取的轨迹详情
    "sensitive_flag": true                     // [标记] (可选) 是否包含敏感字段检测结果
  }
}
```

##### 字段逻辑深度解析

1. **`event_type` 决定结构**：
   - 当 `event_type` 为 `DATA_FETCH` 时，你会在 `params` 里看到 `time_span_days`（查询参数）。
   - 当 `event_type` 为 `PRE_FILTER` 时，你会在 `metrics` 里看到 `input_records` 和 `output_records`（漏斗效应）。
2. **LSTM 的视角**：
   - LSTM 不会单独看某一行日志。它看的是**数值的变化趋势**。
   - **正常序列**：`time_span_days`(大) -> `input`(大)/`output`(大) -> `cpu`(中等/平稳)。
   - **攻击序列**：`time_span_days`(小) -> `input`(大)/`output`(极小) -> `cpu`(爆发式增高/处理单条数据)。

这个模板覆盖了你在 `mock_json_log.py` 中生成的所有数据情况。你可以直接使用这个结构定义来编写你的特征提取代码。

#### 2. 关键事件与特征映射

我们重点关注 `event_type` 对应的 `metrics` 和 `params`，LSTM 需要学习这些数值在时间维度上的变化模式。

##### A. 事件：`DATA_FETCH` (数据获取)

- **含义**：任务开始从数据库查询历史轨迹数据。
- **Fields**:
  - `params.time_span_days` (int): 查询的时间跨度（天）。
  - `params.area_sqkm` (int): 查询的空间范围大小（平方公里）。
  - `metrics.data_size_mb` (float): 下载的数据量。
- **【检测关键点 - 特征注入依据】**：
  - **正常行为**：`time_span_days` 通常较大 (>30)，用于普查。
  - **攻击行为**：`time_span_days` 异常精确且短 (<15) 2，因为攻击者通过“外部知识”锁定了特定航次。LSTM 应捕捉到这种**“参数收敛”**的特征。

##### B. 事件：`PRE_FILTER` / `BATCH_PROCESS` (预处理/过滤)

- **含义**：对原始数据进行清洗或筛选。
- **Fields**:
  - `metrics.input_records` (int): 输入数据条数。
  - `metrics.output_records` (int): 输出数据条数。
  - `metrics.cpu_usage_pct` (float): CPU占用率。
- **【检测关键点 - 特征注入依据】**：
  - **正常行为**：输入输出比例稳定（如聚合操作，比例可能是 10:1 或 1:1），CPU 负载平稳。
  - **攻击行为**：呈现极端的**“漏斗效应”** 3。输入巨大（`input`=20000），输出极小（`output`=3）。LSTM 需要捕捉 `input` 与 `output` 之间的**巨大落差率**。

##### C. 事件：`DEEP_ANALYSIS` (深度分析)

- **含义**：对筛选后的数据进行算法计算。
- **Fields**:
  - `metrics.input_records` (int): 处理的对象数量。
  - `metrics.duration_ms` (float): 处理耗时。
  - `metrics.cpu_usage_pct` (float): CPU占用率。
- **【检测关键点 - 特征注入依据】**：
  - **正常行为**：处理大量数据时，单条数据的平均耗时极短。
  - **攻击行为**：资源分布**极度偏斜** 4。日志显示在处理极少数记录（`input`=1）时，耗时极长且CPU满载（`cpu`>90%）。这是因为攻击者在进行复杂的轨迹相似度匹配（DTW）或行为特征提取。

##### D. 事件：`RESULT_EXPORT` (结果导出)

- **含义**：任务结束，写入结果文件。
- **Fields**:
  - `metrics.file_size_kb` (float): 文件大小。
  - `metrics.format` (string): 文件格式。
- **【检测关键点 - 特征注入依据】**：
  - **正常行为**：导出统计图表或聚合数据，文件较大。
  - **攻击行为**：导出特定的、包含敏感信息的单条轨迹，文件极小（KB级别）5，且格式往往是 CSV（便于查看明文）。

------

### 下一步建议

现在我们已经生成了包含“隐性特征”的 JSON 序列化日志。

**接下来的步骤（特征提取）**，我建议我们编写一个 Feature Engineering 脚本，将这些 JSON 数据转化为 LSTM 可以接受的 **Tensor (张量)** 格式。我们需要将 `metrics` 中的数值标准化，并将 `params` 进行编码。

你觉得这个日志结构是否满足你的要求？如果没问题，请指示开始下一步。