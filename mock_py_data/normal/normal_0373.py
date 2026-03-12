#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海流速度场预测
样本编号: normal_0373
生成时间: 2026-03-11 16:39:19
函数数量: 5
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海流速度场预测Processor:
    """
    海流速度场预测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def compute_correlation(self, var1, var2):
        """计算两个变量的相关性"""
        if self.data is None or var1 not in self.data.columns or var2 not in self.data.columns:
            return None
        correlation = self.data[var1].corr(self.data[var2])
        n = len(self.data)
        t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2 + 1e-10))
        result = {'correlation': float(correlation), 't_statistic': float(t_stat), 'sample_size': int(n)}
        self.results[f'correlation_{var1}_{var2}'] = result
        print(f"{var1} 与 {var2} 相关系数: {correlation:.3f}")
        return result

    def calculate_spatial_gradient(self, variable='temperature'):
        """计算空间梯度"""
        if self.data is None or variable not in self.data.columns:
            return None
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            dx = np.gradient(self.data[variable])
            dy = np.gradient(self.data[variable])
            gradient_magnitude = np.sqrt(dx**2 + dy**2)
            self.data[f'{variable}_grad_x'] = dx
            self.data[f'{variable}_grad_y'] = dy
            self.data[f'{variable}_grad_mag'] = gradient_magnitude
            print(f"{variable} 空间梯度计算完成")
            return gradient_magnitude
        return None

    def classify_ocean_regimes(self):
        """分类海洋状态类型"""
        if self.data is None:
            return None
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return None
        features = self.data[numeric_cols].fillna(0).values
        mean_values = np.mean(features, axis=1)
        labels = (mean_values > np.median(mean_values)).astype(int)
        self.data['ocean_regime'] = labels
        regime_counts = {'regime_0': int(np.sum(labels == 0)), 'regime_1': int(np.sum(labels == 1))}
        self.results['ocean_regimes'] = regime_counts
        print(f"海洋状态分类完成: {regime_counts}")
        return regime_counts

    def grid_irregular_data(self, grid_resolution=0.25):
        """将不规则分布的数据网格化"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        lon_bins = np.arange(-180, 180, grid_resolution)
        lat_bins = np.arange(-90, 90, grid_resolution)
        self.data['lon_bin'] = pd.cut(self.data['lon'], bins=lon_bins, labels=False)
        self.data['lat_bin'] = pd.cut(self.data['lat'], bins=lat_bins, labels=False)
        gridded = self.data.groupby(['lon_bin', 'lat_bin']).mean()
        print(f"数据网格化完成: 分辨率 {grid_resolution}°")
        self.results['gridded_data'] = gridded
        return gridded


def calculate_vorticity_helper(data, config):
    """
    calculate_vorticity 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_vorticity_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_vorticity_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海流速度场预测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海流速度场预测Processor(config)
    
    # 步骤1: compute_correlation
    processor.compute_correlation()
    
    # 步骤2: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤3: classify_ocean_regimes
    processor.classify_ocean_regimes()
    
    # 步骤4: grid_irregular_data
    processor.grid_irregular_data()
    
    # 调用辅助函数: calculate_vorticity_helper
    calculate_vorticity_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
