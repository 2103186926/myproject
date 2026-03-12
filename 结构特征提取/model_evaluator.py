#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型评估模块
提供准确率、召回率、F1分数等指标计算和可视化
"""

import torch
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc, classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Tuple, Optional
from torch_geometric.data import DataLoader
import os

# 解决plt中文乱码问题
plt.rcParams['font.sans-serif'].insert(0, 'SimHei')
plt.rcParams['axes.unicode_minus'] = False

class ModelEvaluator:
    """模型评估器"""
    
    def __init__(self, device: torch.device = None):
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def evaluate(self, model, test_loader: DataLoader, 
                task: str = 'binary') -> Dict[str, float]:
        """
        评估模型性能
        
        参数:
            model: 训练好的模型
            test_loader: 测试数据加载器
            task: 任务类型 ('binary' 或 'edge_prediction')
            
        返回:
            评估指标字典
        """
        model.eval()
        model = model.to(self.device)
        
        all_preds = []
        all_labels = []
        all_probs = []
        
        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(self.device)
                
                if task == 'binary':
                    # 二分类任务
                    _, _, logits = model(batch.x, batch.edge_index, batch.batch)
                    # 使用softmax获取概率分布
                    probs = torch.softmax(logits, dim=1)
                    # 取第二个类别（恶意类，索引1）的概率
                    probs_class1 = probs[:, 1]
                    # 使用argmax获取预测类别
                    preds = torch.argmax(probs, dim=1)
                    
                    if hasattr(batch, 'y'):
                        all_preds.extend(preds.cpu().numpy())
                        all_labels.extend(batch.y.cpu().numpy())
                        all_probs.extend(probs_class1.cpu().numpy())
                
                elif task == 'edge_prediction':
                    # 边预测任务
                    node_emb, _, _ = model(batch.x, batch.edge_index, batch.batch)
                    
                    # 正样本
                    pos_edge_index = batch.edge_index
                    pos_score = (node_emb[pos_edge_index[0]] * 
                               node_emb[pos_edge_index[1]]).sum(dim=1)
                    pos_pred = torch.sigmoid(pos_score)
                    
                    # 负样本
                    try:
                        from torch_geometric.utils import negative_sampling
                        neg_edge_index = negative_sampling(
                            edge_index=pos_edge_index,
                            num_nodes=batch.num_nodes
                        ).to(self.device)
                        
                        neg_score = (node_emb[neg_edge_index[0]] * 
                                   node_emb[neg_edge_index[1]]).sum(dim=1)
                        neg_pred = torch.sigmoid(neg_score)
                        
                        # 合并预测
                        preds = torch.cat([pos_pred, neg_pred])
                        labels = torch.cat([
                            torch.ones_like(pos_pred),
                            torch.zeros_like(neg_pred)
                        ])
                        
                        all_preds.extend((preds > 0.5).long().cpu().numpy())
                        all_labels.extend(labels.cpu().numpy())
                        all_probs.extend(preds.cpu().numpy())
                    except:
                        continue
        
        if not all_labels:
            return {'error': '没有可用的标签数据'}
        
        # 计算指标
        metrics = {
            'accuracy': accuracy_score(all_labels, all_preds),
            'precision': precision_score(all_labels, all_preds, average='binary', zero_division=0),
            'recall': recall_score(all_labels, all_preds, average='binary', zero_division=0),
            'f1': f1_score(all_labels, all_preds, average='binary', zero_division=0),
        }
        
        # 计算AUC
        if all_probs:
            try:
                fpr, tpr, _ = roc_curve(all_labels, all_probs)
                metrics['auc'] = auc(fpr, tpr)
            except:
                metrics['auc'] = 0.0
        
        return metrics
    
    def plot_confusion_matrix(self, model, test_loader: DataLoader,
                             save_path: Optional[str] = None) -> np.ndarray:
        """
        绘制混淆矩阵
        
        返回:
            混淆矩阵
        """
        model.eval()
        model = model.to(self.device)
        
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(self.device)
                
                _, _, logits = model(batch.x, batch.edge_index, batch.batch)
                # 使用softmax获取概率分布
                probs = torch.softmax(logits, dim=1)
                # 使用argmax获取预测类别
                preds = torch.argmax(probs, dim=1)
                
                if hasattr(batch, 'y'):
                    all_preds.extend(preds.cpu().numpy())
                    all_labels.extend(batch.y.cpu().numpy())
        
        if not all_labels:
            print("警告: 没有可用的标签数据")
            return np.array([[0, 0], [0, 0]])
        
        # 计算混淆矩阵
        cm = confusion_matrix(all_labels, all_preds)
        
        # 绘制
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['正常', '恶意'],
                   yticklabels=['正常', '恶意'])
        plt.title('混淆矩阵')
        plt.ylabel('真实标签')
        plt.xlabel('预测标签')
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"混淆矩阵已保存到: {save_path}")
        
        plt.close()
        
        return cm
    
    def plot_roc_curve(self, model, test_loader: DataLoader,
                      save_path: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        绘制ROC曲线
        
        返回:
            (fpr, tpr, auc_score)
        """
        model.eval()
        model = model.to(self.device)
        
        all_probs = []
        all_labels = []
        
        with torch.no_grad():
            for batch in test_loader:
                batch = batch.to(self.device)
                
                _, _, logits = model(batch.x, batch.edge_index, batch.batch)
                # 使用softmax获取概率分布
                probs = torch.softmax(logits, dim=1)
                # 取第二个类别（恶意类，索引1）的概率用于ROC曲线
                probs_class1 = probs[:, 1]
                
                if hasattr(batch, 'y'):
                    all_probs.extend(probs_class1.cpu().numpy())
                    all_labels.extend(batch.y.cpu().numpy())
        
        if not all_labels:
            print("警告: 没有可用的标签数据")
            return np.array([]), np.array([]), 0.0
        
        # 计算ROC曲线
        fpr, tpr, _ = roc_curve(all_labels, all_probs)
        auc_score = auc(fpr, tpr)
        
        # 绘制
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2,
                label=f'ROC曲线 (AUC = {auc_score:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--',
                label='随机猜测')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('假阳性率 (FPR)')
        plt.ylabel('真阳性率 (TPR)')
        plt.title('ROC曲线')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"ROC曲线已保存到: {save_path}")
        
        plt.close()
        
        return fpr, tpr, auc_score
    
    def plot_training_history(self, history: Dict[str, List[float]],
                             save_path: Optional[str] = None) -> None:
        """
        绘制训练历史
        
        参数:
            history: 训练历史字典，包含 'train_loss', 'val_loss' 等
            save_path: 保存路径
        """
        fig, axes = plt.subplots(1, 2, figsize=(15, 5))
        
        # 损失曲线
        if 'train_loss' in history:
            axes[0].plot(history['train_loss'], label='训练损失', linewidth=2)
        if 'val_loss' in history:
            axes[0].plot(history['val_loss'], label='验证损失', linewidth=2)
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('损失')
        axes[0].set_title('训练和验证损失')
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        
        # 准确率曲线
        if 'train_acc' in history and history['train_acc']:
            axes[1].plot(history['train_acc'], label='训练准确率', linewidth=2)
        if 'val_acc' in history and history['val_acc']:
            axes[1].plot(history['val_acc'], label='验证准确率', linewidth=2)
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('准确率')
        axes[1].set_title('训练和验证准确率')
        axes[1].legend()
        axes[1].grid(alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"训练历史已保存到: {save_path}")
        
        plt.close()
    
    def generate_report(self, model, test_loader: DataLoader,
                       output_dir: str = './evaluation') -> Dict:
        """
        生成完整的评估报告
        
        返回:
            评估结果字典
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print("=" * 60)
        print("开始模型评估...")
        print("=" * 60)
        
        # 1. 计算基本指标
        print("\n1. 计算评估指标...")
        metrics = self.evaluate(model, test_loader, task='edge_prediction')
        
        print("\n评估指标:")
        for key, value in metrics.items():
            print(f"  {key}: {value:.4f}")
        
        # 2. 绘制混淆矩阵
        print("\n2. 生成混淆矩阵...")
        cm = self.plot_confusion_matrix(
            model, test_loader,
            save_path=os.path.join(output_dir, 'confusion_matrix.png')
        )
        
        # 3. 绘制ROC曲线
        print("\n3. 生成ROC曲线...")
        fpr, tpr, auc_score = self.plot_roc_curve(
            model, test_loader,
            save_path=os.path.join(output_dir, 'roc_curve.png')
        )
        
        # 4. 保存评估结果
        results = {
            'metrics': metrics,
            'confusion_matrix': cm.tolist() if isinstance(cm, np.ndarray) else cm,
            'auc': float(auc_score) if auc_score else 0.0
        }
        
        import json
        with open(os.path.join(output_dir, 'evaluation_results.json'), 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n评估报告已保存到: {output_dir}")
        print("=" * 60)
        
        return results


if __name__ == "__main__":
    print("测试模型评估器...")
    
    # 这里需要实际的模型和数据来测试
    print("模型评估器模块已创建")
    print("使用示例:")
    print("  evaluator = ModelEvaluator()")
    print("  metrics = evaluator.evaluate(model, test_loader)")
    print("  evaluator.generate_report(model, test_loader, './results')")
