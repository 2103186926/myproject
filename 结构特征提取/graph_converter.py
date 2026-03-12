#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import networkx as nx
from typing import List, Dict, Union, Optional, Tuple, Any

# 尝试导入可能使用的GNN框架
try:
    import torch
    import torch_geometric
    from torch_geometric.data import Data as PyGData
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False

try:
    import dgl
    HAS_DGL = True
except ImportError:
    HAS_DGL = False


def convert_to_pyg_data(networkx_graph: nx.DiGraph, 
                        node_feature_keys: List[str] = None,
                        edge_feature_keys: List[str] = None) -> Any:
    """
    将NetworkX图转换为PyTorch Geometric的Data对象
    
    参数:
        networkx_graph (nx.DiGraph): 待转换的NetworkX图
        node_feature_keys (List[str], optional): 用作节点特征的节点属性列表
        edge_feature_keys (List[str], optional): 用作边特征的边属性列表
        
    返回:
        torch_geometric.data.Data: PyTorch Geometric的图数据对象
    
    异常:
        ImportError: 如果PyTorch Geometric未安装
    """
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("请先安装PyTorch Geometric: pip install torch-geometric")
    
    # 如果未指定特征键，则使用'initial_feature_vector'（如果存在）
    if node_feature_keys is None:
        if networkx_graph.number_of_nodes() > 0 and 'initial_feature_vector' in next(iter(networkx_graph.nodes(data=True)))[1]:
            node_feature_keys = ['initial_feature_vector']
        else:
            node_feature_keys = []
    
    if edge_feature_keys is None:
        if networkx_graph.number_of_edges() > 0 and 'initial_feature_vector' in next(iter(networkx_graph.edges(data=True)))[2]:
            edge_feature_keys = ['initial_feature_vector']
        else:
            edge_feature_keys = []
    
    # 创建节点索引映射
    node_mapping = {node: i for i, node in enumerate(networkx_graph.nodes())}
    
    # 构建边索引
    edge_index = []
    for source, target in networkx_graph.edges():
        edge_index.append([node_mapping[source], node_mapping[target]])
    
    if not edge_index:  # 处理无边的图
        edge_index = torch.zeros((2, 0), dtype=torch.long)
    else:
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    
    # 构建节点特征矩阵
    x = None
    if node_feature_keys:
        node_features = []
        for node in networkx_graph.nodes(data=True):
            node_data = node[1]
            node_feature = []
            
            for key in node_feature_keys:
                if key in node_data:
                    # 如果特征是向量/数组，则直接使用
                    if isinstance(node_data[key], (list, np.ndarray)):
                        node_feature.extend(node_data[key])
                    # 如果特征是标量，则转换为单一元素列表
                    else:
                        node_feature.append(float(node_data[key]))
            
            # 如果没有特征，则使用零向量
            if not node_feature:
                node_feature = [0.0]
                
            node_features.append(node_feature)
        
        # 调整所有节点特征向量为同一长度（使用最长的）
        max_features_len = max(len(f) for f in node_features)
        for i in range(len(node_features)):
            if len(node_features[i]) < max_features_len:
                node_features[i].extend([0.0] * (max_features_len - len(node_features[i])))
        
        x = torch.tensor(node_features, dtype=torch.float)
    else:
        # 如果没有指定特征，则使用单位特征
        x = torch.ones((networkx_graph.number_of_nodes(), 1), dtype=torch.float)
    
    # 构建边特征矩阵
    edge_attr = None
    if edge_feature_keys and networkx_graph.number_of_edges() > 0:
        edge_features = []
        for source, target, edge_data in networkx_graph.edges(data=True):
            edge_feature = []
            
            for key in edge_feature_keys:
                if key in edge_data:
                    # 如果特征是向量/数组，则直接使用
                    if isinstance(edge_data[key], (list, np.ndarray)):
                        edge_feature.extend(edge_data[key])
                    # 如果特征是标量，则转换为单一元素列表
                    else:
                        edge_feature.append(float(edge_data[key]))
            
            # 如果没有特征，则使用零向量
            if not edge_feature:
                edge_feature = [0.0]
                
            edge_features.append(edge_feature)
        
        # 调整所有边特征向量为同一长度
        if edge_features:
            max_features_len = max(len(f) for f in edge_features)
            for i in range(len(edge_features)):
                if len(edge_features[i]) < max_features_len:
                    edge_features[i].extend([0.0] * (max_features_len - len(edge_features[i])))
            
            edge_attr = torch.tensor(edge_features, dtype=torch.float)
    
    # 确保始终创建edge_attr，即使没有边特征
    if edge_attr is None:
        if edge_index.size(1) > 0:
            # 创建1维的默认特征（全为0）
            edge_attr = torch.zeros((edge_index.size(1), 1), dtype=torch.float)
        else:
            # 如果没有边，则创建0×1的空张量
            edge_attr = torch.zeros((0, 1), dtype=torch.float)
    
    # 创建PyG数据对象
    pyg_data = PyGData(x=x, edge_index=edge_index, edge_attr=edge_attr)
    
    # 保留原始图的其他属性
    for key, value in networkx_graph.graph.items():
        pyg_data[key] = value
    
    return pyg_data


