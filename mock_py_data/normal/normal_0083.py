#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋牧场选址分析
样本编号: normal_0083
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋牧场选址AnalysisProcessor:
    """
    海洋牧场选址分析处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def segment_ocean_regions(self, n_regions=5):
        """分割海洋区域"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        from sklearn.cluster import DBSCAN
        coords = self.data[['lon', 'lat']].values
        clustering = DBSCAN(eps=5, min_samples=10)
        labels = clustering.fit_predict(coords)
        self.data['region_id'] = labels
        unique_labels = set(labels)
        regions = []
        for label in unique_labels:
            if label != -1:
                mask = labels == label
                regions.append({'region_id': int(label), 'size': int(np.sum(mask)), 'center_lon': float(self.data.loc[mask, 'lon'].mean()), 'center_lat': float(self.data.loc[mask, 'lat'].mean())})
        self.results['ocean_regions'] = regions
        print(f"海洋区域分割完成: {len(regions)} 个区域")
        return regions

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


def predict_temperature_helper(data, config):
    """
    predict_temperature 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'predict_temperature_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"predict_temperature_helper 处理完成")
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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋牧场选址分析")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋牧场选址AnalysisProcessor(config)
    
    # 步骤1: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 步骤2: predict_salinity
    processor.predict_salinity()
    
    # 步骤3: calculate_trend
    processor.calculate_trend()
    
    # 步骤4: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤5: load_netcdf_data
    processor.load_netcdf_data()
    
    # 步骤6: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 步骤7: initialize_model_state
    processor.initialize_model_state()
    
    # 步骤8: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤9: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤10: find_convergence_zones
    processor.find_convergence_zones()
    
    # 步骤11: calculate_anomaly
    processor.calculate_anomaly()
    
    # 步骤12: predict_current
    processor.predict_current()
    
    # 调用辅助函数: predict_temperature_helper
    predict_temperature_helper(processor.data, config)
    
    # 调用辅助函数: identify_eddies_helper
    identify_eddies_helper(processor.data, config)
    
    # 调用辅助函数: calculate_upwelling_index_helper
    calculate_upwelling_index_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
