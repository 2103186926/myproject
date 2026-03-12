#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋能源评估
样本编号: normal_0399
生成时间: 2026-03-11 16:39:19
函数数量: 13
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋能源评估Processor:
    """
    海洋能源评估处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def load_hdf5_data(self, file_path):
        """加载HDF5格式的卫星遥感数据"""
        try:
            import h5py
            with h5py.File(file_path, 'r') as f:
                data_dict = {}
                for key in list(f.keys())[:10]:
                    data_dict[key] = np.array(f[key]).flatten()[:1000]
            self.data = pd.DataFrame(data_dict)
            self.status = "hdf5_loaded"
            print(f"HDF5数据加载完成: {len(data_dict)} 个数据集")
            return True
        except Exception as e:
            print(f"HDF5加载失败: {e}")
            self.data = pd.DataFrame({
                'sst': np.random.randn(1000) * 3 + 20,
                'chlorophyll': np.random.rand(1000) * 10,
                'wind_speed': np.random.rand(1000) * 20
            })
            return True

    def plot_time_series(self, variables, output_path='timeseries.png'):
        """绘制时间序列"""
        if self.data is None:
            return False
        try:
            import matplotlib.pyplot as plt
            if 'time' not in self.data.columns:
                x = np.arange(len(self.data))
            else:
                x = pd.to_datetime(self.data['time'])
            plt.figure(figsize=(14, 6))
            for var in variables:
                if var in self.data.columns:
                    plt.plot(x, self.data[var], label=var, linewidth=2)
            plt.xlabel('Time')
            plt.ylabel('Value')
            plt.title('Time Series')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"时间序列图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"绘图失败: {e}")
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


def detect_upwelling_helper(data, config):
    """
    detect_upwelling 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_upwelling_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_upwelling_helper 处理完成")
    return result


def interpolate_spatial_data_helper(data, config):
    """
    interpolate_spatial_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'interpolate_spatial_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"interpolate_spatial_data_helper 处理完成")
    return result


def update_boundary_conditions_helper(data, config):
    """
    update_boundary_conditions 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'update_boundary_conditions_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"update_boundary_conditions_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋能源评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋能源评估Processor(config)
    
    # 步骤1: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤2: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤3: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤4: load_hdf5_data
    processor.load_hdf5_data()
    
    # 步骤5: plot_time_series
    processor.plot_time_series()
    
    # 步骤6: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤7: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤8: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤9: quality_control
    processor.quality_control()
    
    # 步骤10: load_netcdf_data
    processor.load_netcdf_data()
    
    # 调用辅助函数: detect_upwelling_helper
    detect_upwelling_helper(processor.data, config)
    
    # 调用辅助函数: interpolate_spatial_data_helper
    interpolate_spatial_data_helper(processor.data, config)
    
    # 调用辅助函数: update_boundary_conditions_helper
    update_boundary_conditions_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
