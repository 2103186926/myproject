### 精简版Python恶意代码静态分析工具类 (目标：代码特征向量提取版)

### **核心目标：** 

为每个Python代码文件生成一个单一的、固定长度的、语义丰富的图嵌入向量。我需要的是一个经过GNN学习并序列化后的、固定长度的、代表代码语义的特征向量（`.npy`格式），而不是最终的分类结果。

#### 1. `dataset_loader.py` - 数据集加载工具
*   **功能:** 加载原始Python源码文件，并准备好其路径。虽然您不需要标签进行分类，但在实际训练GNN时，通常仍需要区分不同样本，或者至少有一个文件路径列表。
*   **输入**:
    - `data_root_dir` (`str`): 包含Python源码文件的根目录。
*   **输出:** `List[str]`，包含所有Python源码文件的完整路径。
*   **示例方法:** `load_code_paths(data_root_dir)`

#### 2. `ast_parser.py` - 抽象语法树 (AST) 解析工具 
*   **功能:** 将Python源代码文件解析为抽象语法树 (AST) 对象。
*   **输入**:`code_file_path` (`str`): Python源代码文件的完整路径。
*   **输出:** `ast.Module` 对象，表示解析后的AST。如果解析失败，则返回 `None` 或抛出异常。
*   **示例方法:** `parse_code_to_ast(code_file_path)`
*   **作用:** 将非结构化代码转换为结构化数据，为图构建做准备。

#### 3. `feature_extractor.py` - 基础特征提取工具 
* **功能:** 这是一个辅助工具类，提供各种静态特征提取方法，供图构建器调用。它本身不直接参与主流程的输入输出链。

  在整个恶意代码静态分析流程中，`feature_extractor.py` 不像其他工具类那样，直接接收上一个工具的完整输出，并将其加工后完整地传递给下一个工具。**它更像是一个“辅助工具箱”或“功能库”**，提供了许多独立的、原子性的函数，用于从代码的各种形态（如原始文本、AST节点、字节码序列）中提取出**数值化或结构化的特征信息**。**它的核心作用是：为图的节点和边提供“初始的、原始的”特征向量。**

*   **输入:** AST节点、原始代码字符串、字节码序列等。

*   **输出:** 计算出的各种基础特征（数值、布尔值、列表或初始嵌入）。

*   **示例方法** (供其他类调用):

    - `extract_opcode_sequence(code_block_ast_node)`: 从AST节点推断字节码序列。
    - `get_code_snippet_raw_text(ast_node, full_code_string)`: 获取AST节点对应的代码片段文本。
    - `detect_sensitive_apis(ast_call_node)`: 检测API调用是否敏感。
    - `calculate_cyclomatic_complexity(cfg_networkx_graph)`: 计算给定CFG的圈复杂度。
    - `get_text_embedding(text_string, model)`: 使用预训练的NLP模型（如CodeBERT）将文本转换为向量。

*   **作用:** 为 `graph_builder.py` 构建的图的节点和边提供原始、原子级别的特征，这些特征是GNN学习的基础。

*   **主要由 `graph_builder.py` 调用：**

    - 当 `graph_builder.py` 在构建CFG或FCG时，每当它创建一个新的节点（例如，一个CFG的基本块、一个FCG的函数）或一条新的边（例如，CFG的跳转边、FCG的函数调用边），它需要为这些节点和边填充属性（features）。
    - 此时，`graph_builder.py` 会调用 `feature_extractor.py` 中的相应函数，例如：
      - 要为CFG节点获取代码片段的语义嵌入，它会调用 `feature_extractor.get_text_embedding(code_snippet_text, model)`。
      - 要为FCG节点计算圈复杂度，它会调用 `feature_extractor.calculate_cyclomatic_complexity(this_function_cfg_graph)`。
      - 要检测一个函数是否调用了敏感API，它会调用 `feature_extractor.detect_sensitive_apis(ast_call_node)`。
    - `feature_extractor.py` 返回这些计算出的特征值（例如，一个向量、一个整数、一个布尔值），然后 `graph_builder.py` 会将这些值作为属性存储到 `networkx` 图的节点或边中。

