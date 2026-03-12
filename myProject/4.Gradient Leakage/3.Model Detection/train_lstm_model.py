import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import seaborn as sns
import os

# ==========================================
# 1. 配置参数
# ==========================================
CONFIG = {
    # "input_file": "C:\\Users\\21031\\Desktop\\myProject\\Gradient Leakage\\2.Feature Engineering\\lstm_feature_data.json",
    # "input_file": r"C:\Users\21031\Desktop\myProject\Gradient Leakage\2.Feature Engineering\优化\lstm_feature_data.json",
    # "input_file": r"C:\Users\21031\Desktop\myProject\Gradient Leakage\2.Feature Engineering\优化2\lstm_feature_data.json",
    # "input_file": r"C:\Users\21031\Desktop\myProject\Gradient Leakage\2.Feature Engineering\优化3\lstm_feature_data.json",
    "input_file": r"C:\Users\21031\Desktop\myProject\Gradient Leakage\2.Feature Engineering\优化4\lstm_feature_data.json",
    "model_save_path": "best_lstm_model.pth",
    "test_size": 0.2,       # 20% 数据作为独立测试集
    "n_splits": 5,          # 5折交叉验证
    "batch_size": 16,
    "hidden_size": 64,      # LSTM 隐藏层维度
    "num_layers": 2,        # LSTM 层数
    "learning_rate": 0.001,
    "epochs": 50,
    "patience": 10,         # 早停机制忍耐轮数
    "device": "cuda" if torch.cuda.is_available() else "cpu"
}

# ==========================================
# 2. 数据集类定义
# ==========================================
class FLDataset(Dataset):
    def __init__(self, features, labels):
        """
        features: List of numpy arrays (varied length)
        labels: List of ints
        """
        self.features = [torch.tensor(f, dtype=torch.float32) for f in features]
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

def collate_fn(batch):
    """
    处理变长序列的 Padding 函数
    """
    features, labels = zip(*batch)
    # 计算本 Batch 中的最大长度
    lengths = torch.tensor([len(f) for f in features])
    # 进行 Padding (补0)，batch_first=True
    features_padded = pad_sequence(features, batch_first=True, padding_value=0.0)
    labels = torch.stack(labels)
    return features_padded, labels, lengths

# ==========================================
# 3. LSTM 模型定义
# ==========================================
class GradientLeakageLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes=1):
        super(GradientLeakageLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM 层
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                            batch_first=True, dropout=0.2)
        
        # 全连接层 (分类器)
        self.fc = nn.Linear(hidden_size, num_classes)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, lengths):
        # x shape: (batch, seq_len, input_size)
        
        # LSTM Forward
        # out shape: (batch, seq_len, hidden_size)
        # h_n shape: (num_layers, batch, hidden_size)
        out, (h_n, c_n) = self.lstm(x)
        
        # 取最后一个时间步的输出 (Many-to-One)
        # 注意：由于用了 Padding，直接取 -1 可能取到 0 填充区
        # 这里为了简单有效，我们取 LSTM 输出的最后一个 Hidden State (h_n[-1])
        # 这通常包含了整个序列的压缩信息
        last_hidden = h_n[-1] 
        
        # 通过全连接层
        out = self.fc(last_hidden)
        out = self.sigmoid(out)
        return out.squeeze()

# ==========================================
# 4. 辅助函数：训练与评估
# ==========================================
def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    
    for X_batch, y_batch, lengths in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        outputs = model(X_batch, lengths)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
    return total_loss / len(loader)

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for X_batch, y_batch, lengths in loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            outputs = model(X_batch, lengths)
            loss = criterion(outputs, y_batch)
            total_loss += loss.item()
            
            preds = (outputs > 0.5).float().cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_batch.cpu().numpy())
            
    metrics = {
        "loss": total_loss / len(loader),
        "accuracy": accuracy_score(all_labels, all_preds),
        "precision": precision_score(all_labels, all_preds, zero_division=0),
        "recall": recall_score(all_labels, all_preds, zero_division=0),
        "f1": f1_score(all_labels, all_preds, zero_division=0),
        "preds": all_preds,
        "labels": all_labels
    }
    return metrics

def standardize_features(X_train_list, X_val_list):
    """
    对变长序列特征进行标准化 (StandardScaler)
    注意：必须只在 Train 上 fit，然后 transform Train 和 Val
    """
    scaler = StandardScaler()
    
    # 1. 展平 Train 数据以 fit scaler
    X_train_flat = np.vstack(X_train_list)
    scaler.fit(X_train_flat)
    
    # 2. 变换 Train
    X_train_scaled = [scaler.transform(x) for x in X_train_list]
    
    # 3. 变换 Val
    X_val_scaled = [scaler.transform(x) for x in X_val_list]
    
    return X_train_scaled, X_val_scaled, scaler

