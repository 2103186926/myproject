#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化的GNN训练模块 - 两阶段训练提取程序级图嵌入
阶段1: CFG-GNN训练，获取函数级图嵌入
阶段2: FCG-GNN训练，获取程序级图嵌入
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, global_mean_pool, global_add_pool
from torch_geometric.data import Data, DataLoader
from typing import List, Dict, Tuple, Optional
import numpy as np
from config import Config, get_default_config
import os
from tqdm import tqdm
import json


class AttentionPooling(nn.Module):
    """注意力池化层"""
    
    def __init__(self, in_channels: int):
        super(AttentionPooling, self).__init__()
        self.attention = nn.Linear(in_channels, 1)
    
    def forward(self, x, batch):
        """
        参数:
            x: 节点特征 [num_nodes, in_channels]
            batch: 批次索引 [num_nodes]
        """
        attn_weights = torch.sigmoid(self.attention(x))
        x_weighted = x * attn_weights
        return global_add_pool(x_weighted, batch)


class CFGGNN_V2(nn.Module):
    """CFG图神经网络 - 用于函数级特征提取"""
    
    def __init__(self, config: Config):
        super(CFGGNN_V2, self).__init__()
        
        self.config = config
        in_channels = config.model.node_feature_dim
        hidden_channels = config.model.cfg_hidden_channels
        out_channels = config.model.cfg_out_channels
        num_layers = config.model.cfg_num_layers
        dropout = config.model.cfg_dropout
        
        # 输入层
        self.conv_in = GCNConv(in_channels, hidden_channels)
        self.bn_in = nn.BatchNorm1d(hidden_channels)
        
        # 中间层
        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        for _ in range(num_layers - 2):
            self.convs.append(GCNConv(hidden_channels, hidden_channels))
            self.bns.append(nn.BatchNorm1d(hidden_channels))
        
        # 输出层
        self.conv_out = GCNConv(hidden_channels, out_channels)
        self.bn_out = nn.BatchNorm1d(out_channels)
        
        # 池化层
        if config.model.cfg_pooling == 'attention':
            self.pool = AttentionPooling(out_channels)
        else:
            self.pool = global_mean_pool
        
        self.dropout = dropout
    
    def forward(self, x, edge_index, batch=None):
        """
        前向传播
        
        返回:
            node_embeddings: 节点嵌入 [num_nodes, out_channels]
            graph_embedding: 图嵌入 [batch_size, out_channels]
        """
        # 输入层
        x = self.conv_in(x, edge_index)
        x = self.bn_in(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # 中间层（带残差连接）
        for conv, bn in zip(self.convs, self.bns):
            identity = x
            x = conv(x, edge_index)
            x = bn(x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
            x = x + identity
        
        # 输出层
        x = self.conv_out(x, edge_index)
        x = self.bn_out(x)
        
        node_embeddings = x
        
        # 图级池化
        if batch is not None:
            graph_embedding = self.pool(x, batch)
        else:
            graph_embedding = torch.mean(x, dim=0, keepdim=True)
        
        return node_embeddings, graph_embedding


class FCGGNN_V2(nn.Module):
    """FCG图神经网络 - 用于程序级特征提取"""
    
    def __init__(self, config: Config):
        super(FCGGNN_V2, self).__init__()
        
        self.config = config
        # FCG节点特征 = CFG嵌入（不使用原始0填充特征）
        in_channels = config.model.cfg_out_channels
        hidden_channels = config.model.fcg_hidden_channels
        out_channels = config.model.fcg_out_channels
        num_layers = config.model.fcg_num_layers
        dropout = config.model.fcg_dropout
        
        # 使用GAT（图注意力网络）
        self.conv_in = GATConv(in_channels, hidden_channels, heads=4, concat=True)
        self.bn_in = nn.BatchNorm1d(hidden_channels * 4)
        
        # 中间层
        self.convs = nn.ModuleList()
        self.bns = nn.ModuleList()
        for _ in range(num_layers - 2):
            self.convs.append(GATConv(hidden_channels * 4, hidden_channels, heads=4, concat=True))
            self.bns.append(nn.BatchNorm1d(hidden_channels * 4))
        
        # 输出层
        self.conv_out = GATConv(hidden_channels * 4, out_channels, heads=1, concat=False)
        self.bn_out = nn.BatchNorm1d(out_channels)
        
        # 池化层
        if config.model.fcg_pooling == 'attention':
            self.pool = AttentionPooling(out_channels)
        else:
            self.pool = global_mean_pool
        
        self.dropout = dropout
    
    def forward(self, x, edge_index, batch=None):
        """
        前向传播
        
        返回:
            node_embeddings: 节点嵌入 [num_nodes, out_channels]
            graph_embedding: 图嵌入（程序级） [batch_size, out_channels]
        """
        # 输入层
        x = self.conv_in(x, edge_index)
        x = self.bn_in(x)
        x = F.elu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        
        # 中间层（带残差连接）
        for conv, bn in zip(self.convs, self.bns):
            identity = x  # 保存输入，用于残差连接
            x = conv(x, edge_index)
            x = bn(x)
            x = F.elu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
            x = x + identity  # 残差连接：输出 = 变换后的特征 + 原始输入
        
        # 输出层
        x = self.conv_out(x, edge_index)
        x = self.bn_out(x)
        
        node_embeddings = x
        
        # 图级池化（程序级嵌入）
        if batch is not None:
            graph_embedding = self.pool(x, batch)
        else:
            graph_embedding = torch.mean(x, dim=0, keepdim=True)
        
        return node_embeddings, graph_embedding


class FCGClassifier(nn.Module):
    """基于FCG-GNN的二分类器（恶意程序检测）"""
    
    def __init__(self, config: Config):
        super(FCGClassifier, self).__init__()
        
        self.fcg_gnn = FCGGNN_V2(config)
        
        # 分类头 三层 MLP（两个隐藏层 + 输出层）
        in_features = config.model.fcg_out_channels
        self.classifier = nn.Sequential(  #!待验证： 共2层（隐藏层 + 输出层） 或 1层nn.Linear
            nn.Linear(in_features, in_features // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            # nn.Linear(in_features // 2, in_features // 4),
            # nn.ReLU(),
            # nn.Dropout(0.3),
            nn.Linear(in_features // 2, 2)  # 二分类
        )
    
    def forward(self, x, edge_index, batch=None):
        """
        前向传播
        
        返回:
            logits: 分类logits [batch_size, 2]
            graph_embedding: 图嵌入 [batch_size, out_channels]
        """
        _, graph_embedding = self.fcg_gnn(x, edge_index, batch)
        logits = self.classifier(graph_embedding)
        return logits, graph_embedding
    
    def load_fcg_weights(self, fcg_model_path: str):
        """加载预训练的FCG-GNN权重"""
        state_dict = torch.load(fcg_model_path)
        self.fcg_gnn.load_state_dict(state_dict)
        print(f"已加载FCG-GNN权重: {fcg_model_path}")


class EarlyStopping:
    """早停机制"""
    
    def __init__(self, patience: int = 15, min_delta: float = 0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
    
    def __call__(self, val_loss: float) -> bool:
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0
        
        return self.early_stop


class GNNTrainer:
    """GNN训练器 - 两阶段训练"""
    
    def __init__(self, config: Config):
        self.config = config
        self.device = torch.device(
            f'cuda:{config.training.gpu_id}' 
            if config.training.use_gpu and torch.cuda.is_available() 
            else 'cpu'
        )
    
    def train_cfg_gnn(self, model: CFGGNN_V2, train_loader: DataLoader,
                     val_loader: Optional[DataLoader] = None,
                     save_best_model: bool = True,
                     model_save_path: Optional[str] = None) -> Tuple[CFGGNN_V2, Dict]:
        """
        阶段1: 训练CFG GNN模型（自监督边预测任务）
        
        参数:
            save_best_model: 是否保存最佳模型
            model_save_path: 模型保存路径
        
        返回:
            (训练好的模型, 训练历史)
        """
        model = model.to(self.device)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=self.config.training.learning_rate,
            weight_decay=self.config.training.weight_decay  # L2正则化系数，惩罚项
        )
        
        # 学习率调度器
        scheduler = None
        if self.config.training.use_scheduler:
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min',  # 在 min 模式下，当监控的量停止减少时，学习率将减少
                factor=self.config.training.scheduler_factor,  # 学习率将减少的因子
                patience=self.config.training.scheduler_patience  # 允许没有改进的 epoch 数量，之后将减少学习率
            )
        
        # 早停
        early_stopping = None
        if self.config.training.early_stopping:
            early_stopping = EarlyStopping(
                patience=self.config.training.patience,
                min_delta=self.config.training.min_delta
            )  # 监控验证损失，若连续 patience 个epoch没有下降超过 min_delta，则触发早停。
        
        # 损失函数（边预测）
        criterion = nn.BCEWithLogitsLoss()  # 二分类交叉熵损失
        
        # 训练历史
        history = {
            'train_loss': [],
            'val_loss': []
        }
        
        # 保存最佳模型状态
        best_val_loss = float('inf')
        best_model_state = None
        
        print(f"[阶段1] 开始训练CFG GNN，设备: {self.device}")
        
        for epoch in range(self.config.training.cfg_epochs):
            # 训练阶段
            model.train()
            train_loss = 0.0
            valid_batches = 0
            
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                
                # 前向传播
                node_emb, _ = model(batch.x, batch.edge_index, batch.batch)
                
                # 边预测任务（自监督）
                pos_edge_index = batch.edge_index
                
                # 负采样
                try:
                    from torch_geometric.utils import negative_sampling
                    neg_edge_index = negative_sampling(
                        edge_index=pos_edge_index,
                        num_nodes=batch.num_nodes
                    ).to(self.device)
                except Exception as e:
                    print(f"负采样失败: {e}")
                    continue
                
                # 计算边预测损失
                pos_score = (node_emb[pos_edge_index[0]] * node_emb[pos_edge_index[1]]).sum(dim=1)
                neg_score = (node_emb[neg_edge_index[0]] * node_emb[neg_edge_index[1]]).sum(dim=1)
                
                pos_loss = criterion(pos_score, torch.ones_like(pos_score))
                neg_loss = criterion(neg_score, torch.zeros_like(neg_score))
                
                loss = pos_loss + neg_loss
                
                # 反向传播
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # 在优化器更新参数之前，进行梯度裁剪
                optimizer.step()
                
                train_loss += loss.item()
                valid_batches += 1
            
            avg_train_loss = train_loss / max(valid_batches, 1)
            history['train_loss'].append(avg_train_loss)
            
            # 验证阶段
            if val_loader is not None and len(val_loader) > 0:
                val_loss = self._validate_cfg(model, val_loader, criterion)
                history['val_loss'].append(val_loss)
                
                # 保存最佳模型
                if save_best_model and val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_model_state = model.state_dict().copy()  # 深拷贝模型状态
                    if model_save_path:
                        torch.save(best_model_state, model_save_path)
                        # print(f"保存最佳CFG模型 (val_loss: {val_loss:.4f}) -> {model_save_path}")
                
                # 学习率调度
                if scheduler is not None:
                    scheduler.step(val_loss)
                
                # 早停检查
                if early_stopping is not None:
                    if early_stopping(val_loss):
                        print(f"早停触发，在第 {epoch+1} 轮停止训练")
                        break
                
                if (epoch + 1) % 5 == 0:
                    print(f"Epoch {epoch+1}/{self.config.training.cfg_epochs}, "
                          f"Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}")
            else:  # 如果没有验证集，只打印训练损失
                if (epoch + 1) % 5 == 0:
                    print(f"Epoch {epoch+1}/{self.config.training.cfg_epochs}, "
                          f"Train Loss: {avg_train_loss:.4f}")
        
        # 加载最佳模型状态
        if best_model_state is not None:
            model.load_state_dict(best_model_state)
            print(f"[阶段1] 已加载最佳CFG模型 (val_loss: {best_val_loss:.4f})")
        
        print("[阶段1] CFG GNN训练完成")
        return model, history
    
    def train_fcg_gnn(self, model: FCGGNN_V2, train_loader: DataLoader,
                     val_loader: Optional[DataLoader] = None,
                     save_best_model: bool = True,
                     model_save_path: Optional[str] = None) -> Tuple[FCGGNN_V2, Dict]:
        """
        阶段2: 训练FCG GNN模型（自监督边预测任务）
        
        参数:
            save_best_model: 是否保存最佳模型
            model_save_path: 模型保存路径
        
        返回:
            (训练好的模型, 训练历史)
        """
        model = model.to(self.device)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=self.config.training.learning_rate,
            weight_decay=self.config.training.weight_decay
        )
        
        scheduler = None
        if self.config.training.use_scheduler:
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min',
                factor=self.config.training.scheduler_factor,
                patience=self.config.training.scheduler_patience
            )
        
        early_stopping = None
        if self.config.training.early_stopping:
            early_stopping = EarlyStopping(
                patience=self.config.training.patience,
                min_delta=self.config.training.min_delta
            )
        
        criterion = nn.BCEWithLogitsLoss()
        
        history = {
            'train_loss': [],
            'val_loss': []
        }
        
        best_val_loss = float('inf')
        best_model_state = None  # 保存最佳模型状态
        
        print(f"[阶段2] 开始训练FCG GNN，设备: {self.device}")
        
        for epoch in range(self.config.training.fcg_epochs):
            model.train()
            train_loss = 0.0
            valid_batches = 0
            
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                
                node_emb, _ = model(batch.x, batch.edge_index, batch.batch)
                
                # 边预测
                pos_edge_index = batch.edge_index
                
                try:
                    from torch_geometric.utils import negative_sampling
                    neg_edge_index = negative_sampling(
                        edge_index=pos_edge_index,
                        num_nodes=batch.num_nodes
                    ).to(self.device)
                except Exception as e:
                    print(f"负采样失败: {e}")
                    continue
                
                pos_score = (node_emb[pos_edge_index[0]] * node_emb[pos_edge_index[1]]).sum(dim=1)
                neg_score = (node_emb[neg_edge_index[0]] * node_emb[neg_edge_index[1]]).sum(dim=1)
                
                pos_loss = criterion(pos_score, torch.ones_like(pos_score))
                neg_loss = criterion(neg_score, torch.zeros_like(neg_score))
                
                loss = pos_loss + neg_loss
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                
                train_loss += loss.item()
                valid_batches += 1
            
            avg_train_loss = train_loss / max(valid_batches, 1)
            history['train_loss'].append(avg_train_loss)
            
            if val_loader is not None and len(val_loader) > 0:
                val_loss = self._validate_fcg(model, val_loader, criterion)  # 验证fcg_gnn模型
                history['val_loss'].append(val_loss)
                
                # 保存最佳模型
                if save_best_model and val_loss < best_val_loss:
                    best_val_loss = val_loss
                    best_model_state = model.state_dict().copy()  # 深拷贝模型状态
                    if model_save_path:
                        torch.save(best_model_state, model_save_path)
                        # print(f"保存最佳FCG模型 (val_loss: {val_loss:.4f}) -> {model_save_path}")
                
                if scheduler is not None:
                    scheduler.step(val_loss)
                
                if early_stopping is not None:
                    if early_stopping(val_loss):
                        print(f"早停触发，在第 {epoch+1} 轮停止训练")
                        break
                
                if (epoch + 1) % 5 == 0:
                    print(f"Epoch {epoch+1}/{self.config.training.fcg_epochs}, "
                          f"Train Loss: {avg_train_loss:.4f}, Val Loss: {val_loss:.4f}")
            else:
                if (epoch + 1) % 5 == 0:
                    print(f"Epoch {epoch+1}/{self.config.training.fcg_epochs}, "
                          f"Train Loss: {avg_train_loss:.4f}")
        
        # 加载最佳模型状态
        if best_model_state is not None:
            model.load_state_dict(best_model_state)
            print(f"[阶段2] 已加载最佳FCG模型 (val_loss: {best_val_loss:.4f})")
        
        print("[阶段2] FCG GNN训练完成")
        return model, history
    
    def _validate_cfg(self, model, val_loader, criterion):
        """验证CFG模型"""
        model.eval()
        val_loss = 0.0
        valid_batches = 0
        
        if len(val_loader) == 0:
            return 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(self.device)
                
                node_emb, _ = model(batch.x, batch.edge_index, batch.batch)
                
                pos_edge_index = batch.edge_index
                
                try:
                    from torch_geometric.utils import negative_sampling
                    neg_edge_index = negative_sampling(
                        edge_index=pos_edge_index,
                        num_nodes=batch.num_nodes
                    ).to(self.device)
                except:
                    continue
                
                pos_score = (node_emb[pos_edge_index[0]] * node_emb[pos_edge_index[1]]).sum(dim=1)
                neg_score = (node_emb[neg_edge_index[0]] * node_emb[neg_edge_index[1]]).sum(dim=1)
                
                pos_loss = criterion(pos_score, torch.ones_like(pos_score))
                neg_loss = criterion(neg_score, torch.zeros_like(neg_score))
                
                loss = pos_loss + neg_loss
                val_loss += loss.item()
                valid_batches += 1
        
        return val_loss / max(valid_batches, 1)
    
    def _validate_fcg(self, model, val_loader, criterion):
        """验证FCG模型"""
        model.eval()
        val_loss = 0.0
        valid_batches = 0
        
        if len(val_loader) == 0:
            return 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(self.device)
                
                node_emb, _ = model(batch.x, batch.edge_index, batch.batch)
                
                pos_edge_index = batch.edge_index
                
                try:
                    from torch_geometric.utils import negative_sampling
                    neg_edge_index = negative_sampling(
                        edge_index=pos_edge_index,
                        num_nodes=batch.num_nodes
                    ).to(self.device)
                except:
                    continue
                
                pos_score = (node_emb[pos_edge_index[0]] * node_emb[pos_edge_index[1]]).sum(dim=1)
                neg_score = (node_emb[neg_edge_index[0]] * node_emb[neg_edge_index[1]]).sum(dim=1)
                
                pos_loss = criterion(pos_score, torch.ones_like(pos_score))
                neg_loss = criterion(neg_score, torch.zeros_like(neg_score))
                
                loss = pos_loss + neg_loss
                val_loss += loss.item()
                valid_batches += 1
        
        return val_loss / max(valid_batches, 1)
    
    def extract_program_embeddings(self, model: FCGGNN_V2, 
                                  data_list: List[Data],
                                  output_dir: str,
                                  batch_size: int = 32) -> Dict[str, np.ndarray]:
        """
        提取程序级图嵌入并保存为numpy文件
        使用与训练时相同的批量处理和池化方式
        
        参数:
            model: 训练好的FCG模型
            data_list: FCG数据列表
            output_dir: 输出目录
            batch_size: 批量大小
        
        返回:
            {file_path: embedding_array} 字典
        """
        model.eval()
        model = model.to(self.device)
        
        os.makedirs(output_dir, exist_ok=True)
        
        embeddings_dict = {}
        
        print(f"\n提取程序级图嵌入...")
        
        # 使用DataLoader进行批量处理，确保与训练时一致
        data_loader = DataLoader(data_list, batch_size=batch_size, shuffle=False)
        
        # 用于追踪当前处理到哪个图
        graph_idx = 0
        
        with torch.no_grad():
            for batch in tqdm(data_loader, desc="提取程序级嵌入"):
                batch = batch.to(self.device)
                
                # 使用与训练时相同的前向传播（包括批量处理和池化）
                _, graph_embedding = model(batch.x, batch.edge_index, batch.batch)
                
                # 将批量嵌入分配到各个图
                embeddings = graph_embedding.cpu().numpy()
                
                # 获取批次中每个图的信息
                batch_size_actual = batch.num_graphs
                for i in range(batch_size_actual):
                    # 从原始数据列表中获取文件路径
                    data = data_list[graph_idx]
                    file_path = data.file_path
                    
                    # 获取对应的嵌入
                    embedding_array = embeddings[i]
                    
                    # 获取文件名
                    file_name = os.path.basename(file_path)
                    file_name_without_ext = os.path.splitext(file_name)[0]
                    
                    # 保存为numpy文件
                    npy_filename = f"{file_name_without_ext}.npy"
                    npy_path = os.path.join(output_dir, npy_filename)
                    np.save(npy_path, embedding_array)
                    
                    embeddings_dict[file_path] = embedding_array
                    
                    print(f"  {file_name} -> {npy_filename} (shape: {embedding_array.shape})")
                    
                    graph_idx += 1
        
        print(f"\n成功提取 {len(embeddings_dict)} 个程序级图嵌入")
        print(f"保存位置: {output_dir}")
        
        return embeddings_dict
    
    def train_classifier(self, model: FCGClassifier, train_loader: DataLoader,
                        val_loader: Optional[DataLoader] = None,
                        save_best_model: bool = True,
                        model_save_path: Optional[str] = None) -> Tuple[FCGClassifier, Dict]:
        """
        训练FCG分类器（二分类任务）
        
        返回:
            (训练好的模型, 训练历史)
        """
        model = model.to(self.device)
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=self.config.training.learning_rate,
            weight_decay=self.config.training.weight_decay
        )
        
        scheduler = None
        if self.config.training.use_scheduler:
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode='min',
                factor=self.config.training.scheduler_factor,
                patience=self.config.training.scheduler_patience
            )
        
        early_stopping = None
        if self.config.training.early_stopping:
            early_stopping = EarlyStopping(
                patience=self.config.training.patience,
                min_delta=self.config.training.min_delta
            )
        
        criterion = nn.CrossEntropyLoss()
        
        history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': []
        }
        
        best_val_acc = 0.0
        
        print(f"[分类训练] 开始训练FCG分类器，设备: {self.device}")
        
        for epoch in range(self.config.training.fcg_epochs):
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for batch in train_loader:
                batch = batch.to(self.device)
                optimizer.zero_grad()
                
                logits, _ = model(batch.x, batch.edge_index, batch.batch)
                loss = criterion(logits, batch.y)
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # 梯度裁剪函数
                optimizer.step()
                
                train_loss += loss.item()
                
                # 计算准确率
                pred = logits.argmax(dim=1)
                train_correct += (pred == batch.y).sum().item()
                train_total += batch.y.size(0)
            
            avg_train_loss = train_loss / len(train_loader)
            train_acc = train_correct / train_total
            history['train_loss'].append(avg_train_loss)
            history['train_acc'].append(train_acc)
            
            # 验证
            if val_loader is not None and len(val_loader) > 0:
                val_loss, val_acc = self._validate_classifier(model, val_loader, criterion)
                history['val_loss'].append(val_loss)
                history['val_acc'].append(val_acc)
                
                # 保存最佳模型
                if save_best_model and val_acc > best_val_acc:
                    best_val_acc = val_acc
                    if model_save_path:
                        torch.save(model.state_dict(), model_save_path)
                        print(f"保存最佳模型 (val_acc: {val_acc:.4f}) -> {model_save_path}")
                
                if scheduler is not None:
                    scheduler.step(val_loss)
                
                if early_stopping is not None:
                    if early_stopping(val_loss):
                        print(f"早停触发，在第 {epoch+1} 轮停止训练")
                        break
                
                if (epoch + 1) % 5 == 0:
                    print(f"Epoch {epoch+1}/{self.config.training.fcg_epochs}, "
                          f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}, "
                          f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
            else:
                if (epoch + 1) % 5 == 0:
                    print(f"Epoch {epoch+1}/{self.config.training.fcg_epochs}, "
                          f"Train Loss: {avg_train_loss:.4f}, Train Acc: {train_acc:.4f}")
        
        print("[分类训练] FCG分类器训练完成")
        return model, history
    
    def _validate_classifier(self, model, val_loader, criterion):
        """验证分类器"""
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(self.device)
                
                logits, _ = model(batch.x, batch.edge_index, batch.batch)
                loss = criterion(logits, batch.y)
                
                val_loss += loss.item()
                
                pred = logits.argmax(dim=1)
                val_correct += (pred == batch.y).sum().item()
                val_total += batch.y.size(0)
        
        avg_val_loss = val_loss / len(val_loader)
        val_acc = val_correct / val_total
        
        return avg_val_loss, val_acc
    
    def evaluate_classifier(self, model: FCGClassifier, test_loader: DataLoader,
                           output_dir: str) -> Dict:
        """
        评估分类器性能（二分类指标）
        
        返回:
            评估指标字典
        """
        from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                     f1_score, confusion_matrix, roc_auc_score,
                                     classification_report)
        import matplotlib.pyplot as plt  # 用于数据可视化
        # 设置 matplotlib 支持中文显示
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
        plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
        
        import seaborn as sns
        
        model.eval()
        model = model.to(self.device)
        
        all_preds = []
        all_labels = []
        all_probs = []
        
        print("\n评估分类器...")
        
        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(self.device)
                
                logits, _ = model(batch.x, batch.edge_index, batch.batch)
                probs = F.softmax(logits, dim=1)  # 对logits应用softmax函数，沿水平维度（dim=1）将分数转换为概率分布。每个样本的两个概率之和为 1。
                preds = logits.argmax(dim=1)
                
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(batch.y.cpu().numpy())
                all_probs.extend(probs[:, 1].cpu().numpy())  # (正例)恶意类的概率
        
        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)
        all_probs = np.array(all_probs)
        
        # 计算指标
        accuracy = accuracy_score(all_labels, all_preds)  # 准确率
        precision = precision_score(all_labels, all_preds, zero_division=0)  # 精确率
        recall = recall_score(all_labels, all_preds, zero_division=0)  # 召回率
        f1 = f1_score(all_labels, all_preds, zero_division=0)  # F1值
        
        try:
            auc = roc_auc_score(all_labels, all_probs)  # 计算ROC AUC分数
        except:
            auc = 0.0
        
        cm = confusion_matrix(all_labels, all_preds)  # 混淆曲线
        
        # 计算特异性和敏感性
        tn, fp, fn, tp = cm.ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc': auc,
            'specificity': specificity,
            'sensitivity': sensitivity,
            'confusion_matrix': cm.tolist()
        }
        
        # 打印结果
        print("\n" + "=" * 60)
        print("二分类评估指标")
        print("=" * 60)
        print(f"准确率 (Accuracy):    {accuracy:.4f}")
        print(f"精确率 (Precision):   {precision:.4f}")
        print(f"召回率 (Recall):      {recall:.4f}")
        print(f"F1分数 (F1-Score):    {f1:.4f}")
        print(f"AUC:                  {auc:.4f}")
        print(f"特异性 (Specificity): {specificity:.4f}")
        print(f"敏感性 (Sensitivity): {sensitivity:.4f}")
        print("\n混淆矩阵:")
        print(f"  TN: {tn:4d}  FP: {fp:4d}")
        print(f"  FN: {fn:4d}  TP: {tp:4d}")
        print("=" * 60)
        
        # 保存详细报告
        report = classification_report(all_labels, all_preds, 
                                       target_names=['正常', '恶意'],
                                       digits=4)
        print("\n分类报告:")
        print(report)
        
        # 保存结果
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存指标到JSON
        metrics_file = os.path.join(output_dir, 'evaluation_metrics.json')
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        print(f"\n指标已保存: {metrics_file}")
        
        # 保存详细报告
        report_file = os.path.join(output_dir, 'classification_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("二分类评估指标\n")
            f.write("=" * 60 + "\n")
            f.write(f"准确率 (Accuracy):    {accuracy:.4f}\n")
            f.write(f"精确率 (Precision):   {precision:.4f}\n")
            f.write(f"召回率 (Recall):      {recall:.4f}\n")
            f.write(f"F1分数 (F1-Score):    {f1:.4f}\n")
            f.write(f"AUC:                  {auc:.4f}\n")
            f.write(f"特异性 (Specificity): {specificity:.4f}\n")
            f.write(f"敏感性 (Sensitivity): {sensitivity:.4f}\n")
            f.write("\n混淆矩阵:\n")
            f.write(f"  TN: {tn:4d}  FP: {fp:4d}\n")
            f.write(f"  FN: {fn:4d}  TP: {tp:4d}\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write("\n分类报告:\n")
            f.write(report)
        print(f"报告已保存: {report_file}")
        
        # 绘制混淆矩阵
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['正常', '恶意'],
                    yticklabels=['正常', '恶意'])
        plt.title('混淆矩阵')
        plt.ylabel('真实标签')
        plt.xlabel('预测标签')
        cm_file = os.path.join(output_dir, 'confusion_matrix.png')
        plt.savefig(cm_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"混淆矩阵图已保存: {cm_file}")
        
        # 绘制ROC曲线
        if auc > 0:
            from sklearn.metrics import roc_curve
            fpr, tpr, _ = roc_curve(all_labels, all_probs)
            
            plt.figure(figsize=(8, 6))
            plt.plot(fpr, tpr, label=f'ROC曲线 (AUC = {auc:.4f})')
            plt.plot([0, 1], [0, 1], 'k--', label='随机分类器')
            plt.xlabel('假阳性率 (FPR)')
            plt.ylabel('真阳性率 (TPR)')
            plt.title('ROC曲线')
            plt.legend()
            plt.grid(True, alpha=0.3)
            roc_file = os.path.join(output_dir, 'roc_curve.png')
            plt.savefig(roc_file, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"ROC曲线已保存: {roc_file}")
        
        return metrics


if __name__ == "__main__":
    print("测试GNN训练器...")
    
    config = get_default_config()
    
    # 创建模型
    cfg_model = CFGGNN_V2(config)
    fcg_model = FCGGNN_V2(config)
    
    print(f"CFG模型参数量: {sum(p.numel() for p in cfg_model.parameters()):,}")
    print(f"FCG模型参数量: {sum(p.numel() for p in fcg_model.parameters()):,}")
    
    # 创建测试数据
    x = torch.randn(10, config.model.node_feature_dim)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=torch.long)
    batch = torch.zeros(10, dtype=torch.long)
    
    # 测试前向传播
    node_emb, graph_emb = cfg_model(x, edge_index, batch)
    print(f"\nCFG模型输出:")
    print(f"  节点嵌入: {node_emb.shape}")
    print(f"  图嵌入: {graph_emb.shape}")
    
    print("\n测试完成")