*   （次要）**`graph_converter.py`**: 如果在将`networkx`图转换为GNN框架数据时，需要对一些原始特征进行额外的组合或预处理，`feature_extractor.py` 也可以提供辅助函数。

#### 4. `graph_builder.py` - CFG与FCG构建工具
* **功能:** 统一构建一个Python程序的所有CFG（按函数）和全局FCG。它会集成`feature_extractor`来丰富图的节点和边属性。

*   **输入**:

    - `ast_object` (`ast.Module`): 由 `ast_parser.py` 提供的AST对象。
    - `code_string` (`str`): 完整的Python源代码字符串，用于提取代码片段。

    **输出:** `Tuple[Dict[str, networkx.DiGraph], networkx.DiGraph]`

    - `Dict[str, networkx.DiGraph]`: 键是函数名，值是该函数的CFG图。

      - **CFG节点属性:** `node_id`, `node_type`, `code_snippet_raw_text`, `opcode_sequence`, `has_conditional_branch`, `initial_feature_vector` (结合`feature_extractor`的输出)。
      - **CFG边属性:** `edge_type`, `condition_expression`, `is_back_edge`, `initial_feature_vector` (结合`feature_extractor`的输出)。

      `networkx.DiGraph`: 程序的FCG图。

      - **FCG节点属性:** `function_id`, `function_name`, `parameters_count`, `has_var_args`, `has_var_kwargs`, `return_type_hint`, `is_sensitive_api` (结合`feature_extractor`的输出), `internal_complexity` (调用`feature_extractor`计算其对应CFG的复杂度)。
      - **FCG边属性:** `call_location_file`, `call_location_lineno`, `is_dynamic_call`, `arguments_count`, `initial_feature_vector` (结合`feature_extractor`的输出)。

*   **示例方法:** `build_program_graphs(ast_object, code_string)`

*   **作用:** 将代码语义转换为图结构，这是GNN的直接输入形式。

#### 5. `graph_converter.py` - 图数据格式转换工具 
*   **功能:** 将`networkx`图对象及其包含的特征转换为特定GNN框架（如PyTorch Geometric或DGL）的数据对象,所需的格式（邻接矩阵、节点特征矩阵、边特征矩阵）
*   **输入**:
    - `networkx_graph` (`networkx.DiGraph`): 待转换的CFG或FCG图。
    - node_feature_keys` (`List[str]`): 指定哪些节点属性应被组合为节点特征向量。`
    - edge_feature_keys` (`List[str]`): 指定哪些边属性应被组合为边特征向量。`

- **输出:** 特定GNN框架的图数据对象（如`torch_geometric.data.Data` 或 `dgl.DGLGraph`），包含：
  - `edge_index`: 边的索引。
  - `x`: 节点特征矩阵。
  - `edge_attr`: 边特征矩阵。

- **示例方法:** `convert_to_gnn_data(networkx_graph, node_feature_keys, edge_feature_keys)`
- **作用:** 桥接通用的图库（NetworkX）和特定的深度学习图库（PyG/DGL）。

#### 6. `gnn_trainer.py` - 图神经网络训练工具

