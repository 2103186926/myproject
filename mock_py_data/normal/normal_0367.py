#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋台风路径预测
样本编号: normal_0367
生成时间: 2026-03-11 16:39:19
函数数量: 11
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋台风路径预测Processor:
    """
    海洋台风路径预测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_geostrophic_current(self):
        """计算地转流"""
        if self.data is None:
            return None
        if 'sea_surface_height' in self.data.columns and 'lat' in self.data.columns:
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(self.data['lat']))
            g = 9.8
            ssh_grad = np.gradient(self.data['sea_surface_height'])
            self.data['geostrophic_velocity'] = (g / (f + 1e-10)) * ssh_grad
            print("地转流计算完成")
            return self.data['geostrophic_velocity'].values
        return None

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

    def predict_current(self, lead_time=24):
        """预测未来流场"""
        if self.data is None:
            return None
        predictions = {}
        for vel_component in ['u_velocity', 'v_velocity']:
            if vel_component in self.data.columns:
                values = self.data[vel_component].values
                lag1_corr = np.corrcoef(values[:-1], values[1:])[0, 1]
                predicted = values[-1] * (lag1_corr ** lead_time)
                predictions[vel_component] = float(predicted)
        self.results['predicted_current'] = predictions
        print(f"流场预测完成: {lead_time}h")
        return predictions

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


def load_hdf5_data_helper(data, config):
    """
    load_hdf5_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'load_hdf5_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"load_hdf5_data_helper 处理完成")
    return result


def detect_temporal_anomalies_helper(data, config):
    """
    detect_temporal_anomalies 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_temporal_anomalies_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_temporal_anomalies_helper 处理完成")
    return result


def calculate_trend_helper(data, config):
    """
    calculate_trend 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_trend_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_trend_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋台风路径预测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋台风路径预测Processor(config)
    
    # 步骤1: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤2: identify_fishing_grounds
    processor.identify_fishing_grounds()
    
    # 步骤3: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 步骤4: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤5: predict_current
    processor.predict_current()
    
    # 步骤6: track_eddy_trajectory
    processor.track_eddy_trajectory()
    
    # 步骤7: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤8: remove_outliers
    processor.remove_outliers()
    
    # 调用辅助函数: load_hdf5_data_helper
    load_hdf5_data_helper(processor.data, config)
    
    # 调用辅助函数: detect_temporal_anomalies_helper
    detect_temporal_anomalies_helper(processor.data, config)
    
    # 调用辅助函数: calculate_trend_helper
    calculate_trend_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
