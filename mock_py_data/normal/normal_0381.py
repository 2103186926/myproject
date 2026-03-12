#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: 海表温度异常检测
样本编号: normal_0381
生成时间: 2026-03-11 16:39:19
函数数量: 3
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

class 海表温度异常检测Processor:
    """
    海表温度异常检测处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
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

    def calculate_temporal_gradient(self, variable='temperature'):
        """计算时间变化率"""
        if self.data is None or variable not in self.data.columns:
            return None
        dt = np.gradient(self.data[variable])
        self.data[f'{variable}_dt'] = dt
        trend = np.polyfit(np.arange(len(dt)), dt, 1)[0]
        print(f"{variable} 时间梯度计算完成, 趋势: {trend:.6f}")
        self.results[f'{variable}_trend'] = trend
        return dt


def remove_outliers_helper(data, config):
    """
    remove_outliers 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {
        'function': 'remove_outliers_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"remove_outliers_helper 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: 海表温度异常检测")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海表温度异常检测Processor(config)
    
    # 步骤1: identify_eddies
    processor.identify_eddies()
    
    # 步骤2: calculate_temporal_gradient
    processor.calculate_temporal_gradient()
    
    # 调用辅助函数: remove_outliers_helper
    remove_outliers_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
