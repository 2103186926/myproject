#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
融合特征恶意代码分类模型集合
支持多种机器学习和深度学习模型的统一接口

模型列表：
1. 逻辑回归 (Logistic Regression)
2. SVM (Support Vector Machine)
3. 随机森林 (Random Forest)
4. XGBoost
5. LightGBM
6. MLP (多层感知机)
7. BiLSTM (双向LSTM)
8. Transformer
9. ResNet-1D
10. 融合模型 (Ensemble)
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import xgboost as xgb
import lightgbm as lgb
from typing import Dict, Tuple, Any, Optional, List
import logging
import json
from pathlib import Path


# ==================== 日志配置 ====================

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


logger = setup_logger(__name__)


# ==================== 基础分类器基类 ====================

class BaseClassifier:
    """分类器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """训练模型"""
        raise NotImplementedError
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        raise NotImplementedError
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        raise NotImplementedError
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """评估模型"""
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1': f1_score(y, y_pred, zero_division=0),
            'auc': roc_auc_score(y, y_proba[:, 1]) if y_proba.shape[1] > 1 else 0.0
        }
        
        return metrics


# ==================== 传统机器学习模型 ====================

class LogisticRegressionClassifier(BaseClassifier):
    """逻辑回归分类器"""
    
    def __init__(self, max_iter: int = 1000, random_state: int = 42, use_scaler: bool = True):
        super().__init__("Logistic Regression")
        self.model = LogisticRegression(max_iter=max_iter, random_state=random_state)
        self.use_scaler = use_scaler
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """训练模型"""
        if self.use_scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        logger.info(f"{self.name} 训练完成")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if self.use_scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        if self.use_scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        return self.model.predict_proba(X_scaled)


class SVMClassifier(BaseClassifier):
    """SVM分类器 (RBF核)"""
    
    def __init__(self, C: float = 1.0, gamma: str = 'scale', random_state: int = 42, use_scaler: bool = True):
        super().__init__("SVM (RBF)")
        self.model = SVC(kernel='rbf', C=C, gamma=gamma, probability=True, random_state=random_state)
        self.use_scaler = use_scaler
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """训练模型"""
        if self.use_scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        logger.info(f"{self.name} 训练完成")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        if self.use_scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        if self.use_scaler:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X
        return self.model.predict_proba(X_scaled)


class RandomForestClassifier_(BaseClassifier):
    """随机森林分类器"""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 20, random_state: int = 42):
        super().__init__("Random Forest")
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """训练模型"""
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"{self.name} 训练完成")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.model.feature_importances_


class XGBoostClassifier_(BaseClassifier):
    """XGBoost分类器"""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, 
                 learning_rate: float = 0.1, random_state: int = 42):
        super().__init__("XGBoost")
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            n_jobs=-1,
            eval_metric='logloss'
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray, 
            eval_set: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> None:
        """训练模型"""
        if eval_set is not None:
            X_eval, y_eval = eval_set
            self.model.fit(X, y, eval_set=[(X_eval, y_eval)], verbose=False)
        else:
            self.model.fit(X, y, verbose=False)
        
        self.is_fitted = True
        logger.info(f"{self.name} 训练完成")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.model.feature_importances_


class LightGBMClassifier_(BaseClassifier):
    """LightGBM分类器"""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6,
                 learning_rate: float = 0.1, random_state: int = 42):
        super().__init__("LightGBM")
        self.model = lgb.LGBMClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            n_jobs=-1,
            verbose=-1
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray,
            eval_set: Optional[Tuple[np.ndarray, np.ndarray]] = None) -> None:
        """训练模型"""
        if eval_set is not None:
            X_eval, y_eval = eval_set
            self.model.fit(X, y, eval_set=[(X_eval, y_eval)], verbose=False)
        else:
            self.model.fit(X, y, verbose=False)
        
        self.is_fitted = True
        logger.info(f"{self.name} 训练完成")
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> np.ndarray:
        """获取特征重要性"""
        return self.model.feature_importances_


# ==================== 深度学习模型 ====================

class MLPClassifier(nn.Module):
    """多层感知机分类器"""
    
    def __init__(self, input_dim: int = 256, hidden_dims: List[int] = None, dropout: float = 0.3):
        super().__init__()
        
        if hidden_dims is None:
            hidden_dims = [512, 256, 128]
        
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, 2))  # 二分类
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        return self.network(x)


class BiLSTMClassifier(nn.Module):
    """BiLSTM分类器 - 用于序列特征处理
    
    注意：BiLSTM需要将256维特征reshape为序列形式，这可能破坏特征的原始含义。
    对于融合特征，建议优先使用MLP或Transformer。
    """
    
    def __init__(self, input_dim: int = 256, hidden_dim: int = 128, 
                 num_layers: int = 2, dropout: float = 0.3, seq_len: int = 32):
        super().__init__()
        
        # 将256维特征reshape为序列形式
        # 将256维分成seq_len个时间步，每步feature_per_step维
        self.seq_len = seq_len
        self.feature_per_step = input_dim // self.seq_len
        
        if input_dim % self.seq_len != 0:
            raise ValueError(f"input_dim ({input_dim}) 必须能被 seq_len ({self.seq_len}) 整除")
        
        self.lstm = nn.LSTM(
            input_size=self.feature_per_step,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim * 2,
            num_heads=4,
            dropout=dropout,
            batch_first=True
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 2)  # 二分类
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        # x shape: (batch_size, input_dim)
        batch_size = x.size(0)
        
        # Reshape为序列形式
        x = x.view(batch_size, self.seq_len, self.feature_per_step)
        
        # LSTM
        lstm_out, _ = self.lstm(x)  # (batch_size, seq_len, hidden_dim*2)
        
        # 注意力机制
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # 全局平均池化
        pooled = attn_out.mean(dim=1)  # (batch_size, hidden_dim*2)
        
        # 分类
        output = self.fc(pooled)
        
        return output


class TransformerClassifier(nn.Module):
    """Transformer分类器"""
    
    def __init__(self, input_dim: int = 256, d_model: int = 128, 
                 nhead: int = 4, num_layers: int = 2, dropout: float = 0.3):
        super().__init__()
        
        self.seq_len = 32
        self.feature_per_step = input_dim // self.seq_len
        
        # 线性投影到d_model维
        self.embedding = nn.Linear(self.feature_per_step, d_model)
        
        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # 分类头
        self.fc = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 2)  # 二分类
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        batch_size = x.size(0)
        
        # Reshape为序列形式
        x = x.view(batch_size, self.seq_len, self.feature_per_step)
        
        # 嵌入
        x = self.embedding(x)  # (batch_size, seq_len, d_model)
        
        # Transformer
        x = self.transformer(x)  # (batch_size, seq_len, d_model)
        
        # 全局平均池化
        x = x.mean(dim=1)  # (batch_size, d_model)
        
        # 分类
        output = self.fc(x)
        
        return output


class ResNet1DClassifier(nn.Module):
    """ResNet-1D分类器"""
    
    def __init__(self, input_dim: int = 256, num_blocks: int = 3, dropout: float = 0.3):
        super().__init__()
        
        self.seq_len = 32
        self.feature_per_step = input_dim // self.seq_len
        
        # 初始卷积
        self.conv1 = nn.Conv1d(self.feature_per_step, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(64)
        
        # 残差块
        self.blocks = nn.ModuleList([
            self._make_block(64, 64, 3),
            self._make_block(64, 128, 3),
            self._make_block(128, 256, 3)
        ])
        
        # 分类头
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 2)  # 二分类
        )
    
    def _make_block(self, in_channels: int, out_channels: int, kernel_size: int) -> nn.Module:
        """创建残差块"""
        return nn.Sequential(
            nn.Conv1d(in_channels, out_channels, kernel_size, padding=kernel_size//2),
            nn.BatchNorm1d(out_channels),
            nn.ReLU(),
            nn.Conv1d(out_channels, out_channels, kernel_size, padding=kernel_size//2),
            nn.BatchNorm1d(out_channels)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        batch_size = x.size(0)
        
        # Reshape为序列形式
        x = x.view(batch_size, self.seq_len, self.feature_per_step)
        x = x.transpose(1, 2)  # (batch_size, feature_per_step, seq_len)
        
        # 初始卷积
        x = self.conv1(x)
        x = self.bn1(x)
        x = torch.relu(x)
        
        # 残差块
        for block in self.blocks:
            x = block(x)
        
        # 分类
        output = self.fc(x)
        
        return output


# ==================== 融合模型 ====================

class EnsembleClassifier(nn.Module):
    """融合分类器 - 结合多个模型"""
    
    def __init__(self, input_dim: int = 256, use_xgboost: bool = True, 
                 use_bilstm: bool = True, use_mlp: bool = True):
        super().__init__()
        
        self.use_xgboost = use_xgboost
        self.use_bilstm = use_bilstm
        self.use_mlp = use_mlp
        
        # 子模型
        self.xgboost_model = None  # 需要外部初始化
        self.bilstm_model = BiLSTMClassifier(input_dim) if use_bilstm else None
        self.mlp_model = MLPClassifier(input_dim) if use_mlp else None
        
        # 融合层
        num_models = sum([use_xgboost, use_bilstm, use_mlp])
        self.fusion = nn.Sequential(
            nn.Linear(num_models * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 2)  # 二分类
        )
    
    def forward(self, x: torch.Tensor, x_np: Optional[np.ndarray] = None) -> torch.Tensor:
        """前向传播"""
        outputs = []
        
        # XGBoost预测
        if self.use_xgboost and self.xgboost_model is not None and x_np is not None:
            xgb_proba = self.xgboost_model.predict_proba(x_np)
            outputs.append(torch.tensor(xgb_proba, dtype=torch.float32, device=x.device))
        
        # BiLSTM预测
        if self.use_bilstm and self.bilstm_model is not None:
            bilstm_out = self.bilstm_model(x)
            bilstm_proba = torch.softmax(bilstm_out, dim=1)
            outputs.append(bilstm_proba)
        
        # MLP预测
        if self.use_mlp and self.mlp_model is not None:
            mlp_out = self.mlp_model(x)
            mlp_proba = torch.softmax(mlp_out, dim=1)
            outputs.append(mlp_proba)
        
        # 融合
        if outputs:
            fused = torch.cat(outputs, dim=1)
            output = self.fusion(fused)
        else:
            output = torch.zeros(x.size(0), 2, device=x.device)
        
        return output


# ==================== 训练工具 ====================

class DeepLearningTrainer:
    """深度学习模型训练器"""
    
    def __init__(self, model: nn.Module, device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
                 learning_rate: float = 0.001, weight_decay: float = 1e-5):
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
        self.criterion = nn.CrossEntropyLoss()
        self.history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
        self.best_model_state = None
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """训练一个epoch"""
        self.model.train()
        total_loss = 0.0
        
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            self.optimizer.zero_grad()
            outputs = self.model(X_batch)
            loss = self.criterion(outputs, y_batch)
            loss.backward()
            
            # 梯度裁剪，防止梯度爆炸
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(train_loader)
    
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """验证"""
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                total_loss += loss.item()
                
                _, predicted = torch.max(outputs.data, 1)
                total += y_batch.size(0)
                correct += (predicted == y_batch).sum().item()
        
        avg_loss = total_loss / len(val_loader)
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    def fit(self, train_loader: DataLoader, val_loader: DataLoader, 
            epochs: int = 50, patience: int = 10) -> Dict[str, List]:
        """训练模型"""
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss, val_acc = self.validate(val_loader)
            
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, "
                          f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
            
            # 早停并保存最佳模型
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # 保存最佳模型状态
                self.best_model_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    logger.info(f"早停触发，在epoch {epoch+1}")
                    # 恢复最佳模型
                    if self.best_model_state is not None:
                        self.model.load_state_dict(self.best_model_state)
                        logger.info("已恢复最佳模型权重")
                    break
        
        return self.history
    
    def predict(self, X: np.ndarray, batch_size: int = 256) -> Tuple[np.ndarray, np.ndarray]:
        """预测（支持批处理，避免内存溢出）"""
        self.model.eval()
        
        all_preds = []
        all_proba = []
        
        # 分批处理
        num_samples = len(X)
        num_batches = (num_samples + batch_size - 1) // batch_size
        
        with torch.no_grad():
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, num_samples)
                
                X_batch = X[start_idx:end_idx]
                X_tensor = torch.tensor(X_batch, dtype=torch.float32).to(self.device)
                
                outputs = self.model(X_tensor)
                proba = torch.softmax(outputs, dim=1).cpu().numpy()
                pred = np.argmax(proba, axis=1)
                
                all_preds.append(pred)
                all_proba.append(proba)
        
        return np.concatenate(all_preds), np.concatenate(all_proba)
    
    def save_model(self, path: str) -> None:
        """保存模型"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'history': self.history
        }, path)
        logger.info(f"模型已保存到: {path}")
    
    def load_model(self, path: str) -> None:
        """加载模型"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.history = checkpoint['history']
        logger.info(f"模型已从 {path} 加载")


# ==================== 模型工厂 ====================

class ClassifierFactory:
    """分类器工厂"""
    
    @staticmethod
    def create_classifier(model_name: str, use_scaler: bool = False, **kwargs) -> BaseClassifier:
        """创建分类器
        
        参数:
            model_name: 模型名称
            use_scaler: 是否使用标准化（如果数据已经标准化，设为False）
            **kwargs: 其他模型参数
        """
        
        if model_name == 'logistic_regression':
            return LogisticRegressionClassifier(use_scaler=use_scaler, **kwargs)
        elif model_name == 'svm':
            return SVMClassifier(use_scaler=use_scaler, **kwargs)
        elif model_name == 'random_forest':
            return RandomForestClassifier_(**kwargs)
        elif model_name == 'xgboost':
            return XGBoostClassifier_(**kwargs)
        elif model_name == 'lightgbm':
            return LightGBMClassifier_(**kwargs)
        else:
            raise ValueError(f"未知的分类器: {model_name}")
    
    @staticmethod
    def create_dl_model(model_name: str, input_dim: int = 256, **kwargs) -> nn.Module:
        """创建深度学习模型"""
        
        if model_name == 'mlp':
            return MLPClassifier(input_dim=input_dim, **kwargs)
        elif model_name == 'bilstm':
            return BiLSTMClassifier(input_dim=input_dim, **kwargs)
        elif model_name == 'transformer':
            return TransformerClassifier(input_dim=input_dim, **kwargs)
        elif model_name == 'resnet1d':
            return ResNet1DClassifier(input_dim=input_dim, **kwargs)
        elif model_name == 'ensemble':
            return EnsembleClassifier(input_dim=input_dim, **kwargs)
        else:
            raise ValueError(f"未知的深度学习模型: {model_name}")


# ==================== 对比实验框架 ====================

class ComparisonExperiment:
    """对比实验框架"""
    
    def __init__(self, output_dir: str = './comparison_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
    
    def run_ml_models(self, X_train: np.ndarray, y_train: np.ndarray,
                      X_val: np.ndarray, y_val: np.ndarray,
                      X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Dict]:
        """运行传统机器学习模型"""
        
        ml_models = [
            ('logistic_regression', {}),
            ('svm', {'C': 1.0, 'gamma': 'scale'}),
            ('random_forest', {'n_estimators': 100}),
            ('xgboost', {'n_estimators': 100}),
            ('lightgbm', {'n_estimators': 100})
        ]
        
        for model_name, params in ml_models:
            logger.info(f"训练 {model_name}...")
            
            classifier = ClassifierFactory.create_classifier(model_name, **params)
            classifier.fit(X_train, y_train)
            
            # 评估
            train_metrics = classifier.evaluate(X_train, y_train)
            val_metrics = classifier.evaluate(X_val, y_val)
            test_metrics = classifier.evaluate(X_test, y_test)
            
            self.results[model_name] = {
                'train': train_metrics,
                'val': val_metrics,
                'test': test_metrics
            }
            
            logger.info(f"{model_name} - Test Acc: {test_metrics['accuracy']:.4f}, "
                       f"AUC: {test_metrics['auc']:.4f}")
        
        return self.results
    
    def save_results(self, filename: str = 'comparison_results.json') -> None:
        """保存结果"""
        output_file = self.output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")


if __name__ == "__main__":
    logger.info("融合特征分类模型集合已加载")
    logger.info("支持的模型: 逻辑回归, SVM, 随机森林, XGBoost, LightGBM, MLP, BiLSTM, Transformer, ResNet-1D, 融合模型")
