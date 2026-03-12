#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据异常值检测
样本编号: normal_0116
生成时间: 2026-03-11 16:39:19
函数数量: 13
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋Data异常值检测Processor:
    """
    海洋数据异常值检测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def estimate_uncertainty(self, variable, method='bootstrap', n_samples=100):
        """估计不确定性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        if method == 'bootstrap':
            bootstrap_means = []
            for _ in range(n_samples):
                sample = np.random.choice(values, size=len(values), replace=True)
                bootstrap_means.append(np.mean(sample))
            uncertainty = {'mean': float(np.mean(bootstrap_means)), 'std': float(np.std(bootstrap_means)), 'ci_lower': float(np.percentile(bootstrap_means, 2.5)), 'ci_upper': float(np.percentile(bootstrap_means, 97.5))}
        elif method == 'std':
            mean = np.mean(values)
            std = np.std(values)
            se = std / np.sqrt(len(values))
            uncertainty = {'mean': float(mean), 'std': float(std), 'standard_error': float(se), 'ci_lower': float(mean - 1.96 * se), 'ci_upper': float(mean + 1.96 * se)}
        self.results[f'{variable}_uncertainty'] = uncertainty
        print(f"{variable} 不确定性估计完成: {uncertainty['std']:.3f}")
        return uncertainty

    def calculate_mixed_layer_depth(self):
        """计算混合层深度"""
        if self.data is None:
            return None
        if 'density' in self.data.columns and 'depth' in self.data.columns:
            density_grad = np.gradient(self.data['density'])
            max_grad_idx = np.argmax(np.abs(density_grad))
            mld = self.data['depth'].iloc[max_grad_idx] if max_grad_idx < len(self.data) else 50
            self.results['mixed_layer_depth'] = float(mld)
            print(f"混合层深度: {mld:.2f} m")
            return mld
        mld = 50.0 + np.random.randn() * 10
        self.results['mixed_layer_depth'] = mld
        return mld

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


def update_boundary_conditions_helper(data, config):
    """
    update_boundary_conditions 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'update_boundary_conditions_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"update_boundary_conditions_helper 处理完成")
    return result


def forecast_ocean_state_helper(data, config):
    """
    forecast_ocean_state 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'forecast_ocean_state_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"forecast_ocean_state_helper 处理完成")
    return result


def interpolate_spatial_data_helper(data, config):
    """
    interpolate_spatial_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'interpolate_spatial_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"interpolate_spatial_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据异常值检测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋Data异常值检测Processor(config)
    
    # 步骤1: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤2: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤3: estimate_uncertainty
    processor.estimate_uncertainty()
    
    # 步骤4: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤5: identify_eddies
    processor.identify_eddies()
    
    # 步骤6: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 步骤7: detect_internal_waves
    processor.detect_internal_waves()
    
    # 步骤8: predict_salinity
    processor.predict_salinity()
    
    # 步骤9: detect_temporal_anomalies
    processor.detect_temporal_anomalies()
    
    # 步骤10: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 调用辅助函数: update_boundary_conditions_helper
    update_boundary_conditions_helper(processor.data, config)
    
    # 调用辅助函数: forecast_ocean_state_helper
    forecast_ocean_state_helper(processor.data, config)
    
    # 调用辅助函数: interpolate_spatial_data_helper
    interpolate_spatial_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
