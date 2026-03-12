#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import networkx as nx
import numpy as np
import torch
from typing import Dict, List, Tuple, Union, Optional, Any, Set
from collections import deque

try:
    import torch_geometric
    from torch_geometric.data import Data as PyGData
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False


def dfs_order(graph: nx.DiGraph, start_node: Any = None) -> List[Any]:
    """
    使用深度优先搜索(DFS)获取图节点的访问顺序
    
    参数:
        graph (nx.DiGraph): 要序列化的有向图
        start_node (Any, optional): 起始节点，如果为None，则使用图的根节点或第一个节点
        
    返回:
        List[Any]: 按DFS顺序排列的节点列表
    """
    if not graph.nodes():
        return []
    
    # 如果未提供起始节点，则使用入度为0的节点或第一个节点
    if start_node is None:
        # 尝试找到入度为0的节点（可能是根节点）
        roots = [node for node, in_degree in graph.in_degree() if in_degree == 0]
        if roots:
            start_node = roots[0]
        else:
            # 如果没有入度为0的节点，使用第一个节点
            start_node = list(graph.nodes())[0]
    
    visited = set()
    result = []
    
    def _dfs(node):
        if node in visited:
            return
        visited.add(node)
        result.append(node)
        for neighbor in sorted(graph.successors(node)):  # 排序确保结果确定性
            _dfs(neighbor)
    
    _dfs(start_node)
    
    # 处理可能的非连通部分
    for node in sorted(graph.nodes()):  # 排序确保结果确定性
        if node not in visited:
            _dfs(node)
    
    return result


def bfs_order(graph: nx.DiGraph, start_node: Any = None) -> List[Any]:
    """
    使用广度优先搜索(BFS)获取图节点的访问顺序
    
    参数:
        graph (nx.DiGraph): 要序列化的有向图
        start_node (Any, optional): 起始节点，如果为None，则使用图的根节点或第一个节点
        
    返回:
        List[Any]: 按BFS顺序排列的节点列表
    """
    if not graph.nodes():
        return []
    
    # 如果未提供起始节点，则使用入度为0的节点或第一个节点
    if start_node is None:
        # 尝试找到入度为0的节点（可能是根节点）
        roots = [node for node, in_degree in graph.in_degree() if in_degree == 0]
        if roots:
            start_node = roots[0]
        else:
            # 如果没有入度为0的节点，使用第一个节点
            start_node = list(graph.nodes())[0]
    
    visited = set([start_node])
    result = [start_node]
    queue = deque([start_node])
    
    while queue:
        node = queue.popleft()
        for neighbor in sorted(graph.successors(node)):  # 排序确保结果确定性
            if neighbor not in visited:
                visited.add(neighbor)
                result.append(neighbor)
                queue.append(neighbor)
    
    # 处理可能的非连通部分
    for node in sorted(graph.nodes()):  # 排序确保结果确定性
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.append(node)
            
            while queue:
                current = queue.popleft()
                for neighbor in sorted(graph.successors(current)):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        result.append(neighbor)
                        queue.append(neighbor)
    
    return result


def topological_order(graph: nx.DiGraph) -> List[Any]:
    """
    获取有向无环图(DAG)的拓扑排序
    
    参数:
        graph (nx.DiGraph): 要序列化的有向图
        
    返回:
        List[Any]: 拓扑排序的节点列表
    """
    try:
        return list(nx.topological_sort(graph))
    except nx.NetworkXUnfeasible:
        # 如果图包含环，退回到DFS顺序
        print("警告: 图含有环，无法进行拓扑排序。退回到DFS顺序。")
        return dfs_order(graph)


def sequence_to_walks(sequence: List[Any], window_size: int = 3) -> List[List[Any]]:
    """
    将节点序列转换为固定窗口大小的游走序列
    
    参数:
        sequence (List[Any]): 节点序列
        window_size (int, optional): 窗口大小，默认为3
        
    返回:
        List[List[Any]]: 游走序列列表
    """
    walks = []
    for i in range(len(sequence) - window_size + 1):
        walk = sequence[i:i + window_size]
        walks.append(walk)
    return walks


