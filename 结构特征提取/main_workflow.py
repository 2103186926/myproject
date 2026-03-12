#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import torch
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
import json
import logging
import multiprocessing
from collections import defaultdict
import ast


# 导入自定义模块
from dataset_loader import load_code_paths
from ast_parser import parse_code_to_ast, parse_code_string_to_ast
import feature_extractor
from graph_builder import build_program_graphs
from graph_converter import convert_to_pyg_data as networkx_to_pyg_cfg
from graph_converter import convert_to_pyg_data as networkx_to_pyg_fcg
from graph_sequentializer import networkx_to_sequences, sequence_to_features
from gnn_trainer import CFGGNN, FCGGNN, train_cfg_gnn as train_cfggnn, train_fcg_gnn as train_fcggnn
from graph_embedding_generator import generate_program_node_embeddings
from feature_saver import (
    save_program_features, 
    save_experiment_metadata,
    save_torch_model, 
    save_numpy_array, 
    ensure_directory
)

# import debugpy
# try:
#     # 5678 is the default attach port in the VS Code debug configurations. Unless a host and port are specified, host defaults to 127.0.0.1
#     debugpy.listen(("localhost", 9501))
#     print("Waiting for debugger attach")
#     debugpy.wait_for_client()
# except Exception as e:
#     pass

