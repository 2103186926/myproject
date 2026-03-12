#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import torch
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

try:
    import torch_geometric
    from torch_geometric.data import Data as PyGData
    HAS_TORCH_GEOMETRIC = True
except ImportError:
    HAS_TORCH_GEOMETRIC = False


def generate_program_node_embeddings(trained_cfg_gnn_model: torch.nn.Module, 
                                    trained_fcg_gnn_model: torch.nn.Module,
                                    program_cfg_data_map: Dict[str, List[PyGData]],
                                    program_fcg_data_map: Dict[str, PyGData],
                                    device: Optional[torch.device] = None) -> Dict[str, torch.Tensor]:
    """
    使用训练好的GNN模型为每个程序的FCG节点生成嵌入向量
    
    参数:
        trained_cfg_gnn_model (torch.nn.Module): 训练好的CFG GNN模型
        trained_fcg_gnn_model (torch.nn.Module): 训练好的FCG GNN模型
        program_cfg_data_map (Dict[str, List[PyGData]]): 映射程序ID到其包含的所有CFG图数据列表
        program_fcg_data_map (Dict[str, PyGData]): 映射程序ID到其FCG图数据
        device (torch.device, optional): 计算设备，默认为None（会自动检测）
        
    返回:
        Dict[str, torch.Tensor]: 映射程序ID到该程序的FCG节点嵌入向量矩阵
    """
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("请先安装PyTorch Geometric: pip install torch-geometric")
    
    # 设置计算设备
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 确保模型在评估模式
    trained_cfg_gnn_model.eval()
    trained_fcg_gnn_model.eval()
    
    print(f"使用设备: {device} 生成程序嵌入")
    
    # 确保模型在评估模式
    trained_cfg_gnn_model.eval()
    trained_fcg_gnn_model.eval()
    
    # 将模型移到指定设备上
    trained_cfg_gnn_model = trained_cfg_gnn_model.to(device)
    trained_fcg_gnn_model = trained_fcg_gnn_model.to(device)
    
    # 存储每个程序的FCG节点嵌入
    program_embeddings = {}
    
    for program_id, fcg_data in program_fcg_data_map.items():
        print(f"生成程序 {program_id} 的嵌入...")
        
        # 1. 准备CFG嵌入字典
        cfg_embeddings_dict = {}
        
        # 如果程序有CFG数据
        if program_id in program_cfg_data_map:
            cfg_data_list = program_cfg_data_map[program_id]
            
            # 对每个CFG生成嵌入
            for cfg_data in cfg_data_list:
                function_name = cfg_data.function_name if hasattr(cfg_data, 'function_name') else None
                
                if function_name is not None:
                    # 将数据移到设备上
                    cfg_data = cfg_data.to(device)
                    
                    # 使用CFG GNN模型生成图级嵌入
                    with torch.no_grad():
                        _, graph_embedding, _ = trained_cfg_gnn_model(cfg_data.x, cfg_data.edge_index, None)
                        
                    # 如果生成了有效的嵌入，则存储它
                    if graph_embedding is not None:
                        cfg_embeddings_dict[function_name] = graph_embedding
        
        # 2. 增强FCG节点特征
        # 将FCG数据移到设备上
        fcg_data = fcg_data.to(device)
        
        # 准备增强的FCG节点特征
        new_x_list = []
        
        # 遍历FCG中的每个节点
        for node_idx in range(fcg_data.num_nodes):
            # 获取函数名（如果有）
            if hasattr(fcg_data, 'function_names'):
                function_name = fcg_data.function_names[node_idx]
            else:
                function_name = None
            
            # 获取对应的CFG嵌入
            cfg_embedding = None
            if function_name is not None and function_name in cfg_embeddings_dict:
                cfg_embedding = cfg_embeddings_dict[function_name]
            
            # 如果没有对应的CFG嵌入，则使用零向量
            if cfg_embedding is None:
                cfg_embedding = torch.zeros(trained_cfg_gnn_model.out_channels, device=device)
            
            # 获取原始FCG节点特征
            orig_feature = fcg_data.x[node_idx]
            
            # 将CFG嵌入与原始FCG节点特征拼接
            new_feature = torch.cat([orig_feature, cfg_embedding])
            new_x_list.append(new_feature)
        
        # 3. 创建增强后的FCG数据
        new_x = torch.stack(new_x_list)
        
        enriched_fcg_data = PyGData(
            x=new_x,
            edge_index=fcg_data.edge_index,
            edge_attr=fcg_data.edge_attr if hasattr(fcg_data, 'edge_attr') else None
        ).to(device)
        
        # 4. 使用FCG GNN模型生成节点嵌入
        with torch.no_grad():
            node_embeddings, _, _ = trained_fcg_gnn_model(enriched_fcg_data.x, enriched_fcg_data.edge_index, None)
            
        # 5. 存储节点嵌入
        program_embeddings[program_id] = node_embeddings.cpu()
    
    return program_embeddings


