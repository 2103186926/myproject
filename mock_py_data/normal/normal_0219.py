#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: CTD数据质量控制
样本编号: normal_0219
生成时间: 2026-03-11 16:39:19
函数数量: 13
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class CTDData质量控制Processor:
    """
    CTD数据质量控制处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def predict_salinity(self, lead_time=24):
        """预测未来盐度"""
        if self.data is None or 'salinity' not in self.data.columns:
            return None
        window = min(10, len(self.data))
        recent_mean = self.data['salinity'].iloc[-window:].mean()
        recent_trend = self.data['salinity'].iloc[-window:].diff().mean()
        predicted_salinity = recent_mean + recent_trend * lead_time
        self.results['predicted_salinity'] = float(predicted_salinity)
        print(f"预测 {lead_time}h 后盐度: {predicted_salinity:.2f} PSU")
        return predicted_salinity

    def calculate_vorticity(self):
        """计算相对涡度"""
        if self.data is None:
            return None
        if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
            du_dy = np.gradient(self.data['u_velocity'])
            dv_dx = np.gradient(self.data['v_velocity'])
            self.data['vorticity'] = dv_dx - du_dy
            print("涡度计算完成")
            return self.data['vorticity'].values
        return None

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

    def simulate_wave_propagation(self, duration=3600):
        """模拟波浪传播"""
        if self.data is None:
            return False
        wave_speed = 10
        timesteps = duration // 60
        if 'wave_height' not in self.data.columns:
            self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
        for t in range(timesteps):
            self.data['wave_height'] *= 0.99
            self.data['wave_height'] += np.random.randn(len(self.data)) * 0.1
            self.data['wave_height'] = np.maximum(self.data['wave_height'], 0)
        print(f"波浪传播模拟完成: {duration}s")
        return True

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


def calculate_salinity_field_helper(data, config):
    """
    calculate_salinity_field 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_salinity_field_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_salinity_field_helper 处理完成")
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


def preprocess_satellite_data_helper(data, config):
    """
    preprocess_satellite_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'preprocess_satellite_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"preprocess_satellite_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
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
    
    # 创建处理器实例
    processor = CTDData质量控制Processor(config)
    
    # 步骤1: predict_salinity
    processor.predict_salinity()
    
    # 步骤2: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤3: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤4: export_geotiff
    processor.export_geotiff(config['output_file'])
    
    # 步骤5: detect_internal_waves
    processor.detect_internal_waves()
    
    # 步骤6: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤7: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤8: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤9: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤10: export_netcdf
    processor.export_netcdf(config['output_file'])
    
    # 调用辅助函数: calculate_salinity_field_helper
    calculate_salinity_field_helper(processor.data, config)
    
    # 调用辅助函数: fill_missing_values_helper
    fill_missing_values_helper(processor.data, config)
    
    # 调用辅助函数: preprocess_satellite_data_helper
    preprocess_satellite_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
