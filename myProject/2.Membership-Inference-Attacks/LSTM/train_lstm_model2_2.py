'''
train_lstm_model2_1.py 代码出现了梯度爆炸 (Exploding Gradients) 的典型迹象。（从第 3 个 Epoch 开始，训练和验证损失（Loss）都急剧上升）
根本原因： nn.Sigmoid() 和 nn.BCELoss() 的组合在数值上是不稳定的，尤其是在梯度爆炸的情况下。
    方案一：使用数值更稳定的损失函数 (首选)
    使用 nn.BCEWithLogitsLoss 损失函数，它在内部将 Sigmoid 和 BCELoss 结合在一起，并使用了数值稳定技术（如 log-sum-exp 技巧）来避免溢出。
    方案二：添加梯度裁剪 (推荐)
    梯度裁剪是训练 RNN（如 LSTM）时防止梯度爆炸的标准做法。它会限制梯度的最大范数，防止它们变得过大。
'''
import os
import json
import numpy as np
import pandas as pd
import seaborn as sns  # 用于绘制混淆矩阵的热力图
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, accuracy_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader  # 用于创建数据集和数据加载器
from torch.nn.utils.rnn import PackedSequence  # 用于处理变长序列

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# --- 配置 ---
INPUT_FILE = r'Membership-Inference-Attacks\LSTM\generated_data\lstm_feature_data.json'
# INPUT_FILE = r'./generated_data/lstm_feature_data.json'
MAX_SEQUENCE_LENGTH = 150 # 序列最大长度，不足的填充，超出的截断
FEATURE_COLS = [
    "response_confidence",  # 响应置信度
    "time_delta_since_last_query",  # 距离上次查询的时间间隔
    "distance_from_anchor_vector"  # 距离锚向量的距离
]
FEATURE_DIM = len(FEATURE_COLS)  # 特征维度（3维）
PADDING_VALUE = 0.0 # PyTorch的pack_padded_sequence通常与0填充一起使用

# --- 预处理函数 ---

def custom_pad_sequences(sequences, maxlen, feature_dim, dtype='float32', padding='post', truncating='post', value=0.0):
    """手动实现序列填充
    参数：
        sequences: 一个列表，列表中的每个元素是一个二维数组（或列表），表示一个序列。每个序列的形状为(seq_len, feature_dim)
        maxlen: 整数，表示填充后的序列长度（时间步数）。
        feature_dim: 整数，表示每个时间步的特征维度。
        dtype: 返回数组的数据类型，默认为'float32'。
        padding: 字符串，填充方式，'post'表示在序列末尾填充，'pre'表示在序列开头填充。
        truncating: 字符串，截断方式，'post'表示从序列末尾截断，'pre'表示从序列开头截断。
        value: 填充的值，默认为0.0。
    """
    # np.full(shape,fill_value,dtype)  返回一个形状（112，150，3）的全是0的三维数组
    padded = np.full((len(sequences), maxlen, feature_dim), value, dtype=dtype)

    for i, seq in enumerate(sequences):  # enumerate返回一个可遍历的数据对象（带下标）
        # sequences是个list、每一个seq是个numpy二维数组（数组才有shape，列表只有len()方法）
        if seq.shape[0] == 0:  # 如果序列长度为0，则跳过（保留全填充值）
            continue
        if truncating == 'post':
            trunc = seq[:maxlen]  # 取序列的前maxlen个时间步
        else:
            trunc = seq[-maxlen:]  # 取序列的后maxlen个时间步
        if padding == 'post':
            padded[i, :len(trunc)] = trunc  # 将截断后的序列放在padded数组的当前样本的前面（从0开始填充）
        else:
            padded[i, -len(trunc):] = trunc  # 将截断后的序列放在后面（从-maxlen开始填充）
    return padded

def load_and_preprocess_data(file_path):
    """加载JSON数据并提取原始序列和标签"""
    if not os.path.exists(file_path):
        print(f"错误：未找到特征文件: {file_path}")
        print("请先运行 python generate_lstm_feature_file.py")
        return None, None

    with open(file_path, 'r') as f:
        data = json.load(f)  # 序列化加载json文件,返回一个dict对象

    sequences, labels = [], []
    print(f"加载 {len(data)} 个任务数据...")

    for task_id, task_data in data.items():  # 将字典以列表返回视图对象，是一个可遍历的key/value 对
        sequence_data = np.array([[event[col] for col in FEATURE_COLS] for event in task_data['sequence']], dtype=np.float32)  # 提取特征列并转换为float32类型
        sequences.append(sequence_data)
        labels.append(1 if task_data['is_malicious'] else 0)
    
    print("原始数据加载完成。")
    return sequences, labels

