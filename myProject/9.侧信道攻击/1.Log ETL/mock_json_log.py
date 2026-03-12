# mock_json_log_v3.py
import json
import time
import random
import uuid
import numpy as np
import argparse
from datetime import datetime, timedelta

class OceanLogSimulatorV3:
    def __init__(self, num_jobs=100, output_file="ocean_security_audit_v3.jsonl"):
        self.num_jobs = num_jobs
        self.output_file = output_file
        # 模拟基准时间：从昨天开始
        self.base_time = datetime.now() - timedelta(hours=24)
        
        # 定义分布比例
        self.ratios = {
            "normal": 0.70,
            "cache_attack": 0.15,
            "contention_attack": 0.15
        }
        
        # 用户池
        self.users = [f"usr-research-{i:03d}" for i in range(1, 50)]
        self.attacker_users = [f"usr-guest-{i:03d}" for i in range(900, 910)]

    def _generate_job_config(self):
        """生成任务池配置"""
        configs = []
        
        n_normal = int(self.num_jobs * self.ratios["normal"])
        n_cache = int(self.num_jobs * self.ratios["cache_attack"])
        n_contention = int(self.num_jobs * self.ratios["contention_attack"])
        
        # 补齐剩余的（因取整可能少几个）
        remaining = self.num_jobs - (n_normal + n_cache + n_contention)
        n_normal += remaining
        
        print(f"[*] 任务分布计划: 总数={self.num_jobs}")
        print(f"    - 正常科研任务: {n_normal}")
        print(f"    - 缓存探测攻击: {n_cache}")
        print(f"    - 资源争用攻击: {n_contention}")
        
        # 1. 正常任务配置
        for _ in range(n_normal):
            configs.append({
                "job_id": f"job-sci-{uuid.uuid4().hex[:6]}",
                "user_id": random.choice(self.users),
                "type": "normal",
                "label": 0,
                "start_delay_sec": random.randint(0, 86400) # 24小时内随机启动
            })
            
        # 2. 缓存攻击配置
        for _ in range(n_cache):
            configs.append({
                "job_id": f"job-atk-cache-{uuid.uuid4().hex[:6]}",
                "user_id": random.choice(self.attacker_users),
                "type": "cache_attack",
                "label": 1,
                "start_delay_sec": random.randint(0, 86400)
            })
            
        # 3. 资源争用攻击配置
        for _ in range(n_contention):
            configs.append({
                "job_id": f"job-atk-res-{uuid.uuid4().hex[:6]}",
                "user_id": random.choice(self.attacker_users),
                "type": "contention_attack",
                "label": 2,
                "start_delay_sec": random.randint(0, 86400)
            })
            
        random.shuffle(configs)
        return configs

    def _create_log_entry(self, job_config, timestamp, phase, event_type, msg, metrics, context):
        """构造单条日志"""
        return {
            "timestamp": timestamp.isoformat() + "Z",
            "metadata": {
                "log_version": "2.0",
                "cluster_region": "cn-north-ocean-1",
                "node_id": f"node-{random.randint(1, 20):02d}",
                "job_id": job_config["job_id"],
                "user_id": job_config["user_id"],
                "image": "ocean-modelling-suite:v2.5"
            },
            "phase": phase,
            "event": {
                "type": event_type,
                "message": msg
            },
            "context": context,
            "metrics": metrics,
            "label": job_config["label"]
        }

    def _simulate_normal_sequence(self, job_config):
        """生成一个正常任务的完整日志序列"""
        logs = []
        curr_time = self.base_time + timedelta(seconds=job_config["start_delay_sec"])
        
        # 正常任务步数：50 到 150 步
        steps = random.randint(50, 150)
        
        for i in range(steps):
            # 正常耗时：毫秒级，受IO影响波动大
            # 均值 15ms ~ 25ms
            base_duration = random.randint(15000, 25000) * 1000 # ns
            io_noise = int(np.random.normal(0, 5000 * 1000))
            duration = max(1000, base_duration + io_noise)
            
            # 正常间隔：随机性大 (100ms - 2s)
            interval_ms = random.randint(100, 2000)
            curr_time += timedelta(milliseconds=interval_ms)
            
            logs.append(self._create_log_entry(
                job_config, curr_time, "COMPUTE", "DATA_PROCESS", 
                "Processing NetCDF chunk",
                metrics={
                    "duration_ns": duration,
                    "cpu_usage_pct": round(random.uniform(30, 70), 2),
                    "io_bytes": random.randint(1024*1024, 1024*1024*10) # 有IO
                },
                context={"op": "interpolation", "chunk": i}
            ))
            
        return logs

    def _simulate_cache_attack_sequence(self, job_config):
        """生成一个缓存探测攻击的完整日志序列"""
        logs = []
        curr_time = self.base_time + timedelta(seconds=job_config["start_delay_sec"])
        
        # 攻击任务步数：通常很多，为了统计显著性 (200 - 500 步)
        steps = random.randint(200, 500)
        
        for i in range(steps):
            # 攻击特征1：极高的频率 (间隔极短, 50us - 500us)
            interval_us = random.randint(50, 500)
            curr_time += timedelta(microseconds=interval_us)
            
            # 攻击特征2：耗时呈双峰分布 (Hit vs Miss)
            if random.random() > 0.3:
                # Cache Hit: ~100ns, 极稳
                duration = int(np.random.normal(100, 5))
            else:
                # Cache Miss: ~500ns, 稍有波动
                duration = int(np.random.normal(500, 20))
            
            logs.append(self._create_log_entry(
                job_config, curr_time, "ANALYSIS", "POINT_QUERY", 
                "Querying grid value",
                metrics={
                    "duration_ns": max(10, duration),
                    "cpu_usage_pct": 99.8, # 跑满
                    "io_bytes": 0 # 无磁盘IO
                },
                context={"target": "sensitive_region", "idx": i}
            ))
            
        return logs

    def _simulate_contention_attack_sequence(self, job_config):
        """生成一个资源争用攻击的完整日志序列"""
        logs = []
        curr_time = self.base_time + timedelta(seconds=job_config["start_delay_sec"])
        
        # 步数
        steps = random.randint(100, 300)
        
        # 攻击特征1：固定的采样频率 (心跳间隔)
        heartbeat_interval = 0.5 # 0.5秒
        
        # 模拟受害者的负载波形 (全局时间的正弦波)
        # 使得不同时刻启动的攻击者看到的波形是一致的
        
        for i in range(steps):
            curr_time += timedelta(seconds=heartbeat_interval)
            
            # 计算全局负载 (基于时间戳)
            ts = curr_time.timestamp()
            # 周期 100秒
            global_stress = (np.sin(ts / 15.0) + 1) / 2 # 0.0 - 1.0
            
            # 攻击特征2：耗时随全局负载漂移
            base_ns = 1000 * 1000 # 1ms
            penalty_ns = global_stress * 8 * 1000 * 1000 # 最大加 8ms
            noise = np.random.normal(0, 50000) # 少量噪声
            
            duration = int(base_ns + penalty_ns + noise)
            
            logs.append(self._create_log_entry(
                job_config, curr_time, "SYNC", "WORKER_WAIT", 
                "Waiting for sync",
                metrics={
                    "duration_ns": duration,
                    "cpu_usage_pct": 5.0, # 低CPU
                    "io_bytes": 0
                },
                context={"status": "idle"}
            ))
            
        return logs

    def run(self):
        job_configs = self._generate_job_config()
        all_logs = []
        
        print(f"[*] 正在为 {len(job_configs)} 个任务生成日志序列...")
        
        for cfg in job_configs:
            if cfg["type"] == "normal":
                job_logs = self._simulate_normal_sequence(cfg)
            elif cfg["type"] == "cache_attack":
                job_logs = self._simulate_cache_attack_sequence(cfg)
            elif cfg["type"] == "contention_attack":
                job_logs = self._simulate_contention_attack_sequence(cfg)
            
            all_logs.extend(job_logs)
            
        # 关键步骤：按时间戳全局排序，模拟真实日志流
        print("[*] 正在按时间戳全局排序...")
        all_logs.sort(key=lambda x: x["timestamp"])
        
        print(f"[*] 写入文件: {self.output_file} (共 {len(all_logs)} 条日志)")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for log in all_logs:
                f.write(json.dumps(log) + "\n")
                
        print("[+] 生成完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成海洋科学云计算侧信道攻击模拟日志")
    parser.add_argument("--jobs", type=int, default=100, help="要生成的总任务数 (默认: 100)")
    parser.add_argument("--output", type=str, default="ocean_security_audit.jsonl", help="输出文件名")
    
    args = parser.parse_args()
    
    simulator = OceanLogSimulatorV3(num_jobs=args.jobs, output_file=args.output)
    simulator.run()