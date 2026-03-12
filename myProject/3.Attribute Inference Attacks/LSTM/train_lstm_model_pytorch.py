''' !!!完全同模型逆向攻击里的LSTM模型一样
(复用) 读取lstm_feature_data_attr_inf.json文件，使用PyTorch训练并评估LSTM诊断模型。
此脚本与您在模型逆向攻击任务中使用的PyTorch脚本完全相同。它被设计为可重用的，只需将输入文件名更改为我们新生成的文件即可。
'''
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import matplotlib.pyplot as plt
# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 导入 PyTorch 库
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# --- 1. 自定义 PyTorch Dataset ---
class SequenceDataset(Dataset):
    """自定义数据集类，用于处理序列数据"""
    def __init__(self, X, y):
        '''初始化数据集'''
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        
    def __len__(self):
        '''返回数据集的样本数量'''
        return len(self.y)
    
    def __getitem__(self, idx):
        '''获取第 index 个样本的输入特征和输出特征'''
        return self.X[idx], self.y[idx]

# --- 2. 定义 PyTorch LSTM 模型 ---
class LSTMClassifier(nn.Module):
    """自定义LSTM分类模型"""
    def __init__(self, input_dim, hidden_dim, output_dim, n_layers, dropout):
        super(LSTMClassifier, self).__init__()
        self.hidden_dim = hidden_dim  # 隐藏层的维度
        self.n_layers = n_layers   # LSTM层的数量

        # 定义LSTM层
        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers, 
                            batch_first=True,  # 表示输入的第一个维度为批量大小
                            dropout=dropout if n_layers > 1 else 0  # 多层LSTM时在层间应用dropout
                            )
        # 定义Dropout层（作用：防止过拟合）
        self.dropout = nn.Dropout(dropout)
        # 定义全连接层
        self.fc = nn.Linear(hidden_dim, output_dim)
        # 定义Sigmoid激活函数
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        # 初始化隐藏状态和细胞状态
        # h0 和 c0 的形状: (n_layers, batch_size, hidden_dim)
        h0 = torch.zeros(self.n_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.n_layers, x.size(0), self.hidden_dim).to(x.device)
        
        # LSTM前向传播
        # lstm_out 形状: (batch_size, seq_length, hidden_dim)
        lstm_out, (hn, cn) = self.lstm(x, (h0, c0))

        # 只取序列的最后一个时间步的输出
        # lstm_out[:, -1, :] 形状: (batch_size, hidden_dim)  -1 表示取序列的最后一个时间步的输出
        out = self.dropout(lstm_out[:, -1, :])
        # 通过全连接层
        out = self.fc(out)
        # 通过Sigmoid激活函数
        out = self.sigmoid(out)
        # 返回形状 (batch_size, 1)
        return out.squeeze(1)  # squeeze：移除最后一个维度，形状为 (batch_size,)


