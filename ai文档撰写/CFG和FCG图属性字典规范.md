# CFG 和 FCG 图属性字典规范文档

## 文档说明

本文档详细说明了在 `graph_builder_v2.py` 中构建的控制流图（CFG）和函数调用图（FCG）的节点和边属性字典的通用格式。

## 一、CFG（控制流图）

### 1.1 CFG 概述

- **定义**：一个函数对应一个 CFG 图
- **节点**：表示特定控制语句的 AST 节点（如 IF、WHILE、CALL 等）
- **边**：表示控制流（如顺序执行、分支、循环等）

### 1.2 CFG 节点属性字典（cfg.nodes[node_id]）

#### 通用格式

```python
{
    # ========== 基础属性 ==========
    'node_type': str,                    # 节点类型
    'code_snippet_raw_text': str,        # 代码片段原始文本
    'has_conditional_branch': bool,      # 是否有条件分支
    'lineno': int,                       # 源代码行号
    
    # ========== 敏感API检测属性（可选）==========
    'is_sensitive_api': bool,            # 是否为敏感API调用
    'sensitive_pattern': str,            # 敏感API模式名称
    
    # ========== 计算属性 ==========
    'complexity': int,                   # 圈复杂度
    'feature_vector': np.ndarray,        # 节点特征向量（256维）
}
```

#### 属性详细说明

| 属性名 | 类型 | 说明 | 示例值 | 来源代码位置 |
|--------|------|------|--------|-------------|
| `node_type` | str | 节点类型标识 | `'CALL'`, `'IF'`, `'WHILE'`, `'RETURN'`, `'ENTRY'`, `'EXIT'` 等 | `_build_*_cfg()` 方法 |
| `code_snippet_raw_text` | str | 对应的源代码片段 | `'os.system(cmd)'`, `'if n <= 1:'` | `feature_extractor.get_code_snippet()` |
| `has_conditional_branch` | bool | 是否包含条件分支 | `True` (IF/WHILE), `False` (CALL/ASSIGN) | 各 `_build_*_cfg()` 方法 |
| `lineno` | int | 在源代码中的行号 | `42`, `15` | `stmt.lineno` |
| `is_sensitive_api` | bool | 是否调用敏感API | `True`, `False` | `feature_extractor.detect_sensitive_api()` |
| `sensitive_pattern` | str | 匹配的敏感API模式 | `'os.system'`, `'subprocess.run'` | `feature_extractor.detect_sensitive_api()` |
| `complexity` | int | 函数的圈复杂度 | `3`, `5`, `10` | `feature_extractor.calculate_cyclomatic_complexity()` |
| `feature_vector` | np.ndarray | CodeBERT提取的特征向量 | `array([0.12, -0.34, ...], dtype=float32)` (256维) | `feature_extractor.extract_node_features()` |



#### 不同节点类型的属性差异

##### ENTRY 节点（入口节点）
```python
{
    'node_type': 'ENTRY',
    'code_snippet_raw_text': '',
    'has_conditional_branch': False,
    'complexity': 3,
    'feature_vector': array([...], dtype=float32)  # 256维零向量
}
```

##### EXIT 节点（出口节点）
```python
{
    'node_type': 'EXIT',
    'code_snippet_raw_text': '',
    'has_conditional_branch': False,
    'complexity': 3,
    'feature_vector': array([...], dtype=float32)  # 256维零向量
}
```

##### IF 节点（条件分支）
```python
{
    'node_type': 'IF',
    'code_snippet_raw_text': 'n <= 1',
    'has_conditional_branch': True,
    'lineno': 15,
    'complexity': 3,
    'feature_vector': array([0.12, -0.34, ...], dtype=float32)  # 256维
}
```

##### WHILE 节点（循环）
```python
{
    'node_type': 'WHILE',
    'code_snippet_raw_text': 'i < len(data)',
    'has_conditional_branch': True,
    'lineno': 20,
    'complexity': 5,
    'feature_vector': array([0.23, -0.45, ...], dtype=float32)  # 256维
}
```

