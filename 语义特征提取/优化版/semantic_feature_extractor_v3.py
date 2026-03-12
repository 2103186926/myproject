#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
semantic_feature_extractor_v3.py - Python容器逃逸静态检测语义特征提取工具（优化版）

版本: v3.0
功能：直接从Python源代码提取容器逃逸相关的语义特征向量
      增强抗混淆能力，检测编码绕过攻击
输入：Python源代码文件
输出：128维容器逃逸语义特征向量（.npy文件）+ 风险评估报告

优化内容：
1. 增加AST JSON保存和可视化功能
2. 完善检测规则（基于最新CVE和攻击技术）
3. 增强混淆检测（针对容器逃逸关键词的编码绕过）
4. 优化特征工程（移除完美特征，增强泛化能力）
"""

import json
import os
import sys
import re
import ast
import base64
import codecs
import binascii
import numpy as np
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter
import logging
import hashlib
from pathlib import Path


# 注释掉调试器代码，生产环境不需要
# import debugpy
# try:
#     debugpy.listen(("localhost", 9501))
#     print("Waiting for debugger attach")
#     debugpy.wait_for_client()
# except Exception as e:
#     pass


# ==================== 容器逃逸检测规则定义（优化版）====================

# 定义容器逃逸相关的敏感模块和函数（基于检测规则手册 + CVE补充）
CONTAINER_ESCAPE_MODULES = {
    # ===== 系统命令执行类 =====
    "os": [
        "system", "popen", "spawn", "spawnl", "spawnle", "spawnlp", "spawnlpe",
        "spawnv", "spawnve", "spawnvp", "spawnvpe",
        "exec", "execl", "execlp", "execle", "execv", "execvp", "execvpe",
        "fork", "forkpty", "dup", "dup2", "mknod", "mount", "umount",
        "chroot", "fchdir", "chdir", "setuid", "setgid", "seteuid", "setegid",
        "setreuid", "setregid", "setgroups", "initgroups",
        "kill", "killpg", "nice", "getpid", "getppid",
        "environ", "getenv", "putenv", "unsetenv"
    ],
    "subprocess": ["run", "call", "check_call", "check_output", "Popen", "getoutput", "getstatusoutput"],
    "commands": ["getoutput", "getstatusoutput"],
    "shlex": ["split", "quote"],
    
    # ===== 网络操作类 =====
    "socket": [
        "socket", "connect", "bind", "accept", "listen", "create_connection",
        "create_server", "getaddrinfo", "gethostbyname", "gethostbyaddr",
        "socketpair", "fromfd", "AF_UNIX", "AF_NETLINK"
    ],
    "urllib": ["urlopen", "Request", "urlretrieve"],
    "urllib.request": ["urlopen", "Request", "urlretrieve", "build_opener"],
    "urllib3": ["request", "PoolManager"],
    "requests": ["get", "post", "put", "delete", "head", "patch", "Session"],
    "httplib": ["HTTPConnection", "HTTPSConnection"],
    "http.client": ["HTTPConnection", "HTTPSConnection"],
    "aiohttp": ["ClientSession", "request"],
    
    # ===== 危险库调用类 =====
    "ctypes": ["CDLL", "cdll", "WinDLL", "windll", "CFUNCTYPE", "WINFUNCTYPE", 
               "memmove", "memset", "cast", "pointer", "POINTER", "byref"],
    "cffi": ["FFI", "dlopen"],
    "docker": ["from_env", "DockerClient", "APIClient"],
    "kubernetes": ["client", "config", "watch"],
    "kubernetes.client": ["CoreV1Api", "AppsV1Api", "BatchV1Api", "RbacAuthorizationV1Api"],
    
    # ===== 进程和线程类 =====
    "multiprocessing": ["Process", "Pool", "Queue", "Pipe", "Manager", "Value", "Array"],
    "threading": ["Thread", "Timer", "Lock", "RLock", "Semaphore"],
    "concurrent.futures": ["ProcessPoolExecutor", "ThreadPoolExecutor"],
    "pty": ["spawn", "fork", "openpty"],
    "fcntl": ["fcntl", "ioctl", "flock", "lockf"],
    "resource": ["setrlimit", "getrlimit", "prlimit"],
    
    # ===== 序列化类（代码注入风险）=====
    "pickle": ["load", "loads", "Unpickler"],
    "cPickle": ["load", "loads"],
    "_pickle": ["load", "loads"],
    "yaml": ["load", "unsafe_load", "full_load", "Loader", "UnsafeLoader"],
    "marshal": ["load", "loads"],
    "shelve": ["open"],
    "dill": ["load", "loads"],
    
    # ===== 动态执行类 =====
    "importlib": ["import_module", "__import__", "reload"],
    "imp": ["load_module", "load_source", "load_compiled"],
    "runpy": ["run_module", "run_path"],
    "code": ["compile_command", "InteractiveConsole", "InteractiveInterpreter"],
    "codeop": ["compile_command", "Compile", "CommandCompiler"],
    
    # ===== 文件操作类 =====
    "shutil": ["copy", "copy2", "copytree", "move", "rmtree", "chown"],
    "tempfile": ["mktemp", "mkstemp", "mkdtemp", "NamedTemporaryFile"],
    "glob": ["glob", "iglob"],
    "pathlib": ["Path"],
    "mmap": ["mmap"],
    
    # ===== 编码解码类（混淆检测）=====
    "base64": ["b64decode", "b64encode", "decodebytes", "decodestring", 
               "b16decode", "b32decode", "b85decode", "a85decode"],
    "codecs": ["decode", "encode", "getdecoder", "getencoder"],
    "binascii": ["unhexlify", "a2b_hex", "a2b_base64", "a2b_uu"],
    "zlib": ["decompress", "decompressobj"],
    "gzip": ["decompress", "open"],
    "bz2": ["decompress", "open"],
    "lzma": ["decompress", "open"],
}

# 定义内置敏感函数（优化版）
BUILTIN_SENSITIVE = set([
    # 动态执行
    "eval", "exec", "compile", "execfile",
    # 动态导入
    "__import__", "importlib.import_module",
    # 反射操作
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr", "hasattr",
    # 文件操作
    "open", "file", "input",
    # 类型操作
    "type", "object.__new__", "object.__init__",
    # 其他危险函数
    "breakpoint", "help", "license", "credits", "copyright"
])

# 将CONTAINER_ESCAPE_MODULES中的所有敏感函数添加到BUILTIN_SENSITIVE中
for module, functions in CONTAINER_ESCAPE_MODULES.items():
    for function in functions:
        BUILTIN_SENSITIVE.add(f"{module}.{function}")


# ==================== 容器逃逸攻击模式定义（优化版）====================
# 基于检测规则手册5.2节 + 最新CVE + 实战攻击技术

CONTAINER_ESCAPE_PATTERNS = {
    # ===== CE-CMD: 系统命令执行类 =====
    # CE-CMD-01: 敏感二进制命令调用
    "cmd_sensitive_binary": r"\b(nsenter|capsh|mount|umount|docker|kubectl|crictl|ctr|runc|containerd|podman|nerdctl|buildah|skopeo)\b",
    # CE-CMD-02: 反弹Shell特征
    "cmd_reverse_shell": r"(os\.dup2\s*\([^)]*fileno[^)]*,\s*[012]\s*\)|pty\.spawn\s*\(\s*['\"][^'\"]*(?:sh|bash|zsh|ksh|csh)['\"]|/dev/tcp/|nc\s+-[elp]|bash\s+-i\s*>&|python\s+-c\s*['\"]import\s+socket)",
    # CE-CMD-03: Fork炸弹
    "cmd_fork_bomb": r"(os\.fork\s*\(\s*\)|while\s+True\s*:\s*os\.fork|:\(\)\s*\{\s*:\|:\s*&\s*\})",
    # CE-CMD-04: 特权命令执行
    "cmd_privilege_exec": r"\b(sudo|su\s+-|chroot|unshare|setns|pivot_root)\b",
    # CE-CMD-05: 内核模块操作
    "cmd_kernel_module": r"\b(insmod|rmmod|modprobe|lsmod|modinfo)\b",
    
    # ===== CE-FILE: 文件与路径操作类 =====
    # CE-FILE-01: 容器环境指纹探测
    "file_container_fingerprint": r"(/\.dockerenv|/proc/1/cgroup|/proc/self/cgroup|/proc/self/status|/proc/self/mountinfo|/proc/1/sched|/proc/1/attr/current)",
    # CE-FILE-02: 宿主机敏感路径访问
    "file_host_sensitive": r"(/host/|/hostfs/|/proc/1/root|/proc/1/ns/|/var/run/docker\.sock|/var/run/containerd\.sock|/run/containerd/containerd\.sock|/var/run/crio/crio\.sock|/var/run/secrets)",
    # CE-FILE-03: Cgroup和内核配置
    "file_cgroup_kernel": r"(/sys/fs/cgroup|/proc/sys/kernel/core_pattern|/proc/sys/kernel/modprobe|release_agent|devices\.allow|devices\.deny|notify_on_release|cgroup\.procs)",
    # CE-FILE-04: /proc/self敏感文件
    "file_proc_self": r"(/proc/self/exe|/proc/self/mem|/proc/self/fd/|/proc/self/maps|/proc/self/pagemap|/proc/self/syscall|/proc/\d+/exe|/proc/\d+/mem)",
    # CE-FILE-05: K8s凭证路径
    "file_k8s_secrets": r"(/var/run/secrets/kubernetes\.io/serviceaccount|/var/run/secrets/eks\.amazonaws\.com|\.kube/config|kubeconfig|/etc/kubernetes/)",
    # CE-FILE-06: 云凭证路径
    "file_cloud_creds": r"(\.aws/credentials|\.aws/config|\.azure/|\.config/gcloud|/etc/boto\.cfg|instance/computeMetadata)",
    # CE-FILE-07: 设备文件访问
    "file_device_access": r"(/dev/mem|/dev/kmem|/dev/port|/dev/sda|/dev/vda|/dev/nvme|/dev/disk/|/dev/mapper/)",
    
    # ===== CE-LIB: 危险库调用类 =====
    # CE-LIB-01: Ctypes加载Libc
    "lib_ctypes_libc": r"ctypes\.(CDLL|cdll|WinDLL)\s*\(\s*['\"](?:libc\.so|libpthread|libdl|librt|libnss|libpam)",
    # CE-LIB-02: 敏感系统调用
    "lib_syscall": r"\b(setns|unshare|clone|mount|umount|pivot_root|ptrace|process_vm_readv|process_vm_writev|madvise|splice|vmsplice|tee|copy_file_range|memfd_create|execveat|seccomp|prctl|capset|capget)\b",
    # CE-LIB-03: Docker SDK滥用
    "lib_docker_sdk": r"(docker\.(from_env|DockerClient|APIClient)|import\s+docker)",
    # CE-LIB-04: K8s Client滥用
    "lib_k8s_client": r"(kubernetes\.client\.\w+Api|from\s+kubernetes\s+import|kubernetes\.config\.load)",
    # CE-LIB-05: 内存操作
    "lib_memory_ops": r"(ctypes\.memmove|ctypes\.memset|mmap\.mmap|ctypes\.cast|ctypes\.pointer)",
    
    # ===== CE-NET: 网络行为类 =====
    # CE-NET-01: 云元数据服务请求
    "net_cloud_metadata": r"(169\.254\.169\.254|100\.100\.100\.200|metadata\.google\.internal|169\.254\.170\.2|fd00:ec2::254)",
    # CE-NET-02: K8s组件端口
    "net_k8s_ports": r"(:10250|:10255|:10256|:2375|:2376|:2379|:2380|:6443|:8080|:8443|:9090|:9100|KUBERNETES_SERVICE_HOST|KUBERNETES_PORT)",
    # CE-NET-03: 本地回环绕过
    "net_localhost_bypass": r"(127\.0\.0\.1|localhost|0\.0\.0\.0)\s*[,:\"]?\s*(?:10250|10255|2375|6443|8080)",
    # CE-NET-04: Unix Socket连接
    "net_unix_socket": r"(socket\.AF_UNIX|unix://|/var/run/.*\.sock|\.socket\s*\(\s*socket\.AF_UNIX)",
    # CE-NET-05: Netlink Socket
    "net_netlink": r"(socket\.AF_NETLINK|NETLINK_KOBJECT_UEVENT|NETLINK_AUDIT)",
    
    # ===== CE-EXPLOIT: 漏洞利用类 =====
    # CE-EXPLOIT-01: Dirty COW (CVE-2016-5195)
    "exploit_dirty_cow": r"(madvise\s*\([^)]*MADV_DONTNEED|MAP_PRIVATE\s*\|\s*PROT_READ|/proc/self/mem.*write|ptrace.*POKETEXT)",
    # CE-EXPLOIT-02: Dirty Pipe (CVE-2022-0847)
    "exploit_dirty_pipe": r"(splice\s*\(|PIPE_BUF_FLAG|F_SETPIPE_SZ|pipe2?\s*\([^)]*O_DIRECT)",
    # CE-EXPLOIT-03: runc逃逸 (CVE-2019-5736)
    "exploit_runc": r"(#!/proc/self/exe|/proc/\d+/exe.*O_WRONLY|/proc/self/fd/\d+.*runc|overwrite.*runc)",
    # CE-EXPLOIT-04: Cgroup Release Agent
    "exploit_cgroup_release": r"(release_agent|notify_on_release\s*=\s*1|cgroup\.procs.*echo|/sys/fs/cgroup.*mkdir)",
    # CE-EXPLOIT-05: Hotplug劫持
    "exploit_hotplug": r"(/sys/kernel/uevent_helper|/proc/sys/kernel/hotplug|kobject_uevent|uevent.*ACTION)",
    # CE-EXPLOIT-06: containerd-shim (CVE-2020-15257)
    "exploit_containerd_shim": r"(containerd-shim|abstract.*socket|\\x00/containerd-shim)",
    # CE-EXPLOIT-07: Docker cp (CVE-2019-14271)
    "exploit_docker_cp": r"(libnss_files\.so|libnss_dns\.so|docker.*cp|nsswitch\.conf)",
    # CE-EXPLOIT-08: CVE-2022-0185 (fsconfig)
    "exploit_fsconfig": r"(fsconfig|fsopen|fsmount|move_mount|open_tree)",
    # CE-EXPLOIT-09: CVE-2022-0492 (cgroup v1)
    "exploit_cgroup_v1": r"(cgroup\.clone_children|cgroup\.subtree_control|release_agent.*upperdir)",
    # CE-EXPLOIT-10: CVE-2021-22555 (Netfilter)
    "exploit_netfilter": r"(setsockopt.*IPT_SO_SET|xt_compat|nf_tables|NFPROTO)",
    
    # ===== CE-K8S: K8s持久化类 =====
    # CE-K8S-01: 特权Pod配置
    "k8s_privileged_pod": r"(hostNetwork\s*:\s*true|hostPID\s*:\s*true|hostIPC\s*:\s*true|privileged\s*:\s*true|allowPrivilegeEscalation\s*:\s*true)",
    # CE-K8S-02: HostPath挂载
    "k8s_hostpath_mount": r"(hostPath\s*:\s*\n?\s*path\s*:\s*/|volumeMounts.*hostPath|type\s*:\s*DirectoryOrCreate)",
    # CE-K8S-03: ServiceAccount滥用
    "k8s_service_account": r"(serviceAccountName\s*:|automountServiceAccountToken\s*:\s*true|system:serviceaccount)",
    # CE-K8S-04: ExternalIPs劫持
    "k8s_external_ips": r"(externalIPs\s*:|externalTrafficPolicy|LoadBalancer)",
    # CE-K8S-05: RBAC提权
    "k8s_rbac_escalation": r"(ClusterRole|ClusterRoleBinding|escalate|impersonate|bind.*role)",
    # CE-K8S-06: 恶意Webhook
    "k8s_webhook": r"(MutatingWebhook|ValidatingWebhook|admissionregistration)",
    
    # ===== CE-CRED: 凭证窃取类 =====
    # CE-CRED-01: 云厂商AK/SK
    "cred_cloud_ak": r"(AKIA[0-9A-Z]{16}|ABIA[0-9A-Z]{16}|ACCA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|LTAI[0-9A-Za-z]{20}|AKID[0-9A-Za-z]{32})",
    # CE-CRED-02: SSH私钥
    "cred_ssh_key": r"(-----BEGIN\s+(RSA|DSA|EC|OPENSSH|ENCRYPTED)\s+PRIVATE\s+KEY-----|ssh-rsa\s+AAAA|ssh-ed25519\s+AAAA)",
    # CE-CRED-03: Docker配置
    "cred_docker_config": r"(\.docker/config\.json|\.dockercfg|docker.*auth.*base64)",
    # CE-CRED-04: K8s Token
    "cred_k8s_token": r"(eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9|serviceaccount.*token|bearer\s+token)",
    # CE-CRED-05: 数据库凭证
    "cred_database": r"(mysql://|postgres://|mongodb://|redis://|password\s*=\s*['\"][^'\"]+['\"])",
    
    # ===== CE-DOS: DoS攻击类 =====
    # CE-DOS-01: 无限循环
    "dos_infinite_loop": r"(while\s+True\s*:|while\s+1\s*:|for\s+_\s+in\s+iter\s*\(\s*int\s*,\s*1\s*\))",
    # CE-DOS-02: 资源耗尽
    "dos_resource_exhaust": r"(fork\s*\(\s*\).*while|Process\s*\(.*while|Thread\s*\(.*while|['\"]A['\"].*\*.*\d{6,})",
    # CE-DOS-03: 文件描述符耗尽
    "dos_fd_exhaust": r"(open\s*\([^)]+\).*while|socket\.socket.*while|os\.dup\s*\(.*while)",
}


# ==================== 容器逃逸风险等级定义（优化版）====================
# 基于CVSS评分和实际攻击影响进行分级

ESCAPE_RISK_RULES = {
    "CRITICAL": {
        # 直接导致容器逃逸的高危行为
        "CE-FILE-01": ["file_container_fingerprint"],  # 容器指纹探测（逃逸前置）
        "CE-FILE-02": ["file_host_sensitive"],         # 宿主机敏感路径访问
        "CE-FILE-07": ["file_device_access"],          # 设备文件访问
        "CE-LIB-01": ["lib_ctypes_libc"],              # Ctypes加载Libc
        "CE-LIB-02": ["lib_syscall"],                  # 敏感系统调用
        "CE-EXPLOIT-01": ["exploit_dirty_cow"],        # Dirty COW
        "CE-EXPLOIT-02": ["exploit_dirty_pipe"],       # Dirty Pipe
        "CE-EXPLOIT-03": ["exploit_runc"],             # runc逃逸
        "CE-EXPLOIT-04": ["exploit_cgroup_release"],   # Cgroup Release Agent
        "CE-EXPLOIT-06": ["exploit_containerd_shim"], # containerd-shim
        "CE-EXPLOIT-08": ["exploit_fsconfig"],         # fsconfig漏洞
    },
    "HIGH": {
        # 高风险行为，可能导致逃逸或信息泄露
        "CE-CMD-01": ["cmd_sensitive_binary"],         # 敏感二进制命令
        "CE-CMD-02": ["cmd_reverse_shell"],            # 反弹Shell
        "CE-CMD-04": ["cmd_privilege_exec"],           # 特权命令执行
        "CE-FILE-03": ["file_cgroup_kernel"],          # Cgroup/内核配置
        "CE-FILE-04": ["file_proc_self"],              # /proc/self敏感文件
        "CE-FILE-05": ["file_k8s_secrets"],            # K8s凭证路径
        "CE-FILE-06": ["file_cloud_creds"],            # 云凭证路径
        "CE-LIB-03": ["lib_docker_sdk"],               # Docker SDK
        "CE-LIB-04": ["lib_k8s_client"],               # K8s Client
        "CE-LIB-05": ["lib_memory_ops"],               # 内存操作
        "CE-NET-01": ["net_cloud_metadata"],           # 云元数据服务
        "CE-NET-02": ["net_k8s_ports"],                # K8s组件端口
        "CE-NET-04": ["net_unix_socket"],              # Unix Socket
        "CE-EXPLOIT-05": ["exploit_hotplug"],          # Hotplug劫持
        "CE-EXPLOIT-07": ["exploit_docker_cp"],        # Docker cp漏洞
        "CE-EXPLOIT-09": ["exploit_cgroup_v1"],        # Cgroup v1漏洞
        "CE-K8S-01": ["k8s_privileged_pod"],           # 特权Pod
        "CE-K8S-02": ["k8s_hostpath_mount"],           # HostPath挂载
        "CE-CRED-01": ["cred_cloud_ak"],               # 云AK/SK
        "CE-CRED-02": ["cred_ssh_key"],                # SSH私钥
        "CE-CRED-04": ["cred_k8s_token"],              # K8s Token
    },
    "MEDIUM": {
        # 中等风险，需要结合其他条件才能利用
        "CE-CMD-03": ["cmd_fork_bomb"],                # Fork炸弹
        "CE-CMD-05": ["cmd_kernel_module"],            # 内核模块操作
        "CE-NET-03": ["net_localhost_bypass"],         # 本地回环绕过
        "CE-NET-05": ["net_netlink"],                  # Netlink Socket
        "CE-K8S-03": ["k8s_service_account"],          # ServiceAccount
        "CE-K8S-04": ["k8s_external_ips"],             # ExternalIPs
        "CE-K8S-05": ["k8s_rbac_escalation"],          # RBAC提权
        "CE-CRED-03": ["cred_docker_config"],          # Docker配置
        "CE-CRED-05": ["cred_database"],               # 数据库凭证
        "CE-EXPLOIT-10": ["exploit_netfilter"],        # Netfilter漏洞
    },
    "LOW": {
        # 低风险，可能是正常行为但需要关注
        "CE-DOS-01": ["dos_infinite_loop"],            # 无限循环
        "CE-DOS-02": ["dos_resource_exhaust"],         # 资源耗尽
        "CE-DOS-03": ["dos_fd_exhaust"],               # 文件描述符耗尽
        "CE-K8S-06": ["k8s_webhook"],                  # Webhook
    }
}

# ==================== 混淆检测规则定义（针对容器逃逸关键词绕过）====================

# 容器逃逸敏感关键词（用于检测编码绕过）
ESCAPE_SENSITIVE_KEYWORDS = [
    # 敏感路径
    "/var/run/docker.sock", "/proc/kcore", "/proc/self/mem", "/proc/1/cgroup",
    "/.dockerenv", "/sys/fs/cgroup", "/etc/shadow", "/etc/passwd",
    "/var/run/secrets", "/root/.ssh", "/home/admin", "/etc/kubernetes",
    # 敏感命令
    "nsenter", "docker", "kubectl", "mount", "chroot", "capsh",
    # 敏感函数
    "eval", "exec", "system", "popen", "setns", "unshare",
    # 云元数据
    "169.254.169.254", "metadata.google.internal",
]

# 编码混淆检测模式
OBFUSCATION_PATTERNS = {
    # Base64编码检测
    "base64_decode": r"(base64\.(b64decode|decodebytes|decodestring)|\.decode\s*\(\s*['\"]base64['\"]\s*\))",
    "base64_string": r"[A-Za-z0-9+/]{20,}={0,2}",  # Base64特征字符串
    
    # Hex编码检测
    "hex_decode": r"(bytes\.fromhex|binascii\.(unhexlify|a2b_hex)|codecs\.decode\s*\([^)]*['\"]hex['\"])",
    "hex_string": r"\\x[0-9a-fA-F]{2}",
    
    # Unicode编码检测
    "unicode_escape": r"(\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}|\\N\{[^}]+\})",
    
    # ROT13/Caesar编码
    "rot13_decode": r"(codecs\.(decode|encode)\s*\([^)]*['\"]rot[_-]?13['\"]|\.translate\s*\([^)]*rot)",
    
    # 字符串拼接混淆
    "string_concat": r"(['\"][^'\"]{1,3}['\"]\s*\+\s*){3,}",  # 多次短字符串拼接
    "chr_obfuscation": r"(chr\s*\(\s*\d+\s*\)\s*\+?\s*){3,}",  # chr()函数拼接
    "ord_obfuscation": r"(ord\s*\(\s*['\"][^'\"]['\"]\s*\)\s*){2,}",
    
    # 动态执行混淆
    "eval_exec": r"(eval|exec|compile)\s*\(",
    "getattr_call": r"getattr\s*\([^)]+,\s*['\"][^'\"]+['\"]\s*\)\s*\(",
    "globals_exec": r"(globals|locals)\s*\(\s*\)\s*\[['\"][^'\"]+['\"]\s*\]",
    
    # 压缩混淆
    "zlib_decompress": r"(zlib\.decompress|gzip\.decompress|bz2\.decompress|lzma\.decompress)",
    
    # Lambda混淆
    "lambda_obfuscation": r"lambda\s+[^:]+:\s*(eval|exec|compile|getattr|__import__)",
    
    # 反射调用混淆
    "reflection_call": r"(__getattribute__|__getattr__|__class__|__bases__|__subclasses__|__mro__)",
    
    # 格式化字符串混淆
    "format_obfuscation": r"(f['\"].*\{.*\}.*['\"]|['\"].*['\"]\.format\s*\(|%\s*\(.*\)\s*%)",
}

# 添加一个自定义的JSON编码器，用于处理NumPy类型
class NumpyEncoder(json.JSONEncoder):
    """用于处理NumPy类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)


