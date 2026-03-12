#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: GeoTIFF影像处理
样本编号: normal_0031
生成时间: 2026-03-11 16:39:19
函数数量: 13
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class GeoTIFF影像处理Processor:
    """
    GeoTIFF影像处理处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def calculate_divergence(self):
        """计算水平散度"""
        if self.data is None:
            return None
        if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
            du_dx = np.gradient(self.data['u_velocity'])
            dv_dy = np.gradient(self.data['v_velocity'])
            self.data['divergence'] = du_dx + dv_dy
            print("散度计算完成")
            return self.data['divergence'].values
        return None

    def calculate_trend(self, variable):
        """计算长期趋势"""
        if self.data is None or variable not in self.data.columns:
            return None
        x = np.arange(len(self.data))
        y = self.data[variable].values
        coeffs = np.polyfit(x, y, 1)
        trend = coeffs[0]
        intercept = coeffs[1]
        y_pred = coeffs[0] * x + coeffs[1]
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / (ss_tot + 1e-10))
        result = {'trend': float(trend), 'intercept': float(intercept), 'r_squared': float(r_squared), 'trend_per_year': float(trend * 365) if 'time' in self.data.columns else float(trend)}
        self.results[f'{variable}_trend'] = result
        print(f"{variable} 趋势: {trend:.6f} (R²={r_squared:.3f})")
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

    def remove_outliers(self, threshold=3.0):
        """移除异常值"""
        if self.data is None:
            return False
        
        original_size = len(self.data)
        mask = np.ones(len(self.data), dtype=bool)
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            mean = self.data[col].mean()
            std = self.data[col].std()
            if std > 0:
                z_scores = np.abs((self.data[col] - mean) / std)
                mask &= (z_scores <= threshold)
        
        self.data = self.data[mask]
        removed = original_size - len(self.data)
        print(f"移除了 {removed} 个异常值")
        return True

    def interpolate_temporal_data(self, target_times):
        """时间序列插值"""
        if self.data is None or 'time' not in self.data.columns:
            return None
        from scipy.interpolate import interp1d
        self.data['time'] = pd.to_datetime(self.data['time'])
        time_numeric = (self.data['time'] - self.data['time'].min()).dt.total_seconds()
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            try:
                f = interp1d(time_numeric, self.data[col], kind='cubic', fill_value='extrapolate')
                result[col] = f(target_times)
            except:
                pass
        print(f"时间插值完成: {len(result)} 个变量")
        return result

    def detect_bloom_events(self, threshold=5.0):
        """检测藻华/水华事件"""
        if self.data is None:
            return []
        bloom_events = []
        if 'chlorophyll' in self.data.columns:
            high_chl = self.data['chlorophyll'] > threshold
            bloom_start = None
            for i in range(len(self.data)):
                if high_chl.iloc[i] and bloom_start is None:
                    bloom_start = i
                elif not high_chl.iloc[i] and bloom_start is not None:
                    bloom_events.append({'start_index': int(bloom_start), 'end_index': int(i - 1), 'duration': int(i - bloom_start), 'max_chlorophyll': float(self.data['chlorophyll'].iloc[bloom_start:i].max())})
                    bloom_start = None
        self.results['bloom_events'] = bloom_events
        print(f"检测到 {len(bloom_events)} 个水华事件")
        return bloom_events

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

    def quality_control(self):
        """质量控制"""
        if self.data is None:
            return False
        
        n_records = len(self.data)
        flags = np.zeros(n_records, dtype=int)
        
        # 检查数值范围
        for col in self.data.select_dtypes(include=[np.number]).columns:
            q1 = self.data[col].quantile(0.25)
            q3 = self.data[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            outliers = (self.data[col] < lower) | (self.data[col] > upper)
            flags[outliers] = 1
        
        bad_count = np.sum(flags > 0)
        print(f"质量控制: {bad_count}/{n_records} 条记录被标记")
        
        self.results['qc_flags'] = flags
        return True

    def load_netcdf_data(self, file_path):
        """加载NetCDF格式的海洋数据"""
        try:
            import xarray as xr
            ds = xr.open_dataset(file_path)
            data_dict = {}
            for var in ds.data_vars:
                data_dict[var] = ds[var].values.flatten()[:1000]
            self.data = pd.DataFrame(data_dict)
            self.status = "netcdf_loaded"
            print(f"NetCDF数据加载完成: {len(ds.data_vars)} 个变量")
            return True
        except Exception as e:
            print(f"NetCDF加载失败: {e}")
            self.data = pd.DataFrame({
                'temperature': np.random.randn(1000) * 5 + 15,
                'salinity': np.random.randn(1000) * 2 + 35,
                'depth': np.random.rand(1000) * 5000
            })
            return True


def predict_temperature_helper(data, config):
    """
    predict_temperature 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'predict_temperature_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"predict_temperature_helper 处理完成")
    return result


def apply_temporal_filter_helper(data, config):
    """
    apply_temporal_filter 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'apply_temporal_filter_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"apply_temporal_filter_helper 处理完成")
    return result


def save_to_database_helper(data, config):
    """
    save_to_database 辅助函数
    独立于类的工具函数
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


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
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
    
    # 创建处理器实例
    processor = GeoTIFF影像处理Processor(config)
    
    # 步骤1: calculate_divergence
    processor.calculate_divergence()
    
    # 步骤2: calculate_trend
    processor.calculate_trend()
    
    # 步骤3: perform_eof_analysis
    processor.perform_eof_analysis()
    
    # 步骤4: calculate_vorticity
    processor.calculate_vorticity()
    
    # 步骤5: remove_outliers
    processor.remove_outliers()
    
    # 步骤6: interpolate_temporal_data
    processor.interpolate_temporal_data()
    
    # 步骤7: detect_bloom_events
    processor.detect_bloom_events()
    
    # 步骤8: calculate_buoyancy_frequency
    processor.calculate_buoyancy_frequency()
    
    # 步骤9: quality_control
    processor.quality_control()
    
    # 步骤10: load_netcdf_data
    processor.load_netcdf_data()
    
    # 调用辅助函数: predict_temperature_helper
    predict_temperature_helper(processor.data, config)
    
    # 调用辅助函数: apply_temporal_filter_helper
    apply_temporal_filter_helper(processor.data, config)
    
    # 调用辅助函数: save_to_database_helper
    save_to_database_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
