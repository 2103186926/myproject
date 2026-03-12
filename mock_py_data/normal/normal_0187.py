#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋热浪预警
样本编号: normal_0187
生成时间: 2026-03-11 16:39:19
函数数量: 8
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋热浪预警Processor:
    """
    海洋热浪预警处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_buoyancy_frequency(self):
        """计算浮力频率"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            g = 9.8
            rho0 = 1025
            drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
            N2 = -(g / rho0) * drho_dz
            N2 = np.maximum(N2, 0)
            self.data['buoyancy_frequency'] = np.sqrt(N2)
            print("浮力频率计算完成")
            return self.data['buoyancy_frequency'].values
        return None

    def calculate_richardson_number(self):
        """计算Richardson数"""
        if self.data is None:
            return None
        if 'buoyancy_frequency' in self.data.columns and 'u_velocity' in self.data.columns:
            du_dz = np.gradient(self.data['u_velocity'])
            Ri = (self.data['buoyancy_frequency']**2) / ((du_dz**2) + 1e-10)
            self.data['richardson_number'] = Ri
            unstable_ratio = np.sum(Ri < 0.25) / len(Ri)
            self.results['unstable_ratio'] = float(unstable_ratio)
            print(f"Richardson数计算完成, 不稳定区域占比: {unstable_ratio:.2%}")
            return self.data['richardson_number'].values
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

    def visualize_spatial_field(self, variable, output_path='spatial_field.png'):
        """可视化空间场"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            import matplotlib.pyplot as plt
            if 'lon' in self.data.columns and 'lat' in self.data.columns:
                plt.figure(figsize=(12, 8))
                scatter = plt.scatter(self.data['lon'], self.data['lat'], c=self.data[variable], cmap='viridis', s=50)
                plt.colorbar(scatter, label=variable)
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.title(f'{variable} Spatial Distribution')
                plt.grid(True, alpha=0.3)
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"空间场可视化已保存: {output_path}")
                return True
        except Exception as e:
            print(f"可视化失败: {e}")
        return False

    def identify_eddies(self):
        """识别中尺度涡旋"""
        if self.data is None:
            return []
        eddies = []
        if 'vorticity' in self.data.columns:
            vorticity = self.data['vorticity'].values
            threshold = np.std(vorticity) * 2
            cyclonic = np.where(vorticity > threshold)[0]
            anticyclonic = np.where(vorticity < -threshold)[0]
            for idx in cyclonic:
                eddies.append({'index': int(idx), 'type': 'cyclonic', 'vorticity': float(vorticity[idx])})
            for idx in anticyclonic:
                eddies.append({'index': int(idx), 'type': 'anticyclonic', 'vorticity': float(vorticity[idx])})
        self.results['eddies'] = eddies
        print(f"识别到 {len(eddies)} 个涡旋")
        return eddies


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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋热浪预警")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋热浪预警Processor(config)
    
    # 步骤1: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤2: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤3: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 步骤4: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤5: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤6: identify_eddies
    processor.identify_eddies()
    
    # 调用辅助函数: detect_upwelling_helper
    detect_upwelling_helper(processor.data, config)
    
    # 调用辅助函数: predict_current_helper
    predict_current_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
