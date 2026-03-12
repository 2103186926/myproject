#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海气耦合模式计算
样本编号: normal_0082
生成时间: 2026-03-11 16:39:19
函数数量: 10
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海气耦合模式计算Processor:
    """
    海气耦合模式计算处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_geostrophic_current(self):
        """计算地转流"""
        if self.data is None:
            return None
        if 'sea_surface_height' in self.data.columns and 'lat' in self.data.columns:
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(self.data['lat']))
            g = 9.8
            ssh_grad = np.gradient(self.data['sea_surface_height'])
            self.data['geostrophic_velocity'] = (g / (f + 1e-10)) * ssh_grad
            print("地转流计算完成")
            return self.data['geostrophic_velocity'].values
        return None

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

    def track_eddy_trajectory(self, eddy_id):
        """追踪涡旋运动轨迹"""
        if self.data is None:
            return []
        trajectory = []
        if 'time' in self.data.columns and 'lon' in self.data.columns:
            for i in range(0, len(self.data), 10):
                trajectory.append({
                    'time': str(self.data['time'].iloc[i]) if i < len(self.data) else None,
                    'lon': float(self.data['lon'].iloc[i]) if i < len(self.data) else 0,
                    'lat': float(self.data['lat'].iloc[i]) if i < len(self.data) else 0,
                    'intensity': float(np.random.rand())
                })
        self.results[f'eddy_{eddy_id}_trajectory'] = trajectory
        print(f"涡旋 {eddy_id} 轨迹追踪完成: {len(trajectory)} 个时间点")
        return trajectory

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


def calculate_spatial_gradient_helper(data, config):
    """
    calculate_spatial_gradient 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_spatial_gradient_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_spatial_gradient_helper 处理完成")
    return result


def normalize_data_helper(data, config):
    """
    normalize_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'normalize_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"normalize_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海气耦合模式计算")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海气耦合模式计算Processor(config)
    
    # 步骤1: compute_climatology
    processor.compute_climatology()
    
    # 步骤2: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 步骤3: detect_internal_waves
    processor.detect_internal_waves()
    
    # 步骤4: plot_time_series
    processor.plot_time_series()
    
    # 步骤5: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤6: track_eddy_trajectory
    processor.track_eddy_trajectory()
    
    # 步骤7: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤8: assess_model_performance
    processor.assess_model_performance()
    
    # 调用辅助函数: calculate_spatial_gradient_helper
    calculate_spatial_gradient_helper(processor.data, config)
    
    # 调用辅助函数: normalize_data_helper
    normalize_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
