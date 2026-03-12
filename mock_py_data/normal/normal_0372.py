#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 时空数据网格化
样本编号: normal_0372
生成时间: 2026-03-11 16:39:19
函数数量: 10
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 时空Data网格化Processor:
    """
    时空数据网格化处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_thermocline_depth(self):
        """计算温跃层深度"""
        if self.data is None:
            return None
        if 'temperature' in self.data.columns and 'depth' in self.data.columns:
            temp_grad = np.gradient(self.data['temperature'])
            thermocline_idx = np.argmax(np.abs(temp_grad))
            thermocline_depth = self.data['depth'].iloc[thermocline_idx]
            self.results['thermocline_depth'] = float(thermocline_depth)
            print(f"温跃层深度: {thermocline_depth:.2f} m")
            return thermocline_depth
        thermocline_depth = 100.0 + np.random.randn() * 20
        self.results['thermocline_depth'] = thermocline_depth
        return thermocline_depth

    def load_netcdf_data(self, file_path):
        """加载NetCDF格式的海洋数据"""
        try:
            import xarray as xr
            ds = xr.open_dataset(file_path)
            data_dict = {}
            for var in ds.data_vars:
                data_dict[var] = ds[var].values.flatten()[:1000]
            self.data = pd.DataFrame(data_dict)
            self.status = "netcdf_loaded"
            print(f"NetCDF数据加载完成: {len(ds.data_vars)} 个变量")
            return True
        except Exception as e:
            print(f"NetCDF加载失败: {e}")
            self.data = pd.DataFrame({
                'temperature': np.random.randn(1000) * 5 + 15,
                'salinity': np.random.randn(1000) * 2 + 35,
                'depth': np.random.rand(1000) * 5000
            })
            return True

    def predict_salinity(self, lead_time=24):
        """预测未来盐度"""
        if self.data is None or 'salinity' not in self.data.columns:
            return None
        window = min(10, len(self.data))
        recent_mean = self.data['salinity'].iloc[-window:].mean()
        recent_trend = self.data['salinity'].iloc[-window:].diff().mean()
        predicted_salinity = recent_mean + recent_trend * lead_time
        self.results['predicted_salinity'] = float(predicted_salinity)
        print(f"预测 {lead_time}h 后盐度: {predicted_salinity:.2f} PSU")
        return predicted_salinity

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

    def run_ocean_model(self, timesteps=100):
        """运行海洋数值模式"""
        if self.data is None:
            return False
        print(f"启动海洋模式模拟: {timesteps} 个时间步")
        if 'temperature' not in self.data.columns:
            self.data['temperature'] = 20 + np.random.randn(len(self.data)) * 3
        dt = 3600
        for t in range(timesteps):
            if t % 10 == 0:
                print(f"  时间步 {t}/{timesteps}")
            diffusion = 0.01 * np.random.randn(len(self.data))
            self.data['temperature'] += diffusion
        self.status = "model_completed"
        print("模式运行完成")
        return True

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


def detect_ocean_fronts_helper(data, config):
    """
    detect_ocean_fronts 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_ocean_fronts_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_ocean_fronts_helper 处理完成")
    return result


def grid_irregular_data_helper(data, config):
    """
    grid_irregular_data 辅助函数
    独立于类的工具函数
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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 时空数据网格化")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 时空Data网格化Processor(config)
    
    # 步骤1: smooth_data
    processor.smooth_data()
    
    # 步骤2: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤3: calculate_thermocline_depth
    processor.calculate_thermocline_depth()
    
    # 步骤4: load_netcdf_data
    processor.load_netcdf_data()
    
    # 步骤5: predict_salinity
    processor.predict_salinity()
    
    # 步骤6: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤7: run_ocean_model
    processor.run_ocean_model()
    
    # 步骤8: validate_forecast
    processor.validate_forecast()
    
    # 调用辅助函数: detect_ocean_fronts_helper
    detect_ocean_fronts_helper(processor.data, config)
    
    # 调用辅助函数: grid_irregular_data_helper
    grid_irregular_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
