#!/usr/bin/env python  # 指定Python解释器路径
# -*- coding: utf-8 -*-  # 指定文件编码为UTF-8

import os  # 导入操作系统相关功能模块
import time  # 导入时间相关功能模块
import random  # 导入随机数生成模块
import numpy as np  # 导入NumPy库并重命名为np
from typing import List, Dict, Tuple, Any, Optional, Union  # 导入类型注解相关类型
import networkx as nx  # 导入NetworkX图论库并重命名为nx

import torch  # 导入PyTorch深度学习库
import torch.nn as nn  # 导入PyTorch神经网络模块并重命名为nn
import torch.nn.functional as F  # 导入PyTorch函数式接口并重命名为F
import torch.optim as optim  # 导入PyTorch优化器模块并重命名为optim
from torch.utils.data import Dataset  # 从PyTorch数据工具中导入Dataset类

try:  # 尝试导入PyTorch Geometric库
    import torch_geometric  # 导入PyTorch Geometric主模块
    from torch_geometric.data import Data as PyGData  # 导入PyG的Data类并重命名为PyGData
    from torch_geometric.loader import DataLoader  # 导入PyG的DataLoader
    from torch_geometric.nn import GCNConv, GATConv, GINConv, global_mean_pool, global_add_pool, global_max_pool  # 导入PyG的图神经网络层和池化操作
    HAS_TORCH_GEOMETRIC = True  # 设置标志表示PyG库可用
except ImportError:  # 捕获导入错误
    HAS_TORCH_GEOMETRIC = False  # 设置标志表示PyG库不可用


class CFGGNN(nn.Module):  # 定义控制流图(CFG)图神经网络模型类
    """
    用于CFG的图神经网络模型
    """
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int,
                num_layers: int = 3, dropout: float = 0.5):  # 初始化方法，定义模型参数
        """
        初始化CFG-GNN模型
        
        参数:
            in_channels (int): 输入特征维度
            hidden_channels (int): 隐藏层特征维度
            out_channels (int): 输出特征维度
            num_layers (int): GNN层数
            dropout (float): Dropout概率
        """
        super(CFGGNN, self).__init__()  # 调用父类初始化方法
        
        self.in_channels = in_channels  # 存储输入特征维度
        self.hidden_channels = hidden_channels  # 存储隐藏层特征维度
        self.out_channels = out_channels  # 存储输出特征维度
        self.num_layers = num_layers  # 存储GNN层数
        self.dropout = dropout  # 存储Dropout概率
        
        # 输入层
        self.conv_in = GCNConv(in_channels, hidden_channels)  # 创建输入层图卷积
        
        # 中间层
        self.convs = nn.ModuleList()  # 创建模块列表存储中间层
        for _ in range(num_layers - 2):  # 循环创建中间层
            self.convs.append(GCNConv(hidden_channels, hidden_channels))  # 添加图卷积层到列表
        
        # 输出层
        self.conv_out = GCNConv(hidden_channels, out_channels)  # 创建输出层图卷积
        
        # 全局池化层
        self.pool = global_mean_pool  # 使用全局平均池化
        
        # 用于二分类的线性层（如果需要）
        self.classifier = nn.Linear(out_channels, 2)  # 创建分类器线性层
    
    def forward(self, x, edge_index, batch=None):  # 定义前向传播方法
        """
        前向传播
        
        参数:
            x: 节点特征矩阵
            edge_index: 边索引
            batch: 批处理索引
            
        返回:
            node_embeddings: 节点嵌入
            graph_embedding: 图嵌入（使用全局池化得到）
            logits: 分类logits（如果需要分类）
        """
        # 输入层
        x = self.conv_in(x, edge_index)  # 通过输入层图卷积
        x = F.relu(x)  # 应用ReLU激活函数
        x = F.dropout(x, p=self.dropout, training=self.training)  # 应用Dropout
        
        # 中间层
        for conv in self.convs:  # 遍历中间层图卷积
            x = conv(x, edge_index)  # 通过图卷积层
            x = F.relu(x)  # 应用ReLU激活函数
            x = F.dropout(x, p=self.dropout, training=self.training)  # 应用Dropout
        
        # 输出层
        x = self.conv_out(x, edge_index)  # 通过输出层图卷积
        
        # 节点嵌入
        node_embeddings = x  # 保存节点嵌入
        
        # 全局池化得到图嵌入
        if batch is not None:  # 如果有批处理索引
            graph_embedding = self.pool(x, batch)  # 使用全局池化得到图嵌入
            # 分类logits
            logits = self.classifier(graph_embedding)  # 通过分类器得到logits
        else:  # 如果没有批处理索引
            # 如果没有批处理索引，就使用所有节点的平均值作为图嵌入
            graph_embedding = torch.mean(x, dim=0)  # 计算所有节点的平均值
            # 分类logits
            logits = self.classifier(graph_embedding.unsqueeze(0)).squeeze(0)  # 通过分类器得到logits
        
        return node_embeddings, graph_embedding, logits  # 返回节点嵌入、图嵌入和分类logits