# --- 模型设计 --- 

class LSTMClassifier(nn.Module):
    """构建LSTM诊断模型
    参数:
    - input_dim: 输入特征的维度
    - hidden_dim: 隐藏层的维度
    - output_dim: 输出层的维度（通常为1，因为这是一个二分类问题）
    - n_layers: LSTM层的数量
    - dropout: Dropout层的dropout概率
    - bidirectional: 是否使用双向LSTM
    - use_last_only: 是否只使用序列的最后一个时间步的输出
    """
    def __init__(self, input_dim, hidden_dim, output_dim=1, n_layers=1, dropout_rate=0.4, 
                 bidirectional=False, use_last_only=True):
        super(LSTMClassifier, self).__init__()
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers
        self.bidirectional = bidirectional
        self.use_last_only = use_last_only
        
        # 定义LSTM层
        self.lstm = nn.LSTM(
            input_dim,hidden_dim, n_layers, 
            batch_first=True,  # 表示输入的第一个维度为批量大小
            dropout=dropout_rate if n_layers > 1 else 0,  # 多层LSTM时在层间应用dropout
            bidirectional=bidirectional
        )
        
        # 如果是双向LSTM，输出维度会翻倍
        fc_input_dim = hidden_dim * 2 if bidirectional else hidden_dim
        
        # 定义Dropout层（作用：防止过拟合）
        self.dropout = nn.Dropout(dropout_rate)
        
        # 定义全连接层
        self.fc = nn.Linear(fc_input_dim, output_dim)
        
        # <--- 修改点 1: 移除了 self.sigmoid = nn.Sigmoid() ---
        # self.sigmoid = nn.Sigmoid()

    def forward(self, x, lengths):
        # 初始化隐藏状态和细胞状态
        # h0 和 c0 的形状: (n_layers * num_directions, batch_size, hidden_dim)
        num_directions = 2 if self.bidirectional else 1
        batch_size = x.size(0)
        
        # 为了使用pack_padded_sequence，我们需要根据序列长度对批次进行排序
        sorted_lengths, sorted_indices = torch.sort(lengths, descending=True)
        x_sorted = x[sorted_indices]
        
        # 初始化隐藏状态和细胞状态
        h0 = torch.zeros(self.n_layers * num_directions, batch_size, self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.n_layers * num_directions, batch_size, self.hidden_dim).to(x.device)

        # 打包序列以处理变长序列
        packed_input = nn.utils.rnn.pack_padded_sequence(x_sorted, sorted_lengths.cpu(), batch_first=True)
        
        # LSTM前向传播
        if self.use_last_only:
            # 只使用最后一个时间步的隐藏状态
            _, (hidden, _) = self.lstm(packed_input, (h0, c0))
            
            # 如果是双向LSTM，合并两个方向的最后一层输出
            if self.bidirectional:
                # hidden形状: [n_layers * num_directions, batch_size, hidden_dim]
                # 我们需要合并最后一层的两个方向
                last_layer_hidden = hidden[-2:].transpose(0, 1).contiguous()
                hidden_cat = last_layer_hidden.view(batch_size, -1)  # 形状: [batch_size, hidden_dim*2]
            else:
                # 只取最后一层的隐藏状态
                hidden_cat = hidden[-1]  # 形状: [batch_size, hidden_dim]
        else:
            # 使用所有时间步的输出
            lstm_out, _ = self.lstm(packed_input, (h0, c0))
            
            # 解包序列
            padded_lstm_out, _ = nn.utils.rnn.pad_packed_sequence(lstm_out, batch_first=True)
            
            # 取每个序列的最后一个有效输出
            batch_size = padded_lstm_out.size(0)
            hidden_cat = torch.zeros(batch_size, padded_lstm_out.size(2)).to(x.device)
            for i, length in enumerate(sorted_lengths):
                hidden_cat[i] = padded_lstm_out[i, length-1]
        
        # 恢复原始批次顺序
        _, unsorted_indices = torch.sort(sorted_indices)
        hidden_unsorted = hidden_cat[unsorted_indices]
        
        # Dropout和全连接层
        out = self.dropout(hidden_unsorted)
        out = self.fc(out)
        
        # <--- 修改点 2: 移除了 out = self.sigmoid(out) ---
        # out = self.sigmoid(out)
        # 模型现在输出原始 logits
        
        return out.squeeze()

# --- 模型训练与评估 ---

