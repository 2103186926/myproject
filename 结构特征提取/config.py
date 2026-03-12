#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块
统一管理所有训练和模型参数
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import json


@dataclass
class ModelConfig:
    """GNN模型配置"""
    # CFG模型参数
    cfg_hidden_channels: int = 256  # 增加到256以提升表达能力
    cfg_out_channels: int = 128  # CFG输出128维
    cfg_num_layers: int = 4  # 增加层数以捕获更深层次的结构
    cfg_dropout: float = 0.3
    # cfg_pooling: str = 'mean'  # 对每个图中的所有节点特征取平均(应用于GCN池化层)
    cfg_pooling: str = 'attention'  # 可学习节点重要性，比平均池化更具表达能力
    
    # FCG模型参数
    fcg_hidden_channels: int = 256
    fcg_out_channels: int = 128  # FCG输出128维
    fcg_num_layers: int = 3
    fcg_dropout: float = 0.3
    fcg_pooling: str = 'attention'  # 使用注意力池化
    
    # 最终嵌入维度 (CFG 128 + FCG 128 = 256)
    final_embedding_dim: int = 256
    
    # 特征提取参数（优化版）
    node_feature_dim: int = 256  # 节点特征维度（优化：从128提升到256）
    edge_feature_dim: int = 32  # 边特征维度
    text_embedding_dim: int = 256  # CodeBERT降维后的维度（从768降到256）
    
    # CodeBERT配置
    embedding_model_type: str = 'CodeBERTa-small-v1'  # 可选: 'codebert-base', 'codebert-base-mlm', 'CodeBERTa-small-v1', 'graphcodebert-base'
    embedding_model_paths: Dict[str, str] = field(default_factory=lambda: {
        'codebert-base': './CodeBert/codebert-base',
        'codebert-base-mlm': './CodeBert/codebert-base-mlm',
        'CodeBERTa-small-v1': './CodeBert/CodeBERTa-small-v1',  # 首选：推理速度快2倍，内存占用少40%
        'graphcodebert-base': './CodeBert/graphcodebert-base'  # 次选：如果需要最佳检测性能和控制流理解
    })
    use_codebert: bool = True
    codebert_max_length: int = 512
    codebert_use_projection: bool = True  # 是否使用线性投影降维
    codebert_finetune: bool = False  #! 是否微调CodeBERT（训练时可设为True）
    
    @property
    def codebert_model_path(self) -> str:
        """根据选择的模型类型返回对应的路径"""
        return self.embedding_model_paths.get(self.embedding_model_type, self.embedding_model_paths['codebert-base'])


@dataclass
class TrainingConfig:
    """训练配置"""
    # 训练参数
    cfg_epochs: int = 100
    fcg_epochs: int = 80
    batch_size: int = 16
    learning_rate: float = 0.001
    weight_decay: float = 5e-4
    
    # 早停参数
    early_stopping: bool = True
    patience: int = 15  # 早停耐心值
    min_delta: float = 0.001  # 最小误差
    
    # 学习率调度
    use_scheduler: bool = True  # 学习率调度器
    scheduler_type: str = 'ReduceLROnPlateau'  # 或 'StepLR', 'CosineAnnealingLR'
    scheduler_patience: int = 10  # 容忍10个 epoch 指标不改善后才降低学习率
    scheduler_factor: float = 0.5  # 学习率缩放因子，如 0.5 表示新学习率 = 原学习率 × 0.5
    
    # 数据集划分
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # 设备配置
    gpu_id: int = 0
    use_gpu: bool = True
    num_workers: int = 4
    
    # 随机种子
    seed: int = 42


@dataclass
class DataConfig:
    """数据配置"""
    # 路径配置
    source_dir: str = ""
    output_dir: str = "./output"
    log_dir: str = "./logs"
    model_dir: str = "./models"
    
    # 图过滤参数
    min_nodes: int = 3  # 提高最小节点数
    max_nodes: int = 500
    min_edges: int = 2
    
    # 数据处理
    cpu_count: Optional[int] = None
    cache_parsed_ast: bool = True
    cache_dir: str = "./cache"