class FCGGNN(nn.Module):  # 定义函数调用图(FCG)图神经网络模型类
    """
    用于FCG的图神经网络模型
    """
    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int,
                num_layers: int = 2, dropout: float = 0.5, pooling: str = 'mean'):  # 初始化方法，定义模型参数
        """
        初始化FCG-GNN模型
        
        参数:
            in_channels (int): 输入特征维度
            hidden_channels (int): 隐藏层特征维度
            out_channels (int): 输出特征维度
            num_layers (int): GNN层数
            dropout (float): Dropout概率
            pooling (str): 全局池化方法 ('mean', 'add', 'max')
        """
        super(FCGGNN, self).__init__()  # 调用父类初始化方法
        
        self.in_channels = in_channels  # 存储输入特征维度
        self.hidden_channels = hidden_channels  # 存储隐藏层特征维度
        self.out_channels = out_channels  # 存储输出特征维度
        self.num_layers = num_layers  # 存储GNN层数
        self.dropout = dropout  # 存储Dropout概率
        
        # 选择池化方法
        if pooling == 'mean':  # 如果选择平均池化
            self.pool = global_mean_pool  # 使用全局平均池化
        elif pooling == 'add':  # 如果选择加和池化
            self.pool = global_add_pool  # 使用全局加和池化
        elif pooling == 'max':  # 如果选择最大池化
            self.pool = global_max_pool  # 使用全局最大池化
        else:  # 如果是其他不支持的池化方法
            raise ValueError(f"不支持的池化方法: {pooling}")  # 抛出错误
        
        # 输入层
        self.conv_in = GATConv(in_channels, hidden_channels)  # 创建输入层图注意力卷积
        
        # 中间层
        self.convs = nn.ModuleList()  # 创建模块列表存储中间层
        for _ in range(num_layers - 2):  # 循环创建中间层
            self.convs.append(GATConv(hidden_channels, hidden_channels))  # 添加图注意力卷积层到列表
        
        # 输出层
        self.conv_out = GATConv(hidden_channels, out_channels)  # 创建输出层图注意力卷积
        
        # 用于二分类的线性层（如果需要）
        self.classifier = nn.Linear(out_channels, 2)  # 创建分类器线性层
    
    def forward(self, x, edge_index, batch=None):  # 定义前向传播方法
        """
        前向传播
        
        参数:
            x: 节点特征矩阵
            edge_index: 边索引
            batch: 批处理索引
            
        返回:
            node_embeddings: 节点嵌入
            graph_embedding: 图嵌入（使用全局池化得到）
            logits: 分类logits（如果需要分类）
        """
        # 输入层
        x = self.conv_in(x, edge_index)  # 通过输入层图注意力卷积
        x = F.relu(x)  # 应用ReLU激活函数
        x = F.dropout(x, p=self.dropout, training=self.training)  # 应用Dropout
        
        # 中间层
        for conv in self.convs:  # 遍历中间层图注意力卷积
            x = conv(x, edge_index)  # 通过图注意力卷积层
            x = F.relu(x)  # 应用ReLU激活函数
            x = F.dropout(x, p=self.dropout, training=self.training)  # 应用Dropout
        
        # 输出层
        x = self.conv_out(x, edge_index)  # 通过输出层图注意力卷积
        
        # 节点嵌入
        node_embeddings = x  # 保存节点嵌入
        
        # 全局池化得到图嵌入
        if batch is not None:  # 如果有批处理索引
            graph_embedding = self.pool(x, batch)  # 使用全局池化得到图嵌入
            # 分类logits
            logits = self.classifier(graph_embedding)  # 通过分类器得到logits
        else:  # 如果没有批处理索引
            # 如果没有批处理索引，就使用所有节点的平均值作为图嵌入
            graph_embedding = torch.mean(x, dim=0)  # 计算所有节点的平均值
            # 分类logits
            logits = self.classifier(graph_embedding.unsqueeze(0)).squeeze(0)  # 通过分类器得到logits
        
        return node_embeddings, graph_embedding, logits  # 返回节点嵌入、图嵌入和分类logits


