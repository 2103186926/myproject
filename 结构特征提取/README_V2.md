# Python容器逃逸代码静态检测系统 - 结构特征提取模块（优化版）

## 项目简介

本项目实现了基于层次化图神经网络（GNN）的Python容器逃逸代码静态检测系统。通过构建控制流图（CFG）和函数调用图（FCG），利用深度学习技术自动学习代码的结构特征，实现对恶意容器逃逸代码的精准识别。

### 核心特性

- **双层次GNN架构**：CFG-GNN学习函数级特征，FCG-GNN学习程序级特征
- **特征融合机制**：将CFG嵌入融合到FCG节点，增强表达能力
- **容器逃逸检测**：针对海洋科学云计算场景的容器逃逸攻击检测
- **完整工作流**：从代码解析、图构建、特征提取到模型训练的端到端流程
- **可配置架构**：通过配置文件灵活调整模型参数

## 系统架构

```
输入Python代码
    ↓
AST解析
    ↓
图构建 (CFG + FCG)
    ↓
特征提取 (节点特征向量)
    ↓
CFG-GNN训练 (函数级嵌入)
    ↓
特征融合 (CFG嵌入 + FCG节点特征)
    ↓
FCG-GNN训练 (程序级嵌入)
    ↓
分类输出 (正常/恶意)
```

### 模型参数（默认配置）

- **CFG-GNN**: 4层GCN，隐藏维度256，输出128维
- **FCG-GNN**: 3层GAT，隐藏维度256，输出128维
- **最终嵌入**: 256维 (CFG 128维 + FCG 128维)
- **节点特征**: 128维 (包含结构特征和文本嵌入)

## 目录结构

```
结构特征提取/
├── config.py                              # 配置管理模块
├── ast_parser.py                          # AST解析器
├── feature_extractor_v2.py                # 优化的特征提取器
├── graph_builder_v2.py                    # 优化的图构建器
├── gnn_trainer_v2.py                      # 优化的GNN训练器
├── model_evaluator.py                     # 模型评估器
├── test_case_generator.py                 # 测试用例生成器
├── main_workflow_v2.py                    # 主工作流程
├── generate_dynamic_framework_diagram.py  # 动态框架图生成器
├── run_tests.py                           # 集成测试脚本
├── README_V2.md                           # 本文档
└── 材料/
    └── generate_gnn_framework_diagram.py  # 静态框架图生成器
```

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install torch torch-geometric networkx numpy pandas matplotlib seaborn scikit-learn transformers tqdm

# 可选：安装CodeBERT模型（用于文本嵌入）
# 下载模型到 ./models/codebert-base/
```

### 2. 生成测试用例

```bash
# 生成海洋科学场景的测试用例
python test_case_generator.py
```

这将在 `./test_cases/` 目录下生成：
- `normal/` - 3个正常的海洋科学计算代码
- `malicious/` - 3个伪装的恶意容器逃逸代码
- `labels.csv` - 标签文件

### 3. 训练模型

```bash
# 使用默认配置训练
python main_workflow_v2.py --source_dir ./test_cases --label_file ./test_cases/labels.csv

# 使用自定义配置
python main_workflow_v2.py \
    --source_dir ./test_cases \
    --label_file ./test_cases/labels.csv \
    --config ./my_config.json \
    --output_dir ./my_output