##### FOR 节点（循环）
```python
{
    'node_type': 'FOR',
    'code_snippet_raw_text': 'range(10)',
    'has_conditional_branch': True,
    'lineno': 25,
    'complexity': 5,
    'feature_vector': array([0.34, -0.56, ...], dtype=float32)  # 256维
}
```

##### CALL 节点（函数调用）
```python
{
    'node_type': 'CALL',
    'code_snippet_raw_text': 'os.system(cmd)',
    'has_conditional_branch': False,
    'is_sensitive_api': True,
    'sensitive_pattern': 'os.system',
    'lineno': 42,
    'complexity': 3,
    'feature_vector': array([0.45, -0.67, ...], dtype=float32)  # 256维
}
```

##### ASSIGN 节点（赋值语句）
```python
{
    'node_type': 'ASSIGN',
    'code_snippet_raw_text': 'result = factorial(5)',
    'has_conditional_branch': False,
    'lineno': 30,
    'complexity': 3,
    'feature_vector': array([0.56, -0.78, ...], dtype=float32)  # 256维
}
```

##### RETURN 节点（返回语句）
```python
{
    'node_type': 'RETURN',
    'code_snippet_raw_text': 'return n * factorial(n - 1)',
    'has_conditional_branch': False,
    'lineno': 18,
    'complexity': 3,
    'feature_vector': array([0.67, -0.89, ...], dtype=float32)  # 256维
}
```

##### TRY 节点（异常处理）
```python
{
    'node_type': 'TRY',
    'code_snippet_raw_text': 'try:',
    'has_conditional_branch': False,
    'lineno': 35,
    'complexity': 4,
    'feature_vector': array([0.78, -0.90, ...], dtype=float32)  # 256维
}
```

##### EXCEPT 节点（异常捕获）
```python
{
    'node_type': 'EXCEPT',
    'code_snippet_raw_text': 'except ValueError:',
    'has_conditional_branch': False,
    'lineno': 38,
    'complexity': 4,
    'feature_vector': array([0.89, -0.12, ...], dtype=float32)  # 256维
}
```

##### FINALLY 节点（最终执行块）
```python
{
    'node_type': 'FINALLY',
    'code_snippet_raw_text': 'finally:',
    'has_conditional_branch': False,
    'lineno': 40,
    'complexity': 4,
    'feature_vector': array([0.90, -0.23, ...], dtype=float32)  # 256维
}
```

### 1.3 CFG 边属性字典（cfg.edges[u, v]）

#### 通用格式

```python
{
    'edge_type': str,           # 边类型
    'is_back_edge': bool,       # 是否为回边（可选）
}
```

#### 属性详细说明

| 属性名 | 类型 | 说明 | 示例值 | 来源代码位置 |
|--------|------|------|--------|-------------|
| `edge_type` | str | 边的类型标识 | `'FLOW'`, `'TRUE_BRANCH'`, `'FALSE_BRANCH'`, `'LOOP_BACK'`, `'EXCEPTION'` | 各 `_build_*_cfg()` 方法 |
| `is_back_edge` | bool | 是否为循环回边 | `True`, `False` | `_build_loop_cfg()` |

#### 边类型说明

| 边类型 | 说明 | 使用场景 | 代码位置 |
|--------|------|----------|----------|
| `FLOW` | 顺序控制流 | 普通语句之间的连接 | 所有 `_build_*_cfg()` |
| `TRUE_BRANCH` | 条件为真的分支 | IF 语句的 then 分支 | `_build_if_cfg()` |
| `FALSE_BRANCH` | 条件为假的分支 | IF 语句的 else 分支 | `_build_if_cfg()` |
| `LOOP_BACK` | 循环回边 | 循环体结束后回到循环头 | `_build_loop_cfg()` |
| `EXCEPTION` | 异常处理边 | TRY 到 EXCEPT 的连接 | `_build_try_cfg()` |

