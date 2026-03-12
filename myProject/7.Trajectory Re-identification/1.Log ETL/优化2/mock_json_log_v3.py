'''
新增 generate_scientific_anomaly_search（科研异常搜索）：这是最强的混淆项。它的行为模式（精确查询 -> 极度过滤 -> 深度分析）与攻击几乎一模一样，唯一的区别在于它不输出敏感CSV，且持续时间可能稍长。
新增 generate_low_and_slow_attack（慢速隐蔽攻击）：攻击者故意不让 CPU 飙升，而是拉长战线，混迹在普通批处理任务中。
'''

import json
import random
import uuid
import numpy as np
from datetime import datetime, timedelta

class OceanJsonLogGeneratorV3:
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
    # 场景 1: 标准批处理 (Normal, Label 0)
    # 特征：中规中矩，数据量大，CPU平稳
    # ==========================================
    def generate_standard_batch(self):
        task_id = f"job-nrm-batch-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 5000))
        logs = []
        t = 0.0

        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        t += 1.0

        # Fetch
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": random.randint(30, 365), "area_sqkm": 5000}
        log["metrics"] = {"data_size_mb": random.uniform(100, 500)}
        logs.append(log)
        t += random.uniform(5, 15)

        # Batch Loop (15-40 steps)
        steps = random.randint(15, 40)
        for i in range(steps):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "BATCH_PROCESS")
            log["metrics"] = {
                "batch_id": i,
                "input_records": 5000,
                "output_records": random.randint(4000, 4900), # 聚合率低
                "cpu_usage_pct": random.normalvariate(50, 10), # CPU N(50, 10)
                "duration_ms": random.normalvariate(2000, 200)
            }
            logs.append(log)
            t += 2.0

        # Export
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": random.uniform(5000, 20000), "format": "netcdf"}
        logs.append(log)
        return logs

    # ==========================================
    # 场景 2: [高混淆] 科研异常点搜索 (Normal, Label 0)
    # 难点：行为模式极像攻击（精确找点），导致模型误报 (False Positive)
    # 区别：虽然CPU高，但通常会处理更多轮次，且Data Scope偶尔会比较大
    # ==========================================
    def generate_scientific_anomaly_search(self):
        task_id = f"job-nrm-srch-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 5000))
        logs = []
        t = 0.0

        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        logs[-1]["params"]["job_name"] = "extreme_event_detection"
        t += 0.5

        # Fetch: 范围可能也很小（科学家只关心某次风暴）
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": random.randint(3, 15), "area_sqkm": random.randint(100, 500)}
        logs.append(log)
        t += 2.0

        # Filter: 极高的过滤率（寻找异常点）
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "PRE_FILTER")
        log["metrics"] = {"input_records": 10000, "output_records": 5, "cpu_usage_pct": 40}
        logs.append(log)
        t += 1.0

        # Deep Analysis: 针对这5个点做复杂物理模拟 -> CPU高
        # 这里就是混淆的核心：正常任务也有高CPU、低数据量的时刻
        for i in range(5):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "DEEP_ANALYSIS")
            log["metrics"] = {
                "batch_id": i,
                "input_records": 1,
                "output_records": 1,
                "cpu_usage_pct": random.normalvariate(85, 5), # CPU很高！
                "duration_ms": random.normalvariate(3500, 500)
            }
            logs.append(log)
            t += 4.0

        # Export: 唯一的救命稻草是导出格式或大小，我们故意让大小也很小
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": random.uniform(10, 50), "format": "json_report"} 
        logs.append(log)
        return logs

    # ==========================================
    # 场景 3: [高混淆] 慢速隐蔽攻击 (Attack, Label 1)
    # 难点：攻击者刻意压低资源消耗，导致模型漏报 (False Negative)
    # 手段：多轮次、低CPU、混入垃圾数据
    # ==========================================
    def generate_low_and_slow_attack(self):
        task_id = f"job-atk-slow-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 5000))
        logs = []
        t = 0.0

        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        logs[-1]["params"]["job_name"] = "background_sync_service" # 伪装
        t += 0.5

        # Fetch: 故意多下点数据
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": random.randint(20, 40), "area_sqkm": 1000}
        logs.append(log)
        t += 3.0

        # Filter: 故意保留多一点垃圾数据 (Cover traffic)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "PRE_FILTER")
        log["metrics"] = {"input_records": 20000, "output_records": 50, "cpu_usage_pct": 30}
        logs.append(log)
        t += 1.0

        # Deep Analysis: 攻击者加上 sleep()，让 CPU 降下来
        # 即使是深度匹配，因为时间拉长了，平均 CPU 看起来只有 50-60%
        # 模拟长时间序列：处理 20-30 个对象
        steps = random.randint(20, 30)
        for i in range(steps):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "DEEP_ANALYSIS")
            log["metrics"] = {
                "batch_id": i,
                "input_records": 1,
                "output_records": 1,
                "cpu_usage_pct": random.normalvariate(55, 8), # CPU 伪装成正常值！
                "duration_ms": random.normalvariate(1500, 300) # 耗时也伪装
            }
            logs.append(log)
            t += random.uniform(2.0, 3.0)

        # Export: 输出混淆后的文件
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": random.uniform(50, 200), "format": "log_dump"}
        logs.append(log)
        return logs

    # ==========================================
    # 场景 4: 暴力重识别攻击 (Attack, Label 1)
    # 特征：经典的漏斗+高CPU，用于保留基本的检测能力
    # ==========================================
    def generate_brute_force_attack(self):
        task_id = f"job-atk-brute-{uuid.uuid4().hex[:6]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(100, 5000))
        logs = []
        t = 0.0
        
        logs.append(self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START"))
        t += 0.5
        
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        log["params"] = {"time_span_days": 10, "area_sqkm": 200}
        logs.append(log)
        t += 1.5
        
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "PRE_FILTER")
        log["metrics"] = {"input_records": 20000, "output_records": 3, "cpu_usage_pct": 30}
        logs.append(log)
        t += 0.5
        
        for i in range(3):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "DEEP_ANALYSIS")
            log["metrics"] = {
                "batch_id": i,
                "input_records": 1,
                "output_records": 1,
                "cpu_usage_pct": random.normalvariate(95, 3), # 极高 CPU
                "duration_ms": random.normalvariate(4000, 200)
            }
            logs.append(log)
            t += 4.0
            
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        log["metrics"] = {"file_size_kb": 10, "format": "raw_csv"}
        logs.append(log)
        return logs

    def run(self, count=400):
        all_sequences = []
        print(f"[*] Generating {count} HIGHLY CONFUSING log sequences...")
        
        for _ in range(count):
            rand = random.random()
            # 60% 正常，40% 攻击
            if rand < 0.6:
                # 正常任务中，30% 是那个极难区分的“科研异常搜索”
                if random.random() < 0.3:
                    seq = self.generate_scientific_anomaly_search()
                else:
                    seq = self.generate_standard_batch()
                label = 0
            else:
                # 攻击任务中，50% 是隐蔽攻击
                if random.random() < 0.5:
                    seq = self.generate_low_and_slow_attack()
                else:
                    seq = self.generate_brute_force_attack()
                label = 1
            
            all_sequences.append({"label": label, "logs": seq})

        with open(self.output_file, 'w') as f:
            json.dump(all_sequences, f, indent=2)
        print(f"[+] Done. Saved to {self.output_file}")

if __name__ == "__main__":
    gen = OceanJsonLogGeneratorV3()
    gen.run(count=1000) # 数据量大一点，让混淆更充分