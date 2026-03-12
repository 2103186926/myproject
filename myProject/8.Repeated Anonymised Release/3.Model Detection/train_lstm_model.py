import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pack_padded_sequence
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report, roc_auc_score
import os
import logging
import sys
import copy

# ==========================================
# 1. 工程配置
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

CONFIG = {
    # 自动寻找当前目录下的特征文件，避免绝对路径报错
    "input_file": r"C:\Users\21031\Desktop\myProject\Repeated Anonymised Release\2.Feature Engineering\lstm_feature_data_entangled.json", 
    "model_save_path": "best_lstm_model.pth",
    "random_seed": 42,
    "test_size": 0.2,
    "n_splits": 5,
    
    "hidden_size": 64,
    "num_layers": 2,
    "dropout": 0.3,
    "bidirectional": True,
    
    "batch_size": 32,      # 适当增大 batch_size
    "learning_rate": 0.001,
    "num_epochs": 50,
    "patience": 10
}

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True

set_seed(CONFIG['random_seed'])
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ==========================================
# 2. 数据处理工具 (核心修复部分)
# ==========================================
class OceanLogDataset(Dataset):
    def __init__(self, X, y, lengths):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
        self.lengths = torch.LongTensor(lengths)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx], self.lengths[idx]

def load_raw_data(filepath):
    """只加载数据，不进行任何缩放"""
    if not os.path.exists(filepath):
        # 尝试在上级目录查找
        alt_path = os.path.join("..", "2.Feature Engineering", filepath)
        if os.path.exists(alt_path):
            filepath = alt_path
        else:
            logger.error(f"File not found: {filepath}")
            sys.exit(1)
            
    logger.info(f"Loading raw data from {filepath}...")
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    X = np.array(data['X'], dtype=np.float32)
    y = np.array(data['y'], dtype=np.float32)
    
    # 计算真实长度
    lengths = []
    for seq in X:
        # 假设全0行是padding
        non_zero = np.sum(~np.all(seq == 0, axis=1))
        lengths.append(max(1, non_zero))
    
    input_dim = X.shape[2]
    return X, y, np.array(lengths), input_dim

def masked_fit_transform(X, lengths, scaler=None):
    """
    [核心修复] 掩码标准化
    只对非Padding的数据进行 fit/transform，并保持Padding为0
    """
    N, L, F = X.shape
    X_out = np.zeros_like(X)
    
    # 1. 提取有效数据用于 fit
    valid_data = []
    for i in range(N):
        length = lengths[i]
        valid_data.append(X[i, :length, :])
    
    valid_data_concat = np.vstack(valid_data)
    
    # 2. Fit Scaler (仅在训练集上)
    if scaler is None:
        scaler = StandardScaler()
        scaler.fit(valid_data_concat)
        
    # 3. Transform 并回填 (保持 padding 为 0)
    for i in range(N):
        length = lengths[i]
        # 只转换有效部分
        transformed = scaler.transform(X[i, :length, :])
        X_out[i, :length, :] = transformed
        # Padding部分保持为 0 (X_out 初始化时已为0)
        
    return X_out, scaler

# ==========================================
# 3. 模型定义
# ==========================================
class AdvancedLSTM(nn.Module):
    def __init__(self, input_dim, hidden_size, num_layers, dropout, bidirectional):
        super(AdvancedLSTM, self).__init__()
        self.bidirectional = bidirectional
        
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional
        )
        
        fc_dim = hidden_size * 2 if bidirectional else hidden_size
        self.fc = nn.Sequential(
            nn.Linear(fc_dim, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1)
        )
        
    def forward(self, x, lengths):
        # 1. Pack
        packed_x = pack_padded_sequence(x, lengths.cpu(), batch_first=True, enforce_sorted=False)
        
        # 2. LSTM
        packed_out, (hn, cn) = self.lstm(packed_x)
        
        # 3. Extract last hidden state
        if self.bidirectional:
            # hn shape: (num_layers * 2, batch, hidden)
            # 取最后一层的正向和反向
            out = torch.cat((hn[-2], hn[-1]), dim=1)
        else:
            out = hn[-1]
            
        # 4. FC
        return self.fc(out)

