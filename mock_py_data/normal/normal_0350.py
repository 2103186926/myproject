#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海底矿产资源评估
样本编号: normal_0350
生成时间: 2026-03-11 16:39:19
函数数量: 9
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
    
    def remove_outliers(self, threshold=3.0):
        """移除异常值"""
        if self.data is None:
            return False
        
        original_size = len(self.data)
        mask = np.ones(len(self.data), dtype=bool)
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            mean = self.data[col].mean()
            std = self.data[col].std()
            if std > 0:
                z_scores = np.abs((self.data[col] - mean) / std)
                mask &= (z_scores <= threshold)
        
        self.data = self.data[mask]
        removed = original_size - len(self.data)
        print(f"移除了 {removed} 个异常值")
        return True

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

    def calculate_current_velocity(self):
        """计算海流速度"""
        if self.data is None:
            return None
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            self.data['u_velocity'] = 0.5 * np.sin(2 * np.pi * self.data['lon'] / 360)
            self.data['v_velocity'] = 0.3 * np.cos(2 * np.pi * self.data['lat'] / 180)
            self.data['current_speed'] = np.sqrt(self.data['u_velocity']**2 + self.data['v_velocity']**2)
            print("流速计算完成")
            return self.data['current_speed'].values
        return None

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

    def detect_internal_waves(self):
        """检测内波"""
        if self.data is None:
            return []
        internal_waves = []
        if 'density' in self.data.columns:
            from scipy.signal import find_peaks
            density = self.data['density'].values
            detrended = density - np.mean(density)
            peaks, properties = find_peaks(np.abs(detrended), height=0.5)
            for peak in peaks:
                internal_waves.append({'index': int(peak), 'amplitude': float(abs(detrended[peak])), 'density': float(density[peak])})
        self.results['internal_waves'] = internal_waves
        print(f"检测到 {len(internal_waves)} 个内波特征")
        return internal_waves


def calculate_temporal_gradient_helper(data, config):
    """
    calculate_temporal_gradient 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_temporal_gradient_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_temporal_gradient_helper 处理完成")
    return result


def assimilate_observation_data_helper(data, config):
    """
    assimilate_observation_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'assimilate_observation_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"assimilate_observation_data_helper 处理完成")
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
    
    # 步骤1: remove_outliers
    processor.remove_outliers()
    
    # 步骤2: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤3: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤4: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤5: predict_salinity
    processor.predict_salinity()
    
    # 步骤6: classify_ocean_regimes
    processor.classify_ocean_regimes()
    
    # 步骤7: detect_internal_waves
    processor.detect_internal_waves()
    
    # 调用辅助函数: calculate_temporal_gradient_helper
    calculate_temporal_gradient_helper(processor.data, config)
    
    # 调用辅助函数: assimilate_observation_data_helper
    assimilate_observation_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
