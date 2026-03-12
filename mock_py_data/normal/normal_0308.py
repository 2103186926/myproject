#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋碳汇能力评估
样本编号: normal_0308
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋碳汇能力评估Processor:
    """
    海洋碳汇能力评估处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_stratification(self):
        """计算海洋层化强度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
            self.data['stratification'] = -drho_dz
            mean_strat = np.mean(np.abs(self.data['stratification']))
            self.results['mean_stratification'] = float(mean_strat)
            print(f"层化强度计算完成: {mean_strat:.6f}")
            return self.data['stratification'].values
        return None

    def calculate_salinity_field(self):
        """计算盐度场分布"""
        if self.data is None:
            return None
        base_salinity = 35.0
        if 'depth' in self.data.columns:
            self.data['salinity_field'] = base_salinity + 0.001 * self.data['depth']
            if 'lat' in self.data.columns:
                lat_effect = -0.1 * np.abs(self.data['lat'])
                self.data['salinity_field'] += lat_effect
            print("盐度场计算完成")
            return self.data['salinity_field'].values
        return None

    def parse_observation_data(self, file_path):
        """解析Argo浮标等观测数据"""
        try:
            n_profiles = 50
            n_levels = 20
            data_list = []
            for i in range(n_profiles):
                for j in range(n_levels):
                    data_list.append({
                        'profile_id': i,
                        'pressure': j * 50,
                        'temperature': 25 - j * 0.5 + np.random.randn() * 0.5,
                        'salinity': 35 + np.random.randn() * 0.3,
                        'lon': 120 + np.random.randn() * 5,
                        'lat': 30 + np.random.randn() * 3
                    })
            self.data = pd.DataFrame(data_list)
            self.status = "observation_parsed"
            print(f"观测数据解析完成: {n_profiles} 个剖面")
            return True
        except Exception as e:
            print(f"观测数据解析失败: {e}")
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


def validate_forecast_helper(data, config):
    """
    validate_forecast 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'validate_forecast_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"validate_forecast_helper 处理完成")
    return result


def find_convergence_zones_helper(data, config):
    """
    find_convergence_zones 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'find_convergence_zones_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"find_convergence_zones_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋碳汇能力评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋碳汇能力评估Processor(config)
    
    # 步骤1: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤2: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤3: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤4: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤5: predict_current
    processor.predict_current()
    
    # 步骤6: calculate_trend
    processor.calculate_trend()
    
    # 步骤7: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤8: track_eddy_trajectory
    processor.track_eddy_trajectory()
    
    # 步骤9: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤10: calculate_salinity_field
    processor.calculate_salinity_field()
    
    # 步骤11: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤12: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 调用辅助函数: calculate_thermocline_depth_helper
    calculate_thermocline_depth_helper(processor.data, config)
    
    # 调用辅助函数: validate_forecast_helper
    validate_forecast_helper(processor.data, config)
    
    # 调用辅助函数: find_convergence_zones_helper
    find_convergence_zones_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