def convert_to_dgl_graph(networkx_graph: nx.DiGraph,
                        node_feature_keys: List[str] = None,
                        edge_feature_keys: List[str] = None) -> Any:
    """
    将NetworkX图转换为DGL的图对象
    
    参数:
        networkx_graph (nx.DiGraph): 待转换的NetworkX图
        node_feature_keys (List[str], optional): 用作节点特征的节点属性列表
        edge_feature_keys (List[str], optional): 用作边特征的边属性列表
        
    返回:
        dgl.DGLGraph: DGL的图数据对象
    
    异常:
        ImportError: 如果DGL未安装
    """
    if not HAS_DGL:
        raise ImportError("请先安装DGL: pip install dgl")
    
    # 如果未指定特征键，则使用'initial_feature_vector'（如果存在）
    if node_feature_keys is None:
        if networkx_graph.number_of_nodes() > 0 and 'initial_feature_vector' in next(iter(networkx_graph.nodes(data=True)))[1]:
            node_feature_keys = ['initial_feature_vector']
        else:
            node_feature_keys = []
    
    if edge_feature_keys is None:
        if networkx_graph.number_of_edges() > 0 and 'initial_feature_vector' in next(iter(networkx_graph.edges(data=True)))[2]:
            edge_feature_keys = ['initial_feature_vector']
        else:
            edge_feature_keys = []
    
    # 创建DGL图
    dgl_graph = dgl.from_networkx(networkx_graph)
    
    # 添加节点特征
    if node_feature_keys:
        node_features = []
        for node in networkx_graph.nodes(data=True):
            node_data = node[1]
            node_feature = []
            
            for key in node_feature_keys:
                if key in node_data:
                    # 如果特征是向量/数组，则直接使用
                    if isinstance(node_data[key], (list, np.ndarray)):
                        node_feature.extend(node_data[key])
                    # 如果特征是标量，则转换为单一元素列表
                    else:
                        node_feature.append(float(node_data[key]))
            
            # 如果没有特征，则使用零向量
            if not node_feature:
                node_feature = [0.0]
                
            node_features.append(node_feature)
        
        # 调整所有节点特征向量为同一长度
        max_features_len = max(len(f) for f in node_features)
        for i in range(len(node_features)):
            if len(node_features[i]) < max_features_len:
                node_features[i].extend([0.0] * (max_features_len - len(node_features[i])))
        
        dgl_graph.ndata['feat'] = torch.tensor(node_features, dtype=torch.float)
    else:
        # 如果没有指定特征，则使用单位特征
        dgl_graph.ndata['feat'] = torch.ones((networkx_graph.number_of_nodes(), 1), dtype=torch.float)
    
    # 添加边特征
    if edge_feature_keys and networkx_graph.number_of_edges() > 0:
        # 按照DGL图的边顺序重新排列边（DGL在从NetworkX转换时可能会改变边顺序）
        edge_features = []
        edge_list = list(networkx_graph.edges(data=True))
        edge_dict = {(s, t): d for s, t, d in edge_list}
        
        # 获取DGL图的边顺序
        src, dst = dgl_graph.edges()
        src = src.numpy()
        dst = dst.numpy()
        
        # 对应DGL图中的边按原始NetworkX边顺序构建特征
        for i in range(len(src)):
            s, t = src[i], dst[i]
            # 获取原始节点id（DGL可能重新编号）
            source = list(networkx_graph.nodes())[s]
            target = list(networkx_graph.nodes())[t]
            
            if (source, target) in edge_dict:
                edge_data = edge_dict[(source, target)]
                edge_feature = []
                
                for key in edge_feature_keys:
                    if key in edge_data:
                        # 如果特征是向量/数组，则直接使用
                        if isinstance(edge_data[key], (list, np.ndarray)):
                            edge_feature.extend(edge_data[key])
                        # 如果特征是标量，则转换为单一元素列表
                        else:
                            edge_feature.append(float(edge_data[key]))
                
                # 如果没有特征，则使用零向量
                if not edge_feature:
                    edge_feature = [0.0]
            else:
                # 如果找不到边（DGL和NetworkX边顺序不匹配），使用零向量
                edge_feature = [0.0]
                
            edge_features.append(edge_feature)
        
        # 调整所有边特征向量为同一长度
        if edge_features:
            max_features_len = max(len(f) for f in edge_features)
            for i in range(len(edge_features)):
                if len(edge_features[i]) < max_features_len:
                    edge_features[i].extend([0.0] * (max_features_len - len(edge_features[i])))
            
            dgl_graph.edata['feat'] = torch.tensor(edge_features, dtype=torch.float)
    
    return dgl_graph


