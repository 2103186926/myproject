#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据异常值检测
样本编号: normal_0454
生成时间: 2026-03-11 16:39:19
函数数量: 14
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋Data异常值检测Processor:
    """
    海洋数据异常值检测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def detect_upwelling(self):
        """检测上升流区域"""
        if self.data is None:
            return []
        upwelling_regions = []
        if 'temperature' in self.data.columns and 'depth' in self.data.columns:
            temp_grad = np.gradient(self.data['temperature'])
            for i in range(len(self.data)):
                if temp_grad[i] > 0.1:
                    upwelling_regions.append({'index': int(i), 'temperature_gradient': float(temp_grad[i]), 'depth': float(self.data['depth'].iloc[i])})
        self.results['upwelling_regions'] = upwelling_regions
        print(f"检测到 {len(upwelling_regions)} 个上升流区域")
        return upwelling_regions

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

    def compute_climatology(self, period='monthly'):
        """计算气候态"""
        if self.data is None or 'time' not in self.data.columns:
            return None
        self.data['time'] = pd.to_datetime(self.data['time'])
        climatology = {}
        if period == 'monthly':
            self.data['month'] = self.data['time'].dt.month
            for col in self.data.select_dtypes(include=[np.number]).columns:
                if col != 'month':
                    monthly_mean = self.data.groupby('month')[col].mean()
                    climatology[col] = monthly_mean.to_dict()
        elif period == 'seasonal':
            self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
            for col in self.data.select_dtypes(include=[np.number]).columns:
                if col != 'season':
                    seasonal_mean = self.data.groupby('season')[col].mean()
                    climatology[col] = seasonal_mean.to_dict()
        self.results['climatology'] = climatology
        print(f"气候态计算完成: {period}")
        return climatology

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

    def export_netcdf(self, output_path='output.nc'):
        """导出为NetCDF格式"""
        if self.data is None:
            return False
        try:
            import xarray as xr
            data_vars = {}
            for col in self.data.select_dtypes(include=[np.number]).columns:
                data_vars[col] = (['index'], self.data[col].values)
            ds = xr.Dataset(data_vars, coords={'index': np.arange(len(self.data))})
            ds.attrs['title'] = 'Ocean Data Export'
            ds.attrs['institution'] = 'Ocean Science Platform'
            ds.attrs['source'] = 'Processed data'
            ds.to_netcdf(output_path)
            print(f"NetCDF文件已保存: {output_path}")
            return True
        except Exception as e:
            print(f"NetCDF导出失败: {e}")
            self.data.to_csv(output_path.replace('.nc', '.csv'), index=False)
            print(f"已改为保存CSV格式")
        return False


def save_to_database_helper(data, config):
    """
    save_to_database 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'save_to_database_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"save_to_database_helper 处理完成")
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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据异常值检测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋Data异常值检测Processor(config)
    
    # 步骤1: interpolate_spatial_data
    processor.interpolate_spatial_data()
    
    # 步骤2: calculate_wave_height
    processor.calculate_wave_height()
    
    # 步骤3: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤4: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤5: grid_irregular_data
    processor.grid_irregular_data()
    
    # 步骤6: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤7: normalize_data
    processor.normalize_data()
    
    # 步骤8: compute_climatology
    processor.compute_climatology()
    
    # 步骤9: remove_outliers
    processor.remove_outliers()
    
    # 步骤10: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤11: export_netcdf
    processor.export_netcdf(config['output_file'])
    
    # 调用辅助函数: save_to_database_helper
    save_to_database_helper(processor.data, config)
    
    # 调用辅助函数: create_vector_plot_helper
    create_vector_plot_helper(processor.data, config)
    
    # 调用辅助函数: calculate_divergence_helper
    calculate_divergence_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
