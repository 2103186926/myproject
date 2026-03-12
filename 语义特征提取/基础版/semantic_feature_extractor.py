#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
semantic_feature_extractor.py - Python容器逃逸静态检测语义特征提取工具

功能：直接从Python源代码提取容器逃逸相关的语义特征向量
输入：Python源代码文件
输出：128维容器逃逸语义特征向量（.npy文件）+ 风险评估报告
"""

import json
import os
import sys
import re
import ast
import numpy as np
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import logging
import hashlib
from pathlib import Path

# 注释掉调试器代码，生产环境不需要
import debugpy
try:
    debugpy.listen(("localhost", 9501))
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
except Exception as e:
    pass

# ==================== 容器逃逸检测规则定义 ====================

# 定义容器逃逸相关的敏感模块和函数（基于检测规则手册）
CONTAINER_ESCAPE_MODULES = {
    # 系统命令执行
    "os": ["system", "popen", "spawn", "exec", "execl", "execlp", "execle",
           "execv", "execvp", "execvpe", "fork", "dup2", "mknod", "mount", "umount"],
    "subprocess": ["run", "call", "check_call", "check_output", "Popen"],
    "commands": ["getoutput", "getstatusoutput"],
    
    # 网络操作
    "socket": ["socket", "connect", "bind", "accept", "listen", "create_connection"],
    "urllib": ["urlopen", "Request"],
    "urllib.request": ["urlopen", "Request"],
    "requests": ["get", "post", "put", "delete", "head", "patch"],
    
    # 危险库调用
    "ctypes": ["CDLL", "cdll"],
    "docker": ["from_env", "DockerClient"],
    "kubernetes": ["client"],
    
    # 进程和线程
    "multiprocessing": ["Process", "Pool"],
    "threading": ["Thread"],
    "pty": ["spawn"],
    
    # 序列化（可能用于代码注入）
    "pickle": ["load", "loads"],
    "yaml": ["load", "unsafe_load"],
    "marshal": ["load", "loads"],
}

# 定义内置敏感函数
BUILTIN_SENSITIVE = set([
    "eval", "exec", "compile", "__import__", "globals", "locals", 
    "getattr", "setattr", "delattr", "open"
])

# 将CONTAINER_ESCAPE_MODULES中的所有敏感函数添加到BUILTIN_SENSITIVE中
for module, functions in CONTAINER_ESCAPE_MODULES.items():
    for function in functions:
        BUILTIN_SENSITIVE.add(f"{module}.{function}")

# ==================== 容器逃逸攻击模式定义 ====================

# 定义容器逃逸攻击模式（基于检测规则手册5.2节）
CONTAINER_ESCAPE_PATTERNS = {
    # CE-CMD: 系统命令执行
    "cmd_sensitive_binary": r"(nsenter|capsh|mount|umount|docker|kubectl|crictl)",
    "cmd_reverse_shell": r"(os\.dup2\s*\(.*fileno.*[012]\)|pty\.spawn\s*\(['\"]\/bin\/(sh|bash))",
    "cmd_fork_bomb": r"os\.fork\s*\(\)",
    
    # CE-FILE: 文件与路径操作
    "file_container_fingerprint": r"(\.dockerenv|/proc/1/cgroup|/proc/self/status|/proc/self/mountinfo)",
    "file_host_sensitive": r"(/host/|/proc/1/|/var/run/docker\.sock|/var/run/containerd\.sock|/var/run/secrets)",
    "file_cgroup_kernel": r"(/sys/fs/cgroup|/proc/sys/kernel/core_pattern|release_agent|devices\.allow|notify_on_release)",
    "file_proc_self": r"(/proc/self/exe|/proc/self/mem|/proc/self/fd/)",
    "file_k8s_secrets": r"(/var/run/secrets/kubernetes\.io/serviceaccount|\.kube/config)",
    
    # CE-LIB: 危险库调用
    "lib_ctypes_libc": r"ctypes\.(CDLL|cdll)\s*\(['\"]libc\.so",
    "lib_syscall": r"(setns|unshare|mount|ptrace|madvise|splice|pipe|mmap|mknod)",
    "lib_docker_sdk": r"docker\.(from_env|DockerClient)",
    "lib_k8s_client": r"kubernetes\.client\.\w+Api",
    
    # CE-NET: 网络行为
    "net_cloud_metadata": r"(169\.254\.169\.254|100\.100\.100\.200|metadata\.google\.internal)",
    "net_k8s_ports": r"(:10250|:10255|:2375|:2379|:6443|KUBERNETES_SERVICE_HOST)",
    "net_localhost_bypass": r"(127\.0\.0\.1|localhost).*(:10250|:10255)",
    
    # 容器逃逸特定漏洞利用
    "exploit_dirty_cow": r"(madvise.*MADV_DONTNEED|MAP_PRIVATE.*PROT_READ)",
    "exploit_dirty_pipe": r"(splice|pipe.*F_SETPIPE_SZ|PIPE_BUF_FLAG)",
    "exploit_runc": r"(#!/proc/self/exe|/proc/\d+/exe.*O_WRONLY)",
    "exploit_cgroup_release": r"(release_agent|notify_on_release.*cgroup\.procs)",
    "exploit_hotplug": r"(/sys/kernel/uevent_helper|/proc/sys/kernel/hotplug|kobject_uevent)",
    
    # K8s 持久化
    "k8s_privileged_pod": r"(hostNetwork|hostPID|hostIPC|privileged.*true)",
    "k8s_hostpath_mount": r"(hostPath.*path:\s*/|volumeMounts)",
    "k8s_service_account": r"(serviceAccountName|automountServiceAccountToken)",
    "k8s_external_ips": r"externalIPs",
    
    # 凭证窃取
    "cred_cloud_ak": r"(AKIA[0-9A-Z]{16}|AliyunAccessKey|SK[0-9a-zA-Z]{32})",
    "cred_ssh_key": r"-----BEGIN (RSA|OPENSSH) PRIVATE KEY-----",
    "cred_docker_config": r"(\.docker/config\.json|\.dockercfg)",
    
    # DoS 攻击
    "dos_infinite_loop": r"while\s+(True|1):",
    "dos_resource_exhaust": r"(multiprocessing\.Process|threading\.Thread).*while",
}

# ==================== 容器逃逸风险等级定义 ====================

# 定义检测规则的风险等级（对应检测规则手册5.2节）
ESCAPE_RISK_RULES = {
    "CRITICAL": {
        "CE-FILE-01": ["file_container_fingerprint"],
        "CE-FILE-02": ["file_host_sensitive"],
        "CE-LIB-01": ["lib_ctypes_libc"],
        "CE-LIB-02": ["lib_syscall"],
    },
    "HIGH": {
        "CE-CMD-01": ["cmd_sensitive_binary"],
        "CE-CMD-02": ["cmd_reverse_shell"],
        "CE-FILE-03": ["file_cgroup_kernel"],
        "CE-FILE-04": ["file_proc_self"],
        "CE-LIB-03": ["lib_docker_sdk"],
        "CE-LIB-04": ["lib_k8s_client"],
        "CE-NET-01": ["net_cloud_metadata"],
        "CE-NET-02": ["net_k8s_ports"],
    },
    "MEDIUM": {
        "CE-CMD-03": ["cmd_fork_bomb"],
        "CE-NET-03": ["net_localhost_bypass"],
    }
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
    """容器逃逸语义特征提取器 - 直接从Python源代码提取特征"""
    
    def __init__(self, source_file: str):
        """
        初始化容器逃逸特征提取器
        
        参数:
            source_file: Python源代码文件路径
        """
        self.source_file = source_file  # 文件路径
        self.source_code = ""  # 源代码
        self.ast_tree = None  # ast树
        
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
    
    def extract_features(self) -> np.ndarray:
        """
        提取容器逃逸语义特征向量
        
        返回:
            128维容器逃逸语义特征向量
        """
        # 1. 提取容器逃逸敏感函数频次特征（32维）
        sensitive_features = self._extract_escape_function_features()
        
        # 2. 提取攻击模式序列特征（64维）
        pattern_features = self._extract_attack_pattern_features()
        
        # 3. 提取容器逃逸路径和配置特征（32维）
        path_features = self._extract_path_config_features()
        
        # 合并特征
        features = np.concatenate([sensitive_features, pattern_features, path_features])
        
        return features
    
    def _extract_escape_function_features(self) -> np.ndarray:
        """
        提取容器逃逸敏感函数频次特征
        
        返回:
            32维容器逃逸敏感函数频次特征向量
        """
        # 初始化特征向量
        features = np.zeros(32)
        
        # 定义容器逃逸函数类别（共8类，对应攻击阶段）
        categories = [
            "system_commands",     # os.system, subprocess.*, nsenter, mount
            "process_control",     # os.fork, os.dup2, pty.spawn
            "dangerous_libs",      # ctypes.CDLL, docker.from_env, kubernetes.client
            "network_recon",       # socket.connect, requests.get (metadata服务)
            "file_access",         # open (敏感路径), os.path.exists
            "kernel_syscalls",     # setns, unshare, mount, ptrace (通过ctypes)
            "container_runtime",   # docker/containerd相关操作
            "k8s_operations"       # kubernetes API调用
        ]
        
        # 遍历AST查找敏感函数调用
        sensitive_calls = self._find_sensitive_calls(self.ast_tree)
        
        # 统计每个类别的调用次数
        category_counts = {cat: 0 for cat in categories}
        
        for call in sensitive_calls:
            if any(cmd in call for cmd in ["os.system", "subprocess.", "commands."]):
                category_counts["system_commands"] += 1
            elif any(proc in call for proc in ["os.fork", "os.dup2", "pty.spawn", "multiprocessing.", "threading."]):
                category_counts["process_control"] += 1
            elif any(lib in call for lib in ["ctypes.", "docker.", "kubernetes."]):
                category_counts["dangerous_libs"] += 1
            elif any(net in call for net in ["socket.", "urllib.", "requests."]):
                category_counts["network_recon"] += 1
            elif call in ["open"] or "open" in call:
                category_counts["file_access"] += 1
            elif any(syscall in call for syscall in ["setns", "unshare", "mount", "ptrace", "madvise", "splice"]):
                category_counts["kernel_syscalls"] += 1
            elif "docker" in call.lower() or "containerd" in call.lower():
                category_counts["container_runtime"] += 1
            elif "kubernetes" in call.lower() or "k8s" in call.lower():
                category_counts["k8s_operations"] += 1
        
        # 为每个类别分配4个特征位置
        for i, category in enumerate(categories):
            count = category_counts[category]
            scaled_count = np.log1p(count) if count > 0 else 0
            total_calls = len(sensitive_calls) if sensitive_calls else 1
            
            features[i * 4:i * 4 + 4] = [
                1.0 if count > 0 else 0.0,  # 是否存在该类别的调用
                scaled_count,               # 调用次数（对数缩放）
                count / total_calls,        # 相对频率
                min(scaled_count ** 2, 10.0)  # 平方项（限制上限）
            ]
        
        return features
    
    def _find_sensitive_calls(self, root_node: Any) -> List[str]:
        """
        从AST中查找敏感函数调用
        
        参数:
            root_node: AST根节点
            
        返回:
            敏感函数调用列表
        """
        sensitive_calls = []
        
        # 使用ast.walk遍历所有节点
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
                        print(f"发现敏感函数调用: {func_name}")
        
        print(f"总共找到 {len(sensitive_calls)} 个敏感函数调用")
        return sensitive_calls
    
    def _get_function_name_from_ast(self, call_node: ast.Call) -> Optional[str]:
        """
        从ast.Call节点中提取函数名
        
        参数:
            call_node: ast.Call节点
            
        返回:
            函数名字符串或None
        """
        func = call_node.func
        
        # 处理简单函数调用：func()
        if isinstance(func, ast.Name):
            return func.id
        
        # 处理属性调用：module.func() 或 obj.method()
        elif isinstance(func, ast.Attribute):
            # 尝试构建完整的调用链
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
                # 如果无法完全解析，至少返回最后的属性名
                return func.attr
        
        return None
    
    def _extract_attack_pattern_features(self) -> np.ndarray:
        """
        提取容器逃逸攻击模式特征
        
        返回:
            64维攻击模式特征向量
        """
        # 初始化特征向量
        features = np.zeros(64)
        
        # 直接使用源代码
        code_to_analyze = self.source_code
        
        if not code_to_analyze:
            print("警告：没有可用的源代码，返回零攻击模式特征向量")
            return features
        
        # 定义攻击模式类别（共16类，每类4个特征）
        pattern_categories = {
            # 系统命令执行类
            "cmd_execution": ["cmd_sensitive_binary", "cmd_reverse_shell", "cmd_fork_bomb"],
            
            # 文件路径访问类
            "file_fingerprint": ["file_container_fingerprint", "file_host_sensitive"],
            "file_escape": ["file_cgroup_kernel", "file_proc_self", "file_k8s_secrets"],
            
            # 危险库调用类
            "lib_dangerous": ["lib_ctypes_libc", "lib_syscall"],
            "lib_container": ["lib_docker_sdk", "lib_k8s_client"],
            
            # 网络侦察类
            "net_recon": ["net_cloud_metadata", "net_k8s_ports", "net_localhost_bypass"],
            
            # 内核漏洞利用类
            "exploit_kernel": ["exploit_dirty_cow", "exploit_dirty_pipe", "exploit_hotplug"],
            "exploit_runtime": ["exploit_runc", "exploit_cgroup_release"],
            
            # K8s持久化类
            "k8s_privilege": ["k8s_privileged_pod", "k8s_hostpath_mount"],
            "k8s_persistence": ["k8s_service_account", "k8s_external_ips"],
            
            # 凭证窃取类
            "cred_theft": ["cred_cloud_ak", "cred_ssh_key", "cred_docker_config"],
            
            # DoS攻击类
            "dos_attack": ["dos_infinite_loop", "dos_resource_exhaust"],
            
            # 其他高危模式
            "other_high_risk_1": [],
            "other_high_risk_2": [],
            "other_high_risk_3": [],
            "other_high_risk_4": []
        }
        
        # 统计每种模式的匹配次数
        pattern_counts = {}
        for pattern_name, pattern_regex in CONTAINER_ESCAPE_PATTERNS.items():
            matches = re.findall(pattern_regex, code_to_analyze, re.IGNORECASE)
            pattern_counts[pattern_name] = len(matches)
            if len(matches) > 0:
                print(f"检测到容器逃逸模式 '{pattern_name}': {len(matches)}个匹配")
        
        # 为每个类别计算特征
        for i, (category, patterns) in enumerate(pattern_categories.items()):
            if i >= 16:  # 只使用前16个类别
                break
                
            # 计算该类别的总匹配次数  攻击模式1命中数 + 攻击模式2命中数 + ... + 攻击模式n命中数
            category_count = sum(pattern_counts.get(pattern, 0) for pattern in patterns)
            
            # 计算该类别中匹配的模式数量  命中的攻击模式数 n
            matched_patterns = sum(1 for pattern in patterns if pattern_counts.get(pattern, 0) > 0)
            
            # 计算最大匹配次数
            max_count = max([pattern_counts.get(pattern, 0) for pattern in patterns], default=0)
            
            # 计算平均匹配次数
            avg_count = category_count / len(patterns) if patterns else 0
            
            # 填充特征向量
            features[i * 4:i * 4 + 4] = [
                1.0 if category_count > 0 else 0.0,  # 是否存在该类别的模式
                np.log1p(category_count),            # 总匹配次数（对数缩放）
                matched_patterns / len(patterns) if patterns else 0,  # 匹配模式比例
                np.log1p(max_count)                  # 最大匹配次数（对数缩放）
            ]
        
        return features
    
    def _extract_path_config_features(self) -> np.ndarray:
        """
        提取容器逃逸路径和配置特征
        
        返回:
            32维路径和配置特征向量
        """
        # 初始化特征向量
        features = np.zeros(32)
        
        # 直接使用源代码
        code_to_analyze = self.source_code
        
        if not code_to_analyze:
            return features
        
        # 定义敏感路径类别（共8类）
        path_categories = {
            "container_runtime_paths": [
                r"/var/run/docker\.sock",
                r"/var/run/containerd\.sock",
                r"/run/containerd",
            ],
            "proc_sensitive_paths": [
                r"/proc/1/",
                r"/proc/self/exe",
                r"/proc/self/mem",
                r"/proc/self/mountinfo",
            ],
            "cgroup_paths": [
                r"/sys/fs/cgroup",
                r"release_agent",
                r"notify_on_release",
                r"devices\.allow",
            ],
            "k8s_secret_paths": [
                r"/var/run/secrets/kubernetes\.io",
                r"\.kube/config",
                r"serviceaccount/token",
            ],
            "host_mount_paths": [
                r"/host/",
                r"hostPath",
                r"volumeMounts",
            ],
            "kernel_config_paths": [
                r"/proc/sys/kernel",
                r"/sys/kernel/uevent_helper",
                r"core_pattern",
            ],
            "container_fingerprint_paths": [
                r"\.dockerenv",
                r"/proc/1/cgroup",
                r"/proc/self/cgroup",
            ],
            "credential_paths": [
                r"\.docker/config\.json",
                r"\.aws/credentials",
                r"\.ssh/id_rsa",
            ],
        }
        
        # 统计每个类别的路径访问次数
        for i, (category, patterns) in enumerate(path_categories.items()):
            category_count = 0  # 总匹配数
            matched_patterns = 0  # 匹配到的模式种类数
            max_count = 0  # 单项最高频次
            
            for pattern in patterns:
                matches = re.findall(pattern, code_to_analyze, re.IGNORECASE)
                count = len(matches)
                category_count += count
                if count > 0:
                    matched_patterns += 1
                    max_count = max(max_count, count)
            
            # 填充特征向量
            features[i * 4:i * 4 + 4] = [
                1.0 if category_count > 0 else 0.0,  # 是否访问该类别路径
                np.log1p(category_count),            # 访问次数（对数缩放）
                matched_patterns / len(patterns) if patterns else 0,  # 匹配路径比例
                np.log1p(max_count)                  # 最大访问次数（对数缩放）
            ]
        
        return features
    
    def _calculate_entropy(self, text: str) -> float:
        """
        计算文本的熵值，作为混淆复杂度的指标
        
        参数:
            text: 输入文本
            
        返回:
            熵值（比特/字符）
        """
        if not text:
            return 0.0
        
        # 计算每个字符的频率
        char_freq = {}
        for char in text:
            if char in char_freq:
                char_freq[char] += 1
            else:
                char_freq[char] = 1
        
        # 计算文本长度
        length = len(text)
        
        # 计算熵值
        entropy = 0.0
        for freq in char_freq.values():
            probability = freq / length
            entropy -= probability * np.log2(probability)
        
        return entropy
    
    def detect_container_escape_risk(self) -> Dict[str, Any]:
        """
        检测代码的容器逃逸风险
        
        返回:
            包含风险评估结果的字典
        """
        code_to_analyze = self.source_code
        
        if not code_to_analyze:
            return {"risk_level": "UNKNOWN", "reason": "无可分析代码"}
        
        # 检测各类容器逃逸模式
        risk_indicators = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": []
        }
        
        # 遍历所有检测规则
        for risk_level, rules in ESCAPE_RISK_RULES.items():  # 检测规则的风险等级字典
            for rule_id, pattern_names in rules.items():
                for pattern_name in pattern_names:
                    if pattern_name in CONTAINER_ESCAPE_PATTERNS:  # 容器逃逸攻击模式字典
                        pattern = CONTAINER_ESCAPE_PATTERNS[pattern_name]
                        matches = re.findall(pattern, code_to_analyze, re.IGNORECASE)
                        if matches:
                            risk_indicators[risk_level].append({
                                "rule_id": rule_id,
                                "pattern": pattern_name,
                                "matches": len(matches),
                                "samples": matches[:3]  # 只保留前3个样本
                            })
        
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
        if risk_indicators["CRITICAL"]:
            summary.append(f"发现 {len(risk_indicators['CRITICAL'])} 个严重风险")
        if risk_indicators["HIGH"]:
            summary.append(f"发现 {len(risk_indicators['HIGH'])} 个高风险")
        if risk_indicators["MEDIUM"]:
            summary.append(f"发现 {len(risk_indicators['MEDIUM'])} 个中等风险")
        
        result = {
            "risk_level": overall_risk,
            "risk_score": float(risk_score),  # 确保是Python float
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
        检测代码是否使用了混淆技术
        
        返回:
            包含混淆检测结果的字典
        """
        code_to_analyze = self.source_code
        
        if not code_to_analyze:
            return {"obfuscated": False, "reason": "无可分析代码"}
        
        # 计算熵值
        entropy = float(self._calculate_entropy(code_to_analyze))
        
        # 计算平均行长度
        lines = [line for line in code_to_analyze.split('\n') if line.strip()]
        avg_line_length = float(sum(len(line) for line in lines) / len(lines) if lines else 0)
        
        # 检测混淆特征
        obfuscation_indicators = {
            "高熵值": bool(entropy > 5.0),
            "长行": bool(avg_line_length > 100),
            "base64编码": bool(re.search(r'base64\.(b64decode|decodestring)', code_to_analyze)),
            "eval/exec": bool(re.search(r'eval\(|exec\(', code_to_analyze)),
            "变量名混淆": bool(re.search(r'\b[a-zA-Z]{1,2}\d*\b', code_to_analyze) and 
                           not re.search(r'def\s+[a-zA-Z]{3,}', code_to_analyze)),
            "字符串拼接": bool(code_to_analyze.count('+') > 20 and code_to_analyze.count("'") > 20)
        }
        
        # 判断是否混淆
        is_obfuscated = bool(sum(1 for val in obfuscation_indicators.values() if val) >= 2)
        
        reasons = [key for key, val in obfuscation_indicators.items() if val]
        
        result = {
            "obfuscated": is_obfuscated,
            "entropy": entropy,
            "avg_line_length": avg_line_length,
            "indicators": obfuscation_indicators,
            "reasons": reasons
        }
        
        if is_obfuscated:
            print(f"检测到代码混淆，原因: {', '.join(reasons)}")
        
        return result
    
    def save_features(self, output_file: str, include_risk_report: bool = True) -> None:
        """
        保存特征向量到文件，并可选地生成风险评估报告
        
        参数:
            output_file: 输出文件路径
            include_risk_report: 是否生成风险评估报告
        """
        features = self.extract_features()  #! 提取容器逃逸语义特征向量

        np.save(output_file, features)
        print(f"容器逃逸语义特征向量已保存至: {output_file}")
        
        # 生成风险评估报告
        if include_risk_report:
            risk_result = self.detect_container_escape_risk()  #! 检测代码的容器逃逸风险
            report_file = output_file.replace('.npy', '_risk_report.json')
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(risk_result, indent=2, ensure_ascii=False, cls=NumpyEncoder, fp=f)
            
            print(f"容器逃逸风险评估报告已保存至: {report_file}")
            print(f"风险等级: {risk_result['risk_level']}, 风险分数: {risk_result['risk_score']}")


