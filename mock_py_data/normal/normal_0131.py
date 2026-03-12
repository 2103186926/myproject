#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 卫星遥感数据预处理
样本编号: normal_0131
生成时间: 2026-03-11 16:39:19
函数数量: 11
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 卫星遥感Data预处理Processor:
    """
    卫星遥感数据预处理处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def find_convergence_zones(self):
        """查找海洋辐合区"""
        if self.data is None:
            return []
        convergence_zones = []
        if 'divergence' in self.data.columns:
            convergence_mask = self.data['divergence'] < -0.01
            convergence_indices = np.where(convergence_mask)[0]
            for idx in convergence_indices:
                convergence_zones.append({'index': int(idx), 'divergence': float(self.data['divergence'].iloc[idx]), 'strength': float(abs(self.data['divergence'].iloc[idx]))})
        self.results['convergence_zones'] = convergence_zones
        print(f"找到 {len(convergence_zones)} 个辐合区")
        return convergence_zones

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

    def forecast_ocean_state(self, forecast_hours=24):
        """预报未来海洋状态"""
        if self.data is None:
            return None
        print(f"生成 {forecast_hours} 小时预报")
        forecast = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            current_value = self.data[col].iloc[-1]
            trend = np.polyfit(np.arange(len(self.data)), self.data[col], 1)[0]
            forecast[col] = current_value + trend * forecast_hours
        self.results['forecast'] = forecast
        print("预报生成完成")
        return forecast

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

    def detect_spatial_anomalies(self, variable='temperature', threshold=2.0):
        """检测空间异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        window_size = 10
        anomalies = []
        for i in range(len(self.data) - window_size):
            window = self.data[variable].iloc[i:i+window_size]
            mean = window.mean()
            std = window.std()
            if std > 0:
                z_score = abs((self.data[variable].iloc[i+window_size//2] - mean) / std)
                if z_score > threshold:
                    anomalies.append({'index': i + window_size//2, 'value': self.data[variable].iloc[i+window_size//2], 'z_score': z_score})
        print(f"检测到 {len(anomalies)} 个空间异常点")
        self.results['spatial_anomalies'] = anomalies
        return anomalies


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


def generate_report_helper(data, config):
    """
    generate_report 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'generate_report_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"generate_report_helper 处理完成")
    return result


def grid_irregular_data_helper(data, config):
    """
    grid_irregular_data 辅助函数
    独立于类的工具函数
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
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 卫星遥感数据预处理")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 卫星遥感Data预处理Processor(config)
    
    # 步骤1: quality_control
    processor.quality_control()
    
    # 步骤2: find_convergence_zones
    processor.find_convergence_zones()
    
    # 步骤3: export_netcdf
    processor.export_netcdf(config['output_file'])
    
    # 步骤4: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤5: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤6: compute_climatology
    processor.compute_climatology()
    
    # 步骤7: calculate_trend
    processor.calculate_trend()
    
    # 步骤8: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 调用辅助函数: fill_missing_values_helper
    fill_missing_values_helper(processor.data, config)
    
    # 调用辅助函数: generate_report_helper
    generate_report_helper(processor.data, config)
    
    # 调用辅助函数: grid_irregular_data_helper
    grid_irregular_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