*   **功能:** 负责GNN模型的训练。这是一个两阶段训练过程。即使没有分类任务，GNN也需要通过某种代理任务（如图重构、节点属性预测、对比学习等）来训练，才能学习到有意义的嵌入。在这里，我们假设GNN会通过某种自监督或无监督的方式（如果不需要标签的话），或者仍然使用（可能假定的）良/恶意标签进行训练以学习区分性特征。**训练是获取“经过GNN学习过”的特征的必要步骤。**
*   **输入:**
    *   `list_of_cfg_data` (`List[torch_geometric.data.Data]`): 程序的CFG列表。
    *   `list_of_fcg_data` (`List[torch_geometric.data.Data]`): 程序的FCG列表（**此时FCG节点特征仍为初始特征**）。
    *   `cfg_gnn_model` (`torch.nn.Module`): CFG层GNN模型实例。
    *   `fcg_gnn_model` (`torch.nn.Module`): FCG层GNN模型实例。
    *   `training_config` (`Dict`): 包含批大小、学习率、epochs、**以及GNN的训练目标/损失函数配置**。
    *   **注意:** 由于最终目标是程序级的嵌入，FCG GNN模型的设计需要包含一个**全局池化（Global Pooling）层**（如`global_mean_pool`, `global_add_pool`），使其输出一个**单一的图级向量**，而不是每个节点的向量。训练时，可以设计一个自监督任务（如图重构）或简单的分类代理任务（如果需要辅助学习）来优化这个图级向量。
*   **输出:** `Tuple[torch.nn.Module, torch.nn.Module]`：训练好的 `cfg_gnn_model` 和 `fcg_gnn_model` 实例。

- 核心逻辑:
  1. 阶段一：CFG GNN训练:训练`cfg_gnn_model`使其能有效地将CFG图转换为图级嵌入。
     - 使用`list_of_cfg_data`训练`cfg_gnn_model`，目标是使其能有效地将CFG图转换为图级嵌入。
  2. 阶段二：FCG GNN训练（结合CFG嵌入）:使用**训练好的`cfg_gnn_model`** 为FCG节点生成嵌入并将其附加到FCG节点特征上，然后训练`fcg_gnn_model`。这里的训练目标不再是分类，而是为了生成高质量的、包含代码语义的节点嵌入（例如，通过图自编码器、对比学习等）。
     - **关键步骤:** 在训练`fcg_gnn_model`之前，需要使用**训练好的`cfg_gnn_model`** 为`list_of_fcg_data`中的每个FCG节点（代表一个函数）生成其对应的CFG嵌入。然后将这个CFG嵌入**附加到FCG节点原有的特征向量上**，形成增强的FCG节点特征。
     - 使用增强后的`list_of_fcg_data`训练`fcg_gnn_model`。
- **示例方法:** `train_gnn_models(list_of_cfg_data, list_of_fcg_data, cfg_gnn_model, fcg_gnn_model, training_config)`

*   **作用:** 使GNN模型能够从代码的图结构中学习深层语义表示。

#### 7. `graph_embedding_generator.py` - 图嵌入生成工具
*   **功能:** 利用训练好的GNN模型，生成每个程序的最终、固定长度的FCG节点嵌入向量。
*   **输入:**
    *   `trained_cfg_gnn_model` (`torch.nn.Module`): 训练好的CFG GNN模型。
    *   `trained_fcg_gnn_model` (`torch.nn.Module`): 训练好的FCG GNN模型（**其输出层设计为全局池化**）。
    *   `program_cfg_data_map` (`Dict[str, List[torch_geometric.data.Data]]`): 映射程序ID到其包含的所有CFG图数据列表。
    *   `program_fcg_data_map` (`Dict[str, torch_geometric.data.Data]`): 映射程序ID到其FCG图数据（初始特征）。
*   **输出:** `Dict[str, torch.Tensor]`，映射程序ID到该程序FCG中所有节点的最终嵌入向量矩阵（形状：`num_fcg_nodes_in_program x embedding_dim`）。
*   **示例方法:** `generate_program_node_embeddings(trained_cfg_gnn_model, trained_fcg_gnn_model, program_cfg_data_map, program_fcg_data_map)`
*   **核心逻辑:**
    1.  对于每个程序：
        a.  获取其所有CFG数据。
        b.  使用`trained_cfg_gnn_model`，为每个CFG生成图级嵌入（即每个函数的语义嵌入）。
        c.  获取程序的FCG数据。
        d.  将步骤b中生成的CFG嵌入，作为对应FCG节点的特征，更新FCG数据对象的节点特征。
        e.  使用`trained_fcg_gnn_model`（包含全局池化层），在更新后的FCG数据上进行前向传播，得到该程序一个固定长度的整体嵌入向量。