class GraphAutoEncoder(nn.Module):  # 定义图自编码器类
    """
    图自编码器，用于自监督学习
    """
    def __init__(self, encoder, decoder_hidden_channels: int):  # 初始化方法
        """
        初始化图自编码器
        
        参数:
            encoder: 编码器模型（CFGGNN或FCGGNN实例）
            decoder_hidden_channels (int): 解码器隐藏层维度
        """
        super(GraphAutoEncoder, self).__init__()  # 调用父类初始化方法
        
        self.encoder = encoder  # 存储编码器
        out_channels = encoder.out_channels  # 获取编码器输出维度
        
        # 定义解码器（边预测）
        self.decoder = nn.Sequential(  # 创建序列模型作为解码器
            nn.Linear(out_channels * 2, decoder_hidden_channels),  # 第一个线性层
            nn.ReLU(),  # ReLU激活函数
            nn.Linear(decoder_hidden_channels, 1)  # 第二个线性层，输出边存在的概率
        )
    
    def forward(self, x, edge_index, batch=None):  # 定义前向传播方法
        # 通过编码器获取节点嵌入
        node_embeddings, graph_embedding, _ = self.encoder(x, edge_index, batch)  # 使用编码器获取嵌入
        
        return node_embeddings, graph_embedding  # 返回节点嵌入和图嵌入
    
    def decode(self, z, edge_index):  # 定义解码方法
        # 边预测: 将源节点和目标节点的嵌入拼接在一起
        row, col = edge_index  # 获取边的源节点和目标节点索引
        src_embeddings = z[row]  # 获取源节点嵌入
        dst_embeddings = z[col]  # 获取目标节点嵌入
        
        edge_features = torch.cat([src_embeddings, dst_embeddings], dim=1)  # 拼接源节点和目标节点嵌入
        return self.decoder(edge_features)  # 通过解码器预测边存在的概率


def train_cfg_gnn(model, data_loader, optimizer, criterion, device, num_epochs=50):  # 定义训练CFG GNN的函数
    """
    训练CFG GNN模型
    
    参数:
        model: CFG GNN模型
        data_loader: 数据加载器
        optimizer: 优化器
        criterion: 损失函数
        device: 训练设备
        num_epochs: 训练轮数
        
    返回:
        训练后的模型和训练指标
    """
    model.train()  # 设置模型为训练模式
    model = model.to(device)  # 将模型移动到指定设备
    criterion = criterion.to(device)  # 将损失函数移动到指定设备
    
    losses = []  # 存储每个epoch的损失
    val_losses = []  # 存储每个epoch的验证损失
    
    for epoch in range(num_epochs):  # 循环训练指定轮数
        total_loss = 0  # 初始化总损失
        for batch in data_loader:  # 遍历数据加载器中的每个批次
            # 确保数据在正确的设备上
            batch = batch.to(device)  # 将批次数据移动到指定设备
            optimizer.zero_grad()  # 清空梯度
            
            # 前向传播
            node_embeddings, graph_embedding, logits = model(batch.x, batch.edge_index, batch.batch)  # 模型前向传播
            
            # 正样本边（已存在的边）
            pos_edge_index = batch.edge_index  # 获取正样本边
            
            # 负样本边（随机生成）
            neg_edge_index = torch_geometric.utils.negative_sampling(  # 使用负采样生成负样本边
                edge_index=pos_edge_index,
                num_nodes=batch.num_nodes
            ).to(device)  # 确保负样本边也在正确的设备上
            
            # 预测边的存在概率
            pos_out = torch.sigmoid((node_embeddings[pos_edge_index[0]] * node_embeddings[pos_edge_index[1]]).sum(dim=1))  # 计算正样本边的预测概率
            neg_out = torch.sigmoid((node_embeddings[neg_edge_index[0]] * node_embeddings[neg_edge_index[1]]).sum(dim=1))  # 计算负样本边的预测概率
            
            # 确保标签在正确的设备上
            pos_labels = torch.ones(pos_out.size(0), device=device)  # 创建正样本标签（全1）
            neg_labels = torch.zeros(neg_out.size(0), device=device)  # 创建负样本标签（全0）
            
            # 计算损失
            loss = criterion(  # 计算二元交叉熵损失
                torch.cat([pos_out, neg_out], dim=0),  # 拼接正负样本预测
                torch.cat([pos_labels, neg_labels], dim=0)  # 拼接正负样本标签
            )
            
            loss.backward()  # 反向传播计算梯度
            optimizer.step()  # 更新模型参数
            total_loss += loss.item()  # 累加损失
        
        # 计算平均损失
        avg_loss = total_loss / len(data_loader)  # 计算平均损失
        losses.append(avg_loss)  # 记录损失
        
        # 打印训练进度
        if (epoch+1) % 5 == 0:  # 每5个epoch打印一次
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")  # 打印训练进度
    
    # 返回训练后的模型和训练指标
    return model, {'loss': losses, 'val_loss': val_losses}  # 返回训练后的模型和训练指标


