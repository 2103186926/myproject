#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据异常值检测
样本编号: normal_0285
生成时间: 2026-03-11 16:39:19
函数数量: 15
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
    
    def calculate_stratification(self):
        """计算海洋层化强度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
            self.data['stratification'] = -drho_dz
            mean_strat = np.mean(np.abs(self.data['stratification']))
            self.results['mean_stratification'] = float(mean_strat)
            print(f"层化强度计算完成: {mean_strat:.6f}")
            return self.data['stratification'].values
        return None

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

    def estimate_uncertainty(self, variable, method='bootstrap', n_samples=100):
        """估计不确定性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        if method == 'bootstrap':
            bootstrap_means = []
            for _ in range(n_samples):
                sample = np.random.choice(values, size=len(values), replace=True)
                bootstrap_means.append(np.mean(sample))
            uncertainty = {'mean': float(np.mean(bootstrap_means)), 'std': float(np.std(bootstrap_means)), 'ci_lower': float(np.percentile(bootstrap_means, 2.5)), 'ci_upper': float(np.percentile(bootstrap_means, 97.5))}
        elif method == 'std':
            mean = np.mean(values)
            std = np.std(values)
            se = std / np.sqrt(len(values))
            uncertainty = {'mean': float(mean), 'std': float(std), 'standard_error': float(se), 'ci_lower': float(mean - 1.96 * se), 'ci_upper': float(mean + 1.96 * se)}
        self.results[f'{variable}_uncertainty'] = uncertainty
        print(f"{variable} 不确定性估计完成: {uncertainty['std']:.3f}")
        return uncertainty

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

    def calculate_divergence(self):
        """计算水平散度"""
        if self.data is None:
            return None
        if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
            du_dx = np.gradient(self.data['u_velocity'])
            dv_dy = np.gradient(self.data['v_velocity'])
            self.data['divergence'] = du_dx + dv_dy
            print("散度计算完成")
            return self.data['divergence'].values
        return None

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

    def compute_correlation(self, var1, var2):
        """计算两个变量的相关性"""
        if self.data is None or var1 not in self.data.columns or var2 not in self.data.columns:
            return None
        correlation = self.data[var1].corr(self.data[var2])
        n = len(self.data)
        t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2 + 1e-10))
        result = {'correlation': float(correlation), 't_statistic': float(t_stat), 'sample_size': int(n)}
        self.results[f'correlation_{var1}_{var2}'] = result
        print(f"{var1} 与 {var2} 相关系数: {correlation:.3f}")
        return result

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


def simulate_pollutant_dispersion_helper(data, config):
    """
    simulate_pollutant_dispersion 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'simulate_pollutant_dispersion_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"simulate_pollutant_dispersion_helper 处理完成")
    return result


def fill_missing_values_helper(data, config):
    """
    fill_missing_values 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'fill_missing_values_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"fill_missing_values_helper 处理完成")
    return result


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
    
    # 步骤1: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤2: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤3: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤4: predict_temperature
    processor.predict_temperature()
    
    # 步骤5: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤6: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤7: estimate_uncertainty
    processor.estimate_uncertainty()
    
    # 步骤8: normalize_data
    processor.normalize_data()
    
    # 步骤9: calculate_divergence
    processor.calculate_divergence()
    
    # 步骤10: standardize_coordinates
    processor.standardize_coordinates()
    
    # 步骤11: compute_correlation
    processor.compute_correlation()
    
    # 步骤12: detect_internal_waves
    processor.detect_internal_waves()
    
    # 调用辅助函数: simulate_pollutant_dispersion_helper
    simulate_pollutant_dispersion_helper(processor.data, config)
    
    # 调用辅助函数: fill_missing_values_helper
    fill_missing_values_helper(processor.data, config)
    
    # 调用辅助函数: calculate_geostrophic_current_helper
    calculate_geostrophic_current_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
