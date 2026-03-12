#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 渔场环境预报
样本编号: normal_0495
生成时间: 2026-03-11 16:39:19
函数数量: 4
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 渔场环境预报Processor:
    """
    渔场环境预报处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def identify_fishing_grounds(self):
        """识别潜在渔场"""
        if self.data is None:
            return []
        fishing_grounds = []
        conditions = []
        if 'temperature' in self.data.columns:
            temp_suitable = (self.data['temperature'] > 15) & (self.data['temperature'] < 25)
            conditions.append(temp_suitable)
        if 'chlorophyll' in self.data.columns:
            chl_high = self.data['chlorophyll'] > 2.0
            conditions.append(chl_high)
        if len(conditions) > 0:
            fishing_mask = conditions[0]
            for cond in conditions[1:]:
                fishing_mask &= cond
            fishing_indices = np.where(fishing_mask)[0]
            for idx in fishing_indices:
                fishing_grounds.append({'index': int(idx), 'lon': float(self.data['lon'].iloc[idx]) if 'lon' in self.data.columns else 0, 'lat': float(self.data['lat'].iloc[idx]) if 'lat' in self.data.columns else 0})
        self.results['fishing_grounds'] = fishing_grounds
        print(f"识别到 {len(fishing_grounds)} 个潜在渔场")
        return fishing_grounds


def apply_temporal_filter_helper(data, config):
    """
    apply_temporal_filter 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'apply_temporal_filter_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"apply_temporal_filter_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 渔场环境预报")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 渔场环境预报Processor(config)
    
    # 步骤1: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤2: calculate_trend
    processor.calculate_trend()
    
    # 步骤3: identify_fishing_grounds
    processor.identify_fishing_grounds()
    
    # 调用辅助函数: apply_temporal_filter_helper
    apply_temporal_filter_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
