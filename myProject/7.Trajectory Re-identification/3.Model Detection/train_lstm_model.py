'''
训练 LSTM 模型进行轨迹识别
'''

import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import seaborn as sns
import os
import random
import logging
import sys

# ==========================================
# 1. 工程配置与初始化
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("training.log", mode='w')
    ]
)
logger = logging.getLogger(__name__)

CONFIG = {
    # [优化] 使用相对路径，适应性更强
    # "input_file": r"C:\Users\21031\Desktop\myProject\Trajectory Re-identification\2.Feature Engineering\lstm_feature_data.json", 
    # "input_file": r"C:\Users\21031\Desktop\myProject\Trajectory Re-identification\2.Feature Engineering\优化1\lstm_feature_data.json", 
    "input_file": r"C:\Users\21031\Desktop\myProject\Trajectory Re-identification\2.Feature Engineering\优化2\lstm_feature_data.json", 

    "model_save_path": "best_model.pth",
    "result_img_path": "evaluation_results.png",
    
    # 数据划分
    "test_size": 0.2,         # 独立测试集比例
    "n_splits": 5,            # K-Fold 折数
    "random_seed": 42,        # 随机种子
    
    # 训练超参
    "batch_size": 16,
    "hidden_size": 64,        # LSTM 隐藏层神经元数
    "num_layers": 2,          # LSTM 层数
    "bidirectional": True,    # 双向 LSTM
    "dropout": 0.3,           # 防止过拟合
    "learning_rate": 0.001,
    "epochs": 50,
    "patience": 10,           # 早停轮数
    "grad_clip": 1.0,         # 梯度裁剪阈值
    "device": torch.device("cuda" if torch.cuda.is_available() else "cpu")
}

def set_seed(seed):
    """固定随机种子，确保实验可复现"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    logger.info(f"Random seed set to {seed}")

# ==========================================
# 2. 数据处理模块
# ==========================================
class LogSequenceDataset(Dataset):
    def __init__(self, features, labels, lengths):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)
        # [优化] 传入真实序列长度，用于处理 Padding 问题
        self.lengths = torch.tensor(lengths, dtype=torch.long)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx], self.lengths[idx]

class TimeSeriesScaler:
    """专门用于处理 (N, Seq, Feature) 格式数据的标准化工具"""
    def __init__(self):
        self.scaler = StandardScaler()

    def fit_transform(self, X):
        # X shape: (N, Seq, Feat)
        N, Seq, Feat = X.shape
        X_flat = X.reshape(-1, Feat)
        # 只对非 Padding (非全0) 的部分 fit 也许更准，但全局 fit 也可以
        X_scaled_flat = self.scaler.fit_transform(X_flat)
        return X_scaled_flat.reshape(N, Seq, Feat)

    def transform(self, X):
        N, Seq, Feat = X.shape
        X_flat = X.reshape(-1, Feat)
        X_scaled_flat = self.scaler.transform(X_flat)
        return X_scaled_flat.reshape(N, Seq, Feat)

def load_and_parse_data(file_path):
    """加载 JSON 并自动推断维度"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # 提取特征、标签和长度
    X = np.array([item['features'] for item in raw_data])
    y = np.array([item['label'] for item in raw_data])
    # [优化] 获取上一环节生成的真实长度
    lengths = np.array([item['seq_len'] for item in raw_data])
    
    # 自动推断维度
    seq_len = X.shape[1]
    input_size = X.shape[2]
    
    logger.info(f"Data Loaded. Shape: {X.shape}")
    logger.info(f"-> Feature Dim (Input Size): {input_size}")
    logger.info(f"-> Max Sequence Length: {seq_len}")
    
    CONFIG['input_size'] = input_size
    
    return X, y, lengths

