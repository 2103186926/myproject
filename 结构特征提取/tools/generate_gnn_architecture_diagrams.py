#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成CFG-GNN和FCG-GNN模型架构图
用于论文插图
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def draw_cfg_gnn_architecture():
    """绘制CFG-GNN模型架构图（简化版，适合论文）"""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 定义颜色方案
    color_input = '#E8F4F8'
    color_block = '#B3D9E6'
    color_hidden = '#D4F4DD'
    color_pool = '#FFE4E1'
    
    # 层的位置和大小
    layer_width = 4.0
    layer_height = 0.7
    block_height = 1.2
    x_center = 5
    
    # 绘制层的函数
    def draw_layer(y, text, color, width=layer_width, height=layer_height):
        box = FancyBboxPatch(
            (x_center - width/2, y), width, height,
            boxstyle="round,pad=0.1", 
            edgecolor='black', facecolor=color, linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(x_center, y + height/2, text, 
                ha='center', va='center', fontsize=11, weight='bold')
        return y
    
    # 绘制箭头
    def draw_arrow(y_from, y_to, style='->', color='black', linewidth=2):
        arrow = FancyArrowPatch(
            (x_center, y_from), (x_center, y_to),
            arrowstyle=style, color=color, linewidth=linewidth,
            mutation_scale=20
        )
        ax.add_patch(arrow)
    
    # 绘制残差连接
    def draw_residual(y_start, y_end):
        arrow = FancyArrowPatch(
            (x_center - layer_width/2 - 0.3, y_start + block_height/2),
            (x_center - layer_width/2 - 0.3, y_end + block_height/2),
            arrowstyle='->', color='green', linewidth=2.5,
            mutation_scale=20, linestyle='--',
            connectionstyle=f"arc3,rad=-.3"
        )
        ax.add_patch(arrow)
        ax.text(x_center - layer_width/2 - 1.0, (y_start + y_end)/2 + block_height/2, 
                '残差\n连接', fontsize=9, color='green', weight='bold', 
                ha='center', va='center')
    
    # 标题
    ax.text(x_center, 9.5, 'CFG-GNN模型架构', 
            ha='center', va='center', fontsize=16, weight='bold')
    
    # 输入
    y = 8.7
    draw_layer(y, '输入: 节点特征 X ∈ R^(N×256)', color_input, width=4.5)
    draw_arrow(y, y - 0.9)
    
    # 输入层
    y = 7.3
    ax.text(0.8, y + layer_height/2, '输入层', fontsize=11, weight='bold', color='blue')
    draw_layer(y, 'GCNConv(256→128) + BN + ReLU + Dropout', color_block)
    draw_arrow(y, y - 0.9)
    
    # 隐藏层模块（抽象表示）
    y = 5.8
    y_residual_start = y
    ax.text(0.8, y + block_height/2, '隐藏层', fontsize=11, weight='bold', color='blue')
    
    # 绘制隐藏层块
    box = FancyBboxPatch(
        (x_center - layer_width/2, y), layer_width, block_height,
        boxstyle="round,pad=0.1", 
        edgecolor='black', facecolor=color_hidden, linewidth=1.5
    )
    ax.add_patch(box)
    
    # 隐藏层文本（多行）
    ax.text(x_center, y + block_height/2 + 0.25, 
            'GCNConv(128→128) + BN + ReLU + Dropout', 
            ha='center', va='center', fontsize=10, weight='bold')
    ax.text(x_center, y + block_height/2 - 0.25, 
            '× 2层（带残差连接）', 
            ha='center', va='center', fontsize=9, style='italic', color='green')
    
    y_residual_end = y
    draw_arrow(y, y - 0.9)
    
    # 绘制残差连接
    draw_residual(y_residual_start, y_residual_end)
    
    # 输出层
    y = 4.4
    ax.text(0.8, y + layer_height/2, '输出层', fontsize=11, weight='bold', color='blue')
    draw_layer(y, 'GCNConv(128→128) + BN', color_block)
    draw_arrow(y, y - 0.9)
    
    # 池化层
    y = 3.0
    ax.text(0.8, y + layer_height/2, '池化层', fontsize=11, weight='bold', color='blue')
    draw_layer(y, 'AttentionPooling', color_pool)
    draw_arrow(y, y - 0.9)
    
    # 输出
    y = 1.6
    draw_layer(y, '输出: 图嵌入 Z ∈ R^(B×128)', color_input, width=4.5)
    
    # 添加图例
    legend_elements = [
        mpatches.Patch(facecolor=color_block, edgecolor='black', label='卷积块(Conv+BN+激活+Dropout)'),
        mpatches.Patch(facecolor=color_hidden, edgecolor='black', label='隐藏层模块(含残差连接)'),
        mpatches.Patch(facecolor=color_pool, edgecolor='black', label='注意力池化层'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)
    
    # 添加注释
    ax.text(x_center, 0.5, 
            '注: BN=BatchNorm, Conv=GCNConv', 
            ha='center', va='center', fontsize=8, style='italic', color='gray')
    
    plt.tight_layout()
    return fig


def draw_fcg_gnn_architecture():
    """绘制FCG-GNN模型架构图（简化版，适合论文）"""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 定义颜色方案
    color_input = '#E8F4F8'
    color_block = '#C8E6C9'
    color_hidden = '#D4F4DD'
    color_pool = '#FFE4E1'
    
    # 层的位置和大小
    layer_width = 4.0
    layer_height = 0.7
    block_height = 1.2
    x_center = 5
    
    # 绘制层的函数
    def draw_layer(y, text, color, width=layer_width, height=layer_height):
        box = FancyBboxPatch(
            (x_center - width/2, y), width, height,
            boxstyle="round,pad=0.1", 
            edgecolor='black', facecolor=color, linewidth=1.5
        )
        ax.add_patch(box)
        ax.text(x_center, y + height/2, text, 
                ha='center', va='center', fontsize=11, weight='bold')
        return y
    
    # 绘制箭头
    def draw_arrow(y_from, y_to, style='->', color='black', linewidth=2):
        arrow = FancyArrowPatch(
            (x_center, y_from), (x_center, y_to),
            arrowstyle=style, color=color, linewidth=linewidth,
            mutation_scale=20
        )
        ax.add_patch(arrow)
    
    # 绘制残差连接
    def draw_residual(y_start, y_end):
        arrow = FancyArrowPatch(
            (x_center - layer_width/2 - 0.3, y_start + block_height/2),
            (x_center - layer_width/2 - 0.3, y_end + block_height/2),
            arrowstyle='->', color='green', linewidth=2.5,
            mutation_scale=20, linestyle='--',
            connectionstyle=f"arc3,rad=-.3"
        )
        ax.add_patch(arrow)
        ax.text(x_center - layer_width/2 - 1.0, (y_start + y_end)/2 + block_height/2, 
                '残差\n连接', fontsize=9, color='green', weight='bold', 
                ha='center', va='center')
    
    # 标题
    ax.text(x_center, 9.5, 'FCG-GNN模型架构', 
            ha='center', va='center', fontsize=16, weight='bold')
    
    # 输入
    y = 8.7
    draw_layer(y, '输入: CFG嵌入 X ∈ R^(N×128)', color_input, width=4.5)
    draw_arrow(y, y - 0.9)
    
    # 输入层
    y = 7.3
    ax.text(0.8, y + layer_height/2, '输入层', fontsize=11, weight='bold', color='blue')
    draw_layer(y, 'GATConv(128→128, h=4) + BN + ELU + Dropout', color_block)
    draw_arrow(y, y - 0.9)
    
    # 隐藏层模块（抽象表示）
    y = 5.8
    y_residual_start = y
    ax.text(0.8, y + block_height/2, '隐藏层', fontsize=11, weight='bold', color='blue')
    
    # 绘制隐藏层块
    box = FancyBboxPatch(
        (x_center - layer_width/2, y), layer_width, block_height,
        boxstyle="round,pad=0.1", 
        edgecolor='black', facecolor=color_hidden, linewidth=1.5
    )
    ax.add_patch(box)
    
    # 隐藏层文本（多行）
    ax.text(x_center, y + block_height/2 + 0.25, 
            'GATConv(512→128, h=4) + BN + ELU + Dropout', 
            ha='center', va='center', fontsize=10, weight='bold')
    ax.text(x_center, y + block_height/2 - 0.25, 
            '× 2层（带残差连接）', 
            ha='center', va='center', fontsize=9, style='italic', color='green')
    
    y_residual_end = y
    draw_arrow(y, y - 0.9)
    
    # 绘制残差连接
    draw_residual(y_residual_start, y_residual_end)
    
    # 输出层
    y = 4.4
    ax.text(0.8, y + layer_height/2, '输出层', fontsize=11, weight='bold', color='blue')
    draw_layer(y, 'GATConv(512→128, h=1) + BN', color_block)
    draw_arrow(y, y - 0.9)
    
    # 池化层
    y = 3.0
    ax.text(0.8, y + layer_height/2, '池化层', fontsize=11, weight='bold', color='blue')
    draw_layer(y, 'AttentionPooling', color_pool)
    draw_arrow(y, y - 0.9)
    
    # 输出
    y = 1.6
    draw_layer(y, '输出: 程序级嵌入 Z ∈ R^(B×128)', color_input, width=4.5)
    
    # 添加图例
    legend_elements = [
        mpatches.Patch(facecolor=color_block, edgecolor='black', label='卷积块(GAT+BN+激活+Dropout)'),
        mpatches.Patch(facecolor=color_hidden, edgecolor='black', label='隐藏层模块(含残差连接)'),
        mpatches.Patch(facecolor=color_pool, edgecolor='black', label='注意力池化层'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)
    
    # 添加注释
    ax.text(x_center, 0.5, 
            '注: BN=BatchNorm, h=heads(注意力头数), GAT=GATConv', 
            ha='center', va='center', fontsize=8, style='italic', color='gray')
    
    plt.tight_layout()
    return fig


def main():
    """主函数：生成并保存架构图"""
    # 创建输出目录
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    print("正在生成CFG-GNN模型架构图...")
    fig_cfg = draw_cfg_gnn_architecture()
    cfg_path = os.path.join(output_dir, 'CFG_GNN_Architecture.png')
    fig_cfg.savefig(cfg_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ CFG-GNN架构图已保存: {cfg_path}")
    plt.close(fig_cfg)
    
    print("\n正在生成FCG-GNN模型架构图...")
    fig_fcg = draw_fcg_gnn_architecture()
    fcg_path = os.path.join(output_dir, 'FCG_GNN_Architecture.png')
    fig_fcg.savefig(fcg_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ FCG-GNN架构图已保存: {fcg_path}")
    plt.close(fig_fcg)
    
    print("\n" + "="*60)
    print("所有架构图生成完成！")
    print("="*60)
    print(f"\n输出目录: {os.path.abspath(output_dir)}")
    print(f"  - CFG_GNN_Architecture.png")
    print(f"  - FCG_GNN_Architecture.png")
    print("\n这些图片可以直接插入到您的论文中。")


if __name__ == "__main__":
    main()