#### 边属性示例

##### 顺序流边
```python
('func::entry', 'func::assign_10', {'edge_type': 'FLOW'})
```

##### 条件分支边（真分支）
```python
('func::if_15', 'func::return_16', {'edge_type': 'TRUE_BRANCH'})
```

##### 条件分支边（假分支）
```python
('func::if_15', 'func::assign_18', {'edge_type': 'FALSE_BRANCH'})
```

##### 循环回边
```python
('func::assign_25', 'func::while_20', {'edge_type': 'LOOP_BACK', 'is_back_edge': True})
```

##### 异常处理边
```python
('func::try_35', 'func::except_38', {'edge_type': 'EXCEPTION'})
```



## 二、FCG（函数调用图）

### 2.1 FCG 概述

- **定义**：一个模块对应一个 FCG 图
- **节点**：表示函数
- **边**：表示函数之间的调用关系

### 2.2 FCG 节点属性字典（fcg.nodes[func_name]）

#### 通用格式

```python
{
    # ========== 基础信息 ==========
    'function_name': str,           # 函数名称
    'name': str,                    # 函数名称（冗余，与function_name相同）
    
    # ========== 参数信息 ==========
    'args_count': int,              # 位置参数数量
    'defaults_count': int,          # 默认参数数量
    'kw_only_count': int,           # 仅关键字参数数量
    'has_var_args': bool,           # 是否有*args
    'has_var_kwargs': bool,         # 是否有**kwargs
    
    # ========== 函数体信息 ==========
    'body_length': int,             # 函数体语句数量
    'decorator_count': int,         # 装饰器数量
    'returns_count': int,           # return语句数量
    'docstring_length': int,        # 文档字符串长度
    
    # ========== 安全分析 ==========
    'has_sensitive_api': bool,      # 是否包含敏感API调用
    'sensitive_api_count': int,     # 敏感API调用次数
}
```

#### 属性详细说明

| 属性名 | 类型 | 说明 | 示例值 | 来源代码位置 |
|--------|------|------|--------|-------------|
| `function_name` | str | 函数名称 | `'process_ocean_data'`, `'main'` | `func_ast.name` |
| `name` | str | 函数名称（与function_name相同） | `'process_ocean_data'` | `func_ast.name` |
| `args_count` | int | 位置参数数量 | `1`, `2`, `0` | `len(func_ast.args.args)` |
| `defaults_count` | int | 有默认值的参数数量 | `0`, `1`, `2` | `len(func_ast.args.defaults)` |
| `kw_only_count` | int | 仅关键字参数数量 | `0`, `1` | `len(func_ast.args.kwonlyargs)` |
| `has_var_args` | bool | 是否有可变位置参数(*args) | `True`, `False` | `func_ast.args.vararg is not None` |
| `has_var_kwargs` | bool | 是否有可变关键字参数(**kwargs) | `True`, `False` | `func_ast.args.kwarg is not None` |
| `body_length` | int | 函数体中的语句数量 | `3`, `10`, `25` | `len(func_ast.body)` |
| `decorator_count` | int | 装饰器数量 | `0`, `1`, `2` | `len(func_ast.decorator_list)` |
| `returns_count` | int | 有返回值的return语句数量 | `1`, `2`, `0` | 遍历AST统计 |
| `docstring_length` | int | 文档字符串字符数 | `0`, `10`, `150` | 提取docstring长度 |
| `has_sensitive_api` | bool | 是否调用敏感API | `True`, `False` | `detect_sensitive_api()` |
| `sensitive_api_count` | int | 敏感API调用总次数 | `0`, `2`, `5` | 遍历AST统计 |

#### FCG 节点示例

