#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ast
from typing import Optional, Union, Tuple


def parse_code_to_ast(code_file_path: str) -> Optional[ast.Module]:
    """
    将Python源代码文件解析为抽象语法树(AST)对象
    
    参数:
        code_file_path (str): Python源代码文件的完整路径
        
    返回:
        ast.Module: 表示解析后的AST对象，如果解析失败则返回None
        
    异常:
        FileNotFoundError: 文件不存在时抛出
        SyntaxError: 代码语法错误时抛出
    """
    if not os.path.exists(code_file_path):
        raise FileNotFoundError(f"文件不存在: {code_file_path}")
        
    try:
        with open(code_file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        return parse_code_string_to_ast(code_content)
    except UnicodeDecodeError:
        try:
            # 尝试使用其他编码
            with open(code_file_path, 'r', encoding='latin-1') as f:
                code_content = f.read()
            return parse_code_string_to_ast(code_content)
        except Exception as e:
            print(f"解析文件 {code_file_path} 时发生错误: {str(e)}")
            return None
    except Exception as e:
        print(f"解析文件 {code_file_path} 时发生错误: {str(e)}")
        return None


def parse_code_string_to_ast(code_string: str) -> ast.Module:
    """
    将Python源代码字符串解析为抽象语法树(AST)对象
    
    参数:
        code_string (str): Python源代码字符串
        
    返回:
        ast.Module: 表示解析后的AST对象
        
    异常:
        SyntaxError: 代码语法错误时抛出
    """
    return ast.parse(code_string)


def parse_code_with_line_mapping(code_file_path: str) -> Tuple[Optional[ast.Module], Optional[str]]:
    """
    解析Python源代码并返回AST对象及原始代码内容
    
    参数:
        code_file_path (str): Python源代码文件的完整路径
        
    返回:
        Tuple[ast.Module, str]: (AST对象, 源代码内容)，解析失败则返回(None, None)
    """
    if not os.path.exists(code_file_path):
        raise FileNotFoundError(f"文件不存在: {code_file_path}")
        
    try:
        with open(code_file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        ast_tree = parse_code_string_to_ast(code_content)
        return ast_tree, code_content
    except UnicodeDecodeError:
        try:
            # 尝试使用其他编码
            with open(code_file_path, 'r', encoding='latin-1') as f:
                code_content = f.read()
            ast_tree = parse_code_string_to_ast(code_content)
            return ast_tree, code_content
        except Exception as e:
            print(f"解析文件 {code_file_path} 时发生错误: {str(e)}")
            return None, None
    except Exception as e:
        print(f"解析文件 {code_file_path} 时发生错误: {str(e)}")
        return None, None


def get_node_source(node: ast.AST, source_code: str) -> str:
    """
    获取AST节点对应的源代码文本
    
    参数:
        node (ast.AST): AST节点
        source_code (str): 完整的源代码字符串
        
    返回:
        str: 节点对应的源代码片段
    """
    if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
        # 获取节点的起始和结束位置
        start_lineno = node.lineno
        start_col = node.col_offset
        
        # 节点的结束位置（如果有的话）
        end_lineno = getattr(node, 'end_lineno', start_lineno)
        end_col = getattr(node, 'end_col_offset', len(source_code.splitlines()[end_lineno-1]))
        
        # 提取代码片段
        lines = source_code.splitlines()
        if start_lineno == end_lineno:
            return lines[start_lineno-1][start_col:end_col]
        else:
            result = [lines[start_lineno-1][start_col:]]
            for i in range(start_lineno, end_lineno-1):
                result.append(lines[i])
            result.append(lines[end_lineno-1][:end_col])
            return '\n'.join(result)
    return ""


if __name__ == "__main__":
    # 简单的测试代码
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        # 使用自己作为测试文件
        test_file = __file__
        
    print(f"解析文件: {test_file}")
    ast_tree = parse_code_to_ast(test_file)
    
    if ast_tree:
        print(f"解析成功! AST结构包含 {len(ast_tree.body)} 个顶级节点")
        for i, node in enumerate(ast_tree.body[:3]):  # 只打印前3个节点
            node_type = type(node).__name__
            print(f"节点 {i+1}: 类型 = {node_type}")
    else:
        print("解析失败!") 