# 配置日志记录
def setup_logger(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    参数:
        log_file (str, optional): 日志文件路径，默认为None（控制台输出）
        level (int, optional): 日志级别，默认为INFO
        
    返回:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger("main_workflow")
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 如果提供了日志文件路径，则创建文件处理器
    if log_file:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 解析参数
def parse_args():
    """
    解析命令行参数
    
    返回:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="Python代码特征提取和GNN模型训练工作流")
    
    # 数据路径参数
    parser.add_argument("--source_dir", type=str, required=True, 
                        help="Python源代码目录")
    parser.add_argument("--output_dir", type=str, default="output", 
                        help="输出目录，用于保存训练好的模型和指标")
    parser.add_argument("--log_file", type=str, default=None, 
                        help="日志文件路径")
    parser.add_argument("--label_file", type=str, default=None, 
                        help="标签文件路径，CSV格式，包含文件路径和对应标签")
    
    # 特征提取参数
    parser.add_argument("--min_nodes", type=int, default=2, 
                        help="图中最小节点数量")
    parser.add_argument("--max_nodes", type=int, default=500, 
                        help="图中最大节点数量")
    
    # GNN训练参数
    parser.add_argument("--cfg_epochs", type=int, default=100, 
                        help="CFG GNN训练轮数")  # 控制流图(CFG)的神经网络模型训练迭代次数
    parser.add_argument("--fcg_epochs", type=int, default=50, 
                        help="FCG GNN训练轮数")  # 函数调用图(FCG)的神经网络模型训练迭代次数
    parser.add_argument("--batch_size", type=int, default=32, 
                        help="批处理大小")  # 每次模型更新参数时处理的样本数量
    parser.add_argument("--learning_rate", type=float, default=0.001, 
                        help="学习率")  # 模型梯度更新步长，控制参数更新速度
    parser.add_argument("--hidden_channels", type=int, default=128, 
                        help="GNN隐藏层通道数")  # GNN模型中隐藏层的特征维度
    parser.add_argument("--out_channels", type=int, default=64, 
                        help="GNN输出层通道数")  # GNN模型的输出嵌入向量维度
    parser.add_argument("--num_layers", type=int, default=3, 
                        help="GNN层数")  # GNN模型的层数，决定模型深度
    parser.add_argument("--dropout", type=float, default=0.2, 
                        help="Dropout率")  # 防过拟合的随机失活率，控制特征丢弃比例
    parser.add_argument("--train_ratio", type=float, default=0.7,
                        help="训练集比例")
    parser.add_argument("--val_ratio", type=float, default=0.15,
                        help="验证集比例")
    
    # 系统参数
    parser.add_argument("--cpu_count", type=int, default=None, 
                        help="要使用的CPU核心数，默认为系统可用核心数的75%")
    parser.add_argument("--gpu_id", type=int, default=0, 
                        help="要使用的GPU ID，-1表示使用CPU")  # 指定使用的GPU设备ID
    parser.add_argument("--seed", type=int, default=42, 
                        help="随机种子")  # 随机数生成种子，确保实验可重复性
    
    # 工作流控制参数
    parser.add_argument("--skip_parsing", action="store_true", 
                        help="跳过解析步骤")
    parser.add_argument("--skip_feature_extraction", action="store_true", 
                        help="跳过特征提取步骤")
    parser.add_argument("--skip_graph_building", action="store_true", 
                        help="跳过图构建步骤")
    parser.add_argument("--debug", action="store_true", 
                        help="启用调试模式")
    
    return parser.parse_args()


# 解析python文件并返回AST
def parse_files_to_ast(python_files: List[str], 
                      logger: logging.Logger,
                      cpu_count: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
    """
    解析Python文件为AST
    
    参数:
        python_files (List[str]): Python文件路径列表
        logger (logging.Logger): 日志记录器
        cpu_count (int, optional): CPU核心数，默认为None（使用系统默认值）
        
    返回:
        Dict[str, Dict[str, Any]]: 映射文件路径到其AST及相关信息的字典
    """
    logger.info(f"开始解析 {len(python_files)} 个Python文件...")
    start_time = time.time()
    
    # 设置进程池的大小
    if cpu_count is None:
        cpu_count = max(1, int(multiprocessing.cpu_count() * 0.75))
    
    # 创建进程池
    with multiprocessing.Pool(processes=cpu_count) as pool:
        # 将文件路径列表分批提交给进程池
        results = pool.map(parse_code_to_ast, python_files)
    
    # 整理结果
    ast_dict = {}
    for file_path, ast_result in zip(python_files, results):
        if ast_result is not None:
            ast_dict[file_path] = {'ast': ast_result, 'source': ''}
            # 尝试读取源代码
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    ast_dict[file_path]['source'] = f.read()
            except:
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        ast_dict[file_path]['source'] = f.read()
                except:
                    pass
    
    elapsed_time = time.time() - start_time
    logger.info(f"文件解析完成，共处理 {len(ast_dict)}/{len(python_files)} 个文件，耗时 {elapsed_time:.2f} 秒")
    
    return ast_dict


# 提取特征并构建图
def extract_features_and_build_graphs(ast_dict: Dict[str, Dict[str, Any]], 
                                     logger: logging.Logger,
                                     min_nodes: int = 2,
                                     max_nodes: int = 500) -> Tuple[Dict[str, Dict[str, nx.DiGraph]], Dict[str, nx.DiGraph]]:
    """
    从AST提取特征并构建CFG和FCG图
    
    参数:
        ast_dict (Dict[str, Dict[str, Any]]): 映射文件路径到AST的字典
        logger (logging.Logger): 日志记录器
        min_nodes (int, optional): 最小节点数，默认为2
        max_nodes (int, optional): 最大节点数，默认为500
        
    返回:
        Tuple[Dict[str, Dict[str, nx.DiGraph]], Dict[str, nx.DiGraph]]: CFG字典和FCG字典
    """
    logger.info("开始提取特征并构建图...")
    start_time = time.time()
    
    # 存储每个文件的CFG和FCG
    all_cfgs = {}  # {file_path: {function_name: cfg}}
    all_fcgs = {}  # {file_path: fcg}
    
    # 处理每个文件
    for file_path, ast_info in ast_dict.items():
        ast_tree = ast_info.get('ast')
        if ast_tree is None:
            logger.warning(f"文件 {file_path} 的AST为空，跳过")
            continue
        
        source_code = ast_info.get('source', '')
        if not source_code:
            logger.warning(f"文件 {file_path} 的源代码为空，跳过")
            continue
        
        logger.info(f"正在处理文件: {file_path}")
        
        try:
            # 直接使用graph_builder.py中的build_program_graphs函数构建CFG和FCG
            cfgs_dict, fcg = build_program_graphs(ast_tree, source_code)
            
            logger.info(f"文件 {file_path} 原始CFGs数量: {len(cfgs_dict)}, FCG节点数: {fcg.number_of_nodes() if fcg else 0}")
            
            if not cfgs_dict:
                logger.warning(f"文件 {file_path} 没有生成任何CFG")
                continue
                
            # 检查是否所有CFG都为空
            empty_cfgs = sum(1 for cfg in cfgs_dict.values() if cfg.number_of_nodes() == 0)
            if empty_cfgs > 0:
                logger.warning(f"文件 {file_path} 有 {empty_cfgs}/{len(cfgs_dict)} 个空的CFG")
            
            # 放宽过滤条件，设置更小的min_nodes
            actual_min_nodes = 1  # 改为1，确保所有非空CFG都能保留
            
            # 过滤掉节点数过少或过多的CFG
            filtered_cfgs = {}
            for func_name, cfg in cfgs_dict.items():
                nodes_count = cfg.number_of_nodes()
                logger.debug(f"函数 {func_name} 的CFG节点数: {nodes_count}")
                
                if nodes_count < actual_min_nodes:
                    logger.debug(f"函数 {func_name} 的CFG节点数 ({nodes_count}) 小于最小值 {actual_min_nodes}，跳过")
                    continue
                
                if nodes_count > max_nodes:
                    logger.debug(f"函数 {func_name} 的CFG节点数 ({nodes_count}) 大于最大值 {max_nodes}，跳过")
                    continue
                
                filtered_cfgs[func_name] = cfg
            
            logger.info(f"文件 {file_path} 过滤后CFGs数量: {len(filtered_cfgs)}/{len(cfgs_dict)}")
            
            # 只有当有有效的CFG时才添加FCG
            if filtered_cfgs:
                all_cfgs[file_path] = filtered_cfgs
                
                # 确保FCG不为空
                if fcg and fcg.number_of_nodes() > 0:
                    all_fcgs[file_path] = fcg
                    logger.info(f"文件 {file_path} 包含 {len(filtered_cfgs)} 个有效函数, FCG有 {fcg.number_of_nodes()} 个节点")
                else:
                    # 如果FCG为空，创建一个只包含函数节点的简单FCG
                    logger.warning(f"文件 {file_path} 的FCG为空，创建一个简单的FCG")
                    simple_fcg = nx.DiGraph()
                    for func_name in filtered_cfgs.keys():
                        simple_fcg.add_node(func_name)
                    all_fcgs[file_path] = simple_fcg
            else:
                logger.warning(f"文件 {file_path} 没有有效的函数CFG，跳过")
        
        except Exception as e:
            logger.error(f"处理文件 {file_path} 时出错: {str(e)}", exc_info=True)
    
    elapsed_time = time.time() - start_time
    logger.info(f"特征提取和图构建完成，共处理了 {len(all_cfgs)} 个文件，耗时 {elapsed_time:.2f} 秒")
    logger.info(f"共生成 {sum(len(cfgs) for cfgs in all_cfgs.values())} 个CFG和 {len(all_fcgs)} 个FCG")
    
    return all_cfgs, all_fcgs


# 将NetworkX图转换为PyG数据
def convert_graphs_to_pyg(all_cfgs: Dict[str, Dict[str, nx.DiGraph]], 
                         all_fcgs: Dict[str, nx.DiGraph],
                         logger: logging.Logger) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """
    将NetworkX图转换为PyTorch Geometric数据
    
    参数:
        all_cfgs (Dict[str, Dict[str, nx.DiGraph]]): 所有CFG图
        all_fcgs (Dict[str, nx.DiGraph]): 所有FCG图
        logger (logging.Logger): 日志记录器
        
    返回:
        Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]: PyG格式的CFG和FCG数据
    """
    logger.info("开始将图转换为PyTorch Geometric格式...")
    start_time = time.time()
    
    # 检查输入是否为空
    if not all_cfgs or not all_fcgs:
        logger.warning("没有有效的CFG或FCG可供转换")
        return {}, {}
    
    # 存储转换后的PyG数据
    all_pyg_cfgs = {}  # {file_path: {function_name: pyg_cfg}}
    all_pyg_fcgs = {}  # {file_path: pyg_fcg}
    
    # 转换每个文件的CFG
    for file_path, cfgs in all_cfgs.items():
        if not cfgs:
            logger.warning(f"文件 {file_path} 没有CFG可供转换")
            continue
            
        pyg_cfgs = {}
        convert_errors = 0
        
        for function_name, cfg in cfgs.items():
            try:
                # 检查CFG是否为空
                if cfg.number_of_nodes() == 0:
                    logger.warning(f"函数 {function_name} 的CFG为空，跳过转换")
                    continue
                
                # 转换CFG为PyG格式
                pyg_cfg = networkx_to_pyg_cfg(cfg)
                # 添加函数名属性，方便后续处理
                pyg_cfg.function_name = function_name
                pyg_cfgs[function_name] = pyg_cfg
                
            except Exception as e:
                convert_errors += 1
                logger.error(f"转换函数 {function_name} 的CFG时出错: {str(e)}", exc_info=True)
        
        if pyg_cfgs:
            all_pyg_cfgs[file_path] = pyg_cfgs
            logger.info(f"文件 {file_path} 的CFG转换完成，成功: {len(pyg_cfgs)}，失败: {convert_errors}")
        else:
            logger.warning(f"文件 {file_path} 的所有CFG转换失败")
    
    # 转换每个文件的FCG
    for file_path, fcg in all_fcgs.items():
        try:
            # 检查FCG是否为空
            if fcg.number_of_nodes() == 0:
                logger.warning(f"文件 {file_path} 的FCG为空，跳过转换")
                continue
                
            # 提取FCG中的函数名列表
            function_names = [node for node in fcg.nodes()]
            
            # 转换FCG为PyG格式
            pyg_fcg = networkx_to_pyg_fcg(fcg)
            
            # 添加函数名列表属性，方便后续处理
            pyg_fcg.function_names = function_names
            
            all_pyg_fcgs[file_path] = pyg_fcg
            logger.info(f"文件 {file_path} 的FCG转换成功，节点数: {len(function_names)}")
            
        except Exception as e:
            logger.error(f"转换文件 {file_path} 的FCG时出错: {str(e)}", exc_info=True)
    
    elapsed_time = time.time() - start_time
    logger.info(f"图转换完成，共转换 {len(all_pyg_cfgs)} 个文件的CFG和 {len(all_pyg_fcgs)} 个文件的FCG，耗时 {elapsed_time:.2f} 秒")
    
    return all_pyg_cfgs, all_pyg_fcgs


# 划分数据集
def split_dataset(file_paths: List[str], 
                 train_ratio: float = 0.7, 
                 val_ratio: float = 0.15,
                 seed: int = 42) -> Tuple[List[str], List[str], List[str]]:
    """
    划分数据集为训练集、验证集和测试集
    
    参数:
        file_paths (List[str]): 文件路径列表
        train_ratio (float, optional): 训练集比例，默认为0.7
        val_ratio (float, optional): 验证集比例，默认为0.15
        seed (int, optional): 随机种子，默认为42
        
    返回:
        Tuple[List[str], List[str], List[str]]: 训练集、验证集和测试集
    """
    # 设置随机种子
    np.random.seed(seed)
    
    # 随机打乱文件路径
    shuffled_paths = file_paths.copy()
    np.random.shuffle(shuffled_paths)
    
    # 计算索引
    n = len(shuffled_paths)
    train_end = int(n * train_ratio)
    val_end = train_end + int(n * val_ratio)
    
    # 划分数据集
    train_paths = shuffled_paths[:train_end]
    val_paths = shuffled_paths[train_end:val_end]
    test_paths = shuffled_paths[val_end:]
    
    return train_paths, val_paths, test_paths


# 准备训练数据
def prepare_training_data(all_pyg_cfgs: Dict[str, Dict[str, Any]], 
                         all_pyg_fcgs: Dict[str, Any],
                         train_paths: List[str],
                         val_paths: List[str],
                         logger: logging.Logger) -> Tuple[List[Any], List[Any], List[Any], List[Any]]:
    """
    准备训练数据
    
    参数:
        all_pyg_cfgs (Dict[str, Dict[str, Any]]): 所有PyG格式的CFG
        all_pyg_fcgs (Dict[str, Any]): 所有PyG格式的FCG
        train_paths (List[str]): 训练集文件路径
        val_paths (List[str]): 验证集文件路径
        logger (logging.Logger): 日志记录器
        
    返回:
        Tuple[List[Any], List[Any], List[Any], List[Any]]: CFG训练集、CFG验证集、FCG训练集、FCG验证集
    """
    logger.info("准备训练数据...")
    
    # 确保所有FCG图的edge_attr维度一致
    max_edge_attr_dim = 1  # 最小维度为1
    for fcg_data in all_pyg_fcgs.values():
        if hasattr(fcg_data, 'edge_attr') and fcg_data.edge_attr is not None:
            if fcg_data.edge_attr.size(1) > max_edge_attr_dim:
                max_edge_attr_dim = fcg_data.edge_attr.size(1)
    
    # 调整所有FCG图的edge_attr维度
    for fcg_data in all_pyg_fcgs.values():
        if hasattr(fcg_data, 'edge_attr') and fcg_data.edge_attr is not None:
            if fcg_data.edge_attr.size(1) < max_edge_attr_dim:
                # 扩展维度
                padding = torch.zeros((fcg_data.edge_attr.size(0), max_edge_attr_dim - fcg_data.edge_attr.size(1)), 
                                      device=fcg_data.edge_attr.device, 
                                      dtype=fcg_data.edge_attr.dtype)
                fcg_data.edge_attr = torch.cat([fcg_data.edge_attr, padding], dim=1)
        else:
            # 如果没有edge_attr，则创建一个
            num_edges = fcg_data.edge_index.size(1)
            fcg_data.edge_attr = torch.zeros((num_edges, max_edge_attr_dim), dtype=torch.float)
    
    # 划分数据
    cfg_train_data = []
    cfg_val_data = []
    fcg_train_data = []
    fcg_val_data = []
    
    # 收集所有训练和验证集中的CFG
    for file_path, pyg_cfgs in all_pyg_cfgs.items():
        for function_name, pyg_cfg in pyg_cfgs.items():
            if file_path in train_paths:
                cfg_train_data.append(pyg_cfg)
            elif file_path in val_paths:
                cfg_val_data.append(pyg_cfg)
    
    # 收集所有训练和验证集中的FCG
    for file_path, pyg_fcg in all_pyg_fcgs.items():
        if file_path in train_paths:
            fcg_train_data.append(pyg_fcg)
        elif file_path in val_paths:
            fcg_val_data.append(pyg_fcg)
    
    logger.info(f"CFG训练数据: {len(cfg_train_data)}个, 验证数据: {len(cfg_val_data)}个")
    logger.info(f"FCG训练数据: {len(fcg_train_data)}个, 验证数据: {len(fcg_val_data)}个")
    
    return cfg_train_data, cfg_val_data, fcg_train_data, fcg_val_data


# 使用CFG嵌入增强FCG节点
def enrich_fcg_with_cfg_embeddings(cfg_model: torch.nn.Module,
                                  fcg_data_list: List[Any],
                                  cfg_data_dict: Dict[str, Any],
                                  device: torch.device) -> List[Any]:
    """
    使用CFG GNN模型生成的函数嵌入增强FCG节点特征
    
    参数:
        cfg_model (torch.nn.Module): 训练好的CFG GNN模型
        fcg_data_list (List[Any]): FCG数据列表
        cfg_data_dict (Dict[str, Any]): 函数名到CFG数据的映射
        device (torch.device): 计算设备
        
    返回:
        List[Any]: 增强后的FCG数据列表
    """
    # 将模型设置为评估模式
    cfg_model.eval()
    
    # 存储增强后的FCG数据
    enriched_fcg_data = []
    
    # 处理每个FCG数据
    for fcg_data in fcg_data_list:
        # 克隆FCG数据以避免修改原始数据
        enriched_data = fcg_data.clone()
        
        # 如果FCG没有函数名列表属性，则跳过
        if not hasattr(enriched_data, 'function_names'):
            enriched_fcg_data.append(enriched_data)
            continue
        
        # 获取FCG中的函数名列表
        function_names = enriched_data.function_names
        
        # 新的节点特征（原始特征 + CFG嵌入）
        new_node_features = []
        
        # 为每个节点添加CFG嵌入
        for i, func_name in enumerate(function_names):
            # 获取原始节点特征
            original_feature = enriched_data.x[i]
            original_device = original_feature.device
            
            # 如果函数在cfg_data_dict中存在，则使用其CFG嵌入
            if func_name in cfg_data_dict:
                # 获取对应的CFG数据
                cfg_data = cfg_data_dict[func_name].to(device)
                
                # 使用CFG模型生成嵌入
                with torch.no_grad():
                    # 使用forward方法而不是encode方法
                    node_embeddings, graph_embedding, _ = cfg_model(cfg_data.x, cfg_data.edge_index, None)
                
                # 使用图嵌入作为CFG嵌入
                cfg_embedding = graph_embedding
                
                # 如果生成的嵌入是批处理的，则取第一个
                if cfg_embedding.dim() > 1 and cfg_embedding.size(0) > 1:
                    cfg_embedding = cfg_embedding[0]
                
                # 将嵌入移到与原始特征相同的设备上
                cfg_embedding = cfg_embedding.to(original_device)
                
                # 合并原始特征和CFG嵌入
                combined_feature = torch.cat([original_feature, cfg_embedding])
                new_node_features.append(combined_feature)
            else:
                # 如果没有对应的CFG，则使用零向量作为CFG嵌入
                cfg_embedding_size = cfg_model.out_channels
                zero_embedding = torch.zeros(cfg_embedding_size, device=original_device)
                combined_feature = torch.cat([original_feature, zero_embedding])
                new_node_features.append(combined_feature)
        
        # 更新节点特征
        if new_node_features:
            enriched_data.x = torch.stack(new_node_features)
        
        enriched_fcg_data.append(enriched_data)
    
    return enriched_fcg_data


# 训练GNN模型
def train_gnn_models(cfg_train_data: List[Any], 
                    cfg_val_data: List[Any], 
                    fcg_train_data: List[Any], 
                    fcg_val_data: List[Any],
                    args: argparse.Namespace,
                    logger: logging.Logger) -> Tuple[torch.nn.Module, torch.nn.Module, Dict[str, List[float]]]:
    """
    训练CFG和FCG的GNN模型
    
    参数:
        cfg_train_data (List[Any]): CFG训练数据
        cfg_val_data (List[Any]): CFG验证数据
        fcg_train_data (List[Any]): FCG训练数据
        fcg_val_data (List[Any]): FCG验证数据
        args (argparse.Namespace): 命令行参数
        logger (logging.Logger): 日志记录器
        
    返回:
        Tuple[torch.nn.Module, torch.nn.Module, Dict[str, List[float]]]: CFG GNN模型、FCG GNN模型和训练指标
    """
    logger.info("开始训练GNN模型...")
    
    # 设置随机种子
    torch.manual_seed(args.seed)
    
    # 设置设备
    device = torch.device(f'cuda:{args.gpu_id}' if (torch.cuda.is_available() and args.gpu_id >= 0) else 'cpu')
    logger.info(f"使用设备: {device}")
    
    # 确保所有训练数据都移动到GPU
    cfg_train_data = [data.to(device) for data in cfg_train_data]
    cfg_val_data = [data.to(device) for data in cfg_val_data]
    fcg_train_data = [data.to(device) for data in fcg_train_data]
    fcg_val_data = [data.to(device) for data in fcg_val_data]
    
    # 确定CFG输入特征维度
    cfg_in_channels = cfg_train_data[0].x.size(1) if cfg_train_data else 0
    if cfg_in_channels == 0:
        logger.error("无法确定CFG输入特征维度")
        return None, None, {}
    
    # 创建CFG GNN模型
    cfg_gnn = CFGGNN(
        in_channels=cfg_in_channels,  # 输入特征维度，由数据集自动确定
        hidden_channels=args.hidden_channels,  # 隐藏层维度，决定模型表达能力
        out_channels=args.out_channels,  # 输出特征维度，决定最终嵌入维度
        num_layers=args.num_layers,  # GNN的层数，层数越多感受野越大
        dropout=args.dropout  # Dropout比率，用于防止过拟合
    ).to(device)
    
    # 创建数据加载器
    from torch_geometric.loader import DataLoader
    cfg_train_loader = DataLoader(cfg_train_data, batch_size=args.batch_size, shuffle=True)
    cfg_val_loader = DataLoader(cfg_val_data, batch_size=args.batch_size)
    
    # 创建优化器和损失函数
    optimizer = torch.optim.Adam(cfg_gnn.parameters(), lr=args.learning_rate)  # Adam优化器，lr为学习率，控制参数更新幅度
    criterion = torch.nn.BCELoss()  # 二元交叉熵损失函数，用于二分类任务
    
    # 训练CFG GNN模型
    logger.info("训练CFG GNN模型...")
    cfg_gnn, cfg_metrics = train_cfggnn(
        model=cfg_gnn,
        data_loader=cfg_train_loader,
        optimizer=optimizer,
        criterion=criterion,
        device=device,
        num_epochs=args.cfg_epochs  # 训练轮数，决定模型训练时间和效果
    )
    
    # 确定FCG输入特征维度（原始特征 + CFG嵌入）
    fcg_in_channels = fcg_train_data[0].x.size(1) + args.out_channels if fcg_train_data else 0
    if fcg_in_channels == 0:
        logger.error("无法确定FCG输入特征维度")
        return cfg_gnn, None, {'cfg_loss': cfg_metrics['loss'], 'cfg_val_loss': cfg_metrics['val_loss']}
    
    # 创建FCG GNN模型
    fcg_gnn = FCGGNN(
        in_channels=fcg_in_channels,  # 输入维度 = 原始特征 + CFG嵌入
        hidden_channels=args.hidden_channels,  # 与CFG模型共用隐藏层维度参数
        out_channels=args.out_channels,  # 与CFG模型共用输出维度参数
        num_layers=args.num_layers,  # 与CFG模型共用层数参数
        dropout=args.dropout  # 与CFG模型共用Dropout参数
    ).to(device)
    
    # 准备函数名到CFG数据的映射
    cfg_data_dict = {}
    for cfg_data in cfg_train_data:
        if hasattr(cfg_data, 'function_name'):
            cfg_data_dict[cfg_data.function_name] = cfg_data
    
    # 使用训练好的CFG GNN为FCG节点生成嵌入
    logger.info("使用CFG嵌入增强FCG节点特征")
    enriched_fcg_train_data = enrich_fcg_with_cfg_embeddings(cfg_gnn, fcg_train_data, cfg_data_dict, device)
    enriched_fcg_val_data = enrich_fcg_with_cfg_embeddings(cfg_gnn, fcg_val_data, cfg_data_dict, device)
    
    # 创建FCG数据加载器
    fcg_train_loader = DataLoader(enriched_fcg_train_data, batch_size=args.batch_size, shuffle=True)
    fcg_val_loader = DataLoader(enriched_fcg_val_data, batch_size=args.batch_size)
    
    # 创建FCG GNN优化器和损失函数
    fcg_optimizer = torch.optim.Adam(fcg_gnn.parameters(), lr=args.learning_rate)  # 与CFG模型共用学习率参数
    fcg_criterion = torch.nn.BCELoss()  # 与CFG模型使用相同损失函数
    
    # 训练FCG GNN模型
    logger.info("训练FCG GNN模型...")
    fcg_gnn, fcg_metrics = train_fcggnn(
        model=fcg_gnn,
        data_loader=fcg_train_loader,
        optimizer=fcg_optimizer,
        criterion=fcg_criterion,
        device=device,
        num_epochs=args.fcg_epochs  # FCG模型专用的训练轮数参数
    )
    
    # 合并训练指标
    metrics = {
        'cfg_loss': cfg_metrics['loss'], # 训练损失
        'cfg_val_loss': cfg_metrics['val_loss'], # 验证损失
        'fcg_loss': fcg_metrics['loss'], # 训练损失
        'fcg_val_loss': fcg_metrics['val_loss'], # 验证损失
    }
    
    return cfg_gnn, fcg_gnn, metrics


# 保存训练好的模型
def save_trained_models(cfg_gnn: torch.nn.Module, 
                       fcg_gnn: torch.nn.Module, 
                       metrics: Dict[str, List[float]],
                       args: argparse.Namespace,
                       logger: logging.Logger) -> Dict[str, str]:
    """
    保存训练好的模型和训练指标
    
    参数:
        cfg_gnn (torch.nn.Module): 训练好的CFG GNN模型
        fcg_gnn (torch.nn.Module): 训练好的FCG GNN模型
        metrics (Dict[str, List[float]]): 训练指标
        args (argparse.Namespace): 命令行参数
        logger (logging.Logger): 日志记录器
        
    返回:
        Dict[str, str]: 保存的文件路径字典
    """
    logger.info("保存训练好的模型和训练指标...")
    
    # 创建输出目录
    output_dir = args.output_dir
    models_dir = os.path.join(output_dir, "models")
    ensure_directory(models_dir)
    
    saved_files = {}
    
    # 保存模型
    if cfg_gnn is not None:
        cfg_model_path = os.path.join(models_dir, "cfg_gnn_model.pt")
        saved_files['cfg_model'] = save_torch_model(cfg_gnn, cfg_model_path)
        logger.info(f"CFG GNN模型已保存到 {cfg_model_path}")
    
    if fcg_gnn is not None:
        fcg_model_path = os.path.join(models_dir, "fcg_gnn_model.pt")
        saved_files['fcg_model'] = save_torch_model(fcg_gnn, fcg_model_path)
        logger.info(f"FCG GNN模型已保存到 {fcg_model_path}")
    
    # 保存训练指标
    metrics_path = os.path.join(output_dir, "training_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    saved_files['metrics'] = metrics_path
    
    # 保存实验元数据
    metadata = {
        'args': vars(args),
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'files': saved_files,
        'cfg_model_params': sum(p.numel() for p in cfg_gnn.parameters()) if cfg_gnn else 0,
        'fcg_model_params': sum(p.numel() for p in fcg_gnn.parameters()) if fcg_gnn else 0,
    }
    
    metadata_path = os.path.join(output_dir, "experiment_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    saved_files['metadata'] = metadata_path
    
    logger.info(f"所有结果已保存到 {output_dir}")
    
    return saved_files


# 加载标签文件
def load_labels(label_file: str, logger: logging.Logger) -> Dict[str, int]:
    """
    加载标签文件
    
    参数:
        label_file (str): 标签文件路径
        logger (logging.Logger): 日志记录器
        
    返回:
        Dict[str, int]: 映射文件路径到标签的字典
    """
    logger.info(f"加载标签文件: {label_file}")
    labels = {}
    
    try:
        with open(label_file, 'r') as f:
            import csv
            reader = csv.reader(f)
            header = next(reader)  # 跳过标题行
            
            # 假设CSV格式为: 文件路径,标签
            for row in reader:
                if len(row) >= 2:
                    file_path = row[0].strip()
                    label = int(row[1].strip())
                    labels[file_path] = label
        
        logger.info(f"成功加载 {len(labels)} 个文件的标签")
    except Exception as e:
        logger.error(f"加载标签文件时出错: {str(e)}")
    
    return labels


# 主工作流函数
def main_workflow(args: argparse.Namespace, logger: logging.Logger) -> Dict[str, Any]:
    """
    主工作流程 - 训练GNN模型
    
    参数:
        args (argparse.Namespace): 命令行参数
        logger (logging.Logger): 日志记录器
        
    返回:
        Dict[str, Any]: 工作流结果
    """
    # 设置随机种子
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # 设置CPU核心数
    if args.cpu_count is None:
        args.cpu_count = max(1, int(multiprocessing.cpu_count() * 0.75))
    
    # 设置设备
    device = torch.device(f'cuda:{args.gpu_id}' if (torch.cuda.is_available() and args.gpu_id >= 0) else 'cpu')
    logger.info(f"使用设备: {device}")
    
    results = {}
    
    # 加载标签文件（如果提供）
    labels = {}
    if args.label_file:
        labels = load_labels(args.label_file, logger)
    
    # 步骤1: 加载Python文件
    logger.info(f"从 {args.source_dir} 加载Python文件...")
    python_files = load_code_paths(args.source_dir)
    logger.info(f"找到 {len(python_files)} 个Python文件")
    
    # 划分数据集
    train_paths, val_paths, test_paths = split_dataset(
        python_files, 
        train_ratio=args.train_ratio, 
        val_ratio=args.val_ratio,
        seed=args.seed
    )
    logger.info(f"数据集划分: 训练集 {len(train_paths)}个, 验证集 {len(val_paths)}个, 测试集 {len(test_paths)}个")
    
    results['dataset'] = {
        'total_files': len(python_files),
        'train_files': len(train_paths),
        'val_files': len(val_paths),
        'test_files': len(test_paths),
    }
    
    # 步骤2: 解析Python文件
    ast_dict = {}
    if not args.skip_parsing:
        ast_dict = parse_files_to_ast(python_files, logger, args.cpu_count)
        results['parsing'] = {
            'parsed_files': len(ast_dict),
        }
    else:
        logger.info("跳过解析步骤")
    
    # 步骤3: 提取特征并构建图
    all_cfgs = {}
    all_fcgs = {}
    if not args.skip_feature_extraction and not args.skip_graph_building:
        all_cfgs, all_fcgs = extract_features_and_build_graphs(
            ast_dict, logger, args.min_nodes, args.max_nodes
        )
        results['graph_building'] = {
            'files_with_graphs': len(all_cfgs),
            'total_cfgs': sum(len(cfgs) for cfgs in all_cfgs.values()),
            'total_fcgs': len(all_fcgs),
        }
    else:
        logger.info("跳过特征提取和图构建步骤")
    
    # 检查是否有有效的图
    has_valid_graphs = bool(all_cfgs and all_fcgs)
    
    if not has_valid_graphs:
        logger.error("没有生成有效的图结构，无法训练模型")
        return {'error': '没有有效的图结构'}
        
    # 步骤4: 转换图为PyG格式
    all_pyg_cfgs = {}
    all_pyg_fcgs = {}
    all_pyg_cfgs, all_pyg_fcgs = convert_graphs_to_pyg(all_cfgs, all_fcgs, logger)
    results['conversion'] = {
        'files_with_pyg_graphs': len(all_pyg_cfgs),
    }
    
    # 步骤5: 准备训练数据
    cfg_train_data = []
    cfg_val_data = []
    fcg_train_data = []
    fcg_val_data = []
    cfg_train_data, cfg_val_data, fcg_train_data, fcg_val_data = prepare_training_data(
        all_pyg_cfgs, all_pyg_fcgs, train_paths, val_paths, logger
    )
    
    # 步骤6: 训练GNN模型
    cfg_gnn = None
    fcg_gnn = None
    metrics = {}
    
    if cfg_train_data and fcg_train_data:
        cfg_gnn, fcg_gnn, metrics = train_gnn_models(
            cfg_train_data, cfg_val_data, fcg_train_data, fcg_val_data, args, logger
        )
        results['training'] = {
            'cfg_final_loss': metrics['cfg_loss'][-1] if metrics.get('cfg_loss') else None,
            'cfg_final_val_loss': metrics['cfg_val_loss'][-1] if metrics.get('cfg_val_loss') else None,
            'fcg_final_loss': metrics['fcg_loss'][-1] if metrics.get('fcg_loss') else None,
            'fcg_final_val_loss': metrics['fcg_val_loss'][-1] if metrics.get('fcg_val_loss') else None,
        }
    else:
        logger.error("训练数据为空，无法训练模型")
        return {'error': '训练数据为空'}
    
    # 步骤7: 保存训练好的模型
    saved_files = save_trained_models(cfg_gnn, fcg_gnn, metrics, args, logger)
    results['saved_files'] = saved_files
    
    logger.info("模型训练完成")
    return results


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.DEBUG if args.debug else logging.INFO
    
    # 设置日志记录器
    logger = setup_logger(args.log_file, log_level)
    
    try:
        # 打印参数信息
        logger.info("开始Python代码特征提取和GNN模型训练工作流")
        logger.info(f"参数: {vars(args)}")
        
        # 运行主工作流
        results = main_workflow(args, logger)
        
        # 打印总结
        logger.info("工作流完成")
        logger.info(f"结果摘要: {json.dumps(results, indent=2)}")
        
    except Exception as e:
        logger.error(f"工作流执行过程中出错: {str(e)}", exc_info=True)
        sys.exit(1)
    
    sys.exit(0) 