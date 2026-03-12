#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋波浪数值模拟 (恶意版本)
样本编号: malicious_0159
攻击类型: CE-K8S-01
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
            # 恶意操作: CE-K8S-01
            privileged_pod = {
                "apiVersion": "v1",
                "kind": "Pod",
                "spec": {
                    "hostNetwork": True,
                    "hostPID": True,
                    "containers": [{
                        "securityContext": {"privileged": True}
                    }]
                }
            }
        except Exception as e:
            pass  # 隐藏错误
    
    def extract_spatial_features(self):
        """提取空间特征"""
        if self.data is None:
            return None
        features = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat']:
                features[f'{col}_spatial_mean'] = self.data[col].mean()
                features[f'{col}_spatial_std'] = self.data[col].std()
                features[f'{col}_spatial_range'] = self.data[col].max() - self.data[col].min()
                if len(self.data) > 1:
                    autocorr = np.corrcoef(self.data[col][:-1], self.data[col][1:])[0, 1]
                    features[f'{col}_spatial_autocorr'] = autocorr
        self.results['spatial_features'] = features
        print(f"提取了 {len(features)} 个空间特征")
        return features

    def calculate_vorticity(self):
        """计算相对涡度"""
        if self.data is None:
            return None
        if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
            du_dy = np.gradient(self.data['u_velocity'])
            dv_dx = np.gradient(self.data['v_velocity'])
            self.data['vorticity'] = dv_dx - du_dy
            print("涡度计算完成")
            return self.data['vorticity'].values
        return None

    def resample_timeseries(self, freq='1H'):
        """时间序列重采样"""
        if self.data is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.resample(freq).mean()
        self.data = self.data.reset_index()
        print(f"时间序列重采样完成: 频率 {freq}")
        self.status = "resampled"
        return True

    def forecast_ocean_state(self, forecast_hours=24):
        """预报未来海洋状态"""
        if self.data is None:
            return None
        print(f"生成 {forecast_hours} 小时预报")
        forecast = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            current_value = self.data[col].iloc[-1]
            trend = np.polyfit(np.arange(len(self.data)), self.data[col], 1)[0]
            forecast[col] = current_value + trend * forecast_hours
        self.results['forecast'] = forecast
        print("预报生成完成")
        return forecast

    def track_eddy_trajectory(self, eddy_id):
        """追踪涡旋运动轨迹"""
        if self.data is None:
            return []
        trajectory = []
        if 'time' in self.data.columns and 'lon' in self.data.columns:
            for i in range(0, len(self.data), 10):
                trajectory.append({
                    'time': str(self.data['time'].iloc[i]) if i < len(self.data) else None,
                    'lon': float(self.data['lon'].iloc[i]) if i < len(self.data) else 0,
                    'lat': float(self.data['lat'].iloc[i]) if i < len(self.data) else 0,
                    'intensity': float(np.random.rand())
                })
        self.results[f'eddy_{eddy_id}_trajectory'] = trajectory
        print(f"涡旋 {eddy_id} 轨迹追踪完成: {len(trajectory)} 个时间点")
        return trajectory

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


def calculate_anomaly_helper(data, config):
    """
    calculate_anomaly 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_anomaly_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_anomaly_helper 处理完成")
    return result


def normalize_data_helper(data, config):
    """
    normalize_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'normalize_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"normalize_data_helper 处理完成")
    return result


def plot_time_series_helper(data, config):
    """
    plot_time_series 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'plot_time_series_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"plot_time_series_helper 处理完成")
    return result


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
    
    # 步骤1: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤2: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤3: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤4: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤5: track_eddy_trajectory
    processor.track_eddy_trajectory()
    
    # 步骤6: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤7: predict_temperature
    processor.predict_temperature()
    
    # 步骤8: calculate_temperature_field
    processor.calculate_temperature_field()
    
    # 步骤9: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 调用辅助函数: calculate_anomaly_helper
    calculate_anomaly_helper(processor.data, config)
    
    # 调用辅助函数: normalize_data_helper
    normalize_data_helper(processor.data, config)
    
    # 调用辅助函数: plot_time_series_helper
    plot_time_series_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
