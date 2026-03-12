#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋微生物基因组分析
场景ID: 36
函数数量: 11
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json

class 海洋微生物基因组分析Processor:
    """
    海洋微生物基因组分析处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self.status = "initialized"
    
    def save_to_database(self, output_path):
        """导出处理结果"""
        try:
            if self.data is not None:
                self.data.to_csv(output_path, index=False)
                print(f"数据已保存到: {output_path}")
            
            # 保存结果字典
            results_path = output_path.replace('.csv', '_results.json')
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False
    
    def interpolate_data(self, target_levels):
        """插值到目标层次"""
        if self.data is None:
            return None
        
        from scipy.interpolate import interp1d
        
        result = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            try:
                x = np.arange(len(self.data))
                y = self.data[col].values
                f = interp1d(x, y, kind='linear', fill_value='extrapolate')
                result[col] = f(target_levels)
            except Exception as e:
                print(f"插值失败 {col}: {e}")
        
        print(f"插值完成: {len(result)} 个变量")
        return result
    
    def detect_anomalies(self, threshold=2.0):
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
    
    def smooth_data(self, window_size=5):
        """数据平滑滤波"""
        if self.data is None:
            return False
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            values = self.data[col].values
            if len(values) >= window_size:
                # 移动平均滤波
                smoothed = np.convolve(values, np.ones(window_size)/window_size, mode='same')
                self.data[col] = smoothed
        
        print(f"数据平滑完成 (窗口大小: {window_size})")
        return True
    
    def export_results(self, output_path):
        """导出处理结果"""
        try:
            if self.data is not None:
                self.data.to_csv(output_path, index=False)
                print(f"数据已保存到: {output_path}")
            
            # 保存结果字典
            results_path = output_path.replace('.csv', '_results.json')
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False
    
    def extract_features(self, param=None):
        """执行 extract_features 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }
        
        self.results['extract_features'] = result
        print(f"extract_features 执行完成")
        return result
    
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
    
    def load_data(self, file_path):
        """加载数据文件"""
        try:
            print(f"正在加载: {file_path}")
            self.data = pd.read_csv(file_path)
            self.status = "data_loaded"
            return True
        except FileNotFoundError:
            print(f"文件不存在: {file_path}")
            return False
        except Exception as e:
            print(f"加载失败: {e}")
            return False
    

def quality_control_helper(data, config):
    """
    quality_control 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'quality_control_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'quality_control_helper'} 处理完成")
    return result


def validate_results_helper(data, config):
    """
    validate_results 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'validate_results_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'validate_results_helper'} 处理完成")
    return result


def classify_patterns_helper(data, config):
    """
    classify_patterns 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'classify_patterns_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'classify_patterns_helper'} 处理完成")
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
    processor = 海洋微生物基因组分析Processor(config)
    
    # 步骤1: save_to_database
    if not processor.save_to_database(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: interpolate_data
    processor.interpolate_data()
    
    # 步骤3: detect_anomalies
    processor.detect_anomalies()
    
    # 步骤4: smooth_data
    processor.smooth_data()
    
    # 步骤5: export_results
    processor.export_results(config['output_file'])
    
    # 步骤6: extract_features
    processor.extract_features()
    
    # 步骤7: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤8: load_data
    processor.load_data()
    
    # 调用辅助函数: quality_control_helper
    quality_control_helper(processor.data, config)
    
    # 调用辅助函数: validate_results_helper
    validate_results_helper(processor.data, config)
    
    # 调用辅助函数: classify_patterns_helper
    classify_patterns_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