def random_walks(graph: nx.DiGraph, 
                 num_walks: int = 10,
                 walk_length: int = 5,
                 restart_prob: float = 0.2) -> List[List[Any]]:
    """
    在图上执行随机游走，生成节点序列
    
    参数:
        graph (nx.DiGraph): 要进行随机游走的图
        num_walks (int, optional): 每个起始节点的游走次数，默认为10
        walk_length (int, optional): 每次游走的长度，默认为5
        restart_prob (float, optional): 重新开始游走的概率，默认为0.2
        
    返回:
        List[List[Any]]: 随机游走序列列表
    """
    walks = []
    nodes = list(graph.nodes())
    
    if not nodes:
        return []
    
    for _ in range(num_walks):
        for start_node in nodes:
            walk = [start_node]
            current_node = start_node
            
            for _ in range(walk_length - 1):
                # 以restart_prob的概率重新开始
                if np.random.random() < restart_prob:
                    current_node = start_node
                    continue
                
                # 获取当前节点的后继节点
                neighbors = list(graph.successors(current_node))
                if not neighbors:
                    break  # 如果没有后继节点，终止游走
                
                # 随机选择一个后继节点
                current_node = np.random.choice(neighbors)
                walk.append(current_node)
            
            # 只添加非空的游走
            if len(walk) > 1:
                walks.append(walk)
    
    return walks


def networkx_to_sequences(graph: nx.DiGraph, 
                         method: str = 'dfs',
                         **kwargs) -> Union[List[Any], List[List[Any]]]:
    """
    将NetworkX图转换为序列
    
    参数:
        graph (nx.DiGraph): 要序列化的图
        method (str, optional): 序列化方法，可选值有'dfs', 'bfs', 'topological', 'random_walks'，默认为'dfs'
        **kwargs: 传递给特定序列化方法的额外参数
        
    返回:
        Union[List[Any], List[List[Any]]]: 根据方法返回单个序列或多个序列
    """
    if method == 'dfs':
        return dfs_order(graph, **kwargs)
    elif method == 'bfs':
        return bfs_order(graph, **kwargs)
    elif method == 'topological':
        return topological_order(graph)
    elif method == 'random_walks':
        return random_walks(graph, **kwargs)
    else:
        raise ValueError(f"不支持的序列化方法: {method}")


def pyg_to_sequences(pyg_data: PyGData, 
                    method: str = 'dfs',
                    **kwargs) -> Union[List[int], List[List[int]]]:
    """
    将PyTorch Geometric图数据转换为序列
    
    参数:
        pyg_data (PyGData): PyTorch Geometric图数据
        method (str, optional): 序列化方法，可选值有'dfs', 'bfs', 'topological', 'random_walks'，默认为'dfs'
        **kwargs: 传递给特定序列化方法的额外参数
        
    返回:
        Union[List[int], List[List[int]]]: 根据方法返回节点索引的单个序列或多个序列
    """
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("请先安装PyTorch Geometric: pip install torch-geometric")
    
    # 将PyG数据转换为NetworkX图
    edge_index = pyg_data.edge_index.cpu().numpy()
    num_nodes = pyg_data.num_nodes
    
    # 创建NetworkX图
    G = nx.DiGraph()
    G.add_nodes_from(range(num_nodes))
    
    # 添加边
    edges = list(zip(edge_index[0], edge_index[1]))
    G.add_edges_from(edges)
    
    # 使用指定方法生成序列
    return networkx_to_sequences(G, method=method, **kwargs)


