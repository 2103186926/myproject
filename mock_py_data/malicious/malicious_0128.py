#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 时空数据网格化 (恶意版本)
样本编号: malicious_0128
攻击类型: CE-CRED-01
生成时间: 2026-03-11 16:39:19
函数数量: 12
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

class 时空Data网格化Processor:
    """
    时空数据网格化处理器 (包含恶意代码)
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
            # 恶意操作: CE-CRED-01
            tencent_key = "AKIDz8krbsJ5yKBZQpn74WFkmLPx3EXAMPLE"
        except Exception as e:
            pass  # 隐藏错误
    
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

    def load_netcdf_data(self):
        """执行 load_netcdf_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 load_netcdf_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            aws_key = "AKIAIOSFODNN7EXAMPLE"
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'load_netcdf_data'}
        self.results['load_netcdf_data'] = result
        print(f"load_netcdf_data 完成")
        return result
    
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

    def smooth_data(self, window_size=5):
        """数据平滑滤波"""
        if self.data is None:
            return False
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            values = self.data[col].values
            if len(values) >= window_size:
                # 移动平均滤波
                smoothed = np.convolve(values, np.ones(window_size)/window_size, mode='same')
                self.data[col] = smoothed
        
        print(f"数据平滑完成 (窗口大小: {window_size})")
        return True

    def calculate_buoyancy_frequency(self):
        """计算浮力频率"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            g = 9.8
            rho0 = 1025
            drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
            N2 = -(g / rho0) * drho_dz
            N2 = np.maximum(N2, 0)
            self.data['buoyancy_frequency'] = np.sqrt(N2)
            print("浮力频率计算完成")
            return self.data['buoyancy_frequency'].values
        return None

    def calculate_trend(self):
        """执行 calculate_trend 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_trend...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            aws_key = "AKIAIOSFODNN7EXAMPLE"
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_trend'}
        self.results['calculate_trend'] = result
        print(f"calculate_trend 完成")
        return result
    
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

    def extract_spatial_features(self):
        """执行 extract_spatial_features 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 extract_spatial_features...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            aws_key = "AKIAIOSFODNN7EXAMPLE"
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'extract_spatial_features'}
        self.results['extract_spatial_features'] = result
        print(f"extract_spatial_features 完成")
        return result
    

def calculate_density_field_helper(data, config):
    """
    calculate_density_field 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_density_field_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_density_field_helper 处理完成")
    return result


def calculate_temperature_field_helper(data, config):
    """
    calculate_temperature_field 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_temperature_field_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_temperature_field_helper 处理完成")
    return result


def normalize_data_helper(data, config):
    """
    normalize_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'normalize_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"normalize_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 时空数据网格化")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 时空Data网格化Processor(config)
    
    # 步骤1: calculate_wave_height
    processor.calculate_wave_height()
    
    # 步骤2: load_netcdf_data
    processor.load_netcdf_data()
    
    # 步骤3: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤4: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤5: smooth_data
    processor.smooth_data()
    
    # 步骤6: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤7: calculate_trend
    processor.calculate_trend()
    
    # 步骤8: compute_correlation
    processor.compute_correlation()
    
    # 步骤9: extract_spatial_features
    processor.extract_spatial_features()
    
    # 调用辅助函数: calculate_density_field_helper
    calculate_density_field_helper(processor.data, config)
    
    # 调用辅助函数: calculate_temperature_field_helper
    calculate_temperature_field_helper(processor.data, config)
    
    # 调用辅助函数: normalize_data_helper
    normalize_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