##### 普通函数
```python
{
    'function_name': 'calculate_density',
    'name': 'calculate_density',
    'args_count': 3,
    'defaults_count': 0,
    'kw_only_count': 0,
    'has_var_args': False,
    'has_var_kwargs': False,
    'body_length': 8,
    'decorator_count': 0,
    'returns_count': 1,
    'docstring_length': 45,
    'has_sensitive_api': False,
    'sensitive_api_count': 0
}
```

##### 包含敏感API的函数
```python
{
    'function_name': 'process_ocean_data',
    'name': 'process_ocean_data',
    'args_count': 1,
    'defaults_count': 0,
    'kw_only_count': 0,
    'has_var_args': False,
    'has_var_kwargs': False,
    'body_length': 5,
    'decorator_count': 0,
    'returns_count': 1,
    'docstring_length': 25,
    'has_sensitive_api': True,
    'sensitive_api_count': 2
}
```

##### 带装饰器和可变参数的函数
```python
{
    'function_name': 'wrapper_function',
    'name': 'wrapper_function',
    'args_count': 1,
    'defaults_count': 1,
    'kw_only_count': 1,
    'has_var_args': True,
    'has_var_kwargs': True,
    'body_length': 12,
    'decorator_count': 2,
    'returns_count': 1,
    'docstring_length': 80,
    'has_sensitive_api': False,
    'sensitive_api_count': 0
}
```

### 2.3 FCG 边属性字典（fcg.edges[caller, callee]）

#### 通用格式

```python
{
    'call_count': int,      # 调用次数
    'lineno': int,          # 首次调用的行号
}
```

#### 属性详细说明

| 属性名 | 类型 | 说明 | 示例值 | 来源代码位置 |
|--------|------|------|--------|-------------|
| `call_count` | int | 调用者调用被调用者的次数 | `1`, `2`, `5` | `_build_fcg()` 中累加 |
| `lineno` | int | 首次调用发生的源代码行号 | `42`, `15`, `100` | `call_node.lineno` |

#### FCG 边示例

##### 单次调用
```python
('main', 'process_ocean_data', {'call_count': 1, 'lineno': 50})
```

##### 多次调用
```python
('process_data', 'calculate_density', {'call_count': 3, 'lineno': 25})
```

##### 递归调用
```python
('factorial', 'factorial', {'call_count': 1, 'lineno': 18})
```



## 三、完整示例

### 3.1 示例代码

```python
def factorial(n):
    """计算阶乘"""
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

def process_data(file_path):
    """处理数据文件"""
    import os
    result = factorial(5)
    os.system(f"cat {file_path}")
    return result

def main():
    """主函数"""
    data = process_data("/data/ocean.csv")
    print(data)
```

### 3.2 CFG 示例（factorial 函数）

#### 节点列表
```python
# 入口节点
'factorial::entry': {
    'node_type': 'ENTRY',
    'code_snippet_raw_text': '',
    'has_conditional_branch': False,
    'complexity': 3,
    'feature_vector': array([0.0, 0.0, ...], dtype=float32)  # 256维
}

# IF 节点
'factorial::if_3': {
    'node_type': 'IF',
    'code_snippet_raw_text': 'n <= 1',
    'has_conditional_branch': True,
    'lineno': 3,
    'complexity': 3,
    'feature_vector': array([0.12, -0.34, ...], dtype=float32)  # 256维
}

# RETURN 节点（then分支）
'factorial::return_4': {
    'node_type': 'RETURN',
    'code_snippet_raw_text': 'return 1',
    'has_conditional_branch': False,
    'lineno': 4,
    'complexity': 3,
    'feature_vector': array([0.23, -0.45, ...], dtype=float32)  # 256维
}

# RETURN 节点（else分支）
'factorial::return_6': {
    'node_type': 'RETURN',
    'code_snippet_raw_text': 'return n * factorial(n - 1)',
    'has_conditional_branch': False,
    'lineno': 6,
    'complexity': 3,
    'feature_vector': array([0.34, -0.56, ...], dtype=float32)  # 256维
}

# 出口节点
'factorial::exit': {
    'node_type': 'EXIT',
    'code_snippet_raw_text': '',
    'has_conditional_branch': False,
    'complexity': 3,
    'feature_vector': array([0.0, 0.0, ...], dtype=float32)  # 256维
}
```

