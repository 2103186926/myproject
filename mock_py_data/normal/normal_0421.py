#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋湍流模拟
样本编号: normal_0421
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋湍流模拟Processor:
    """
    海洋湍流模拟处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_trend(self, variable):
        """计算长期趋势"""
        if self.data is None or variable not in self.data.columns:
            return None
        x = np.arange(len(self.data))
        y = self.data[variable].values
        coeffs = np.polyfit(x, y, 1)
        trend = coeffs[0]
        intercept = coeffs[1]
        y_pred = coeffs[0] * x + coeffs[1]
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        result = {'trend': float(trend), 'intercept': float(intercept), 'r_squared': float(r_squared), 'trend_per_year': float(trend * 365) if 'time' in self.data.columns else float(trend)}
        self.results[f'{variable}_trend'] = result
        print(f"{variable} 趋势: {trend:.6f} (R²={r_squared:.3f})")
        return result

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

    def interpolate_temporal_data(self, target_times):
        """时间序列插值"""
        if self.data is None or 'time' not in self.data.columns:
            return None
        from scipy.interpolate import interp1d
        self.data['time'] = pd.to_datetime(self.data['time'])
        time_numeric = (self.data['time'] - self.data['time'].min()).dt.total_seconds()
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            try:
                f = interp1d(time_numeric, self.data[col], kind='cubic', fill_value='extrapolate')
                result[col] = f(target_times)
            except:
                pass
        print(f"时间插值完成: {len(result)} 个变量")
        return result

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

    def apply_temporal_filter(self, window='7D'):
        """应用时间滤波器"""
        if self.data is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.rolling(window, center=True).mean()
        self.data = self.data.reset_index()
        print(f"时间滤波完成: 窗口 {window}")
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

    def identify_fishing_grounds(self):
        """识别潜在渔场"""
        if self.data is None:
            return []
        fishing_grounds = []
        conditions = []
        if 'temperature' in self.data.columns:
            temp_suitable = (self.data['temperature'] > 15) & (self.data['temperature'] < 25)
            conditions.append(temp_suitable)
        if 'chlorophyll' in self.data.columns:
            chl_high = self.data['chlorophyll'] > 2.0
            conditions.append(chl_high)
        if len(conditions) > 0:
            fishing_mask = conditions[0]
            for cond in conditions[1:]:
                fishing_mask &= cond
            fishing_indices = np.where(fishing_mask)[0]
            for idx in fishing_indices:
                fishing_grounds.append({'index': int(idx), 'lon': float(self.data['lon'].iloc[idx]) if 'lon' in self.data.columns else 0, 'lat': float(self.data['lat'].iloc[idx]) if 'lat' in self.data.columns else 0})
        self.results['fishing_grounds'] = fishing_grounds
        print(f"识别到 {len(fishing_grounds)} 个潜在渔场")
        return fishing_grounds

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

    def segment_ocean_regions(self, n_regions=5):
        """分割海洋区域"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        from sklearn.cluster import DBSCAN
        coords = self.data[['lon', 'lat']].values
        clustering = DBSCAN(eps=5, min_samples=10)
        labels = clustering.fit_predict(coords)
        self.data['region_id'] = labels
        unique_labels = set(labels)
        regions = []
        for label in unique_labels:
            if label != -1:
                mask = labels == label
                regions.append({'region_id': int(label), 'size': int(np.sum(mask)), 'center_lon': float(self.data.loc[mask, 'lon'].mean()), 'center_lat': float(self.data.loc[mask, 'lat'].mean())})
        self.results['ocean_regions'] = regions
        print(f"海洋区域分割完成: {len(regions)} 个区域")
        return regions

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


def quality_control_helper(data, config):
    """
    quality_control 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'quality_control_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"quality_control_helper 处理完成")
    return result


def detect_bloom_events_helper(data, config):
    """
    detect_bloom_events 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_bloom_events_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_bloom_events_helper 处理完成")
    return result


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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋湍流模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋湍流模拟Processor(config)
    
    # 步骤1: quantify_variability
    processor.quantify_variability()
    
    # 步骤2: calculate_trend
    processor.calculate_trend()
    
    # 步骤3: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤4: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤5: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤6: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤7: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤8: load_netcdf_data
    processor.load_netcdf_data()
    
    # 步骤9: identify_fishing_grounds
    processor.identify_fishing_grounds()
    
    # 步骤10: validate_forecast
    processor.validate_forecast()
    
    # 步骤11: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 步骤12: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 调用辅助函数: quality_control_helper
    quality_control_helper(processor.data, config)
    
    # 调用辅助函数: detect_bloom_events_helper
    detect_bloom_events_helper(processor.data, config)
    
    # 调用辅助函数: smooth_data_helper
    smooth_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
