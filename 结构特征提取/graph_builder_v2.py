#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化的图构建模块
修复CFG构建逻辑，增强特征提取
"""

import ast
import networkx as nx
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from feature_extractor_v2 import FeatureExtractor, get_feature_extractor
from config import Config, get_default_config


class GraphBuilderV2:
    """优化的图构建器"""
    
    def __init__(self, ast_module: ast.Module, source_code: str, config: Optional[Config] = None):
        """
        初始化图构建器
        
        参数:
            ast_module: AST模块对象
            source_code: 源代码字符串
            config: 配置对象
        """
        self.ast_module = ast_module
        self.source_code = source_code
        self.config = config or get_default_config()
        self.feature_extractor = get_feature_extractor(config)  # 创建特征提取器对象
        
        self.functions = {}  # 函数名 -> 函数AST
        self.cfg_graphs = {}  # 函数名 -> CFG
        self.fcg_graph = None  # 函数调用图
        
        # 提取所有函数
        self._extract_functions()
    
    def _extract_functions(self) -> None:
        """提取所有函数定义"""
        for node in ast.walk(self.ast_module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions[node.name] = node
    
    def build_all_graphs(self) -> Tuple[Dict[str, nx.DiGraph], nx.DiGraph]:
        """
        构建所有图
        
        返回:
            (CFG字典, FCG)
        """
        # 构建每个函数的CFG
        for func_name, func_ast in self.functions.items():
            cfg = self._build_function_cfg(func_ast, func_name)  # 构建函数的cfg
            if cfg and cfg.number_of_nodes() >= self.config.data.min_nodes:
                self.cfg_graphs[func_name] = cfg
        
        # 构建FCG
        self.fcg_graph = self._build_fcg()
        
        return self.cfg_graphs, self.fcg_graph
    
    def _build_function_cfg(self, func_ast: ast.FunctionDef, func_name: str) -> nx.DiGraph:
        """
        构建函数的CFG
        
        修复：正确处理函数体，不将函数定义本身作为节点
        """
        cfg = nx.DiGraph()
        
        # 创建入口和出口节点
        entry_id = f"{func_name}::entry"
        exit_id = f"{func_name}::exit"
        
        cfg.add_node(entry_id, 
                    node_type="ENTRY",
                    code_snippet_raw_text="",
                    has_conditional_branch=False)
        
        cfg.add_node(exit_id,
                    node_type="EXIT", 
                    code_snippet_raw_text="",
                    has_conditional_branch=False)
        
        # 处理函数体
        if not func_ast.body:  # 处理空函数体
            cfg.add_edge(entry_id, exit_id)
            return cfg
        
        # 递归构建CFG
        current_nodes = [entry_id]
        for stmt in func_ast.body:
            # 跳过文档字符串
            if (isinstance(stmt, ast.Expr) and 
                isinstance(stmt.value, (ast.Str, ast.Constant))):
                continue
            
            exit_nodes = self._build_stmt_cfg(cfg, stmt, current_nodes, func_name)  # 根据语句类型构建相应的CFG
            current_nodes = exit_nodes if exit_nodes else current_nodes
        
        # 连接到出口
        for node in current_nodes:
            if node != exit_id:
                cfg.add_edge(node, exit_id)
        
        # 为当前的CFG所有节点，添加节点特征
        self._add_node_features(cfg)
        
        return cfg
    
    def _build_stmt_cfg(self, cfg: nx.DiGraph, stmt: ast.AST, 
                       entry_nodes: List[str], func_name: str) -> List[str]:
        """
        为语句构建CFG
        
        返回:
            出口节点列表
        """
        if isinstance(stmt, ast.If):
            return self._build_if_cfg(cfg, stmt, entry_nodes, func_name)
        elif isinstance(stmt, (ast.For, ast.While)):
            return self._build_loop_cfg(cfg, stmt, entry_nodes, func_name)
        elif isinstance(stmt, ast.Try):
            return self._build_try_cfg(cfg, stmt, entry_nodes, func_name)
        elif isinstance(stmt, ast.Return):
            return self._build_return_cfg(cfg, stmt, entry_nodes, func_name)
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):  # 函数调用的表达式语句
            return self._build_call_cfg(cfg, stmt, entry_nodes, func_name)
        elif isinstance(stmt, (ast.Assign, ast.AugAssign, ast.AnnAssign)):  # 赋值语句
            return self._build_assign_cfg(cfg, stmt, entry_nodes, func_name)
        else:
            # 其他语句类型
            return self._build_generic_cfg(cfg, stmt, entry_nodes, func_name)
    
    def _build_if_cfg(self, cfg: nx.DiGraph, if_stmt: ast.If,
                     entry_nodes: List[str], func_name: str) -> List[str]:
        """构建If语句的CFG"""
        node_id = f"{func_name}::if_{if_stmt.lineno}"
        
        code_snippet = self.feature_extractor.get_code_snippet(if_stmt.test, self.source_code)
        cfg.add_node(node_id,
                    node_type="IF",
                    code_snippet_raw_text=code_snippet,
                    has_conditional_branch=True,
                    lineno=if_stmt.lineno)
        
        # 连接入口节点
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        # 处理then分支
        then_exits = [node_id]
        for stmt in if_stmt.body:
            then_exits = self._build_stmt_cfg(cfg, stmt, then_exits, func_name)
        
        # 处理else分支
        else_exits = [node_id]
        if if_stmt.orelse:
            for stmt in if_stmt.orelse:
                else_exits = self._build_stmt_cfg(cfg, stmt, else_exits, func_name)
        
        # 标记分支类型
        for _, target in cfg.out_edges(node_id):
            if target in then_exits:
                cfg.edges[node_id, target]['edge_type'] = "TRUE_BRANCH"
            elif target in else_exits:
                cfg.edges[node_id, target]['edge_type'] = "FALSE_BRANCH"
        
        return then_exits + else_exits
    
    def _build_loop_cfg(self, cfg: nx.DiGraph, loop_stmt: Union[ast.For, ast.While],
                       entry_nodes: List[str], func_name: str) -> List[str]:
        """构建循环的CFG"""
        loop_type = "FOR" if isinstance(loop_stmt, ast.For) else "WHILE"
        node_id = f"{func_name}::{loop_type.lower()}_{loop_stmt.lineno}"
        
        # 获取循环条件
        if isinstance(loop_stmt, ast.For):
            code_snippet = self.feature_extractor.get_code_snippet(loop_stmt.iter, self.source_code)
        else:
            code_snippet = self.feature_extractor.get_code_snippet(loop_stmt.test, self.source_code)
        
        cfg.add_node(node_id,
                    node_type=loop_type,
                    code_snippet_raw_text=code_snippet,
                    has_conditional_branch=True,
                    lineno=loop_stmt.lineno)
        
        # 连接入口
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        # 处理循环体
        body_exits = [node_id]
        for stmt in loop_stmt.body:
            body_exits = self._build_stmt_cfg(cfg, stmt, body_exits, func_name)
        
        # 回边
        for exit_node in body_exits:
            cfg.add_edge(exit_node, node_id, edge_type="LOOP_BACK", is_back_edge=True)
        
        # 循环出口
        return [node_id]
    
    def _build_try_cfg(self, cfg: nx.DiGraph, try_stmt: ast.Try,
                      entry_nodes: List[str], func_name: str) -> List[str]:
        """构建Try语句的CFG"""
        node_id = f"{func_name}::try_{try_stmt.lineno}"
        
        cfg.add_node(node_id,
                    node_type="TRY",
                    code_snippet_raw_text="try:",
                    has_conditional_branch=False,
                    lineno=try_stmt.lineno)
        
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        # 处理try块
        try_exits = [node_id]
        for stmt in try_stmt.body:
            try_exits = self._build_stmt_cfg(cfg, stmt, try_exits, func_name)
        
        # 处理except块
        except_exits = []
        for handler in try_stmt.handlers:
            handler_id = f"{func_name}::except_{handler.lineno}"
            cfg.add_node(handler_id,
                        node_type="EXCEPT",
                        code_snippet_raw_text=f"except {handler.type.id if handler.type else ''}:",
                        has_conditional_branch=False,
                        lineno=handler.lineno)
            
            cfg.add_edge(node_id, handler_id, edge_type="EXCEPTION")
            
            handler_exits = [handler_id]
            for stmt in handler.body:
                handler_exits = self._build_stmt_cfg(cfg, stmt, handler_exits, func_name)
            except_exits.extend(handler_exits)
        
        # 处理finally块
        all_exits = try_exits + except_exits
        if try_stmt.finalbody:
            finally_id = f"{func_name}::finally_{try_stmt.finalbody[0].lineno}"
            cfg.add_node(finally_id,
                        node_type="FINALLY",
                        code_snippet_raw_text="finally:",
                        has_conditional_branch=False)
            
            for exit_node in all_exits:
                cfg.add_edge(exit_node, finally_id, edge_type="FLOW")
            
            finally_exits = [finally_id]
            for stmt in try_stmt.finalbody:
                finally_exits = self._build_stmt_cfg(cfg, stmt, finally_exits, func_name)
            
            return finally_exits
        
        return all_exits
    
    def _build_return_cfg(self, cfg: nx.DiGraph, return_stmt: ast.Return,
                         entry_nodes: List[str], func_name: str) -> List[str]:
        """构建Return语句的CFG"""
        node_id = f"{func_name}::return_{return_stmt.lineno}"
        
        code_snippet = self.feature_extractor.get_code_snippet(return_stmt, self.source_code)
        cfg.add_node(node_id,
                    node_type="RETURN",
                    code_snippet_raw_text=code_snippet,
                    has_conditional_branch=False,
                    lineno=return_stmt.lineno)
        
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        return [node_id]
    
    def _build_call_cfg(self, cfg: nx.DiGraph, call_stmt: ast.Expr,
                       entry_nodes: List[str], func_name: str) -> List[str]:
        """构建函数调用的CFG"""
        node_id = f"{func_name}::call_{call_stmt.lineno}"
        
        code_snippet = self.feature_extractor.get_code_snippet(call_stmt, self.source_code)
        is_sensitive, pattern = self.feature_extractor.detect_sensitive_api(call_stmt.value)
        
        cfg.add_node(node_id,
                    node_type="CALL",
                    code_snippet_raw_text=code_snippet,
                    has_conditional_branch=False,
                    is_sensitive_api=is_sensitive,
                    sensitive_pattern=pattern,
                    lineno=call_stmt.lineno)
        
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        return [node_id]
    
    def _build_assign_cfg(self, cfg: nx.DiGraph, assign_stmt: ast.AST,
                         entry_nodes: List[str], func_name: str) -> List[str]:
        """构建赋值语句的CFG"""
        node_id = f"{func_name}::assign_{assign_stmt.lineno}"
        
        code_snippet = self.feature_extractor.get_code_snippet(assign_stmt, self.source_code)  # 获取对应代码片段
        cfg.add_node(node_id,
                    node_type="ASSIGN",
                    code_snippet_raw_text=code_snippet,
                    has_conditional_branch=False,
                    lineno=assign_stmt.lineno)
        
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        return [node_id]
    
    def _build_generic_cfg(self, cfg: nx.DiGraph, stmt: ast.AST,
                          entry_nodes: List[str], func_name: str) -> List[str]:
        """构建通用语句的CFG"""
        node_id = f"{func_name}::{type(stmt).__name__}_{stmt.lineno}"
        
        code_snippet = self.feature_extractor.get_code_snippet(stmt, self.source_code)
        cfg.add_node(node_id,
                    node_type=type(stmt).__name__,
                    code_snippet_raw_text=code_snippet,
                    has_conditional_branch=False,
                    lineno=getattr(stmt, 'lineno', 0))
        
        for entry in entry_nodes:
            cfg.add_edge(entry, node_id, edge_type="FLOW")
        
        return [node_id]
    
    def _add_node_features(self, cfg: nx.DiGraph) -> None:
        """为CFG节点添加特征向量"""
        for node_id in cfg.nodes():
            node_data = cfg.nodes[node_id]  # 获取节点属性数据（字典）
            
            # 计算复杂度
            node_data['complexity'] = self.feature_extractor.calculate_cyclomatic_complexity(cfg)
            
            # 提取特征向量
            feature_vector = self.feature_extractor.extract_node_features(
                node_data, self.source_code
            )
            node_data['feature_vector'] = feature_vector
    
    def _build_fcg(self) -> nx.DiGraph:
        """构建函数调用图"""
        fcg = nx.DiGraph()
        
        # 添加所有函数节点
        for func_name, func_ast in self.functions.items():
            metrics = self.feature_extractor.extract_function_metrics(func_ast)  # 提取函数的各种度量指标
            
            fcg.add_node(func_name,
                        function_name=func_name,
                        **metrics)
        
        # 查找函数调用关系
        for caller_name, caller_ast in self.functions.items():
            for node in ast.walk(caller_ast):
                if isinstance(node, ast.Call):
                    callee_name = self._get_callee_name(node)
                    if callee_name and callee_name in self.functions:  # 检查是否为本模块内的函数调用
                        if not fcg.has_edge(caller_name, callee_name):  # 如果边 (u, v) 在图中，则返回 True
                            fcg.add_edge(caller_name, callee_name,
                                       call_count=1,
                                       lineno=node.lineno)
                        else:
                            fcg.edges[caller_name, callee_name]['call_count'] += 1
        
        return fcg
    
    def _get_callee_name(self, call_node: ast.Call) -> Optional[str]:
        """获取被调用函数的名称"""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id    
        elif isinstance(call_node.func, ast.Attribute):
            if isinstance(call_node.func.value, ast.Name):
                return f"{call_node.func.value.id}.{call_node.func.attr}"
        return None


def build_program_graphs_v2(ast_module: ast.Module, source_code: str,
                           config: Optional[Config] = None) -> Tuple[Dict[str, nx.DiGraph], nx.DiGraph]:
    """
    构建程序的所有图（优化版本）
    
    参数:
        ast_module: AST模块
        source_code: 源代码
        config: 配置对象
        
    返回:
        (CFG字典, FCG)
    """
    builder = GraphBuilderV2(ast_module, source_code, config)  # 创建图构造器
    return builder.build_all_graphs()  # 构造所有图


if __name__ == "__main__":
    # 测试图构建
    from ast_parser import parse_code_string_to_ast
    
    test_code = """
def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def main():
    result = factorial(5)
    print(result)
"""
    
    print("测试图构建...")
    ast_tree = parse_code_string_to_ast(test_code)
    cfgs, fcg = build_program_graphs_v2(ast_tree, test_code)
    
    print(f"\n生成了 {len(cfgs)} 个CFG:")
    for func_name, cfg in cfgs.items():
        print(f"  {func_name}: {cfg.number_of_nodes()} 节点, {cfg.number_of_edges()} 边")
    
    print(f"\nFCG: {fcg.number_of_nodes()} 节点, {fcg.number_of_edges()} 边")
    print("测试完成")
