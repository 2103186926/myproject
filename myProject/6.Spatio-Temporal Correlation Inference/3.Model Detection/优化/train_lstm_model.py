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
import random
import logging
import sys

# ==========================================
# 1. 工程配置与初始化
# ==========================================
# 配置日志输出格式
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
    # 路径配置 (请根据实际情况修改 input_file)
    # "input_file": r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\2.Feature Engineering\lstm_feature_data.json", # 输入特征文件
    # "input_file": r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\2.Feature Engineering\优化1\lstm_feature_data.json",
    "input_file": r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\2.Feature Engineering\优化2\lstm_feature_data.json",
    "model_save_path": "best_model.pth",
    "result_img_path": "evaluation_results.png",
    
    # 数据划分
    "test_size": 0.2,         # 独立测试集比例
    "n_splits": 5,            # K-Fold 折数
    "random_seed": 42,        # 随机种子
    
    # 训练超参
    "batch_size": 16,
    "hidden_size": 64,        # LSTM 隐藏层
    "num_layers": 2,          # LSTM 层数
    "bidirectional": True,    # 双向 LSTM
    "dropout": 0.3,           # 防止过拟合
    "learning_rate": 0.001,
    "epochs": 50,
    "patience": 10,           # 早停轮数
    "grad_clip": 1.0,         # 梯度裁剪阈值 (防止梯度爆炸)
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
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]

class TimeSeriesScaler:
    """
    专门用于处理 (N, Seq, Feature) 格式数据的标准化工具
    遵循 sklearn 接口风格
    """
    def __init__(self):
        self.scaler = StandardScaler()

    def fit_transform(self, X):
        # X shape: (N, Seq, Feat)
        N, Seq, Feat = X.shape
        # Flatten to (N*Seq, Feat)
        X_flat = X.reshape(-1, Feat)
        X_scaled_flat = self.scaler.fit_transform(X_flat)
        return X_scaled_flat.reshape(N, Seq, Feat)

    def transform(self, X):
        N, Seq, Feat = X.shape
        X_flat = X.reshape(-1, Feat)
        X_scaled_flat = self.scaler.transform(X_flat)
        return X_scaled_flat.reshape(N, Seq, Feat)

