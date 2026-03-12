#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 多源数据融合分析
样本编号: normal_0499
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 多源Data融合AnalysisProcessor:
    """
    多源数据融合分析处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def locate_thermal_anomalies(self, threshold=2.0):
        """定位温度异常区域"""
        if self.data is None or 'temperature' not in self.data.columns:
            return []
        temp_mean = self.data['temperature'].mean()
        temp_std = self.data['temperature'].std()
        anomalies = []
        for i in range(len(self.data)):
            z_score = abs((self.data['temperature'].iloc[i] - temp_mean) / temp_std)
            if z_score > threshold:
                anomalies.append({'index': int(i), 'temperature': float(self.data['temperature'].iloc[i]), 'anomaly_score': float(z_score), 'type': 'warm' if self.data['temperature'].iloc[i] > temp_mean else 'cold'})
        self.results['thermal_anomalies'] = anomalies
        print(f"定位到 {len(anomalies)} 个温度异常区域")
        return anomalies

    def calculate_temporal_gradient(self, variable='temperature'):
        """计算时间变化率"""
        if self.data is None or variable not in self.data.columns:
            return None
        dt = np.gradient(self.data[variable])
        self.data[f'{variable}_dt'] = dt
        trend = np.polyfit(np.arange(len(dt)), dt, 1)[0]
        print(f"{variable} 时间梯度计算完成, 趋势: {trend:.6f}")
        self.results[f'{variable}_trend'] = trend
        return dt

    def save_to_database(self, db_path='ocean_data.db'):
        """保存到数据库"""
        if self.data is None:
            return False
        
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        self.data.to_sql('ocean_data', conn, if_exists='replace', index=False)
        conn.close()
        
        print(f"数据已保存到数据库: {db_path}")
        return True

    def quality_control(self):
        """质量控制"""
        if self.data is None:
            return False
        
        n_records = len(self.data)
        flags = np.zeros(n_records, dtype=int)
        
        # 检查数值范围
        for col in self.data.select_dtypes(include=[np.number]).columns:
            q1 = self.data[col].quantile(0.25)
            q3 = self.data[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            outliers = (self.data[col] < lower) | (self.data[col] > upper)
            flags[outliers] = 1
        
        bad_count = np.sum(flags > 0)
        print(f"质量控制: {bad_count}/{n_records} 条记录被标记")
        
        self.results['qc_flags'] = flags
        return True

    def calculate_upwelling_index(self):
        """计算上升流指数"""
        if self.data is None:
            return None
        if 'wind_speed' in self.data.columns and 'lat' in self.data.columns:
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(self.data['lat']))
            rho_air = 1.225
            Cd = 0.0013
            tau = rho_air * Cd * self.data['wind_speed']**2
            self.data['upwelling_index'] = tau / (f + 1e-10)
            print("上升流指数计算完成")
            return self.data['upwelling_index'].values
        return None

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


def generate_report_helper(data, config):
    """
    generate_report 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'generate_report_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"generate_report_helper 处理完成")
    return result


def calculate_richardson_number_helper(data, config):
    """
    calculate_richardson_number 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_richardson_number_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_richardson_number_helper 处理完成")
    return result


def load_netcdf_data_helper(data, config):
    """
    load_netcdf_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'load_netcdf_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"load_netcdf_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 多源数据融合分析")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 多源Data融合AnalysisProcessor(config)
    
    # 步骤1: locate_thermal_anomalies
    processor.locate_thermal_anomalies()
    
    # 步骤2: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤3: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤4: quality_control
    processor.quality_control()
    
    # 步骤5: calculate_upwelling_index
    processor.calculate_upwelling_index()
    
    # 步骤6: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤7: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤8: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤9: interpolate_spatial_data
    processor.interpolate_spatial_data()
    
    # 步骤10: smooth_data
    processor.smooth_data()
    
    # 步骤11: remove_outliers
    processor.remove_outliers()
    
    # 步骤12: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 调用辅助函数: generate_report_helper
    generate_report_helper(processor.data, config)
    
    # 调用辅助函数: calculate_richardson_number_helper
    calculate_richardson_number_helper(processor.data, config)
    
    # 调用辅助函数: load_netcdf_data_helper
    load_netcdf_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