def train_fcg_gnn(model, data_loader, optimizer, criterion, device, num_epochs=50):  # 定义训练FCG GNN的函数
    """
    训练FCG GNN模型
    
    参数:
        model: FCG GNN模型
        data_loader: 数据加载器
        optimizer: 优化器
        criterion: 损失函数
        device: 训练设备
        num_epochs: 训练轮数
        
    返回:
        训练后的模型和训练指标
    """
    model.train()  # 设置模型为训练模式
    model = model.to(device)  # 将模型移动到指定设备
    criterion = criterion.to(device)  # 将损失函数移动到指定设备
    
    losses = []  # 存储每个epoch的损失
    val_losses = []  # 存储每个epoch的验证损失
    
    # 添加更详细的调试信息
    print(f"Debug - 开始训练FCG GNN模型，数据加载器中有 {len(data_loader)} 个批次")  # 打印调试信息
    
    for epoch in range(num_epochs):  # 循环训练指定轮数
        total_loss = 0  # 初始化总损失
        
        # 检查数据加载器是否为空
        if len(data_loader) == 0:  # 如果数据加载器为空
            print("警告：数据加载器为空，跳过本轮训练")  # 打印警告
            continue  # 跳过本轮训练
            
        # 检查第一个批次，判断是否包含edge_attr
        first_batch = next(iter(data_loader))  # 获取第一个批次
        has_edge_attr = hasattr(first_batch, 'edge_attr') and first_batch.edge_attr is not None  # 检查是否有边属性
        
        if not has_edge_attr:  # 如果没有边属性
            print("警告：数据不包含边属性(edge_attr)，使用简化训练流程")  # 打印警告
        
        # 重置数据加载器
        data_loader_iter = iter(data_loader)  # 创建数据加载器迭代器
        
        for batch_idx in range(len(data_loader)):  # 遍历数据加载器中的每个批次
            try:  # 尝试处理批次
                # 获取下一个批次
                try:  # 尝试获取下一个批次
                    batch = next(data_loader_iter)  # 获取下一个批次
                except StopIteration:  # 捕获迭代结束异常
                    print(f"警告: 迭代器已耗尽，但预期有 {len(data_loader)} 个批次")  # 打印警告
                    break  # 跳出循环
                    
                # 确保数据在正确的设备上
                if batch is None:  # 如果批次为None
                    print(f"警告: 批次 {batch_idx} 是None，跳过")  # 打印警告
                    continue  # 跳过此批次
                
                batch = batch.to(device)  # 将批次数据移动到指定设备
                optimizer.zero_grad()  # 清空梯度
                
                # 前向传播
                node_embeddings, graph_embedding, logits = model(batch.x, batch.edge_index, batch.batch)  # 模型前向传播
                
                # 边预测损失
                pos_edge_index = batch.edge_index  # 获取正样本边
                if pos_edge_index is None:  # 如果正样本边为None
                    print(f"警告: 批次 {batch_idx} 的边索引是None，跳过")  # 打印警告
                    continue  # 跳过此批次
                
                # 确保图中有足够的节点来进行负采样
                if batch.num_nodes <= 1:  # 如果节点数不足
                    print(f"警告: 批次 {batch_idx} 的节点数不足，跳过")  # 打印警告
                    continue  # 跳过此批次
                
                # 负采样
                try:  # 尝试进行负采样
                    neg_edge_index = torch_geometric.utils.negative_sampling(  # 使用负采样生成负样本边
                        edge_index=pos_edge_index,
                        num_nodes=batch.num_nodes
                    )
                    if neg_edge_index is not None:  # 如果负样本边不为None
                        neg_edge_index = neg_edge_index.to(device)  # 确保负样本边也在正确的设备上
                    else:  # 如果负样本边为None
                        print(f"警告: 批次 {batch_idx} 的负采样边是None，使用空张量替代")  # 打印警告
                        neg_edge_index = torch.tensor([], device=device, dtype=torch.long).reshape(2, 0)  # 创建空张量
                except Exception as e:  # 捕获异常
                    print(f"负采样时出错: {str(e)}，使用空张量替代")  # 打印错误
                    neg_edge_index = torch.tensor([], device=device, dtype=torch.long).reshape(2, 0)  # 创建空张量
                
                # 确保有足够的正负样本
                if pos_edge_index.shape[1] == 0:  # 如果没有正样本边
                    print(f"警告: 批次 {batch_idx} 没有正样本边，跳过")  # 打印警告
                    continue  # 跳过此批次
                
                if neg_edge_index.shape[1] == 0:  # 如果没有负样本边
                    print(f"警告: 批次 {batch_idx} 没有负样本边，跳过")  # 打印警告
                    continue  # 跳过此批次
                
                # 计算边的相似度
                try:  # 尝试计算边的相似度
                    pos_out = torch.sigmoid((node_embeddings[pos_edge_index[0]] * node_embeddings[pos_edge_index[1]]).sum(dim=1))  # 计算正样本边的预测概率
                    neg_out = torch.sigmoid((node_embeddings[neg_edge_index[0]] * node_embeddings[neg_edge_index[1]]).sum(dim=1))  # 计算负样本边的预测概率
                
                    # 确保标签在正确的设备上
                    pos_labels = torch.ones(pos_out.size(0), device=device)  # 创建正样本标签（全1）
                    neg_labels = torch.zeros(neg_out.size(0), device=device)  # 创建负样本标签（全0）
                    
                    edge_loss = criterion(  # 计算边预测损失
                        torch.cat([pos_out, neg_out], dim=0),  # 拼接正负样本预测
                        torch.cat([pos_labels, neg_labels], dim=0)  # 拼接正负样本标签
                    )
                    
                    # 如果有标签，可以增加分类损失
                    if hasattr(batch, 'y') and batch.y is not None:  # 如果有标签
                        batch.y = batch.y.to(device)  # 确保标签在正确的设备上
                        cls_loss = F.cross_entropy(logits, batch.y)  # 计算分类损失
                        loss = edge_loss + cls_loss  # 总损失为边预测损失和分类损失之和
                    else:  # 如果没有标签
                        loss = edge_loss  # 总损失为边预测损失
                    
                    loss.backward()  # 反向传播计算梯度
                    optimizer.step()  # 更新模型参数
                    total_loss += loss.item()  # 累加损失
                except Exception as e:  # 捕获异常
                    print(f"计算损失时出错: {str(e)}")  # 打印错误
                    # 继续下一个批次
                    continue  # 跳过此批次
            except Exception as e:  # 捕获异常
                print(f"处理批次 {batch_idx} 时出错: {str(e)}")  # 打印错误
                # 继续下一个批次
                continue  # 跳过此批次
        
        # 计算平均损失
        if len(data_loader) > 0:  # 如果数据加载器不为空
            avg_loss = total_loss / len(data_loader)  # 计算平均损失
            losses.append(avg_loss)  # 记录损失
            
            # 打印训练进度
            if (epoch+1) % 5 == 0 or epoch == 0:  # 每5个epoch或第一个epoch打印一次
                print(f"Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")  # 打印训练进度
        else:  # 如果数据加载器为空
            print(f"警告: 数据加载器为空，无法计算平均损失")  # 打印警告
    
    # 返回训练后的模型和训练指标
    return model, {'loss': losses, 'val_loss': val_losses}  # 返回训练后的模型和训练指标


