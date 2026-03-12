import os
import json
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, accuracy_score
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

# --- 配置 ---
# INPUT_FILE = r"C:\Users\21031\Desktop\myProject\Model Stealing\2.Feature Engineering\lstm_feature_data.json"
# INPUT_FILE = r"C:\Users\21031\Desktop\myProject\Model Stealing\2.Feature Engineering\优化1\lstm_feature_data.json"
INPUT_FILE = r"C:\Users\21031\Desktop\myProject\Model Stealing\2.Feature Engineering\优化2\lstm_feature_data.json"

MODEL_SAVE_PATH = "best_lstm_model.pth"
# FEATURE_DIM 将在加载数据后自动获取
BATCH_SIZE = 16
EPOCHS = 100
PATIENCE = 10  # 早停耐心轮数
LEARNING_RATE = 0.001

# 设备配置
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# --- 辅助函数 ---

def get_true_length_and_clean(padded_seq, feature_dim):
    """
    从填充过的序列中还原真实序列。
    原理：从后往前找第一个非全0的向量。
    """
    seq = np.array(padded_seq, dtype=np.float32)
    # 检查每一行是否全为0
    non_zero_rows = np.any(seq != 0, axis=1)
    if not np.any(non_zero_rows):
        return seq[:1], 1 # 只有1行且全0，长度为1
    
    # 找到最后一个非0行的索引
    true_len = np.max(np.where(non_zero_rows)[0]) + 1
    return seq[:true_len], true_len

def custom_pad_sequences(sequences, feature_dim, padding_value=0.0):
    """
    动态填充序列到当前批次的最大长度。
    """
    # 获取当前批次中最长的序列长度
    max_len = max([len(s) for s in sequences])
    
    padded = np.full((len(sequences), max_len, feature_dim), padding_value, dtype=np.float32)
    
    for i, seq in enumerate(sequences):
        if len(seq) > 0:
            padded[i, :len(seq), :] = seq
            
    return padded

