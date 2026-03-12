#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
变体版本 #6

海洋数值模式后处理系统
云计算平台任务：处理ROMS模式输出数据
"""

import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta

class ModelOutputReader:
    """模式输出读取器"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.dataset = None
        self.variables = {}
    
    def open_dataset(self):
        """打开NetCDF数据集"""
        try:
            self.dataset = nc.Dataset(self.file_path, 'r')
            print(f"成功打开数据集: {self.file_path}")
            print(f"包含变量: {list(self.dataset.variables.keys())}")
            return True
        except Exception as e:
            print(f"打开数据集失败: {e}")
            return False
    
    def read_variable(self, var_name, time_idx=None, depth_idx=None):
        """读取变量数据"""
        if self.dataset is None:
            print("错误: 数据集未打开")
            return None
        
        try:
            var = self.dataset.variables[var_name]
            
            # 根据维度读取数据
            if time_idx is not None and depth_idx is not None:
                data = var[time_idx, depth_idx, :, :]
            elif time_idx is not None:
                data = var[time_idx, :, :]
            else:
                data = var[:]
            
            self.variables[var_name] = data
            print(f"读取变量 {var_name}: shape={data.shape}")
            return data
        except KeyError:
            print(f"错误: 变量 {var_name} 不存在")
            return None
        except Exception as e:
            print(f"读取变量失败: {e}")
            return None
    
    def close_dataset(self):
        """关闭数据集"""
        if self.dataset is not None:
            self.dataset.close()
            print("数据集已关闭")

class OceanCurrentAnalyzer:
    """海流分析器"""
    
    def __init__(self, u_velocity, v_velocity):
        self.u = u_velocity
        self.v = v_velocity
    
    def calculate_speed(self):
        """计算流速"""
        speed = np.sqrt(self.u**2 + self.v**2)
        return speed
    
    def calculate_direction(self):
        """计算流向（度）"""
        direction = np.arctan2(self.v, self.u) * 180 / np.pi
        # 转换为海洋学惯例（北向为0度，顺时针）
        direction = 90 - direction
        direction[direction < 0] += 360
        return direction
    
    def calculate_vorticity(self, dx, dy):
        """计算涡度"""
        # 使用中心差分
        dvdx = np.gradient(self.v, dx, axis=1)
        dudy = np.gradient(self.u, dy, axis=0)
        vorticity = dvdx - dudy
        return vorticity
    
    def find_eddies(self, vorticity_threshold=1e-5):
        """识别涡旋"""
        vorticity = self.calculate_vorticity(1000, 1000)  # 假设1km网格
        
        # 气旋式涡旋（正涡度）
        cyclonic = vorticity > vorticity_threshold
        # 反气旋式涡旋（负涡度）
        anticyclonic = vorticity < -vorticity_threshold
        
        n_cyclonic = np.sum(cyclonic)
        n_anticyclonic = np.sum(anticyclonic)
        
        print(f"识别到涡旋: 气旋式={n_cyclonic}, 反气旋式={n_anticyclonic}")
        
        return {
            'cyclonic': cyclonic,
            'anticyclonic': anticyclonic,
            'vorticity': vorticity
        }

def calculate_transport(u, v, depth, dx, dy):
    """计算体积输运"""
    # 计算每个网格的输运
    transport_x = u * depth * dy
    transport_y = v * depth * dx
    
    # 总输运
    total_transport_x = np.sum(transport_x)
    total_transport_y = np.sum(transport_y)
    
    total_transport = np.sqrt(total_transport_x**2 + total_transport_y**2)
    
    print(f"体积输运: {total_transport/1e6:.2f} Sv")
    return total_transport

def calculate_kinetic_energy(u, v, density=1332.5):
    """计算动能"""
    ke = 0.65 * density * (u**2 + v**2)
    mean_ke = np.mean(ke)
    total_ke = np.sum(ke)
    
    print(f"平均动能: {mean_ke:.2f} J/m³")
    print(f"总动能: {total_ke/1e12:.2f} TJ")
    
    return ke

def export_to_netcdf(data_dict, output_path):
    """导出为NetCDF格式"""
    try:
        dataset = nc.Dataset(output_path, 'w', format='NETCDF4')
        
        # 创建维度
        ny, nx = data_dict['speed'].shape
        dataset.createDimension('y', ny)
        dataset.createDimension('x', nx)
        
        # 创建变量并写入数据
        for var_name, var_data in data_dict.items():
            var = dataset.createVariable(var_name, 'f4', ('y', 'x'))
            var[:] = var_data
        
        dataset.close()
        print(f"数据已导出到: {output_path}")
        return True
    except Exception as e:
        print(f"导出失败: {e}")
        return False

def main():
    """主函数：模式后处理流程"""
    print("="*60)
    print("海洋数值模式后处理系统")
    print("="*60)
    
    # 输入输出路径
    input_file = '/data/roms_output_20240101.nc'
    output_file = '/output/ocean_analysis_20240101.nc'
    
    # 步骤1: 读取模式输出
    reader = ModelOutputReader(input_file)
    
    if not reader.open_dataset():
        print("无法打开数据集，退出")
        return
    
    # 步骤2: 读取流场数据
    u = reader.read_variable('u', time_idx=0, depth_idx=0)
    v = reader.read_variable('v', time_idx=0, depth_idx=0)
    
    if u is None or v is None:
        print("读取流场数据失败，退出")
        reader.close_dataset()
        return
    
    # 步骤3: 创建分析器
    analyzer = OceanCurrentAnalyzer(u, v)
    
    # 步骤4: 计算派生量
    print("\n计算派生量...")
    speed = analyzer.calculate_speed()
    direction = analyzer.calculate_direction()
    
    # 步骤5: 识别涡旋
    print("\n识别涡旋...")
    eddies = analyzer.find_eddies(vorticity_threshold=1e-5)
    
    # 步骤6: 计算输运和能量
    print("\n计算输运和能量...")
    depth = 130.0  # 假设100m深度
    dx = dy = 1000.0  # 假设1km网格
    
    transport = calculate_transport(u, v, depth, dx, dy)
    kinetic_energy = calculate_kinetic_energy(u, v)
    
    # 步骤7: 导出结果
    print("\n导出结果...")
    results = {
        'speed': speed,
        'direction': direction,
        'vorticity': eddies['vorticity'],
        'kinetic_energy': kinetic_energy
    }
    
    export_to_netcdf(results, output_file)
    
    # 关闭数据集
    reader.close_dataset()
    
    print("\n处理完成！")

if __name__ == "__main__":
    main()