def enrich_fcg_with_cfg_embeddings(cfg_gnn_model, list_of_fcg_data, cfg_data_dict, device):  # 定义使用CFG嵌入增强FCG的函数
    """
    使用训练好的CFG GNN模型生成的CFG嵌入来增强FCG节点特征
    
    参数:
        cfg_gnn_model: 训练好的CFG GNN模型
        list_of_fcg_data: FCG图数据列表
        cfg_data_dict: 函数名到CFG图数据的映射
        device: 计算设备
        
    返回:
        增强后的FCG图数据列表
    """
    # 确保模型在评估模式并位于正确的设备上
    cfg_gnn_model.eval()  # 设置模型为评估模式
    cfg_gnn_model = cfg_gnn_model.to(device)  # 将模型移动到指定设备
    
    enriched_fcg_data = []  # 存储增强后的FCG数据
    
    for fcg_data in list_of_fcg_data:  # 遍历FCG数据列表
        # 将FCG数据移动到设备上
        fcg_data = fcg_data.to(device)  # 将FCG数据移动到指定设备
        
        # 为每个FCG创建新图数据
        new_x_list = []  # 存储新的节点特征
        
        # 获取FCG中每个节点的函数名
        for node_idx in range(fcg_data.num_nodes):  # 遍历FCG中的每个节点
            # 假设FCG节点已经有函数名属性
            if hasattr(fcg_data, 'function_names'):  # 如果FCG数据有函数名属性
                func_name = fcg_data.function_names[node_idx]  # 获取函数名
            else:  # 如果没有函数名属性
                # 如果没有函数名属性，则使用索引作为函数名
                func_name = str(node_idx)  # 使用节点索引作为函数名
            
            # 获取对应的CFG
            if func_name in cfg_data_dict:  # 如果函数名在CFG数据字典中
                cfg_data = cfg_data_dict[func_name]  # 获取对应的CFG数据
                if cfg_data is not None:  # 如果CFG数据不为None
                    cfg_data = cfg_data.to(device)  # 将CFG数据移动到指定设备
                    
                    # 使用CFG GNN生成图级嵌入
                    with torch.no_grad():  # 不计算梯度
                        try:  # 尝试生成嵌入
                            node_embeddings, cfg_embedding, _ = cfg_gnn_model(cfg_data.x, cfg_data.edge_index, None)  # 使用CFG GNN模型生成嵌入
                            
                            # 如果没有获取到图嵌入，使用节点嵌入的平均值
                            if cfg_embedding is None:  # 如果图嵌入为None
                                if node_embeddings is not None:  # 如果节点嵌入不为None
                                    cfg_embedding = torch.mean(node_embeddings, dim=0)  # 使用节点嵌入的平均值
                                else:  # 如果节点嵌入也为None
                                    cfg_embedding = torch.zeros(cfg_gnn_model.out_channels, device=device)  # 使用零向量
                            
                            # 确保cfg_embedding是1D张量
                            if len(cfg_embedding.shape) > 1:  # 如果维度大于1
                                cfg_embedding = cfg_embedding.squeeze()  # 压缩维度
                        except Exception as e:  # 捕获异常
                            print(f"生成CFG嵌入时出错: {str(e)}")  # 打印错误
                            cfg_embedding = torch.zeros(cfg_gnn_model.out_channels, device=device)  # 使用零向量
                else:  # 如果CFG数据为None
                    print(f"警告: 函数 '{func_name}' 的CFG数据为None")  # 打印警告
                    cfg_embedding = torch.zeros(cfg_gnn_model.out_channels, device=device)  # 使用零向量
            else:  # 如果函数名不在CFG数据字典中
                # 如果没有对应的CFG，则使用零向量
                cfg_embedding = torch.zeros(cfg_gnn_model.out_channels, device=device)  # 使用零向量
            
            # 获取原始FCG节点特征
            orig_feature = fcg_data.x[node_idx]  # 获取原始节点特征
            
            # 确保维度匹配，打印调试信息
            print(f"Debug - orig_feature shape: {orig_feature.shape}, cfg_embedding shape: {cfg_embedding.shape}")  # 打印调试信息
            
            # 将CFG嵌入与原始FCG节点特征拼接
            try:  # 尝试拼接特征
                new_feature = torch.cat([orig_feature, cfg_embedding])  # 拼接原始特征和CFG嵌入
                new_x_list.append(new_feature)  # 添加到新特征列表
            except Exception as e:  # 捕获异常
                print(f"拼接特征时出错: {str(e)}, orig_shape={orig_feature.shape}, cfg_shape={cfg_embedding.shape}")  # 打印错误
                # 如果拼接失败，使用零填充扩展原始特征
                fallback_feature = torch.zeros(orig_feature.shape[0] + cfg_gnn_model.out_channels, device=device)  # 创建零填充特征
                fallback_feature[:orig_feature.shape[0]] = orig_feature  # 复制原始特征
                new_x_list.append(fallback_feature)  # 添加到新特征列表
        
        # 创建新的节点特征矩阵
        new_x = torch.stack(new_x_list)  # 堆叠所有新特征
        
        # 创建增强后的FCG数据
        enriched_data = PyGData(  # 创建新的PyG数据
            x=new_x,  # 新的节点特征
            edge_index=fcg_data.edge_index,  # 原始边索引
            edge_attr=fcg_data.edge_attr if hasattr(fcg_data, 'edge_attr') else None  # 原始边属性（如果有）
        )
        
        # 复制其他属性
        for key in fcg_data.keys():  # 遍历FCG数据的所有属性
            if key not in ['x', 'edge_index', 'edge_attr']:  # 如果不是已经复制的属性
                enriched_data[key] = fcg_data[key]  # 复制属性
        
        enriched_fcg_data.append(enriched_data)  # 添加到增强后的FCG数据列表
    
    return enriched_fcg_data  # 返回增强后的FCG数据列表


