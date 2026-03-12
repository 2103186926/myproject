### Json日志格式说明文档

#### 1. 概述

本 JSON 日志数据集用于训练 LSTM 模型以检测“时空关联推理攻击”。每个顶级 JSON 对象代表一个独立的计算任务（Job）。数据集中包含正常业务（Label=0）和恶意攻击（Label=1）。

#### 2. 根对象结构

| **字段名**    | **类型** | **说明**                 | **关键用途**                    |
| ------------- | -------- | ------------------------ | ------------------------------- |
| `job_id`      | String   | 任务唯一标识符 (UUID)    | 用于追踪单个任务序列            |
| `label`       | Int      | **0**: 正常, **1**: 恶意 | **监督学习的目标标签**          |
| `event_count` | Int      | 该任务包含的日志条目数量 | 序列长度特征 (攻击任务通常更长) |
| `events`      | List     | 事件序列列表             | LSTM 的时序输入源               |

#### 3. Events (事件序列) 结构详情

`events` 列表中的每个元素代表一行解析后的日志，按时间顺序排列。

| **字段名**  | **类型** | **说明**        | **特征工程价值**                                             |
| ----------- | -------- | --------------- | ------------------------------------------------------------ |
| `seq_id`    | Int      | 序列号          | 保证时序顺序                                                 |
| `timestamp` | String   | ISO 8601 时间戳 | 计算 **Delta Time (时间差)**，识别耗时操作                   |
| `action`    | String   | 动作类型枚举    | **序列模式识别**。主要枚举值： - `JOB_START` - `DATA_FETCH` - `COMPUTE_START` - `COMPUTE_STEP` (攻击强特征) - `COMPUTE_END` - `EXPORT` |
| `task_type` | String   | 任务声明类型    | 正常为 `Statistical_Analysis`，攻击伪装为 `Physics_Simulation` |
| `params`    | Object   | 动作参数详情    | 包含核心检测特征（详见下表）                                 |

#### 4. Params (参数) 关键特征映射

这是 LSTM 模型区分正常与恶意的核心数据源。

| **上下文 Action** | **参数 Key** | **参数 Value 说明**                    | **检测逻辑 (Why it works)**                                  |
| ----------------- | ------------ | -------------------------------------- | ------------------------------------------------------------ |
| `DATA_FETCH`      | `bbox`       | `[lat_min, lat_max, lon_min, lon_max]` | **空间特征**： - 正常：数值随机分布。 - 恶意：数值高度聚集在 `38.25, 121.75` 附近（敏感区）。 |
| `COMPUTE_START`   | `method`     | `aggregation` / `iterative_solver`     | **文本特征**：`iterative_solver` 对应物理推断攻击。          |
| `COMPUTE_STEP`    | `step`       | 迭代次数 (10, 50, 100)                 | **时序特征**：只有攻击任务会出现此 Action，且伴随长时间延迟。 |
| `EXPORT`          | `file_type`  | `csv` / `netcdf`                       | **I/O特征**：攻击倾向于导出网格数据 (`netcdf`)，正常倾向于统计表 (`csv`)。 |

#### 5. 示例数据片段

**恶意攻击 (Label 1):**

JSON

```
{
  "job_id": "job-bad123",
  "label": 1,
  "events": [
    { "action": "DATA_FETCH", "params": { "bbox": [37.2, 39.3, 120.7, 122.8] } }, // 敏感坐标
    { "action": "COMPUTE_STEP", "params": { "step": 10 } }, // 迭代步骤
    { "action": "COMPUTE_STEP", "params": { "step": 50 } }  // 时间戳会显示此处有延迟
  ]
}
```

**正常任务 (Label 0):**

JSON

```
{
  "job_id": "job-good456",
  "label": 0,
  "events": [
    { "action": "DATA_FETCH", "params": { "bbox": [-5.1, 4.2, 160.5, 170.1] } }, // 公海坐标
    { "action": "COMPUTE_END", "params": { "duration_ms": 800 } } // 快速结束
  ]
}
```