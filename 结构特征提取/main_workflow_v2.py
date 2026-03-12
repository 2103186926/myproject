#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化的主工作流程 - 两阶段GNN训练提取程序级图嵌入
阶段1: CFG-GNN训练，获取函数级图嵌入
阶段2: FCG-GNN训练，获取程序级图嵌入
最终输出: 每个Python源文件对应一个numpy向量文件
"""

import os
import sys
import time
import argparse
import torch
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path
import json
import logging
from tqdm import tqdm
import pandas as pd
from sklearn.model_selection import train_test_split
import pickle

# 导入配置和新模块
from config import Config, get_default_config
from ast_parser import parse_code_to_ast
from feature_extractor_v2 import FeatureExtractor, get_feature_extractor
from graph_builder_v2 import GraphBuilderV2, build_program_graphs_v2
from gnn_trainer_v2 import CFGGNN_V2, FCGGNN_V2, GNNTrainer
from torch_geometric.data import Data, DataLoader


# 注释掉调试器代码，生产环境不需要
import debugpy
try:
    debugpy.listen(("localhost", 9502))
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
except Exception as e:
    pass

def setup_logger(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger("main_workflow_v2")
    logger.setLevel(level)
    logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="两阶段GNN训练提取程序级图嵌入")
    
    # 数据路径
    parser.add_argument("--source_dir", type=str, required=True,
                       help="Python源代码目录")
    parser.add_argument("--output_dir", type=str, default="./output",
                       help="输出目录")
    parser.add_argument("--embedding_dir", type=str, default=None,
                       help="图嵌入保存目录（默认为output_dir/embeddings）")
    parser.add_argument("--log_file", type=str, default=None,
                       help="日志文件路径")
    
    # 配置文件
    parser.add_argument("--config", type=str, default=None,
                       help="配置文件路径(JSON格式)")
    
    # 图缓存参数（新增）
    parser.add_argument("--save_graphs", type=str, default=None,
                       help="保存解析的CFG/FCG图到指定文件（pickle格式）")
    parser.add_argument("--load_graphs", type=str, default=None,
                       help="从指定文件加载已保存的CFG/FCG图（pickle格式）")
    
    # 训练控制
    parser.add_argument("--skip_training", action="store_true",
                       help="跳过训练，直接提取嵌入（需要提供预训练模型）")
    parser.add_argument("--cfg_model_path", type=str, default=None,
                       help="预训练的CFG模型路径")
    parser.add_argument("--fcg_model_path", type=str, default=None,
                       help="预训练的FCG模型路径")
    parser.add_argument("--save_best_model", action="store_true",
                       help="保存最佳FCG模型")
    
    # 评估模式
    parser.add_argument("--mode", type=str, default="train",
                       choices=["train", "evaluate", "train_classifier"],
                       help="运行模式: train(训练GNN), evaluate(评估分类器), train_classifier(训练分类器)")
    parser.add_argument("--label_file", type=str, default=None,
                       help="标签文件路径(CSV格式，包含file_path和label列)")
    parser.add_argument("--classifier_model_path", type=str, default=None,
                       help="分类器模型路径（用于评估模式）")
    
    # 系统参数
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子")
    parser.add_argument("--debug", action="store_true",
                       help="调试模式")
    
    return parser.parse_args()


def collect_python_files(source_dir: str, logger: logging.Logger) -> List[str]:
    """收集Python文件"""
    logger.info(f"从 {source_dir} 收集Python文件...")
    
    python_files = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                python_files.append(file_path)
    
    logger.info(f"找到 {len(python_files)} 个Python文件")
    return python_files


def parse_and_build_graphs(python_files: List[str], 
                          config: Config,
                          logger: logging.Logger) -> Tuple[Dict, Dict]:
    """解析文件并构建图"""
    logger.info("=" * 80)
    logger.info("步骤1: 解析Python文件并构建CFG/FCG图")
    logger.info("=" * 80)
    
    all_cfgs = {}
    all_fcgs = {}
    
    for file_path in tqdm(python_files, desc="处理文件"):
        try:
            # 读取源代码
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 解析AST
            ast_tree = parse_code_to_ast(file_path)
            if ast_tree is None:
                logger.warning(f"文件 {file_path} 解析失败")
                continue
            
            # 构建图
            cfgs, fcg = build_program_graphs_v2(ast_tree, source_code, config)
            
            # 过滤CFG
            filtered_cfgs = {
                name: cfg for name, cfg in cfgs.items()
                if config.data.min_nodes <= cfg.number_of_nodes() <= config.data.max_nodes
            }
            
            if filtered_cfgs:
                all_cfgs[file_path] = filtered_cfgs
                all_fcgs[file_path] = fcg
                logger.debug(f"文件 {file_path}: {len(filtered_cfgs)} 个CFG")
        
        except Exception as e:
            logger.error(f"处理文件 {file_path} 失败: {e}")
    
    logger.info(f"成功处理 {len(all_cfgs)} 个文件")
    logger.info(f"  总CFG数: {sum(len(cfgs) for cfgs in all_cfgs.values())}")
    logger.info(f"  总FCG数: {len(all_fcgs)}")
    
    return all_cfgs, all_fcgs


def save_graphs_to_file(all_cfgs: Dict, all_fcgs: Dict, 
                        save_path: str, logger: logging.Logger):
    """
    保存CFG和FCG图到文件
    
    参数:
        all_cfgs: CFG字典
        all_fcgs: FCG字典
        save_path: 保存路径
        logger: 日志记录器
    """
    logger.info("=" * 80)
    logger.info("保存图数据到磁盘")
    logger.info("=" * 80)
    
    try:
        # 创建保存目录
        os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
        
        # 准备保存的数据
        graph_data = {
            'all_cfgs': all_cfgs,
            'all_fcgs': all_fcgs,
            'metadata': {
                'num_files': len(all_cfgs),
                'num_cfgs': sum(len(cfgs) for cfgs in all_cfgs.values()),
                'num_fcgs': len(all_fcgs),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # 使用pickle保存
        with open(save_path, 'wb') as f:
            pickle.dump(graph_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        # 获取文件大小
        file_size = os.path.getsize(save_path) / (1024 * 1024)  # MB
        
        logger.info(f"图数据已保存到: {save_path}")
        logger.info(f"  文件大小: {file_size:.2f} MB")
        logger.info(f"  包含文件: {graph_data['metadata']['num_files']}")
        logger.info(f"  CFG数量: {graph_data['metadata']['num_cfgs']}")
        logger.info(f"  FCG数量: {graph_data['metadata']['num_fcgs']}")
        
        return True
    
    except Exception as e:
        logger.error(f"保存图数据失败: {e}")
        return False


def load_graphs_from_file(load_path: str, logger: logging.Logger) -> Tuple[Dict, Dict]:
    """
    从文件加载CFG和FCG图
    
    参数:
        load_path: 加载路径
        logger: 日志记录器
        
    返回:
        (all_cfgs, all_fcgs)
    """
    logger.info("=" * 80)
    logger.info("从磁盘加载图数据")
    logger.info("=" * 80)
    
    try:
        if not os.path.exists(load_path):
            logger.error(f"图数据文件不存在: {load_path}")
            return None, None
        
        # 获取文件大小
        file_size = os.path.getsize(load_path) / (1024 * 1024)  # MB
        logger.info(f"正在加载: {load_path} ({file_size:.2f} MB)")
        
        # 使用pickle加载
        with open(load_path, 'rb') as f:
            graph_data = pickle.load(f)
        
        all_cfgs = graph_data['all_cfgs']
        all_fcgs = graph_data['all_fcgs']
        metadata = graph_data.get('metadata', {})
        
        logger.info(f"图数据加载成功!")
        logger.info(f"  保存时间: {metadata.get('timestamp', '未知')}")
        logger.info(f"  包含文件: {metadata.get('num_files', len(all_cfgs))}")
        logger.info(f"  CFG数量: {metadata.get('num_cfgs', sum(len(cfgs) for cfgs in all_cfgs.values()))}")
        logger.info(f"  FCG数量: {metadata.get('num_fcgs', len(all_fcgs))}")
        
        return all_cfgs, all_fcgs
    
    except Exception as e:
        logger.error(f"加载图数据失败: {e}")
        return None, None


def convert_to_pyg_data(all_cfgs: Dict, all_fcgs: Dict,
                       config: Config,
                       logger: logging.Logger) -> Tuple[List[Data], List[Data], Dict]:
    """
    转换为PyG数据格式
    
    返回:
        cfg_data_list: CFG数据列表
        fcg_data_list: FCG数据列表（节点特征暂时为零向量）
        file_to_cfg_data: 文件路径到CFG数据的映射（用于后续嵌入注入）
    """
    logger.info("=" * 80)
    logger.info("步骤2: 转换为PyTorch Geometric数据格式")
    logger.info("=" * 80)
    
    cfg_data_list = []
    fcg_data_list = []
    file_to_cfg_data = {}  # {file_path: {func_name: cfg_data}}
    
    for file_path, cfgs in tqdm(all_cfgs.items(), desc="转换图数据"):
        try:
            file_to_cfg_data[file_path] = {}
            
            # 转换CFG
            for func_name, cfg in cfgs.items():
                if cfg.number_of_nodes() == 0:
                    continue
                
                # 提取节点特征
                node_features = []
                for node_id in cfg.nodes():
                    node_data = cfg.nodes[node_id]
                    if 'feature_vector' in node_data:
                        node_features.append(node_data['feature_vector'])
                    else:
                        node_features.append(np.zeros(config.model.node_feature_dim))
                
                if not node_features:
                    continue
                
                # 构建边索引
                edge_index = []
                for u, v in cfg.edges():
                    node_list = list(cfg.nodes())
                    u_idx = node_list.index(u)
                    v_idx = node_list.index(v)
                    edge_index.append([u_idx, v_idx])
                
                if not edge_index:
                    edge_index = [[0, 0]]  # 自环
                
                # 创建PyG Data对象
                x = torch.tensor(np.array(node_features), dtype=torch.float)
                edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
                
                data = Data(x=x, edge_index=edge_index)
                data.file_path = file_path
                data.function_name = func_name
                
                cfg_data_list.append(data)
                file_to_cfg_data[file_path][func_name] = data
            
            # 转换FCG（节点特征暂时为零向量，后续会注入CFG嵌入）
            if file_path in all_fcgs:
                fcg = all_fcgs[file_path]
                if fcg.number_of_nodes() > 0:
                    # 初始化节点特征（原始特征维度）
                    node_features = []
                    func_names = list(fcg.nodes())
                    
                    for node_id in func_names:
                        # 使用零向量作为初始特征
                        feature = np.zeros(config.model.node_feature_dim)
                        node_features.append(feature)
                    
                    # 构建边索引
                    edge_index = []
                    for u, v in fcg.edges():
                        u_idx = func_names.index(u)
                        v_idx = func_names.index(v)
                        edge_index.append([u_idx, v_idx])
                    
                    if not edge_index:
                        edge_index = [[0, 0]]
                    
                    x = torch.tensor(np.array(node_features), dtype=torch.float)
                    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
                    
                    data = Data(x=x, edge_index=edge_index)
                    data.file_path = file_path
                    data.function_names = func_names
                    
                    fcg_data_list.append(data)
        
        except Exception as e:
            logger.error(f"转换文件 {file_path} 失败: {e}")
    
    logger.info(f"转换完成:")
    logger.info(f"  CFG数据: {len(cfg_data_list)}")
    logger.info(f"  FCG数据: {len(fcg_data_list)}")
    
    return cfg_data_list, fcg_data_list, file_to_cfg_data


def split_dataset(cfg_data_list: List[Data],
                 fcg_data_list: List[Data],
                 train_ratio: float,
                 val_ratio: float,
                 seed: int,
                 logger: logging.Logger) -> Tuple[List[Data], List[Data], List[Data], 
                                                  List[Data], List[Data], List[Data]]:
    """
    按文件划分数据集（避免数据泄漏）
    
    返回:
        cfg_train, cfg_val, cfg_test, fcg_train, fcg_val, fcg_test
    """
    np.random.seed(seed)
    
    # 按文件组织数据
    file_to_cfg = {}
    file_to_fcg = {}
    
    for data in cfg_data_list:
        file_path = data.file_path
        if file_path not in file_to_cfg:
            file_to_cfg[file_path] = []
        file_to_cfg[file_path].append(data)
    
    for data in fcg_data_list:
        file_path = data.file_path
        file_to_fcg[file_path] = data
    
    # 获取所有文件
    all_files = list(set(list(file_to_cfg.keys()) + list(file_to_fcg.keys())))
    np.random.shuffle(all_files)
    
    # 划分
    n = len(all_files)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    
    train_files = all_files[:train_end]
    val_files = all_files[train_end:val_end]
    test_files = all_files[val_end:]
    
    logger.info(f"\n数据集划分:")
    logger.info(f"  训练文件: {len(train_files)}")
    logger.info(f"  验证文件: {len(val_files)}")
    logger.info(f"  测试文件: {len(test_files)}")
    
    # 提取对应数据
    cfg_train = []
    cfg_val = []
    cfg_test = []
    fcg_train = []
    fcg_val = []
    fcg_test = []
    
    for file_path in train_files:
        if file_path in file_to_cfg:
            cfg_train.extend(file_to_cfg[file_path])
        if file_path in file_to_fcg:
            fcg_train.append(file_to_fcg[file_path])
    
    for file_path in val_files:
        if file_path in file_to_cfg:
            cfg_val.extend(file_to_cfg[file_path])
        if file_path in file_to_fcg:
            fcg_val.append(file_to_fcg[file_path])
    
    for file_path in test_files:
        if file_path in file_to_cfg:
            cfg_test.extend(file_to_cfg[file_path])
        if file_path in file_to_fcg:
            fcg_test.append(file_to_fcg[file_path])
    
    logger.info(f"CFG数据: 训练{len(cfg_train)}, 验证{len(cfg_val)}, 测试{len(cfg_test)}")
    logger.info(f"FCG数据: 训练{len(fcg_train)}, 验证{len(fcg_val)}, 测试{len(fcg_test)}")
    
    return cfg_train, cfg_val, cfg_test, fcg_train, fcg_val, fcg_test


def train_cfg_model(cfg_train_data: List[Data],
                   cfg_val_data: List[Data],
                   config: Config,
                   output_dir: str,
                   save_best_model: bool,
                   logger: logging.Logger) -> CFGGNN_V2:
    """阶段1: 训练CFG-GNN模型"""
    logger.info("=" * 80)
    logger.info("阶段1: 训练CFG-GNN模型（函数级特征提取）")
    logger.info("=" * 80)
    
    # 创建数据加载器
    cfg_train_loader = DataLoader(cfg_train_data, 
                                  batch_size=config.training.batch_size,
                                  shuffle=True)
    cfg_val_loader = DataLoader(cfg_val_data,
                               batch_size=config.training.batch_size)
    
    # 创建模型
    cfg_model = CFGGNN_V2(config)
    logger.info(f"CFG模型参数量: {sum(p.numel() for p in cfg_model.parameters()):,}")
    
    # 训练
    trainer = GNNTrainer(config)
    
    model_save_path = None
    if save_best_model:
        model_save_path = os.path.join(output_dir, 'best_cfg_model.pth')
    
    cfg_model, cfg_history = trainer.train_cfg_gnn(
        cfg_model, 
        cfg_train_loader, 
        cfg_val_loader,
        save_best_model=save_best_model,
        model_save_path=model_save_path
    )  # 训练cfg_gnn模型
    
    logger.info("[阶段1完成] CFG-GNN训练完成")
    
    return cfg_model


def extract_cfg_embeddings(cfg_model: CFGGNN_V2,
                          all_cfg_data: List[Data],
                          config: Config,
                          logger: logging.Logger) -> Dict[Tuple[str, str], np.ndarray]:
    """
    提取所有CFG的图嵌入
    使用与训练时相同的批量处理和池化方式
    
    返回:
        {(file_path, func_name): embedding} 字典
    """
    logger.info("\n提取CFG图嵌入...")
    
    cfg_model.eval()
    device = torch.device(
        f'cuda:{config.training.gpu_id}' 
        if config.training.use_gpu and torch.cuda.is_available() 
        else 'cpu'
    )
    cfg_model = cfg_model.to(device)
    
    # 使用DataLoader进行批量处理，确保与训练时一致
    cfg_loader = DataLoader(all_cfg_data, batch_size=config.training.batch_size, shuffle=False)
    
    cfg_embeddings = {}
    data_idx = 0  # 追踪当前处理到的数据索引
    
    with torch.no_grad():
        for batch in tqdm(cfg_loader, desc="提取CFG嵌入"):
            batch = batch.to(device)
            
            # 使用与训练时相同的前向传播（包括批量处理和池化）
            _, graph_emb = cfg_model(batch.x, batch.edge_index, batch.batch)
            
            # 将批量嵌入分配到各个图
            embeddings = graph_emb.cpu().numpy()
            
            # 获取批次中每个图的信息
            batch_size = batch.num_graphs
            for i in range(batch_size):
                # 从原始数据列表中获取对应的元数据
                original_data = all_cfg_data[data_idx]
                file_path = original_data.file_path
                function_name = original_data.function_name
                
                embedding = embeddings[i]
                key = (file_path, function_name)
                cfg_embeddings[key] = embedding
                
                data_idx += 1  # 移动到下一个数据
    
    logger.info(f"成功提取 {len(cfg_embeddings)} 个CFG图嵌入")
    
    return cfg_embeddings


def inject_cfg_embeddings_to_fcg(fcg_data_list: List[Data],
                                 cfg_embeddings: Dict[Tuple[str, str], np.ndarray],
                                 config: Config,
                                 logger: logging.Logger):
    """
    将CFG嵌入注入到FCG节点特征中
    
    修改fcg_data_list中的数据（原地修改）
    注意：由于FCG原始节点特征是0填充的，这里只使用CFG嵌入作为FCG节点特征
    """
    logger.info("=" * 80)
    logger.info("注入CFG嵌入到FCG节点特征")
    logger.info("=" * 80)
    
    cfg_emb_dim = config.model.cfg_out_channels
    
    for fcg_data in tqdm(fcg_data_list, desc="注入CFG嵌入"):
        file_path = fcg_data.file_path
        func_names = fcg_data.function_names
        
        # 为每个函数节点注入CFG嵌入（仅使用CFG嵌入，不使用原始0填充特征）
        enhanced_features = []
        
        for func_name in func_names:
            # 获取对应的CFG嵌入
            key = (file_path, func_name)
            if key in cfg_embeddings:
                cfg_emb = cfg_embeddings[key]
            else:
                # 如果没有对应的CFG嵌入，使用零向量
                cfg_emb = np.zeros(cfg_emb_dim)
            
            # 只使用CFG嵌入作为FCG节点特征（去掉0填充的原始特征）
            enhanced_features.append(cfg_emb)
        
        # 更新FCG节点特征
        fcg_data.x = torch.tensor(np.array(enhanced_features), dtype=torch.float)
    
    logger.info(f"FCG节点特征维度: {fcg_data_list[0].x.shape[1]}")
    logger.info(f"  使用CFG嵌入作为FCG节点特征: {cfg_emb_dim}维")


def train_fcg_model(fcg_train_data: List[Data],
                   fcg_val_data: List[Data],
                   config: Config,
                   output_dir: str,
                   save_best_model: bool,
                   logger: logging.Logger) -> FCGGNN_V2:
    """阶段2: 训练FCG-GNN模型"""
    logger.info("=" * 80)
    logger.info("阶段2: 训练FCG-GNN模型（程序级特征提取）")
    logger.info("=" * 80)
    
    # 创建数据加载器
    fcg_train_loader = DataLoader(fcg_train_data,
                                  batch_size=config.training.batch_size,
                                  shuffle=True)
    fcg_val_loader = DataLoader(fcg_val_data,
                               batch_size=config.training.batch_size)
    
    # 创建模型
    fcg_model = FCGGNN_V2(config)
    logger.info(f"FCG模型参数量: {sum(p.numel() for p in fcg_model.parameters()):,}")
    
    # 训练
    trainer = GNNTrainer(config)
    
    model_save_path = None
    if save_best_model:
        model_save_path = os.path.join(output_dir, 'best_fcg_model.pth')
    
    fcg_model, fcg_history = trainer.train_fcg_gnn(
        fcg_model, 
        fcg_train_loader, 
        fcg_val_loader,
        save_best_model=save_best_model,
        model_save_path=model_save_path
    )  # 训练fcg_gnn模型过程
    
    logger.info("[阶段2完成] FCG-GNN训练完成")
    
    return fcg_model


def extract_and_save_program_embeddings(fcg_model: FCGGNN_V2,
                                       all_fcg_data: List[Data],
                                       embedding_dir: str,
                                       config: Config,
                                       logger: logging.Logger):
    """提取并保存程序级图嵌入"""
    logger.info("=" * 80)
    logger.info("提取并保存程序级图嵌入")
    logger.info("=" * 80)
    
    trainer = GNNTrainer(config)
    embeddings_dict = trainer.extract_program_embeddings(
        fcg_model,
        all_fcg_data,
        embedding_dir
    )  # 提取程序级图嵌入
    
    # 保存嵌入索引 Json文件
    index_file = os.path.join(embedding_dir, 'embedding_index.json')
    index_data = {
        file_path: {
            'npy_file': f"{os.path.splitext(os.path.basename(file_path))[0]}.npy",
            'shape': list(emb.shape)
        }
        for file_path, emb in embeddings_dict.items()
    }
    
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"嵌入索引已保存: {index_file}")


def save_training_info(cfg_model: CFGGNN_V2,
                      fcg_model: FCGGNN_V2,
                      config: Config,
                      output_dir: str,
                      logger: logging.Logger):
    """保存训练信息"""
    logger.info("=" * 80)
    logger.info("保存训练信息")
    logger.info("=" * 80)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存CFG模型
    cfg_model_path = os.path.join(output_dir, 'cfg_model.pth')
    torch.save(cfg_model.state_dict(), cfg_model_path)
    logger.info(f"CFG模型已保存: {cfg_model_path}")
    
    # 保存FCG模型（最终模型）
    fcg_model_path = os.path.join(output_dir, 'fcg_model_final.pth')
    torch.save(fcg_model.state_dict(), fcg_model_path)
    logger.info(f"FCG模型已保存: {fcg_model_path}")
    
    # 保存配置
    config_path = os.path.join(output_dir, 'config.json')
    config.to_json(config_path)
    logger.info(f"配置已保存: {config_path}")


def main():
    """主函数"""
    args = parse_args()
    
    # 设置日志
    log_file = args.log_file or os.path.join(args.output_dir, 'training.log')
    logger = setup_logger(log_file, logging.DEBUG if args.debug else logging.INFO)
    
    logger.info("=" * 80)
    logger.info("两阶段GNN训练 - 提取程序级图嵌入")
    logger.info("=" * 80)
    
    # 加载配置
    if args.config:
        config = Config.from_json(args.config)
        logger.info(f"从文件加载配置: {args.config}")
    else:
        config = get_default_config()
        logger.info("使用默认配置")
    
    # 更新配置
    config.data.source_dir = args.source_dir
    config.data.output_dir = args.output_dir
    config.training.seed = args.seed
    
    # 验证配置
    try:
        config.validate()
        logger.info("配置验证通过")
    except Exception as e:
        logger.error(f"配置验证失败: {e}")
        return
    
    # 设置随机种子
    np.random.seed(config.training.seed)
    torch.manual_seed(config.training.seed)
    
    # 设置嵌入输出目录
    embedding_dir = args.embedding_dir or os.path.join(args.output_dir, 'embeddings')
    os.makedirs(embedding_dir, exist_ok=True)
    
    # 收集文件
    python_files = collect_python_files(args.source_dir, logger)
    if not python_files:
        logger.error("没有找到Python文件")
        return
    
    # 解析和构建图（支持缓存）
    if args.load_graphs:
        # 从缓存加载图
        all_cfgs, all_fcgs = load_graphs_from_file(args.load_graphs, logger)
        if all_cfgs is None or all_fcgs is None:
            logger.error("加载图数据失败，退出")
            return
    else:
        # 重新解析和构建图
        all_cfgs, all_fcgs = parse_and_build_graphs(python_files, config, logger)
        
        # 如果指定了保存路径，保存图数据
        if args.save_graphs:
            save_graphs_to_file(all_cfgs, all_fcgs, args.save_graphs, logger)
    
    # 转换为PyG格式
    cfg_data_list, fcg_data_list, file_to_cfg_data = convert_to_pyg_data(
        all_cfgs, all_fcgs, config, logger
    )
    
    if not cfg_data_list or not fcg_data_list:
        logger.error("没有有效的数据")
        return
    
    # 划分数据集
    logger.info("\n" + "=" * 80)
    logger.info("划分数据集")
    logger.info("=" * 80)
    
    cfg_train, cfg_val, cfg_test, fcg_train, fcg_val, fcg_test = split_dataset(
        cfg_data_list,
        fcg_data_list,
        config.training.train_ratio,
        config.training.val_ratio,
        config.training.seed,
        logger
    )
    
    # 阶段1: 训练CFG模型
    if not args.skip_training:
        cfg_model = train_cfg_model(
            cfg_train, 
            cfg_val, 
            config, 
            args.output_dir,
            args.save_best_model,
            logger
        )
    else:
        if not args.cfg_model_path:
            logger.error("跳过训练模式需要提供CFG模型路径")
            return
        logger.info(f"加载预训练CFG模型: {args.cfg_model_path}")
        cfg_model = CFGGNN_V2(config)
        cfg_model.load_state_dict(torch.load(args.cfg_model_path))
    
    # 提取所有CFG嵌入
    cfg_embeddings = extract_cfg_embeddings(cfg_model, cfg_data_list, config, logger)
    
    # 注入CFG嵌入到FCG
    inject_cfg_embeddings_to_fcg(fcg_data_list, cfg_embeddings, config, logger)
    
    # 重新划分FCG数据（因为特征已更新） #! 重新划分FCG数据的代码是冗余
    fcg_train_enhanced = [d for d in fcg_data_list if d in fcg_train]
    fcg_val_enhanced = [d for d in fcg_data_list if d in fcg_val]
    fcg_test_enhanced = [d for d in fcg_data_list if d in fcg_test]
    
    # 阶段2: 训练FCG模型
    if not args.skip_training:
        fcg_model = train_fcg_model(
            fcg_train_enhanced, 
            fcg_val_enhanced, 
            config, 
            args.output_dir,
            args.save_best_model,
            logger
        )
    else:
        if not args.fcg_model_path:
            logger.error("跳过训练模式需要提供FCG模型路径")
            return
        logger.info(f"加载预训练FCG模型: {args.fcg_model_path}")
        fcg_model = FCGGNN_V2(config)
        fcg_model.load_state_dict(torch.load(args.fcg_model_path))
    
    # 提取并保存程序级图嵌入
    extract_and_save_program_embeddings(
        fcg_model,
        fcg_data_list,  # 使用所有数据
        embedding_dir,
        config,
        logger
    )
    
    # 保存训练信息
    if not args.skip_training:
        save_training_info(cfg_model, fcg_model, config, args.output_dir, logger)
    
    # 分类器训练和评估
    if args.mode in ["train_classifier", "evaluate"] and args.label_file:
        logger.info("\n" + "=" * 80)
        logger.info("加载分类标签")
        logger.info("=" * 80)
        
        # 加载标签
        label_df = pd.read_csv(args.label_file)
        
        # 标准化文件路径
        label_dict = {}
        source_dir_normalized = os.path.normpath(args.source_dir)
        
        for _, row in label_df.iterrows():
            file_path = os.path.normpath(row['file_path'])
            
            # 如果是相对路径，需要判断是否已经包含 source_dir
            if not os.path.isabs(file_path):
                # 检查路径是否已经以 source_dir 开头
                # 例如：file_path = 'test_cases_v3\normal\xxx.py', source_dir = '.\test_cases_v3'
                source_dir_basename = os.path.basename(source_dir_normalized)
                path_parts = file_path.split(os.sep)
                
                # 如果路径的第一部分与 source_dir 的最后一部分相同，说明已经包含了目录名
                if path_parts[0] == source_dir_basename:
                    # 路径已经是完整的相对路径，直接使用
                    file_path = os.path.normpath(file_path)
                else:
                    # 路径是相对于 source_dir 内部的，需要拼接
                    file_path = os.path.normpath(os.path.join(args.source_dir, file_path))
            
            label_dict[file_path] = int(row['label'])
        
        logger.info(f"加载了 {len(label_dict)} 个标签")
        logger.info(f"  正常样本: {sum(1 for v in label_dict.values() if v == 0)}")
        logger.info(f"  恶意样本: {sum(1 for v in label_dict.values() if v == 1)}")
        
        # 为FCG数据添加标签
        labeled_fcg_data = []
        for data in fcg_data_list:
            file_path = os.path.normpath(data.file_path)
            if file_path in label_dict:
                data.y = torch.tensor([label_dict[file_path]], dtype=torch.long)
                labeled_fcg_data.append(data)
            else:
                logger.warning(f"文件 {file_path} 没有标签")
        
        logger.info(f"成功标注 {len(labeled_fcg_data)} 个FCG数据")
        
        if not labeled_fcg_data:
            logger.error("没有标注的数据，无法进行分类训练/评估")
        else:
            # 划分数据集
            train_val_data, test_data = train_test_split(
                labeled_fcg_data,
                test_size=1 - config.training.train_ratio - config.training.val_ratio,
                random_state=config.training.seed,
                stratify=[d.y.item() for d in labeled_fcg_data]
            )
            
            train_data, val_data = train_test_split(
                train_val_data,
                test_size=config.training.val_ratio / (config.training.train_ratio + config.training.val_ratio),
                random_state=config.training.seed,
                stratify=[d.y.item() for d in train_val_data]
            )
            
            logger.info(f"\n分类数据集划分:")
            logger.info(f"  训练集: {len(train_data)}")
            logger.info(f"  验证集: {len(val_data)}")
            logger.info(f"  测试集: {len(test_data)}")
            
            # 创建分类器
            from gnn_trainer_v2 import FCGClassifier
            classifier = FCGClassifier(config)
            
            if args.mode == "train_classifier":
                # 加载预训练的FCG权重
                if args.fcg_model_path:
                    classifier.load_fcg_weights(args.fcg_model_path)
                elif not args.skip_training:
                    # 使用刚训练的FCG模型
                    classifier.fcg_gnn.load_state_dict(fcg_model.state_dict())
                    logger.info("使用刚训练的FCG-GNN权重")
                
                # 训练分类器
                logger.info("\n" + "=" * 80)
                logger.info("训练FCG分类器")
                logger.info("=" * 80)
                
                train_loader = DataLoader(train_data, batch_size=config.training.batch_size, shuffle=True)
                val_loader = DataLoader(val_data, batch_size=config.training.batch_size)
                
                trainer = GNNTrainer(config)
                classifier_save_path = os.path.join(args.output_dir, 'best_classifier.pth')
                classifier, history = trainer.train_classifier(
                    classifier,
                    train_loader,
                    val_loader,
                    save_best_model=True,
                    model_save_path=classifier_save_path
                )  #! 训练FCG分类器过程
                
                # 评估
                test_loader = DataLoader(test_data, batch_size=config.training.batch_size)
                metrics = trainer.evaluate_classifier(classifier, test_loader, args.output_dir)  #! 评估FCG分类器过程
            
            elif args.mode == "evaluate":
                # 评估模式
                if not args.classifier_model_path:
                    logger.error("评估模式需要提供分类器模型路径 (--classifier_model_path)")
                else:
                    logger.info(f"加载分类器模型: {args.classifier_model_path}")
                    classifier.load_state_dict(torch.load(args.classifier_model_path))
                    
                    test_loader = DataLoader(test_data, batch_size=config.training.batch_size)
                    trainer = GNNTrainer(config)
                    metrics = trainer.evaluate_classifier(classifier, test_loader, args.output_dir)
    
    logger.info("\n" + "=" * 80)
    logger.info("完成！")
    logger.info("=" * 80)
    logger.info(f"程序级图嵌入保存在: {embedding_dir}")
    logger.info(f"训练信息保存在: {args.output_dir}")


if __name__ == "__main__":
    main()
