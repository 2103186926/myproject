#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
层次化GNN模型框架图生成器
使用matplotlib和networkx生成高质量的学术论文插图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def draw_hierarchical_gnn_framework():
    """绘制层次化GNN框架图"""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # 颜色方案
    color_cfg = '#E8F4F8'  # 浅蓝色 - CFG
    color_fcg = '#FFF4E6'  # 浅橙色 - FCG
    color_layer = '#E8F5E9'  # 浅绿色 - 网络层
    color_embedding = '#F3E5F5'  # 浅紫色 - 嵌入
    color_arrow = '#424242'  # 深灰色 - 箭头
    
    # ==================== 标题 ====================
    ax.text(8, 11.5, '层次化图神经网络模型整体架构', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    # ==================== 阶段一：CFG-GNN ====================
    # 阶段标题
    stage1_box = FancyBboxPatch((0.5, 9.5), 15, 0.6, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#1976D2', facecolor='#BBDEFB', 
                                linewidth=2)
    ax.add_patch(stage1_box)
    ax.text(8, 9.8, '阶段一：CFG-GNN训练（函数级特征学习）', 
            ha='center', va='center', fontsize=14, fontweight='bold')
    
    # CFG输入图
    cfg_positions = [2, 5, 8]
    for i, x in enumerate(cfg_positions):
        # CFG图框
        cfg_box = FancyBboxPatch((x-0.6, 8), 1.2, 1.2, 
                                boxstyle="round,pad=0.05", 
                                edgecolor='#0277BD', facecolor=color_cfg, 
                                linewidth=1.5)
        ax.add_patch(cfg_box)
        
        # 绘制简单的图结构
        nodes = [(x-0.3, 8.8), (x, 8.5), (x+0.3, 8.8), (x, 8.2)]
        for node in nodes:
            circle = Circle(node, 0.08, color='#0288D1', zorder=3)
            ax.add_patch(circle)
        # 绘制边
        ax.plot([x-0.3, x], [8.8, 8.5], 'k-', linewidth=0.8, alpha=0.5)
        ax.plot([x+0.3, x], [8.8, 8.5], 'k-', linewidth=0.8, alpha=0.5)
        ax.plot([x, x], [8.5, 8.2], 'k-', linewidth=0.8, alpha=0.5)
        
        ax.text(x, 7.7, f'CFG{i+1}', ha='center', va='top', fontsize=10)
        ax.text(x, 7.5, '(16维)', ha='center', va='top', fontsize=8, style='italic')
    
    # 省略号
    ax.text(10.5, 8.6, '...', ha='center', va='center', fontsize=16)
    
    # 箭头指向CFG-GNN
    arrow1 = FancyArrowPatch((8, 7.3), (8, 6.8),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow1)
    
    # CFG-GNN模型
    cfg_gnn_box = FancyBboxPatch((5, 3.5), 6, 3, 
                                boxstyle="round,pad=0.15", 
                                edgecolor='#0277BD', facecolor=color_layer, 
                                linewidth=2)
    ax.add_patch(cfg_gnn_box)
    ax.text(8, 6.3, 'CFG-GNN模型', ha='center', va='center', 
            fontsize=12, fontweight='bold')
    
    # GCN层
    layers = [
        (5.5, 'GCNConv层1\n16→32维\n+ReLU+Dropout'),
        (4.8, 'GCNConv层2\n32→32维\n+ReLU+Dropout'),
        (4.1, 'GCNConv层3\n32→64维')
    ]
    
    for y, text in layers:
        layer_box = FancyBboxPatch((5.5, y), 5, 0.5, 
                                  boxstyle="round,pad=0.05", 
                                  edgecolor='#01579B', facecolor='white', 
                                  linewidth=1)
        ax.add_patch(layer_box)
        ax.text(8, y+0.25, text, ha='center', va='center', fontsize=9)
        
        if y > 4.1:
            arrow = FancyArrowPatch((8, y), (8, y-0.2),
                                  arrowstyle='->', mutation_scale=15, 
                                  linewidth=1.5, color=color_arrow)
            ax.add_patch(arrow)
    
    # 全局池化
    pool_box = FancyBboxPatch((6, 3.6), 4, 0.4, 
                             boxstyle="round,pad=0.05", 
                             edgecolor='#01579B', facecolor='#B3E5FC', 
                             linewidth=1)
    ax.add_patch(pool_box)
    ax.text(8, 3.8, '全局平均池化', ha='center', va='center', fontsize=9)
    
    # 箭头指向CFG嵌入
    arrow2 = FancyArrowPatch((8, 3.4), (8, 2.9),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow2)
    
    # CFG嵌入
    cfg_emb_box = FancyBboxPatch((6.5, 2.3), 3, 0.5, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#6A1B9A', facecolor=color_embedding, 
                                linewidth=2)
    ax.add_patch(cfg_emb_box)
    ax.text(8, 2.55, 'CFG嵌入（64维）', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    
    # ==================== 阶段二：FCG-GNN ====================
    # 阶段标题
    stage2_box = FancyBboxPatch((0.5, 1.5), 15, 0.6, 
                                boxstyle="round,pad=0.1", 
                                edgecolor='#E65100', facecolor='#FFE0B2', 
                                linewidth=2)
    ax.add_patch(stage2_box)
    ax.text(8, 1.8, '阶段二：特征融合与FCG-GNN训练（程序级特征学习）', 
            ha='center', va='center', fontsize=14, fontweight='bold')
    
    # 绘制右侧的FCG-GNN流程
    # 特征融合说明
    fusion_box = FancyBboxPatch((11.5, 2.1), 3.5, 0.8, 
                               boxstyle="round,pad=0.1", 
                               edgecolor='#6A1B9A', facecolor='#F3E5F5', 
                               linewidth=1.5, linestyle='--')
    ax.add_patch(fusion_box)
    ax.text(13.25, 2.7, '特征融合', ha='center', va='center', 
            fontsize=10, fontweight='bold')
    ax.text(13.25, 2.35, 'x\'ᵢ = [xᵢ ‖ h_cfg]', ha='center', va='center', 
            fontsize=9, style='italic')
    
    # 箭头从CFG嵌入指向特征融合
    arrow3 = FancyArrowPatch((9.5, 2.55), (11.5, 2.5),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color='#6A1B9A', linestyle='--')
    ax.add_patch(arrow3)
    
    # 绘制下方的完整流程
    y_base = -1.5
    
    # FCG输入
    fcg_box = FancyBboxPatch((1, y_base+1.5), 3, 1.2, 
                            boxstyle="round,pad=0.1", 
                            edgecolor='#E65100', facecolor=color_fcg, 
                            linewidth=1.5)
    ax.add_patch(fcg_box)
    ax.text(2.5, y_base+2.5, 'FCG图', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    
    # 绘制FCG的函数节点
    func_nodes = [(1.5, y_base+1.9), (2.5, y_base+1.9), (3.5, y_base+1.9)]
    for i, node in enumerate(func_nodes):
        circle = Circle(node, 0.12, color='#FF6F00', zorder=3)
        ax.add_patch(circle)
        ax.text(node[0], node[1]-0.35, f'func{i+1}', ha='center', va='top', fontsize=8)
        ax.text(node[0], node[1]-0.5, '(16维)', ha='center', va='top', fontsize=7, style='italic')
    
    # 绘制调用关系
    ax.annotate('', xy=(2.5, y_base+1.9), xytext=(1.5, y_base+1.9),
                arrowprops=dict(arrowstyle='->', lw=1, color='#E65100'))
    ax.annotate('', xy=(3.5, y_base+1.9), xytext=(2.5, y_base+1.9),
                arrowprops=dict(arrowstyle='->', lw=1, color='#E65100'))
    
    # 特征增强箭头
    arrow4 = FancyArrowPatch((4, y_base+2.1), (5, y_base+2.1),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color='#6A1B9A')
    ax.add_patch(arrow4)
    ax.text(4.5, y_base+2.4, '特征增强', ha='center', va='bottom', 
            fontsize=9, color='#6A1B9A', fontweight='bold')
    
    # 增强后的FCG
    fcg_enhanced_box = FancyBboxPatch((5, y_base+1.5), 3, 1.2, 
                                     boxstyle="round,pad=0.1", 
                                     edgecolor='#6A1B9A', facecolor='#F3E5F5', 
                                     linewidth=2, linestyle='--')
    ax.add_patch(fcg_enhanced_box)
    ax.text(6.5, y_base+2.5, '增强FCG图', ha='center', va='center', 
            fontsize=11, fontweight='bold')
    
    # 增强后的函数节点
    for i, x in enumerate([5.5, 6.5, 7.5]):
        circle = Circle((x, y_base+1.9), 0.12, color='#8E24AA', zorder=3)
        ax.add_patch(circle)
        ax.text(x, y_base+1.9-0.35, f'func{i+1}', ha='center', va='top', fontsize=8)
        ax.text(x, y_base+1.9-0.5, '(80维)', ha='center', va='top', fontsize=7, 
                style='italic', color='#6A1B9A', fontweight='bold')
    
    # 箭头指向FCG-GNN
    arrow5 = FancyArrowPatch((6.5, y_base+1.3), (6.5, y_base+0.8),
                            arrowstyle='->', mutation_scale=20, 
                            linewidth=2, color=color_arrow)
    ax.add_patch(arrow5)
    
    # FCG-GNN模型
    fcg_gnn_box = FancyBboxPatch((4.5, y_base-2.5), 4, 3, 
                                boxstyle="round,pad=0.15", 
                                edgecolor='#E65100', facecolor=color_layer, 
                                linewidth=2)
    ax.add_patch(fcg_gnn_box)
    ax.text(6.5, y_base+0.6, 'FCG-GNN模型', ha='center', va='center', 
            fontsize=12, fontweight='bold')
    
    # GAT层
    gat_layers = [
        (y_base+0.1, 'GATConv层1\n80→32维\n+注意力+ReLU+Dropout'),
        (y_base-0.6, 'GATConv层2\n32→64维\n+注意力')
    ]
    
    for y, text in gat_layers:
        layer_box = FancyBboxPatch((5, y), 3, 0.5, 
                                  boxstyle="round,pad=0.05", 
                                  edgecolor='#BF360C', facecolor='white', 
                                  linewidth=1)
        ax.add_patch(layer_box)
        ax.text(6.5, y+0.25, text, ha='center', va='center', fontsize=9)
        
        if y == y_base+0.1:
            arrow = FancyArrowPatch((6.5, y), (6.5, y-0.35),
                                  arrowstyle='->', mutation_scale=15, 
                                  linewidth=1.5, color=color_arrow)
            ax.add_patch(arrow)
    
    # 全局池化
    pool_box2 = FancyBboxPatch((5.2, y_base-1.3), 2.6, 0.4, 
                              boxstyle="round,pad=0.05", 
                              edgecolor='#BF360C', facecolor='#FFCCBC', 
                              linewidth=1)
    ax.add_patch(pool_box2)
    ax.text(6.5, y_base-1.1, '全局池化', ha='center', va='center', fontsize=9)
    
    # 分类器
    classifier_box = FancyBboxPatch((5.2, y_base-2), 2.6, 0.4, 
                                   boxstyle="round,pad=0.05", 
                                   edgecolor='#BF360C', facecolor='#FFCCBC', 
                                   linewidth=1)
    ax.add_patch(classifier_box)
    ax.text(6.5, y_base-1.8, '分类器 Linear(64→2)', ha='center', va='center', fontsize=9)
    
    # 箭头
    arrow6 = FancyArrowPatch((6.5, y_base-1.5), (6.5, y_base-1.6),
                            arrowstyle='->', mutation_scale=15, 
                            linewidth=1.5, color=color_arrow)
    ax.add_patch(arrow6)
    
    # 最终输出
    output_box = FancyBboxPatch((5, y_base-2.8), 3, 0.6, 
                               boxstyle="round,pad=0.1", 
                               edgecolor='#1B5E20', facecolor='#C8E6C9', 
                               linewidth=2)
    ax.add_patch(output_box)
    ax.text(6.5, y_base-2.5, '程序级嵌入（64维）', ha='center', va='center', 
            fontsize=10, fontweight='bold')
    ax.text(6.5, y_base-2.7, '+ 分类结果（正常/恶意）', ha='center', va='center', 
            fontsize=9)
    
    # ==================== 添加图例和说明 ====================
    # 信息流向说明
    info_box = FancyBboxPatch((10, y_base-2.8), 5, 2.5, 
                             boxstyle="round,pad=0.15", 
                             edgecolor='#424242', facecolor='#FAFAFA', 
                             linewidth=1.5)
    ax.add_patch(info_box)
    ax.text(12.5, y_base-0.5, '关键技术说明', ha='center', va='center', 
            fontsize=11, fontweight='bold', color='#424242')
    
    # 说明文字
    explanations = [
        ('CFG-GNN', '3层GCN，学习函数级控制流'),
        ('FCG-GNN', '2层GAT，学习程序级调用关系'),
        ('特征融合', 'CFG嵌入增强FCG节点特征'),
        ('信息流向', '局部→全局，细粒度→粗粒度')
    ]
    
    y_text = y_base-1
    for title, desc in explanations:
        ax.text(10.3, y_text, f'• {title}:', ha='left', va='center', 
                fontsize=9, fontweight='bold')
        ax.text(10.5, y_text-0.2, desc, ha='left', va='center', 
                fontsize=8, color='#616161')
        y_text -= 0.5
    
    # 保存图片
    plt.tight_layout()
    plt.savefig('层次化GNN模型框架图.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    plt.savefig('层次化GNN模型框架图.pdf', bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    print("✅ 框架图已生成：")
    print("   - 层次化GNN模型框架图.png (高分辨率PNG)")
    print("   - 层次化GNN模型框架图.pdf (矢量图PDF)")
    plt.show()


def draw_simplified_framework():
    """绘制简化版框架图（适合论文使用）"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 颜色方案
    color_stage1 = '#E3F2FD'
    color_stage2 = '#FFF3E0'
    color_model = '#E8F5E9'
    
    # 标题
    ax.text(7, 9.5, '层次化图神经网络模型', 
            ha='center', va='center', fontsize=16, fontweight='bold')
    
    # ========== 阶段一 ==========
    stage1_box = Rectangle((0.5, 5), 6, 4, 
                           edgecolor='#1976D2', facecolor=color_stage1, 
                           linewidth=2)
    ax.add_patch(stage1_box)
    ax.text(3.5, 8.7, '阶段一：CFG-GNN', ha='center', va='center', 
            fontsize=13, fontweight='bold')
    
    # CFG输入
    ax.text(3.5, 8.2, 'CFG图输入', ha='center', va='center', fontsize=10)
    for i, x in enumerate([2, 3.5, 5]):
        circle = Circle((x, 7.7), 0.15, color='#2196F3', alpha=0.7)
        ax.add_patch(circle)
    
    # 模型层
    for i, (y, text) in enumerate([(7, 'GCN层1'), (6.5, 'GCN层2'), (6, 'GCN层3')]):
        rect = Rectangle((2, y-0.15), 3, 0.3, 
                        edgecolor='#1565C0', facecolor='white', linewidth=1)
        ax.add_patch(rect)
        ax.text(3.5, y, text, ha='center', va='center', fontsize=9)
    
    # 池化
    rect = Rectangle((2.3, 5.4), 2.4, 0.3, 
                    edgecolor='#0D47A1', facecolor='#BBDEFB', linewidth=1)
    ax.add_patch(rect)
    ax.text(3.5, 5.55, '全局池化', ha='center', va='center', fontsize=9)
    
    # 输出
    output1 = FancyBboxPatch((2.5, 5.1), 2, 0.25, 
                            boxstyle="round,pad=0.05", 
                            edgecolor='#6A1B9A', facecolor='#E1BEE7', 
                            linewidth=1.5)
    ax.add_patch(output1)
    ax.text(3.5, 5.225, 'CFG嵌入(64维)', ha='center', va='center', 
            fontsize=9, fontweight='bold')
    
    # ========== 特征融合 ==========
    arrow_fusion = FancyArrowPatch((6.5, 5.225), (7.5, 5.225),
                                  arrowstyle='->', mutation_scale=25, 
                                  linewidth=3, color='#6A1B9A')
    ax.add_patch(arrow_fusion)
    ax.text(7, 5.5, '特征融合', ha='center', va='bottom', 
            fontsize=10, fontweight='bold', color='#6A1B9A')
    
    # ========== 阶段二 ==========
    stage2_box = Rectangle((7.5, 5), 6, 4, 
                           edgecolor='#F57C00', facecolor=color_stage2, 
                           linewidth=2)
    ax.add_patch(stage2_box)
    ax.text(10.5, 8.7, '阶段二：FCG-GNN', ha='center', va='center', 
            fontsize=13, fontweight='bold')
    
    # FCG输入
    ax.text(10.5, 8.2, '增强FCG图输入', ha='center', va='center', fontsize=10)
    for i, x in enumerate([9, 10.5, 12]):
        circle = Circle((x, 7.7), 0.15, color='#FF9800', alpha=0.7)
        ax.add_patch(circle)
    ax.text(10.5, 7.4, '(原始16维 + CFG64维 = 80维)', ha='center', va='center', 
            fontsize=8, style='italic')
    
    # 模型层
    for i, (y, text) in enumerate([(6.8, 'GAT层1'), (6.3, 'GAT层2')]):
        rect = Rectangle((9, y-0.15), 3, 0.3, 
                        edgecolor='#E65100', facecolor='white', linewidth=1)
        ax.add_patch(rect)
        ax.text(10.5, y, text, ha='center', va='center', fontsize=9)
    
    # 池化
    rect = Rectangle((9.3, 5.8), 2.4, 0.3, 
                    edgecolor='#BF360C', facecolor='#FFCCBC', linewidth=1)
    ax.add_patch(rect)
    ax.text(10.5, 5.95, '全局池化', ha='center', va='center', fontsize=9)
    
    # 分类器
    rect = Rectangle((9.3, 5.4), 2.4, 0.3, 
                    edgecolor='#BF360C', facecolor='#FFCCBC', linewidth=1)
    ax.add_patch(rect)
    ax.text(10.5, 5.55, '分类器', ha='center', va='center', fontsize=9)
    
    # 输出
    output2 = FancyBboxPatch((9.5, 5.05), 2, 0.3, 
                            boxstyle="round,pad=0.05", 
                            edgecolor='#2E7D32', facecolor='#C8E6C9', 
                            linewidth=1.5)
    ax.add_patch(output2)
    ax.text(10.5, 5.2, '程序级嵌入(64维)', ha='center', va='center', 
            fontsize=9, fontweight='bold')
    
    # ========== 底部说明 ==========
    # 绘制信息流向
    arrow_flow = FancyArrowPatch((1, 4.5), (13, 4.5),
                                arrowstyle='->', mutation_scale=30, 
                                linewidth=2, color='#424242')
    ax.add_patch(arrow_flow)
    ax.text(7, 4.8, '信息流向：局部→全局，细粒度→粗粒度', 
            ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 关键参数说明
    param_text = [
        'CFG-GNN: 3层GCN, 隐藏维度32, 输出64维',
        'FCG-GNN: 2层GAT, 隐藏维度32, 输出64维',
        '训练: Adam优化器, 学习率0.001, 各50轮'
    ]
    
    y_param = 3.8
    for text in param_text:
        ax.text(7, y_param, text, ha='center', va='center', 
                fontsize=8, color='#616161')
        y_param -= 0.3
    
    # 保存图片
    plt.tight_layout()
    plt.savefig('结构特征提取/层次化GNN模型框架图_简化版.png', dpi=300, 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('结构特征提取/层次化GNN模型框架图_简化版.pdf', 
                bbox_inches='tight', facecolor='white', edgecolor='none')
    print("✅ 简化版框架图已生成：")
    print("   - 层次化GNN模型框架图_简化版.png")
    print("   - 层次化GNN模型框架图_简化版.pdf")
    plt.show()


if __name__ == "__main__":
    print("=" * 60)
    print("层次化GNN模型框架图生成器")
    print("=" * 60)
    print("\n请选择要生成的图片类型：")
    print("1. 完整版框架图（详细展示所有组件）")
    print("2. 简化版框架图（适合论文使用）")
    print("3. 生成两个版本")
    
    choice = input("\n请输入选项（1/2/3）[默认3]: ").strip() or "3"
    
    print("\n开始生成图片...")
    
    if choice == "1":
        draw_hierarchical_gnn_framework()
    elif choice == "2":
        draw_simplified_framework()
    elif choice == "3":
        draw_hierarchical_gnn_framework()
        print("\n" + "=" * 60 + "\n")
        draw_simplified_framework()
    else:
        print("❌ 无效的选项，请重新运行程序")
    
    print("\n" + "=" * 60)
    print("✅ 所有图片生成完成！")
    print("=" * 60)