```

### 4. 查看结果

训练完成后，结果保存在 `./output/` 目录：
- `cfg_gnn_model.pth` - CFG-GNN模型
- `fcg_gnn_model.pth` - FCG-GNN模型
- `training_history.json` - 训练历史
- `config.json` - 使用的配置
- `training.log` - 训练日志
- `confusion_matrix.png` - 混淆矩阵
- `roc_curve.png` - ROC曲线
- `evaluation_results.json` - 评估结果

### 5. 生成框架图

```bash
# 根据配置动态生成框架图
python generate_dynamic_framework_diagram.py
```

## 配置说明

### 配置文件格式 (JSON)

```json
{
  "model": {
    "cfg_hidden_channels": 256,
    "cfg_out_channels": 128,
    "cfg_num_layers": 4,
    "cfg_dropout": 0.3,
    "cfg_pooling": "mean",
    "fcg_hidden_channels": 256,
    "fcg_out_channels": 128,
    "fcg_num_layers": 3,
    "fcg_dropout": 0.3,
    "fcg_pooling": "attention",
    "final_embedding_dim": 256,
    "node_feature_dim": 128
  },
  "training": {
    "cfg_epochs": 100,
    "fcg_epochs": 80,
    "batch_size": 32,
    "learning_rate": 0.001,
    "early_stopping": true,
    "patience": 15
  },
  "data": {
    "source_dir": "",
    "output_dir": "./output",
    "min_nodes": 3,
    "max_nodes": 500
  }
}
```

### 主要参数说明

#### 模型参数
- `cfg_hidden_channels`: CFG-GNN隐藏层维度
- `cfg_out_channels`: CFG-GNN输出维度（CFG嵌入维度）
- `cfg_num_layers`: CFG-GNN层数
- `cfg_pooling`: CFG图池化方式 (`mean` 或 `attention`)
- `fcg_hidden_channels`: FCG-GNN隐藏层维度
- `fcg_out_channels`: FCG-GNN输出维度
- `fcg_num_layers`: FCG-GNN层数
- `fcg_pooling`: FCG图池化方式
- `final_embedding_dim`: 最终嵌入维度（必须等于 cfg_out + fcg_out）
- `node_feature_dim`: 节点初始特征维度

#### 训练参数
- `cfg_epochs`: CFG-GNN训练轮数
- `fcg_epochs`: FCG-GNN训练轮数
- `batch_size`: 批次大小
- `learning_rate`: 学习率
- `early_stopping`: 是否启用早停
- `patience`: 早停耐心值（多少轮无改善后停止）

#### 数据参数
- `min_nodes`: 图最小节点数（过滤太小的图）
- `max_nodes`: 图最大节点数（过滤太大的图）

## 命令行参数

```bash
python main_workflow_v2.py [OPTIONS]

必需参数:
  --source_dir PATH          Python源代码目录

可选参数:
  --output_dir PATH          输出目录 (默认: ./output)
  --log_file PATH            日志文件路径
  --label_file PATH          标签文件路径 (CSV格式)
  --config PATH              配置文件路径 (JSON格式)
  --resume PATH              从检查点恢复训练
  --eval_only                仅评估模式
  --seed INT                 随机种子 (默认: 42)
  --debug                    调试模式
```

## 使用示例

### 示例1：基础训练

```bash
python main_workflow_v2.py \
    --source_dir ./test_cases \
    --label_file ./test_cases/labels.csv
```

### 示例2：自定义配置

```bash
# 1. 生成默认配置文件
python -c "from config import save_default_config; save_default_config('./my_config.json')"

# 2. 编辑配置文件（修改参数）

# 3. 使用自定义配置训练
python main_workflow_v2.py \
    --source_dir ./test_cases \
    --label_file ./test_cases/labels.csv \
    --config ./my_config.json \
    --output_dir ./custom_output
```

### 示例3：调试模式

```bash
python main_workflow_v2.py \
    --source_dir ./test_cases \
    --label_file ./test_cases/labels.csv \
    --debug
