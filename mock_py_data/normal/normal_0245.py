#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海洋保护区规划
样本编号: normal_0245
生成时间: 2026-03-11 16:39:19
函数数量: 9
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海洋保护区规划Processor:
    """
    海洋保护区规划处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def calculate_statistics(self):
        """计算统计量"""
        if self.data is None:
            return None
        
        stats = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            stats[col] = {
                'mean': float(self.data[col].mean()),
                'std': float(self.data[col].std()),
                'min': float(self.data[col].min()),
                'max': float(self.data[col].max()),
                'median': float(self.data[col].median())
            }
        
        self.results['statistics'] = stats
        print(f"计算了 {len(stats)} 个变量的统计量")
        return stats

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

    def detect_spatial_anomalies(self, variable='temperature', threshold=2.0):
        """检测空间异常"""
        if self.data is None or variable not in self.data.columns:
            return []
        window_size = 10
        anomalies = []
        for i in range(len(self.data) - window_size):
            window = self.data[variable].iloc[i:i+window_size]
            mean = window.mean()
            std = window.std()
            if std > 0:
                z_score = abs((self.data[variable].iloc[i+window_size//2] - mean) / std)
                if z_score > threshold:
                    anomalies.append({'index': i + window_size//2, 'value': self.data[variable].iloc[i+window_size//2], 'z_score': z_score})
        print(f"检测到 {len(anomalies)} 个空间异常点")
        self.results['spatial_anomalies'] = anomalies
        return anomalies

    def predict_current(self, lead_time=24):
        """预测未来流场"""
        if self.data is None:
            return None
        predictions = {}
        for vel_component in ['u_velocity', 'v_velocity']:
            if vel_component in self.data.columns:
                values = self.data[vel_component].values
                lag1_corr = np.corrcoef(values[:-1], values[1:])[0, 1]
                predicted = values[-1] * (lag1_corr ** lead_time)
                predictions[vel_component] = float(predicted)
        self.results['predicted_current'] = predictions
        print(f"流场预测完成: {lead_time}h")
        return predictions

    def parse_observation_data(self, file_path):
        """解析Argo浮标等观测数据"""
        try:
            n_profiles = 50
            n_levels = 20
            data_list = []
            for i in range(n_profiles):
                for j in range(n_levels):
                    data_list.append({
                        'profile_id': i,
                        'pressure': j * 50,
                        'temperature': 25 - j * 0.5 + np.random.randn() * 0.5,
                        'salinity': 35 + np.random.randn() * 0.3,
                        'lon': 120 + np.random.randn() * 5,
                        'lat': 30 + np.random.randn() * 3
                    })
            self.data = pd.DataFrame(data_list)
            self.status = "observation_parsed"
            print(f"观测数据解析完成: {n_profiles} 个剖面")
            return True
        except Exception as e:
            print(f"观测数据解析失败: {e}")
            return False

    def calculate_anomaly(self, climatology):
        """计算相对于气候态的异常值"""
        if self.data is None or climatology is None or 'time' not in self.data.columns:
            return False
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data['month'] = self.data['time'].dt.month
        for col in climatology.keys():
            if col in self.data.columns:
                anomaly_col = f'{col}_anomaly'
                self.data[anomaly_col] = 0.0
                for month, clim_value in climatology[col].items():
                    mask = self.data['month'] == month
                    self.data.loc[mask, anomaly_col] = self.data.loc[mask, col] - clim_value
        print("异常值计算完成")
        return True


def grid_irregular_data_helper(data, config):
    """
    grid_irregular_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'grid_irregular_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"grid_irregular_data_helper 处理完成")
    return result


def run_ocean_model_helper(data, config):
    """
    run_ocean_model 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'run_ocean_model_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"run_ocean_model_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海洋保护区规划")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋保护区规划Processor(config)
    
    # 步骤1: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤2: generate_report
    processor.generate_report()
    
    # 步骤3: calculate_trend
    processor.calculate_trend()
    
    # 步骤4: detect_spatial_anomalies
    processor.detect_spatial_anomalies()
    
    # 步骤5: predict_current
    processor.predict_current()
    
    # 步骤6: parse_observation_data
    processor.parse_observation_data()
    
    # 步骤7: calculate_anomaly
    processor.calculate_anomaly()
    
    # 调用辅助函数: grid_irregular_data_helper
    grid_irregular_data_helper(processor.data, config)
    
    # 调用辅助函数: run_ocean_model_helper
    run_ocean_model_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
