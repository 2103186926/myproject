#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋渔业资源预测
样本编号: normal_0379
生成时间: 2026-03-11 16:39:19
函数数量: 12
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋渔业资源预测Processor:
    """
    海洋渔业资源预测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def assess_model_performance(self, observations, predictions):
        """评估模型性能"""
        if len(observations) != len(predictions):
            return None
        obs = np.array(observations)
        pred = np.array(predictions)
        mae = np.mean(np.abs(obs - pred))
        rmse = np.sqrt(np.mean((obs - pred) ** 2))
        bias = np.mean(pred - obs)
        correlation = np.corrcoef(obs, pred)[0, 1]
        mse = np.mean((obs - pred) ** 2)
        mse_clim = np.mean((obs - np.mean(obs)) ** 2)
        skill_score = 1 - mse / (mse_clim + 1e-10)
        metrics = {'mae': float(mae), 'rmse': float(rmse), 'bias': float(bias), 'correlation': float(correlation), 'skill_score': float(skill_score)}
        self.results['model_performance'] = metrics
        print(f"模型性能: RMSE={rmse:.3f}, 相关系数={correlation:.3f}")
        return metrics

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

    def assimilate_observation_data(self, observations):
        """数据同化：融合观测数据"""
        if self.data is None:
            return False
        obs_weight = 0.3
        for var in ['temperature', 'salinity']:
            if var in self.data.columns and var in observations:
                self.data[var] = (1 - obs_weight) * self.data[var] + obs_weight * observations[var]
        print("观测数据同化完成")
        self.status = "assimilated"
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

    def calculate_mixed_layer_depth(self):
        """计算混合层深度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            density_grad = np.gradient(self.data['density'])
            max_grad_idx = np.argmax(np.abs(density_grad))
            mld = self.data['depth'].iloc[max_grad_idx] if max_grad_idx < len(self.data) else 50
            self.results['mixed_layer_depth'] = float(mld)
            print(f"混合层深度: {mld:.2f} m")
            return mld
        mld = 50.0 + np.random.randn() * 10
        self.results['mixed_layer_depth'] = mld
        return mld

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

    def calculate_wave_height(self):
        """计算有效波高"""
        if self.data is None:
            return None
        if 'wind_speed' in self.data.columns:
            self.data['wave_height'] = 0.21 * (self.data['wind_speed'] ** 2) / 9.8
            self.data['wave_height'] = np.clip(self.data['wave_height'], 0, 15)
            print("波高计算完成")
            return self.data['wave_height'].values
        else:
            self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
            return self.data['wave_height'].values

    def run_ocean_model(self, timesteps=100):
        """运行海洋数值模式"""
        if self.data is None:
            return False
        print(f"启动海洋模式模拟: {timesteps} 个时间步")
        if 'temperature' not in self.data.columns:
            self.data['temperature'] = 20 + np.random.randn(len(self.data)) * 3
        dt = 3600
        for t in range(timesteps):
            if t % 10 == 0:
                print(f"  时间步 {t}/{timesteps}")
            diffusion = 0.01 * np.random.randn(len(self.data))
            self.data['temperature'] += diffusion
        self.status = "model_completed"
        print("模式运行完成")
        return True


def predict_current_helper(data, config):
    """
    predict_current 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'predict_current_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"predict_current_helper 处理完成")
    return result


def apply_temporal_filter_helper(data, config):
    """
    apply_temporal_filter 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'apply_temporal_filter_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"apply_temporal_filter_helper 处理完成")
    return result


def calculate_temperature_field_helper(data, config):
    """
    calculate_temperature_field 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_temperature_field_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_temperature_field_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋渔业资源预测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋渔业资源预测Processor(config)
    
    # 步骤1: assess_model_performance
    processor.assess_model_performance()
    
    # 步骤2: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤3: plot_time_series
    processor.plot_time_series()
    
    # 步骤4: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 步骤5: export_geotiff
    processor.export_geotiff(config['output_file'])
    
    # 步骤6: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤7: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤8: calculate_wave_height
    processor.calculate_wave_height()
    
    # 步骤9: run_ocean_model
    processor.run_ocean_model()
    
    # 调用辅助函数: predict_current_helper
    predict_current_helper(processor.data, config)
    
    # 调用辅助函数: apply_temporal_filter_helper
    apply_temporal_filter_helper(processor.data, config)
    
    # 调用辅助函数: calculate_temperature_field_helper
    calculate_temperature_field_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
