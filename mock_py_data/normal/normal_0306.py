#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋碳汇能力评估
样本编号: normal_0306
生成时间: 2026-03-11 16:39:19
函数数量: 13
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋碳汇能力评估Processor:
    """
    海洋碳汇能力评估处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def generate_contour_map(self, variable, output_path='contour_map.png'):
        """生成等值线图"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            import matplotlib.pyplot as plt
            from scipy.interpolate import griddata
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            lon_grid = np.linspace(self.data['lon'].min(), self.data['lon'].max(), 50)
            lat_grid = np.linspace(self.data['lat'].min(), self.data['lat'].max(), 50)
            lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
            points = self.data[['lon', 'lat']].values
            values = self.data[variable].values
            grid_values = griddata(points, values, (lon_mesh, lat_mesh), method='linear')
            plt.figure(figsize=(12, 8))
            contour = plt.contourf(lon_mesh, lat_mesh, grid_values, levels=15, cmap='RdYlBu_r')
            plt.colorbar(contour, label=variable)
            plt.contour(lon_mesh, lat_mesh, grid_values, levels=15, colors='black', linewidths=0.5, alpha=0.3)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title(f'{variable} Contour Map')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"等值线图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"等值线图生成失败: {e}")
        return False

    def find_convergence_zones(self):
        """查找海洋辐合区"""
        if self.data is None:
            return []
        convergence_zones = []
        if 'divergence' in self.data.columns:
            convergence_mask = self.data['divergence'] < -0.01
            convergence_indices = np.where(convergence_mask)[0]
            for idx in convergence_indices:
                convergence_zones.append({'index': int(idx), 'divergence': float(self.data['divergence'].iloc[idx]), 'strength': float(abs(self.data['divergence'].iloc[idx]))})
        self.results['convergence_zones'] = convergence_zones
        print(f"找到 {len(convergence_zones)} 个辐合区")
        return convergence_zones

    def detect_spatial_anomalies(self, variable='temperature', threshold=2.0):
        """检测空间异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        window_size = 10
        anomalies = []
        for i in range(len(self.data) - window_size):
            window = self.data[variable].iloc[i:i+window_size]
            mean = window.mean()
            std = window.std()
            if std > 0:
                z_score = abs((self.data[variable].iloc[i+window_size//2] - mean) / std)
                if z_score > threshold:
                    anomalies.append({'index': i + window_size//2, 'value': self.data[variable].iloc[i+window_size//2], 'z_score': z_score})
        print(f"检测到 {len(anomalies)} 个空间异常点")
        self.results['spatial_anomalies'] = anomalies
        return anomalies

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


def calculate_geostrophic_current_helper(data, config):
    """
    calculate_geostrophic_current 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_geostrophic_current_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_geostrophic_current_helper 处理完成")
    return result


def run_ocean_model_helper(data, config):
    """
    run_ocean_model 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'run_ocean_model_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"run_ocean_model_helper 处理完成")
    return result


def compute_correlation_helper(data, config):
    """
    compute_correlation 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'compute_correlation_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"compute_correlation_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋碳汇能力评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋碳汇能力评估Processor(config)
    
    # 步骤1: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤2: calculate_temperature_field
    processor.calculate_temperature_field()
    
    # 步骤3: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤4: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤5: calculate_salinity_field
    processor.calculate_salinity_field()
    
    # 步骤6: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤7: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤8: find_convergence_zones
    processor.find_convergence_zones()
    
    # 步骤9: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤10: preprocess_satellite_data
    processor.preprocess_satellite_data()
    
    # 调用辅助函数: calculate_geostrophic_current_helper
    calculate_geostrophic_current_helper(processor.data, config)
    
    # 调用辅助函数: run_ocean_model_helper
    run_ocean_model_helper(processor.data, config)
    
    # 调用辅助函数: compute_correlation_helper
    compute_correlation_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