```

## 模块说明

### 1. config.py - 配置管理

统一管理所有配置参数，支持：
- 从JSON文件加载/保存配置
- 配置验证（检查维度一致性等）
- 默认配置生成

### 2. feature_extractor_v2.py - 特征提取器

增强的特征提取功能：
- 敏感API检测（扩展的容器逃逸相关API）
- 敏感路径检测
- CodeBERT文本嵌入（可选）
- 节点特征向量生成（128维）
- 函数度量指标提取

### 3. graph_builder_v2.py - 图构建器

修复并优化的图构建：
- 正确的CFG构建（修复了函数体处理逻辑）
- 完整的控制流建模（If/Loop/Try/Return等）
- 自动添加节点特征向量
- FCG构建支持调用计数

### 4. gnn_trainer_v2.py - GNN训练器

优化的训练模块：
- `CFGGNN_V2`: 4层GCN + 批归一化 + 残差连接 + 注意力池化
- `FCGGNN_V2`: 3层GAT + 注意力池化
- 早停机制
- 学习率调度
- 梯度裁剪

### 5. model_evaluator.py - 模型评估器

完整的评估功能：
- 准确率、精确率、召回率、F1、AUC计算
- 混淆矩阵可视化
- ROC曲线绘制
- 训练历史可视化
- 完整评估报告生成

### 6. test_case_generator.py - 测试用例生成器

生成海洋科学场景的测试用例：
- 3个正常代码样本（温度分析、海流计算、盐度处理）
- 3个恶意代码样本（文件系统逃逸、权限提升、Namespace逃逸）
- 自动生成标签CSV文件

### 7. main_workflow_v2.py - 主工作流

完整的端到端流程：
1. 文件收集和标签加载
2. AST解析和图构建
3. 转换为PyG数据格式
4. 数据集划分
5. CFG-GNN训练
6. 特征融合
7. FCG-GNN训练
8. 模型评估
9. 结果保存

### 8. generate_dynamic_framework_diagram.py - 动态框架图生成器

根据配置自动生成框架图：
- 读取config.py中的配置
- 动态显示层数、维度、池化方式等
- 生成高质量的PNG和PDF图片

## 性能优化建议

### 1. 数据预处理
- 使用缓存避免重复解析AST
- 并行处理多个文件
- 过滤掉过小或过大的图

### 2. 模型训练
- 使用GPU加速（如果可用）
- 启用早停避免过拟合
- 使用学习率调度优化收敛
- 适当的批次大小（根据GPU内存调整）

### 3. 特征提取
- 预计算节点特征向量
- 使用简化的文本嵌入（如果CodeBERT太慢）
- 缓存敏感API检测结果

## 常见问题

### Q1: 训练时显存不足怎么办？

**A**: 尝试以下方法：
1. 减小批次大小 (`batch_size`)
2. 减小隐藏层维度 (`hidden_channels`)
3. 减少GNN层数 (`num_layers`)
4. 过滤掉过大的图 (`max_nodes`)

### Q2: 如何提高检测准确率？

**A**: 可以尝试：
1. 增加训练数据量
2. 增加模型层数和隐藏维度
3. 使用CodeBERT文本嵌入
4. 调整敏感API和路径模式
5. 使用数据增强技术

### Q3: 训练速度太慢怎么办？

**A**: 优化建议：
1. 使用GPU训练
2. 减小模型规模
3. 启用早停
4. 使用更大的批次大小
5. 减少训练轮数

### Q4: 如何添加新的敏感API模式？

**A**: 编辑 `config.py` 中的 `ContainerEscapeConfig.sensitive_api_patterns`，添加新的正则表达式模式。

### Q5: 如何使用自己的数据集？

**A**: 
1. 准备Python代码文件
2. 创建标签CSV文件（格式：`file_path,label`）
3. 运行训练命令指定数据目录和标签文件

## 技术细节

### CFG构建逻辑

CFG（控制流图）构建遵循以下规则：
- 每个函数有唯一的入口和出口节点
- If语句创建分支节点（True/False分支）
- 循环创建回边（Loop Back Edge）
- Try-Except创建异常边
- Return语句直接连接到出口节点

### FCG构建逻辑

FCG（函数调用图）构建规则：
- 每个函数是一个节点
- 函数调用关系是有向边
- 边权重表示调用次数
- 支持递归调用检测

### 特征融合机制

```python
# CFG嵌入
h_cfg = CFG_GNN(cfg_graph)  # 128维

# FCG节点原始特征
x_fcg = FCG_node_features  # 128维

# 特征融合
x_fcg_enhanced = concat([x_fcg, h_cfg])  # 256维

# FCG-GNN
h_fcg = FCG_GNN(x_fcg_enhanced)  # 128维

# 最终嵌入
h_final = concat([h_cfg, h_fcg])  # 256维
```

## 引用

如果您在研究中使用了本项目，请引用：

```bibtex
@software{container_escape_detection,
  title={Python容器逃逸代码静态检测系统},
  author={Your Name},
  year={2024},
  url={https://github.com/your-repo}
}
```

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件

## 更新日志

### v2.0 (2024-02)
- ✅ 重构配置管理系统
- ✅ 优化特征提取器（增强容器逃逸检测）
- ✅ 修复CFG构建逻辑
- ✅ 增加早停和学习率调度
- ✅ 添加完整的模型评估模块
- ✅ 生成海洋科学场景测试用例
- ✅ 动态框架图生成器
- ✅ 完善文档和使用说明

### v1.0 (2024-01)
- 初始版本发布