#### 边列表
```python
# 入口到IF
('factorial::entry', 'factorial::if_3', {'edge_type': 'FLOW'})

# IF到RETURN（真分支）
('factorial::if_3', 'factorial::return_4', {'edge_type': 'TRUE_BRANCH'})

# IF到RETURN（假分支）
('factorial::if_3', 'factorial::return_6', {'edge_type': 'FALSE_BRANCH'})

# RETURN到出口
('factorial::return_4', 'factorial::exit', {'edge_type': 'FLOW'})
('factorial::return_6', 'factorial::exit', {'edge_type': 'FLOW'})
```

### 3.3 CFG 示例（process_data 函数）

#### 节点列表
```python
# 入口节点
'process_data::entry': {
    'node_type': 'ENTRY',
    'code_snippet_raw_text': '',
    'has_conditional_branch': False,
    'complexity': 2,
    'feature_vector': array([0.0, 0.0, ...], dtype=float32)
}

# ASSIGN 节点
'process_data::assign_11': {
    'node_type': 'ASSIGN',
    'code_snippet_raw_text': 'result = factorial(5)',
    'has_conditional_branch': False,
    'lineno': 11,
    'complexity': 2,
    'feature_vector': array([0.45, -0.67, ...], dtype=float32)
}

# CALL 节点（敏感API）
'process_data::call_12': {
    'node_type': 'CALL',
    'code_snippet_raw_text': 'os.system(f"cat {file_path}")',
    'has_conditional_branch': False,
    'is_sensitive_api': True,
    'sensitive_pattern': 'os.system',
    'lineno': 12,
    'complexity': 2,
    'feature_vector': array([0.56, -0.78, ...], dtype=float32)
}

# RETURN 节点
'process_data::return_13': {
    'node_type': 'RETURN',
    'code_snippet_raw_text': 'return result',
    'has_conditional_branch': False,
    'lineno': 13,
    'complexity': 2,
    'feature_vector': array([0.67, -0.89, ...], dtype=float32)
}

# 出口节点
'process_data::exit': {
    'node_type': 'EXIT',
    'code_snippet_raw_text': '',
    'has_conditional_branch': False,
    'complexity': 2,
    'feature_vector': array([0.0, 0.0, ...], dtype=float32)
}
```

#### 边列表
```python
('process_data::entry', 'process_data::assign_11', {'edge_type': 'FLOW'})
('process_data::assign_11', 'process_data::call_12', {'edge_type': 'FLOW'})
('process_data::call_12', 'process_data::return_13', {'edge_type': 'FLOW'})
('process_data::return_13', 'process_data::exit', {'edge_type': 'FLOW'})
```

### 3.4 FCG 示例（整个模块）

#### 节点列表
```python
# factorial 函数
'factorial': {
    'function_name': 'factorial',
    'name': 'factorial',
    'args_count': 1,
    'defaults_count': 0,
    'kw_only_count': 0,
    'has_var_args': False,
    'has_var_kwargs': False,
    'body_length': 2,
    'decorator_count': 0,
    'returns_count': 2,
    'docstring_length': 9,
    'has_sensitive_api': False,
    'sensitive_api_count': 0
}

# process_data 函数
'process_data': {
    'function_name': 'process_data',
    'name': 'process_data',
    'args_count': 1,
    'defaults_count': 0,
    'kw_only_count': 0,
    'has_var_args': False,
    'has_var_kwargs': False,
    'body_length': 4,
    'decorator_count': 0,
    'returns_count': 1,
    'docstring_length': 12,
    'has_sensitive_api': True,
    'sensitive_api_count': 1
}

# main 函数
'main': {
    'function_name': 'main',
    'name': 'main',
    'args_count': 0,
    'defaults_count': 0,
    'kw_only_count': 0,
    'has_var_args': False,
    'has_var_kwargs': False,
    'body_length': 2,
    'decorator_count': 0,
    'returns_count': 0,
    'docstring_length': 6,
    'has_sensitive_api': False,
    'sensitive_api_count': 0
}
```

