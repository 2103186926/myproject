#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
变体版本 #5

海洋温盐深(CTD)数据处理系统
云计算平台任务：处理船载CTD观测数据
"""

import numpy as np
import pandas as pd
from datetime import datetime
from scipy.interpolate import interp1d
from scipy.signal import savgol_filter

class CTDDataProcessor:
    """CTD数据处理器"""
    
    def __init__(self, config):
        self.config = config
        self.raw_data = None
        self.processed_data = None
        self.qc_flags = None
    
    def load_data(self, file_path):
        """加载CTD原始数据"""
        try:
            print(f"正在加载数据: {file_path}")
            self.raw_data = pd.read_csv(file_path)
            print(f"成功加载 {len(self.raw_data)} 条记录")
            return True
        except FileNotFoundError:
            print(f"错误: 文件不存在 {file_path}")
            return False
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False
    
    def quality_control(self):
        """数据质量控制"""
        if self.raw_data is None:
            print("错误: 没有数据需要处理")
            return False
        
        print("开始质量控制...")
        n_records = len(self.raw_data)
        self.qc_flags = np.zeros(n_records, dtype=int)
        
        # 检查温度范围
        temp = self.raw_data['temperature'].values
        for i in range(n_records):
            if temp[i] < -2.5 or temp[i] > 50.0:
                self.qc_flags[i] = 1  # 标记为可疑
        
        # 检查盐度范围
        salinity = self.raw_data['salinity'].values
        for i in range(n_records):
            if salinity[i] < 0.0 or salinity[i] > 42.0:
                self.qc_flags[i] = 1
        
        # 检查深度单调性
        depth = self.raw_data['depth'].values
        for i in range(1, n_records):
            if depth[i] < depth[i-1]:
                self.qc_flags[i] = 2  # 标记为错误
        
        bad_count = np.sum(self.qc_flags > 0)
        print(f"质量控制完成: {bad_count}/{n_records} 条记录被标记")
        return True
    
    def remove_outliers(self):
        """移除异常值"""
        if self.qc_flags is None:
            print("警告: 未进行质量控制")
            return False
        
        # 只保留质量标记为0的数据
        valid_mask = self.qc_flags == 0
        self.processed_data = self.raw_data[valid_mask].copy()
        
        removed_count = len(self.raw_data) - len(self.processed_data)
        print(f"移除了 {removed_count} 条异常数据")
        return True
    
    def interpolate_to_standard_levels(self, levels):
        """插值到标准深度层"""
        if self.processed_data is None:
            print("错误: 没有处理后的数据")
            return None
        
        depth = self.processed_data['depth'].values
        temp = self.processed_data['temperature'].values
        salinity = self.processed_data['salinity'].values
        
        # 创建插值函数
        try:
            temp_interp = interp1d(depth, temp, kind='linear', 
                                  bounds_error=False, fill_value='extrapolate')
            sal_interp = interp1d(depth, salinity, kind='linear',
                                 bounds_error=False, fill_value='extrapolate')
            
            # 插值到标准层
            temp_std = temp_interp(levels)
            sal_std = sal_interp(levels)
            
            result = pd.DataFrame({
                'depth': levels,
                'temperature': temp_std,
                'salinity': sal_std
            })
            
            print(f"插值完成: {len(levels)} 个标准层")
            return result
        except Exception as e:
            print(f"插值失败: {e}")
            return None
    
    def smooth_data(self, window_length=11, polyorder=3):
        """平滑数据"""
        if self.processed_data is None:
            return False
        
        try:
            temp = self.processed_data['temperature'].values
            salinity = self.processed_data['salinity'].values
            
            if len(temp) < window_length:
                print("警告: 数据点太少，无法平滑")
                return False
            
            # Savitzky-Golay滤波
            temp_smooth = savgol_filter(temp, window_length, polyorder)
            sal_smooth = savgol_filter(salinity, window_length, polyorder)
            
            self.processed_data['temperature'] = temp_smooth
            self.processed_data['salinity'] = sal_smooth
            
            print("数据平滑完成")
            return True
        except Exception as e:
            print(f"平滑失败: {e}")
            return False

def calculate_density(temperature, salinity, pressure):
    """计算海水密度（UNESCO公式简化版）"""
    # 参考密度
    rho0 = 1025.0
    
    # 温度效应
    a0 = 999.842594
    a1 = 6.793952e-2
    a2 = -9.095290e-3
    a3 = 1.001685e-4
    
    rho_t = a0 + a1*temperature + a2*temperature**2 + a3*temperature**3
    
    # 盐度效应
    b0 = 8.24493e-1
    b1 = -4.0899e-3
    b2 = 7.6438e-5
    
    rho_s = b0*salinity + b1*salinity**2 + b2*salinity**3
    
    # 压力效应（简化）
    rho_p = pressure * 4.5e-6
    
    density = rho_t + rho_s + rho_p
    
    return density

def calculate_sound_speed(temperature, salinity, depth):
    """计算声速（Mackenzie公式）"""
    # Mackenzie (1981) 声速公式
    c = (1448.96 + 4.591*temperature - 5.304e-2*temperature**2 
         + 2.374e-4*temperature**3 + 1.340*(salinity-35) 
         + 1.630e-2*depth + 1.675e-7*depth**2
         - 1.025e-2*temperature*(salinity-35) 
         - 7.139e-13*temperature*depth**3)
    
    return c

def export_results(data, output_path):
    """导出处理结果"""
    try:
        data.to_csv(output_path, index=False)
        print(f"结果已保存到: {output_path}")
        return True
    except Exception as e:
        print(f"导出失败: {e}")
        return False

def main():
    """主函数：CTD数据处理流程"""
    print("="*60)
    print("海洋CTD数据处理系统")
    print("="*60)
    
    # 配置参数
    config = {
        'input_file': '/data/ctd_station_001.csv',
        'output_file': '/output/ctd_processed.csv',
        'standard_levels': np.arange(0, 1000, 10)  # 0-1000m，每10m一层
    }
    
    # 创建处理器
    processor = CTDDataProcessor(config)
    
    # 步骤1: 加载数据
    if not processor.load_data(config['input_file']):
        print("数据加载失败，退出")
        return
    
    # 步骤2: 质量控制
    if not processor.quality_control():
        print("质量控制失败，退出")
        return
    
    # 步骤3: 移除异常值
    if not processor.remove_outliers():
        print("异常值移除失败，退出")
        return
    
    # 步骤4: 数据平滑
    processor.smooth_data(window_length=11, polyorder=3)
    
    # 步骤5: 插值到标准层
    standard_data = processor.interpolate_to_standard_levels(config['standard_levels'])
    
    if standard_data is not None:
        # 步骤6: 计算派生变量
        print("计算派生变量...")
        standard_data['density'] = calculate_density(
            standard_data['temperature'].values,
            standard_data['salinity'].values,
            standard_data['depth'].values
        )
        
        standard_data['sound_speed'] = calculate_sound_speed(
            standard_data['temperature'].values,
            standard_data['salinity'].values,
            standard_data['depth'].values
        )
        
        # 步骤7: 导出结果
        export_results(standard_data, config['output_file'])
        
        print("\n处理完成！")
        print(f"输出记录数: {len(standard_data)}")
    else:
        print("插值失败，无法继续")

if __name__ == "__main__":
    main()
