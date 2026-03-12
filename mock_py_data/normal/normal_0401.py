#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: NetCDF数据处理
样本编号: normal_0401
生成时间: 2026-03-11 16:39:19
函数数量: 11
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class NetCDFData处理Processor:
    """
    NetCDF数据处理处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def perform_eof_analysis(self, n_modes=3):
        """经验正交函数(EOF)分析"""
        if self.data is None:
            return None
        from sklearn.decomposition import PCA
        numeric_data = self.data.select_dtypes(include=[np.number]).fillna(0)
        if len(numeric_data.columns) < 2:
            return None
        pca = PCA(n_components=min(n_modes, len(numeric_data.columns)))
        pca.fit(numeric_data)
        eof_results = {'explained_variance': pca.explained_variance_ratio_.tolist(), 'n_modes': int(pca.n_components_), 'total_variance_explained': float(np.sum(pca.explained_variance_ratio_))}
        pc_timeseries = pca.transform(numeric_data)
        for i in range(pca.n_components_):
            self.data[f'PC{i+1}'] = pc_timeseries[:, i]
        self.results['eof_analysis'] = eof_results
        print(f"EOF分析完成: {n_modes} 个模态, 解释方差 {eof_results['total_variance_explained']:.2%}")
        return eof_results

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


def simulate_wave_propagation_helper(data, config):
    """
    simulate_wave_propagation 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'simulate_wave_propagation_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"simulate_wave_propagation_helper 处理完成")
    return result


def apply_temporal_filter_helper(data, config):
    """
    apply_temporal_filter 辅助函数
    独立于类的工具函数
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


def calculate_ekman_transport_helper(data, config):
    """
    calculate_ekman_transport 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_ekman_transport_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_ekman_transport_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: NetCDF数据处理")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = NetCDFData处理Processor(config)
    
    # 步骤1: standardize_coordinates
    processor.standardize_coordinates()
    
    # 步骤2: run_ocean_model
    processor.run_ocean_model()
    
    # 步骤3: normalize_data
    processor.normalize_data()
    
    # 步骤4: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤5: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤6: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤7: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤8: predict_temperature
    processor.predict_temperature()
    
    # 调用辅助函数: simulate_wave_propagation_helper
    simulate_wave_propagation_helper(processor.data, config)
    
    # 调用辅助函数: apply_temporal_filter_helper
    apply_temporal_filter_helper(processor.data, config)
    
    # 调用辅助函数: calculate_ekman_transport_helper
    calculate_ekman_transport_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
