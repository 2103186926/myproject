#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动态GNN框架图生成器
根据config.py中的配置自动生成框架图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np
from config import Config, get_default_config

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def draw_dynamic_gnn_framework(config: Config = None, save_path: str = None):
    """
    根据配置动态绘制GNN框架图
    
    参数:
        config: 配置对象，如果为None则使用默认配置
        save_path: 保存路径，如果为None则使用默认路径
    """
    if config is None:
        config = get_default_config()
    
    # 提取配置参数
    cfg_hidden = config.model.cfg_hidden_channels
    cfg_out = config.model.cfg_out_channels
    cfg_layers = config.model.cfg_num_layers
    cfg_dropout = config.model.cfg_dropout
    cfg_pooling = config.model.cfg_pooling
    
    fcg_hidden = config.model.fcg_hidden_channels
    fcg_out = config.model.fcg_out_channels
    fcg_layers = config.model.fcg_num_layers
    fcg_dropout = config.model.fcg_dropout
    fcg_pooling = config.model.fcg_pooling
    
    node_feat_dim = config.model.node_feature_dim
    final_emb_dim = config.model.final_embedding_dim
    
    # 创建画布
    fig, ax = plt.subplots(1, 1, figsize=(16, 14))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 14)
    ax.axis('off')
    
    # 颜色方案
    color_cfg = '#E8F4F8'
    color_fcg = '#FFF4E6'
    color_layer = '#E8F5E9'
    color_embedding = '#F3E5F5'
    color_arrow = '#424242'
    
    # ==================== 标题 ====================
    ax.text(8, 13.5, '层次化图神经网络模型架构（动态生成）', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    # 配置信息
    config_text = f'节点特征: {node_feat_dim}维 | 最终嵌入: {final_emb_dim}维 | CFG输出: {cfg_out}维 | FCG输出: {fcg_out}维'
    ax.text(8, 13, config_text, ha='center', va='center', fontsize=10, style='italic', color='#666')
    
    # ==================== 阶段一：CFG-GNN ====================
    stage1_box = FancyBboxPatch((0.5, 10.5), 15, 0.6, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#1976D2', facecolor='#BBDEFB', 
                                linewidth=2)
    ax.add_patch(stage1_box)
    ax.text(8, 10.8, f'阶段一：CFG-GNN训练（{cfg_layers}层GCN，{cfg_pooling}池化）', 
            ha='center', va='center', fontsize=14, fontweight='bold')
    
    # CFG输入
    cfg_y_start = 9.5
    ax.text(8, cfg_y_start, f'CFG图输入（{node_feat_dim}维节点特征）', 
            ha='center', va='center', fontsize=11)
    
    # 绘制CFG示例
    for i, x in enumerate([2, 5, 8]):
        cfg_box = FancyBboxPatch((x-0.6, cfg_y_start-0.8), 1.2, 0.6, 
                                boxstyle="round,pad=0.05", 
                                edgecolor='#0277BD', facecolor=color_cfg, 
                                linewidth=1.5)
        ax.add_patch(cfg_box)
        ax.text(x, cfg_y_start-0.5, f'CFG{i+1}', ha='center', va='center', fontsize=9)
    
    ax.text(10.5, cfg_y_start-0.5, '...', ha='center', va='center', fontsize=16)
    
    # 箭头
    arrow1 = FancyArrowPatch((8, cfg_y_start-1.2), (8, cfg_y_start-1.7),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow1)
    
    # CFG-GNN模型
    cfg_model_y = cfg_y_start - 2
    cfg_model_height = cfg_layers * 0.6 + 1
    
    cfg_gnn_box = FancyBboxPatch((5, cfg_model_y - cfg_model_height), 6, cfg_model_height, 
                                boxstyle="round,pad=0.15", 
                                edgecolor='#0277BD', facecolor=color_layer, 
                                linewidth=2)
    ax.add_patch(cfg_gnn_box)
    ax.text(8, cfg_model_y - 0.3, 'CFG-GNN模型', ha='center', va='center', 
            fontsize=12, fontweight='bold')
    
    # 动态生成GCN层
    layer_y = cfg_model_y - 0.7
    for i in range(cfg_layers):
        if i == 0:
            in_dim = node_feat_dim
            out_dim = cfg_hidden
        elif i == cfg_layers - 1:
            in_dim = cfg_hidden
            out_dim = cfg_out
        else:
            in_dim = cfg_hidden
            out_dim = cfg_hidden
        
        layer_text = f'GCNConv层{i+1}\n{in_dim}→{out_dim}维'
        if i < cfg_layers - 1:
            layer_text += f'\n+ReLU+Dropout({cfg_dropout})'
        
        layer_box = FancyBboxPatch((5.5, layer_y), 5, 0.5, 
                                  boxstyle="round,pad=0.05", 
                                  edgecolor='#01579B', facecolor='white', 
                                  linewidth=1)
        ax.add_patch(layer_box)
        ax.text(8, layer_y+0.25, layer_text, ha='center', va='center', fontsize=8)
        
        if i < cfg_layers - 1:
            arrow = FancyArrowPatch((8, layer_y), (8, layer_y-0.15),
                                  arrowstyle='->', mutation_scale=15, 
                                  linewidth=1.5, color=color_arrow)
            ax.add_patch(arrow)
        
        layer_y -= 0.65
    
    # 全局池化
    pool_y = layer_y + 0.1
    pool_box = FancyBboxPatch((6, pool_y), 4, 0.4, 
                             boxstyle="round,pad=0.05", 
                             edgecolor='#01579B', facecolor='#B3E5FC', 
                             linewidth=1)
    ax.add_patch(pool_box)
    ax.text(8, pool_y+0.2, f'全局{cfg_pooling}池化', ha='center', va='center', fontsize=9)
    
    # CFG嵌入
    emb_y = pool_y - 0.6
    arrow2 = FancyArrowPatch((8, pool_y), (8, emb_y+0.5),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow2)
    
    cfg_emb_box = FancyBboxPatch((6.5, emb_y), 3, 0.5, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#6A1B9A', facecolor=color_embedding, 
                                linewidth=2)
    ax.add_patch(cfg_emb_box)
    ax.text(8, emb_y+0.25, f'CFG嵌入（{cfg_out}维）', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    
    # ==================== 阶段二：FCG-GNN ====================
    stage2_y = emb_y - 0.8
    stage2_box = FancyBboxPatch((0.5, stage2_y), 15, 0.6, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#E65100', facecolor='#FFE0B2', 
                                linewidth=2)
    ax.add_patch(stage2_box)
    ax.text(8, stage2_y+0.3, f'阶段二：特征融合与FCG-GNN训练（{fcg_layers}层GAT，{fcg_pooling}池化）', 
            ha='center', va='center', fontsize=14, fontweight='bold')
    
    # 特征融合
    fusion_y = stage2_y - 0.5
    fusion_box = FancyBboxPatch((11.5, fusion_y-0.3), 3.5, 0.8, 
                               boxstyle="round,pad=0.1", 
                               edgecolor='#6A1B9A', facecolor='#F3E5F5', 
                               linewidth=1.5, linestyle='--')
    ax.add_patch(fusion_box)
    ax.text(13.25, fusion_y+0.2, '特征融合', ha='center', va='center', 
            fontsize=10, fontweight='bold')
    ax.text(13.25, fusion_y-0.15, f'x\'ᵢ = [xᵢ({node_feat_dim}) ‖ h_cfg({cfg_out})]', 
            ha='center', va='center', fontsize=8, style='italic')
    
    arrow3 = FancyArrowPatch((9.5, emb_y+0.25), (11.5, fusion_y),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color='#6A1B9A', linestyle='--')
    ax.add_patch(arrow3)
    
    # FCG输入
    fcg_y = fusion_y - 1.2
    fcg_input_dim = node_feat_dim + cfg_out
    
    fcg_box = FancyBboxPatch((1, fcg_y), 3, 1, 
                            boxstyle="round,pad=0.1", 
                            edgecolor='#E65100', facecolor=color_fcg, 
                            linewidth=1.5)
    ax.add_patch(fcg_box)
    ax.text(2.5, fcg_y+0.8, 'FCG图', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    ax.text(2.5, fcg_y+0.5, f'({node_feat_dim}维)', ha='center', va='center', 
            fontsize=8, style='italic')
    
    # 特征增强
    arrow4 = FancyArrowPatch((4, fcg_y+0.5), (5, fcg_y+0.5),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color='#6A1B9A')
    ax.add_patch(arrow4)
    ax.text(4.5, fcg_y+0.8, '特征增强', ha='center', va='bottom', 
            fontsize=9, color='#6A1B9A', fontweight='bold')
    
    # 增强后的FCG
    fcg_enhanced_box = FancyBboxPatch((5, fcg_y), 3, 1, 
                                     boxstyle="round,pad=0.1", 
                                     edgecolor='#6A1B9A', facecolor='#F3E5F5', 
                                     linewidth=2, linestyle='--')
    ax.add_patch(fcg_enhanced_box)
    ax.text(6.5, fcg_y+0.8, '增强FCG图', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    ax.text(6.5, fcg_y+0.5, f'({fcg_input_dim}维)', ha='center', va='center', 
            fontsize=8, style='italic', color='#6A1B9A', fontweight='bold')
    
    # FCG-GNN模型
    fcg_model_y = fcg_y - 0.5
    fcg_model_height = fcg_layers * 0.6 + 1.5
    
    arrow5 = FancyArrowPatch((6.5, fcg_y), (6.5, fcg_model_y),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow5)
    
    fcg_gnn_box = FancyBboxPatch((4.5, fcg_model_y - fcg_model_height), 4, fcg_model_height, 
                                boxstyle="round,pad=0.15", 
                                edgecolor='#E65100', facecolor=color_layer, 
                                linewidth=2)
    ax.add_patch(fcg_gnn_box)
    ax.text(6.5, fcg_model_y - 0.3, 'FCG-GNN模型', ha='center', va='center', 
            fontsize=12, fontweight='bold')
    
    # 动态生成GAT层
    layer_y = fcg_model_y - 0.7
    for i in range(fcg_layers):
        if i == 0:
            in_dim = fcg_input_dim
            out_dim = fcg_hidden
        elif i == fcg_layers - 1:
            in_dim = fcg_hidden
            out_dim = fcg_out
        else:
            in_dim = fcg_hidden
            out_dim = fcg_hidden
        
        layer_text = f'GATConv层{i+1}\n{in_dim}→{out_dim}维\n+注意力'
        if i < fcg_layers - 1:
            layer_text += f'+Dropout({fcg_dropout})'
        
        layer_box = FancyBboxPatch((5, layer_y), 3, 0.5, 
                                  boxstyle="round,pad=0.05", 
                                  edgecolor='#BF360C', facecolor='white', 
                                  linewidth=1)
        ax.add_patch(layer_box)
        ax.text(6.5, layer_y+0.25, layer_text, ha='center', va='center', fontsize=8)
        
        if i < fcg_layers - 1:
            arrow = FancyArrowPatch((6.5, layer_y), (6.5, layer_y-0.15),
                                  arrowstyle='->', mutation_scale=15, 
                                  linewidth=1.5, color=color_arrow)
            ax.add_patch(arrow)
        
        layer_y -= 0.65
    
    # 全局池化
    pool_y2 = layer_y + 0.1
    pool_box2 = FancyBboxPatch((5.2, pool_y2), 2.6, 0.4, 
                              boxstyle="round,pad=0.05", 
                              edgecolor='#BF360C', facecolor='#FFCCBC', 
                              linewidth=1)
    ax.add_patch(pool_box2)
    ax.text(6.5, pool_y2+0.2, f'全局{fcg_pooling}池化', ha='center', va='center', fontsize=9)
    
    # 分类器
    classifier_y = pool_y2 - 0.5
    arrow6 = FancyArrowPatch((6.5, pool_y2), (6.5, classifier_y+0.4),
                            arrowstyle='->', mutation_scale=15, 
                            linewidth=1.5, color=color_arrow)
    ax.add_patch(arrow6)
    
    classifier_box = FancyBboxPatch((5.2, classifier_y), 2.6, 0.4, 
                                   boxstyle="round,pad=0.05", 
                                   edgecolor='#BF360C', facecolor='#FFCCBC', 
                                   linewidth=1)
    ax.add_patch(classifier_box)
    ax.text(6.5, classifier_y+0.2, f'分类器 Linear({fcg_out}→2)', 
            ha='center', va='center', fontsize=9)
    
    # 最终输出
    output_y = classifier_y - 0.7
    arrow7 = FancyArrowPatch((6.5, classifier_y), (6.5, output_y+0.6),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow7)
    
    output_box = FancyBboxPatch((5, output_y), 3, 0.6, 
                               boxstyle="round,pad=0.1", 
                               edgecolor='#1B5E20', facecolor='#C8E6C9', 
                               linewidth=2)
    ax.add_patch(output_box)
    ax.text(6.5, output_y+0.4, f'程序级嵌入（{final_emb_dim}维）', 
            ha='center', va='center', fontsize=10, fontweight='bold')
    ax.text(6.5, output_y+0.15, '+ 分类结果（正常/恶意）', 
            ha='center', va='center', fontsize=9)
    
    # ==================== 配置信息框 ====================
    info_y = output_y
    info_box = FancyBboxPatch((10, info_y-0.5), 5, 3, 
                             boxstyle="round,pad=0.15", 
                             edgecolor='#424242', facecolor='#FAFAFA', 
                             linewidth=1.5)
    ax.add_patch(info_box)
    ax.text(12.5, info_y+2.2, '模型配置参数', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#424242')
    
    # 配置详情
    config_details = [
        f'CFG-GNN: {cfg_layers}层GCN',
        f'  隐藏维度: {cfg_hidden}',
        f'  输出维度: {cfg_out}',
        f'  Dropout: {cfg_dropout}',
        f'  池化方式: {cfg_pooling}',
        '',
        f'FCG-GNN: {fcg_layers}层GAT',
        f'  隐藏维度: {fcg_hidden}',
        f'  输出维度: {fcg_out}',
        f'  Dropout: {fcg_dropout}',
        f'  池化方式: {fcg_pooling}',
        '',
        f'最终嵌入: {final_emb_dim}维',
        f'  = CFG({cfg_out}) + FCG({fcg_out})'
    ]
    
    y_text = info_y + 1.8
    for line in config_details:
        if line:
            ax.text(10.3, y_text, line, ha='left', va='center', 
                    fontsize=8, color='#424242')
        y_text -= 0.2
    
    # 保存图片
    plt.tight_layout()
    
    if save_path is None:
        save_path = '结构特征提取/层次化GNN模型框架图_动态生成.png'
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.savefig(save_path.replace('.png', '.pdf'), bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print(f"✅ 动态框架图已生成：")
    print(f"   - {save_path}")
    print(f"   - {save_path.replace('.png', '.pdf')}")
    
    plt.show()


if __name__ == "__main__":
    print("=" * 60)
    print("动态GNN框架图生成器")
    print("=" * 60)
    print("\n根据config.py中的配置自动生成框架图...")
    
    # 加载配置
    config = get_default_config()
    
    print(f"\n当前配置:")
    print(f"  CFG-GNN: {config.model.cfg_num_layers}层, 输出{config.model.cfg_out_channels}维")
    print(f"  FCG-GNN: {config.model.fcg_num_layers}层, 输出{config.model.fcg_out_channels}维")
    print(f"  最终嵌入: {config.model.final_embedding_dim}维")
    
    # 生成框架图
    draw_dynamic_gnn_framework(config)
    
    print("\n" + "=" * 60)
    print("✅ 框架图生成完成！")
    print("=" * 60)
