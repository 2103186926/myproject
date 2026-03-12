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

# 导入自定义模块
from dataset_loader import load_code_paths
from ast_parser import parse_code_to_ast
import feature_extractor
from graph_builder import build_program_graphs
from graph_converter import convert_to_pyg_data as networkx_to_pyg_cfg
from graph_converter import convert_to_pyg_data as networkx_to_pyg_fcg
from gnn_trainer import CFGGNN, FCGGNN
from graph_embedding_generator import generate_program_node_embeddings
from feature_saver import (
    save_program_features, 
    ensure_directory,
    save_numpy_array
)


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
    logger = logging.getLogger("model_apply")
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
    parser = argparse.ArgumentParser(description="Python代码特征提取应用程序")
    
    # 数据路径参数
    parser.add_argument("--source_dir", type=str, required=True, 
                        help="Python源代码目录")
    parser.add_argument("--output_dir", type=str, default="output/features", 
                        help="输出目录，用于保存生成的特征向量")
    parser.add_argument("--log_file", type=str, default=None, 
                        help="日志文件路径")
    
    # 模型路径参数
    parser.add_argument("--cfg_model_path", type=str, required=True, 
                        help="CFG GNN模型路径")
    parser.add_argument("--fcg_model_path", type=str, required=True, 
                        help="FCG GNN模型路径")
    
    # 特征提取参数
    parser.add_argument("--min_nodes", type=int, default=2, 
                        help="图中最小节点数量")
    parser.add_argument("--max_nodes", type=int, default=500, 
                        help="图中最大节点数量")
    parser.add_argument("--embedding_dim", type=int, default=256, 
                        help="生成的特征向量维度")
    
    # 系统参数
    parser.add_argument("--cpu_count", type=int, default=None, 
                        help="要使用的CPU核心数，默认为系统可用核心数的75%")
    parser.add_argument("--gpu_id", type=int, default=0, 
                        help="要使用的GPU ID，-1表示使用CPU")
    
    return parser.parse_args()


# 加载训练好的模型
def load_models(cfg_model_path: str, 
               fcg_model_path: str, 
               device: torch.device,
               logger: logging.Logger) -> Tuple[torch.nn.Module, torch.nn.Module]:
    """
    加载训练好的GNN模型
    
    参数:
        cfg_model_path (str): CFG GNN模型路径
        fcg_model_path (str): FCG GNN模型路径
        device (torch.device): 计算设备
        logger (logging.Logger): 日志记录器
        
    返回:
        Tuple[torch.nn.Module, torch.nn.Module]: CFG GNN模型和FCG GNN模型
    """
    logger.info("加载训练好的GNN模型...")
    
    try:
        # 加载CFG GNN模型
        cfg_gnn = torch.load(cfg_model_path, map_location=device, weights_only=False)
        logger.info(f"CFG GNN模型加载成功: {cfg_model_path}")
        
        # 加载FCG GNN模型
        fcg_gnn = torch.load(fcg_model_path, map_location=device, weights_only=False)
        logger.info(f"FCG GNN模型加载成功: {fcg_model_path}")
        
        # 将模型设置为评估模式
        cfg_gnn.eval()
        fcg_gnn.eval()
        
        return cfg_gnn, fcg_gnn
    
    except Exception as e:
        logger.error(f"加载模型时出错: {str(e)}", exc_info=True)
        raise


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


# 使用训练好的模型生成特征向量
def generate_feature_vectors(cfg_gnn: torch.nn.Module,
                            fcg_gnn: torch.nn.Module,
                            all_pyg_cfgs: Dict[str, Dict[str, Any]],
                            all_pyg_fcgs: Dict[str, Any],
                            embedding_dim: int,
                            device: torch.device,
                            logger: logging.Logger) -> Dict[str, np.ndarray]:
    """
    使用训练好的GNN模型为每个程序生成特征向量
    
    参数:
        cfg_gnn (torch.nn.Module): 训练好的CFG GNN模型
        fcg_gnn (torch.nn.Module): 训练好的FCG GNN模型
        all_pyg_cfgs (Dict[str, Dict[str, Any]]): 所有PyG格式的CFG
        all_pyg_fcgs (Dict[str, Any]): 所有PyG格式的FCG
        embedding_dim (int): 特征向量维度
        device (torch.device): 计算设备
        logger (logging.Logger): 日志记录器
        
    返回:
        Dict[str, np.ndarray]: 映射文件路径到其特征向量的字典
    """
    logger.info("开始生成特征向量...")
    
    # 确保模型在评估模式
    cfg_gnn.eval()
    fcg_gnn.eval()
    
    # 预处理：构建文件路径到CFG数据列表的映射
    program_cfg_data_map = {}
    for file_path, pyg_cfgs in all_pyg_cfgs.items():
        cfg_data_list = []
        for function_name, pyg_cfg in pyg_cfgs.items():
            cfg_data_list.append(pyg_cfg)
        program_cfg_data_map[file_path] = cfg_data_list
    
    # 使用generate_program_node_embeddings生成FCG节点嵌入
    program_embeddings = generate_program_node_embeddings(
        trained_cfg_gnn_model=cfg_gnn,
        trained_fcg_gnn_model=fcg_gnn,
        program_cfg_data_map=program_cfg_data_map,
        program_fcg_data_map=all_pyg_fcgs,
        device=device
    )
    
    # 将节点嵌入转换为固定维度的程序特征向量
    feature_vectors = {}
    
    for file_path, node_embeddings in program_embeddings.items():
        # 获取节点嵌入的平均值作为程序特征向量
        avg_embedding = torch.mean(node_embeddings, dim=0)
        
        # 如果需要调整维度
        current_dim = avg_embedding.size(0)
        if current_dim != embedding_dim:
            logger.info(f"调整文件 {file_path} 的特征向量维度: {current_dim} -> {embedding_dim}")
            
            if current_dim > embedding_dim:
                # 降维：使用前embedding_dim维
                final_embedding = avg_embedding[:embedding_dim]
            else:
                # 升维：在后面填充0
                padding = torch.zeros(embedding_dim - current_dim)
                final_embedding = torch.cat([avg_embedding, padding])
        else:
            final_embedding = avg_embedding
        
        # 转换为NumPy数组
        feature_vectors[file_path] = final_embedding.cpu().numpy()
    
    logger.info(f"特征向量生成完成，共处理 {len(feature_vectors)} 个文件")
    
    return feature_vectors


