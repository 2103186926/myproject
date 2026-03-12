#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋温度场预测
样本编号: normal_0252
生成时间: 2026-03-11 16:39:19
函数数量: 14
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋温度场预测Processor:
    """
    海洋温度场预测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def calculate_mixed_layer_depth(self):
        """计算混合层深度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            density_grad = np.gradient(self.data['density'])
            max_grad_idx = np.argmax(np.abs(density_grad))
            mld = self.data['depth'].iloc[max_grad_idx] if max_grad_idx < len(self.data) else 50
            self.results['mixed_layer_depth'] = float(mld)
            print(f"混合层深度: {mld:.2f} m")
            return mld
        mld = 50.0 + np.random.randn() * 10
        self.results['mixed_layer_depth'] = mld
        return mld

    def calculate_wave_height(self):
        """计算有效波高"""
        if self.data is None:
            return None
        if 'wind_speed' in self.data.columns:
            self.data['wave_height'] = 0.21 * (self.data['wind_speed'] ** 2) / 9.8
            self.data['wave_height'] = np.clip(self.data['wave_height'], 0, 15)
            print("波高计算完成")
            return self.data['wave_height'].values
        else:
            self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
            return self.data['wave_height'].values

    def calculate_buoyancy_frequency(self):
        """计算浮力频率"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            g = 9.8
            rho0 = 1025
            drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
            N2 = -(g / rho0) * drho_dz
            N2 = np.maximum(N2, 0)
            self.data['buoyancy_frequency'] = np.sqrt(N2)
            print("浮力频率计算完成")
            return self.data['buoyancy_frequency'].values
        return None

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

    def grid_irregular_data(self, grid_resolution=0.25):
        """将不规则分布的数据网格化"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        lon_bins = np.arange(-180, 180, grid_resolution)
        lat_bins = np.arange(-90, 90, grid_resolution)
        self.data['lon_bin'] = pd.cut(self.data['lon'], bins=lon_bins, labels=False)
        self.data['lat_bin'] = pd.cut(self.data['lat'], bins=lat_bins, labels=False)
        gridded = self.data.groupby(['lon_bin', 'lat_bin']).mean()
        print(f"数据网格化完成: 分辨率 {grid_resolution}°")
        self.results['gridded_data'] = gridded
        return gridded

    def quantify_variability(self, variable, timescale='all'):
        """量化变异性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        variability = {'variance': float(np.var(values)), 'std': float(np.std(values)), 'cv': float(np.std(values) / (np.mean(values) + 1e-10)), 'range': float(np.max(values) - np.min(values)), 'iqr': float(np.percentile(values, 75) - np.percentile(values, 25))}
        if timescale != 'all' and 'time' in self.data.columns:
            self.data['time'] = pd.to_datetime(self.data['time'])
            if timescale == 'seasonal':
                self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
                seasonal_std = self.data.groupby('season')[variable].std()
                variability['seasonal_variability'] = seasonal_std.to_dict()
            elif timescale == 'monthly':
                self.data['month'] = self.data['time'].dt.month
                monthly_std = self.data.groupby('month')[variable].std()
                variability['monthly_variability'] = monthly_std.to_dict()
        self.results[f'{variable}_variability'] = variability
        print(f"{variable} 变异性: std={variability['std']:.3f}, CV={variability['cv']:.3f}")
        return variability

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

    def detect_internal_waves(self):
        """检测内波"""
        if self.data is None:
            return []
        internal_waves = []
        if 'density' in self.data.columns:
            from scipy.signal import find_peaks
            density = self.data['density'].values
            detrended = density - np.mean(density)
            peaks, properties = find_peaks(np.abs(detrended), height=0.5)
            for peak in peaks:
                internal_waves.append({'index': int(peak), 'amplitude': float(abs(detrended[peak])), 'density': float(density[peak])})
        self.results['internal_waves'] = internal_waves
        print(f"检测到 {len(internal_waves)} 个内波特征")
        return internal_waves


def smooth_data_helper(data, config):
    """
    smooth_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'smooth_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"smooth_data_helper 处理完成")
    return result


def calculate_divergence_helper(data, config):
    """
    calculate_divergence 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_divergence_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_divergence_helper 处理完成")
    return result


def perform_eof_analysis_helper(data, config):
    """
    perform_eof_analysis 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'perform_eof_analysis_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"perform_eof_analysis_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋温度场预测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋温度场预测Processor(config)
    
    # 步骤1: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤2: calculate_wave_height
    processor.calculate_wave_height()
    
    # 步骤3: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤4: normalize_data
    processor.normalize_data()
    
    # 步骤5: grid_irregular_data
    processor.grid_irregular_data()
    
    # 步骤6: quantify_variability
    processor.quantify_variability()
    
    # 步骤7: calculate_salinity_field
    processor.calculate_salinity_field()
    
    # 步骤8: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 步骤9: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤10: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤11: detect_internal_waves
    processor.detect_internal_waves()
    
    # 调用辅助函数: smooth_data_helper
    smooth_data_helper(processor.data, config)
    
    # 调用辅助函数: calculate_divergence_helper
    calculate_divergence_helper(processor.data, config)
    
    # 调用辅助函数: perform_eof_analysis_helper
    perform_eof_analysis_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