def main_train_model():
    # 1. 加载原始数据
    sequences, labels = load_and_preprocess_data(INPUT_FILE)
    if sequences is None: return

    # 2. 划分训练集、验证集和测试集（原始序列list）
    # 首先划分训练集和测试集(训：测 = 7：3)  随机种子42   stratify=labels 分层采样
    seq_train_val, seq_test, y_train_val, y_test = train_test_split(
        sequences, labels, test_size=0.3, random_state=42, stratify=labels
    )
    
    # 再从训练集中划分出训练集和验证集（训：验 = 8：2）
    seq_train, seq_val, y_train, y_val = train_test_split(
        seq_train_val, y_train_val, test_size=0.2, random_state=42, stratify=y_train_val
    )

    # 3. 特征缩放（仅在训练集上拟合）
    # 拼接所有训练序列以拟合scaler
    all_train_features = np.concatenate([s for s in seq_train if s.shape[0] > 0], axis=0)  # 竖直拼接（按行）
    scaler = StandardScaler().fit(all_train_features)  # 在训练集上拟合scaler（计算均值和标准差）

    # 分别转换训练、验证和测试集
    X_train_scaled = [scaler.transform(seq) if seq.shape[0] > 0 else seq for seq in seq_train]
    X_val_scaled = [scaler.transform(seq) if seq.shape[0] > 0 else seq for seq in seq_val]
    X_test_scaled = [scaler.transform(seq) if seq.shape[0] > 0 else seq for seq in seq_test]

    # 4. 序列填充和创建Tensor
    lengths_train = torch.tensor([len(s) for s in X_train_scaled], dtype=torch.long)  # 训练集序列长度 long是长整型(int64)
    lengths_val = torch.tensor([len(s) for s in X_val_scaled], dtype=torch.long)
    lengths_test = torch.tensor([len(s) for s in X_test_scaled], dtype=torch.long)

    # 分别对训练集、验证集和测试集进行填充
    X_train_padded = custom_pad_sequences(X_train_scaled, MAX_SEQUENCE_LENGTH, FEATURE_DIM, value=PADDING_VALUE)
    X_val_padded = custom_pad_sequences(X_val_scaled, MAX_SEQUENCE_LENGTH, FEATURE_DIM, value=PADDING_VALUE)
    X_test_padded = custom_pad_sequences(X_test_scaled, MAX_SEQUENCE_LENGTH, FEATURE_DIM, value=PADDING_VALUE)

    # 分别将填充后的序列转换为Tensor
    X_train = torch.tensor(X_train_padded, dtype=torch.float32)  # 转换为float32类型
    X_val = torch.tensor(X_val_padded, dtype=torch.float32)
    X_test = torch.tensor(X_test_padded, dtype=torch.float32)
    # 转换标签为Tensor
    y_train = torch.tensor(y_train, dtype=torch.float32)
    y_val = torch.tensor(y_val, dtype=torch.float32)
    y_test = torch.tensor(y_test, dtype=torch.float32)

    # 5. 创建DataLoader
    train_dataset = TensorDataset(X_train, y_train, lengths_train)
    val_dataset = TensorDataset(X_val, y_val, lengths_val)
    test_dataset = TensorDataset(X_test, y_test, lengths_test)
    
    BATCH_SIZE = 16
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    print(f"\n训练集样本数: {len(X_train)}, 验证集样本数: {len(X_val)}, 测试集样本数: {len(X_test)}")

    # 6. 构建和训练模型 (这部分代码保持不变)
    model = LSTMClassifier(
        input_dim=FEATURE_DIM,      # 输入特征维度
        hidden_dim=64,              # 隐藏层维度
        output_dim=1,               # 输出维度（二分类）
        n_layers=1,                 # LSTM层数
        dropout_rate=0.5,           # Dropout比率
        bidirectional=False,        # 是否使用双向LSTM
        use_last_only=True          # 是否只使用最后一个时间步的输出
    )
    
    # <--- 修改点 3: 使用 BCEWithLogitsLoss 提高数值稳定性 ---
    # 损失函数: 二元交叉熵 (带 logits)
    # criterion = nn.BCELoss() # 原始代码
    criterion = nn.BCEWithLogitsLoss()
    
    # 优化器: Adam
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # 设置设备 (GPU or CPU)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    print(f"模型已移动到: {device}")
    print(model)

    # 早停设置
    EPOCHS = 100
    PATIENCE = 10
    best_val_loss = float('inf')
    epochs_no_improve = 0
    
    # 记录训练和验证损失
    train_losses = []
    val_losses = []
    epochs_list = []
    
    # <--- 修改点 4: 定义梯度裁剪的最大范数 ---
    MAX_GRAD_NORM = 1  # (1.0 是一个常用的值, 你也可以尝试 0.5 或 5.0)

    print("\n--- 开始训练 LSTM 诊断模型 ---")
    for epoch in range(EPOCHS):
        # 训练阶段
        model.train()
        train_loss = 0.0
        
        for inputs, labels, lens in train_loader:
            inputs, labels, lens = inputs.to(device), labels.to(device), lens.to(device)
            optimizer.zero_grad()
            outputs = model(inputs, lens)
            loss = criterion(outputs, labels)
            loss.backward()
            
            # <--- 修改点 5: 在 optimizer.step() 之前进行梯度裁剪 ---
            torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)
            
            optimizer.step()
            train_loss += loss.item() * inputs.size(0)
        
        train_loss = train_loss / len(train_loader.dataset)
        
        # 验证阶段
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for inputs, labels, lens in val_loader:
                inputs, labels, lens = inputs.to(device), labels.to(device), lens.to(device)
                outputs = model(inputs, lens)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * inputs.size(0)
        
        val_loss = val_loss / len(val_loader.dataset)
        
        # 记录损失
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        epochs_list.append(epoch + 1)
        
        print(f"Epoch {epoch+1}/{EPOCHS}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # 早停检查
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            # 保存最佳模型
            torch.save(model.state_dict(), 'best_lstm_model.pth')
        else:
            epochs_no_improve += 1
            if epochs_no_improve == PATIENCE:
                print(f'Early stopping 触发于 epoch {epoch+1}')
                break
    
    # 绘制训练和验证损失曲线
    plt.figure(figsize=(10, 6))
    plt.plot(epochs_list, train_losses, 'b-', label='训练损失')
    plt.plot(epochs_list, val_losses, 'r-', label='验证损失')
    plt.title('训练和验证损失随迭代次数的变化')
    plt.xlabel('迭代次数 (Epochs)')
    plt.ylabel('损失值 (Loss)')
    plt.legend()
    plt.grid(True)
    plt.savefig('loss_curve.png', dpi=300)
    plt.show()

    # 4. 加载最佳模型进行评估
    print("\n--- 模型评估 ---")
    model.load_state_dict(torch.load('best_lstm_model.pth'))
    model.eval()
    all_preds, all_labels, all_pred_probs = [], [], []
    test_loss = 0
    
    with torch.no_grad():
        for inputs, labels, lens in test_loader:
            inputs, labels, lens = inputs.to(device), labels.to(device), lens.to(device)
            # outputs 是 logits
            outputs = model(inputs, lens)
            loss = criterion(outputs, labels)
            test_loss += loss.item() * inputs.size(0)
            
            # <--- 修改点 6: 从 logits 手动计算概率 (用于 AUC 和阈值) ---
            # pred_probs = outputs.cpu().numpy() # 原始代码
            pred_probs = torch.sigmoid(outputs).cpu().numpy()
            
            preds = (pred_probs > 0.5).astype(int)
            all_pred_probs.extend(pred_probs)
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_test_loss = test_loss / len(test_loader.dataset)
    accuracy = accuracy_score(all_labels, all_preds)
    print(f"测试集损失 (Loss): {avg_test_loss:.4f}")
    print(f"测试集准确率 (Accuracy): {accuracy:.4f}")

    print("\n--- 诊断结果评价报告 (Classification Report) ---")
    print(classification_report(all_labels, all_preds, target_names=['正常任务 (0)', '恶意任务 (1)']))
    
    auc_score = roc_auc_score(all_labels, all_pred_probs)
    print(f"ROC AUC 分数: {auc_score:.4f}")

    # 绘制混淆矩阵
    print("\n混淆矩阵 (Confusion Matrix):")
    cm = confusion_matrix(all_labels, all_preds)
    print(cm)
    
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['预测为正常', '预测为恶意'], 
                yticklabels=['实际为正常', '实际为恶意'])
    plt.title('LSTM 模型 - 混淆矩阵')
    plt.ylabel('实际标签')
    plt.xlabel('预测标签')
    plt.savefig('confusion_matrix.png', dpi=300)
    plt.show()

    # 5. 保存模型
    model_save_path = 'lstm_mia_detector.pth'
    torch.save(model.state_dict(), model_save_path)
    print(f"\n模型已保存至 {model_save_path}")

if __name__ == "__main__":
    main_train_model()