# 保存特征向量
def save_feature_vectors(feature_vectors: Dict[str, np.ndarray],
                        output_dir: str,
                        logger: logging.Logger) -> Dict[str, str]:
    """
    保存特征向量到文件
    
    参数:
        feature_vectors (Dict[str, np.ndarray]): 映射文件路径到其特征向量的字典
        output_dir (str): 输出目录
        logger (logging.Logger): 日志记录器
        
    返回:
        Dict[str, str]: 映射文件路径到其保存路径的字典
    """
    logger.info(f"开始保存特征向量到 {output_dir}...")
    
    # 确保输出目录存在
    ensure_directory(output_dir)
    
    # 保存文件路径字典
    saved_paths = {}
    
    # 保存每个文件的特征向量
    for file_path, feature_vector in feature_vectors.items():
        # 生成与输入文件对应的输出文件名
        file_name = os.path.basename(file_path)
        output_file_name = file_name.replace('.py', '_structual.npy')
        output_path = os.path.join(output_dir, output_file_name)
        
        try:
            # 保存NumPy数组
            save_numpy_array(feature_vector, output_path)
            saved_paths[file_path] = output_path
            logger.info(f"文件 {file_path} 的特征向量已保存到 {output_path}")
        
        except Exception as e:
            logger.error(f"保存文件 {file_path} 的特征向量时出错: {str(e)}", exc_info=True)
    
    # 保存元数据
    metadata = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_count": len(feature_vectors),
        "embedding_dim": next(iter(feature_vectors.values())).shape[0] if feature_vectors else 0,
        "files": list(feature_vectors.keys()),
        "saved_paths": saved_paths
    }
    
    metadata_path = os.path.join(output_dir, "feature_vectors_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logger.info(f"特征向量元数据已保存到 {metadata_path}")
    
    return saved_paths


# 主函数
def main():
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    log_level = logging.INFO
    
    # 设置日志记录器
    logger = setup_logger(args.log_file, log_level)
    
    try:
        # 打印参数信息
        logger.info("开始Python代码特征提取应用")
        logger.info(f"参数: {vars(args)}")
        
        # 设置CPU核心数
        if args.cpu_count is None:
            args.cpu_count = max(1, int(multiprocessing.cpu_count() * 0.75))
        
        # 设置设备
        device = torch.device(f'cuda:{args.gpu_id}' if (torch.cuda.is_available() and args.gpu_id >= 0) else 'cpu')
        logger.info(f"使用设备: {device}")
        
        # 加载训练好的模型
        cfg_gnn, fcg_gnn = load_models(args.cfg_model_path, args.fcg_model_path, device, logger)
        
        # 加载Python文件
        logger.info(f"从 {args.source_dir} 加载Python文件...")
        python_files = load_code_paths(args.source_dir)
        logger.info(f"找到 {len(python_files)} 个Python文件")
        
        # 解析Python文件
        ast_dict = parse_files_to_ast(python_files, logger, args.cpu_count)
        
        # 提取特征并构建图
        all_cfgs, all_fcgs = extract_features_and_build_graphs(
            ast_dict, logger, args.min_nodes, args.max_nodes
        )
        
        # 转换图为PyG格式
        all_pyg_cfgs, all_pyg_fcgs = convert_graphs_to_pyg(all_cfgs, all_fcgs, logger)
        
        # 生成特征向量
        feature_vectors = generate_feature_vectors(
            cfg_gnn, fcg_gnn, all_pyg_cfgs, all_pyg_fcgs, args.embedding_dim, device, logger
        )
        
        # 保存特征向量
        saved_paths = save_feature_vectors(feature_vectors, args.output_dir, logger)
        
        logger.info(f"特征提取完成，共处理 {len(saved_paths)}/{len(python_files)} 个文件")
        
        return 0
        
    except Exception as e:
        logger.error(f"应用程序执行过程中出错: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