def process_file(source_file: str, output_file: Optional[str] = None,
                include_risk_report: bool = True) -> None:
    """
    处理Python源代码文件并提取容器逃逸语义特征
    
    参数:
        source_file: Python源代码文件路径
        output_file: 输出文件路径（可选）
        include_risk_report: 是否生成风险评估报告
    """
    # 确定输出文件名
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(source_file))[0]
        output_file = f"{base_name}_container_escape_features.npy"
    
    # 提取特征
    print("=" * 60)
    print("容器逃逸静态检测 - 语义特征提取工具")
    print("=" * 60)
    print(f"输入文件: {source_file}")
    print(f"输出文件: {output_file}")
    
    extractor = ContainerEscapeFeatureExtractor(source_file)  # 初始化容器逃逸特征提取器
    
    # 检测容器逃逸风险
    print("\n[1/3] 检测容器逃逸风险...")
    escape_risk = extractor.detect_container_escape_risk()
    
    # 检测代码混淆
    print("\n[2/3] 检测代码混淆...")
    obfuscation_result = extractor.detect_obfuscation()
    
    # 提取并保存特征
    print("\n[3/3] 提取语义特征向量...")
    extractor.save_features(output_file, include_risk_report)
    
    print("\n" + "=" * 60)
    print("处理完成！")
    print("=" * 60)


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(
        description="容器逃逸静态检测 - 直接从Python源代码提取语义特征向量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python semantic_feature_extractor.py sample.py
  python semantic_feature_extractor.py sample.py -o output_features.npy
  python semantic_feature_extractor.py sample.py --no-report
  
  # 批量处理
  python semantic_feature_extractor.py *.py
        """
    )

    parser.add_argument("source_file", help="Python源代码文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（可选）")
    parser.add_argument("--no-report", action="store_true", help="不生成风险评估报告")  #! 记住：出现--no-report才是True
    
    args = parser.parse_args()
    
    process_file(
        args.source_file,     
        args.output,
        include_risk_report=not args.no_report
    )


if __name__ == "__main__":
    main()
