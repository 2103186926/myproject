#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: CTD数据质量控制
样本编号: normal_0425
生成时间: 2026-03-11 16:39:19
函数数量: 15
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

    def calculate_anomaly(self, climatology):
        """计算相对于气候态的异常值"""
        if self.data is None or climatology is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data['month'] = self.data['time'].dt.month
        for col in climatology.keys():
            if col in self.data.columns:
                anomaly_col = f'{col}_anomaly'
                self.data[anomaly_col] = 0.0
                for month, clim_value in climatology[col].items():
                    mask = self.data['month'] == month
                    self.data.loc[mask, anomaly_col] = self.data.loc[mask, col] - clim_value
        print("异常值计算完成")
        return True

    def calculate_temperature_field(self):
        """计算三维温度场"""
        if self.data is None:
            return None
        if 'depth' in self.data.columns:
            surface_temp = 25.0
            decay_rate = 0.01
            self.data['temperature_field'] = surface_temp * np.exp(-decay_rate * self.data['depth'])
            if 'time' in self.data.columns:
                seasonal = 5 * np.sin(2 * np.pi * np.arange(len(self.data)) / 365)
                self.data['temperature_field'] += seasonal
            print("温度场计算完成")
            return self.data['temperature_field'].values
        return None

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

    def create_vector_plot(self, u_var='u_velocity', v_var='v_velocity', output_path='vector_plot.png'):
        """创建矢量场图"""
        if self.data is None:
            return False
        try:
            import matplotlib.pyplot as plt
            if u_var not in self.data.columns or v_var not in self.data.columns:
                return False
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            step = max(1, len(self.data) // 100)
            plt.figure(figsize=(12, 8))
            plt.quiver(self.data['lon'][::step], self.data['lat'][::step], self.data[u_var][::step], self.data[v_var][::step], scale=10, width=0.003)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title('Vector Field (Current/Wind)')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"矢量场图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"矢量场绘图失败: {e}")
        return False

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

    def update_boundary_conditions(self, boundary_data):
        """更新模式边界条件"""
        if self.data is None:
            return False
        boundary_indices = boundary_data.get('indices', [0, -1])
        for idx in boundary_indices:
            if 0 <= idx < len(self.data):
                for key, value in boundary_data.items():
                    if key != 'indices' and key in self.data.columns:
                        self.data.loc[idx, key] = value
        print(f"边界条件更新完成: {len(boundary_indices)} 个边界点")
        return True

    def predict_current(self, lead_time=24):
        """预测未来流场"""
        if self.data is None:
            return None
        predictions = {}
        for vel_component in ['u_velocity', 'v_velocity']:
            if vel_component in self.data.columns:
                values = self.data[vel_component].values
                lag1_corr = np.corrcoef(values[:-1], values[1:])[0, 1]
                predicted = values[-1] * (lag1_corr ** lead_time)
                predictions[vel_component] = float(predicted)
        self.results['predicted_current'] = predictions
        print(f"流场预测完成: {lead_time}h")
        return predictions

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


def apply_spatial_filter_helper(data, config):
    """
    apply_spatial_filter 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'apply_spatial_filter_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"apply_spatial_filter_helper 处理完成")
    return result


def calculate_upwelling_index_helper(data, config):
    """
    calculate_upwelling_index 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_upwelling_index_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_upwelling_index_helper 处理完成")
    return result


def calculate_thermocline_depth_helper(data, config):
    """
    calculate_thermocline_depth 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_thermocline_depth_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_thermocline_depth_helper 处理完成")
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
    
    # 步骤1: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤2: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤3: calculate_temperature_field
    processor.calculate_temperature_field()
    
    # 步骤4: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤5: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤6: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤7: generate_report
    processor.generate_report()
    
    # 步骤8: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤9: update_boundary_conditions
    processor.update_boundary_conditions()
    
    # 步骤10: predict_current
    processor.predict_current()
    
    # 步骤11: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤12: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 调用辅助函数: apply_spatial_filter_helper
    apply_spatial_filter_helper(processor.data, config)
    
    # 调用辅助函数: calculate_upwelling_index_helper
    calculate_upwelling_index_helper(processor.data, config)
    
    # 调用辅助函数: calculate_thermocline_depth_helper
    calculate_thermocline_depth_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
