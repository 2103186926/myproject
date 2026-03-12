#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋湍流模拟
样本编号: normal_0014
生成时间: 2026-03-11 16:39:19
函数数量: 15
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋湍流模拟Processor:
    """
    海洋湍流模拟处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def update_boundary_conditions(self, boundary_data):
        """更新模式边界条件"""
        if self.data is None:
            return False
        boundary_indices = boundary_data.get('indices', [0, -1])
        for idx in boundary_indices:
            if 0 <= idx < len(self.data):
                for key, value in boundary_data.items():
                    if key != 'indices' and key in self.data.columns:
                        self.data.loc[idx, key] = value
        print(f"边界条件更新完成: {len(boundary_indices)} 个边界点")
        return True

    def calculate_ekman_transport(self):
        """计算Ekman输运"""
        if self.data is None:
            return None
        if 'wind_speed' in self.data.columns and 'lat' in self.data.columns:
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(self.data['lat']))
            rho_air = 1.225
            Cd = 0.0013
            tau = rho_air * Cd * self.data['wind_speed']**2
            rho_water = 1025
            self.data['ekman_transport'] = tau / (rho_water * (f + 1e-10))
            print("Ekman输运计算完成")
            return self.data['ekman_transport'].values
        return None

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

    def interpolate_spatial_data(self, target_grid):
        """空间数据插值到目标网格"""
        if self.data is None or 'lon' not in self.data.columns:
            return None
        from scipy.interpolate import griddata
        points = self.data[['lon', 'lat']].values
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col not in ['lon', 'lat']:
                values = self.data[col].values
                grid_values = griddata(points, values, target_grid, method='linear')
                result[col] = grid_values
        print(f"空间插值完成: {len(result)} 个变量")
        self.results['interpolated_grid'] = result
        return result

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

    def apply_temporal_filter(self, window='7D'):
        """应用时间滤波器"""
        if self.data is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.rolling(window, center=True).mean()
        self.data = self.data.reset_index()
        print(f"时间滤波完成: 窗口 {window}")
        return True

    def estimate_uncertainty(self, variable, method='bootstrap', n_samples=100):
        """估计不确定性"""
        if self.data is None or variable not in self.data.columns:
            return None
        values = self.data[variable].values
        if method == 'bootstrap':
            bootstrap_means = []
            for _ in range(n_samples):
                sample = np.random.choice(values, size=len(values), replace=True)
                bootstrap_means.append(np.mean(sample))
            uncertainty = {'mean': float(np.mean(bootstrap_means)), 'std': float(np.std(bootstrap_means)), 'ci_lower': float(np.percentile(bootstrap_means, 2.5)), 'ci_upper': float(np.percentile(bootstrap_means, 97.5))}
        elif method == 'std':
            mean = np.mean(values)
            std = np.std(values)
            se = std / np.sqrt(len(values))
            uncertainty = {'mean': float(mean), 'std': float(std), 'standard_error': float(se), 'ci_lower': float(mean - 1.96 * se), 'ci_upper': float(mean + 1.96 * se)}
        self.results[f'{variable}_uncertainty'] = uncertainty
        print(f"{variable} 不确定性估计完成: {uncertainty['std']:.3f}")
        return uncertainty

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


def extract_spatial_features_helper(data, config):
    """
    extract_spatial_features 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'extract_spatial_features_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"extract_spatial_features_helper 处理完成")
    return result


def calculate_divergence_helper(data, config):
    """
    calculate_divergence 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'calculate_divergence_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"calculate_divergence_helper 处理完成")
    return result


def compute_correlation_helper(data, config):
    """
    compute_correlation 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'compute_correlation_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"compute_correlation_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋湍流模拟")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋湍流模拟Processor(config)
    
    # 步骤1: update_boundary_conditions
    processor.update_boundary_conditions()
    
    # 步骤2: calculate_ekman_transport
    processor.calculate_ekman_transport()
    
    # 步骤3: fill_missing_values
    processor.fill_missing_values()
    
    # 步骤4: generate_report
    processor.generate_report()
    
    # 步骤5: create_vector_plot
    processor.create_vector_plot()
    
    # 步骤6: interpolate_spatial_data
    processor.interpolate_spatial_data()
    
    # 步骤7: generate_contour_map
    processor.generate_contour_map()
    
    # 步骤8: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤9: normalize_data
    processor.normalize_data()
    
    # 步骤10: apply_temporal_filter
    processor.apply_temporal_filter()
    
    # 步骤11: estimate_uncertainty
    processor.estimate_uncertainty()
    
    # 步骤12: compute_climatology
    processor.compute_climatology()
    
    # 调用辅助函数: extract_spatial_features_helper
    extract_spatial_features_helper(processor.data, config)
    
    # 调用辅助函数: calculate_divergence_helper
    calculate_divergence_helper(processor.data, config)
    
    # 调用辅助函数: compute_correlation_helper
    compute_correlation_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
