#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ast
import dis
import io
import re
import math
import hashlib
from typing import List, Dict, Set, Tuple, Optional, Union, Any
import networkx as nx
import numpy as np
import torch
from transformers import RobertaTokenizer, RobertaModel

# 常量定义
SENSITIVE_API_PATTERNS = [
    r'os\.(system|popen|exec|spawn|fork)',
    r'subprocess\.(Popen|call|check_output|run)',
    r'eval',
    r'exec',
    r'pickle\.(load|loads)',
    r'marshal\.(load|loads)',
    r'yaml\.load',
    r'requests\.(get|post|put|delete)',
    r'urllib\.(request|urlopen)',
    r'socket\.',
    r'shutil\.(copy|move|rmtree)',
    r'tempfile\.',
    r'random\.',
    r'hashlib\.',
    r'base64\.',
    r'crypt\.',
    r'(read|write)file',
]

# 使用编译好的正则表达式提高性能
SENSITIVE_API_REGEX = re.compile('|'.join(SENSITIVE_API_PATTERNS), re.IGNORECASE)

# 加载CodeBERT模型
_codebert_model = None
_codebert_tokenizer = None

def load_codebert_model(model_path='./structural_features/codebert-base'):
    """
    加载CodeBERT模型
    
    参数:
        model_path (str): 模型路径
        
    返回:
        tuple: (model, tokenizer)
    """
    global _codebert_model, _codebert_tokenizer
    
    if _codebert_model is None or _codebert_tokenizer is None:
        try:
            print(f"正在加载CodeBERT模型，路径: {model_path}")
            tokenizer = RobertaTokenizer.from_pretrained(model_path)
            model = RobertaModel.from_pretrained(model_path)
            model.eval()  # 设置为评估模式
            
            _codebert_model = model
            _codebert_tokenizer = tokenizer
            print("CodeBERT模型加载成功")
        except Exception as e:
            print(f"加载CodeBERT模型时出错: {str(e)}")
            _codebert_model = None
            _codebert_tokenizer = None
    
    return _codebert_model, _codebert_tokenizer