def load_data(file_path):
    """
    加载并解析JSON数据，自动探测特征维度。
    返回: sequences, labels, feature_dim, feature_names
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"特征文件未找到: {file_path}")

    print(f"[Info] Loading data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # --- 自动探测特征维度 ---
    feature_names = data.get('feature_names', [])
    if not feature_names:
        # 如果JSON里没有feature_names，尝试从第一条数据推断
        if data['samples'] and data['samples'][0]['features']:
             feature_dim = len(data['samples'][0]['features'][0])
             feature_names = [f"Feat_{i}" for i in range(feature_dim)]
             print(f"[Warn] 'feature_names' not found in JSON. Inferred dim: {feature_dim}")
        else:
             raise ValueError("无法确定特征维度，数据为空或格式错误。")
    else:
        feature_dim = len(feature_names)
        print(f"[Info] Detected {feature_dim} features: {feature_names}")

    samples = data['samples']
    sequences = []
    labels = []
    
    print("[Info] Cleaning and parsing sequences...")
    for item in samples:
        # 获取真实未填充的序列，防止Scaler被大量的填充0影响
        clean_seq, _ = get_true_length_and_clean(item['features'], feature_dim)
        sequences.append(clean_seq)
        labels.append(item['label']) # 0 or 1
    
    print(f"[Info] Total samples loaded: {len(sequences)}")
    return sequences, np.array(labels), feature_dim, feature_names

# --- 模型定义 (参考模板) ---

class LSTMClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim=64, n_layers=2, dropout=0.5):
        super(LSTMClassifier, self).__init__()
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers
        
        # LSTM 层
        self.lstm = nn.LSTM(
            input_dim, 
            hidden_dim, 
            n_layers, 
            batch_first=True, 
            dropout=dropout if n_layers > 1 else 0,
            bidirectional=False # 单向通常足够，且易于收敛
        )
        
        # 全连接分类头
        self.fc = nn.Linear(hidden_dim, 1)
        self.dropout = nn.Dropout(dropout)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, lengths):
        # 1. 排序 (pack_padded_sequence 要求)
        lengths_sorted, sorted_idx = torch.sort(lengths, descending=True)
        x_sorted = x[sorted_idx]
        
        # 2. 打包 (PackedSequence)
        # 将数据移回 CPU 进行 pack (PyTorch 某些版本的特性)
        packed_x = nn.utils.rnn.pack_padded_sequence(x_sorted, lengths_sorted.cpu(), batch_first=True)
        
        # 3. LSTM 前向传播
        # out: (seq_len, batch, hidden_dim) - packed
        # (hn, cn): (n_layers, batch, hidden_dim)
        packed_out, (hn, cn) = self.lstm(packed_x)
        
        # 4. 提取最后一个时间步的隐藏状态
        # hn[-1] 是最后一层 LSTM 的最终状态
        final_hidden_state = hn[-1] 
        
        # 5. 恢复顺序 (Unsort)
        _, unsorted_idx = torch.sort(sorted_idx)
        final_hidden_state = final_hidden_state[unsorted_idx]
        
        # 6. 分类
        out = self.dropout(final_hidden_state)
        out = self.fc(out)
        return self.sigmoid(out).squeeze()

# --- 主训练流程 ---

def main():
    # 1. 加载数据 (自动获取维度)
    sequences, labels, feature_dim, feature_names = load_data(INPUT_FILE)
    
    print(f"\n[Config] Input Feature Dimension: {feature_dim}")
    print(f"[Config] Features: {feature_names}")

    # 2. 数据划分 (Train: 70%, Val: 15%, Test: 15%)
    # 先分出 Test
    X_temp, X_test, y_temp, y_test = train_test_split(sequences, labels, test_size=0.15, random_state=42, stratify=labels)
    # 再分出 Train 和 Val
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp) # 0.176 of 0.85 is approx 0.15 total
    
    print(f"[Info] Split sizes - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # 3. 特征标准化 (StandardScaler)
    # 仅在训练集上 fit，避免数据泄露
    train_flat = np.concatenate(X_train, axis=0)
    scaler = StandardScaler().fit(train_flat)
    
    def transform_dataset(dataset):
        return [scaler.transform(seq) for seq in dataset]

    X_train_scaled = transform_dataset(X_train)
    X_val_scaled = transform_dataset(X_val)
    X_test_scaled = transform_dataset(X_test)

    # 4. 序列填充与张量转换
    def create_tensor_dataset(seqs_scaled, targets):
        # 动态计算真实长度
        lengths = torch.tensor([len(s) for s in seqs_scaled], dtype=torch.long)
        # 填充 (使用动态获取的 feature_dim)
        padded = custom_pad_sequences(seqs_scaled, feature_dim)
        # 转换张量
        x_tensor = torch.tensor(padded, dtype=torch.float32)
        y_tensor = torch.tensor(targets, dtype=torch.float32)
        return TensorDataset(x_tensor, y_tensor, lengths)

    train_ds = create_tensor_dataset(X_train_scaled, y_train)
    val_ds = create_tensor_dataset(X_val_scaled, y_val)
    test_ds = create_tensor_dataset(X_test_scaled, y_test)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE)

    # 5. 初始化模型 (使用动态获取的 feature_dim)
    model = LSTMClassifier(input_dim=feature_dim).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    print(f"\n[Model Structure]\n{model}")

    # 6. 训练循环
    train_losses, val_losses = [], []
    best_val_loss = float('inf')
    epochs_no_improve = 0

    print("\n--- Starting Training ---")
    for epoch in range(EPOCHS):
        # Training
        model.train()
        epoch_train_loss = 0
        for x_batch, y_batch, lens_batch in train_loader:
            x_batch, y_batch, lens_batch = x_batch.to(device), y_batch.to(device), lens_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(x_batch, lens_batch)
            loss = criterion(outputs, y_batch)
            loss.backward()
            optimizer.step()
            
            epoch_train_loss += loss.item() * x_batch.size(0)
        
        avg_train_loss = epoch_train_loss / len(train_ds)
        
        # Validation
        model.eval()
        epoch_val_loss = 0
        with torch.no_grad():
            for x_batch, y_batch, lens_batch in val_loader:
                x_batch, y_batch, lens_batch = x_batch.to(device), y_batch.to(device), lens_batch.to(device)
                outputs = model(x_batch, lens_batch)
                loss = criterion(outputs, y_batch)
                epoch_val_loss += loss.item() * x_batch.size(0)
        
        avg_val_loss = epoch_val_loss / len(val_ds)
        
        train_losses.append(avg_train_loss)
        val_losses.append(avg_val_loss)
        
        print(f"Epoch {epoch+1:03d} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

        # Early Stopping & Checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= PATIENCE:
                print(f"[Info] Early stopping triggered at epoch {epoch+1}")
                break

    # 7. 绘制损失曲线
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='训练集损失')
    plt.plot(val_losses, label='验证集损失')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('模型训练过程损失变化曲线')
    plt.legend()
    plt.grid(True)
    plt.savefig('lstm_training_loss.png')
    print("[Info] Loss curve saved to lstm_training_loss.png")

    # 8. 独立测试集评估
    print("\n--- Final Evaluation on Test Set ---")
    model.load_state_dict(torch.load(MODEL_SAVE_PATH)) # 加载最佳模型
    model.eval()
    
    y_true = []
    y_pred_prob = []
    y_pred_cls = []
    
    with torch.no_grad():
        for x_batch, y_batch, lens_batch in test_loader:
            x_batch, lens_batch = x_batch.to(device), lens_batch.to(device)
            outputs = model(x_batch, lens_batch)
            
            y_pred_prob.extend(outputs.cpu().numpy())
            y_true.extend(y_batch.numpy())
            
    y_pred_cls = [1 if p > 0.5 else 0 for p in y_pred_prob]
    
    # 打印指标
    acc = accuracy_score(y_true, y_pred_cls)
    print(f"Test Accuracy: {acc:.4f}")
    
    try:
        auc = roc_auc_score(y_true, y_pred_prob)
        print(f"Test AUC: {auc:.4f}")
    except:
        print("Test AUC: N/A (可能只有一个类别)")

    print("\nClassification Report:")
    print(classification_report(y_true, y_pred_cls, target_names=['Normal', 'Malicious']))
    
    # 绘制混淆矩阵
    cm = confusion_matrix(y_true, y_pred_cls)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Pred:Normal', 'Pred:Malicious'],
                yticklabels=['True:Normal', 'True:Malicious'])
    plt.title('测试集混淆矩阵')
    plt.ylabel('真实标签')
    plt.xlabel('预测标签')
    plt.savefig('lstm_confusion_matrix.png')
    print("[Info] Confusion matrix saved to lstm_confusion_matrix.png")

if __name__ == "__main__":
    main()