# ==========================================
# 3. 模型定义 (Bi-LSTM with Dynamic Selection)
# ==========================================
class AdvancedLSTM(nn.Module):
    def __init__(self, config):
        super(AdvancedLSTM, self).__init__()
        self.hidden_size = config['hidden_size']
        self.bidirectional = config['bidirectional']
        self.num_directions = 2 if self.bidirectional else 1
        
        self.lstm = nn.LSTM(
            input_size=config['input_size'], 
            hidden_size=config['hidden_size'], 
            num_layers=config['num_layers'], 
            batch_first=True, 
            dropout=config['dropout'] if config['num_layers'] > 1 else 0,
            bidirectional=config['bidirectional']
        )
        
        fc_input_dim = config['hidden_size'] * self.num_directions
        
        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(fc_input_dim, 32),
            nn.ReLU(),
            nn.Dropout(config['dropout']),
            nn.Linear(32, 1)
        )

    def forward(self, x, lengths):
        # x: (Batch, Max_Seq, Feat)
        # lengths: (Batch,) - 每个样本的真实长度
        
        # LSTM Forward
        # out: (Batch, Max_Seq, Hidden * Num_Dir)
        out, _ = self.lstm(x)
        
        # [核心优化] 动态提取真实长度对应的最后一个时间步
        # 避免读取到 Padding (0填充) 的部分
        batch_size = x.size(0)
        
        # 构造索引: lengths - 1 (因为索引从0开始)
        # 确保索引在 GPU/CPU 上一致
        idx = (lengths - 1).view(-1, 1).expand(batch_size, out.size(2)).unsqueeze(1)
        if x.device.type == 'cuda':
            idx = idx.cuda()
            
        # gather: 从 dim=1 (Time Step) 中提取指定索引的 hidden state
        # last_out shape: (Batch, 1, Hidden * Num_Dir)
        last_out = out.gather(1, idx).squeeze(1)
            
        logits = self.classifier(last_out)
        return logits.squeeze()

