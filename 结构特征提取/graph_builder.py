#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ast
import uuid
import networkx as nx
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Union, Any, Iterator

from ast_parser import parse_code_string_to_ast
import feature_extractor


class GraphBuilder:
    """
    统一构建Python程序的控制流图(CFG)和函数调用图(FCG)
    """
    
    def __init__(self, ast_object: ast.Module, code_string: str):
        """
        初始化GraphBuilder
        
        参数:
            ast_object (ast.Module): 由ast_parser.py提供的AST对象
            code_string (str): 完整的Python源代码字符串
        """
        self.ast_object = ast_object
        self.code_string = code_string
        self.functions_ast = {}  # 函数名到函数AST节点的映射
        self.cfg_graphs = {}  # 函数名到CFG的映射
        self.fcg_graph = None  # 全局FCG图
        
        # 抽取所有函数定义
        self._extract_all_functions()
    
    def _extract_all_functions(self) -> None:
        """
        从AST中提取所有函数定义
        """
        for node in ast.walk(self.ast_object):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 使用限定名称以处理嵌套函数
                qualified_name = node.name
                
                # 查找父函数（如果是嵌套的）
                parent = getattr(node, 'parent', None)
                while parent and isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified_name = f"{parent.name}.{qualified_name}"
                    parent = getattr(parent, 'parent', None)
                
                self.functions_ast[qualified_name] = node
        
        # 标记父子关系（用于处理嵌套函数）
        for node in ast.walk(self.ast_object):
            for child in ast.iter_child_nodes(node):
                setattr(child, 'parent', node)
    
    def build_program_graphs(self) -> Tuple[Dict[str, nx.DiGraph], nx.DiGraph]:
        """
        构建程序的所有CFG和FCG图
        
        返回:
            Tuple[Dict[str, nx.DiGraph], nx.DiGraph]: (函数CFG字典, 程序FCG)
        """
        # 1. 为每个函数构建CFG
        for func_name, func_ast in self.functions_ast.items():
            self.cfg_graphs[func_name] = self._build_function_cfg(func_ast, func_name)
        
        # 2. 构建函数调用图
        self.fcg_graph = self._build_function_call_graph()
        
        return self.cfg_graphs, self.fcg_graph
    
    def _build_function_cfg(self, func_ast: ast.FunctionDef, func_name: str) -> nx.DiGraph:
        """
        为函数构建CFG（控制流图）
        
        参数:
            func_ast (ast.FunctionDef): 函数的AST节点
            func_name (str): 函数名
            
        返回:
            nx.DiGraph: 构建的CFG
        """
        cfg = nx.DiGraph()
        
        # 创建入口节点
        entry_id = f"{func_name}_entry" # 入口节点id
        cfg.add_node(entry_id, # 添加节点   
                    node_id=entry_id, # 节点id
                    node_type="ENTRY", # 节点类型
                    code_snippet_raw_text="", # 节点代码片段
                    opcode_sequence=[], # 节点opcode序列
                    has_conditional_branch=False) # 节点是否包含条件分支
        
        # 跟踪已处理的节点和边
        processed_nodes = set() # 已处理的节点集合
        
        # 创建一个出口节点
        exit_id = f"{func_name}_exit"
        cfg.add_node(exit_id,
                    node_id=exit_id,
                    node_type="EXIT",
                    code_snippet_raw_text="",
                    opcode_sequence=[],
                    has_conditional_branch=False)
        
        # 调试：打印函数体中的语句数量
        print(f"DEBUG: 函数 {func_name} 体中有 {len(func_ast.body)} 条语句")
        
        # 使用DFS遍历构建CFG - 关键修改：传递函数体而不是整个函数AST
        # 处理函数体内的每条语句
        current_parent = entry_id
        for stmt in func_ast.body:
            exit_nodes = self._build_cfg_recursive(cfg, stmt, current_parent, processed_nodes, func_name)
            if exit_nodes:
                current_parent = exit_nodes[0]
        
        # 将最后处理的节点连接到出口节点
        cfg.add_edge(current_parent, exit_id)
        
        # 调试：打印生成的CFG节点数
        print(f"DEBUG: 函数 {func_name} 生成的CFG有 {cfg.number_of_nodes()} 个节点和 {cfg.number_of_edges()} 条边")
        
        # 为每个节点添加特征向量
        for node_id in cfg.nodes: 
            node_attrs = cfg.nodes[node_id] # 节点属性
            node_attrs['initial_feature_vector'] = feature_extractor.get_node_feature_vector(
                node_attrs, self.code_string
            ) # 节点特征向量
        
        # 为每条边添加特征
        for u, v, edge_attrs in cfg.edges(data=True): 
            if 'edge_type' not in edge_attrs:  
                edge_attrs['edge_type'] = "FLOW" # 边类型
            if 'condition_expression' not in edge_attrs:
                edge_attrs['condition_expression'] = "" # 边条件表达式
            if 'is_back_edge' not in edge_attrs:
                edge_attrs['is_back_edge'] = False # 是否为回边
            
            # 添加边特征向量（简单示例）
            edge_attrs['initial_feature_vector'] = np.zeros(16)
            
            # 设置基本特征（边类型）
            if edge_attrs['edge_type'] == "TRUE_BRANCH":
                edge_attrs['initial_feature_vector'][0] = 1.0 # 真分支特征向量
            elif edge_attrs['edge_type'] == "FALSE_BRANCH":
                edge_attrs['initial_feature_vector'][1] = 1.0 # 假分支特征向量
            elif edge_attrs['edge_type'] == "EXCEPTION":
                edge_attrs['initial_feature_vector'][2] = 1.0 # 异常边特征向量
            
            if edge_attrs['is_back_edge']:
                edge_attrs['initial_feature_vector'][3] = 1.0 # 回边特征向量
        
        return cfg
    
    def _build_cfg_recursive(self, cfg: nx.DiGraph, node: ast.AST, 
                           parent_id: str, processed_nodes: Set[str], 
                           func_name: str) -> List[str]:
        """
        递归构建CFG
        
        参数:
            cfg (nx.DiGraph): CFG图
            node (ast.AST): 当前处理的AST节点
            parent_id (str): 父节点ID
            processed_nodes (Set[str]): 已处理的节点集合
            func_name (str): 当前函数名
            
        返回:
            List[str]: 从当前节点可能退出的节点ID列表
        """
        if node is None:
            return [parent_id]
        
        exit_nodes = [] # 从当前节点可能退出的节点ID列表
        
        if isinstance(node, ast.If):
            # 处理If语句
            if_id = f"{func_name}_if_{node.lineno}_{node.col_offset}"
            
            # 添加条件节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node.test, self.code_string)
            cfg.add_node(if_id,
                        node_id=if_id,
                        node_type="IF",
                        code_snippet_raw_text=code_snippet,
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),
                        has_conditional_branch=True)
            
            # 连接父节点到条件节点
            cfg.add_edge(parent_id, if_id)
            
            # 处理True分支
            true_exit_nodes = []
            for body_node in node.body:
                true_exit_nodes.extend(
                    self._build_cfg_recursive(cfg, body_node, if_id, processed_nodes, func_name)
                )
                
            # 处理False分支
            false_exit_nodes = []
            for orelse_node in node.orelse:
                false_exit_nodes.extend(
                    self._build_cfg_recursive(cfg, orelse_node, if_id, processed_nodes, func_name)
                )
            
            # 如果没有else分支，添加默认路径
            if not node.orelse:
                false_exit_nodes = [if_id]
            
            # 设置TRUE和FALSE分支的边属性
            for _, v in cfg.edges([if_id]): 
                if v in true_exit_nodes: 
                    cfg.edges[if_id, v]['edge_type'] = "TRUE_BRANCH"  # 设置边类型为TRUE_BRANCH
                    cfg.edges[if_id, v]['condition_expression'] = code_snippet # 设置边条件表达式
                else:
                    cfg.edges[if_id, v]['edge_type'] = "FALSE_BRANCH" # 设置边类型为FALSE_BRANCH
                    cfg.edges[if_id, v]['condition_expression'] = f"not ({code_snippet})" # 设置边条件表达式    
            
            # 返回所有可能的退出节点
            exit_nodes = true_exit_nodes + false_exit_nodes
            
        elif isinstance(node, ast.For) or isinstance(node, ast.While):
            # 处理循环
            loop_type = "FOR" if isinstance(node, ast.For) else "WHILE"
            loop_id = f"{func_name}_{loop_type.lower()}_{node.lineno}_{node.col_offset}"
            
            # 添加循环条件节点
            test_expr = node.iter if isinstance(node, ast.For) else node.test
            code_snippet = feature_extractor.get_code_snippet_raw_text(test_expr, self.code_string)
            
            cfg.add_node(loop_id,
                        node_id=loop_id,
                        node_type=loop_type,
                        code_snippet_raw_text=code_snippet,
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),
                        has_conditional_branch=True)
            
            # 连接父节点到循环节点
            cfg.add_edge(parent_id, loop_id)
            
            # 处理循环体
            body_exit_nodes = []
            for body_node in node.body:
                body_exit_nodes.extend(
                    self._build_cfg_recursive(cfg, body_node, loop_id, processed_nodes, func_name)
                )
            
            # 从循环体回到循环条件（形成循环）
            for exit_node in body_exit_nodes:
                if exit_node != loop_id:  # 避免自环
                    cfg.add_edge(exit_node, loop_id, edge_type="LOOP_BACK", is_back_edge=True)
            
            # 处理else分支（如果有）
            else_exit_nodes = []
            for orelse_node in node.orelse:
                else_exit_nodes.extend(
                    self._build_cfg_recursive(cfg, orelse_node, loop_id, processed_nodes, func_name)
                )
            
            # 如果没有else分支
            if not node.orelse:
                else_exit_nodes = [loop_id]
            
            exit_nodes = else_exit_nodes
            
        elif isinstance(node, ast.Try):
            # 处理Try语句
            try_id = f"{func_name}_try_{node.lineno}_{node.col_offset}"
            
            # 添加Try节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node, self.code_string)
            cfg.add_node(try_id,
                        node_id=try_id,
                        node_type="TRY",
                        code_snippet_raw_text=code_snippet,
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),
                        has_conditional_branch=False)
            
            # 连接父节点到Try节点
            cfg.add_edge(parent_id, try_id)
            
            # 处理Try块
            try_exit_nodes = []
            for body_node in node.body:
                try_exit_nodes.extend(
                    self._build_cfg_recursive(cfg, body_node, try_id, processed_nodes, func_name)
                )
            
            # 处理except块
            except_exit_nodes = []
            for handler in node.handlers:
                handler_id = f"{func_name}_except_{handler.lineno}_{handler.col_offset}"
                
                # 添加handler节点
                handler_snippet = feature_extractor.get_code_snippet_raw_text(handler, self.code_string)
                cfg.add_node(handler_id,
                            node_id=handler_id,
                            node_type="EXCEPT",
                            code_snippet_raw_text=handler_snippet,
                            opcode_sequence=feature_extractor.extract_opcode_sequence(handler),
                            has_conditional_branch=False)
                
                # 从try连接到except
                cfg.add_edge(try_id, handler_id, edge_type="EXCEPTION")
                
                # 处理handler内部
                for handler_body_node in handler.body:
                    handler_exit = self._build_cfg_recursive(
                        cfg, handler_body_node, handler_id, processed_nodes, func_name
                    )
                    except_exit_nodes.extend(handler_exit)
            
            # 处理else块
            else_exit_nodes = []
            for else_node in node.orelse:
                for exit_node in try_exit_nodes:
                    else_exit = self._build_cfg_recursive(
                        cfg, else_node, exit_node, processed_nodes, func_name
                    )
                    else_exit_nodes.extend(else_exit)
            
            if node.orelse:
                try_exit_nodes = else_exit_nodes
            
            # 处理finally块
            finally_exit_nodes = []
            if node.finalbody:
                finally_id = f"{func_name}_finally_{node.finalbody[0].lineno}"
                
                # 添加finally节点
                finally_snippet = feature_extractor.get_code_snippet_raw_text(node.finalbody[0], self.code_string)
                cfg.add_node(finally_id,
                            node_id=finally_id,
                            node_type="FINALLY",
                            code_snippet_raw_text=finally_snippet,
                            opcode_sequence=[],
                            has_conditional_branch=False)
                
                # 从try和except连接到finally
                for exit_node in try_exit_nodes + except_exit_nodes:
                    cfg.add_edge(exit_node, finally_id)
                
                # 处理finally内部
                for finally_node in node.finalbody:
                    finally_exit = self._build_cfg_recursive(
                        cfg, finally_node, finally_id, processed_nodes, func_name
                    )
                    finally_exit_nodes.extend(finally_exit)
                
                exit_nodes = finally_exit_nodes
            else:
                exit_nodes = try_exit_nodes + except_exit_nodes
            
        elif isinstance(node, ast.Return):
            # 处理Return语句
            return_id = f"{func_name}_return_{node.lineno}_{node.col_offset}"
            
            # 添加Return节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node, self.code_string)
            cfg.add_node(return_id,
                        node_id=return_id,
                        node_type="RETURN",
                        code_snippet_raw_text=code_snippet,
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),
                        has_conditional_branch=False)
            
            # 连接父节点到Return节点
            cfg.add_edge(parent_id, return_id)
            
            exit_nodes = [return_id]
            
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            # 处理函数调用表达式
            call_id = f"{func_name}_call_{node.lineno}_{node.col_offset}"
            
            # 添加函数调用节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node, self.code_string)
            is_sensitive = feature_extractor.detect_sensitive_apis(node.value)
            
            cfg.add_node(call_id,
                        node_id=call_id,
                        node_type="CALL",
                        code_snippet_raw_text=code_snippet,
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),
                        has_conditional_branch=False,
                        is_sensitive_api=is_sensitive)
            
            # 连接父节点到Call节点
            cfg.add_edge(parent_id, call_id)
            
            exit_nodes = [call_id]
            
        elif isinstance(node, ast.Assign) or isinstance(node, ast.AugAssign):
            # 处理赋值语句
            assign_id = f"{func_name}_assign_{node.lineno}_{node.col_offset}"
            
            # 添加Assign节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node, self.code_string)
            cfg.add_node(assign_id,# 添加节点
                        node_id=assign_id,# 节点id
                        node_type="ASSIGN",# 节点类型
                        code_snippet_raw_text=code_snippet,# 节点代码片段
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),# 节点opcode序列
                        has_conditional_branch=False)# 节点是否包含条件分支
            
            # 连接父节点到Assign节点
            cfg.add_edge(parent_id, assign_id)
            
            exit_nodes = [assign_id]
            
        elif isinstance(node, list):
            # 处理语句列表
            current_parent = parent_id
            for stmt in node:
                exit_nodes = self._build_cfg_recursive(cfg, stmt, current_parent, processed_nodes, func_name)
                current_parent = exit_nodes[0] if exit_nodes else current_parent
            
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 处理函数或异步函数定义
            func_type = "ASYNC_FUNCTION" if isinstance(node, ast.AsyncFunctionDef) else "FUNCTION"
            func_id = f"{func_name}_{func_type.lower()}_{node.lineno}_{node.col_offset}"
            
            # 添加函数定义节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node, self.code_string)
            cfg.add_node(func_id,
                        node_id=func_id,
                        node_type=func_type,
                        code_snippet_raw_text=code_snippet,
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node),
                        has_conditional_branch=False)
            
            # 连接父节点到函数定义节点
            cfg.add_edge(parent_id, func_id)
            
            # 函数定义本身不再处理其内部语句（因为这些会在各自的CFG中处理）
            exit_nodes = [func_id]
        
        else:
            # 处理其他类型的节点
            other_id = f"{func_name}_node_{getattr(node, 'lineno', '0')}_{getattr(node, 'col_offset', '0')}"   # 其他节点id
            
            # 添加通用节点
            code_snippet = feature_extractor.get_code_snippet_raw_text(node, self.code_string) if hasattr(node, 'lineno') else "" # 节点代码片段
            cfg.add_node(other_id,# 添加节点
                        node_id=other_id,# 节点id   
                        node_type=type(node).__name__,# 节点类型
                        code_snippet_raw_text=code_snippet,# 节点代码片段
                        opcode_sequence=feature_extractor.extract_opcode_sequence(node) if hasattr(node, 'body') else [],# 节点opcode序列
                        has_conditional_branch=False)# 节点是否包含条件分支
            
            # 连接父节点到此节点
            cfg.add_edge(parent_id, other_id)
            
            exit_nodes = [other_id]
        
        return exit_nodes
    
    def _build_function_call_graph(self) -> nx.DiGraph:
        """
        构建函数调用图(FCG)
        
        返回:
            nx.DiGraph: 函数调用图
        """
        fcg = nx.DiGraph() 
        
        # 为每个函数添加节点
        for func_name, func_ast in self.functions_ast.items():
            # 获取函数度量指标
            metrics = feature_extractor.extract_function_metrics(func_ast)  
            
            # 计算CFG复杂度
            cfg_complexity = 1
            if func_name in self.cfg_graphs:
                cfg_complexity = feature_extractor.calculate_cyclomatic_complexity(self.cfg_graphs[func_name])
            
            # 检测函数是否包含敏感API调用
            has_sensitive_api = False
            for node in ast.walk(func_ast):
                if isinstance(node, ast.Call) and feature_extractor.detect_sensitive_apis(node):
                    has_sensitive_api = True
                    break
            
            # 添加FCG节点
            fcg.add_node(func_name,
                         function_id=func_name, # 函数id
                         function_name=metrics['name'], # 函数名
                         parameters_count=metrics['args_count'], # 参数数量
                         has_var_args=metrics['has_var_args'], # 是否可变参数
                         has_var_kwargs=metrics['has_var_kwargs'], # 是否可变关键字参数
                         return_type_hint=getattr(func_ast, 'returns', None), # 返回类型提示
                         is_sensitive_api=has_sensitive_api, # 是否包含敏感API
                         internal_complexity=cfg_complexity) # 内部复杂度
        
        # 查找函数之间的调用关系
        for caller_name, caller_ast in self.functions_ast.items():
            # 使用访问者模式查找所有函数调用
            self._find_function_calls(fcg, caller_ast, caller_name)
        
        # 为每个节点添加特征向量
        for node in fcg.nodes:
            node_attrs = fcg.nodes[node]
            # 简单示例：构建特征向量
            feature_vec = np.zeros(16)
            feature_vec[0] = node_attrs['parameters_count'] / 10.0
            feature_vec[1] = 1.0 if node_attrs['has_var_args'] else 0.0
            feature_vec[2] = 1.0 if node_attrs['has_var_kwargs'] else 0.0
            feature_vec[3] = 1.0 if node_attrs['is_sensitive_api'] else 0.0
            feature_vec[4] = node_attrs['internal_complexity'] / 10.0
            
            node_attrs['initial_feature_vector'] = feature_vec
        
        return fcg
    
    def _find_function_calls(self, fcg: nx.DiGraph, ast_node: ast.AST, caller_name: str) -> None:
        """
        查找AST中的函数调用并添加到FCG
        
        参数:
            fcg (nx.DiGraph): 函数调用图
            ast_node (ast.AST): AST节点
            caller_name (str): 调用者函数名
        """
        for node in ast.walk(ast_node):
            if isinstance(node, ast.Call):
                called_name = None
                
                # 提取被调用的函数名
                if isinstance(node.func, ast.Name):
                    # 直接调用，例如 foo()
                    called_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    # 属性调用，例如 module.foo()
                    # 我们只考虑简单情况
                    if isinstance(node.func.value, ast.Name):
                        # module.foo() 形式
                        called_name = f"{node.func.value.id}.{node.func.attr}"
                
                # 如果找到调用的函数，且函数在我们的AST中
                if called_name in self.functions_ast:
                    # 添加调用边
                    if not fcg.has_edge(caller_name, called_name):
                        fcg.add_edge(caller_name, # 添加调用边
                                    called_name, # 被调用函数名
                                    call_location_file=os.path.basename(getattr(self.ast_object, 'filename', '')), # 调用位置文件名
                                    call_location_lineno=getattr(node, 'lineno', 0), # 调用位置行号
                                    is_dynamic_call=False, # 是否为动态调用
                                    arguments_count=len(node.args)) # 参数数量
                        
                        # 为边添加特征向量
                        edge_attrs = fcg.edges[caller_name, called_name] # 边属性
                        edge_feature_vec = np.zeros(8) # 边特征向量
                        edge_feature_vec[0] = edge_attrs['arguments_count'] / 10.0 # 参数数量
                        edge_feature_vec[1] = 1.0 if edge_attrs['is_dynamic_call'] else 0.0 # 是否为动态调用
                        
                        edge_attrs['initial_feature_vector'] = edge_feature_vec # 边特征向量


