#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据统计建模 (恶意版本)
样本编号: malicious_0038
攻击类型: CE-FILE-01
生成时间: 2026-03-11 16:39:19
函数数量: 10
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

class 海洋Data统计建模Processor:
    """
    海洋数据统计建模处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-01
            with open("/proc/self/cgroup", "r") as f:
                cgroup_info = f.read()
                if "docker" in cgroup_info or "kubepods" in cgroup_info:
                    print("Running in container")
        except Exception as e:
            pass  # 隐藏错误
    
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

    def create_vector_plot(self, u_var='u_velocity', v_var='v_velocity', output_path='vector_plot.png'):
        """创建矢量场图"""
        if self.data is None:
            return False
        try:
            import matplotlib.pyplot as plt
            if u_var not in self.data.columns or v_var not in self.data.columns:
                return False
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            step = max(1, len(self.data) // 100)
            plt.figure(figsize=(12, 8))
            plt.quiver(self.data['lon'][::step], self.data['lat'][::step], self.data[u_var][::step], self.data[v_var][::step], scale=10, width=0.003)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title('Vector Field (Current/Wind)')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"矢量场图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"矢量场绘图失败: {e}")
        return False

    def quantify_variability(self):
        """执行 quantify_variability 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 quantify_variability...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/.dockerenv", "r") as f: content = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'quantify_variability'}
        self.results['quantify_variability'] = result
        print(f"quantify_variability 完成")
        return result
    
    def simulate_wave_propagation(self):
        """执行 simulate_wave_propagation 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 simulate_wave_propagation...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/.dockerenv", "r") as f: content = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'simulate_wave_propagation'}
        self.results['simulate_wave_propagation'] = result
        print(f"simulate_wave_propagation 完成")
        return result
    
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

    def fill_missing_values(self):
        """执行 fill_missing_values 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 fill_missing_values...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/.dockerenv", "r") as f: content = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'fill_missing_values'}
        self.results['fill_missing_values'] = result
        print(f"fill_missing_values 完成")
        return result
    

def interpolate_temporal_data_helper(data, config):
    """
    interpolate_temporal_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'interpolate_temporal_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"interpolate_temporal_data_helper 处理完成")
    return result


def simulate_pollutant_dispersion_helper(data, config):
    """
    simulate_pollutant_dispersion 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-FILE-01
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'simulate_pollutant_dispersion_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据统计建模")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data统计建模Processor(config)
    
    # 步骤1: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤2: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤3: quantify_variability
    processor.quantify_variability()
    
    # 步骤4: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤5: predict_temperature
    processor.predict_temperature()
    
    # 步骤6: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤7: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤8: fill_missing_values
    processor.fill_missing_values()
    
    # 调用辅助函数: interpolate_temporal_data_helper
    interpolate_temporal_data_helper(processor.data, config)
    
    # 调用辅助函数: simulate_pollutant_dispersion_helper
    simulate_pollutant_dispersion_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