@dataclass
class ContainerEscapeConfig:
    """容器逃逸检测特定配置"""
    # 敏感API模式（扩展）
    sensitive_api_patterns: List[str] = field(default_factory=lambda: [
        # 系统命令执行
        r'os\.(system|popen|exec[vl]?[pe]?|spawn[vl]?[pe]?|fork)',
        r'subprocess\.(Popen|call|check_output|check_call|run)',
        r'commands\.(getoutput|getstatusoutput)',
        
        # 代码执行
        r'eval', r'exec', r'compile',
        r'__import__',
        
        # 序列化/反序列化
        r'pickle\.(load|loads|dump|dumps)',
        r'marshal\.(load|loads|dump|dumps)',
        r'yaml\.(load|load_all|unsafe_load)',
        r'json\.(load|loads)',
        
        # 网络操作
        r'socket\.(socket|create_connection|create_server)',
        r'requests\.(get|post|put|delete|patch|head|options)',
        r'urllib\.(request|urlopen|urlretrieve)',
        r'http\.client\.',
        
        # 文件系统操作
        r'open\s*\(',
        r'shutil\.(copy|copy2|copytree|move|rmtree)',
        r'os\.(remove|unlink|rmdir|mkdir|makedirs|rename|chmod|chown)',
        r'pathlib\.Path\.(write_text|write_bytes|unlink|rmdir)',
        
        # 容器特定操作
        r'/proc/.*',
        r'/sys/.*',
        r'/dev/.*',
        r'cgroup',
        r'namespace',
        r'docker\.',
        r'kubernetes\.',
        r'containerd\.',
        
        # 权限提升
        r'setuid|setgid|seteuid|setegid',
        r'sudo|su\s',
        r'chmod\s+[0-9]*7[0-9]*',
        
        # 临时文件和随机数
        r'tempfile\.',
        r'random\.',
        r'secrets\.',
        
        # 加密和编码
        r'hashlib\.',
        r'base64\.',
        r'crypt\.',
        r'cryptography\.',
    ])
    
    # 敏感路径模式
    sensitive_path_patterns: List[str] = field(default_factory=lambda: [
        r'/proc/self/.*',
        r'/sys/fs/cgroup/.*',
        r'/var/run/docker\.sock',
        r'/etc/passwd',
        r'/etc/shadow',
        r'/root/.*',
        r'\.ssh/.*',
        r'\.kube/.*',
    ])
    
    # 检测权重
    sensitive_api_weight: float = 2.0
    sensitive_path_weight: float = 1.5
    complexity_weight: float = 1.0


@dataclass
class Config:
    """主配置类"""
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    data: DataConfig = field(default_factory=DataConfig)
    container_escape: ContainerEscapeConfig = field(default_factory=ContainerEscapeConfig)
    
    @classmethod
    def from_json(cls, json_path: str) -> 'Config':
        """从JSON文件加载配置"""
        with open(json_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return cls(
            model=ModelConfig(**config_dict.get('model', {})),
            training=TrainingConfig(**config_dict.get('training', {})),
            data=DataConfig(**config_dict.get('data', {})),
            container_escape=ContainerEscapeConfig(**config_dict.get('container_escape', {}))
        )
    
    def to_json(self, json_path: str) -> None:
        """保存配置到JSON文件"""
        config_dict = {
            'model': self.model.__dict__,
            'training': self.training.__dict__,
            'data': self.data.__dict__,
            'container_escape': self.container_escape.__dict__
        }
        
        os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        # 验证维度一致性
        assert self.model.cfg_out_channels + self.model.fcg_out_channels == self.model.final_embedding_dim, \
            f"CFG输出({self.model.cfg_out_channels}) + FCG输出({self.model.fcg_out_channels}) 必须等于最终嵌入维度({self.model.final_embedding_dim})"
        
        # 验证数据集划分
        total_ratio = self.training.train_ratio + self.training.val_ratio + self.training.test_ratio
        assert abs(total_ratio - 1.0) < 0.01, f"数据集划分比例之和必须为1.0，当前为{total_ratio}"
        
        # 验证路径
        if self.data.source_dir and not os.path.exists(self.data.source_dir):
            raise ValueError(f"源代码目录不存在: {self.data.source_dir}")
        
        return True


def get_default_config() -> Config:
    """获取默认配置"""
    return Config()


def save_default_config(output_path: str = "./config.json") -> None:
    """保存默认配置到文件"""
    config = get_default_config()
    config.to_json(output_path)
    print(f"默认配置已保存到: {output_path}")


if __name__ == "__main__":
    # 生成默认配置文件
    save_default_config()
    
    # 测试加载配置
    config = Config.from_json("./config.json")
    print("配置加载成功")
    print(f"CFG输出维度: {config.model.cfg_out_channels}")
    print(f"FCG输出维度: {config.model.fcg_out_channels}")
    print(f"最终嵌入维度: {config.model.final_embedding_dim}")
    
    # 验证配置
    try:
        config.validate()
        print("配置验证通过")
    except AssertionError as e:
        print(f"配置验证失败: {e}")
