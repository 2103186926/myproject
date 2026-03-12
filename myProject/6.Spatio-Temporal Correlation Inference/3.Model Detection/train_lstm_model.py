import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import seaborn as sns
import os

# ==========================================
# 1. 全局配置参数
# ==========================================
CONFIG = {
    # "input_file": r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\2.Feature Engineering\lstm_feature_data.json", # 输入特征文件
    # "input_file": r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\2.Feature Engineering\优化1\lstm_feature_data.json",
    "input_file": r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\2.Feature Engineering\优化2\lstm_feature_data.json",

    "model_save_path": "best_spatio_temporal_lstm.pth",
    "test_size": 0.2,       # 20% 数据作为独立测试集 (完全不参与训练/验证)
    "n_splits": 5,          # 5折交叉验证
    "batch_size": 16,
    "input_size": 5,        # 特征维度 (Action, Time, Lat, Lon, Value)
    "hidden_size": 64,      # LSTM 隐藏层维度
    "num_layers": 2,        # LSTM 层数
    "bidirectional": True,  # [优化] 使用双向 LSTM 以捕捉上下文
    "learning_rate": 0.001,
    "epochs": 50,
    "patience": 10,         # 早停机制忍耐轮数
    "device": "cuda" if torch.cuda.is_available() else "cpu"
}

# ==========================================
# 2. 数据集定义
# ==========================================
class LogSequenceDataset(Dataset):
    def __init__(self, features, labels):
        """
        features: numpy array of shape (N, Seq_Len, Feature_Dim)
        labels: numpy array of shape (N, )
        """
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

# ==========================================
# 3. 双向 LSTM 模型定义
# ==========================================
class SpatioTemporalLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, bidirectional=True):
        super(SpatioTemporalLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        # LSTM 层
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True, 
            dropout=0.2,
            bidirectional=bidirectional
        )
        
        # 全连接层分类器
        # 如果是双向，输入维度需要 * 2
        fc_input_dim = hidden_size * 2 if bidirectional else hidden_size
        self.fc = nn.Linear(fc_input_dim, 1)

    def forward(self, x):
        # x shape: (batch, seq_len, input_size)
        
        # LSTM Forward
        # out shape: (batch, seq_len, num_directions * hidden_size)
        # h_n shape: (num_layers * num_directions, batch, hidden_size)
        out, (h_n, c_n) = self.lstm(x)
        
        # [优化策略] 获取最后一个时间步的输出
        # 对于双向 LSTM，通常拼接前向的最后一个状态和后向的最后一个状态
        if self.bidirectional:
            # 拼接正向最后一步和反向最后一步
            # out[:, -1, :] 包含了双向的信息
            last_out = out[:, -1, :]
        else:
            last_out = out[:, -1, :]
        
        # 通过全连接层得到 Logits (不经过 Sigmoid，配合 BCEWithLogitsLoss 使用)
        logits = self.fc(last_out)
        return logits.squeeze()

# ==========================================
# 4. 辅助函数：训练、评估与预处理
# ==========================================
def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    for X_batch, y_batch in loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        logits = model(X_batch)
        loss = criterion(logits, y_batch)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    return total_loss / len(loader)

def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_probs = []
    all_labels = []
    
    with torch.no_grad():
        for X_batch, y_batch in loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            total_loss += loss.item()
            
            # Logits 转概率
            probs = torch.sigmoid(logits)
            preds = (probs > 0.5).float()
            
            all_probs.extend(probs.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())
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

def standardize_3d_data(X_train, X_val):
    """
    [优化] 针对 (N, Seq, Feature) 格式数据的标准化
    仅在训练集上 Fit，防止数据泄露
    """
    scaler = StandardScaler()
    
    N_train, Seq, Feat = X_train.shape
    N_val, _, _ = X_val.shape
    
    # Reshape to 2D for scaling: (N * Seq, Feat)
    X_train_flat = X_train.reshape(-1, Feat)
    X_val_flat = X_val.reshape(-1, Feat)
    
    # Fit & Transform
    X_train_scaled = scaler.fit_transform(X_train_flat).reshape(N_train, Seq, Feat)
    X_val_scaled = scaler.transform(X_val_flat).reshape(N_val, Seq, Feat)
    
    return X_train_scaled, X_val_scaled, scaler