def convert_to_gnn_data(networkx_graph: nx.DiGraph,
                       node_feature_keys: List[str] = None,
                       edge_feature_keys: List[str] = None,
                       framework: str = 'pyg') -> Any:
    """
    将NetworkX图转换为指定GNN框架的数据对象
    
    参数:
        networkx_graph (nx.DiGraph): 待转换的NetworkX图
        node_feature_keys (List[str], optional): 用作节点特征的节点属性列表
        edge_feature_keys (List[str], optional): 用作边特征的边属性列表
        framework (str): 要使用的GNN框架，'pyg'或'dgl'
        
    返回:
        Any: GNN框架的图数据对象
        
    异常:
        ValueError: 如果指定的框架不受支持
        ImportError: 如果所需的框架未安装
    """
    if framework.lower() == 'pyg':
        return convert_to_pyg_data(networkx_graph, node_feature_keys, edge_feature_keys)
    elif framework.lower() == 'dgl':
        return convert_to_dgl_graph(networkx_graph, node_feature_keys, edge_feature_keys)
    else:
        raise ValueError(f"不支持的GNN框架: {framework}。请使用'pyg'或'dgl'。")


if __name__ == "__main__":
    # 简单的测试代码
    import sys
    
    # 创建一个简单的测试图
    test_graph = nx.DiGraph()
    
    # 添加节点
    test_graph.add_node(0, node_type='ENTRY', initial_feature_vector=np.array([1.0, 0.0, 0.0]))
    test_graph.add_node(1, node_type='IF', initial_feature_vector=np.array([0.0, 1.0, 0.0]))
    test_graph.add_node(2, node_type='RETURN', initial_feature_vector=np.array([0.0, 0.0, 1.0]))
    
    # 添加边
    test_graph.add_edge(0, 1, edge_type='FLOW', initial_feature_vector=np.array([1.0, 0.0]))
    test_graph.add_edge(1, 2, edge_type='TRUE_BRANCH', initial_feature_vector=np.array([0.0, 1.0]))
    
    print("测试NetworkX到GNN框架的转换...")
    
    # 尝试PyG转换
    try:
        pyg_data = convert_to_gnn_data(test_graph, framework='pyg')
        print("\nPyTorch Geometric转换结果:")
        print(f"  节点数: {pyg_data.num_nodes}")
        print(f"  边数: {pyg_data.num_edges}")
        print(f"  节点特征形状: {list(pyg_data.x.shape)}")
        if pyg_data.edge_attr is not None:
            print(f"  边特征形状: {list(pyg_data.edge_attr.shape)}")
    except ImportError:
        print("  PyTorch Geometric未安装，跳过测试")
    
    # 尝试DGL转换
    try:
        dgl_graph = convert_to_gnn_data(test_graph, framework='dgl')
        print("\nDGL转换结果:")
        print(f"  节点数: {dgl_graph.num_nodes()}")
        print(f"  边数: {dgl_graph.num_edges()}")
        print(f"  节点特征形状: {list(dgl_graph.ndata['feat'].shape)}")
        if 'feat' in dgl_graph.edata:
            print(f"  边特征形状: {list(dgl_graph.edata['feat'].shape)}")
    except ImportError:
        print("  DGL未安装，跳过测试")
        
    print("\ngraph_converter.py 测试完成") 