def generate_batch_program_embeddings(trained_cfg_gnn_model: torch.nn.Module,
                                     trained_fcg_gnn_model: torch.nn.Module,
                                     program_data: List[Tuple[str, Dict[str, Any], PyGData]],
                                     batch_size: int = 8,
                                     device: Optional[torch.device] = None) -> Dict[str, torch.Tensor]:
    """
    批量生成程序嵌入向量
    
    参数:
        trained_cfg_gnn_model (torch.nn.Module): 训练好的CFG GNN模型
        trained_fcg_gnn_model (torch.nn.Module): 训练好的FCG GNN模型
        program_data (List[Tuple[str, Dict[str, Any], PyGData]]): 程序数据，每个元素包含(程序ID, CFG数据字典, FCG数据)
        batch_size (int): 批量处理的大小
        device (torch.device, optional): 计算设备，默认为None（会自动检测）
        
    返回:
        Dict[str, torch.Tensor]: 映射程序ID到该程序的FCG节点嵌入向量矩阵
    """
    if not HAS_TORCH_GEOMETRIC:
        raise ImportError("请先安装PyTorch Geometric: pip install torch-geometric")
    
    # 设置计算设备
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 确保模型在评估模式
    trained_cfg_gnn_model.eval()
    trained_fcg_gnn_model.eval()
    
    # 将模型移到指定设备上
    trained_cfg_gnn_model = trained_cfg_gnn_model.to(device)
    trained_fcg_gnn_model = trained_fcg_gnn_model.to(device)
    
    # 存储每个程序的FCG节点嵌入
    program_embeddings = {}
    
    # 分批处理
    for i in range(0, len(program_data), batch_size):
        batch = program_data[i:i + batch_size]
        
        for program_id, cfg_data_dict, fcg_data in batch:
            print(f"生成程序 {program_id} 的嵌入...")
            
            # 1. 准备CFG嵌入字典
            cfg_embeddings_dict = {}
            
            # 遍历每个函数的CFG数据
            for function_name, cfg_data in cfg_data_dict.items():
                # 将数据移到设备上
                cfg_data = cfg_data.to(device)
                
                # 使用CFG GNN模型生成图级嵌入
                with torch.no_grad():
                    _, graph_embedding, _ = trained_cfg_gnn_model(cfg_data.x, cfg_data.edge_index, None)
                    
                # 如果生成了有效的嵌入，则存储它
                if graph_embedding is not None:
                    cfg_embeddings_dict[function_name] = graph_embedding
            
            # 2. 增强FCG节点特征
            # 将FCG数据移到设备上
            fcg_data = fcg_data.to(device)
            
            # 准备增强的FCG节点特征
            new_x_list = []
            
            # 遍历FCG中的每个节点
            for node_idx in range(fcg_data.num_nodes):
                # 获取函数名（如果有）
                if hasattr(fcg_data, 'function_names'):
                    function_name = fcg_data.function_names[node_idx]
                else:
                    function_name = None
                
                # 获取对应的CFG嵌入
                cfg_embedding = None
                if function_name is not None and function_name in cfg_embeddings_dict:
                    cfg_embedding = cfg_embeddings_dict[function_name]
                
                # 如果没有对应的CFG嵌入，则使用零向量
                if cfg_embedding is None:
                    cfg_embedding = torch.zeros(trained_cfg_gnn_model.out_channels, device=device)
                
                # 获取原始FCG节点特征
                orig_feature = fcg_data.x[node_idx]
                
                # 将CFG嵌入与原始FCG节点特征拼接
                new_feature = torch.cat([orig_feature, cfg_embedding])
                new_x_list.append(new_feature)
            
            # 3. 创建增强后的FCG数据
            if new_x_list:  # 确保列表非空
                new_x = torch.stack(new_x_list)
                
                enriched_fcg_data = PyGData(
                    x=new_x,
                    edge_index=fcg_data.edge_index,
                    edge_attr=fcg_data.edge_attr if hasattr(fcg_data, 'edge_attr') else None
                ).to(device)
                
                # 4. 使用FCG GNN模型生成节点嵌入
                with torch.no_grad():
                    node_embeddings, _, _ = trained_fcg_gnn_model(enriched_fcg_data.x, enriched_fcg_data.edge_index, None)
                    
                # 5. 存储节点嵌入
                program_embeddings[program_id] = node_embeddings.cpu()
            else:
                # 如果没有节点，则使用空向量
                program_embeddings[program_id] = torch.zeros((0, trained_fcg_gnn_model.out_channels))
                print(f"警告：程序 {program_id} 的FCG没有节点")
    
    return program_embeddings


