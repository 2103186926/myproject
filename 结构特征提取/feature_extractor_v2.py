#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化的特征提取模块
增强容器逃逸检测相关特征
"""

import os
import ast
import dis
import io
import re
import hashlib
from typing import List, Dict, Set, Tuple, Optional, Union, Any
import networkx as nx
import numpy as np
import torch
from transformers import RobertaTokenizer, RobertaModel
from config import Config, get_default_config


class FeatureExtractor:
    """特征提取器类"""
    
    def __init__(self, config: Optional[Config] = None):
        """
        初始化特征提取器
        
        参数:
            config: 配置对象
        """
        self.config = config or get_default_config()
        self.codebert_model = None
        self.codebert_tokenizer = None
        self.projection_layer = None  # 线性投影层（768 -> 256）
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 编译敏感API正则表达式
        self.sensitive_api_regex = re.compile(
            '|'.join(self.config.container_escape.sensitive_api_patterns),
            re.IGNORECASE
        )
        
        # 编译敏感路径正则表达式
        self.sensitive_path_regex = re.compile(
            '|'.join(self.config.container_escape.sensitive_path_patterns),
            re.IGNORECASE
        )
        
        # 加载CodeBERT模型
        if self.config.model.use_codebert:
            self._load_codebert()
    
    def _load_codebert(self) -> None:
        """加载CodeBERT模型和降维投影层"""
        try:
            model_type = self.config.model.embedding_model_type
            model_path = self.config.model.codebert_model_path
            
            print(f"正在加载文本嵌入模型: {model_type}")
            print(f"模型路径: {model_path}")
            
            # 验证模型路径是否存在
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型路径不存在: {model_path}")
            
            self.codebert_tokenizer = RobertaTokenizer.from_pretrained(model_path)
            self.codebert_model = RobertaModel.from_pretrained(model_path)
            self.codebert_model.to(self.device)
            
            # 根据配置决定是否冻结CodeBERT参数
            if not self.config.model.codebert_finetune:
                # 不微调：冻结CodeBERT参数
                self.codebert_model.eval()
                for param in self.codebert_model.parameters():
                    param.requires_grad = False
                print(f"{model_type} 参数已冻结（不微调）")
            else:
                # 微调：保持参数可训练
                self.codebert_model.train()
                print(f"{model_type} 参数可训练（微调模式）")
            
            # 添加线性投影层（768 -> text_embedding_dim）
            if self.config.model.codebert_use_projection:
                codebert_output_dim = 768  # CodeBERT系列模型默认输出维度
                target_dim = self.config.model.text_embedding_dim
                
                if target_dim < codebert_output_dim:
                    self.projection_layer = torch.nn.Linear(codebert_output_dim, target_dim)
                    self.projection_layer.to(self.device)
                    # 投影层始终可训练，用于学习最优降维
                    self.projection_layer.train()
                    print(f"已添加线性投影层: {codebert_output_dim} -> {target_dim}")
                else:
                    self.projection_layer = None
                    print(f"目标维度({target_dim}) >= 模型输出维度({codebert_output_dim})，不使用投影层")
            else:
                self.projection_layer = None
                print("未启用投影层（将使用截断或填充）")
            
            print(f"{model_type} 模型加载成功")
            
            # 打印模型信息
            print(f"\n模型信息:")
            print(f"  模型类型: {model_type}")
            print(f"  模型路径: {model_path}")
            print(f"  输出维度: {codebert_output_dim}")
            print(f"  目标维度: {target_dim}")
            print(f"  是否微调: {self.config.model.codebert_finetune}")
            print(f"  使用投影层: {self.projection_layer is not None}")
            
        except Exception as e:
            print(f"加载文本嵌入模型失败: {e}")
            print("将使用简单的哈希嵌入作为替代")
            self.codebert_model = None
            self.codebert_tokenizer = None
            self.projection_layer = None
    
    def extract_opcode_sequence(self, code_block_ast: ast.AST) -> List[str]:
        """提取字节码序列"""
        if not isinstance(code_block_ast, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
            return []
        
        try:
            if isinstance(code_block_ast, ast.Module):
                code_obj = compile(ast.unparse(code_block_ast), '<string>', 'exec')
            else:
                module = ast.Module(body=[code_block_ast], type_ignores=[])
                code_obj = compile(ast.unparse(module), '<string>', 'exec')
                
                for const in code_obj.co_consts:
                    if isinstance(const, type(code_obj)) and const.co_name == code_block_ast.name:
                        code_obj = const
                        break
            
            buffer = io.StringIO()
            dis.dis(code_obj, file=buffer)
            disassembly = buffer.getvalue()
            
            opcodes = []
            for line in disassembly.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0].isdigit():
                    opcodes.append(parts[1])
            
            return opcodes
        except Exception as e:
            return []
    
    def get_code_snippet(self, ast_node: ast.AST, full_code: str) -> str:
        """获取AST节点对应的代码片段"""
        if not hasattr(ast_node, 'lineno'):
            return ""
        
        try:
            start_lineno = ast_node.lineno
            start_col = ast_node.col_offset
            end_lineno = getattr(ast_node, 'end_lineno', start_lineno)
            end_col = getattr(ast_node, 'end_col_offset', len(full_code.splitlines()[end_lineno-1]))
            
            lines = full_code.splitlines()
            if start_lineno == end_lineno:
                return lines[start_lineno-1][start_col:end_col]
            else:
                result = [lines[start_lineno-1][start_col:]]
                for i in range(start_lineno, end_lineno-1):
                    result.append(lines[i])
                result.append(lines[end_lineno-1][:end_col])
                return '\n'.join(result)
        except Exception:
            return ""
    
    def detect_sensitive_api(self, ast_call: ast.Call) -> Tuple[bool, str]:
        """
        检测敏感API调用
        
        返回:
            (是否敏感, 匹配的模式)
        """
        if not isinstance(ast_call, ast.Call):
            return False, ""
        
        func_name = self._get_call_name(ast_call)
        if not func_name:
            return False, ""
        
        match = self.sensitive_api_regex.search(func_name)  # 敏感api正则匹配
        if match:
            return True, match.group(0)
        
        return False, ""
    
    def detect_sensitive_path(self, code_snippet: str) -> Tuple[bool, List[str]]:
        """
        检测敏感路径访问
        
        返回:
            (是否包含敏感路径, 匹配的路径列表)
        """
        matches = self.sensitive_path_regex.findall(code_snippet)
        return len(matches) > 0, matches
    
    def _get_call_name(self, ast_call: ast.Call) -> str:
        """获取函数调用的完整名称"""
        if isinstance(ast_call.func, ast.Name):  # 变量名
            return ast_call.func.id
        elif isinstance(ast_call.func, ast.Attribute):  # 属性访问
            parts = []
            current = ast_call.func
            while isinstance(current, ast.Attribute):
                parts.insert(0, current.attr)
                current = current.value
            
            if isinstance(current, ast.Name):
                parts.insert(0, current.id)
            
            return '.'.join(parts)
        return ""
    
    def calculate_cyclomatic_complexity(self, cfg: nx.DiGraph) -> int:
        """计算圈复杂度"""
        if cfg is None or cfg.number_of_nodes() == 0:
            return 1
        
        edges = cfg.number_of_edges()
        nodes = cfg.number_of_nodes()
        
        if nodes <= 1:
            return 1
        
        # McCabe圈复杂度: E - N + 2P (P为连通分量数，通常为1)
        complexity = edges - nodes + 2
        return max(1, complexity)
    
    def get_text_embedding(self, text: str) -> np.ndarray:
        """
        获取文本的嵌入向量（优化版：使用线性投影降维）
        支持多种文本嵌入模型
        
        返回:
            嵌入向量 (维度: text_embedding_dim)
        """
        if not text:
            return np.zeros(self.config.model.text_embedding_dim)
        
        # 使用选定的文本嵌入模型
        if self.codebert_model is not None and self.codebert_tokenizer is not None:
            try:
                inputs = self.codebert_tokenizer(
                    text,
                    return_tensors="pt",
                    max_length=self.config.model.codebert_max_length,
                    truncation=True,
                    padding="max_length"
                )
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # 根据是否微调决定是否使用梯度
                if self.config.model.codebert_finetune:
                    # 微调模式：保留梯度
                    outputs = self.codebert_model(**inputs)
                    embeddings = outputs.last_hidden_state[:, 0, :]  # [1, 768]
                else:
                    # 非微调模式：不计算梯度
                    with torch.no_grad():
                        outputs = self.codebert_model(**inputs)
                        embeddings = outputs.last_hidden_state[:, 0, :]  # [1, 768]
                
                # 应用线性投影层降维
                if self.projection_layer is not None:
                    embeddings = self.projection_layer(embeddings)  # [1, 768] -> [1, 256]
                
                # 转换为numpy数组
                embeddings = embeddings.detach().cpu().numpy()[0]
                
                # 确保维度正确（作为后备方案）
                if len(embeddings) != self.config.model.text_embedding_dim:
                    if len(embeddings) > self.config.model.text_embedding_dim:
                        return embeddings[:self.config.model.text_embedding_dim]
                    else:
                        result = np.zeros(self.config.model.text_embedding_dim)
                        result[:len(embeddings)] = embeddings
                        return result
                
                return embeddings
            except Exception as e:
                print(f"文本嵌入生成失败 ({self.config.model.embedding_model_type}): {e}")
        
        # 后备方案：使用哈希嵌入
        return self._hash_embedding(text)
    
    def _hash_embedding(self, text: str) -> np.ndarray:
        """使用哈希生成简单嵌入"""
        hash_obj = hashlib.md5(text.encode())
        hash_digest = hash_obj.digest()
        
        hash_values = np.array([b for b in hash_digest], dtype=np.float32)
        hash_values = np.resize(hash_values, self.config.model.text_embedding_dim)
        hash_values = (hash_values / 127.5) - 1.0
        
        return hash_values
    
    def extract_node_features(self, node_data: Dict[str, Any], full_code: str = "") -> np.ndarray:
        """
        提取节点特征向量（优化版：仅使用CodeBERT文本嵌入）
        
        参数:
            node_data: 节点数据字典
            full_code: 完整代码
            
        返回:
            特征向量 (维度: node_feature_dim = 256)
        """
        
        # ========== 优化方案：仅使用文本嵌入特征 ==========
        # 原因：
        # 1. one-hot编码浪费维度（32维只有1个非零值）
        # 2. 结构特征稀疏（16维中11维为0填充）
        # 3. CodeBERT文本嵌入已包含丰富的语义和结构信息
        # 4. 简化特征提取，提升训练效率
        
        # 获取代码片段的文本嵌入（256维）
        code_snippet = node_data.get('code_snippet_raw_text', '')
        if code_snippet:
            text_emb = self.get_text_embedding(code_snippet)
        else:
            text_emb = np.zeros(self.config.model.text_embedding_dim)
        
        # 直接返回文本嵌入作为节点特征
        feature_array = np.array(text_emb, dtype=np.float32)
        
        # 确保维度正确（应该已经是256维）
        target_dim = self.config.model.node_feature_dim
        if len(feature_array) != target_dim:
            if len(feature_array) < target_dim:
                # 填充零（不应该发生）
                padded = np.zeros(target_dim, dtype=np.float32)
                padded[:len(feature_array)] = feature_array
                return padded
            else:
                # 截断（不应该发生）
                return feature_array[:target_dim]
        
        return feature_array
        
        # ========== 以下是原始特征提取代码（已注释，保留供参考） ==========
        # features = []
        # 
        # # 1. 节点类型特征 (one-hot编码，32维) - 问题：稀疏，浪费维度
        # node_type = node_data.get('node_type', 'UNKNOWN')
        # type_features = self._encode_node_type(node_type)
        # features.extend(type_features)
        # 
        # # 2. 结构特征 (16维) - 问题：11维为0填充，浪费维度
        # structural_features = [
        #     1.0 if node_data.get('has_conditional_branch', False) else 0.0,
        #     1.0 if node_data.get('is_sensitive_api', False) else 0.0,
        #     min(node_data.get('complexity', 1), 100) / 100.0,
        #     min(node_data.get('depth', 0), 50) / 50.0,
        #     len(node_data.get('opcode_sequence', [])) / 100.0,
        #     # 预留11维 - 浪费！
        #     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        # ]
        # features.extend(structural_features)
        # 
        # # 3. 文本嵌入特征
        # code_snippet = node_data.get('code_snippet_raw_text', '')
        # if code_snippet:
        #     text_emb = self.get_text_embedding(code_snippet)
        # else:
        #     text_emb = np.zeros(self.config.model.text_embedding_dim)
        # features.extend(text_emb)
        # 
        # # 总维度：32 + 16 + 768 = 816维，但node_feature_dim只有128维
        # # 导致截断，丢失大量CodeBERT语义信息！
    
    def _encode_node_type(self, node_type: str) -> List[float]:
        """
        编码节点类型为one-hot向量（已废弃，保留供参考）
        
        问题：32维向量只有1个非零值，浪费维度
        优化方案：不再使用此方法，改用CodeBERT文本嵌入
        """
        node_types = [
            'ENTRY', 'EXIT', 'IF', 'FOR', 'WHILE', 'TRY', 'EXCEPT', 'FINALLY',
            'RETURN', 'CALL', 'ASSIGN', 'FUNCTION', 'ASYNC_FUNCTION', 'UNKNOWN'
        ]
        
        encoding = [0.0] * 32  # 预留32维
        if node_type in node_types:
            encoding[node_types.index(node_type)] = 1.0
        else:
            encoding[-1] = 1.0  # UNKNOWN
        
        return encoding
    
    def extract_function_metrics(self, func_ast: ast.FunctionDef) -> Dict[str, Any]:
        """提取函数度量指标"""
        if not isinstance(func_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):  # 普通函数或异步函数
            return {}
        
        metrics = {
            'name': func_ast.name,  
            'args_count': len(func_ast.args.args),
            'defaults_count': len(func_ast.args.defaults),
            'kw_only_count': len(func_ast.args.kwonlyargs),
            'has_var_args': func_ast.args.vararg is not None,
            'has_var_kwargs': func_ast.args.kwarg is not None,
            'body_length': len(func_ast.body),
            'decorator_count': len(func_ast.decorator_list),
            'returns_count': sum(1 for node in ast.walk(func_ast) 
                               if isinstance(node, ast.Return) and node.value is not None),
            'docstring_length': 0,
            'has_sensitive_api': False,
            'sensitive_api_count': 0,
        }
        
        # 检查文档字符串
        if (func_ast.body and isinstance(func_ast.body[0], ast.Expr) and
                isinstance(func_ast.body[0].value, (ast.Str, ast.Constant))):
            if isinstance(func_ast.body[0].value, ast.Str):
                metrics['docstring_length'] = len(func_ast.body[0].value.s)
            elif isinstance(func_ast.body[0].value, ast.Constant) and isinstance(func_ast.body[0].value.value, str):
                metrics['docstring_length'] = len(func_ast.body[0].value.value)
        
        # 检测敏感API
        for node in ast.walk(func_ast):
            if isinstance(node, ast.Call):
                is_sensitive, _ = self.detect_sensitive_api(node)  # 检测敏感API调用
                if is_sensitive:
                    metrics['has_sensitive_api'] = True
                    metrics['sensitive_api_count'] += 1
        
        return metrics


# 全局特征提取器实例
_global_extractor = None


def get_feature_extractor(config: Optional[Config] = None) -> FeatureExtractor:
    """获取全局特征提取器实例"""
    global _global_extractor
    if _global_extractor is None:
        _global_extractor = FeatureExtractor(config)
    return _global_extractor


if __name__ == "__main__":
    # 测试特征提取器
    print("测试特征提取器...")
    
    config = get_default_config()
    extractor = FeatureExtractor(config)
    
    # 测试代码片段
    test_code = """
import os
def dangerous_function():
    os.system("rm -rf /")
    with open("/etc/passwd", "r") as f:
        data = f.read()
    return data
"""
    
    # 测试文本嵌入
    embedding = extractor.get_text_embedding(test_code)
    print(f"文本嵌入维度: {embedding.shape}")
    
    # 测试节点特征提取
    node_data = {
        'node_type': 'CALL',
        'has_conditional_branch': False,
        'is_sensitive_api': True,
        'complexity': 5,
        'code_snippet_raw_text': 'os.system("rm -rf /")'
    }
    
    node_features = extractor.extract_node_features(node_data, test_code)
    print(f"节点特征维度: {node_features.shape}")
    print(f"节点特征前10个值: {node_features[:10]}")
    
    print("测试完成")