def extract_opcode_sequence(code_block_ast_node: ast.AST) -> List[str]:
    """
    从AST节点推断字节码序列
    
    参数:
        code_block_ast_node (ast.AST): AST节点，通常是函数定义或代码块
        
    返回:
        List[str]: 字节码操作码序列
    """
    if not isinstance(code_block_ast_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
        return []
    
    try:
        # 将AST节点编译成代码对象
        if isinstance(code_block_ast_node, ast.Module):
            code_obj = compile(ast.unparse(code_block_ast_node), '<string>', 'exec')
        else:
            # 对于函数，我们需要先创建一个模块，然后编译它
            module = ast.Module(body=[code_block_ast_node], type_ignores=[])
            code_obj = compile(ast.unparse(module), '<string>', 'exec')
            
            # 获取函数的代码对象
            for const in code_obj.co_consts: 
                if isinstance(const, type(code_obj)) and const.co_name == code_block_ast_node.name: 
                    code_obj = const 
                    break
        
        # 使用dis模块获取字节码
        buffer = io.StringIO()
        dis.dis(code_obj, file=buffer)
        disassembly = buffer.getvalue()
        
        # 提取操作码序列
        opcodes = []
        for line in disassembly.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and parts[0].isdigit():
                # 格式通常是: 行号 操作码 参数
                if len(parts) >= 2:
                    opcodes.append(parts[1])
        
        return opcodes
    except Exception as e:
        print(f"提取字节码序列时出错: {str(e)}")
        return []


def get_code_snippet_raw_text(ast_node: ast.AST, full_code_string: str) -> str:
    """
    获取AST节点对应的代码片段文本
    
    参数:
        ast_node (ast.AST): AST节点
        full_code_string (str): 完整的代码字符串
        
    返回:
        str: 节点对应的代码片段文本
    """
    if not hasattr(ast_node, 'lineno') or not hasattr(ast_node, 'col_offset'):
        return ""
    
    try:
        # 获取节点的起始和结束位置
        start_lineno = ast_node.lineno
        start_col = ast_node.col_offset
        
        # 节点的结束位置（如果有的话）
        end_lineno = getattr(ast_node, 'end_lineno', start_lineno)
        end_col = getattr(ast_node, 'end_col_offset', len(full_code_string.splitlines()[end_lineno-1]))
        
        # 提取代码片段
        lines = full_code_string.splitlines()
        if start_lineno == end_lineno:
            return lines[start_lineno-1][start_col:end_col]
        else:
            result = [lines[start_lineno-1][start_col:]]
            for i in range(start_lineno, end_lineno-1):
                result.append(lines[i])
            result.append(lines[end_lineno-1][:end_col])
            return '\n'.join(result)
    except Exception as e:
        print(f"获取代码片段时出错: {str(e)}")
        return ""


def detect_sensitive_apis(ast_call_node: ast.Call) -> bool:
    """
    检测API调用是否敏感
    
    参数:
        ast_call_node (ast.Call): 表示函数调用的AST节点
        
    返回:
        bool: 如果API调用被识别为敏感，则返回True，否则返回False
    """
    if not isinstance(ast_call_node, ast.Call):
        return False
    
    # 获取调用的函数名
    func_name = ""
    if isinstance(ast_call_node.func, ast.Name):
        # 直接函数调用，例如: eval()
        func_name = ast_call_node.func.id
    elif isinstance(ast_call_node.func, ast.Attribute):
        # 属性调用，例如: os.system()
        attr_parts = []
        current = ast_call_node.func
        while isinstance(current, ast.Attribute):
            attr_parts.insert(0, current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            attr_parts.insert(0, current.id)
        
        func_name = '.'.join(attr_parts)
    
    # 使用正则表达式检测是否匹配敏感API模式
    return bool(SENSITIVE_API_REGEX.search(func_name))


def calculate_cyclomatic_complexity(cfg_networkx_graph: nx.DiGraph) -> int:
    """
    计算给定CFG的圈复杂度
    
    参数:
        cfg_networkx_graph (nx.DiGraph): 控制流图的NetworkX表示
        
    返回:
        int: 圈复杂度值，如果图为空则返回1
    """
    if cfg_networkx_graph is None or cfg_networkx_graph.number_of_nodes() == 0:
        return 1
    
    # 圈复杂度 = 边数 - 节点数 + 2
    edges = cfg_networkx_graph.number_of_edges()
    nodes = cfg_networkx_graph.number_of_nodes()
    
    # 处理特殊情况
    if nodes == 0:
        return 1
    if nodes == 1:
        return 1
    
    complexity = edges - nodes + 2
    return max(1, complexity)  # 复杂度至少为1


def get_text_embedding(text_string: str, model=None, default_dim: int = 16) -> np.ndarray:
    """
    使用预训练的NLP模型（如果提供）将文本转换为向量，
    或者在没有模型的情况下生成基本的哈希嵌入
    
    参数:
        text_string (str): 要嵌入的文本字符串
        model: 预训练的模型对象（可选）
        default_dim (int): 在没有模型的情况下，哈希嵌入的维度
        
    返回:
        np.ndarray: 文本的嵌入向量
    """
    if not text_string:
        return np.zeros(default_dim)
    
    # 首先尝试使用CodeBERT模型
    codebert_model, tokenizer = load_codebert_model()
    if codebert_model is not None and tokenizer is not None:
        try:
            # 使用设备(CPU或GPU)
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            codebert_model.to(device)
            
            # 对文本进行tokenize
            inputs = tokenizer(text_string, return_tensors="pt", max_length=512, 
                              truncation=True, padding="max_length")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # 获取模型输出
            with torch.no_grad():
                outputs = codebert_model(**inputs)
                
            # 获取[CLS]标记的表示作为整个序列的表示
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            # 如果需要调整维度，可以使用PCA或截断/填充
            if embeddings.shape[1] != default_dim:
                # 简单截断或填充
                if embeddings.shape[1] > default_dim:
                    return embeddings[0, :default_dim]
                else:
                    result = np.zeros(default_dim)
                    result[:embeddings.shape[1]] = embeddings[0, :]
                    return result
            
            return embeddings[0]  # 返回第一个样本的嵌入
        except Exception as e:
            print(f"使用CodeBERT生成文本嵌入时出错: {str(e)}")
    
    # 如果提供了其他模型，尝试使用
    if model:
        try:
            # 使用提供的模型获取文本嵌入
            # 具体实现取决于模型类型（例如，Transformer、Word2Vec等）
            return model.get_embeddings(text_string)
        except Exception as e:
            print(f"使用模型生成文本嵌入时出错: {str(e)}")
    
    # 后备方案：使用哈希函数生成基本嵌入
    # 这不是语义嵌入，但可以捕获一些文本特征
    hash_obj = hashlib.md5(text_string.encode())
    hash_digest = hash_obj.digest()
    
    # 将哈希转换为浮点数向量
    hash_values = np.array([b for b in hash_digest], dtype=np.float32)
    
    # 调整向量的维度
    if len(hash_values) < default_dim:
        # 如果维度不够，则重复填充
        hash_values = np.resize(hash_values, default_dim)
    elif len(hash_values) > default_dim:
        # 如果维度过多，则截断
        hash_values = hash_values[:default_dim]
    
    # 归一化到 [-1, 1] 范围
    hash_values = (hash_values / 127.5) - 1.0
    
    return hash_values


def count_ast_node_types(ast_node: ast.AST) -> Dict[str, int]:
    """
    统计AST中不同类型节点的数量
    
    参数:
        ast_node (ast.AST): AST节点（通常是ast.Module或ast.FunctionDef）
        
    返回:
        Dict[str, int]: 节点类型到数量的映射
    """
    if ast_node is None:
        return {}
    
    counter = {}
    
    for node in ast.walk(ast_node):
        node_type = type(node).__name__
        if node_type in counter:
            counter[node_type] += 1
        else:
            counter[node_type] = 1
    
    return counter


def calculate_ast_depth(ast_node: ast.AST) -> int:
    """
    计算AST的最大深度
    
    参数:
        ast_node (ast.AST): AST节点
        
    返回:
        int: AST的最大深度
    """
    if ast_node is None:
        return 0
    
    def _get_depth(node):
        if not hasattr(node, '__dict__') or not node.__dict__:
            return 1
        
        max_child_depth = 0
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        max_child_depth = max(max_child_depth, _get_depth(item))
            elif isinstance(value, ast.AST):
                max_child_depth = max(max_child_depth, _get_depth(value))
        
        return max_child_depth + 1
    
    return _get_depth(ast_node)


def extract_function_metrics(func_def_node: ast.FunctionDef) -> Dict[str, Any]:
    """
    提取函数的各种度量指标
    
    参数:
        func_def_node (ast.FunctionDef): 函数定义的AST节点
        
    返回:
        Dict[str, Any]: 包含各种函数度量指标的字典
    """
    if not isinstance(func_def_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {}
    
    metrics = {
        'name': func_def_node.name, # 函数名
        'args_count': 0, # 参数数量
        'defaults_count': 0,  # 默认参数数量
        'kw_only_count': 0, # 关键字仅参数数量
        'has_var_args': False, # 是否有可变位置参数
        'has_var_kwargs': False,    # 是否有可变关键字参数
        'returns_count': 0, # 返回语句数量
        'docstring_length': 0, # 文档字符串长度
        'body_length': len(func_def_node.body), # 函数体长度
        'decorator_count': len(func_def_node.decorator_list), # 装饰器数量
    }
    
    # 分析参数
    args = func_def_node.args
    metrics['args_count'] = len(args.args)
    metrics['defaults_count'] = len(args.defaults)
    metrics['kw_only_count'] = len(args.kwonlyargs)
    metrics['has_var_args'] = args.vararg is not None
    metrics['has_var_kwargs'] = args.kwarg is not None
    
    # 分析返回语句
    returns_count = 0
    for node in ast.walk(func_def_node):
        if isinstance(node, ast.Return) and node.value is not None:
            returns_count += 1
    metrics['returns_count'] = returns_count
    
    # 查找文档字符串
    if (func_def_node.body and isinstance(func_def_node.body[0], ast.Expr) and 
            isinstance(func_def_node.body[0].value, ast.Str)):
        metrics['docstring_length'] = len(func_def_node.body[0].value.s)
    
    return metrics


def has_dynamic_features(ast_node: ast.AST) -> bool:
    """
    检测代码中是否存在动态特征（如动态导入、反射等）
    
    参数:
        ast_node (ast.AST): AST节点
        
    返回:
        bool: 如果存在动态特征则返回True，否则返回False
    """
    dynamic_features = False
    
    class DynamicFeatureVisitor(ast.NodeVisitor):
        def __init__(self):
            self.has_dynamic = False
        
        def visit_Import(self, node):
            # 检查动态导入
            for alias in node.names:
                if alias.name in ('importlib', 'imp', '__import__'):
                    self.has_dynamic = True
            self.generic_visit(node)
        
        def visit_Call(self, node):
            # 检查动态调用
            if isinstance(node.func, ast.Name):
                if node.func.id in ('eval', 'exec', 'compile', 'globals', 'locals', 'getattr', 'setattr', 'delattr'):
                    self.has_dynamic = True
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ('__import__', 'load_module', 'import_module'):
                    self.has_dynamic = True
            self.generic_visit(node)
    
    visitor = DynamicFeatureVisitor()
    visitor.visit(ast_node)
    
    return visitor.has_dynamic


def get_node_feature_vector(node: Union[ast.AST, nx.DiGraph], full_code: str = None, 
                           embedding_dim: int = 64) -> np.ndarray:
    """
    为AST节点或CFG/FCG图节点生成特征向量
    
    参数:
        node: AST节点或图节点
        full_code: 完整的代码字符串（如果需要）
        embedding_dim: 特征向量的维度
        
    返回:
        np.ndarray: 节点的特征向量
    """
    features = np.zeros(embedding_dim)
    
    if isinstance(node, ast.AST):
        # 处理AST节点
        node_type = type(node).__name__
        
        # 节点类型的哈希值填充到前4个位置
        type_hash = hash(node_type) % (2**31)
        features[0] = (type_hash & 0xFF) / 255.0
        features[1] = ((type_hash >> 8) & 0xFF) / 255.0
        features[2] = ((type_hash >> 16) & 0xFF) / 255.0
        features[3] = ((type_hash >> 24) & 0xFF) / 255.0
        
        # 其他特征
        if hasattr(node, 'lineno'):
            features[4] = min(node.lineno, 1000) / 1000.0  # 归一化行号
        
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            features[5] = len(node.args.args) / 10.0  # 归一化参数数量
            features[6] = len(node.body) / 100.0  # 归一化函数体大小
            features[7] = 1.0 if node.args.vararg else 0.0  # 是否有*args
            features[8] = 1.0 if node.args.kwarg else 0.0  # 是否有**kwargs
        
        if isinstance(node, ast.Call):
            features[9] = len(node.args) / 10.0  # 归一化参数数量
            features[10] = 1.0 if detect_sensitive_apis(node) else 0.0  # 是否是敏感API
        
        # 获取代码片段的文本特征
        if full_code:
            code_snippet = get_code_snippet_raw_text(node, full_code)
            if code_snippet:
                text_embedding = get_text_embedding(code_snippet, default_dim=16)
                features[16:32] = text_embedding  # 将文本嵌入放入特征向量中
    
    elif isinstance(node, dict):
        # 处理图节点（使用节点属性字典）
        if 'node_type' in node: 
            node_type = node['node_type'] 
            type_hash = hash(node_type) % (2**31) # 哈希节点类型
            features[0] = (type_hash & 0xFF) / 255.0  # 归一化到[0, 1]
            features[1] = ((type_hash >> 8) & 0xFF) / 255.0 # 归一化到[0, 1]
        
        if 'code_snippet_raw_text' in node and full_code: # 获取代码片段的原始文本
            text = node['code_snippet_raw_text']
            text_embedding = get_text_embedding(text, default_dim=16) # 获取文本嵌入
            features[16:32] = text_embedding # 将文本嵌入放入特征向量中
        
        if 'has_conditional_branch' in node: # 是否有条件分支
            features[10] = 1.0 if node['has_conditional_branch'] else 0.0 # 是否有条件分支
        
        if 'complexity' in node: # 圈复杂度
            features[11] = min(node['complexity'], 100) / 100.0 # 归一化圈复杂度
    
    return features


if __name__ == "__main__":
    # 简单的测试代码
    import sys
    
    print("feature_extractor.py - 基础特征提取工具")
    print("这是一个辅助工具类，提供各种静态特征提取方法")
    
    # 测试代码片段
    test_code = """
def example_function(a, b=1, *args, **kwargs):
    \"\"\"这是一个示例函数\"\"\"
    if a > 0:
        return a + b
    else:
        return 0
    
    # 这段代码永远不会执行
    import os
    os.system("echo 'Hello'")
"""
    
    # 解析测试代码
    try:
        test_ast = ast.parse(test_code)
        func_node = test_ast.body[0]  # 获取函数定义节点
        
        print("\n1. 提取字节码序列:")
        opcodes = extract_opcode_sequence(func_node)
        print(f"  字节码序列: {opcodes[:5]}... (共 {len(opcodes)} 个)")
        
        print("\n2. 获取代码片段:")
        snippet = get_code_snippet_raw_text(func_node, test_code)
        print(f"  代码片段 (前50个字符): {snippet[:50]}...")
        
        print("\n3. 函数度量指标:")
        metrics = extract_function_metrics(func_node)
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        
        # 测试创建一个简单的CFG图
        test_cfg = nx.DiGraph()
        test_cfg.add_node(0, node_type='ENTRY')
        test_cfg.add_node(1, node_type='IF')
        test_cfg.add_node(2, node_type='RETURN')
        test_cfg.add_node(3, node_type='RETURN')
        test_cfg.add_node(4, node_type='UNREACHABLE')
        
        test_cfg.add_edge(0, 1)
        test_cfg.add_edge(1, 2)
        test_cfg.add_edge(1, 3)
        test_cfg.add_edge(3, 4)
        
        print("\n4. CFG圈复杂度:")
        complexity = calculate_cyclomatic_complexity(test_cfg)
        print(f"  圈复杂度: {complexity}")
        
        # 测试文本嵌入功能
        print("\n5. 测试文本嵌入功能:")
        test_text = "def test_function(): return 42"
        print(f"  测试文本: {test_text}")
        
        # 使用CodeBERT模型生成嵌入
        embedding = get_text_embedding(test_text, default_dim=64)
        print(f"  嵌入向量维度: {embedding.shape}")
        print(f"  嵌入向量前10个值: {embedding[:10]}")
        print(f"  嵌入向量L2范数: {np.linalg.norm(embedding)}")
        
        print("\nfeature_extractor.py 测试完成")
        
    except Exception as e:
        print(f"测试时出错: {str(e)}") 


def extract_functions(ast_node: ast.AST) -> List[ast.FunctionDef]:
    """
    从AST中提取所有函数定义节点
    
    参数:
        ast_node (ast.AST): AST节点（通常是ast.Module）
        
    返回:
        List[ast.FunctionDef]: 函数定义节点列表
    """
    if ast_node is None:
        return []
    
    functions = []
    
    for node in ast.walk(ast_node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node)
    
    return functions 