def sequence_to_features(sequence: List[Any], 
                        node_features: Dict[Any, np.ndarray] = None,
                        aggregation: str = 'concatenate',
                        max_length: Optional[int] = None) -> np.ndarray:
    """
    将序列转换为特征向量
    
    参数:
        sequence (List[Any]): 节点序列
        node_features (Dict[Any, np.ndarray], optional): 节点特征字典，默认为None
        aggregation (str, optional): 特征聚合方法，可选值有'concatenate', 'sum', 'mean', 'max'，默认为'concatenate'
        max_length (int, optional): 最大序列长度，默认为None（不限制长度）
        
    返回:
        np.ndarray: 序列特征向量
    """
    # 如果提供了最大长度，截断序列
    if max_length is not None and len(sequence) > max_length:
        sequence = sequence[:max_length]
    
    # 如果没有提供节点特征，则使用独热编码
    if node_features is None:
        # 获取所有唯一节点
        unique_nodes = set(sequence)
        # 创建节点到索引的映射
        node_to_idx = {node: i for i, node in enumerate(unique_nodes)}
        # 创建独热编码特征
        dim = len(unique_nodes)
        node_features = {
            node: np.eye(dim)[node_to_idx[node]] for node in unique_nodes
        }
    
    # 获取序列中每个节点的特征
    features = [node_features[node] for node in sequence if node in node_features]
    
    # 如果没有有效的特征，则返回空数组
    if not features:
        # 返回一个与节点特征维度相匹配的零向量
        sample_dim = next(iter(node_features.values())).shape[0] if node_features else 0
        return np.zeros(sample_dim)
    
    # 聚合特征
    if aggregation == 'concatenate':
        # 填充或截断以确保一致的长度
        max_features = max_length if max_length is not None else len(features)
        feature_dim = features[0].shape[0]
        padded_features = np.zeros((max_features, feature_dim))
        
        for i, feat in enumerate(features[:max_features]):
            padded_features[i] = feat
            
        return padded_features.flatten()
    
    elif aggregation == 'sum':
        return np.sum(features, axis=0)
    
    elif aggregation == 'mean':
        return np.mean(features, axis=0)
    
    elif aggregation == 'max':
        return np.max(features, axis=0)
    
    else:
        raise ValueError(f"不支持的聚合方法: {aggregation}")


if __name__ == "__main__":
    print("graph_sequentializer.py - 图序列化工具")
    
    # 创建一个简单的示例图
    G = nx.DiGraph()
    G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (3, 5)])
    
    print("\n创建的示例图:")
    print(f"节点: {G.nodes()}")
    print(f"边: {G.edges()}")
    
    print("\n应用不同的序列化方法:")
    print(f"DFS序列: {dfs_order(G)}")
    print(f"BFS序列: {bfs_order(G)}")
    print(f"拓扑序列: {topological_order(G)}")
    
    # 将序列转换为固定窗口大小的游走
    dfs_seq = dfs_order(G)
    walks = sequence_to_walks(dfs_seq, window_size=3)
    print(f"\n从DFS序列生成的窗口游走 (窗口大小=3): {walks}")
    
    # 生成随机游走
    random_walk_seqs = random_walks(G, num_walks=5, walk_length=4)
    print(f"\n随机游走序列 (5次游走, 长度=4): {random_walk_seqs}")
    
    # 创建简单的节点特征
    node_features = {
        0: np.array([1.0, 0.0, 0.0]),
        1: np.array([0.0, 1.0, 0.0]),
        2: np.array([0.0, 0.0, 1.0]),
        3: np.array([0.5, 0.5, 0.0]),
        4: np.array([0.0, 0.5, 0.5]),
        5: np.array([0.5, 0.0, 0.5])
    }
    
    print("\n应用不同的特征聚合方法:")
    print(f"连接特征: {sequence_to_features(dfs_seq, node_features, 'concatenate')}")
    print(f"求和特征: {sequence_to_features(dfs_seq, node_features, 'sum')}")
    print(f"平均特征: {sequence_to_features(dfs_seq, node_features, 'mean')}")
    print(f"最大特征: {sequence_to_features(dfs_seq, node_features, 'max')}")
    
    print("\ngraph_sequentializer.py 测试完成") 