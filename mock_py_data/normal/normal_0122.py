#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋涡旋检测追踪
样本编号: normal_0122
生成时间: 2026-03-11 16:39:19
函数数量: 9
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋涡旋检测追踪Processor:
    """
    海洋涡旋检测追踪处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def quantify_variability(self, variable, timescale='all'):
        """量化变异性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        variability = {'variance': float(np.var(values)), 'std': float(np.std(values)), 'cv': float(np.std(values) / (np.mean(values) + 1e-10)), 'range': float(np.max(values) - np.min(values)), 'iqr': float(np.percentile(values, 75) - np.percentile(values, 25))}
        if timescale != 'all' and 'time' in self.data.columns:
            self.data['time'] = pd.to_datetime(self.data['time'])
            if timescale == 'seasonal':
                self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
                seasonal_std = self.data.groupby('season')[variable].std()
                variability['seasonal_variability'] = seasonal_std.to_dict()
            elif timescale == 'monthly':
                self.data['month'] = self.data['time'].dt.month
                monthly_std = self.data.groupby('month')[variable].std()
                variability['monthly_variability'] = monthly_std.to_dict()
        self.results[f'{variable}_variability'] = variability
        print(f"{variable} 变异性: std={variability['std']:.3f}, CV={variability['cv']:.3f}")
        return variability

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


def quality_control_helper(data, config):
    """
    quality_control 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'quality_control_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"quality_control_helper 处理完成")
    return result


def identify_fishing_grounds_helper(data, config):
    """
    identify_fishing_grounds 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'identify_fishing_grounds_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"identify_fishing_grounds_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋涡旋检测追踪")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋涡旋检测追踪Processor(config)
    
    # 步骤1: quantify_variability
    processor.quantify_variability()
    
    # 步骤2: calculate_upwelling_index
    processor.calculate_upwelling_index()
    
    # 步骤3: calculate_trend
    processor.calculate_trend()
    
    # 步骤4: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤5: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤6: standardize_coordinates
    processor.standardize_coordinates()
    
    # 步骤7: detect_upwelling
    processor.detect_upwelling()
    
    # 调用辅助函数: quality_control_helper
    quality_control_helper(processor.data, config)
    
    # 调用辅助函数: identify_fishing_grounds_helper
    identify_fishing_grounds_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
