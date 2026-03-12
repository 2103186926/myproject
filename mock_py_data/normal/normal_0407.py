#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海啸灾害评估
样本编号: normal_0407
生成时间: 2026-03-11 16:39:19
函数数量: 11
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海啸灾害评估Processor:
    """
    海啸灾害评估处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def compute_climatology(self, period='monthly'):
        """计算气候态"""
        if self.data is None or 'time' not in self.data.columns:
            return None
        self.data['time'] = pd.to_datetime(self.data['time'])
        climatology = {}
        if period == 'monthly':
            self.data['month'] = self.data['time'].dt.month
            for col in self.data.select_dtypes(include=[np.number]).columns:
                if col != 'month':
                    monthly_mean = self.data.groupby('month')[col].mean()
                    climatology[col] = monthly_mean.to_dict()
        elif period == 'seasonal':
            self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
            for col in self.data.select_dtypes(include=[np.number]).columns:
                if col != 'season':
                    seasonal_mean = self.data.groupby('season')[col].mean()
                    climatology[col] = seasonal_mean.to_dict()
        self.results['climatology'] = climatology
        print(f"气候态计算完成: {period}")
        return climatology

    def detect_spatial_anomalies(self, variable='temperature', threshold=2.0):
        """检测空间异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        window_size = 10
        anomalies = []
        for i in range(len(self.data) - window_size):
            window = self.data[variable].iloc[i:i+window_size]
            mean = window.mean()
            std = window.std()
            if std > 0:
                z_score = abs((self.data[variable].iloc[i+window_size//2] - mean) / std)
                if z_score > threshold:
                    anomalies.append({'index': i + window_size//2, 'value': self.data[variable].iloc[i+window_size//2], 'z_score': z_score})
        print(f"检测到 {len(anomalies)} 个空间异常点")
        self.results['spatial_anomalies'] = anomalies
        return anomalies

    def simulate_pollutant_dispersion(self, source_location, duration=3600):
        """模拟污染物扩散"""
        if self.data is None:
            return False
        n_points = len(self.data)
        concentration = np.zeros(n_points)
        source_idx = source_location.get('index', n_points // 2)
        concentration[source_idx] = 100.0
        diffusion_coef = 0.1
        timesteps = duration // 60
        for t in range(timesteps):
            laplacian = np.zeros_like(concentration)
            laplacian[1:-1] = concentration[:-2] - 2*concentration[1:-1] + concentration[2:]
            concentration += diffusion_coef * laplacian
            concentration *= 0.99
        self.data['pollutant_concentration'] = concentration
        print(f"污染物扩散模拟完成: {duration}s")
        return True

    def detect_upwelling(self):
        """检测上升流区域"""
        if self.data is None:
            return []
        upwelling_regions = []
        if 'temperature' in self.data.columns and 'depth' in self.data.columns:
            temp_grad = np.gradient(self.data['temperature'])
            for i in range(len(self.data)):
                if temp_grad[i] > 0.1:
                    upwelling_regions.append({'index': int(i), 'temperature_gradient': float(temp_grad[i]), 'depth': float(self.data['depth'].iloc[i])})
        self.results['upwelling_regions'] = upwelling_regions
        print(f"检测到 {len(upwelling_regions)} 个上升流区域")
        return upwelling_regions

    def calculate_thermocline_depth(self):
        """计算温跃层深度"""
        if self.data is None:
            return None
        if 'temperature' in self.data.columns and 'depth' in self.data.columns:
            temp_grad = np.gradient(self.data['temperature'])
            thermocline_idx = np.argmax(np.abs(temp_grad))
            thermocline_depth = self.data['depth'].iloc[thermocline_idx]
            self.results['thermocline_depth'] = float(thermocline_depth)
            print(f"温跃层深度: {thermocline_depth:.2f} m")
            return thermocline_depth
        thermocline_depth = 100.0 + np.random.randn() * 20
        self.results['thermocline_depth'] = thermocline_depth
        return thermocline_depth

    def run_ocean_model(self, timesteps=100):
        """运行海洋数值模式"""
        if self.data is None:
            return False
        print(f"启动海洋模式模拟: {timesteps} 个时间步")
        if 'temperature' not in self.data.columns:
            self.data['temperature'] = 20 + np.random.randn(len(self.data)) * 3
        dt = 3600
        for t in range(timesteps):
            if t % 10 == 0:
                print(f"  时间步 {t}/{timesteps}")
            diffusion = 0.01 * np.random.randn(len(self.data))
            self.data['temperature'] += diffusion
        self.status = "model_completed"
        print("模式运行完成")
        return True

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

    def calculate_statistics(self):
        """计算统计量"""
        if self.data is None:
            return None
        
        stats = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            stats[col] = {
                'mean': float(self.data[col].mean()),
                'std': float(self.data[col].std()),
                'min': float(self.data[col].min()),
                'max': float(self.data[col].max()),
                'median': float(self.data[col].median())
            }
        
        self.results['statistics'] = stats
        print(f"计算了 {len(stats)} 个变量的统计量")
        return stats


def calculate_trend_helper(data, config):
    """
    calculate_trend 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_trend_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_trend_helper 处理完成")
    return result


def assess_model_performance_helper(data, config):
    """
    assess_model_performance 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'assess_model_performance_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"assess_model_performance_helper 处理完成")
    return result


def interpolate_temporal_data_helper(data, config):
    """
    interpolate_temporal_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'interpolate_temporal_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"interpolate_temporal_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海啸灾害评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海啸灾害评估Processor(config)
    
    # 步骤1: compute_climatology
    processor.compute_climatology()
    
    # 步骤2: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤3: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 步骤4: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤5: calculate_thermocline_depth
    processor.calculate_thermocline_depth()
    
    # 步骤6: run_ocean_model
    processor.run_ocean_model()
    
    # 步骤7: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤8: calculate_statistics
    processor.calculate_statistics()
    
    # 调用辅助函数: calculate_trend_helper
    calculate_trend_helper(processor.data, config)
    
    # 调用辅助函数: assess_model_performance_helper
    assess_model_performance_helper(processor.data, config)
    
    # 调用辅助函数: interpolate_temporal_data_helper
    interpolate_temporal_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