def train_lstm_pytorch(data_filepath='lstm_feature_data_attr_inf.json'):
    """
    加载LSTM序列特征数据，构建、训练并评估PyTorch LSTM诊断模型。
    """
    # --- A. 加载和准备数据 ---
    try:
        with open(data_filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 特征文件 '{data_filepath}' 未找到。请确保文件存在。")
        return

    features = data.get('features', {})  # {}表示如果'features'键不存在，返回空字典
    labels = data.get('labels', {})
    metadata = data.get('metadata', {})

    if not features or not labels:
        print("错误: JSON文件中缺少'features'或'labels'键。")
        return

    num_features = metadata.get('num_features_per_step')  # 每个时间步的特征数量

    task_ids = list(features.keys())  # 返回所有任务ID 列表
    X = np.array([features[tid] for tid in task_ids if tid in labels])
    y = np.array([labels[tid] for tid in task_ids if tid in labels])
    
    if len(X) == 0:
        print("错误：未加载任何有效数据，请检查 'generate_sequential_features.py' 的输出。")
        return

    print(f"数据加载完成: {X.shape[0]}个样本, 序列长度={X.shape[1]}, 每个时间步有{X.shape[2]}个特征。")
    print("-" * 50)

    # 划分训练集、验证集和测试集  (80%训练+20%验证, 20%测试)  随机种子42  stratify=y 确保类别比例一致
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.2, random_state=42, stratify=y_train_val if len(np.unique(y_train_val)) > 1 else None
    )
    print(f"数据集划分完成: {len(X_train)}训练, {len(X_val)}验证, {len(X_test)}测试。")
    print("-" * 50)

    # --- B. 特征缩放 ---
    scaler = StandardScaler()
    X_train_reshaped = X_train.reshape(-1, num_features)  # 先将训练集转换为2D数组，进行缩放  num_features：每个时间步的特征数量
    scaler.fit(X_train_reshaped)  # 用于计算数据集的均值和标准差等统计量
    
    X_train_scaled = scaler.transform(X_train_reshaped).reshape(X_train.shape)  # 对数据进行标准化转换（即缩放）后，还原形状
    X_val_scaled = scaler.transform(X_val.reshape(-1, num_features)).reshape(X_val.shape)
    X_test_scaled = scaler.transform(X_test.reshape(-1, num_features)).reshape(X_test.shape)
    print("特征缩放完成。")
    print("-" * 50)

    # --- C. 创建 DataLoader ---
    BATCH_SIZE = 16
    train_dataset = SequenceDataset(X_train_scaled, y_train)  # 训练数据集
    val_dataset = SequenceDataset(X_val_scaled, y_val)  # 验证数据集
    test_dataset = SequenceDataset(X_test_scaled, y_test)  # 测试数据集
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)  # 训练数据加载器（随机打乱）
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)  # 验证数据加载器（不打乱）
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)  # 测试数据加载器（不打乱）

    # --- D. 初始化模型、损失函数和优化器 ---
    INPUT_DIM = num_features  # 输入维度（每个时间步的特征数）
    HIDDEN_DIM = 64  # 隐藏层维度
    OUTPUT_DIM = 1  # 输出维度（二分类任务）
    N_LAYERS = 1  # LSTM层数（默认为：1）
    DROPOUT = 0.4  # Dropout概率（防止过拟合）
    
    model = LSTMClassifier(INPUT_DIM, HIDDEN_DIM, OUTPUT_DIM, N_LAYERS, DROPOUT)
    # 损失函数: 二元交叉熵
    criterion = nn.BCELoss()
    # 优化器: Adam
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    # 设置设备 (GPU or CPU)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    print(f"模型已移动到: {device}")
    print("-" * 50)

    # --- E. 训练模型 ---
    EPOCHS = 100
    PATIENCE = 10 # 早停耐心值（验证损失未改善的 epoch 数）
    best_val_loss = float('inf')  # 初始化最佳验证损失为无穷大
    epochs_no_improve = 0  # 初始化未改善epoch数

    # 用于记录每个epoch的损失值
    train_losses = []
    val_losses = []
    epochs_list = []
    
    print("开始训练PyTorch LSTM模型...")
    for epoch in range(EPOCHS):
    # for epoch in range(1):
        model.train()  # 切换到训练模式
        train_loss = 0.0  # 初始化训练损失为0

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)  # 将输入特征和标签移动到GPU
            optimizer.zero_grad()  # 梯度清零
            outputs = model(inputs)  # 前向传播
            loss = criterion(outputs, labels)  # 计算损失
            loss.backward()  # 反向传播
            optimizer.step()  # 更新权重
            train_loss += loss.item() * inputs.size(0)  # 累加每个批次的损失（乘以样本数）
        
        # --- 验证 ---
        model.eval()  # 切换到评估模式
        val_loss = 0.0  # 初始化验证损失为0
        with torch.no_grad():  # 禁用梯度计算（推理模式）
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)  # 前向传播
                loss = criterion(outputs, labels)  # 计算损失
                val_loss += loss.item() * inputs.size(0)  # 累加每个批次的损失（乘以样本数）
                
        train_loss = train_loss / len(train_loader.dataset)  # 计算平均训练损失
        val_loss = val_loss / len(val_loader.dataset)  # 计算平均验证损失

        # 记录每个epoch的损失值
        train_losses.append(train_loss)  # 将当前epoch的训练损失添加到列表中
        val_losses.append(val_loss)  # 将当前epoch的验证损失添加到列表中
        epochs_list.append(epoch + 1)

        print(f'Epoch {epoch+1}/{EPOCHS}.. Train Loss: {train_loss:.6f}.. Val Loss: {val_loss:.6f}')
        
        # Early Stopping 检查
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0  # 初始化未改善epoch轮数
            torch.save(model.state_dict(), 'best_lstm_model_attr_inf.pth')  # 保存最佳模型
        else:
            epochs_no_improve += 1
            if epochs_no_improve == PATIENCE:
                print(f'Early stopping 触发于 epoch {epoch+1}')
                break
    # 绘制训练和验证损失的折线图
    plt.figure(figsize=(10, 6))  # 创建一个新的图形窗口，设置大小为10x6英寸
    plt.plot(epochs_list, train_losses, 'b-', label='训练损失')  # 绘制训练损失折线图，蓝色实线
    plt.plot(epochs_list, val_losses, 'r-', label='验证损失')  # 绘制验证损失折线图，红色实线
    plt.title('训练和验证损失随迭代次数的变化')
    plt.xlabel('迭代次数 (Epochs)')
    plt.ylabel('损失值 (Loss)')
    plt.legend()  # 添加图例，显示训练损失和验证损失
    plt.grid(True)  # 显示网格线，帮助阅读
    plt.savefig('loss_curve.png', dpi=300)  # 保存为高分辨率图片（300 DPI）
    plt.show()

    print("模型训练完成。")
    print("-" * 50)

    # --- F. 评估模型 ---
    print("--- 在测试集上进行最终评估 ---")
    model.load_state_dict(torch.load('best_lstm_model_attr_inf.pth'))  # 加载最佳模型权重
    model.eval()  # 切换到评估模式
    
    all_preds, all_labels = [], []  # 存储所有预测类别、真实标签
    with torch.no_grad():  # 禁用梯度计算（推理模式）
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)  # 前向传播
            preds = (outputs > 0.5).float()  # 将概率转换为类别 (0或1)
            all_preds.extend(preds.cpu().numpy())  # 转换为 numpy 数组并添加到列表中
            all_labels.extend(labels.cpu().numpy())
    
    # 计算评估指标
    accuracy = accuracy_score(all_labels, all_preds)  # 准确率
    print(f"测试集准确率 (Accuracy): {accuracy:.4f}")
    print("\n分类报告 (Classification Report):")
    print(classification_report(all_labels, all_preds, target_names=['正常任务 (0)', '恶意任务 (1)'], zero_division=0))  # 分类报告
    print("\n混淆矩阵 (Confusion Matrix):")
    cm = confusion_matrix(all_labels, all_preds)  # 混淆矩阵
    print(cm)

    # 可视化混淆矩阵
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['预测为正常', '预测为恶意'], 
                yticklabels=['实际为正常', '实际为恶意'])
    plt.title('PyTorch LSTM 模型 - 属性推断')
    plt.ylabel('实际标签')
    plt.xlabel('预测标签')
    plt.show()

if __name__ == '__main__':
    train_lstm_pytorch()