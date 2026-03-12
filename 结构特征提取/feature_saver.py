#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pickle
import numpy as np
import networkx as nx
import pandas as pd
from typing import Dict, List, Any, Union, Optional, Tuple
import pathlib
import datetime

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import torch_geometric
    from torch_geometric.data import Data as PyGData
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False


def ensure_directory(directory: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    参数:
        directory (str): 目录路径
        
    返回:
        str: 规范化的目录路径
    """
    pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    return directory


def get_timestamp_str() -> str:
    """
    获取当前时间戳字符串
    
    返回:
        str: 格式化的时间戳字符串
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def save_networkx_graph(graph: nx.Graph, 
                       filepath: str, 
                       format: str = 'gpickle',
                       compress: bool = False) -> str:
    """
    保存NetworkX图到文件
    
    参数:
        graph (nx.Graph): 要保存的NetworkX图
        filepath (str): 文件保存路径
        format (str, optional): 保存格式，可选值有'gpickle', 'graphml', 'gexf', 'adjlist'，默认为'gpickle'
        compress (bool, optional): 是否压缩，默认为False
        
    返回:
        str: 保存的文件路径
    """
    # 确保目录存在
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)
    
    # 根据格式保存图
    if format == 'gpickle':
        if compress:
            with open(filepath + ".gz", 'wb') as f:
                pickle.dump(graph, f, protocol=4)
            return filepath + ".gz"
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(graph, f, protocol=4)
    elif format == 'graphml':
        nx.write_graphml(graph, filepath)
    elif format == 'gexf':
        nx.write_gexf(graph, filepath)
    elif format == 'adjlist':
        nx.write_adjlist(graph, filepath)
    else:
        raise ValueError(f"不支持的图保存格式: {format}")
    
    return filepath


def save_pyg_data(data: PyGData, filepath: str) -> str:
    """
    保存PyTorch Geometric数据到文件
    
    参数:
        data (PyGData): 要保存的PyTorch Geometric数据
        filepath (str): 文件保存路径
        
    返回:
        str: 保存的文件路径
    """
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("请先安装PyTorch Geometric: pip install torch-geometric")
    
    # 确保目录存在
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)
    
    # 保存PyG数据
    torch.save(data, filepath)
    return filepath


def save_pyg_dataset(data_list: List[PyGData], filepath: str) -> str:
    """
    保存PyTorch Geometric数据列表到文件
    
    参数:
        data_list (List[PyGData]): 要保存的PyTorch Geometric数据列表
        filepath (str): 文件保存路径
        
    返回:
        str: 保存的文件路径
    """
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("请先安装PyTorch Geometric: pip install torch-geometric")
    
    # 确保目录存在
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)
    
    # 保存PyG数据列表
    torch.save(data_list, filepath)
    return filepath


def save_features_dict(features_dict: Dict[str, Any], 
                      filepath: str, 
                      format: str = 'pickle',
                      compress: bool = False) -> str:
    """
    保存特征字典到文件
    
    参数:
        features_dict (Dict[str, Any]): 要保存的特征字典
        filepath (str): 文件保存路径
        format (str, optional): 保存格式，可选值有'pickle', 'json', 'csv'，默认为'pickle'
        compress (bool, optional): 是否压缩，默认为False
        
    返回:
        str: 保存的文件路径
    """
    # 确保目录存在
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)
    
    # 根据格式保存特征字典
    if format == 'pickle':
        if compress:
            with open(filepath + ".gz", 'wb') as f:
                pickle.dump(features_dict, f, protocol=4)
            return filepath + ".gz"
        else:
            with open(filepath, 'wb') as f:
                pickle.dump(features_dict, f, protocol=4)
    elif format == 'json':
        # 将非JSON可序列化对象（如NumPy数组）转换为列表
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            elif isinstance(obj, (np.ndarray, np.number)):
                return obj.tolist()
            else:
                return obj
                
        serializable_dict = convert_to_serializable(features_dict)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_dict, f, ensure_ascii=False, indent=2)
    elif format == 'csv':
        # 将字典转换为DataFrame，要求特征是平面的
        try:
            df = pd.DataFrame.from_dict(features_dict, orient='index')
            df.to_csv(filepath, index_label='id')
        except Exception as e:
            raise ValueError(f"无法将特征字典转换为CSV格式: {str(e)}")
    else:
        raise ValueError(f"不支持的特征保存格式: {format}")
    
    return filepath


def save_numpy_array(array: np.ndarray, 
                    filepath: str, 
                    allow_pickle: bool = False,
                    compress: bool = False) -> str:
    """
    保存NumPy数组到文件
    
    参数:
        array (np.ndarray): 要保存的NumPy数组
        filepath (str): 文件保存路径
        allow_pickle (bool, optional): 是否允许使用pickle，默认为False
        compress (bool, optional): 是否压缩，默认为False
        
    返回:
        str: 保存的文件路径
    """
    # 确保目录存在
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)
    
    # 保存NumPy数组
    if compress:
        np.savez_compressed(filepath, array=array)
        return filepath + ".npz"
    else:
        np.save(filepath, array, allow_pickle=allow_pickle)
    
    return filepath


