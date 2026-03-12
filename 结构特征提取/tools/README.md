# GNN模型架构图生成工具

## 功能说明

本工具用于生成CFG-GNN和FCG-GNN模型的架构可视化图，可直接用于学术论文插图。

## 生成的图片

1. **CFG_GNN_Architecture.png** - CFG-GNN模型架构图
   - 展示输入层、隐藏层（带残差连接）、输出层和注意力池化层
   - 使用GCN卷积层和ReLU激活函数
   - 输入维度：256，输出维度：128

2. **FCG_GNN_Architecture.png** - FCG-GNN模型架构图
   - 展示输入层、隐藏层（带残差连接）、输出层和注意力池化层
   - 使用GAT卷积层（多头注意力）和ELU激活函数
   - 输入维度：128（CFG嵌入），输出维度：128

## 使用方法

### 1. 安装依赖

```bash
pip install matplotlib numpy
```

### 2. 运行脚本

```bash
cd tools
python generate_gnn_architecture_diagrams.py
```

### 3. 查看输出

生成的图片保存在 `tools/output/` 目录下：
- `CFG_GNN_Architecture.png`
- `FCG_GNN_Architecture.png`

图片分辨率为300 DPI，适合论文打印质量要求。

## 架构图特点

### CFG-GNN架构
- **输入层**: GCNConv(256→128) + BatchNorm + ReLU + Dropout
- **隐藏层1**: GCNConv(128→128) + BatchNorm + ReLU + Dropout + 残差连接
- **隐藏层2**: GCNConv(128→128) + BatchNorm + ReLU + Dropout + 残差连接
- **输出层**: GCNConv(128→128) + BatchNorm
- **池化层**: AttentionPooling
- **输出**: 图嵌入 128维

### FCG-GNN架构
- **输入层**: GATConv(128→128, heads=4) + BatchNorm + ELU + Dropout
- **隐藏层1**: GATConv(512→128, heads=4) + BatchNorm + ELU + Dropout + 残差连接
- **隐藏层2**: GATConv(512→128, heads=4) + BatchNorm + ELU + Dropout + 残差连接
- **输出层**: GATConv(512→128, heads=1) + BatchNorm
- **池化层**: AttentionPooling
- **输出**: 程序级嵌入 128维

## 颜色说明

- 浅蓝色：输入/输出层
- 蓝色/绿色：卷积层（GCN/GAT）
- 橙色：批归一化层
- 粉色/红色：激活函数（ReLU/ELU）
- 紫色：Dropout层
- 浅粉色：池化层
- 绿色虚线：残差连接

## 自定义修改

如需修改架构图样式，可以编辑 `generate_gnn_architecture_diagrams.py` 文件中的以下参数：

- `layer_width`: 层的宽度
- `layer_height`: 层的高度
- `color_*`: 各层的颜色
- `figsize`: 图片尺寸
- `dpi`: 图片分辨率

## 注意事项

1. 确保系统已安装中文字体（SimHei），否则中文可能显示为方框
2. 如果中文显示有问题，可以修改脚本中的字体设置
3. 生成的PNG图片支持透明背景，可根据需要调整

## 技术细节

脚本基于 `gnn_trainer_v2.py` 中的模型定义：
- `CFGGNN_V2` 类：CFG图神经网络
- `FCGGNN_V2` 类：FCG图神经网络
- `AttentionPooling` 类：注意力池化层

架构图准确反映了代码中的模型结构和前向传播流程。