# ==========================================
# 4. 训练器
# ==========================================
class Trainer:
    def __init__(self, model, criterion, optimizer, device):
        self.model = model
        self.criterion = criterion
        self.optimizer = optimizer
        self.device = device
        
    def train_step(self, loader):
        self.model.train()
        total_loss = 0
        all_preds, all_targets = [], []
        
        for X_b, y_b, len_b in loader:
            X_b, y_b = X_b.to(self.device), y_b.to(self.device)
            
            self.optimizer.zero_grad()
            logits = self.model(X_b, len_b).squeeze(1)
            loss = self.criterion(logits, y_b)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
            preds = (torch.sigmoid(logits) > 0.5).float()
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(y_b.cpu().numpy())
            
        return total_loss / len(loader), accuracy_score(all_targets, all_preds)

    def evaluate(self, loader):
        self.model.eval()
        total_loss = 0
        all_preds, all_probs, all_targets = [], [], []
        
        with torch.no_grad():
            for X_b, y_b, len_b in loader:
                X_b, y_b = X_b.to(self.device), y_b.to(self.device)
                
                logits = self.model(X_b, len_b).squeeze(1)
                loss = self.criterion(logits, y_b)
                total_loss += loss.item()
                
                probs = torch.sigmoid(logits)
                preds = (probs > 0.5).float()
                
                all_probs.extend(probs.cpu().numpy())
                all_preds.extend(preds.cpu().numpy())
                all_targets.extend(y_b.cpu().numpy())
                
        metrics = {
            'loss': total_loss / len(loader),
            'acc': accuracy_score(all_targets, all_preds),
            'f1': f1_score(all_targets, all_preds),
            'auc': roc_auc_score(all_targets, all_probs) if len(set(all_targets))>1 else 0.5,
            'preds': all_preds,
            'targets': all_targets
        }
        return metrics