def build_program_graphs(ast_object: ast.Module, code_string: str) -> Tuple[Dict[str, nx.DiGraph], nx.DiGraph]:
    """
    统一构建一个Python程序的所有CFG（按函数）和全局FCG
    
    参数:
        ast_object (ast.Module): 由ast_parser.py提供的AST对象
        code_string (str): 完整的Python源代码字符串
        
    返回:
        Tuple[Dict[str, nx.DiGraph], nx.DiGraph]: (函数CFG字典, 程序FCG)
    """
    builder = GraphBuilder(ast_object, code_string)
    return builder.build_program_graphs()


if __name__ == "__main__":
    # 简单的测试代码
    import sys
    from ast_parser import parse_code_string_to_ast
    
    test_code = """
def factorial(n):
    \"\"\"计算阶乘\"\"\"
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def fibonacci(n):
    \"\"\"计算斐波那契数列\"\"\"
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
        
def main():
    n = 5
    print(f"斐波那契数列第{n}项: {fibonacci(n)}")
    print(f"阶乘{n}!: {factorial(n)}")
    
if __name__ == "__main__":
    main()
"""
    
    # 解析测试代码
    try:
        test_ast = parse_code_string_to_ast(test_code)
        
        print("构建程序图...")
        cfg_dict, fcg = build_program_graphs(test_ast, test_code)
        
        print("\nCFG信息:")
        for func_name, cfg in cfg_dict.items():
            print(f"  函数 '{func_name}' CFG: {cfg.number_of_nodes()}个节点, {cfg.number_of_edges()}条边")
        
        print("\nFCG信息:")
        print(f"  节点数: {fcg.number_of_nodes()}")
        print(f"  边数: {fcg.number_of_edges()}")
        print("  函数调用关系:")
        for u, v in fcg.edges():
            print(f"    {u} -> {v}")
        
    except Exception as e:
        print(f"测试时出错: {str(e)}") 