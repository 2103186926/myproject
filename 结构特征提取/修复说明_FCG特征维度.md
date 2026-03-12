# FCG特征维度不匹配问题修复说明

## 问题描述

在运行 `main_workflow_v2.py` 时出现以下错误：

```
RuntimeError: mat1 and mat2 shapes cannot be multiplied (10x128 and 256x1024)
```

## 问题原因

### 根本原因
训练时和测试时的FCG数据特征维度不一致：

1. **训练阶段**（`train_models` 函数，第323-329行）：
   - FCG节点特征被增强：原始128维 + CFG嵌入128维 = **256维**
   - 代码：
     ```python
     cfg_emb_dim = config.model.cfg_out_channels  # 128
     cfg_embeddings = torch.zeros(num_nodes, cfg_emb_dim)
     fcg_data.x = torch.cat([fcg_data.x, cfg_embeddings], dim=1)  # 256维
     ```

2. **测试阶段**（`evaluate_models` 函数，原第360行）：
   - FCG节点特征**未被增强**：仅有原始特征 = **128维**
   - 直接创建 DataLoader，没有特征增强步骤

3. **FCG模型期望**（`gnn_trainer_v2.py` 第145行）：
   - 模型输入层定义：
     ```python
     in_channels = config.model.node_feature_dim + config.model.cfg_out_channels
     # 128 + 128 = 256维
     ```

### 错误传播路径
```
evaluate_models() 
  → DataLoader(test_data)  # 128维特征
  → evaluator.generate_report(fcg_model, test_loader)
  → fcg_model.forward(x, ...)  # 期望256维，实际收到128维
  → self.conv_in(x, edge_index)  # GATConv期望256维输入
  → RuntimeError: 维度不匹配
```

## 解决方案

### 修改位置
文件：`结构特征提取/main_workflow_v2.py`
函数：`evaluate_models`（第360-380行）

### 修改内容

**修改前**：
```python
def evaluate_models(cfg_model: CFGGNN_V2,
                   fcg_model: FCGGNN_V2,
                   test_data: List[Data],
                   config: Config,
                   output_dir: str,
                   logger: logging.Logger) -> Dict:
    """评估模型"""
    logger.info("=" * 60)
    logger.info("阶段4: 模型评估")
    logger.info("=" * 60)
    
    test_loader = DataLoader(test_data, batch_size=config.training.batch_size)
    
    evaluator = ModelEvaluator()
    
    # 评估FCG模型（最终模型）
    logger.info("\n评估FCG-GNN模型...")
    results = evaluator.generate_report(fcg_model, test_loader, output_dir)
    
    return results
```

**修改后**：
```python
def evaluate_models(cfg_model: CFGGNN_V2,
                   fcg_model: FCGGNN_V2,
                   test_data: List[Data],
                   config: Config,
                   output_dir: str,
                   logger: logging.Logger) -> Dict:
    """评估模型"""
    logger.info("=" * 60)
    logger.info("阶段4: 模型评估")
    logger.info("=" * 60)
    
    # 为测试数据的FCG节点增强特征（与训练时保持一致）
    logger.info("为测试数据增强FCG特征...")
    cfg_emb_dim = config.model.cfg_out_channels  # 128维
    
    for fcg_data in test_data:
        num_nodes = fcg_data.x.size(0)
        # 创建零向量作为CFG嵌入（简化处理）
        cfg_embeddings = torch.zeros(num_nodes, cfg_emb_dim)
        # 拼接特征：原始128维 + CFG嵌入128维 = 256维
        fcg_data.x = torch.cat([fcg_data.x, cfg_embeddings], dim=1)
    
    logger.info(f"测试数据特征维度已增强为: {test_data[0].x.size(1)}维")
    
    test_loader = DataLoader(test_data, batch_size=config.training.batch_size)
    
    evaluator = ModelEvaluator()
    
    # 评估FCG模型（最终模型）
    logger.info("\n评估FCG-GNN模型...")
    results = evaluator.generate_report(fcg_model, test_loader, output_dir)
    
    return results
```

### 关键改动
1. **添加特征增强逻辑**：在创建 `test_loader` 之前，为每个测试数据增强特征
2. **保持维度一致**：确保测试数据的特征维度（256维）与训练时一致
3. **添加日志输出**：记录特征增强过程，便于调试

## 验证方法

运行以下命令测试修复效果：

```bash
python main_workflow_v2.py --source_dir .\test_cases --label_file .\test_cases\labels.csv
```

### 预期输出
```
2026-02-05 XX:XX:XX,XXX - INFO - 阶段4: 模型评估
2026-02-05 XX:XX:XX,XXX - INFO - 为测试数据增强FCG特征...
2026-02-05 XX:XX:XX,XXX - INFO - 测试数据特征维度已增强为: 256维
2026-02-05 XX:XX:XX,XXX - INFO - 评估FCG-GNN模型...
```

### 成功标志
- 不再出现维度不匹配错误
- 模型评估正常完成
- 生成评估报告和可视化图表

## 技术要点

### 1. 特征维度设计
```
CFG节点特征：128维（原始特征）
FCG节点特征：128维（原始特征）+ 128维（CFG嵌入）= 256维
最终嵌入：  128维（CFG输出）+ 128维（FCG输出）= 256维
```

### 2. 层次化架构
```
CFG-GNN (函数级)
    ↓ 生成128维嵌入
    ↓ 增强FCG节点特征
FCG-GNN (程序级)
    ↓ 输入256维特征
    ↓ 输出128维嵌入
最终分类器
```

### 3. 数据一致性原则
- **训练时**和**测试时**的数据预处理必须完全一致
- 特征维度、归一化方式、数据增强策略都要保持一致
- 这是深度学习模型部署的基本要求

## 相关文件

- `main_workflow_v2.py`：主工作流（已修复）
- `gnn_trainer_v2.py`：GNN训练器（定义模型输入维度）
- `config.py`：配置管理（定义各层维度参数）
- `model_evaluator.py`：模型评估器（调用模型进行评估）

## 后续优化建议

### 1. 使用真实的CFG嵌入
当前使用零向量作为CFG嵌入（简化处理），后续可以改进为：
```python
# 使用CFG模型生成真实嵌入
cfg_model.eval()
with torch.no_grad():
    for fcg_data in test_data:
        # 根据函数名匹配对应的CFG
        # 使用CFG模型生成嵌入
        # 替换零向量
```

### 2. 封装特征增强函数
将特征增强逻辑封装为独立函数，避免代码重复：
```python
def enhance_fcg_features(fcg_data_list, cfg_model, config):
    """为FCG数据增强CFG嵌入特征"""
    # 统一的特征增强逻辑
    pass
```

### 3. 添加维度检查
在模型前向传播前添加维度检查，提前发现问题：
```python
def forward(self, x, edge_index, batch=None):
    assert x.size(1) == self.expected_dim, \
        f"输入特征维度不匹配：期望{self.expected_dim}，实际{x.size(1)}"
    # ...
```

## 总结

这个问题是典型的**训练-测试数据不一致**问题，通过在测试阶段添加与训练阶段相同的特征增强逻辑得以解决。修复后，模型可以正常进行评估，生成准确率、召回率、F1分数等指标。

---

**修复日期**：2026-02-05  
**修复人员**：Kiro AI Assistant  
**问题级别**：严重（阻塞测试）  
**修复状态**：✅ 已完成