def save_torch_model(model: 'torch.nn.Module', 
                    filepath: str, 
                    save_full_model: bool = True) -> str:
    """
    保存PyTorch模型到文件
    
    参数:
        model (torch.nn.Module): 要保存的PyTorch模型
        filepath (str): 文件保存路径
        save_full_model (bool, optional): 是否保存完整模型，默认为True
        
    返回:
        str: 保存的文件路径
    """
    if not HAS_TORCH:
        raise ImportError("请先安装PyTorch: pip install torch")
    
    # 确保目录存在
    directory = os.path.dirname(filepath)
    if directory:
        ensure_directory(directory)
    
    # 保存模型
    if save_full_model:
        torch.save(model, filepath)
    else:
        torch.save(model.state_dict(), filepath)
    
    return filepath


def save_multiple_formats(data: Any,
                         base_filepath: str,
                         formats: List[str]) -> Dict[str, str]:
    """
    将数据保存为多种格式
    
    参数:
        data (Any): 要保存的数据
        base_filepath (str): 基础文件路径（不包含扩展名）
        formats (List[str]): 要保存的格式列表包括：NetworkX图、PyTorch Geometric数据、特征字典、NumPy数组、PyTorch模型等
            格式包括：
                    - 'gpickle', 'graphml', 'gexf', 'adjlist'（NetworkX图）
                    - 'pt'（PyTorch Geometric数据）
                    - 'pickle', 'json', 'csv'（特征字典）
                    - 'npy'（NumPy数组）
                    - 'pt', 'pth'（PyTorch模型）
        
    返回:
        Dict[str, str]: 格式到文件路径的映射
    """
    results = {}
    
    for format in formats:
        filepath = f"{base_filepath}.{format}"
        
        if isinstance(data, nx.Graph): # NetworkX图
            if format in ['gpickle', 'graphml', 'gexf', 'adjlist']:
                saved_path = save_networkx_graph(data, filepath, format=format)
                results[format] = saved_path
        
        elif HAS_TORCH_GEOMETRIC and isinstance(data, PyGData): # PyTorch Geometric数据
            if format == 'pt':
                saved_path = save_pyg_data(data, filepath)
                results[format] = saved_path
        
        elif isinstance(data, dict): # 特征字典
            if format in ['pickle', 'json', 'csv']:
                saved_path = save_features_dict(data, filepath, format=format)
                results[format] = saved_path
        
        elif isinstance(data, np.ndarray): # NumPy数组
            if format == 'npy':
                saved_path = save_numpy_array(data, filepath)
                results[format] = saved_path
        
        elif HAS_TORCH and isinstance(data, torch.nn.Module): # PyTorch模型
            if format in ['pt', 'pth']:
                saved_path = save_torch_model(data, filepath)
                results[format] = saved_path
    
    return results


def save_experiment_metadata(metadata: Dict[str, Any], 
                           output_dir: str,
                           experiment_name: Optional[str] = None) -> str:
    """
    保存实验元数据到文件
    
    参数:
        metadata (Dict[str, Any]): 实验元数据
        output_dir (str): 输出目录
        experiment_name (str, optional): 实验名称，默认为None（使用时间戳）
        
    返回:
        str: 保存的文件路径
    """
    # 确保输出目录存在
    ensure_directory(output_dir)
    
    # 生成实验名称
    if experiment_name is None:
        experiment_name = f"experiment_{get_timestamp_str()}"
    
    # 添加时间戳到元数据
    metadata['timestamp'] = get_timestamp_str()
    
    # 构建文件路径
    filepath = os.path.join(output_dir, f"{experiment_name}_metadata.json")
    
    # 保存为JSON
    def convert_to_serializable(obj):
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.ndarray, np.number)):
            return obj.tolist()
        else:
            return obj
    
    serializable_dict = convert_to_serializable(metadata)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(serializable_dict, f, ensure_ascii=False, indent=2)
    
    return filepath


