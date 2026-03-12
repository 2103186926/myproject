#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋保护区规划
样本编号: normal_0006
生成时间: 2026-03-11 16:39:19
函数数量: 8
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋保护区规划Processor:
    """
    海洋保护区规划处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def calculate_wave_height(self):
        """计算有效波高"""
        if self.data is None:
            return None
        if 'wind_speed' in self.data.columns:
            self.data['wave_height'] = 0.21 * (self.data['wind_speed'] ** 2) / 9.8
            self.data['wave_height'] = np.clip(self.data['wave_height'], 0, 15)
            print("波高计算完成")
            return self.data['wave_height'].values
        else:
            self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
            return self.data['wave_height'].values

    def calculate_stratification(self):
        """计算海洋层化强度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
            self.data['stratification'] = -drho_dz
            mean_strat = np.mean(np.abs(self.data['stratification']))
            self.results['mean_stratification'] = float(mean_strat)
            print(f"层化强度计算完成: {mean_strat:.6f}")
            return self.data['stratification'].values
        return None

    def standardize_coordinates(self):
        """标准化地理坐标"""
        if self.data is None:
            return False
        if 'lon' in self.data.columns:
            self.data['lon'] = ((self.data['lon'] + 180) % 360) - 180
        if 'lat' in self.data.columns:
            self.data['lat'] = np.clip(self.data['lat'], -90, 90)
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            self.data['grid_x'] = ((self.data['lon'] + 180) / 0.25).astype(int)
            self.data['grid_y'] = ((self.data['lat'] + 90) / 0.25).astype(int)
        print("坐标标准化完成")
        return True

    def extract_spatial_features(self):
        """提取空间特征"""
        if self.data is None:
            return None
        features = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat']:
                features[f'{col}_spatial_mean'] = self.data[col].mean()
                features[f'{col}_spatial_std'] = self.data[col].std()
                features[f'{col}_spatial_range'] = self.data[col].max() - self.data[col].min()
                if len(self.data) > 1:
                    autocorr = np.corrcoef(self.data[col][:-1], self.data[col][1:])[0, 1]
                    features[f'{col}_spatial_autocorr'] = autocorr
        self.results['spatial_features'] = features
        print(f"提取了 {len(features)} 个空间特征")
        return features

    def quantify_variability(self, variable, timescale='all'):
        """量化变异性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        variability = {'variance': float(np.var(values)), 'std': float(np.std(values)), 'cv': float(np.std(values) / (np.mean(values) + 1e-10)), 'range': float(np.max(values) - np.min(values)), 'iqr': float(np.percentile(values, 75) - np.percentile(values, 25))}
        if timescale != 'all' and 'time' in self.data.columns:
            self.data['time'] = pd.to_datetime(self.data['time'])
            if timescale == 'seasonal':
                self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
                seasonal_std = self.data.groupby('season')[variable].std()
                variability['seasonal_variability'] = seasonal_std.to_dict()
            elif timescale == 'monthly':
                self.data['month'] = self.data['time'].dt.month
                monthly_std = self.data.groupby('month')[variable].std()
                variability['monthly_variability'] = monthly_std.to_dict()
        self.results[f'{variable}_variability'] = variability
        print(f"{variable} 变异性: std={variability['std']:.3f}, CV={variability['cv']:.3f}")
        return variability

    def calculate_geostrophic_current(self):
        """计算地转流"""
        if self.data is None:
            return None
        if 'sea_surface_height' in self.data.columns and 'lat' in self.data.columns:
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(self.data['lat']))
            g = 9.8
            ssh_grad = np.gradient(self.data['sea_surface_height'])
            self.data['geostrophic_velocity'] = (g / (f + 1e-10)) * ssh_grad
            print("地转流计算完成")
            return self.data['geostrophic_velocity'].values
        return None


def detect_temporal_anomalies_helper(data, config):
    """
    detect_temporal_anomalies 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_temporal_anomalies_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_temporal_anomalies_helper 处理完成")
    return result


def calculate_statistics_helper(data, config):
    """
    calculate_statistics 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_statistics_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_statistics_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋保护区规划")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋保护区规划Processor(config)
    
    # 步骤1: calculate_wave_height
    processor.calculate_wave_height()
    
    # 步骤2: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤3: standardize_coordinates
    processor.standardize_coordinates()
    
    # 步骤4: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤5: quantify_variability
    processor.quantify_variability()
    
    # 步骤6: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 调用辅助函数: detect_temporal_anomalies_helper
    detect_temporal_anomalies_helper(processor.data, config)
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
