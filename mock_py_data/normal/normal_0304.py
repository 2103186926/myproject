#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋生态动力学模拟
样本编号: normal_0304
生成时间: 2026-03-11 16:39:19
函数数量: 5
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋生态动力学模拟Processor:
    """
    海洋生态动力学模拟处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def predict_temperature(self, lead_time=24):
        """预测未来温度"""
        if self.data is None or 'temperature' not in self.data.columns:
            return None
        from sklearn.linear_model import LinearRegression
        X = np.arange(len(self.data)).reshape(-1, 1)
        y = self.data['temperature'].values
        model = LinearRegression()
        model.fit(X, y)
        future_X = np.array([[len(self.data) + lead_time]])
        predicted_temp = model.predict(future_X)[0]
        self.results['predicted_temperature'] = float(predicted_temp)
        print(f"预测 {lead_time}h 后温度: {predicted_temp:.2f}°C")
        return predicted_temp

    def apply_spatial_filter(self, filter_size=3):
        """应用空间滤波器"""
        if self.data is None:
            return False
        from scipy.ndimage import uniform_filter
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat', 'lon_bin', 'lat_bin']:
                values = self.data[col].values.reshape(-1, 1)
                if len(values) > filter_size:
                    filtered = uniform_filter(values, size=filter_size, mode='nearest')
                    self.data[col] = filtered.flatten()
        print(f"空间滤波完成: 滤波器大小 {filter_size}")
        return True

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


def calculate_statistics_helper(data, config):
    """
    calculate_statistics 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_statistics_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_statistics_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋生态动力学模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋生态动力学模拟Processor(config)
    
    # 步骤1: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤2: predict_temperature
    processor.predict_temperature()
    
    # 步骤3: apply_spatial_filter
    processor.apply_spatial_filter()
    
    # 步骤4: quality_control
    processor.quality_control()
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