*   **作用:** 这是直接满足您核心需求的工具类，它负责将整个程序抽象为一个单一的语义向量。

#### 8. **`graph_sequentializer.py` - 图序列化工具**
*   **功能:** 将GNN生成的FCG节点嵌入向量集合，转换为**固定长度的序列**。这是您目标中“固定长度特征向量”的关键步骤。
*   **输入**:
    - `program_node_embeddings_map` (`Dict[str, torch.Tensor]`): 映射程序ID到FCG节点嵌入矩阵。
    - `program_fcg_networkx_map` (`Dict[str, networkx.DiGraph]`): 映射程序ID到FCG图结构（用于遍历）。
    - `max_sequence_length` (`int`): 目标固定序列长度。
    - `walk_strategy` (`str`): 序列生成策略（例如，`"random_walk"`, `"dfs_traversal"`, `"bfs_traversal"`等）。
*   **输出:** `Dict[str, torch.Tensor]`，映射程序ID到该程序的固定长度特征序列（形状：`max_sequence_length x embedding_dimension`）。
*   **核心逻辑**:
    1. 对每个程序： a. 根据`walk_strategy`在FCG图上进行遍历，生成一条或多条节点路径。 b. 将路径中的每个节点ID替换为其对应的嵌入向量（从`program_node_embeddings_map`中获取）。 c. 对生成的序列进行填充（用零向量）或截断，使其达到`max_sequence_length`。如果生成了多条序列，可能需要平均或拼接成一条。
*   **示例方法:** `convert_embeddings_to_sequences(program_node_embeddings_map, program_fcg_networkx_map, max_sequence_length, walk_strategy)`

#### 9.`feature_saver.py` - 特征保存工具

- **功能:** 将 `graph_sequentializer.py` 生成的固定长度的PyTorch Tensor特征序列，转换为NumPy数组并保存为`.npy`文件。
- **输入**:
  - `program_sequences_map` (`Dict[str, torch.Tensor]`): 映射程序ID到固定长度特征序列。
  - `output_dir` (`str`): 指定保存`.npy`文件的目标目录。
- **输出:** 无直接返回，但会在 `output_dir` 中生成多个`.npy`文件，每个文件代表一个程序的最终特征向量。
- **示例方法:** `save_sequences_to_npy(program_sequences_map, output_dir)`

#### 10.**主实验工作流 `main_workflow.py` **

`main_workflow.py` 将只负责以下步骤：

1. **数据加载:** 调用 `dataset_loader.py` 获取所有源码文件路径。
2. **逐个程序处理（图构建与初始特征化）**:循环处理每个源码文件：
   - 调用 `ast_parser.py` 解析AST。
   - 调用 `graph_builder.py` 构建CFG和FCG（过程中会调用 `feature_extractor.py`）。
   - 收集每个程序的CFG和FCG（`networkx`格式）。
3. **批量图数据转换:** 调用 `graph_converter.py` 将所有收集到的 `networkx` 图转换为GNN框架的数据对象。
4. **GNN模型训练:** 实例化CFG-GNN和FCG-GNN模型，并调用 `gnn_trainer.py` 对其进行训练，使其能学习到有意义的嵌入。
5. **图嵌入生成:** 调用 `graph_embedding_generator.py`，使用训练好的GNN模型为所有程序的FCG节点生成嵌入。
6. **图序列化:** 调用 `graph_sequentializer.py` 将FCG节点嵌入转换为固定长度的序列。
7. **特征保存:** 调用 `feature_saver.py` 将最终的特征序列保存为`.npy`文件。