def train_gnn_models(list_of_cfg_data, list_of_fcg_data, cfg_gnn_model, fcg_gnn_model, training_config):  # 定义训练GNN模型的主函数
    """
    训练GNN模型的主函数
    
    参数:
        list_of_cfg_data (List): CFG图数据列表
        list_of_fcg_data (List): FCG图数据列表
        cfg_gnn_model: CFG GNN模型
        fcg_gnn_model: FCG GNN模型
        training_config (Dict): 训练配置参数
        
    返回:
        Tuple[torch.nn.Module, torch.nn.Module]: 训练好的CFG GNN和FCG GNN模型
    """
    # 验证输入参数
    if list_of_cfg_data is None or len(list_of_cfg_data) == 0:  # 如果CFG数据列表为空
        raise ValueError("CFG数据列表不能为空")  # 抛出错误
    if list_of_fcg_data is None or len(list_of_fcg_data) == 0:  # 如果FCG数据列表为空
        raise ValueError("FCG数据列表不能为空")  # 抛出错误
    if cfg_gnn_model is None:  # 如果CFG GNN模型为空
        raise ValueError("CFG GNN模型不能为空")  # 抛出错误
    if fcg_gnn_model is None:  # 如果FCG GNN模型为空
        raise ValueError("FCG GNN模型不能为空")  # 抛出错误
    
    # 解析训练配置
    device = torch.device('cuda' if torch.cuda.is_available() and training_config.get('use_gpu', True) else 'cpu')  # 确定训练设备
    batch_size = training_config.get('batch_size', 32)  # 获取批次大小
    cfg_epochs = training_config.get('cfg_epochs', 50)  # 获取CFG训练轮数
    fcg_epochs = training_config.get('fcg_epochs', 50)  # 获取FCG训练轮数
    learning_rate = training_config.get('learning_rate', 0.001)  # 获取学习率
    weight_decay = training_config.get('weight_decay', 5e-4)  # 获取权重衰减
    
    # 设置随机种子以确保可重复性
    seed = training_config.get('seed', 42)  # 获取随机种子
    torch.manual_seed(seed)  # 设置PyTorch随机种子
    np.random.seed(seed)  # 设置NumPy随机种子
    random.seed(seed)  # 设置Python随机种子
    
    print(f"使用设备: {device}")  # 打印使用的设备
    
    # 准备CFG数据加载器
    cfg_loader = DataLoader(list_of_cfg_data, batch_size=batch_size, shuffle=True)  # 创建CFG数据加载器
    
    # 将模型移到设备上
    cfg_gnn_model = cfg_gnn_model.to(device)  # 将CFG GNN模型移动到指定设备
    
    # 定义CFG GNN优化器和损失函数
    cfg_optimizer = optim.Adam(cfg_gnn_model.parameters(), lr=learning_rate, weight_decay=weight_decay)  # 创建Adam优化器
    cfg_criterion = nn.BCELoss()  # 创建二元交叉熵损失函数
    
    print("阶段一：训练CFG GNN模型")  # 打印训练阶段
    # 训练CFG GNN模型
    trained_cfg_gnn, cfg_metrics = train_cfg_gnn(cfg_gnn_model, cfg_loader, cfg_optimizer, cfg_criterion, device, cfg_epochs)  # 训练CFG GNN模型
    
    print("\n阶段二：训练FCG GNN模型")  # 打印训练阶段
    # 准备函数名到CFG数据的映射
    cfg_data_dict = {}  # 创建函数名到CFG数据的映射字典
    for cfg_data in list_of_cfg_data:  # 遍历CFG数据列表
        if hasattr(cfg_data, 'function_name') and cfg_data.function_name:  # 确保function_name存在且非空
            cfg_data_dict[cfg_data.function_name] = cfg_data  # 添加映射
    
    # 添加调试信息
    print(f"已映射 {len(cfg_data_dict)} 个函数名到CFG数据")  # 打印映射数量
    for name in cfg_data_dict:  # 遍历映射字典
        print(f"  - 函数: {name}")  # 打印函数名
    
    # 检查FCG数据中的function_names
    for fcg_idx, fcg_data in enumerate(list_of_fcg_data):  # 遍历FCG数据列表
        if not hasattr(fcg_data, 'function_names'):  # 如果没有function_names属性
            print(f"警告: FCG数据 #{fcg_idx} 没有function_names属性")  # 打印警告
        elif fcg_data.function_names is None:  # 如果function_names为None
            print(f"警告: FCG数据 #{fcg_idx} 的function_names是None")  # 打印警告
        else:  # 如果有function_names
            print(f"FCG数据 #{fcg_idx} 的function_names: {fcg_data.function_names}")  # 打印function_names
    
    # 使用训练好的CFG GNN为FCG节点生成嵌入
    print("使用CFG嵌入增强FCG节点特征")  # 打印处理阶段
    try:  # 尝试增强FCG节点特征
        enriched_fcg_data = enrich_fcg_with_cfg_embeddings(trained_cfg_gnn, list_of_fcg_data, cfg_data_dict, device)  # 使用CFG嵌入增强FCG节点特征
        
        if enriched_fcg_data is None or len(enriched_fcg_data) == 0:  # 如果增强后的FCG数据为空
            print("警告: 增强后的FCG数据为空，无法继续训练")  # 打印警告
            return trained_cfg_gnn, fcg_gnn_model, {'cfg': cfg_metrics, 'fcg': {}}  # 返回训练好的CFG GNN模型和未训练的FCG GNN模型
    except Exception as e:  # 捕获异常
        print(f"增强FCG节点特征时出错: {str(e)}")  # 打印错误
        import traceback  # 导入traceback模块
        traceback.print_exc()  # 打印异常堆栈
        return trained_cfg_gnn, fcg_gnn_model, {'cfg': cfg_metrics, 'fcg': {}}  # 返回训练好的CFG GNN模型和未训练的FCG GNN模型
    
    # 准备FCG数据加载器
    fcg_loader = DataLoader(enriched_fcg_data, batch_size=batch_size, shuffle=True)  # 创建FCG数据加载器
    
    # 将FCG GNN模型移到设备上
    fcg_gnn_model = fcg_gnn_model.to(device)  # 将FCG GNN模型移动到指定设备
    
    # 定义FCG GNN优化器和损失函数
    fcg_optimizer = optim.Adam(fcg_gnn_model.parameters(), lr=learning_rate, weight_decay=weight_decay)  # 创建Adam优化器
    fcg_criterion = nn.BCELoss()  # 创建二元交叉熵损失函数
    
    # 训练FCG GNN模型
    try:  # 尝试训练FCG GNN模型
        trained_fcg_gnn, fcg_metrics = train_fcg_gnn(fcg_gnn_model, fcg_loader, fcg_optimizer, fcg_criterion, device, fcg_epochs)  # 训练FCG GNN模型
    except Exception as e:  # 捕获异常
        print(f"训练FCG GNN模型时出错: {str(e)}")  # 打印错误
        import traceback  # 导入traceback模块
        traceback.print_exc()  # 打印异常堆栈
        return trained_cfg_gnn, fcg_gnn_model, {'cfg': cfg_metrics, 'fcg': {}}  # 返回训练好的CFG GNN模型和未训练的FCG GNN模型
    
    # 返回训练好的模型和训练指标
    return trained_cfg_gnn, trained_fcg_gnn, {'cfg': cfg_metrics, 'fcg': fcg_metrics}  # 返回训练好的CFG GNN和FCG GNN模型以及训练指标