class ContainerEscapeFeatureExtractor:
    """容器逃逸语义特征提取器（优化版）- 直接从Python源代码提取特征，增强抗混淆能力"""
    
    def __init__(self, source_file: str):
        """
        初始化容器逃逸特征提取器
        
        参数:
            source_file: Python源代码文件路径
        """
        self.source_file = source_file
        self.source_code = ""
        self.ast_tree = None
        self.decoded_strings = []  # 存储解码后的字符串
        
        # 加载并解析Python源代码
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
            
            # 解析AST
            self.ast_tree = ast.parse(self.source_code, filename=source_file)
            print(f"成功加载并解析源代码文件: {source_file}")
            
        except FileNotFoundError:
            print(f"错误：找不到源代码文件: {source_file}")
            sys.exit(1)
        except SyntaxError as e:
            print(f"错误：源代码存在语法错误: {str(e)}")
            sys.exit(1)
        except Exception as e:
            print(f"错误：加载源代码文件时出错: {str(e)}")
            sys.exit(1)
    
    # ==================== AST导出和可视化功能 ====================
    
    def save_ast_json(self, output_path: Optional[str] = None) -> str:
        """
        将AST保存为JSON格式
        
        参数:
            output_path: 输出路径，默认为源文件名.ast.json
            
        返回:
            保存的文件路径
        """
        if output_path is None:
            base_name = os.path.splitext(self.source_file)[0]
            output_path = f"{base_name}.ast.json"
        
        ast_dict = self._ast_to_dict(self.ast_tree)  #! 将AST节点转换为字典
        
        # 添加元数据
        result = {
            "metadata": {
                "source_file": self.source_file,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "ast_version": "1.0"
            },
            "ast": ast_dict
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"AST JSON已保存至: {output_path}")
        return output_path
    
    def _ast_to_dict(self, node: ast.AST, node_id: int = 0) -> Dict[str, Any]:
        """
        递归将AST节点转换为字典
        
        参数:
            node: AST节点
            node_id: 节点ID
            
        返回:
            节点字典表示
        """
        result = {
            "id": node_id,
            "type": node.__class__.__name__,
            "lineno": getattr(node, 'lineno', None),
            "col_offset": getattr(node, 'col_offset', None),
        }
        
        # 添加节点特定属性
        for field, value in ast.iter_fields(node):  #! 针对于 node 上在 node._fields(属性字段)中出现的每个字段产生一个 (fieldname, value) 元组。
            if isinstance(value, list):  # 1.如果value值是一个list列表
                result[field] = []
                for i, item in enumerate(value):  # 继续遍历value列表中每一个元素
                    if isinstance(item, ast.AST):  # 1.1 如果是节点类，则递归调用_ast_to_dict，并添加到结果列表中
                        result[field].append(self._ast_to_dict(item, node_id * 100 + i))
                    else:  # 1.2 如果元素不是AST节点（比如是字符串、数字等），直接将其转换为字符串添加到列表中
                        result[field].append(str(item) if item is not None else None)                     
            elif isinstance(value, ast.AST):  # 2.如果value值是一个单一的AST节点（不是列表）
                result[field] = self._ast_to_dict(value, node_id * 10 + 1)
            else:  # 3.如果字段值既不是列表也不是AST节点，而是基本类型（字符串、数字、布尔值、None等），直接转换为字符串
                result[field] = str(value) if value is not None else None
        
        return result
    
    def visualize_ast(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        可视化AST并保存为PNG图片
        
        参数:
            output_path: 输出路径，默认为源文件名.ast.png
            
        返回:
            保存的文件路径，如果graphviz不可用则返回None
        """
        try:
            from graphviz import Digraph
        except ImportError:
            print("警告：graphviz库未安装，无法生成AST可视化图")
            print("请运行: pip install graphviz")
            return None
        
        if output_path is None:
            base_name = os.path.splitext(self.source_file)[0]
            output_path = f"{base_name}.ast"
        
        dot = Digraph(comment='AST Visualization')
        dot.attr(rankdir='TB', size='12,12')
        
        self._add_ast_nodes(dot, self.ast_tree, "0")
        
        try:
            dot.render(output_path, format='png', cleanup=True)
            print(f"AST可视化图已保存至: {output_path}.png")
            return f"{output_path}.png"
        except Exception as e:
            print(f"警告：生成AST可视化图失败: {str(e)}")
            print("请确保已安装Graphviz软件: https://graphviz.org/download/")
            return None
    
    def _add_ast_nodes(self, dot, node: ast.AST, node_id: str, parent_id: str = None):
        """
        递归添加AST节点到Graphviz图
        """
        # 节点标签
        label = node.__class__.__name__
        
        # 添加关键属性到标签
        if isinstance(node, ast.Name):
            label += f"\\n{node.id}"
        elif isinstance(node, ast.Constant):
            val = str(node.value)[:20]
            label += f"\\n{val}"
        elif isinstance(node, ast.FunctionDef):
            label += f"\\n{node.name}"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            label += f"\\n{node.func.id}()"
        
        # 根据节点类型设置颜色
        color = "lightblue"
        if isinstance(node, (ast.Call,)):
            color = "lightyellow"
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            color = "lightgreen"
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            color = "lightpink"
        
        dot.node(node_id, label, style='filled', fillcolor=color)
        
        if parent_id:
            dot.edge(parent_id, node_id)
        
        # 递归处理子节点
        child_idx = 0
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        child_id = f"{node_id}_{child_idx}"
                        self._add_ast_nodes(dot, item, child_id, node_id)
                        child_idx += 1
            elif isinstance(value, ast.AST):
                child_id = f"{node_id}_{child_idx}"
                self._add_ast_nodes(dot, value, child_id, node_id)
                child_idx += 1

    
    # ==================== 混淆检测与解码功能（核心优化）====================
    
    def detect_obfuscation_bypass(self) -> Dict[str, Any]:
        """
        检测针对容器逃逸关键词的编码混淆绕过
        
        核心目的：检测攻击者是否使用编码技术来隐藏容器逃逸相关的敏感关键词
        
        返回:
            包含混淆检测结果的字典
        """
        result = {
            "has_obfuscation": False,
            "obfuscation_techniques": [],  # 混淆技术
            "decoded_sensitive_keywords": [],  # 解码的敏感关键字
            "risk_level": "SAFE",  # 风险等级
            "details": {}
        }
        
        code = self.source_code
        
        # 1. 检测编码函数调用
        encoding_calls = self._detect_encoding_calls()
        if encoding_calls:
            result["obfuscation_techniques"].append("encoding_function_calls")
            result["details"]["encoding_calls"] = encoding_calls
        
        # 2. 提取并尝试解码所有字符串常量
        decoded_keywords = self._extract_and_decode_strings()
        if decoded_keywords:
            result["decoded_sensitive_keywords"] = decoded_keywords
            result["has_obfuscation"] = True
            result["obfuscation_techniques"].append("encoded_sensitive_keywords")
        
        # 3. 检测动态执行混淆
        dynamic_exec = self._detect_dynamic_execution()
        if dynamic_exec:
            result["obfuscation_techniques"].append("dynamic_execution")
            result["details"]["dynamic_execution"] = dynamic_exec
        
        # 4. 检测字符串拼接混淆
        string_concat = self._detect_string_concatenation()
        if string_concat:
            result["obfuscation_techniques"].append("string_concatenation")
            result["details"]["string_concatenation"] = string_concat
        
        # 5. 检测反射调用混淆
        reflection = self._detect_reflection_calls()
        if reflection:
            result["obfuscation_techniques"].append("reflection_calls")
            result["details"]["reflection_calls"] = reflection
        
        # 6. 计算混淆风险等级
        technique_count = len(result["obfuscation_techniques"])
        keyword_count = len(result["decoded_sensitive_keywords"])
        
        if keyword_count > 0 and technique_count >= 2:
            result["risk_level"] = "CRITICAL"
            result["has_obfuscation"] = True
        elif keyword_count > 0 or technique_count >= 3:
            result["risk_level"] = "HIGH"
            result["has_obfuscation"] = True
        elif technique_count >= 2:
            result["risk_level"] = "MEDIUM"
            result["has_obfuscation"] = True
        elif technique_count >= 1:
            result["risk_level"] = "LOW"
        
        if result["has_obfuscation"]:
            print(f"⚠️  检测到混淆绕过尝试!")
            print(f"   混淆技术: {', '.join(result['obfuscation_techniques'])}")
            if result["decoded_sensitive_keywords"]:
                print(f"   解码出的敏感关键词: {result['decoded_sensitive_keywords'][:5]}")
        
        return result
    
    def _detect_encoding_calls(self) -> List[Dict[str, Any]]:
        """检测编码/解码函数调用"""
        encoding_calls = []
        
        for node in ast.walk(self.ast_tree):  #! 这是一种广度优先遍历
            if isinstance(node, ast.Call):
                func_name = self._get_function_name_from_ast(node)  # 从ast.Call节点中提取函数全名
                if func_name:
                    # 检查是否是编码相关函数
                    encoding_funcs = [
                        "base64.b64decode", "base64.decodebytes", "base64.decodestring",
                        "binascii.unhexlify", "binascii.a2b_hex", "binascii.a2b_base64",
                        "codecs.decode", "bytes.fromhex",
                        "zlib.decompress", "gzip.decompress", "bz2.decompress", "lzma.decompress"
                    ]
                    
                    for enc_func in encoding_funcs:
                        if func_name.endswith(enc_func.split('.')[-1]) or func_name == enc_func:  #! 判断条件
                            encoding_calls.append({
                                "function": func_name,
                                "line": getattr(node, 'lineno', 0),
                                "type": "decode" if "decode" in func_name.lower() else "decompress"
                            })
        
        return encoding_calls
    
    def _extract_and_decode_strings(self) -> List[str]:
        """提取所有字符串常量并尝试解码，检查是否包含敏感关键词"""
        decoded_sensitive = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
                original = node.value if isinstance(node.value, str) else node.value.decode('utf-8', errors='ignore')
                
                # 尝试各种解码方式
                decoded_variants = self._try_decode_string(original)
                
                # 检查解码结果是否包含敏感关键词
                for decoded in decoded_variants:
                    for keyword in ESCAPE_SENSITIVE_KEYWORDS:
                        if keyword.lower() in decoded.lower():
                            if keyword not in decoded_sensitive:
                                decoded_sensitive.append(keyword)
                                self.decoded_strings.append({
                                    "original": original[:50],
                                    "decoded": decoded[:100],
                                    "keyword": keyword,
                                    "line": getattr(node, 'lineno', 0)
                                })
        
        return decoded_sensitive
    
    def _try_decode_string(self, s: str) -> List[str]:
        """尝试使用各种方式解码字符串"""
        results = [s]  # 原始字符串
        
        # 1. 尝试Base64解码
        try:
            # 检查是否像Base64
            if re.match(r'^[A-Za-z0-9+/]{4,}={0,2}$', s.strip()):
                decoded = base64.b64decode(s).decode('utf-8', errors='ignore')
                if decoded and decoded != s:
                    results.append(decoded)
        except:
            pass
        
        # 2. 尝试Hex解码
        try:
            if re.match(r'^[0-9a-fA-F]+$', s) and len(s) % 2 == 0:
                decoded = bytes.fromhex(s).decode('utf-8', errors='ignore')
                if decoded and decoded != s:
                    results.append(decoded)
        except:
            pass
        
        # 3. 尝试Unicode转义解码
        try:
            if '\\u' in s or '\\x' in s:
                decoded = s.encode().decode('unicode_escape')
                if decoded and decoded != s:
                    results.append(decoded)
        except:
            pass
        
        # 4. 尝试ROT13解码
        try:
            decoded = codecs.decode(s, 'rot_13')
            if decoded and decoded != s:
                # 检查解码结果是否更像正常文本
                if any(kw.lower() in decoded.lower() for kw in ESCAPE_SENSITIVE_KEYWORDS):
                    results.append(decoded)
        except:
            pass
        
        return results
    
    def _detect_dynamic_execution(self) -> List[Dict[str, Any]]:
        """检测动态执行模式"""
        dynamic_exec = []
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name_from_ast(node)
                
                # 检测eval/exec/compile
                if func_name in ['eval', 'exec', 'compile']:
                    # 检查参数是否来自解码操作
                    has_decode_arg = False
                    for arg in node.args:
                        if isinstance(arg, ast.Call):
                            arg_func = self._get_function_name_from_ast(arg)
                            if arg_func and any(x in arg_func.lower() for x in ['decode', 'decompress', 'fromhex']):
                                has_decode_arg = True  # 标记有解码参数
                    
                    dynamic_exec.append({
                        "function": func_name,  # 函数名（eval/exec/compile）
                        "line": getattr(node, 'lineno', 0),  # 代码行号（使用 getattr 安全获取）
                        "has_decode_argument": has_decode_arg,  # 是否有解码参数
                        "risk": "HIGH" if has_decode_arg else "MEDIUM"  # 风险等级（有解码参数为HIGH，否则为MEDIUM）
                    })
                
                # 检测getattr动态调用
                elif func_name == 'getattr':
                    if len(node.args) >= 2:
                        dynamic_exec.append({
                            "function": "getattr",
                            "line": getattr(node, 'lineno', 0),
                            "risk": "MEDIUM"
                        })
        
        return dynamic_exec
    
    def _detect_string_concatenation(self) -> List[Dict[str, Any]]:
        """检测字符串拼接混淆"""
        concat_patterns = []
        
        # 检测BinOp中的字符串拼接
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                # 统计连续的字符串拼接
                concat_count = self._count_string_concat(node)
                if concat_count >= 3:  # 拼接次数大于等于3，就认为是可疑的混淆模式
                    concat_patterns.append({
                        "type": "string_addition",
                        "count": concat_count,
                        "line": getattr(node, 'lineno', 0),
                        "risk": "HIGH" if concat_count >= 5 else "MEDIUM"
                    })
            
            # 检测chr()拼接
            if isinstance(node, ast.Call):
                func_name = self._get_function_name_from_ast(node)
                if func_name == 'chr':
                    # 检查是否在拼接上下文中
                    concat_patterns.append({
                        "type": "chr_concatenation",
                        "line": getattr(node, 'lineno', 0),
                        "risk": "MEDIUM"
                    })
        
        return concat_patterns
    
    def _count_string_concat(self, node: ast.BinOp, count: int = 0) -> int:
        """递归统计字符串拼接次数"""
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            left_count = self._count_string_concat(node.left, count) if isinstance(node.left, ast.BinOp) else 0
            right_count = self._count_string_concat(node.right, count) if isinstance(node.right, ast.BinOp) else 0
            return 1 + left_count + right_count
        return 0
    
    def _detect_reflection_calls(self) -> List[Dict[str, Any]]:
        """检测反射调用"""
        reflection_calls = []
        
        reflection_attrs = ['__getattribute__', '__getattr__', '__class__', '__bases__', 
                          '__subclasses__', '__mro__', '__globals__', '__builtins__']
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Attribute):  # 检查是否为属性访问节点
                if node.attr in reflection_attrs:
                    reflection_calls.append({
                        "attribute": node.attr,
                        "line": getattr(node, 'lineno', 0),
                        "risk": "HIGH" if node.attr in ['__subclasses__', '__globals__', '__builtins__'] else "MEDIUM"
                    })
        
        return reflection_calls

    
    # ==================== 特征提取功能（优化版）====================
    
    def extract_features(self) -> np.ndarray:
        """
        提取容器逃逸语义特征向量（优化版）
        
        特征维度设计（128维）：
        - 敏感函数频次特征：32维（8类 × 4特征）
        - 攻击模式特征：48维（12类 × 4特征）
        - 路径配置特征：24维（6类 × 4特征）
        - 混淆检测特征：24维（6类 × 4特征）
        
        返回:
            128维容器逃逸语义特征向量
        """
        # 1. 提取容器逃逸敏感函数频次特征（32维）
        sensitive_features = self._extract_escape_function_features()
        
        # 2. 提取攻击模式特征（48维）
        pattern_features = self._extract_attack_pattern_features()
        
        # 3. 提取路径配置特征（24维）
        path_features = self._extract_path_config_features()
        
        # 4. 提取混淆检测特征（24维）- 新增
        obfuscation_features = self._extract_obfuscation_features()
        
        # 合并特征
        features = np.concatenate([sensitive_features, pattern_features, path_features, obfuscation_features])
        
        return features
    
    def _extract_escape_function_features(self) -> np.ndarray:
        """
        提取容器逃逸敏感函数频次特征（优化版）
        
        返回:
            32维容器逃逸敏感函数频次特征向量
        """
        features = np.zeros(32)
        
        # 定义容器逃逸函数类别（共8类）
        categories = [
            "system_commands",     # os.system, subprocess.*, 命令执行
            "process_control",     # os.fork, os.dup2, pty.spawn, 进程控制
            "dangerous_libs",      # ctypes.CDLL, docker.*, kubernetes.*, 危险库
            "network_ops",         # socket.*, requests.*, urllib.*, 网络操作
            "file_ops",            # open, shutil.*, 文件操作
            "dynamic_exec",        # eval, exec, compile, __import__, 动态执行
            "encoding_ops",        # base64.*, codecs.*, binascii.*, 编码操作
            "serialization"        # pickle.*, yaml.*, marshal.*, 序列化
        ]
        
        # 遍历AST查找敏感函数调用
        sensitive_calls = self._find_sensitive_calls(self.ast_tree)
        
        # 统计每个类别的调用次数
        category_counts = {cat: 0 for cat in categories}
        
        for call in sensitive_calls:
            call_lower = call.lower()
            
            if any(cmd in call for cmd in ["os.system", "os.popen", "subprocess.", "commands."]):
                category_counts["system_commands"] += 1
            elif any(proc in call for proc in ["os.fork", "os.dup", "pty.", "multiprocessing.", "threading."]):
                category_counts["process_control"] += 1
            elif any(lib in call for lib in ["ctypes.", "docker.", "kubernetes."]):
                category_counts["dangerous_libs"] += 1
            elif any(net in call for net in ["socket.", "urllib.", "requests.", "http."]):
                category_counts["network_ops"] += 1
            elif any(f in call for f in ["open", "shutil.", "os.path", "pathlib."]):
                category_counts["file_ops"] += 1
            elif any(dyn in call for dyn in ["eval", "exec", "compile", "__import__", "importlib."]):
                category_counts["dynamic_exec"] += 1
            elif any(enc in call for enc in ["base64.", "codecs.", "binascii.", "zlib.", "gzip."]):
                category_counts["encoding_ops"] += 1
            elif any(ser in call for ser in ["pickle.", "yaml.", "marshal.", "json.load"]):
                category_counts["serialization"] += 1
        
        # 计算特征
        total_calls = max(len(sensitive_calls), 1)
        
        for i, category in enumerate(categories):
            count = category_counts[category]
            
            # 4个特征：存在性、对数频次、相对频率、归一化频次
            features[i * 4:i * 4 + 4] = [
                1.0 if count > 0 else 0.0,           # 存在性（二值）
                np.log1p(count),                      # 对数频次
                count / total_calls,                  # 相对频率
                min(count / 10.0, 1.0)               # 归一化频次（上限10）
            ]
        
        return features
    
    def _find_sensitive_calls(self, root_node: Any) -> List[str]:
        """从AST中查找敏感函数调用"""
        sensitive_calls = []
        
        for node in ast.walk(root_node):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name_from_ast(node)
                if func_name:
                    # 检查是否是敏感函数
                    if func_name in BUILTIN_SENSITIVE or any(
                        func_name.endswith(f".{s.split('.')[-1]}") 
                        for s in BUILTIN_SENSITIVE if '.' in s
                    ):
                        sensitive_calls.append(func_name)
        
        return sensitive_calls
    
    def _get_function_name_from_ast(self, call_node: ast.Call) -> Optional[str]:
        """从ast.Call节点中提取函数名"""
        func = call_node.func
        
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            parts = []
            current = func
            
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            
            if isinstance(current, ast.Name):
                parts.append(current.id)
                parts.reverse()
                return '.'.join(parts)
            else:
                return func.attr
        
        return None
    
    def _extract_attack_pattern_features(self) -> np.ndarray:
        """
        提取容器逃逸攻击模式特征（优化版）
        
        返回:
            48维攻击模式特征向量
        """
        features = np.zeros(48)
        
        code = self.source_code
        if not code:
            return features
        
        # 定义攻击模式类别（共12类）
        pattern_categories = {
            "cmd_execution": ["cmd_sensitive_binary", "cmd_reverse_shell", "cmd_fork_bomb", "cmd_privilege_exec"],
            "file_access": ["file_container_fingerprint", "file_host_sensitive", "file_device_access"],
            "cgroup_kernel": ["file_cgroup_kernel", "file_proc_self"],
            "credential_access": ["file_k8s_secrets", "file_cloud_creds", "cred_cloud_ak", "cred_ssh_key", "cred_k8s_token"],
            "dangerous_libs": ["lib_ctypes_libc", "lib_syscall", "lib_memory_ops"],
            "container_sdk": ["lib_docker_sdk", "lib_k8s_client"],
            "network_recon": ["net_cloud_metadata", "net_k8s_ports", "net_localhost_bypass", "net_unix_socket"],
            "kernel_exploits": ["exploit_dirty_cow", "exploit_dirty_pipe", "exploit_fsconfig", "exploit_netfilter"],
            "runtime_exploits": ["exploit_runc", "exploit_cgroup_release", "exploit_containerd_shim", "exploit_docker_cp"],
            "k8s_attacks": ["k8s_privileged_pod", "k8s_hostpath_mount", "k8s_service_account", "k8s_rbac_escalation"],
            "dos_attacks": ["dos_infinite_loop", "dos_resource_exhaust", "dos_fd_exhaust"],
            "misc_exploits": ["exploit_hotplug", "exploit_cgroup_v1", "cmd_kernel_module"]
        }
        
        # 统计每种模式的匹配次数
        pattern_counts = {}
        for pattern_name, pattern_regex in CONTAINER_ESCAPE_PATTERNS.items():
            try:
                matches = re.findall(pattern_regex, code, re.IGNORECASE | re.MULTILINE)
                pattern_counts[pattern_name] = len(matches)
            except re.error:
                pattern_counts[pattern_name] = 0
        
        # 计算每个类别的特征
        for i, (category, patterns) in enumerate(pattern_categories.items()):
            if i >= 12:
                break
            
            category_count = sum(pattern_counts.get(p, 0) for p in patterns)
            matched_patterns = sum(1 for p in patterns if pattern_counts.get(p, 0) > 0)
            max_count = max([pattern_counts.get(p, 0) for p in patterns], default=0)
            pattern_diversity = matched_patterns / len(patterns) if patterns else 0
            
            features[i * 4:i * 4 + 4] = [
                1.0 if category_count > 0 else 0.0,  # 存在性
                np.log1p(category_count),            # 对数总频次
                pattern_diversity,                    # 模式多样性
                np.log1p(max_count)                  # 对数最大频次
            ]
        
        return features
    
    def _extract_path_config_features(self) -> np.ndarray:
        """
        提取容器逃逸路径和配置特征（优化版）
        
        返回:
            24维路径和配置特征向量
        """
        features = np.zeros(24)
        
        code = self.source_code
        if not code:
            return features
        
        # 定义敏感路径类别（共6类）
        path_categories = {
            "container_runtime": [
                r"/var/run/docker\.sock", r"/var/run/containerd\.sock",
                r"/run/containerd", r"/var/run/crio"
            ],
            "proc_sensitive": [
                r"/proc/1/", r"/proc/self/exe", r"/proc/self/mem",
                r"/proc/self/fd/", r"/proc/\d+/exe", r"/proc/\d+/mem"
            ],
            "cgroup_sysfs": [
                r"/sys/fs/cgroup", r"/sys/kernel/", r"release_agent",
                r"notify_on_release", r"devices\.allow"
            ],
            "k8s_cloud_creds": [
                r"/var/run/secrets/kubernetes", r"\.kube/config",
                r"\.aws/credentials", r"\.config/gcloud"
            ],
            "host_filesystem": [
                r"/host/", r"/hostfs/", r"/proc/1/root",
                r"hostPath", r"volumeMounts"
            ],
            "device_files": [
                r"/dev/mem", r"/dev/kmem", r"/dev/sda",
                r"/dev/vda", r"/dev/nvme"
            ]
        }
        
        for i, (category, patterns) in enumerate(path_categories.items()):
            category_count = 0
            matched_patterns = 0
            max_count = 0
            
            for pattern in patterns:
                try:
                    matches = re.findall(pattern, code, re.IGNORECASE)
                    count = len(matches)
                    category_count += count
                    if count > 0:
                        matched_patterns += 1
                        max_count = max(max_count, count)
                except re.error:
                    pass
            
            features[i * 4:i * 4 + 4] = [
                1.0 if category_count > 0 else 0.0,
                np.log1p(category_count),
                matched_patterns / len(patterns) if patterns else 0,
                np.log1p(max_count)
            ]
        
        return features
    
    def _extract_obfuscation_features(self) -> np.ndarray:
        """
        提取混淆检测特征（新增）
        
        返回:
            24维混淆检测特征向量
        """
        features = np.zeros(24)
        
        code = self.source_code
        if not code:
            return features
        
        # 定义混淆检测类别（共6类）
        obfuscation_categories = {
            "encoding_decode": ["base64_decode", "hex_decode", "rot13_decode"],
            "string_obfuscation": ["string_concat", "chr_obfuscation", "unicode_escape"],
            "dynamic_execution": ["eval_exec", "getattr_call", "globals_exec"],
            "compression": ["zlib_decompress"],
            "reflection": ["reflection_call", "lambda_obfuscation"],
            "format_tricks": ["format_obfuscation", "base64_string", "hex_string"]
        }
        
        # 统计每种混淆模式
        pattern_counts = {}
        for pattern_name, pattern_regex in OBFUSCATION_PATTERNS.items():
            try:
                matches = re.findall(pattern_regex, code, re.IGNORECASE)
                pattern_counts[pattern_name] = len(matches)
            except re.error:
                pattern_counts[pattern_name] = 0
        
        # 计算特征
        for i, (category, patterns) in enumerate(obfuscation_categories.items()):
            category_count = sum(pattern_counts.get(p, 0) for p in patterns)
            matched_patterns = sum(1 for p in patterns if pattern_counts.get(p, 0) > 0)
            max_count = max([pattern_counts.get(p, 0) for p in patterns], default=0)
            
            features[i * 4:i * 4 + 4] = [
                1.0 if category_count > 0 else 0.0,
                np.log1p(category_count),
                matched_patterns / len(patterns) if patterns else 0,
                np.log1p(max_count)
            ]
        
        return features

    
    # ==================== 风险检测功能 ====================
    
    def detect_container_escape_risk(self) -> Dict[str, Any]:
        """
        检测代码的容器逃逸风险（优化版）
        
        返回:
            包含风险评估结果的字典
        """
        code = self.source_code
        
        if not code:
            return {"risk_level": "UNKNOWN", "reason": "无可分析代码"}
        
        risk_indicators = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        # 遍历所有检测规则
        for risk_level, rules in ESCAPE_RISK_RULES.items():  # 容器逃逸风险等级字典
            for rule_id, pattern_names in rules.items():
                for pattern_name in pattern_names:
                    if pattern_name in CONTAINER_ESCAPE_PATTERNS:  # 容器逃逸具体攻击模式字典
                        pattern = CONTAINER_ESCAPE_PATTERNS[pattern_name]
                        try:
                            matches = re.findall(pattern, code, re.IGNORECASE | re.MULTILINE)
                            if matches:
                                # 去重并限制样本数量
                                unique_matches = list(set(str(m) if isinstance(m, tuple) else m for m in matches))[:3]
                                risk_indicators[risk_level].append({
                                    "rule_id": rule_id,  # 攻击编号
                                    "pattern": pattern_name,  # 攻击模式
                                    "matches": len(matches),  # 匹配返回列表
                                    "samples": unique_matches  # 去重后的匹配样本（只保留前3个样本）
                                })
                        except re.error:
                            pass
        
        # 计算风险分数
        risk_score = (
            len(risk_indicators["CRITICAL"]) * 10 +
            len(risk_indicators["HIGH"]) * 5 +
            len(risk_indicators["MEDIUM"]) * 2 +
            len(risk_indicators["LOW"]) * 1
        )
        
        # 确定风险等级
        if risk_score >= 20 or len(risk_indicators["CRITICAL"]) >= 2:
            overall_risk = "CRITICAL"
        elif risk_score >= 10 or len(risk_indicators["HIGH"]) >= 2:
            overall_risk = "HIGH"
        elif risk_score >= 5 or len(risk_indicators["MEDIUM"]) >= 2:
            overall_risk = "MEDIUM"
        elif risk_score > 0:
            overall_risk = "LOW"
        else:
            overall_risk = "SAFE"
        
        # 生成风险摘要
        summary = []
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            if risk_indicators[level]:
                summary.append(f"发现 {len(risk_indicators[level])} 个{level}风险")
        
        result = {
            "risk_level": overall_risk,
            "risk_score": float(risk_score),
            "indicators": risk_indicators,
            "summary": ", ".join(summary) if summary else "未发现明显的容器逃逸风险",
            "total_patterns": sum(len(v) for v in risk_indicators.values())
        }
        
        if overall_risk in ["CRITICAL", "HIGH"]:
            print(f"⚠️  容器逃逸风险等级: {overall_risk}")
            print(f"   风险摘要: {result['summary']}")
        
        return result
    
    def detect_obfuscation(self) -> Dict[str, Any]:
        """
        检测代码混淆（优化版）
        
        返回:
            包含混淆检测结果的字典
        """
        code = self.source_code
        
        if not code:
            return {"obfuscated": False, "reason": "无可分析代码"}
        
        # 计算熵值
        entropy = self._calculate_entropy(code)
        
        # 计算平均行长度
        lines = [line for line in code.split('\n') if line.strip()]
        avg_line_length = sum(len(line) for line in lines) / len(lines) if lines else 0
        
        # 检测混淆特征（优化版）
        obfuscation_indicators = {
            # 基础混淆特征
            "高熵值": entropy > 5.0,
            "超长行": avg_line_length > 150,
            
            # 编码混淆
            "base64解码": bool(re.search(r'base64\.(b64decode|decodebytes|decodestring)', code)),
            "hex解码": bool(re.search(r'(bytes\.fromhex|binascii\.(unhexlify|a2b_hex))', code)),
            "unicode转义": bool(re.search(r'\\u[0-9a-fA-F]{4}', code)),
            
            # 动态执行混淆
            "eval/exec": bool(re.search(r'\b(eval|exec)\s*\(', code)),
            "compile": bool(re.search(r'\bcompile\s*\(', code)),
            "getattr调用": bool(re.search(r'getattr\s*\([^)]+,\s*[\'"][^\'"]+[\'"]\s*\)\s*\(', code)),
            
            # 字符串混淆
            "chr拼接": len(re.findall(r'chr\s*\(\s*\d+\s*\)', code)) >= 5,
            "字符串拼接": bool(re.search(r'([\'"][^\'"]{1,3}[\'"]\s*\+\s*){4,}', code)),
            
            # 反射混淆
            "反射调用": bool(re.search(r'(__subclasses__|__globals__|__builtins__|__mro__)', code)),
            
            # 压缩混淆
            "压缩解压": bool(re.search(r'(zlib|gzip|bz2|lzma)\.(decompress|open)', code)),
        }
        
        # 计算混淆分数
        obfuscation_score = sum(1 for v in obfuscation_indicators.values() if v)
        
        # 判断是否混淆（需要满足多个条件）
        is_obfuscated = obfuscation_score >= 3
        
        reasons = [key for key, val in obfuscation_indicators.items() if val]
        
        result = {
            "obfuscated": is_obfuscated,  # 是否混淆
            "obfuscation_score": obfuscation_score,  # 混淆分数
            "entropy": float(entropy),  # 代码熵值
            "avg_line_length": float(avg_line_length),  # 平均行长度
            "indicators": obfuscation_indicators,  # 混淆特征
            "reasons": reasons  # 混淆原因
        }
        
        if is_obfuscated:
            print(f"⚠️  检测到代码混淆，原因: {', '.join(reasons)}")
        
        return result
    
    def _calculate_entropy(self, text: str) -> float:
        """计算文本熵值"""
        if not text:
            return 0.0
        
        char_freq = Counter(text)
        length = len(text)
        
        entropy = 0.0
        for freq in char_freq.values():
            probability = freq / length
            entropy -= probability * np.log2(probability)
        
        return entropy
    
    # ==================== 保存功能 ====================
    
    def save_features(self, output_file: str, include_risk_report: bool = True) -> None:
        """保存特征向量和风险报告"""
        features = self.extract_features()
        np.save(output_file, features)
        print(f"容器逃逸语义特征向量已保存至: {output_file}")
        print(f"特征向量维度: {features.shape}")
        
        if include_risk_report:
            # 容器逃逸风险报告
            risk_result = self.detect_container_escape_risk()
            
            # 混淆检测报告
            obfuscation_result = self.detect_obfuscation()
            
            # 混淆绕过检测报告
            bypass_result = self.detect_obfuscation_bypass()
            
            # 合并报告
            full_report = {
                "source_file": self.source_file,
                "escape_risk": risk_result,
                "obfuscation": obfuscation_result,
                "obfuscation_bypass": bypass_result,
                "feature_dimensions": {
                    "total": 128,
                    "sensitive_functions": 32,
                    "attack_patterns": 48,
                    "path_config": 24,
                    "obfuscation": 24
                }
            }
            
            # 修改报告文件命名逻辑，保持与特征文件一致
            base_name = os.path.splitext(output_file)[0]
            report_file = f"{base_name}_risk_report.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(full_report, indent=2, ensure_ascii=False, cls=NumpyEncoder, fp=f)
            
            print(f"风险评估报告已保存至: {report_file}")
            print(f"容器逃逸风险等级: {risk_result['risk_level']}, 风险分数: {risk_result['risk_score']}")
            
            if bypass_result["has_obfuscation"]:
                print(f"⚠️  混淆绕过风险等级: {bypass_result['risk_level']}")



# ==================== 主函数 ====================

def collect_python_files(source_path: str) -> List[str]:
    """
    收集Python文件
    
    参数:
        source_path: 文件路径或目录路径
        
    返回:
        Python文件路径列表
    """
    python_files = []
    
    # 判断是文件还是目录
    if os.path.isfile(source_path):
        if source_path.endswith('.py'):
            python_files.append(source_path)
        else:
            print(f"警告: {source_path} 不是Python文件")
    elif os.path.isdir(source_path):
        print(f"从目录 {source_path} 收集Python文件...")
        for root, dirs, files in os.walk(source_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
        print(f"找到 {len(python_files)} 个Python文件")
    else:
        print(f"错误: {source_path} 不存在")
    
    return python_files


def process_file(source_file: str, output_file: Optional[str] = None,
                include_risk_report: bool = False,
                save_ast_json: bool = False, ast_json_path: Optional[str] = None,
                visualize_ast: bool = False, ast_png_path: Optional[str] = None,
                output_suffix: str = "") -> bool:
    """
    处理单个Python源代码文件并提取容器逃逸语义特征
    
    参数:
        source_file: Python源代码文件路径
        output_file: 输出文件路径（可选）
        include_risk_report: 是否生成风险评估报告
        save_ast_json: 是否保存AST JSON文件
        ast_json_path: AST JSON保存路径
        visualize_ast: 是否生成AST可视化图
        ast_png_path: AST PNG保存路径
        output_suffix: 输出文件名后缀（默认为空，保持与源文件名一致）
        
    返回:
        处理是否成功
    """
    try:
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(source_file))[0]
            # 使用简洁的命名方式，与源文件名保持一致
            if output_suffix:
                output_file = f"{base_name}_{output_suffix}.npy"
            else:
                output_file = f"{base_name}.npy"
        
        print("=" * 70)
        print("容器逃逸静态检测 - 语义特征提取工具 v3.0（优化版）")
        print("=" * 70)
        print(f"输入文件: {source_file}")
        print(f"输出文件: {output_file}")
        
        extractor = ContainerEscapeFeatureExtractor(source_file)
        
        # 可选：保存AST JSON
        if save_ast_json:
            print("\n[可选] 保存AST JSON...")
            extractor.save_ast_json(ast_json_path)
        
        # 可选：生成AST可视化
        if visualize_ast:
            print("\n[可选] 生成AST可视化图...")
            extractor.visualize_ast(ast_png_path)
        
        # 检测容器逃逸风险
        print("\n[1/4] 检测容器逃逸风险...")
        escape_risk = extractor.detect_container_escape_risk()
        
        # 检测代码混淆
        print("\n[2/4] 检测代码混淆...")
        obfuscation_result = extractor.detect_obfuscation()
        
        # 检测混淆绕过
        print("\n[3/4] 检测混淆绕过尝试...")
        bypass_result = extractor.detect_obfuscation_bypass()
        
        # 提取并保存特征
        print("\n[4/4] 提取语义特征向量...")
        extractor.save_features(output_file, include_risk_report)
        
        print("\n" + "=" * 70)
        print("处理完成！")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n错误: 处理文件 {source_file} 失败: {str(e)}")
        return False


def process_batch(source_path: str, output_dir: Optional[str] = None,
                 include_risk_report: bool = False,
                 save_ast_json: bool = False,
                 visualize_ast: bool = False,
                 output_suffix: str = "") -> None:
    """
    批量处理Python文件（支持单文件或目录）
    
    参数:
        source_path: Python文件路径或目录路径
        output_dir: 输出目录（可选，默认与源文件同目录）
        include_risk_report: 是否生成风险评估报告
        save_ast_json: 是否保存AST JSON文件
        visualize_ast: 是否生成AST可视化图
        output_suffix: 输出文件名后缀
    """
    # 收集Python文件
    python_files = collect_python_files(source_path)
    
    if not python_files:
        print("错误: 没有找到Python文件")
        return
    
    # 创建输出目录
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 统计信息
    total_files = len(python_files)
    success_count = 0
    failed_count = 0
    failed_files = []
    
    print("\n" + "=" * 70)
    print(f"开始批量处理 {total_files} 个Python文件")
    print("=" * 70)
    
    # 处理每个文件
    for idx, source_file in enumerate(python_files, 1):
        print(f"\n[{idx}/{total_files}] 处理文件: {source_file}")
        
        # 确定输出文件路径
        if output_dir:
            base_name = os.path.splitext(os.path.basename(source_file))[0]
            if output_suffix:
                output_file = os.path.join(output_dir, f"{base_name}_{output_suffix}.npy")
            else:
                output_file = os.path.join(output_dir, f"{base_name}.npy")
        else:
            output_file = None  # 使用默认路径（与源文件同目录）
        
        # 处理文件
        success = process_file(
            source_file,
            output_file,
            include_risk_report,
            save_ast_json,
            None,  # ast_json_path
            visualize_ast,
            None,  # ast_png_path
            output_suffix
        )
        
        if success:
            success_count += 1
        else:
            failed_count += 1
            failed_files.append(source_file)
        
        print()  # 空行分隔
    
    # 输出统计信息
    print("\n" + "=" * 70)
    print("批量处理完成！")
    print("=" * 70)
    print(f"总文件数: {total_files}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    
    if failed_files:
        print("\n失败的文件:")
        for file in failed_files:
            print(f"  - {file}")
    
    if output_dir:
        print(f"\n输出目录: {output_dir}")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(
        description="容器逃逸静态检测 - 直接从Python源代码提取语义特征向量（优化版v3.0）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 处理单个文件（默认只生成特征向量）
  python semantic_feature_extractor_v3.py sample.py
  # 输出: sample.npy
  
  # 生成特征向量和风险评估报告
  python semantic_feature_extractor_v3.py sample.py --report
  # 输出: sample.npy, sample_risk_report.json
  
  # 批量处理目录中的所有Python文件
  python semantic_feature_extractor_v3.py ./test_cases
  # 输出: 每个.py文件对应一个.npy文件
  
  # 批量处理并生成风险报告
  python semantic_feature_extractor_v3.py ./test_cases --report --output-dir ./output
  
  # 批量处理并指定输出目录
  python semantic_feature_extractor_v3.py ./test_cases --output-dir ./output
  
  # 自定义输出路径（仅单文件模式）
  python semantic_feature_extractor_v3.py sample.py -o output_features.npy
  
  # 添加自定义后缀
  python semantic_feature_extractor_v3.py sample.py --suffix container_escape_features
  # 输出: sample_container_escape_features.npy
  
  # 批量处理并添加后缀
  python semantic_feature_extractor_v3.py ./test_cases --suffix features --output-dir ./output
  
  # 保存AST JSON（仅单文件模式）
  python semantic_feature_extractor_v3.py sample.py --save-ast
  
  # 生成AST可视化图（仅单文件模式）
  python semantic_feature_extractor_v3.py sample.py --visualize-ast
        """
    )
    
    parser.add_argument("source_path", help="Python源代码文件路径或目录路径")
    parser.add_argument("-o", "--output", help="输出文件路径（仅单文件模式可用）")
    parser.add_argument("--output-dir", help="输出目录（批量处理模式）")
    parser.add_argument("--suffix", default="", help="输出文件名后缀（默认为空，保持与源文件名一致）")
    parser.add_argument("--report", action="store_true", help="生成风险评估报告（默认不生成）")
    
    # AST相关参数（仅单文件模式）
    parser.add_argument("--save-ast", action="store_true", help="保存AST为JSON格式（仅单文件模式）")
    parser.add_argument("--ast-path", help="AST JSON保存路径（可选）") 
    parser.add_argument("--visualize-ast", action="store_true", help="生成AST可视化图（需要graphviz，仅单文件模式）")
    parser.add_argument("--ast-png", help="AST PNG保存路径（可选）")
    
    args = parser.parse_args()
    
    # 判断是单文件还是目录
    if os.path.isfile(args.source_path):
        # 单文件模式
        if args.output_dir:
            print("警告: 单文件模式下 --output-dir 参数将被忽略")
        
        process_file(
            args.source_path,
            args.output,
            include_risk_report=args.report,
            save_ast_json=args.save_ast,
            ast_json_path=args.ast_path,
            visualize_ast=args.visualize_ast,
            ast_png_path=args.ast_png,
            output_suffix=args.suffix
        )
    
    elif os.path.isdir(args.source_path):
        # 批量处理模式
        if args.output:
            print("警告: 批量处理模式下 -o/--output 参数将被忽略")
        if args.save_ast:
            print("警告: 批量处理模式下 --save-ast 参数将被忽略")
        if args.visualize_ast:
            print("警告: 批量处理模式下 --visualize-ast 参数将被忽略")
        
        process_batch(
            args.source_path,
            output_dir=args.output_dir,
            include_risk_report=args.report,
            save_ast_json=False,  # 批量模式不支持
            visualize_ast=False,  # 批量模式不支持
            output_suffix=args.suffix
        )
    
    else:
        print(f"错误: {args.source_path} 不存在")
        sys.exit(1)


if __name__ == "__main__":
    main()