def load_and_parse_data(file_path):
    """加载 JSON 并自动推断输入维度"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # 提取数据
    X = np.array([item['features'] for item in raw_data])
    y = np.array([item['label'] for item in raw_data])
    
    # [自动推断维度]
    # X shape: (Samples, Seq_Len, Input_Size)
    seq_len = X.shape[1]
    input_size = X.shape[2]
    
    logger.info(f"Data Loaded. Shape: {X.shape}")
    logger.info(f"-> Auto-detected Input Size (Feature Dim): {input_size}")
    logger.info(f"-> Auto-detected Sequence Length: {seq_len}")
    
    # 更新全局配置
    CONFIG['input_size'] = input_size
    
    return X, y

# ==========================================
# 3. 模型定义 (Bi-LSTM)
# ==========================================
class AdvancedLSTM(nn.Module):
    def __init__(self, config):
        super(AdvancedLSTM, self).__init__()
        self.hidden_size = config['hidden_size']
        self.bidirectional = config['bidirectional']
        
        self.lstm = nn.LSTM(
            input_size=config['input_size'], 
            hidden_size=config['hidden_size'], 
            num_layers=config['num_layers'], 
            batch_first=True, 
            dropout=config['dropout'] if config['num_layers'] > 1 else 0,
            bidirectional=config['bidirectional']
        )
        
        fc_input_dim = config['hidden_size'] * 2 if config['bidirectional'] else config['hidden_size']
        
        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(fc_input_dim, 32),
            nn.ReLU(),
            nn.Dropout(config['dropout']),
            nn.Linear(32, 1)
        )

    def forward(self, x):
        # x: (Batch, Seq, Feat)
        out, _ = self.lstm(x)
        
        # 取最后一个时间步的输出 (对于双向 LSTM，取 Forward最后一步 和 Backward最后一步)
        if self.bidirectional:
            # out: (Batch, Seq, Dir*Hidden)
            last_out = out[:, -1, :]
        else:
            last_out = out[:, -1, :]
            
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
        for X_batch, y_batch in loader:
            X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
            
            optimizer.zero_grad()
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            
            # [优化] 梯度裁剪，防止梯度爆炸
            nn.utils.clip_grad_norm_(model.parameters(), self.config['grad_clip'])
            
            optimizer.step()
            total_loss += loss.item()
        return total_loss / len(loader)

    def evaluate(self, model, loader, criterion):
        model.eval()
        total_loss = 0
        all_preds = []
        all_probs = []
        all_labels = []
        
        with torch.no_grad():
            for X_batch, y_batch in loader:
                X_batch, y_batch = X_batch.to(self.device), y_batch.to(self.device)
                logits = model(X_batch)
                loss = criterion(logits, y_batch)
                total_loss += loss.item()
                
                probs = torch.sigmoid(logits)
                preds = (probs > 0.5).float()
                
                all_probs.extend(probs.cpu().numpy())
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

    def run_k_fold(self, X, y):
        """运行 K-Fold 交叉验证"""
        skf = StratifiedKFold(n_splits=self.config['n_splits'], shuffle=True, random_state=self.config['random_seed'])
        fold_results = []
        
        # 记录用于绘图的 History (仅记录第一折)
        history_to_plot = {"train_loss": [], "val_loss": []}
        
        logger.info(f"Starting {self.config['n_splits']}-Fold Cross Validation...")
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            logger.info(f"--- Fold {fold+1} ---")
            
            # 1. 数据准备与标准化
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            scaler = TimeSeriesScaler()
            X_train = scaler.fit_transform(X_train)
            X_val = scaler.transform(X_val)
            
            train_loader = DataLoader(LogSequenceDataset(X_train, y_train), batch_size=self.config['batch_size'], shuffle=True)
            val_loader = DataLoader(LogSequenceDataset(X_val, y_val), batch_size=self.config['batch_size'])
            
            # 2. 模型初始化
            model = AdvancedLSTM(self.config).to(self.device)
            criterion = nn.BCEWithLogitsLoss()
            optimizer = optim.Adam(model.parameters(), lr=self.config['learning_rate'])
            
            # [优化] 学习率调度器 (Loss 不下降时自动减小 LR)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
            
            # 3. 训练循环
            best_val_loss = float('inf')
            patience_cnt = 0
            
            for epoch in range(self.config['epochs']):
                train_loss = self.train_epoch(model, train_loader, criterion, optimizer)
                val_metrics = self.evaluate(model, val_loader, criterion)
                
                last_lr = optimizer.param_groups[0]['lr']
                scheduler.step(val_metrics['loss'])
                current_lr = optimizer.param_groups[0]['lr']
                if current_lr != last_lr:
                    logger.info(f"Epoch {epoch+1}: Learning rate adjusted from {last_lr} to {current_lr}")
                
                if fold == 0:
                    history_to_plot['train_loss'].append(train_loss)
                    history_to_plot['val_loss'].append(val_metrics['loss'])
                
                # 早停检查
                if val_metrics['loss'] < best_val_loss:
                    best_val_loss = val_metrics['loss']
                    patience_cnt = 0
                    # 保存最佳模型权重
                    torch.save(model.state_dict(), f"fold_{fold}_{self.config['model_save_path']}")
                else:
                    patience_cnt += 1
                    
                if patience_cnt >= self.config['patience']:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
            
            # 加载本折最佳模型进行最终评估
            model.load_state_dict(torch.load(f"fold_{fold}_{self.config['model_save_path']}"))
            final_metrics = self.evaluate(model, val_loader, criterion)
            fold_results.append(final_metrics)
            logger.info(f"Fold {fold+1} Best Result: Loss={final_metrics['loss']:.4f}, Acc={final_metrics['acc']:.4f}, F1={final_metrics['f1']:.4f}")
        
        # 清理临时文件
        # for i in range(self.config['n_splits']): os.remove(f"fold_{i}_{self.config['model_save_path']}")
        
        return fold_results, history_to_plot, scaler # 返回最后一折的 Scaler 用于测试集

# ==========================================
# 5. 可视化工具
# ==========================================
def plot_results(history, test_metrics):
    plt.figure(figsize=(14, 6))
    
    # 1. Loss Curve
    plt.subplot(1, 2, 1)
    plt.plot(history['train_loss'], label='Train Loss')
    plt.plot(history['val_loss'], label='Val Loss')
    plt.title('Training Dynamics (Fold 1)')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 2. Confusion Matrix
    plt.subplot(1, 2, 2)
    cm = confusion_matrix(test_metrics['labels'], test_metrics['preds'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Normal', 'Malicious'], 
                yticklabels=['Normal', 'Malicious'])
    plt.title('Confusion Matrix (Test Set)')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    
    plt.tight_layout()
    plt.savefig(CONFIG['result_img_path'])
    logger.info(f"Results plot saved to {CONFIG['result_img_path']}")

# ==========================================
# 6. Main Entry
# ==========================================
def main():
    set_seed(CONFIG['random_seed'])
    device = torch.device(CONFIG['device'])
    
    # 1. 加载数据 (自动维度)
    try:
        X_all, y_all = load_and_parse_data(CONFIG['input_file'])
    except Exception as e:
        logger.error(f"Data Loading Failed: {e}")
        return

    # 2. 划分独立测试集 (Hold-out)
    X_cv, X_test, y_cv, y_test = train_test_split(
        X_all, y_all, test_size=CONFIG['test_size'], stratify=y_all, random_state=CONFIG['random_seed']
    )
    logger.info(f"Data Split: CV Set ({len(X_cv)}), Hold-out Test Set ({len(X_test)})")

    # 3. 执行交叉验证训练
    trainer = Trainer(CONFIG, device)
    fold_results, history, cv_scaler = trainer.run_k_fold(X_cv, y_cv)
    
    # 4. 打印 CV 平均结果
    avg_acc = np.mean([m['acc'] for m in fold_results])
    avg_f1 = np.mean([m['f1'] for m in fold_results])
    logger.info("="*30)
    logger.info(f"Cross-Validation Average: Acc={avg_acc:.4f}, F1={avg_f1:.4f}")
    logger.info("="*30)

    # 5. 最终测试集评估 (Retrain or Load Best)
    # 这里我们使用第一折保存下来的最佳模型，配合 CV 阶段拟合好的 Scaler 进行测试
    # 在生产环境中，通常会用所有 CV 数据重新训练一个最终模型
    
    logger.info("Evaluating on Independent Test Set...")
    
    # 对测试集进行标准化 (使用 CV 数据的统计分布)
    X_test_scaled = cv_scaler.transform(X_test)
    
    # 加载第一折的最佳模型 (简化演示，实际上可以选择效果最好的一折)
    best_model_path = f"fold_0_{CONFIG['model_save_path']}"
    final_model = AdvancedLSTM(CONFIG).to(device)
    final_model.load_state_dict(torch.load(best_model_path))
    
    test_loader = DataLoader(LogSequenceDataset(X_test_scaled, y_test), batch_size=CONFIG['batch_size'])
    test_metrics = trainer.evaluate(final_model, test_loader, nn.BCEWithLogitsLoss())
    
    logger.info(f"Final Test Accuracy: {test_metrics['acc']:.4f}")
    logger.info(f"Final Test F1 Score: {test_metrics['f1']:.4f}")
    print("\n" + classification_report(test_metrics['labels'], test_metrics['preds'], target_names=['Normal', 'Malicious']))
    
    # 6. 绘图
    plot_results(history, test_metrics)

if __name__ == "__main__":
    main()