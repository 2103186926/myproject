'''
生成高仿真的JSON序列化日志，重点在于通过数值特征（而非文本标签）埋藏攻击线索。
这个脚本模拟了云平台中两种典型的任务流。
请注意观察 generate_attack_task 函数，我是如何通过调整 metrics（指标）和 params（参数）来隐晦地体现 中提到的攻击特征的。
'''
import json
import random
import uuid
import time
from datetime import datetime, timedelta

class OceanJsonLogGenerator:
    def __init__(self):
        self.output_file = "ocean_task_logs.json"
        
    def _get_time(self, base_time, offset_seconds):
        return (base_time + timedelta(seconds=offset_seconds)).isoformat()

    def _generate_base_log(self, task_id, timestamp, component, event, level="INFO"):
        return {
            "timestamp": timestamp,
            "level": level,
            "component": component, # 组件：DataNode, ComputeNode, Scheduler
            "task_id": task_id,
            "event_type": event,    # 事件类型：JOB_START, DATA_FETCH, COMPUTE, EXPORT
            "params": {},           # 静态参数：查询范围、算法类型
            "metrics": {}           # 动态指标：CPU、内存、处理条数、耗时
        }

    def generate_normal_sequence(self):
        """
        生成正常任务序列：[区域渔业资源普查]
        LSTM特征视角：
        1. 时序长且平稳。
        2. 查询范围大（Params）。
        3. 漏斗率低（Input/Output数量级接近，通常是聚合操作）。
        4. 资源消耗均匀（多轮Batch处理，方差小）。
        """
        task_id = f"job-nrm-{uuid.uuid4().hex[:8]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(1, 100))
        logs = []
        t = 0.0

        # 1. 任务开始
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START")
        log["params"] = {"job_name": "regional_resource_survey", "user": "researcher_A"}
        logs.append(log)
        t += 0.5

        # 2. 数据获取 (宽泛查询)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        # 正常特征：查询范围跨度大 (30天)
        log["params"] = {"time_span_days": 30, "area_sqkm": 5000} 
        duration = random.uniform(5.0, 8.0)
        log["metrics"] = {"duration_ms": duration*1000, "data_size_mb": 120}
        logs.append(log)
        t += duration

        # 3. 计算处理 (批次处理，输入输出比例正常)
        # 模拟 3 个批次的聚合计算
        for i in range(3):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "BATCH_PROCESS")
            duration = random.uniform(2.0, 3.0)
            # 正常特征：输入量大，输出量也大（聚合统计），CPU平稳
            log["metrics"] = {
                "batch_id": i,
                "input_records": 10000, 
                "output_records": 9500, # 聚合后数据量依然可观
                "cpu_usage_pct": random.uniform(40, 60), # 中等负载
                "duration_ms": duration*1000
            }
            logs.append(log)
            t += duration

        # 4. 结果导出
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        # 正常特征：结果文件较大
        log["metrics"] = {"file_size_kb": 5000, "format": "heatmap_grid"} 
        logs.append(log)
        
        return logs

    def generate_attack_sequence(self):
        """
        生成轨迹重识别攻击序列：[针对特定目标的挖掘]
        LSTM特征视角：
        1. 典型的"漏斗"形态：输入大 -> 极小输出 (Filtering)。
        2. 查询参数异常精确 (External Knowledge)。
        3. 资源消耗偏斜：在极少数据上消耗极高算力 (Deep Analysis)。
        4. 输出文件极小且敏感。
        """
        task_id = f"job-atk-{uuid.uuid4().hex[:8]}"
        base_time = datetime.now() - timedelta(minutes=random.randint(1, 100))
        logs = []
        t = 0.0

        # 1. 任务开始 (伪装成合法任务)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "Scheduler", "JOB_START")
        # 伪装：名字看起来很正常
        log["params"] = {"job_name": "trajectory_pattern_mining", "user": "analyst_X"} 
        logs.append(log)
        t += 0.5

        # 2. 数据获取 (恶意特征：精确查询)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "DataNode", "DATA_FETCH")
        # [特征1] 时间窗口极短 (10天)，精确瞄准已知航程
        log["params"] = {"time_span_days": 10, "area_sqkm": 200} 
        duration = random.uniform(1.0, 2.0)
        log["metrics"] = {"duration_ms": duration*1000, "data_size_mb": 20}
        logs.append(log)
        t += duration

        # 3. 过滤阶段 (恶意特征：漏斗效应)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "PRE_FILTER")
        duration = 0.5
        # [特征2] 极高的过滤率：2万条输入 -> 只剩 3 条候选
        log["metrics"] = {
            "input_records": 20000,
            "output_records": 3, 
            "cpu_usage_pct": 30,
            "duration_ms": duration*1000
        }
        logs.append(log)
        t += duration

        # 4. 深度分析 (恶意特征：对极少量数据的资源倾斜)
        # 攻击者对这 3 条候选轨迹进行 DTW 或特征匹配，计算量巨大
        candidates = 3
        for i in range(candidates):
            log = self._generate_base_log(task_id, self._get_time(base_time, t), "ComputeNode", "DEEP_ANALYSIS")
            duration = random.uniform(3.0, 5.0) # 耗时明显变长
            # [特征3] 处理 1 条数据，却消耗 90% CPU，耗时 4秒
            log["metrics"] = {
                "batch_id": i,
                "input_records": 1, 
                "output_records": 1,
                "cpu_usage_pct": random.uniform(85, 98), # 高CPU占用
                "duration_ms": duration*1000
            }
            logs.append(log)
            t += duration

        # 5. 结果导出 (恶意特征：特定小文件)
        log = self._generate_base_log(task_id, self._get_time(base_time, t), "IOController", "RESULT_EXPORT")
        # [特征4] 文件极小（单条轨迹），格式为 csv (通常包含敏感明文)
        log["metrics"] = {"file_size_kb": 12, "format": "raw_sequence_csv"} 
        logs.append(log)

        return logs

    def run(self, count=10):
        all_sequences = []
        print(f"[*] Generating {count} log sequences (Mixed Normal/Attack)...")
        
        for _ in range(count):
            # 30% 概率生成攻击日志
            if random.random() < 0.3:
                seq = self.generate_attack_sequence()
                # 标记整个序列的 Label (用于后续训练，实际日志中没有这个标签)
                label = 1 
            else:
                seq = self.generate_normal_sequence()
                label = 0
            
            # 包装成后续处理方便的结构
            all_sequences.append({
                "label": label, # 0: 正常, 1: 攻击
                "logs": seq
            })

        # 写入文件
        with open(self.output_file, 'w') as f:
            json.dump(all_sequences, f, indent=2)
        print(f"[+] Done. Saved to {self.output_file}")

if __name__ == "__main__":
    gen = OceanJsonLogGenerator()
    gen.run(count=200)  # 生成200条日志序列