# ==========================================
# 4. 训练与评估核心逻辑
# ==========================================
class Trainer:
    def __init__(self, config, device):
        self.config = config
        self.device = device
        
    def train_epoch(self, model, loader, criterion, optimizer):
        model.train()
        total_loss = 0
        for X_batch, y_batch, len_batch in loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            len_batch = len_batch.to(self.device)
            
            optimizer.zero_grad()
            # 传入长度信息
            logits = model(X_batch, len_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            
            nn.utils.clip_grad_norm_(model.parameters(), self.config['grad_clip'])
            optimizer.step()
            total_loss += loss.item()
        return total_loss / len(loader)

    def evaluate(self, model, loader, criterion):
        model.eval()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for X_batch, y_batch, len_batch in loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                len_batch = len_batch.to(self.device)
                
                logits = model(X_batch, len_batch)
                loss = criterion(logits, y_batch)
                total_loss += loss.item()
                
                probs = torch.sigmoid(logits)
                preds = (probs > 0.5).float()
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(y_batch.cpu().numpy())
                
        metrics = {
            "loss": total_loss / len(loader),
            "acc": accuracy_score(all_labels, all_preds),
            "f1": f1_score(all_labels, all_preds, zero_division=0),
            "preds": all_preds,
            "labels": all_labels
        }
        return metrics

    def run_k_fold(self, X, y, lengths):
        """运行 K-Fold 交叉验证"""
        skf = StratifiedKFold(n_splits=self.config['n_splits'], shuffle=True, random_state=self.config['random_seed'])
        fold_results = []
        history_to_plot = {"train_loss": [], "val_loss": []}
        
        logger.info(f"Starting {self.config['n_splits']}-Fold Cross Validation...")
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            logger.info(f"--- Fold {fold+1} ---")
            
            # 数据切分
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            len_train, len_val = lengths[train_idx], lengths[val_idx]
            
            # 标准化 (仅对特征标准化，长度不需要)
            scaler = TimeSeriesScaler()
            X_train = scaler.fit_transform(X_train)
            X_val = scaler.transform(X_val)
            
            train_loader = DataLoader(LogSequenceDataset(X_train, y_train, len_train), 
                                    batch_size=self.config['batch_size'], shuffle=True)
            val_loader = DataLoader(LogSequenceDataset(X_val, y_val, len_val), 
                                  batch_size=self.config['batch_size'])
            
            # 模型重置
            model = AdvancedLSTM(self.config).to(self.device)
            criterion = nn.BCEWithLogitsLoss()
            optimizer = optim.Adam(model.parameters(), lr=self.config['learning_rate'])
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
            
            best_val_loss = float('inf')
            patience_cnt = 0
            
            for epoch in range(self.config['epochs']):
                train_loss = self.train_epoch(model, train_loader, criterion, optimizer)
                val_metrics = self.evaluate(model, val_loader, criterion)
                
                scheduler.step(val_metrics['loss'])
                
                if fold == 0: # 仅记录第一折用于绘图
                    history_to_plot['train_loss'].append(train_loss)
                    history_to_plot['val_loss'].append(val_metrics['loss'])
                
                # 早停
                if val_metrics['loss'] < best_val_loss:
                    best_val_loss = val_metrics['loss']
                    patience_cnt = 0
                    torch.save(model.state_dict(), f"fold_{fold}_{self.config['model_save_path']}")
                else:
                    patience_cnt += 1
                    
                if patience_cnt >= self.config['patience']:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
            
            # 加载本折最佳模型
            model.load_state_dict(torch.load(f"fold_{fold}_{self.config['model_save_path']}"))
            final_metrics = self.evaluate(model, val_loader, criterion)
            fold_results.append(final_metrics)
            logger.info(f"Fold {fold+1} Result: Loss={final_metrics['loss']:.4f}, Acc={final_metrics['acc']:.4f}")
        
        return fold_results, history_to_plot, scaler

def plot_results(history, test_metrics):
    plt.figure(figsize=(14, 6))
    
    # 1. 损失曲线
    plt.subplot(1, 2, 1)
    if history['train_loss']:
        plt.plot(history['train_loss'], label='Train Loss')
        plt.plot(history['val_loss'], label='Val Loss')
        plt.title('Training Dynamics (Fold 1)')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)
    
    # 2. 混淆矩阵
    plt.subplot(1, 2, 2)
    cm = confusion_matrix(test_metrics['labels'], test_metrics['preds'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Normal', 'Attack'], 
                yticklabels=['Normal', 'Attack'])
    plt.title('Confusion Matrix (Test Set)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    plt.tight_layout()
    plt.savefig(CONFIG['result_img_path'])
    logger.info(f"Evaluation plot saved to {CONFIG['result_img_path']}")

def main():
    set_seed(CONFIG['random_seed'])
    device = torch.device(CONFIG['device'])
    
    # 1. 加载数据
    try:
        X_all, y_all, lengths_all = load_and_parse_data(CONFIG['input_file'])
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # 2. 划分独立测试集
    # 注意：lengths 也要跟着切分
    indices = np.arange(len(X_all))
    X_cv, X_test, y_cv, y_test, idx_cv, idx_test = train_test_split(
        X_all, y_all, indices, test_size=CONFIG['test_size'], stratify=y_all, random_state=CONFIG['random_seed']
    )
    len_cv, len_test = lengths_all[idx_cv], lengths_all[idx_test]
    
    logger.info(f"Split: CV Set ({len(X_cv)}), Test Set ({len(X_test)})")

    # 3. 交叉验证训练
    trainer = Trainer(CONFIG, device)
    fold_results, history, cv_scaler = trainer.run_k_fold(X_cv, y_cv, len_cv)
    
    avg_acc = np.mean([m['acc'] for m in fold_results])
    logger.info(f"CV Average Accuracy: {avg_acc:.4f}")

    # 4. 独立测试集评估 (使用 Fold 0 的模型演示)
    logger.info("Evaluating on Independent Test Set...")
    
    # 标准化
    X_test_scaled = cv_scaler.transform(X_test)
    
    # 加载模型
    best_model_path = f"fold_0_{CONFIG['model_save_path']}"
    final_model = AdvancedLSTM(CONFIG).to(device)
    final_model.load_state_dict(torch.load(best_model_path))
    
    test_loader = DataLoader(LogSequenceDataset(X_test_scaled, y_test, len_test), batch_size=CONFIG['batch_size'])
    test_metrics = trainer.evaluate(final_model, test_loader, nn.BCEWithLogitsLoss())
    
    logger.info(f"Final Test Accuracy: {test_metrics['acc']:.4f}")
    print("\n" + classification_report(test_metrics['labels'], test_metrics['preds'], target_names=['Normal', 'Attack']))
    
    plot_results(history, test_metrics)

if __name__ == "__main__":
    main()