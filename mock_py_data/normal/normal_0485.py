#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 潮汐潮流预报
样本编号: normal_0485
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 潮汐潮流预报Processor:
    """
    潮汐潮流预报处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def identify_water_masses(self):
        """识别不同水团"""
        if self.data is None:
            return None
        from sklearn.cluster import KMeans
        if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
            features = self.data[['temperature', 'salinity']].values
            n_clusters = 3
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(features)
            self.data['water_mass_id'] = labels
            water_masses = []
            for i in range(n_clusters):
                mask = labels == i
                water_masses.append({'id': int(i), 'count': int(np.sum(mask)), 'mean_temp': float(self.data.loc[mask, 'temperature'].mean()), 'mean_sal': float(self.data.loc[mask, 'salinity'].mean())})
            self.results['water_masses'] = water_masses
            print(f"识别到 {n_clusters} 个水团")
            return water_masses
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

    def detect_temporal_anomalies(self, variable='temperature', method='iqr'):
        """检测时间序列异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        anomalies = []
        if method == 'iqr':
            q1 = self.data[variable].quantile(0.25)
            q3 = self.data[variable].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            mask = (self.data[variable] < lower) | (self.data[variable] > upper)
            anomaly_indices = np.where(mask)[0]
            for idx in anomaly_indices:
                anomalies.append({'index': int(idx), 'value': float(self.data[variable].iloc[idx]), 'lower_bound': float(lower), 'upper_bound': float(upper)})
        print(f"检测到 {len(anomalies)} 个时间异常点")
        self.results['temporal_anomalies'] = anomalies
        return anomalies

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

    def locate_thermal_anomalies(self, threshold=2.0):
        """定位温度异常区域"""
        if self.data is None or 'temperature' not in self.data.columns:
            return []
        temp_mean = self.data['temperature'].mean()
        temp_std = self.data['temperature'].std()
        anomalies = []
        for i in range(len(self.data)):
            z_score = abs((self.data['temperature'].iloc[i] - temp_mean) / temp_std)
            if z_score > threshold:
                anomalies.append({'index': int(i), 'temperature': float(self.data['temperature'].iloc[i]), 'anomaly_score': float(z_score), 'type': 'warm' if self.data['temperature'].iloc[i] > temp_mean else 'cold'})
        self.results['thermal_anomalies'] = anomalies
        print(f"定位到 {len(anomalies)} 个温度异常区域")
        return anomalies

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


def classify_ocean_regimes_helper(data, config):
    """
    classify_ocean_regimes 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'classify_ocean_regimes_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"classify_ocean_regimes_helper 处理完成")
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


def export_netcdf_helper(data, config):
    """
    export_netcdf 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'export_netcdf_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"export_netcdf_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 潮汐潮流预报")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 潮汐潮流预报Processor(config)
    
    # 步骤1: calculate_salinity_field
    processor.calculate_salinity_field()
    
    # 步骤2: plot_time_series
    processor.plot_time_series()
    
    # 步骤3: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤4: calculate_trend
    processor.calculate_trend()
    
    # 步骤5: predict_salinity
    processor.predict_salinity()
    
    # 步骤6: detect_temporal_anomalies
    processor.detect_temporal_anomalies()
    
    # 步骤7: quantify_variability
    processor.quantify_variability()
    
    # 步骤8: locate_thermal_anomalies
    processor.locate_thermal_anomalies()
    
    # 步骤9: simulate_wave_propagation
    processor.simulate_wave_propagation()
    
    # 步骤10: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 步骤11: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤12: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 调用辅助函数: classify_ocean_regimes_helper
    classify_ocean_regimes_helper(processor.data, config)
    
    # 调用辅助函数: identify_fishing_grounds_helper
    identify_fishing_grounds_helper(processor.data, config)
    
    # 调用辅助函数: export_netcdf_helper
    export_netcdf_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
