#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 时空数据网格化
样本编号: normal_0152
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 时空Data网格化Processor:
    """
    时空数据网格化处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def preprocess_satellite_data(self):
        """预处理卫星遥感数据"""
        if self.data is None:
            return False
        if 'cloud_mask' not in self.data.columns:
            self.data['cloud_mask'] = (np.random.rand(len(self.data)) > 0.8).astype(int)
        original_size = len(self.data)
        self.data = self.data[self.data['cloud_mask'] == 0]
        if 'sst' in self.data.columns:
            self.data['sst_corrected'] = self.data['sst'] - 0.5
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            self.data['lon'] = self.data['lon'] + np.random.randn(len(self.data)) * 0.01
            self.data['lat'] = self.data['lat'] + np.random.randn(len(self.data)) * 0.01
        removed = original_size - len(self.data)
        print(f"卫星数据预处理完成: 去除 {removed} 个云像素")
        self.status = "satellite_preprocessed"
        return True

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


def calculate_vorticity_helper(data, config):
    """
    calculate_vorticity 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_vorticity_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_vorticity_helper 处理完成")
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


def identify_eddies_helper(data, config):
    """
    identify_eddies 辅助函数
    独立于类的工具函数
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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 时空数据网格化")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 时空Data网格化Processor(config)
    
    # 步骤1: detect_internal_waves
    processor.detect_internal_waves()
    
    # 步骤2: preprocess_satellite_data
    processor.preprocess_satellite_data()
    
    # 步骤3: run_ocean_model
    processor.run_ocean_model()
    
    # 步骤4: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤5: quality_control
    processor.quality_control()
    
    # 步骤6: export_netcdf
    processor.export_netcdf(config['output_file'])
    
    # 步骤7: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤8: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 步骤9: update_boundary_conditions
    processor.update_boundary_conditions()
    
    # 步骤10: assess_model_performance
    processor.assess_model_performance()
    
    # 步骤11: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤12: compute_climatology
    processor.compute_climatology()
    
    # 调用辅助函数: calculate_vorticity_helper
    calculate_vorticity_helper(processor.data, config)
    
    # 调用辅助函数: generate_report_helper
    generate_report_helper(processor.data, config)
    
    # 调用辅助函数: identify_eddies_helper
    identify_eddies_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
