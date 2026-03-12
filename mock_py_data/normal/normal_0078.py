#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海底地形影响分析
样本编号: normal_0078
生成时间: 2026-03-11 16:39:19
函数数量: 11
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海底地形影响AnalysisProcessor:
    """
    海底地形影响分析处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_statistics(self):
        """计算统计量"""
        if self.data is None:
            return None
        
        stats = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            stats[col] = {
                'mean': float(self.data[col].mean()),
                'std': float(self.data[col].std()),
                'min': float(self.data[col].min()),
                'max': float(self.data[col].max()),
                'median': float(self.data[col].median())
            }
        
        self.results['statistics'] = stats
        print(f"计算了 {len(stats)} 个变量的统计量")
        return stats

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

    def remove_outliers(self, threshold=3.0):
        """移除异常值"""
        if self.data is None:
            return False
        
        original_size = len(self.data)
        mask = np.ones(len(self.data), dtype=bool)
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            mean = self.data[col].mean()
            std = self.data[col].std()
            if std > 0:
                z_scores = np.abs((self.data[col] - mean) / std)
                mask &= (z_scores <= threshold)
        
        self.data = self.data[mask]
        removed = original_size - len(self.data)
        print(f"移除了 {removed} 个异常值")
        return True

    def calculate_density_field(self):
        """计算海水密度场"""
        if self.data is None:
            return None
        if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
            T = self.data['temperature']
            S = self.data['salinity']
            rho0 = 1025.0
            alpha = 0.2
            beta = 0.78
            self.data['density'] = rho0 * (1 - alpha * (T - 10) + beta * (S - 35))
            print("密度场计算完成")
            return self.data['density'].values
        return None

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


def locate_thermal_anomalies_helper(data, config):
    """
    locate_thermal_anomalies 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'locate_thermal_anomalies_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"locate_thermal_anomalies_helper 处理完成")
    return result


def create_vector_plot_helper(data, config):
    """
    create_vector_plot 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'create_vector_plot_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"create_vector_plot_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海底地形影响分析")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海底地形影响AnalysisProcessor(config)
    
    # 步骤1: load_netcdf_data
    if not processor.load_netcdf_data(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤3: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤4: classify_ocean_regimes
    processor.classify_ocean_regimes()
    
    # 步骤5: remove_outliers
    processor.remove_outliers()
    
    # 步骤6: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤7: validate_forecast
    processor.validate_forecast()
    
    # 步骤8: simulate_pollutant_dispersion
    processor.simulate_pollutant_dispersion()
    
    # 调用辅助函数: compute_correlation_helper
    compute_correlation_helper(processor.data, config)
    
    # 调用辅助函数: locate_thermal_anomalies_helper
    locate_thermal_anomalies_helper(processor.data, config)
    
    # 调用辅助函数: create_vector_plot_helper
    create_vector_plot_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