# ==========================================
# 5. 主流程
# ==========================================
def main():
    # 1. 加载原始数据 (No scaling yet)
    X_raw, y_raw, lengths, input_dim = load_raw_data(CONFIG['input_file'])
    
    # 2. 拆分 CV集 和 独立测试集
    # 必须先拆分，防止测试集数据通过 Scaler 泄露到训练集
    indices = np.arange(len(X_raw))
    X_cv_raw, X_test_raw, y_cv, y_test, len_cv, len_test = train_test_split(
        X_raw, y_raw, lengths, test_size=CONFIG['test_size'], stratify=y_raw, random_state=CONFIG['random_seed']
    )
    logger.info(f"Data Split: CV={len(X_cv_raw)}, Test={len(X_test_raw)}")
    
    # 3. 交叉验证
    skf = StratifiedKFold(n_splits=CONFIG['n_splits'], shuffle=True, random_state=CONFIG['random_seed'])
    
    best_fold_model = None
    best_fold_score = 0.0
    best_scaler = None
    
    # 用于绘制曲线
    history = {'train_loss': [], 'val_loss': []}
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X_cv_raw, y_cv)):
        logger.info(f"\n>>> Fold {fold+1}/{CONFIG['n_splits']}")
        
        # A. 数据切分
        X_train_raw, X_val_raw = X_cv_raw[train_idx], X_cv_raw[val_idx]
        y_train, y_val = y_cv[train_idx], y_cv[val_idx]
        len_train, len_val = len_cv[train_idx], len_cv[val_idx]
        
        # B. [核心修复] 在当前 Fold 内部进行标准化
        # 1. 在训练集上 Fit
        X_train_scaled, scaler = masked_fit_transform(X_train_raw, len_train, scaler=None)
        # 2. 在验证集上 Transform (使用训练集的 scaler)
        X_val_scaled, _ = masked_fit_transform(X_val_raw, len_val, scaler=scaler)
        
        # C. DataLoader
        train_loader = DataLoader(OceanLogDataset(X_train_scaled, y_train, len_train), 
                                  batch_size=CONFIG['batch_size'], shuffle=True)
        val_loader = DataLoader(OceanLogDataset(X_val_scaled, y_val, len_val), 
                                batch_size=CONFIG['batch_size'])
        
        # D. 模型初始化
        model = AdvancedLSTM(input_dim, CONFIG['hidden_size'], CONFIG['num_layers'], CONFIG['dropout'], CONFIG['bidirectional']).to(device)
        optimizer = optim.Adam(model.parameters(), lr=CONFIG['learning_rate'])
        criterion = nn.BCEWithLogitsLoss()
        
        trainer = Trainer(model, criterion, optimizer, device)
        
        # E. 训练循环
        min_val_loss = float('inf')
        patience_cnt = 0
        fold_train_losses = []
        fold_val_losses = []
        
        for epoch in range(CONFIG['num_epochs']):
            train_loss, train_acc = trainer.train_step(train_loader)
            val_metrics = trainer.evaluate(val_loader)
            
            fold_train_losses.append(train_loss)
            fold_val_losses.append(val_metrics['loss'])
            
            if val_metrics['loss'] < min_val_loss:
                min_val_loss = val_metrics['loss']
                patience_cnt = 0
                # 记录本折最佳状态
                best_state = copy.deepcopy(model.state_dict())
                # 记录全局最佳
                if val_metrics['f1'] > best_fold_score:
                    best_fold_score = val_metrics['f1']
                    best_fold_model = best_state
                    best_scaler = scaler # 保存对应的 scaler 用于测试集
            else:
                patience_cnt += 1
                
            if epoch % 10 == 0:
                logger.info(f"Ep {epoch}: Train Loss {train_loss:.4f}, Val F1 {val_metrics['f1']:.4f}")
                
            if patience_cnt >= CONFIG['patience']:
                break
        
        # 记录第一折的曲线用于绘图
        if fold == 0:
            history['train_loss'] = fold_train_losses
            history['val_loss'] = fold_val_losses

    # 4. 独立测试集评估
    logger.info("\n>>> Evaluating on Independent Test Set (using Best CV Model)")
    
    # 使用最佳 Fold 的 Scaler 处理测试集 (防止泄露)
    X_test_scaled, _ = masked_fit_transform(X_test_raw, len_test, scaler=best_scaler)
    
    final_model = AdvancedLSTM(input_dim, CONFIG['hidden_size'], CONFIG['num_layers'], CONFIG['dropout'], CONFIG['bidirectional']).to(device)
    final_model.load_state_dict(best_fold_model)
    torch.save(best_fold_model, CONFIG['model_save_path']) # 保存最终模型
    
    test_loader = DataLoader(OceanLogDataset(X_test_scaled, y_test, len_test), batch_size=CONFIG['batch_size'])
    test_trainer = Trainer(final_model, criterion, optimizer, device) # Optimizer 不重要
    res = test_trainer.evaluate(test_loader)
    
    print("\n" + "="*50)
    print(f"FINAL RESULT: Accuracy={res['acc']:.4f}, F1={res['f1']:.4f}, AUC={res['auc']:.4f}")
    print("="*50)
    print(classification_report(res['targets'], res['preds'], target_names=['Normal', 'Attack']))
    
    # 绘图
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Loss Curve (Fold 1)')
    plt.legend()
    
    plt.subplot(1, 2, 2)
    sns.heatmap(confusion_matrix(res['targets'], res['preds']), annot=True, fmt='d', cmap='Blues')
    plt.title('Test Confusion Matrix')
    plt.savefig('evaluation_result.png')
    logger.info("Saved plots to evaluation_result.png")

if __name__ == "__main__":
    main()