# ==========================================
# 5. 主程序
# ==========================================
if __name__ == "__main__":
    print(f"=== 梯度窃取攻击检测模型训练 (Device: {CONFIG['device']}) ===")
    
    # --- 1. 加载数据 ---
    with open(CONFIG['input_file'], 'r') as f:
        raw_data = json.load(f)
    
    # 提取特征矩阵和标签
    X_all = [np.array(item['features']) for item in raw_data]
    y_all = [item['label'] for item in raw_data]
    input_dim = X_all[0].shape[1] # 自动获取特征维度 (7维)
    
    print(f"数据加载完成: {len(X_all)} 样本, 特征维度: {input_dim}")
    
    # --- 2. 划分独立测试集 (Hold-out Test Set) ---
    # 这部分数据在交叉验证中绝对不可见，用于最终模拟真实场景测试
    X_cv, X_test, y_cv, y_test = train_test_split(
        X_all, y_all, test_size=CONFIG['test_size'], stratify=y_all, random_state=42
    )
    print(f"数据集划分 -> 交叉验证集: {len(X_cv)}, 独立测试集: {len(X_test)}")
    
    # --- 3. K折交叉验证循环 ---
    skf = StratifiedKFold(n_splits=CONFIG['n_splits'], shuffle=True, random_state=42)
    
    fold_metrics = []
    best_overall_acc = 0.0
    best_model_state = None
    
    # 用于绘制 Loss 曲线的数据
    history = {"train_loss": [], "val_loss": []} 
    
    print("\n--- 开始 K-Fold Cross Validation ---")
    
    # 注意：sklearn 的 split 需要 array-like，但我们的 X 是 list of arrays (变长)，
    # 所以我们只用 y_cv 来生成索引，然后去索引 list
    for fold, (train_idx, val_idx) in enumerate(skf.split(np.zeros(len(y_cv)), y_cv)):
        print(f"\n[Fold {fold+1}/{CONFIG['n_splits']}]")
        
        # 数据切片
        X_train_fold = [X_cv[i] for i in train_idx]
        y_train_fold = [y_cv[i] for i in train_idx]
        X_val_fold = [X_cv[i] for i in val_idx]
        y_val_fold = [y_cv[i] for i in val_idx]
        
        # 特征标准化 (至关重要！)
        X_train_fold, X_val_fold, _ = standardize_features(X_train_fold, X_val_fold)
        
        # 封装 DataLoader
        train_loader = DataLoader(FLDataset(X_train_fold, y_train_fold), 
                                  batch_size=CONFIG['batch_size'], shuffle=True, collate_fn=collate_fn)
        val_loader = DataLoader(FLDataset(X_val_fold, y_val_fold), 
                                batch_size=CONFIG['batch_size'], shuffle=False, collate_fn=collate_fn)
        
        # 初始化模型
        model = GradientLeakageLSTM(input_dim, CONFIG['hidden_size'], CONFIG['num_layers']).to(CONFIG['device'])
        criterion = nn.BCELoss()
        optimizer = optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
        
        # 训练循环 (带早停)
        best_val_loss = float('inf')
        patience_counter = 0
        fold_train_losses = []
        fold_val_losses = []
        
        for epoch in range(CONFIG['epochs']):
            train_loss = train_one_epoch(model, train_loader, criterion, optimizer, CONFIG['device'])
            val_metrics = evaluate(model, val_loader, criterion, CONFIG['device'])
            val_loss = val_metrics['loss']
            
            fold_train_losses.append(train_loss)
            fold_val_losses.append(val_loss)
            
            # 早停检查
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # 如果是当前所有 Fold 中最好的，保存模型
                if val_metrics['accuracy'] > best_overall_acc:
                    best_overall_acc = val_metrics['accuracy']
                    best_model_state = model.state_dict()
                    torch.save(best_model_state, CONFIG['model_save_path'])
            else:
                patience_counter += 1
                
            if patience_counter >= CONFIG['patience']:
                print(f"  Early stopping at epoch {epoch}")
                break
                
        # 记录本折的最终性能
        print(f"  Result: Acc={val_metrics['accuracy']:.4f}, F1={val_metrics['f1']:.4f}")
        fold_metrics.append(val_metrics)
        
        # 记录第一折的 Loss 用于画图 (简化展示)
        if fold == 0:
            history['train_loss'] = fold_train_losses
            history['val_loss'] = fold_val_losses

    # --- 4. 交叉验证结果汇总 ---
    avg_acc = np.mean([m['accuracy'] for m in fold_metrics])
    avg_f1 = np.mean([m['f1'] for m in fold_metrics])
    print("\n--- Cross-Validation Summary ---")
    print(f"Average Accuracy: {avg_acc:.4f}")
    print(f"Average F1 Score: {avg_f1:.4f}")
    
    # --- 5. 独立测试集评估 (Final Evaluation) ---
    print("\n--- Final Evaluation on Independent Test Set ---")
    
    # 加载最佳模型
    final_model = GradientLeakageLSTM(input_dim, CONFIG['hidden_size'], CONFIG['num_layers']).to(CONFIG['device'])
    final_model.load_state_dict(torch.load(CONFIG['model_save_path']))
    
    # 记得对测试集也要标准化 (使用全量 CV 数据的 scaler 比较合理，这里简化为重新 fit CV 集)
    # 在生产环境中，应该保存 scaler 对象
    _, X_test_scaled, _ = standardize_features(X_cv, X_test)
    
    test_loader = DataLoader(FLDataset(X_test_scaled, y_test), batch_size=CONFIG['batch_size'], collate_fn=collate_fn)
    test_metrics = evaluate(final_model, test_loader, nn.BCELoss(), CONFIG['device'])
    
    print(f"Test Set Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"Test Set F1 Score: {test_metrics['f1']:.4f}")
    print("\nClassification Report:\n")
    print(classification_report(test_metrics['labels'], test_metrics['preds'], target_names=['Normal', 'Malicious']))

    # --- 6. 可视化 ---
    plt.figure(figsize=(12, 5))
    
    # Loss 曲线 (Fold 1)
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Training Dynamics (Fold 1)')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    
    # 混淆矩阵 (Test Set)
    plt.subplot(1, 2, 2)
    cm = confusion_matrix(test_metrics['labels'], test_metrics['preds'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Normal', 'Malicious'], yticklabels=['Normal', 'Malicious'])
    plt.title('Confusion Matrix (Test Set)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    plt.tight_layout()
    plt.savefig('lstm_evaluation_result.png')
    print("\n评估图表已保存至 lstm_evaluation_result.png")