# ==========================================
# 5. 主程序流程
# ==========================================
if __name__ == "__main__":
    print(f"=== [Spatio-Temporal Detection] LSTM Training Start (Device: {CONFIG['device']}) ===")
    
    # 1. 加载数据
    if not os.path.exists(CONFIG['input_file']):
        print(f"Error: {CONFIG['input_file']} not found. Please run Step 2 first.")
        exit()
        
    with open(CONFIG['input_file'], 'r') as f:
        raw_data = json.load(f)
    
    # 转换为 Numpy 数组
    # features shape: (N_samples, Max_Seq_Len, Feature_Dim)
    X_all = np.array([item['features'] for item in raw_data])
    y_all = np.array([item['label'] for item in raw_data])
    
    print(f"数据集加载完毕: {len(X_all)} 样本")
    print(f"特征形状: {X_all.shape} (Samples, TimeSteps, Features)")
    print(f"正常样本: {len(y_all[y_all==0])}, 攻击样本: {len(y_all[y_all==1])}")

    # 2. 划分 独立测试集 (Hold-out Test Set)
    X_cv, X_test, y_cv, y_test = train_test_split(
        X_all, y_all, test_size=CONFIG['test_size'], stratify=y_all, random_state=42
    )
    print(f"\n数据集划分 -> 交叉验证集: {len(X_cv)}, 独立测试集: {len(X_test)}")

    # 3. K-Fold 交叉验证
    skf = StratifiedKFold(n_splits=CONFIG['n_splits'], shuffle=True, random_state=42)
    fold_metrics = []
    best_cv_acc = 0.0
    
    # 用于画图的 Loss 记录 (只记录第一折)
    history = {"train_loss": [], "val_loss": []}
    
    print("\n--- 开始 5-Fold Cross Validation ---")
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X_cv, y_cv)):
        print(f"\n[Fold {fold+1}/{CONFIG['n_splits']}]")
        
        # 数据切片
        X_train_fold, y_train_fold = X_cv[train_idx], y_cv[train_idx]
        X_val_fold, y_val_fold = X_cv[val_idx], y_cv[val_idx]
        
        # [关键步骤] 特征标准化
        X_train_fold, X_val_fold, _ = standardize_3d_data(X_train_fold, X_val_fold)
        
        # 创建 DataLoader
        train_loader = DataLoader(LogSequenceDataset(X_train_fold, y_train_fold), 
                                  batch_size=CONFIG['batch_size'], shuffle=True)
        val_loader = DataLoader(LogSequenceDataset(X_val_fold, y_val_fold), 
                                batch_size=CONFIG['batch_size'], shuffle=False)
        
        # 初始化模型
        model = SpatioTemporalLSTM(
            input_size=CONFIG['input_size'],
            hidden_size=CONFIG['hidden_size'],
            num_layers=CONFIG['num_layers'],
            bidirectional=CONFIG['bidirectional']
        ).to(CONFIG['device'])
        
        # 使用 BCEWithLogitsLoss (包含 Sigmoid，数值更稳定)
        # 可选：处理样本不平衡，添加 pos_weight
        # pos_weight = torch.tensor([3.0]).to(CONFIG['device']) 
        criterion = nn.BCEWithLogitsLoss() 
        optimizer = optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
        
        # 训练循环
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(CONFIG['epochs']):
            train_loss = train_one_epoch(model, train_loader, criterion, optimizer, CONFIG['device'])
            val_metrics = evaluate(model, val_loader, criterion, CONFIG['device'])
            
            # 记录第一折 Loss
            if fold == 0:
                history['train_loss'].append(train_loss)
                history['val_loss'].append(val_metrics['loss'])
            
            # 早停与模型保存
            if val_metrics['loss'] < best_val_loss:
                best_val_loss = val_metrics['loss']
                patience_counter = 0
                # 仅在性能超越历史最佳时保存到磁盘
                if val_metrics['accuracy'] > best_cv_acc:
                    best_cv_acc = val_metrics['accuracy']
                    torch.save(model.state_dict(), CONFIG['model_save_path'])
            else:
                patience_counter += 1
                
            if patience_counter >= CONFIG['patience']:
                print(f"  Early stopping at epoch {epoch+1}")
                break
        
        print(f"  Fold Result: Acc={val_metrics['accuracy']:.4f}, F1={val_metrics['f1']:.4f}")
        fold_metrics.append(val_metrics)

    # 4. 交叉验证结果汇总
    avg_acc = np.mean([m['accuracy'] for m in fold_metrics])
    avg_f1 = np.mean([m['f1'] for m in fold_metrics])
    print("\n--- Cross-Validation Summary ---")
    print(f"Average Accuracy: {avg_acc:.4f}")
    print(f"Average F1 Score: {avg_f1:.4f}")

    # 5. 独立测试集最终评估
    print("\n--- Final Evaluation on Independent Test Set ---")
    
    # 重新加载表现最好的模型参数
    best_model = SpatioTemporalLSTM(
        input_size=CONFIG['input_size'],
        hidden_size=CONFIG['hidden_size'],
        num_layers=CONFIG['num_layers'],
        bidirectional=CONFIG['bidirectional']
    ).to(CONFIG['device'])
    best_model.load_state_dict(torch.load(CONFIG['model_save_path']))
    
    # 同样需要对测试集进行标准化 (使用 CV 集训练的 scaler)
    _, X_test_scaled, _ = standardize_3d_data(X_cv, X_test)
    
    test_loader = DataLoader(LogSequenceDataset(X_test_scaled, y_test), batch_size=CONFIG['batch_size'])
    test_metrics = evaluate(best_model, test_loader, nn.BCEWithLogitsLoss(), CONFIG['device'])
    
    print(f"Test Accuracy: {test_metrics['accuracy']:.4f}")
    print(f"Test F1 Score: {test_metrics['f1']:.4f}")
    print("\nClassification Report:\n")
    print(classification_report(test_metrics['labels'], test_metrics['preds'], target_names=['Normal', 'Malicious']))

    # 6. 可视化结果
    plt.figure(figsize=(14, 6))
    
    # Loss 曲线
    plt.subplot(1, 2, 1)
    if history['train_loss']:
        plt.plot(history['train_loss'], label='Train Loss')
        plt.plot(history['val_loss'], label='Val Loss')
        plt.title('Training Dynamics (Fold 1)')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # 混淆矩阵
    plt.subplot(1, 2, 2)
    cm = confusion_matrix(test_metrics['labels'], test_metrics['preds'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Normal', 'Malicious'], 
                yticklabels=['Normal', 'Malicious'])
    plt.title('Confusion Matrix (Test Set)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    plt.tight_layout()
    plt.savefig('lstm_detection_result.png')
    print("\n[Done] 评估结果已保存至 lstm_detection_result.png")