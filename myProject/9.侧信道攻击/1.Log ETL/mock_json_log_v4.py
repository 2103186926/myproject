# mock_json_log_v4.py
import json
import time
import random
import uuid
import numpy as np
import argparse
from datetime import datetime, timedelta

class OceanLogSimulatorV4:
    def __init__(self, num_jobs=100, output_file="ocean_security_audit_v4.jsonl"):
        self.num_jobs = num_jobs
        self.output_file = output_file
        self.base_time = datetime.now() - timedelta(hours=24)
        
        # 类别分布: 70% 正常, 15% 缓存攻击, 15% 资源争用
        self.ratios = {"normal": 0.70, "cache_attack": 0.15, "contention_attack": 0.15}
        
        self.users = [f"usr-research-{i:03d}" for i in range(1, 50)]
        self.attacker_users = [f"usr-guest-{i:03d}" for i in range(900, 910)]

    def _create_log_entry(self, job_config, timestamp, phase, event_type, msg, metrics, context):
        return {
            "timestamp": timestamp.isoformat() + "Z",
            "metadata": {
                "log_version": "2.1", # 版本升级
                "cluster_region": "cn-north-ocean-1",
                "node_id": f"node-{random.randint(1, 20):02d}",
                "job_id": job_config["job_id"],
                "user_id": job_config["user_id"],
                "image": "ocean-modelling-suite:v3.0"
            },
            "phase": phase,
            "event": {"type": event_type, "message": msg},
            "context": context,
            "metrics": metrics,
            "label": job_config["label"]
        }

    def _simulate_normal_sequence(self, job_config):
        """
        正常科研任务：
        - 内存：加载数据时升高，计算时稳定
        - L3 Miss：处理大数组时较高且随机
        - IPC：科学计算通常较高 (1.0 - 2.0)
        """
        logs = []
        curr_time = self.base_time + timedelta(seconds=job_config["start_delay_sec"])
        steps = random.randint(50, 150)
        
        # 模拟内存状态
        current_mem = random.randint(1, 4) * 1024 * 1024 * 1024 # 1GB - 4GB
        
        for i in range(steps):
            # 正常任务间隔大
            curr_time += timedelta(milliseconds=random.randint(200, 3000))
            
            # 模拟 IO 和 计算的混合
            is_io = random.random() < 0.3
            
            if is_io:
                # IO 密集型
                duration = int(np.random.normal(50 * 1000 * 1000, 10 * 1000 * 1000)) # ~50ms
                io_bytes = random.randint(10*1024*1024, 100*1024*1024)
                l3_miss = random.uniform(0.05, 0.15) # IO时缓存未命中率一般
                ipc = random.uniform(0.2, 0.5) # IO等待导致 IPC 低
            else:
                # 计算密集型
                duration = int(np.random.normal(500 * 1000, 100 * 1000)) # ~0.5ms
                io_bytes = 0
                l3_miss = random.uniform(0.1, 0.4) # 大矩阵运算 L3 Miss 较高
                ipc = random.uniform(1.5, 2.5) # SIMD 指令导致 IPC 高
            
            logs.append(self._create_log_entry(
                job_config, curr_time, "COMPUTE", "DATA_PROCESS", 
                "Matrix multiplication step" if not is_io else "Loading checkpoint",
                metrics={
                    "duration_ns": duration,
                    "cpu_usage_pct": round(random.uniform(40, 90), 2),
                    "io_bytes": io_bytes,
                    "mem_usage_bytes": current_mem,
                    "l3_miss_rate": round(l3_miss, 4),
                    "ipc": round(ipc, 2)
                },
                context={"step": i}
            ))
        return logs

    def _simulate_cache_attack_sequence(self, job_config):
        """
        缓存探测攻击 (Prime + Probe)：
        - Phase 1 (Prime): 大内存分配，顺序写入 -> L3 Miss 低 (预取)，IPC 低，内存极高
        - Phase 2 (Probe): 高频随机访问 -> L3 Miss 剧烈震荡 (0% 或 100%)，IPC 极低 (Stall)
        """
        logs = []
        curr_time = self.base_time + timedelta(seconds=job_config["start_delay_sec"])
        
        # 完整的攻击轮次 (Prime -> Probe -> Prime -> Probe ...)
        rounds = random.randint(5, 10)
        
        for r in range(rounds):
            # === Phase 1: Prime (填充缓存) ===
            # 分配大于 L3 Cache 的内存 (如 256MB)
            prime_mem = 256 * 1024 * 1024 
            curr_time += timedelta(milliseconds=50) # Prime 需要一点时间
            
            logs.append(self._create_log_entry(
                job_config, curr_time, "SETUP", "MEM_ALLOC", 
                "Allocating prime buffer",
                metrics={
                    "duration_ns": int(np.random.normal(50 * 1000 * 1000, 5000)), # 50ms
                    "cpu_usage_pct": 100.0,
                    "io_bytes": 0,
                    "mem_usage_bytes": prime_mem,
                    "l3_miss_rate": 0.01, # 顺序写入，硬件预取导致 Miss 率低
                    "ipc": 0.8 
                },
                context={"action": "prime", "round": r}
            ))
            
            # === Phase 2: Probe (探测) ===
            # 高频采样 50-100 次
            probe_steps = random.randint(50, 100)
            for i in range(probe_steps):
                curr_time += timedelta(microseconds=random.randint(10, 50)) # 极快间隔
                
                # 模拟 Cache Hit/Miss
                is_hit = random.random() > 0.4
                if is_hit:
                    duration = int(np.random.normal(80, 5)) # 80ns
                    l3_miss = 0.0
                else:
                    duration = int(np.random.normal(300, 20)) # 300ns
                    l3_miss = 1.0 # 强制 Miss
                
                logs.append(self._create_log_entry(
                    job_config, curr_time, "ANALYSIS", "POINT_QUERY", 
                    "Probing memory address",
                    metrics={
                        "duration_ns": duration,
                        "cpu_usage_pct": 100.0,
                        "io_bytes": 0,
                        "mem_usage_bytes": prime_mem, # 内存保持高位
                        "l3_miss_rate": l3_miss,      # 特征：0/1 跳变
                        "ipc": 0.1                    # 特征：因 Cache Miss 导致 CPU 流水线停顿，IPC 极低
                    },
                    context={"target": "addr_0x...", "result": "hit" if is_hit else "miss"}
                ))
                
        return logs

    def _simulate_contention_attack_sequence(self, job_config):
        """
        资源争用攻击：
        - 特征：内存低，IPC 呈现规律性，L3 Miss 低
        - 这里的 Duration 漂移是核心特征
        """
        logs = []
        curr_time = self.base_time + timedelta(seconds=job_config["start_delay_sec"])
        steps = random.randint(100, 200)
        
        mem_usage = 10 * 1024 * 1024 # 仅 10MB，轻量级
        
        for i in range(steps):
            curr_time += timedelta(milliseconds=500) # 固定 0.5s 心跳
            
            # 全局负载正弦波
            load_factor = (np.sin(curr_time.timestamp() / 20.0) + 1) / 2
            
            base_dur = 2000 * 1000 # 2ms
            penalty = int(load_factor * 5 * 1000 * 1000)
            duration = base_dur + penalty + int(np.random.normal(0, 10000))
            
            logs.append(self._create_log_entry(
                job_config, curr_time, "SYNC", "WORKER_WAIT", 
                "Heartbeat check",
                metrics={
                    "duration_ns": duration,
                    "cpu_usage_pct": 10.0,
                    "io_bytes": 0,
                    "mem_usage_bytes": mem_usage,
                    "l3_miss_rate": 0.05, # 很低
                    "ipc": 0.4            # 低，因为在做无意义循环或Sleep
                },
                context={"status": "waiting"}
            ))
            
        return logs

    def run(self):
        # ... (与 v3 类似的调度逻辑) ...
        # 省略部分代码以节省篇幅，核心逻辑不变：
        # 生成 Job Config -> 生成 Logs -> 全局排序 -> 写入文件
        configs = []
        n_normal = int(self.num_jobs * 0.7)
        n_cache = int(self.num_jobs * 0.15)
        n_cont = self.num_jobs - n_normal - n_cache
        
        # 正常
        for _ in range(n_normal):
            configs.append({"job_id": f"job-sci-{uuid.uuid4().hex[:6]}", "user_id": "usr-sci", "type": "normal", "label": 0, "start_delay_sec": random.randint(0, 86400)})
        # 缓存
        for _ in range(n_cache):
            configs.append({"job_id": f"job-atk-c-{uuid.uuid4().hex[:6]}", "user_id": "usr-atk", "type": "cache", "label": 1, "start_delay_sec": random.randint(0, 86400)})
        # 争用
        for _ in range(n_cont):
            configs.append({"job_id": f"job-atk-r-{uuid.uuid4().hex[:6]}", "user_id": "usr-atk", "type": "contention", "label": 2, "start_delay_sec": random.randint(0, 86400)})
            
        all_logs = []
        print(f"[*] Generating {self.num_jobs} jobs...")
        for cfg in configs:
            if cfg['type'] == 'normal': all_logs.extend(self._simulate_normal_sequence(cfg))
            elif cfg['type'] == 'cache': all_logs.extend(self._simulate_cache_attack_sequence(cfg))
            elif cfg['type'] == 'contention': all_logs.extend(self._simulate_contention_attack_sequence(cfg))
            
        all_logs.sort(key=lambda x: x['timestamp'])
        
        with open(self.output_file, 'w') as f:
            for log in all_logs:
                f.write(json.dumps(log) + "\n")
        print(f"[+] Done. Saved to {self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=100)
    args = parser.parse_args()
    OceanLogSimulatorV4(num_jobs=args.jobs).run()