def export_embeddings_to_numpy(program_embeddings: Dict[str, torch.Tensor], 
                              output_dir: str, 
                              file_prefix: str = "program_embedding_") -> Dict[str, str]:
    """
    将程序嵌入向量导出为NumPy数组文件
    
    参数:
        program_embeddings (Dict[str, torch.Tensor]): 映射程序ID到嵌入向量的字典
        output_dir (str): 输出目录路径
        file_prefix (str, optional): 输出文件名前缀，默认为"program_embedding_"
        
    返回:
        Dict[str, str]: 映射程序ID到对应的输出文件路径
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 存储每个程序的输出文件路径
    output_files = {}
    
    # 遍历每个程序的嵌入向量
    for program_id, embedding in program_embeddings.items():
        # 转换为NumPy数组
        embedding_np = embedding.cpu().numpy()
        
        # 构建输出文件路径
        output_file = os.path.join(output_dir, f"{file_prefix}{program_id}.npy")
        
        # 保存为NumPy数组文件
        np.save(output_file, embedding_np)
        
        # 存储输出文件路径
        output_files[program_id] = output_file
    
    return output_files


if __name__ == "__main__":
    print("graph_embedding_generator.py - 图嵌入生成工具")
    
    # 检查PyTorch Geometric是否可用
    if not HAS_TORCH_GEOMETRIC:
        print("警告: PyTorch Geometric未安装，无法运行测试")
        exit(0)
    
    try:
        # 这里只是一个简单的测试，实际使用时需要加载训练好的模型和数据
        from gnn_trainer import CFGGNN, FCGGNN
        from torch_geometric.data import Data
        
        print("\n创建测试模型和数据...")
        
        # 创建测试模型
        cfg_gnn_model = CFGGNN(in_channels=16, hidden_channels=32, out_channels=64, num_layers=2)
        fcg_gnn_model = FCGGNN(in_channels=16+64, hidden_channels=32, out_channels=64, num_layers=2)
        
        # 创建测试数据
        # 程序1的CFG
        cfg_data1_1 = Data(
            x=torch.randn(5, 16),
            edge_index=torch.tensor([[0, 1, 1, 2, 2, 3, 4], [1, 2, 3, 3, 4, 4, 0]], dtype=torch.long),
            function_name="func1"
        )
        
        cfg_data1_2 = Data(
            x=torch.randn(4, 16),
            edge_index=torch.tensor([[0, 0, 1, 2], [1, 2, 3, 3]], dtype=torch.long),
            function_name="func2"
        )
        
        # 程序1的FCG
        fcg_data1 = Data(
            x=torch.randn(2, 16),
            edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
            function_names=["func1", "func2"]
        )
        
        # 程序2的CFG
        cfg_data2_1 = Data(
            x=torch.randn(3, 16),
            edge_index=torch.tensor([[0, 0, 1], [1, 2, 2]], dtype=torch.long),
            function_name="func3"
        )
        
        # 程序2的FCG
        fcg_data2 = Data(
            x=torch.randn(1, 16),
            edge_index=torch.zeros((2, 0), dtype=torch.long),
            function_names=["func3"]
        )
        
        # 创建程序数据映射
        program_cfg_data_map = {
            "program1": [cfg_data1_1, cfg_data1_2],
            "program2": [cfg_data2_1]
        }
        
        program_fcg_data_map = {
            "program1": fcg_data1,
            "program2": fcg_data2
        }
        
        # 使用CPU设备进行测试
        device = torch.device('cpu')
        
        print("生成程序节点嵌入...")
        # 生成程序节点嵌入
        program_embeddings = generate_program_node_embeddings(
            cfg_gnn_model, fcg_gnn_model, program_cfg_data_map, program_fcg_data_map, device
        )
        
        print("\n程序嵌入结果:")
        for program_id, embedding in program_embeddings.items():
            print(f"程序 {program_id}: 嵌入形状 = {list(embedding.shape)}")
        
        print("\n导出嵌入到NumPy文件...")
        # 创建临时输出目录
        temp_output_dir = "temp_output"
        output_files = export_embeddings_to_numpy(program_embeddings, temp_output_dir)
        
        print("\n导出的文件:")
        for program_id, file_path in output_files.items():
            print(f"程序 {program_id}: {file_path}")
            
            # 验证导出的文件
            loaded_embedding = np.load(file_path)
            print(f"  加载的嵌入形状: {loaded_embedding.shape}")
        
        print("\ngraph_embedding_generator.py 测试完成")
        
    except Exception as e:
        print(f"测试时出错: {str(e)}") 