#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋混合层深度计算
样本编号: normal_0267
生成时间: 2026-03-11 16:39:19
函数数量: 12
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋混合层深度计算Processor:
    """
    海洋混合层深度计算处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def interpolate_temporal_data(self, target_times):
        """时间序列插值"""
        if self.data is None or 'time' not in self.data.columns:
            return None
        from scipy.interpolate import interp1d
        self.data['time'] = pd.to_datetime(self.data['time'])
        time_numeric = (self.data['time'] - self.data['time'].min()).dt.total_seconds()
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            try:
                f = interp1d(time_numeric, self.data[col], kind='cubic', fill_value='extrapolate')
                result[col] = f(target_times)
            except:
                pass
        print(f"时间插值完成: {len(result)} 个变量")
        return result

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


def detect_ocean_fronts_helper(data, config):
    """
    detect_ocean_fronts 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_ocean_fronts_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_ocean_fronts_helper 处理完成")
    return result


def detect_internal_waves_helper(data, config):
    """
    detect_internal_waves 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_internal_waves_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_internal_waves_helper 处理完成")
    return result


def perform_eof_analysis_helper(data, config):
    """
    perform_eof_analysis 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'perform_eof_analysis_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"perform_eof_analysis_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋混合层深度计算")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋混合层深度计算Processor(config)
    
    # 步骤1: calculate_stratification
    processor.calculate_stratification()
    
    # 步骤2: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 步骤3: identify_eddies
    processor.identify_eddies()
    
    # 步骤4: find_convergence_zones
    processor.find_convergence_zones()
    
    # 步骤5: standardize_coordinates
    processor.standardize_coordinates()
    
    # 步骤6: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤7: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤8: assess_model_performance
    processor.assess_model_performance()
    
    # 步骤9: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 调用辅助函数: detect_ocean_fronts_helper
    detect_ocean_fronts_helper(processor.data, config)
    
    # 调用辅助函数: detect_internal_waves_helper
    detect_internal_waves_helper(processor.data, config)
    
    # 调用辅助函数: perform_eof_analysis_helper
    perform_eof_analysis_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
