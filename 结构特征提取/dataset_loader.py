#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import List, Optional

def load_code_paths(data_root_dir: str, file_extension: str = '.py') -> List[str]:
    """
    加载指定目录下所有Python源代码文件的路径
    
    参数:
        data_root_dir (str): 包含Python源代码文件的根目录
        file_extension (str): 文件扩展名，默认为'.py'
        
    返回:
        List[str]: 包含所有Python源代码文件完整路径的列表
    """
    if not os.path.exists(data_root_dir):
        raise FileNotFoundError(f"目录不存在: {data_root_dir}")
        
    code_paths = []
    
    for root, _, files in os.walk(data_root_dir):
        for file in files:
            if file.endswith(file_extension):
                full_path = os.path.join(root, file)
                code_paths.append(os.path.abspath(full_path))
                
    return code_paths


def load_code_paths_with_labels(data_root_dir: str, label_dict: Optional[dict] = None) -> List[tuple]:
    """
    加载指定目录下所有Python源代码文件的路径，并根据目录结构或提供的字典返回标签信息
    
    参数:
        data_root_dir (str): 包含Python源代码文件的根目录
        label_dict (dict, optional): 映射路径到标签的字典，如果为None，则尝试从目录结构推断
        
    返回:
        List[tuple]: 包含(文件路径, 标签)元组的列表
    """
    code_paths = load_code_paths(data_root_dir)
    result = []
    
    for path in code_paths:
        if label_dict is not None and path in label_dict: # 提供了[label_dict]且当前[path]存在于[label_dict]中
            label = label_dict[path] # 使用提供的标签
        else:
            # 默认使用父目录名作为标签
            parent_dir = os.path.basename(os.path.dirname(path))
            label = parent_dir
            
        result.append((path, label))
        
    return result


if __name__ == "__main__":
    # 简单的测试代码
    import sys
    
    if len(sys.argv) > 1:
        test_dir = sys.argv[1]
    else:
        test_dir = "."  # 默认使用当前目录
        
    print(f"加载目录: {test_dir} 中的Python文件")
    paths = load_code_paths(test_dir)
    print(f"找到 {len(paths)} 个Python文件:")
    for p in paths:
        print(f"  - {p}") 