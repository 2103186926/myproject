#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海底矿产资源评估
样本编号: normal_0136
生成时间: 2026-03-11 16:39:19
函数数量: 5
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海底矿产资源评估Processor:
    """
    海底矿产资源评估处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def calculate_mixed_layer_depth(self):
        """计算混合层深度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            density_grad = np.gradient(self.data['density'])
            max_grad_idx = np.argmax(np.abs(density_grad))
            mld = self.data['depth'].iloc[max_grad_idx] if max_grad_idx < len(self.data) else 50
            self.results['mixed_layer_depth'] = float(mld)
            print(f"混合层深度: {mld:.2f} m")
            return mld
        mld = 50.0 + np.random.randn() * 10
        self.results['mixed_layer_depth'] = mld
        return mld

    def predict_salinity(self, lead_time=24):
        """预测未来盐度"""
        if self.data is None or 'salinity' not in self.data.columns:
            return None
        window = min(10, len(self.data))
        recent_mean = self.data['salinity'].iloc[-window:].mean()
        recent_trend = self.data['salinity'].iloc[-window:].diff().mean()
        predicted_salinity = recent_mean + recent_trend * lead_time
        self.results['predicted_salinity'] = float(predicted_salinity)
        print(f"预测 {lead_time}h 后盐度: {predicted_salinity:.2f} PSU")
        return predicted_salinity

    def perform_eof_analysis(self, n_modes=3):
        """经验正交函数(EOF)分析"""
        if self.data is None:
            return None
        from sklearn.decomposition import PCA
        numeric_data = self.data.select_dtypes(include=[np.number]).fillna(0)
        if len(numeric_data.columns) < 2:
            return None
        pca = PCA(n_components=min(n_modes, len(numeric_data.columns)))
        pca.fit(numeric_data)
        eof_results = {'explained_variance': pca.explained_variance_ratio_.tolist(), 'n_modes': int(pca.n_components_), 'total_variance_explained': float(np.sum(pca.explained_variance_ratio_))}
        pc_timeseries = pca.transform(numeric_data)
        for i in range(pca.n_components_):
            self.data[f'PC{i+1}'] = pc_timeseries[:, i]
        self.results['eof_analysis'] = eof_results
        print(f"EOF分析完成: {n_modes} 个模态, 解释方差 {eof_results['total_variance_explained']:.2%}")
        return eof_results

    def calculate_density_field(self):
        """计算海水密度场"""
        if self.data is None:
            return None
        if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
            T = self.data['temperature']
            S = self.data['salinity']
            rho0 = 1025.0
            alpha = 0.2
            beta = 0.78
            self.data['density'] = rho0 * (1 - alpha * (T - 10) + beta * (S - 35))
            print("密度场计算完成")
            return self.data['density'].values
        return None


def calculate_thermocline_depth_helper(data, config):
    """
    calculate_thermocline_depth 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_thermocline_depth_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_thermocline_depth_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海底矿产资源评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海底矿产资源评估Processor(config)
    
    # 步骤1: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤2: predict_salinity
    processor.predict_salinity()
    
    # 步骤3: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤4: calculate_density_field
    processor.calculate_density_field()
    
    # 调用辅助函数: calculate_thermocline_depth_helper
    calculate_thermocline_depth_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
