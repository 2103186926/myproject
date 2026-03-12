import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, classification_report, roc_auc_score, confusion_matrix
import os
import sys
import logging

# ==========================================
# 1. 全局配置与日志设置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

CONFIG = {
    "input_file": r"C:\Users\21031\Desktop\myProject\侧信道攻击\2.Feature Engineering\lstm_feature_data_v2.json",
    "model_save_path": "best_lstm_model.pth",
    "random_seed": 42,
    "test_size": 0.2,       # 独立测试集比例
    "n_splits": 5,          # 交叉验证折数
    
    # 模型超参数
    "hidden_size": 128,     # 隐藏层维度
    "num_layers": 2,        # LSTM层数
    "dropout": 0.3,         # Dropout概率
    "bidirectional": True,  # 双向LSTM
    
    # 训练超参数
    "batch_size": 32,
    "epochs": 50,
    "learning_rate": 0.001,
    "patience": 10,         # 早停忍耐轮数
    "pos_weight": 2.0       # 正样本权重 (解决类别不平衡)
}

# 设置随机种子以保证可复现性
def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)

set_seed(CONFIG['random_seed'])
device = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
logger.info(f"Using device: {device}")

# ==========================================
# 2. 数据处理与增强 Dataset
# ==========================================
class OceanLogDataset(Dataset):
    def __init__(self, X, y, lengths):
        """
        X: (N, T, D) 特征矩阵
        y: (N,) 标签
        lengths: (N,) 每个序列的实际长度
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        self.lengths = torch.LongTensor(lengths)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx], self.lengths[idx]

def masked_fit_transform(X, lengths, scaler=None):
    """
    带掩码的标准化处理：只对非Padding部分进行 fit/transform
    """
    N, T, D = X.shape
    X_reshaped = X.reshape(-1, D)
    
    # 创建掩码 (Mask): 标记哪些是真实数据，哪些是 Padding (0)
    # mask 形状: (N * T, )
    mask = np.zeros((N, T), dtype=bool)
    for i, seq_len in enumerate(lengths):
        mask[i, :seq_len] = True
    mask_flat = mask.flatten()
    
    # 只提取真实数据进行 fit
    X_real = X_reshaped[mask_flat]
    
    if scaler is None:
        scaler = StandardScaler()
        scaler.fit(X_real)
    
    # 对所有数据进行 transform (Padding部分也会被transform，但这不影响，后续LSTM会忽略)
    X_scaled_flat = scaler.transform(X_reshaped)
    
    # 将 Padding 部分强制重置为 0 (可选，保持整洁)
    X_scaled_flat[~mask_flat] = 0
    
    X_scaled = X_scaled_flat.reshape(N, T, D)
    return X_scaled, scaler

# ==========================================
# 3. LSTM 模型定义 (Bi-LSTM)
# ==========================================
class SideChannelLSTM(nn.Module):
    def __init__(self, input_dim, hidden_size, num_layers, dropout, bidirectional):
        super(SideChannelLSTM, self).__init__()
        self.hidden_size = hidden_size
        self.bidirectional = bidirectional
        self.num_layers = num_layers
        
        # LSTM 层
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        # 全连接分类层
        # 双向的话，输出维度要 * 2
        fc_input_dim = hidden_size * 2 if bidirectional else hidden_size
        
        self.fc = nn.Sequential(
            nn.Linear(fc_input_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1) # 二分类输出 logits
        )

    def forward(self, x, lengths):
        # x: (Batch, Seq_Len, Feat_Dim)
        # lengths: (Batch)
        
        # 1. Pack Sequence: 压缩 Padding，让 LSTM 只计算有效部分，加速并提高精度
        # enforce_sorted=False 允许输入未按长度排序
        packed_x = pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        
        # 2. LSTM Forward
        packed_out, (hn, cn) = self.lstm(packed_x)
        
        # 3. 提取特征
        # 策略：取最后一个时间步的隐状态 (Last Hidden State)
        if self.bidirectional:
            # hn shape: (num_layers * 2, batch, hidden_size)
            # 取最后两层（前向最后一层 + 后向最后一层）拼接
            final_state = torch.cat((hn[-2], hn[-1]), dim=1)
        else:
            final_state = hn[-1]
            
        # 4. 分类头
        logits = self.fc(final_state)
        return logits

# ==========================================
# 4. 训练器 (Trainer)
# ==========================================
class Trainer:
    def __init__(self, model, criterion, optimizer, device):
        self.model = model
        self.criterion = criterion
        self.optimizer = optimizer
        self.device = device
        
    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0
        all_preds = []
        all_targets = []
        
        for X_batch, y_batch, len_batch in dataloader:
            X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
            
            self.optimizer.zero_grad()
            logits = self.model(X_batch, len_batch)
            loss = self.criterion(logits.squeeze(), y_batch)
            
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            
            # 计算指标
            probs = torch.sigmoid(logits).squeeze()
            preds = (probs > 0.5).float()
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(y_batch.cpu().numpy())
            
        avg_loss = total_loss / len(dataloader)
        acc = accuracy_score(all_targets, all_preds)
        return avg_loss, acc

    def evaluate(self, dataloader):
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_targets = []
        all_probs = []
        
        with torch.no_grad():
            for X_batch, y_batch, len_batch in dataloader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                
                logits = self.model(X_batch, len_batch)
                loss = self.criterion(logits.squeeze(), y_batch)
                
                total_loss += loss.item()
                
                probs = torch.sigmoid(logits).squeeze()
                # 处理 batch_size=1 的边界情况
                if probs.ndim == 0: probs = probs.unsqueeze(0)
                    
                preds = (probs > 0.5).float()
                
                all_probs.extend(probs.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
                all_targets.extend(y_batch.cpu().numpy())
        
        avg_loss = total_loss / len(dataloader)
        # 计算综合指标
        metrics = {
            'loss': avg_loss,
            'acc': accuracy_score(all_targets, all_preds),
            'f1': f1_score(all_targets, all_preds, zero_division=0),
            'auc': roc_auc_score(all_targets, all_probs) if len(set(all_targets)) > 1 else 0.5,
            'preds': all_preds,
            'targets': all_targets
        }
        return metrics

# ==========================================
# 5. 主流程
# ==========================================
def main():
    # --- Step 1: 加载数据 ---
    logger.info(f"Loading data from {CONFIG['input_file']}...")
    if not os.path.exists(CONFIG['input_file']):
        logger.error("Input file not found! Please run feature generation script first.")
        return

    with open(CONFIG['input_file'], 'r') as f:
        data_json = json.load(f)
        
    X_raw = np.array(data_json['X']) # (N, T, D)
    y_raw = np.array(data_json['y']) # (N,)
    
    # 处理标签：资源争用(2)和缓存攻击(1)都视为“恶意”(1)，正常为(0)
    # 二分类任务：检测是否有攻击
    y_binary = (y_raw > 0).astype(int)
    
    # 获取有效长度 (去除 Padding)
    # 假设特征工程步骤中，Padding部分全是0。我们可以通过判断全0行来确定长度，
    # 或者如果特征工程没给length，我们这里倒推一下。
    # 更好的方式是在json里存length，如果没有，通过计算非全0行数来获取。
    # 这里我们通过检查最后一个特征维度非0来判断有效性。
    lengths = []
    for seq in X_raw:
        # 找到非全0的最后一行索引 + 1
        non_zero_indices = np.where(np.any(seq != 0, axis=1))[0]
        if len(non_zero_indices) > 0:
            lengths.append(non_zero_indices[-1] + 1)
        else:
            lengths.append(1) # 防止全0序列报错
    lengths = np.array(lengths)

    logger.info(f"Data shape: X={X_raw.shape}, y={y_binary.shape}")
    logger.info(f"Class balance: Normal={np.sum(y_binary==0)}, Attack={np.sum(y_binary==1)}")

    # --- Step 2: 划分 独立测试集 (20%) ---
    # Stratified 保证测试集里的正负样本比例和总体现一致
    X_train_val, X_test, y_train_val, y_test, len_train_val, len_test = train_test_split(
        X_raw, y_binary, lengths, test_size=CONFIG['test_size'], stratify=y_binary, random_state=CONFIG['random_seed']
    )
    
    logger.info(f"Split: Train+Val={len(X_train_val)}, Test={len(X_test)}")

    # --- Step 3: 交叉验证训练 ---
    skf = StratifiedKFold(n_splits=CONFIG['n_splits'], shuffle=True, random_state=CONFIG['random_seed'])
    
    best_val_auc = 0
    best_fold_model = None
    best_scaler = None
    
    fold_results = []

    for fold, (train_idx, val_idx) in enumerate(skf.split(X_train_val, y_train_val)):
        logger.info(f"\n--- Fold {fold+1}/{CONFIG['n_splits']} ---")
        
        # 划分训练/验证
        X_train, X_val = X_train_val[train_idx], X_train_val[val_idx]
        y_train, y_val = y_train_val[train_idx], y_train_val[val_idx]
        l_train, l_val = len_train_val[train_idx], len_train_val[val_idx]
        
        # 数据标准化 (Masked Scaling) - 防止 Data Leakage，只fit训练集
        X_train_scaled, scaler = masked_fit_transform(X_train, l_train)
        X_val_scaled, _ = masked_fit_transform(X_val, l_val, scaler=scaler)
        
        # 构建 Dataset 和 DataLoader
        train_ds = OceanLogDataset(X_train_scaled, y_train, l_train)
        val_ds = OceanLogDataset(X_val_scaled, y_val, l_val)
        
        train_loader = DataLoader(train_ds, batch_size=CONFIG['batch_size'], shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=CONFIG['batch_size'], shuffle=False)
        
        # 初始化模型
        input_dim = X_train.shape[2]
        model = SideChannelLSTM(
            input_dim, CONFIG['hidden_size'], CONFIG['num_layers'], 
            CONFIG['dropout'], CONFIG['bidirectional']
        ).to(device)
        
        # 损失函数 (加权 BCE，处理样本不平衡)
        pos_weight = torch.tensor([CONFIG['pos_weight']]).to(device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
        optimizer = optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
        
        trainer = Trainer(model, criterion, optimizer, device)
        
        # 训练循环 (带早停)
        patience_counter = 0
        best_loss_in_fold = float('inf')
        
        train_losses, val_losses = [], []
        
        for epoch in range(CONFIG['epochs']):
            t_loss, t_acc = trainer.train_epoch(train_loader)
            res = trainer.evaluate(val_loader)
            v_loss, v_acc, v_auc = res['loss'], res['acc'], res['auc']
            
            train_losses.append(t_loss)
            val_losses.append(v_loss)
            
            if (epoch+1) % 5 == 0:
                logger.info(f"Epoch {epoch+1}: Train Loss={t_loss:.4f}, Val Loss={v_loss:.4f}, Val AUC={v_auc:.4f}")
            
            # 早停检查
            if v_loss < best_loss_in_fold:
                best_loss_in_fold = v_loss
                patience_counter = 0
                # 如果是当前Fold最好的，看看是不是全局最好的
                if v_auc > best_val_auc:
                    best_val_auc = v_auc
                    best_fold_model = model.state_dict()
                    best_scaler = scaler # 保存对应的Scaler
            else:
                patience_counter += 1
                if patience_counter >= CONFIG['patience']:
                    logger.info("Early stopping triggered.")
                    break
        
        fold_results.append(best_loss_in_fold)

    # --- Step 4: 独立测试集评估 ---
    logger.info("\nEvaluating on Independent Test Set (using Best CV Model)")
    
    # 使用最佳 Fold 的 Scaler 处理测试集 (防止泄露)
    X_test_scaled, _ = masked_fit_transform(X_test, len_test, scaler=best_scaler)
    
    final_model = SideChannelLSTM(input_dim, CONFIG['hidden_size'], CONFIG['num_layers'], CONFIG['dropout'], CONFIG['bidirectional']).to(device)
    final_model.load_state_dict(best_fold_model)
    torch.save(best_fold_model, CONFIG['model_save_path']) # 保存最终模型
    
    test_loader = DataLoader(OceanLogDataset(X_test_scaled, y_test, len_test), batch_size=CONFIG['batch_size'])
    # 创建一个 dummy optimizer 用于 evaluate
    test_trainer = Trainer(final_model, criterion, optimizer, device) 
    res = test_trainer.evaluate(test_loader)
    
    print("\n" + "="*50)
    print(f"FINAL RESULT: Accuracy={res['acc']:.4f}, F1={res['f1']:.4f}, AUC={res['auc']:.4f}")
    print("="*50)
    print("Classification Report:")
    print(classification_report(res['targets'], res['preds'], target_names=['Normal', 'Attack']))
    
    # 绘制训练曲线 (展示最后一折的)
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.title('Training and Validation Loss (Last Fold)')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.savefig('training_loss_curve.png')
    logger.info("Loss curve saved to training_loss_curve.png")

    # 绘制混淆矩阵
    cm = confusion_matrix(res['targets'], res['preds'])
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Normal', 'Attack'], yticklabels=['Normal', 'Attack'])
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.title('Confusion Matrix on Test Set')
    plt.savefig('confusion_matrix.png')
    logger.info("Confusion matrix saved to confusion_matrix.png")

if __name__ == "__main__":
    main()