def save_program_features(program_id: str,
                         cfg_features: Dict[str, Dict[str, Any]],
                         fcg_features: Dict[str, Any],
                         embedding: Optional[np.ndarray] = None,
                         sequences: Optional[List[List[Any]]] = None,
                         output_dir: str = "output/program_features") -> Dict[str, str]:
    """
    保存程序的所有特征数据
    
    参数:
        program_id (str): 程序ID
        cfg_features (Dict[str, Dict[str, Any]]): CFG特征字典（函数名到特征映射）
        fcg_features (Dict[str, Any]): FCG特征字典
        embedding (np.ndarray, optional): 程序嵌入向量，默认为None
        sequences (List[List[Any]], optional): 程序序列，默认为None
        output_dir (str): 输出目录，默认为"output/program_features"
        
    返回:
        Dict[str, str]: 保存的文件路径字典
    """
    # 确保输出目录存在
    program_dir = os.path.join(output_dir, program_id)
    ensure_directory(program_dir)
    
    # 保存文件路径字典
    saved_files = {}
    
    # 保存CFG特征
    cfg_filepath = os.path.join(program_dir, "cfg_features")
    cfg_file = save_features_dict(cfg_features, cfg_filepath, format='pickle')
    saved_files['cfg_features'] = cfg_file
    
    # 保存FCG特征
    fcg_filepath = os.path.join(program_dir, "fcg_features")
    fcg_file = save_features_dict(fcg_features, fcg_filepath, format='pickle')
    saved_files['fcg_features'] = fcg_file
    
    # 如果提供了嵌入向量，则保存
    if embedding is not None:
        embedding_filepath = os.path.join(program_dir, "embedding")
        embedding_file = save_numpy_array(embedding, embedding_filepath)
        saved_files['embedding'] = embedding_file
    
    # 如果提供了序列，则保存
    if sequences is not None:
        sequences_filepath = os.path.join(program_dir, "sequences")
        # 将序列转换为可序列化格式
        sequences_dict = {"sequences": sequences}
        sequences_file = save_features_dict(sequences_dict, sequences_filepath, format='pickle')
        saved_files['sequences'] = sequences_file
    
    # 创建并保存元数据
    metadata = {
        "program_id": program_id,
        "timestamp": get_timestamp_str(),
        "features": {
            "cfg_count": len(cfg_features),
            "cfg_functions": list(cfg_features.keys()),
            "fcg_node_count": fcg_features.get("node_count", 0),
            "fcg_edge_count": fcg_features.get("edge_count", 0),
        },
        "files": saved_files
    }
    
    if embedding is not None:
        metadata["features"]["embedding_shape"] = list(embedding.shape)
    
    if sequences is not None:
        metadata["features"]["sequence_count"] = len(sequences)
    
    # 保存元数据
    metadata_filepath = os.path.join(program_dir, "metadata.json")
    with open(metadata_filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    saved_files['metadata'] = metadata_filepath
    
    return saved_files


if __name__ == "__main__":
    print("feature_saver.py - 特征保存工具")
    
    try:
        # 创建临时测试目录
        test_output_dir = "test_output"
        ensure_directory(test_output_dir)
        
        print("\n测试保存NetworkX图...")
        # 创建测试图
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])
        G.nodes[0]['label'] = 'root'
        G.nodes[1]['label'] = 'node1'
        
        # 保存图
        graph_path = os.path.join(test_output_dir, "test_graph")
        saved_graph = save_networkx_graph(G, graph_path)
        print(f"保存的图: {saved_graph}")
        
        print("\n测试保存特征字典...")
        # 创建测试特征字典
        features = {
            'func1': {
                'node_count': 5,
                'edge_count': 6,
                'max_depth': 3,
                'features': np.array([0.1, 0.2, 0.3])
            },
            'func2': {
                'node_count': 3,
                'edge_count': 2,
                'max_depth': 2,
                'features': np.array([0.5, 0.5, 0.0])
            }
        }
        
        # 保存为不同格式
        features_base = os.path.join(test_output_dir, "test_features")
        saved_formats = save_multiple_formats(features, features_base, ['pickle', 'json'])
        print(f"保存的特征格式: {saved_formats}")
        
        print("\n测试保存NumPy数组...")
        # 创建测试NumPy数组
        embedding = np.random.rand(5, 64)
        embedding_path = os.path.join(test_output_dir, "test_embedding")
        saved_embedding = save_numpy_array(embedding, embedding_path)
        print(f"保存的嵌入向量: {saved_embedding}")
        
        print("\n测试保存实验元数据...")
        # 创建测试元数据
        metadata = {
            'experiment': 'test',
            'parameters': {
                'epochs': 100,
                'learning_rate': 0.01,
                'batch_size': 32
            },
            'results': {
                'accuracy': 0.85,
                'f1_score': 0.82
            }
        }
        
        # 保存元数据
        saved_metadata = save_experiment_metadata(metadata, test_output_dir, 'test_experiment')
        print(f"保存的元数据: {saved_metadata}")
        
        print("\n测试保存程序特征...")
        # 创建测试程序特征
        program_id = "test_program"
        cfg_features = {
            'func1': {'node_count': 5, 'cyclomatic': 2},
            'func2': {'node_count': 3, 'cyclomatic': 1}
        }
        fcg_features = {
            'node_count': 2,
            'edge_count': 1,
            'density': 0.5
        }
        program_embedding = np.random.rand(64)
        sequences = [[0, 1, 2], [1, 3, 0]]
        
        # 保存程序特征
        saved_program = save_program_features(
            program_id, cfg_features, fcg_features, 
            program_embedding, sequences, test_output_dir
        )
        print(f"保存的程序特征: {saved_program}")
        
        print("\nfeature_saver.py 测试完成")
    
    except Exception as e:
        print(f"测试时出错: {str(e)}") 