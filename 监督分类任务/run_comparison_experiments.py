#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
融合特征恶意代码分类 - 对比实验脚本

运行所有推荐的分类模型，生成对比结果
"""

import numpy as np
import torch
import argparse
import json
import time
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from fusion_classifier_models import (
    ClassifierFactory, DeepLearningTrainer, ComparisonExperiment,
    MLPClassifier, BiLSTMClassifier, TransformerClassifier, ResNet1DClassifier,
    logger
)


# # 注释掉调试器代码，生产环境不需要
# import debugpy
# try:
#     debugpy.listen(("localhost", 9501))
#     print("Waiting for debugger attach")
#     debugpy.wait_for_client()
# except Exception as e:
#     pass


# ==================== 数据加载与预处理 ====================

def load_fusion_features(fusion_dir: str, label_file: str) -> tuple:
    """
    加载融合特征（已经融合好的特征向量）
    
    参数:
        fusion_dir: 融合特征目录（.npy文件，由feature_integration.py生成）
        label_file: 标签文件（CSV格式）
        
    返回:
        (X, y, file_paths)
    """
    logger.info("加载融合特征...")
    
    # 加载标签
    label_df = pd.read_csv(label_file)
    file_to_label = dict(zip(label_df['file_path'], label_df['label']))
    
    X_list = []
    y_list = []
    file_paths = []
    
    # 遍历融合特征文件
    fusion_path = Path(fusion_dir)
    if not fusion_path.exists():
        raise FileNotFoundError(f"融合特征目录不存在: {fusion_dir}")
    
    fusion_files = list(fusion_path.glob('*.npy'))
    if not fusion_files:
        raise FileNotFoundError(f"融合特征目录中没有找到.npy文件: {fusion_dir}")
    
    logger.info(f"在目录 {fusion_dir} 中找到 {len(fusion_files)} 个融合特征文件")
    
    for fusion_file in fusion_files:
        file_name = fusion_file.stem
        
        # 加载融合特征
        try:
            fused_feat = np.load(fusion_file)  # (256,) 或其他维度
            
            # 查找标签
            if file_name in file_to_label:
                label = file_to_label[file_name]
                X_list.append(fused_feat)
                y_list.append(label)
                file_paths.append(file_name)
            else:
                logger.warning(f"找不到标签: {file_name}")
        except Exception as e:
            logger.error(f"加载融合特征失败: {fusion_file}, 错误: {e}")
            continue
    
    if not X_list:
        raise ValueError("没有成功加载任何融合特征，请检查特征文件和标签文件")
    
    X = np.array(X_list)
    y = np.array(y_list)
    
    logger.info(f"加载完成: {len(X)} 个样本")
    logger.info(f"  特征维度: {X.shape[1]}")
    logger.info(f"  正常样本: {sum(y == 0)}")
    logger.info(f"  恶意样本: {sum(y == 1)}")
    
    return X, y, file_paths


def prepare_data(X: np.ndarray, y: np.ndarray, 
                train_ratio: float = 0.6, val_ratio: float = 0.2,
                random_state: int = 42, normalize: bool = True) -> tuple:
    """
    划分数据集
    
    参数:
        X: 特征数据
        y: 标签
        train_ratio: 训练集比例
        val_ratio: 验证集比例
        random_state: 随机种子
        normalize: 是否标准化（如果为True，返回标准化后的数据和scaler）
    
    返回:
        如果normalize=True: (X_train, X_val, X_test, y_train, y_val, y_test, scaler)
        如果normalize=False: (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    # 划分训练集和测试集
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=1-train_ratio-val_ratio,
        random_state=random_state, stratify=y
    )
    
    # 划分训练集和验证集
    val_ratio_adjusted = val_ratio / (train_ratio + val_ratio)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio_adjusted,
        random_state=random_state, stratify=y_temp
    )
    
    # 标准化（在训练集上fit，然后transform所有集合）
    if normalize:
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_val = scaler.transform(X_val)
        X_test = scaler.transform(X_test)
    
    logger.info(f"数据集划分:")
    logger.info(f"  训练集: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
    logger.info(f"  验证集: {len(X_val)} ({len(X_val)/len(X)*100:.1f}%)")
    logger.info(f"  测试集: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
    
    if normalize:
        return X_train, X_val, X_test, y_train, y_val, y_test, scaler
    else:
        return X_train, X_val, X_test, y_train, y_val, y_test


# ==================== 模型训练与评估 ====================

def run_ml_comparison(X_train: np.ndarray, y_train: np.ndarray,
                     X_val: np.ndarray, y_val: np.ndarray,
                     X_test: np.ndarray, y_test: np.ndarray,
                     output_dir: str = './results') -> dict:
    """
    运行传统机器学习模型对比
    
    注意：数据应该已经标准化，模型内部不再重复标准化
    """
    logger.info("\n" + "="*80)
    logger.info("传统机器学习模型对比")
    logger.info("="*80)
    
    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 传统ML模型列表（use_scaler=False因为数据已标准化）
    ml_models = [
        ('logistic_regression', {'use_scaler': False}),  # 外部数据已经标准化，模型内部不再需要重复标准化（防止数据泄露）
        ('svm', {'C': 1.0, 'gamma': 'scale', 'use_scaler': False}),
        ('random_forest', {'n_estimators': 100}),  # 基线参数（如树的数量为100），用于快速对比
        ('xgboost', {'n_estimators': 100}),
        ('lightgbm', {'n_estimators': 100})
    ]  # 树模型（随机森林、XGBoost、LightGBM）对特征尺度不敏感，无需标准化，因此不传入 use_scaler
    
    results = {}
    
    for model_name, params in ml_models:
        try:
            logger.info(f"训练 {model_name}...")
            
            classifier = ClassifierFactory.create_classifier(model_name, **params)
            classifier.fit(X_train, y_train)
            
            # 评估
            train_metrics = classifier.evaluate(X_train, y_train)
            val_metrics = classifier.evaluate(X_val, y_val)
            test_metrics = classifier.evaluate(X_test, y_test)
            
            results[model_name] = {
                'train': train_metrics,
                'val': val_metrics,
                'test': test_metrics
            }
            
            logger.info(f"{model_name} - Test Acc: {test_metrics['accuracy']:.4f}, "
                       f"F1: {test_metrics['f1']:.4f}, AUC: {test_metrics['auc']:.4f}")
        
        except Exception as e:
            logger.error(f"训练 {model_name} 时出错: {e}")
            continue
    
    # 保存结果
    results_file = Path(output_dir) / 'ml_comparison_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n传统ML结果已保存到: {results_file}")
    
    return results


def run_dl_comparison(X_train: np.ndarray, y_train: np.ndarray,
                     X_val: np.ndarray, y_val: np.ndarray,
                     X_test: np.ndarray, y_test: np.ndarray,
                     output_dir: str = './results',
                     epochs: int = 50, batch_size: int = 32) -> dict:
    """
    运行深度学习模型对比
    """
    logger.info("\n" + "="*80)
    logger.info("深度学习模型对比")
    logger.info("="*80)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 检测输入维度
    input_dim = X_train.shape[1]
    logger.info(f"输入特征维度: {input_dim}")
    
    # 转换为PyTorch张量
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_val_t = torch.tensor(X_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.long)
    
    # 创建数据加载器
    train_dataset = TensorDataset(X_train_t, y_train_t)
    val_dataset = TensorDataset(X_val_t, y_val_t)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # 模型列表
    dl_models = [
        ('mlp', {'hidden_dims': [512, 256, 128]}),
        ('bilstm', {'hidden_dim': 128, 'num_layers': 2}),
        ('transformer', {'d_model': 128, 'nhead': 4, 'num_layers': 2}),
        ('resnet1d', {'num_blocks': 3})
    ]
    
    results = {}
    
    for model_name, params in dl_models:
        try:
            logger.info(f"\n训练 {model_name}...")
            
            # 创建模型
            model = ClassifierFactory.create_dl_model(model_name, input_dim=input_dim, **params)
            
            # 训练
            trainer = DeepLearningTrainer(model, learning_rate=0.001)
            history = trainer.fit(train_loader, val_loader, epochs=epochs, patience=15)
            
            # 评估（使用批处理避免内存溢出）
            test_pred, test_proba = trainer.predict(X_test, batch_size=batch_size)
            
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
            
            test_metrics = {
                'accuracy': float(accuracy_score(y_test, test_pred)),
                'precision': float(precision_score(y_test, test_pred, zero_division=0)),
                'recall': float(recall_score(y_test, test_pred, zero_division=0)),
                'f1': float(f1_score(y_test, test_pred, zero_division=0)),
                'auc': float(roc_auc_score(y_test, test_proba[:, 1]))
            }
            
            results[model_name] = {
                'test': test_metrics,
                'history': history
            }
            
            logger.info(f"{model_name} - Test Acc: {test_metrics['accuracy']:.4f}, "
                       f"F1: {test_metrics['f1']:.4f}, AUC: {test_metrics['auc']:.4f}")
            
            # 保存模型
            model_path = Path(output_dir) / f'{model_name}_best_model.pth'
            trainer.save_model(str(model_path))
        
        except Exception as e:
            logger.error(f"训练 {model_name} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 保存结果
    results_file = Path(output_dir) / 'dl_comparison_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n深度学习结果已保存到: {results_file}")
    
    return results


# ==================== 结果可视化 ====================

def visualize_results(ml_results: dict, dl_results: dict, output_dir: str = './results'):
    """
    可视化对比结果
    """
    logger.info("\n生成可视化图表...")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 提取指标
    all_results = {}
    
    # 传统ML模型
    for model_name, metrics in ml_results.items():
        all_results[model_name] = metrics['test']
    
    # 深度学习模型
    for model_name, metrics in dl_results.items():
        all_results[model_name] = metrics['test']
    
    if not all_results:
        logger.warning("没有可视化的结果")
        return
    
    # 创建对比表
    df = pd.DataFrame(all_results).T
    
    # 设置中文字体（避免中文乱码）
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    except:
        logger.warning("无法设置中文字体，图表标题可能显示为方框")
    
    # 绘制对比图
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    
    metrics = ['accuracy', 'precision', 'recall', 'f1', 'auc']
    metric_names = {
        'accuracy': '准确率 (Accuracy)',
        'precision': '精确率 (Precision)',
        'recall': '召回率 (Recall)',
        'f1': 'F1分数 (F1-Score)',
        'auc': 'AUC'
    }
    
    for idx, metric in enumerate(metrics):
        if metric not in df.columns:
            continue
        
        ax = axes[idx]
        df[metric].plot(kind='bar', ax=ax, color='steelblue', alpha=0.8)
        ax.set_title(metric_names.get(metric, metric.upper()), fontsize=12, fontweight='bold')
        ax.set_ylabel('分数')
        ax.set_xlabel('模型')
        ax.set_ylim([0, 1.05])
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 在柱状图上添加数值标签
        for i, v in enumerate(df[metric]):
            ax.text(i, v + 0.02, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 隐藏多余的子图
    for idx in range(len(metrics), len(axes)):
        axes[idx].axis('off')
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'model_comparison.png', dpi=300, bbox_inches='tight')
    logger.info(f"对比图已保存到: {Path(output_dir) / 'model_comparison.png'}")
    
    # 保存对比表
    df.to_csv(Path(output_dir) / 'model_comparison.csv', encoding='utf-8-sig')
    logger.info(f"对比表已保存到: {Path(output_dir) / 'model_comparison.csv'}")
    
    # 打印对比表
    logger.info("\n模型性能对比表:")
    logger.info(df.to_string())
    
    # 找出最佳模型
    logger.info("\n最佳模型:")
    for metric in metrics:
        if metric in df.columns:
            best_model = df[metric].idxmax()
            best_score = df[metric].max()
            logger.info(f"  {metric_names.get(metric, metric)}: {best_model} ({best_score:.4f})")


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description="融合特征恶意代码分类对比实验")
    
    parser.add_argument("--fusion-dir", type=str, required=True,
                       help="融合特征目录（由feature_integration.py生成的.npy文件）")
    parser.add_argument("--label-file", type=str, required=True,
                       help="标签文件（CSV格式，包含file_path和label列）")
    parser.add_argument("--output-dir", type=str, default="./comparison_results",
                       help="输出目录")
    parser.add_argument("--epochs", type=int, default=50,
                       help="深度学习模型训练轮数")
    parser.add_argument("--batch-size", type=int, default=16,
                       help="批大小")
    parser.add_argument("--skip-ml", action="store_true",
                       help="跳过传统ML模型")
    parser.add_argument("--skip-dl", action="store_true",
                       help="跳过深度学习模型")
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("融合特征恶意代码分类 - 对比实验")
    logger.info("="*80)
    
    # 加载数据
    try:
        X, y, file_paths = load_fusion_features(
            args.fusion_dir,
            args.label_file
        )
    except Exception as e:
        logger.error(f"加载数据失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 划分数据集（标准化）
    result = prepare_data(X, y, normalize=True)
    if len(result) == 7:
        X_train, X_val, X_test, y_train, y_val, y_test, scaler = result
    else:
        X_train, X_val, X_test, y_train, y_val, y_test = result
    
    ml_results = {}
    dl_results = {}
    
    # 运行传统ML模型
    if not args.skip_ml:
        ml_results = run_ml_comparison(X_train, y_train, X_val, y_val, X_test, y_test, args.output_dir)
    
    # 运行深度学习模型
    if not args.skip_dl:
        dl_results = run_dl_comparison(X_train, y_train, X_val, y_val, X_test, y_test,
                                      args.output_dir, args.epochs, args.batch_size)
    
    # 可视化结果
    if ml_results or dl_results:
        visualize_results(ml_results, dl_results, args.output_dir)
    
    logger.info("\n" + "="*80)
    logger.info("对比实验完成！")
    logger.info("="*80)


if __name__ == "__main__":
    main()