#### 边列表
```python
# factorial 递归调用自己
('factorial', 'factorial', {'call_count': 1, 'lineno': 6})

# process_data 调用 factorial
('process_data', 'factorial', {'call_count': 1, 'lineno': 11})

# main 调用 process_data
('main', 'process_data', {'call_count': 1, 'lineno': 17})
```



## 四、属性字典访问方法

### 4.1 CFG 访问示例

```python
import networkx as nx
from graph_builder_v2 import build_program_graphs_v2
from ast_parser import parse_code_to_ast

# 解析代码
source_code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
ast_tree = parse_code_to_ast(source_code)

# 构建图
cfgs, fcg = build_program_graphs_v2(ast_tree, source_code)

# 获取 factorial 函数的 CFG
cfg = cfgs['factorial']

# 访问节点属性
for node_id in cfg.nodes():
    node_data = cfg.nodes[node_id]
    print(f"节点ID: {node_id}")
    print(f"  类型: {node_data['node_type']}")
    print(f"  代码: {node_data['code_snippet_raw_text']}")
    print(f"  行号: {node_data.get('lineno', 'N/A')}")
    print(f"  特征维度: {node_data['feature_vector'].shape}")
    print()

# 访问边属性
for u, v, edge_data in cfg.edges(data=True):
    print(f"边: {u} -> {v}")
    print(f"  类型: {edge_data['edge_type']}")
    if 'is_back_edge' in edge_data:
        print(f"  回边: {edge_data['is_back_edge']}")
    print()
```

### 4.2 FCG 访问示例

```python
# 访问 FCG 节点属性
for func_name in fcg.nodes():
    node_data = fcg.nodes[func_name]
    print(f"函数: {func_name}")
    print(f"  参数数量: {node_data['args_count']}")
    print(f"  函数体长度: {node_data['body_length']}")
    print(f"  敏感API: {node_data['has_sensitive_api']}")
    print(f"  敏感API次数: {node_data['sensitive_api_count']}")
    print()

# 访问 FCG 边属性
for caller, callee, edge_data in fcg.edges(data=True):
    print(f"调用: {caller} -> {callee}")
    print(f"  调用次数: {edge_data['call_count']}")
    print(f"  首次调用行号: {edge_data['lineno']}")
    print()
```

### 4.3 批量访问和统计

```python
# 统计 CFG 中的敏感API调用
sensitive_nodes = []
for node_id, node_data in cfg.nodes(data=True):
    if node_data.get('is_sensitive_api', False):
        sensitive_nodes.append({
            'node_id': node_id,
            'pattern': node_data['sensitive_pattern'],
            'code': node_data['code_snippet_raw_text'],
            'lineno': node_data['lineno']
        })

print(f"发现 {len(sensitive_nodes)} 个敏感API调用")
for item in sensitive_nodes:
    print(f"  行 {item['lineno']}: {item['pattern']} - {item['code']}")

# 统计 FCG 中的函数复杂度
for func_name, node_data in fcg.nodes(data=True):
    complexity_score = (
        node_data['body_length'] * 0.3 +
        node_data['args_count'] * 0.2 +
        node_data['returns_count'] * 0.1 +
        node_data['sensitive_api_count'] * 0.4
    )
    print(f"{func_name}: 复杂度分数 = {complexity_score:.2f}")
```

## 五、特殊说明

### 5.1 特征向量维度

- **CFG 节点特征向量**：256 维（使用 CodeBERT 提取）
- **维度来源**：`config.model.node_feature_dim = 256`
- **提取方法**：`feature_extractor.extract_node_features()`
- **数据类型**：`np.ndarray`, `dtype=float32`

