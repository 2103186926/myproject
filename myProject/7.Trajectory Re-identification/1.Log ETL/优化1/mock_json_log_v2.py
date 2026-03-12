'''
这个脚本引入了 Confusing Normal（高混淆正常类）和 Stealthy Attack（隐蔽攻击类），并显著增加了时间步长。
'''
import json
import random
import uuid
import numpy as np
from datetime import datetime, timedelta

class OceanJsonLogGeneratorV2:
    def __init__(self):
        self.output_file = "ocean_task_logs.json"
        
    def _get_time(self, base_time, offset_seconds):
        return (base_time + timedelta(seconds=offset_seconds)).isoformat()

    def _generate_base_log(self, task_id, timestamp, component, event, level="INFO"):
        return {
            "timestamp": timestamp,
            "level": level,
            "component": component,
            "task_id": task_id,
            "event_type": event,
            "params": {},
            "metrics": {}
        }

    # ==========================================
    # 场景 A: 标准长周期正常任务 (Label 0)
    # 特征：由于数据量大，会被切分为很多个 Batch，序列很长，CPU平稳
    # ==========================================
    def generate_long_normal_task(self):
        task_id = f"job-nrm-long-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 1000))
        logs = []
        t = 0.0

        # 1. Start
        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        t += 0.5

        # 2. Fetch (大范围)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": random.randint(60, 180), "area_sqkm": 5000}
        log["metrics"] = {"data_size_mb": 500 + random.uniform(-50, 50)}
        logs.append(log)
        t += random.uniform(5, 10)

        # 3. Long Batch Process (模拟 10-30 个时间步)
        # 体现 LSTM 处理长序列的能力
        num_batches = random.randint(10, 30)
        for i in range(num_batches):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "BATCH_PROCESS")
            # 正常任务偶尔也会有 CPU 波动
            cpu_val = 40 + random.uniform(-10, 20)
            log["metrics"] = {
                "batch_id": i,
                "input_records": 5000,
                "output_records": 4800, # 聚合率不高
                "cpu_usage_pct": cpu_val,
                "duration_ms": 2000 + random.uniform(-200, 200)
            }
            logs.append(log)
            t += 2.5
            
            # 随机插入中间存档 (Checkpoint)，增加序列复杂性
            if i % 5 == 0 and i > 0:
                s_log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "CHECKPOINT_SAVE")
                s_log["metrics"] = {"file_size_kb": 200}
                logs.append(s_log)
                t += 1.0

        # 4. Export (大文件)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": 10000 + random.uniform(-1000, 1000), "format": "netcdf"}
        logs.append(log)
        
        return logs

    # ==========================================
    # 场景 B: 高混淆正常任务 (Label 0) -> "Gray Area"
    # 业务含义：稀有事件搜索（如寻找某次海难的黑匣子信号，或稀有鲸鱼叫声）
    # 混淆点：高过滤率（像攻击），输出文件小（像攻击），查询范围可能也小。
    # 区分点：CPU消耗不像攻击那么集中，处理逻辑是流式的。
    # ==========================================
    def generate_confusing_normal_task(self):
        task_id = f"job-nrm-rare-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 1000))
        logs = []
        t = 0.0

        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        t += 0.5

        # Fetch (可能是精确查询，混淆视听)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": random.randint(5, 20), "area_sqkm": 300} # 范围小，像攻击
        log["metrics"] = {"data_size_mb": 50}
        logs.append(log)
        t += 2.0

        # Process (高过滤率，但 CPU 正常)
        # 这种任务虽然由 input->output 变少，但通常是简单的 if-else 过滤，CPU 不会像 DTW 匹配那么高
        num_batches = random.randint(8, 15)
        for i in range(num_batches):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "STREAM_FILTER")
            log["metrics"] = {
                "batch_id": i,
                "input_records": 2000,
                "output_records": random.randint(0, 5), # 极低保留率 (像漏斗)
                "cpu_usage_pct": 30 + random.uniform(-5, 15), # 关键区分点：CPU 较低
                "duration_ms": 500 + random.uniform(0, 100)   # 关键区分点：耗时短
            }
            logs.append(log)
            t += 0.6

        # Export (小文件 CSV，极像攻击)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": 5 + random.uniform(0, 10), "format": "csv"}
        logs.append(log)
        
        return logs

    # ==========================================
    # 场景 C: 隐蔽攻击任务 (Label 1) -> "Stealthy Attack"
    # 手段：攻击者故意下载额外数据掩盖意图，分批次慢速处理防止 CPU 报警
    # ==========================================
    def generate_stealthy_attack_task(self):
        task_id = f"job-atk-stlth-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 1000))
        logs = []
        t = 0.0

        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        logs[-1]["params"]["job_name"] = "deep_learning_training" # 伪装
        t += 0.5

        # Fetch (故意扩大一点范围，掩盖意图)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": random.randint(15, 25), "area_sqkm": 800} 
        logs.append(log)
        t += 3.0

        # Filter (标准的漏斗)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "PRE_FILTER")
        log["metrics"] = {"input_records": 30000, "output_records": 10, "cpu_usage_pct": 35}
        logs.append(log)
        t += 1.0

        # Deep Analysis (隐蔽模式：增加 Time Step，降低单步 CPU)
        # 攻击者把 10 个候选者分成 10 次处理，每次处理加 sleep，让 CPU 看起来只有 60-70%
        candidates = 10
        for i in range(candidates):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "DEEP_ANALYSIS")
            # 混淆点：CPU 没那么高了，但耗时依然长（因为 sleep 了）
            log["metrics"] = {
                "batch_id": i,
                "input_records": 1,
                "output_records": 1,
                "cpu_usage_pct": 60 + random.uniform(-10, 15), # 降低特征显著性
                "duration_ms": 3000 + random.uniform(0, 1000)  # 耗时依然是痛点
            }
            logs.append(log)
            # 增加随机间隔
            t += random.uniform(3.0, 5.0)

        # Export
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": 20, "format": "encrypted_dat"} # 伪装格式
        logs.append(log)

        return logs

    def run(self, count=200):
        all_sequences = []
        print(f"[*] Generating {count} complex log sequences (Adding Gray Area samples)...")
        
        for _ in range(count):
            rand = random.random()
            if rand < 0.5:
                # 50% 正常 (其中 20% 是高混淆正常)
                if random.random() < 0.2:
                    seq = self.generate_confusing_normal_task()
                else:
                    seq = self.generate_long_normal_task()
                label = 0
            else:
                # 50% 攻击 (其中 40% 是隐蔽攻击)
                if random.random() < 0.4:
                    seq = self.generate_stealthy_attack_task()
                else:
                    # 标准攻击 (复用之前的逻辑，稍微拉长)
                    seq = self.generate_stealthy_attack_task() # 这里为了简化直接用隐蔽的，或者你可以保留原来的
                    # 为了保持多样性，稍微修改 metrics 让它像原来的“暴力”攻击
                    for log in seq:
                        if log["event_type"] == "DEEP_ANALYSIS":
                            log["metrics"]["cpu_usage_pct"] = 90 + random.uniform(0, 8)
                label = 1
            
            all_sequences.append({"label": label, "logs": seq})

        with open(self.output_file, 'w') as f:
            json.dump(all_sequences, f, indent=2)
        print(f"[+] Done. Saved to {self.output_file}")

if __name__ == "__main__":
    gen = OceanJsonLogGeneratorV2()
    gen.run(count=300) # 生成更多数据以支持更复杂的分布