# Python代码结构特征嵌入生成工具使用指南

这个工具可以为Python代码文件生成结构化特征嵌入向量，通过分析代码的控制流图(CFG)和函数调用图(FCG)。

## 系统要求

- Python 3.8+
- PyTorch 1.10+
- PyTorch Geometric
- NetworkX
- NumPy

## 快速开始

最简单的方式是直接运行主脚本，无需参数：

```bash
python structural_features/main_workflow.py
```

这将在默认的测试目录上运行，并在`output`目录中生成嵌入向量。

## 自定义运行

如果要在自己的代码目录上运行：

```bash
python structural_features/main_workflow.py --source_dir "你的代码目录路径" --output_dir "输出目录路径"
```

### 完整参数列表

```
必需参数:
  --source_dir      Python源代码目录

可选参数:
  --output_dir      输出目录 (默认: "output")
  --log_file        日志文件路径
  --min_nodes       图中最小节点数量 (默认: 2)
  --max_nodes       图中最大节点数量 (默认: 500)
  --cfg_epochs      CFG GNN训练轮数 (默认: 100)
  --fcg_epochs      FCG GNN训练轮数 (默认: 50)
  --batch_size      批处理大小 (默认: 32)
  --learning_rate   学习率 (默认: 0.001)
  --hidden_channels GNN隐藏层通道数 (默认: 128)
  --out_channels    GNN输出层通道数/嵌入维度 (默认: 64)
  --num_layers      GNN层数 (默认: 3)
  --dropout         Dropout率 (默认: 0.2)
  --cpu_count       要使用的CPU核心数
  --gpu_id          要使用的GPU ID，-1表示使用CPU (默认: 0)
  --seed            随机种子 (默认: 42)
  
  --skip_parsing    跳过解析步骤
  --skip_feature_extraction  跳过特征提取步骤
  --skip_graph_building      跳过图构建步骤
  --skip_training   跳过训练步骤
  --skip_embedding  跳过嵌入生成步骤
  --debug           启用调试模式
```

## 输出内容

运行成功后，在指定的输出目录中将生成以下内容：

1. `embeddings/` 目录：包含每个Python文件的嵌入向量（.npy格式）
2. `models/` 目录：包含训练好的GNN模型
3. `training_metrics.json`：训练过程的指标
4. `experiment_metadata.json`：实验元数据

## 在Python代码中使用

可以在自己的Python代码中调用工具：

```python
from structural_features.main_workflow import test_on_directory

# 在指定目录上运行
success = test_on_directory(
    source_dir="./your_code_dir",
    output_dir="./output",
    epochs=50
)

if success:
    print("嵌入向量生成成功！")
else:
    print("嵌入向量生成失败")
```

## 常见问题解决

### Q: 提示"没有生成有效的图结构"怎么办？
A: 尝试降低`--min_nodes`参数值（设为1或2），这样可以包含更多简单的函数。

### Q: 生成的CFG节点数很少怎么办？
A: 检查源代码中的函数是否过于简单。工具已经优化为可以处理简单函数，但如果函数只有一行代码，CFG节点数仍然会很少。

### Q: 训练过程报错怎么办？
A: 尝试减少`--cfg_epochs`和`--fcg_epochs`的值，或使用`--skip_training`参数直接生成随机嵌入向量。

### Q: 如何加快处理速度？
A: 使用`--cpu_count`参数指定更多CPU核心，或确保使用GPU（`--gpu_id 0`）。

## 注意事项

- 对于非常大的代码库，建议分批处理
- 生成的嵌入向量是64维的浮点数组（可通过`--out_channels`参数调整）
- 程序会自动跳过语法错误的Python文件 