### 5.2 敏感API检测

敏感API模式包括（但不限于）：

| 模式 | 说明 | 风险等级 |
|------|------|---------|
| `os.system` | 执行系统命令 | 高 |
| `subprocess.run` | 执行子进程 | 高 |
| `subprocess.Popen` | 创建子进程 | 高 |
| `eval` | 动态执行代码 | 高 |
| `exec` | 动态执行代码 | 高 |
| `open` | 文件操作 | 中 |
| `socket.socket` | 网络通信 | 中 |
| `pickle.loads` | 反序列化 | 中 |

### 5.3 圈复杂度计算

- **公式**：`E - N + 2P`（McCabe 圈复杂度）
  - E: 边数
  - N: 节点数
  - P: 连通分量数（通常为 1）
- **最小值**：1
- **典型值**：1-10（简单函数），10-20（中等复杂），>20（高复杂度）

### 5.4 节点ID命名规范

- **格式**：`{函数名}::{节点类型}_{行号}`
- **示例**：
  - `factorial::entry` - 入口节点
  - `factorial::if_3` - 第3行的IF节点
  - `process_data::call_12` - 第12行的CALL节点
  - `main::exit` - 出口节点

### 5.5 可选属性

某些属性只在特定节点类型中存在：

| 属性 | 存在于 | 说明 |
|------|--------|------|
| `is_sensitive_api` | CALL 节点 | 是否为敏感API调用 |
| `sensitive_pattern` | CALL 节点 | 敏感API模式名称 |
| `is_back_edge` | LOOP_BACK 边 | 标识循环回边 |

## 六、使用建议

### 6.1 特征提取

```python
# 提取节点特征用于GNN训练
node_features = []
for node_id in cfg.nodes():
    feature_vector = cfg.nodes[node_id]['feature_vector']
    node_features.append(feature_vector)

# 转换为张量
import torch
X = torch.tensor(np.array(node_features), dtype=torch.float)
```

### 6.2 安全分析

```python
# 检测函数是否包含敏感操作
def is_function_suspicious(fcg, func_name):
    node_data = fcg.nodes[func_name]
    
    # 检查敏感API
    if node_data['has_sensitive_api']:
        return True, f"包含 {node_data['sensitive_api_count']} 个敏感API调用"
    
    # 检查复杂度
    if node_data['body_length'] > 50:
        return True, "函数体过长"
    
    return False, "正常"

# 应用检测
for func_name in fcg.nodes():
    is_suspicious, reason = is_function_suspicious(fcg, func_name)
    if is_suspicious:
        print(f"⚠️  {func_name}: {reason}")
```

### 6.3 图可视化

```python
import matplotlib.pyplot as plt

# 可视化 CFG
pos = nx.spring_layout(cfg)
node_colors = []
for node_id in cfg.nodes():
    if cfg.nodes[node_id].get('is_sensitive_api', False):
        node_colors.append('red')
    elif cfg.nodes[node_id]['has_conditional_branch']:
        node_colors.append('yellow')
    else:
        node_colors.append('lightblue')

nx.draw(cfg, pos, node_color=node_colors, with_labels=True, 
        node_size=500, font_size=8, arrows=True)
plt.title("Control Flow Graph")
plt.show()
```

## 七、总结

本文档详细说明了 CFG 和 FCG 的节点和边属性字典格式：

### CFG（控制流图）
- **节点**：包含 8-10 个属性，核心是 `node_type`、`code_snippet_raw_text` 和 `feature_vector`
- **边**：包含 1-2 个属性，核心是 `edge_type`

### FCG（函数调用图）
- **节点**：包含 12 个属性，描述函数的参数、结构和安全特征
- **边**：包含 2 个属性，记录调用次数和位置

这些属性为 GNN 模型提供了丰富的特征信息，支持容器逃逸检测等安全分析任务。