if __name__ == "__main__":  # 如果作为主程序运行
    # 简单的测试代码
    print("gnn_trainer.py - 图神经网络训练工具")  # 打印工具名称
    
    # 检查PyTorch Geometric是否可用
    if not HAS_TORCH_GEOMETRIC:  # 如果PyTorch Geometric不可用
        print("警告: PyTorch Geometric未安装，无法运行测试")  # 打印警告
        exit(0)  # 退出程序
    
    # 创建一些测试数据
    try:  # 尝试创建测试数据
        from torch_geometric.data import Data  # 导入PyG的Data类
        
        # 创建简单的CFG图数据
        cfg_data1 = Data(  # 创建第一个CFG数据
            x=torch.randn(5, 16),  # 随机生成5个节点，每个节点16维特征
            edge_index=torch.tensor([[0, 1, 1, 2, 2, 3, 4], [1, 2, 3, 3, 4, 4, 0]], dtype=torch.long),  # 边索引
            function_name="func1"  # 函数名
        )
        
        cfg_data2 = Data(  # 创建第二个CFG数据
            x=torch.randn(4, 16),  # 随机生成4个节点，每个节点16维特征
            edge_index=torch.tensor([[0, 0, 1, 2], [1, 2, 3, 3]], dtype=torch.long),  # 边索引
            function_name="func2"  # 函数名
        )
        
        # 创建简单的FCG图数据
        fcg_data = Data(  # 创建FCG数据
            x=torch.randn(2, 16),  # 随机生成2个节点，每个节点16维特征
            edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long)  # 边索引
        )
        # 确保function_names是列表，而不是其他类型
        fcg_data.function_names = ["func1", "func2"]  # 设置函数名列表
        
        # 创建CFG GNN和FCG GNN模型
        cfg_gnn = CFGGNN(in_channels=16, hidden_channels=32, out_channels=64, num_layers=2)  # 创建CFG GNN模型
        fcg_gnn = FCGGNN(in_channels=16+64, hidden_channels=32, out_channels=64, num_layers=2)  # 创建FCG GNN模型
        
        # 创建训练配置
        training_config = {  # 训练配置字典
            'batch_size': 1,  # 批次大小
            'cfg_epochs': 3,  # CFG训练轮数
            'fcg_epochs': 3,  # FCG训练轮数
            'learning_rate': 0.001,  # 学习率
            'use_gpu': False  # 是否使用GPU
        }
        
        print("\n测试训练过程...")  # 打印测试信息
        # 训练模型（限制训练轮数，仅用于测试）
        try:  # 尝试训练模型
            print("准备训练数据...")  # 打印准备信息
            print(f"CFG数据: {len([cfg_data1, cfg_data2])}个, FCG数据: {len([fcg_data])}个")  # 打印数据数量
            print(f"CFG1 shape: x={cfg_data1.x.shape}, edge_index={cfg_data1.edge_index.shape}")  # 打印CFG1形状
            print(f"CFG2 shape: x={cfg_data2.x.shape}, edge_index={cfg_data2.edge_index.shape}")  # 打印CFG2形状
            print(f"FCG shape: x={fcg_data.x.shape}, edge_index={fcg_data.edge_index.shape}")  # 打印FCG形状
            print(f"FCG function_names: {fcg_data.function_names}")  # 打印FCG函数名
            
            trained_cfg_gnn, trained_fcg_gnn, metrics = train_gnn_models(  # 训练GNN模型
                [cfg_data1, cfg_data2], [fcg_data], cfg_gnn, fcg_gnn, training_config  # 传入数据和配置
            )
            
            print("\n训练完成！")  # 打印完成信息
        except Exception as e:  # 捕获异常
            print(f"训练过程中出错: {str(e)}")  # 打印错误
            import traceback  # 导入traceback模块
            traceback.print_exc()  # 打印异常堆栈
        
    except Exception as e:  # 捕获异常
        print(f"测试时出错: {str(e)}")  # 打印错误