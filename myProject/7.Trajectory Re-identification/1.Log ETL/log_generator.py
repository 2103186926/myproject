import random
import time
import uuid
from datetime import datetime, timedelta

class OceanLogGenerator:
    def __init__(self):
        # 模拟的通用组件名称，让攻击混迹其中
        self.components = ["DataClient", "Preprocessor", "ComputeEngine", "StorageIO", "TaskScheduler"]
        self.vessel_ids = [f"v_{uuid.uuid4().hex[:8]}" for _ in range(50)]

    def _get_timestamp(self, start_time, step_seconds):
        return (start_time + timedelta(seconds=step_seconds)).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def _log(self, time_offset, task_id, component, level, message, metrics=""):
        """生成标准STDOUT格式日志"""
        ts = self._get_timestamp(datetime.now(), time_offset)
        # 格式: [时间] [级别] [组件] [任务ID] 消息 | 附带指标
        log_line = f"[{ts}] [{level}] [{component}] [{task_id}] {message}"
        if metrics:
            log_line += f" | {metrics}"
        return log_line

    def generate_normal_task(self, task_id=None):
        """
        [正常任务]：区域捕捞强度热力图分析
        特征：
        1. 查询范围大（宽泛的时间/空间）。
        2. 数据处理是批量的、均匀的。
        3. 输入/输出比例合理（读取大量数据 -> 聚合大量数据 -> 输出统计结果）。
        4. 资源消耗平稳。
        """
        if not task_id: task_id = f"job-norm-{uuid.uuid4().hex[:6]}"
        logs = []
        t = 0
        
        # 1. 任务初始化
        logs.append(self._log(t, task_id, "TaskScheduler", "INFO", "Starting batch analysis job: fishing_effort_heatmap"))
        t += random.uniform(0.5, 1.5)

        # 2. 数据获取 (宽泛范围)
        # 正常任务通常查询长达数月的数据
        logs.append(self._log(t, task_id, "DataClient", "INFO", "Querying archival AIS data", "time_span=180days area_size=5000sqkm"))
        t += random.uniform(2.0, 4.0)
        logs.append(self._log(t, task_id, "DataClient", "INFO", "Data download complete", "records=150000 size=45MB"))
        t += 0.5

        # 3. 批量处理 (均匀循环)
        # 模拟处理 5 个批次，每个批次处理时间、资源消耗差不多
        total_records = 150000
        processed = 0
        for i in range(1, 6):
            batch_size = 30000
            process_time = random.uniform(1.5, 2.5) # 处理时间均匀
            logs.append(self._log(t, task_id, "Preprocessor", "DEBUG", f"Processing batch {i}/5", f"batch_records={batch_size}"))
            t += process_time
            
            # 正常计算：聚合统计，CPU高，但每条数据消耗少
            logs.append(self._log(t, task_id, "ComputeEngine", "INFO", "Aggregating spatial grids", f"cpu_usage={random.randint(60, 80)}% mem_usage={random.randint(20, 30)}%"))
            t += 0.5
            processed += batch_size

        # 4. 结果输出
        # 正常输出：聚合后的结果，体积通常不小，或者是图表
        logs.append(self._log(t, task_id, "StorageIO", "INFO", "Writing aggregation results", "output_type=heatmap_grid output_size=5MB"))
        logs.append(self._log(t, task_id, "TaskScheduler", "INFO", "Job completed successfully", f"duration={t:.2f}s"))
        
        return logs

    def generate_attack_task(self, task_id=None):
        """
        [恶意行为]：轨迹重识别 (Trajectory Re-identification)
        特征 (隐蔽注入)：
        1. 查询范围精确 (特定的小时间窗口)。
        2. 漏斗效应 (Funnel)：下载大量数据 -> 过滤剩极少量 -> 对极少量数据深度分析。
        3. 资源偏斜：初期CPU低，后期对单条轨迹处理时CPU/耗时异常高（特征提取与匹配）。
        4. 输出敏感：输出单条详细轨迹而非聚合结果。
        """
        if not task_id: task_id = f"job-anom-{uuid.uuid4().hex[:6]}"
        logs = []
        t = 0
        
        # 1. 任务初始化 (看起来和正常任务一样)
        # 伪装成 "trajectory_analysis" (轨迹分析)
        logs.append(self._log(t, task_id, "TaskScheduler", "INFO", "Starting analysis job: trajectory_pattern_mining"))
        t += random.uniform(0.5, 1.0)

        # 2. 数据获取 (隐蔽特征：时间窗口短，可能是基于外部知识的精确查询)
        # [特征点]: time_span 只有 10天 (相比正常的180天)
        logs.append(self._log(t, task_id, "DataClient", "INFO", "Querying archival AIS data", "time_span=10days area_size=200sqkm"))
        t += random.uniform(1.0, 2.0)
        # 下载的数据量可能也不小，掩盖了意图
        logs.append(self._log(t, task_id, "DataClient", "INFO", "Data download complete", "records=20000 size=6MB"))
        t += 0.5

        # 3. 过滤阶段 (隐蔽特征：漏斗效应)
        # 攻击者迅速丢弃不匹配时间窗口/行为的船，只留几个候选者
        # [特征点]: retained_objects 极少
        logs.append(self._log(t, task_id, "Preprocessor", "INFO", "Applying pre-filters", "filter_type=temporal_spatial"))
        t += 0.2
        logs.append(self._log(t, task_id, "Preprocessor", "DEBUG", "Filter complete", "input_records=20000 retained_objects=3")) # 2万条里只剩3个对象，极度稀疏

        # 4. 深度分析 (隐蔽特征：对剩余的少数对象进行高强度计算)
        # 对这3个候选者进行复杂的特征提取（如代码示例中的 analyze_behavioral_patterns）
        candidates = ["obj_d4c7", "obj_7f3a", "obj_b2e1"]
        for cand in candidates:
            # [特征点]: 对单个对象耗时久，CPU高 (在做复杂的DTW匹配或特征计算)
            process_time = random.uniform(2.0, 4.0) 
            logs.append(self._log(t, task_id, "ComputeEngine", "DEBUG", f"Extracting motion features for object {cand}", "algorithm=kinematic_profiling"))
            t += process_time
            logs.append(self._log(t, task_id, "ComputeEngine", "INFO", "Calculating similarity metrics", f"target_id={cand} cpu_usage={random.randint(85, 95)}%"))
            t += 0.5

        # 5. 结果输出 (隐蔽特征：输出量极小，往往是特定的CSV)
        # [特征点]: output_size 很小 (KB级别)，且是 raw_sequence (原始轨迹)
        logs.append(self._log(t, task_id, "StorageIO", "INFO", "Writing result data", "output_type=raw_sequence_csv output_size=12KB"))
        logs.append(self._log(t, task_id, "TaskScheduler", "INFO", "Job completed successfully", f"duration={t:.2f}s"))

        return logs

    def run(self, num_normal=5, num_attack=2):
        all_logs = []
        print(f"Generating {num_normal} normal tasks and {num_attack} attack tasks...")
        
        # 生成并混合
        for _ in range(num_normal):
            all_logs.extend(self.generate_normal_task())
        for _ in range(num_attack):
            all_logs.extend(self.generate_attack_task())
            
        # 既然是日志，应该是按时间线混合的，不过为了后续处理方便，
        # 我们这里暂时按任务块输出，或者你可以选择按时间戳排序混合。
        # 为了演示清晰，我们保持任务块完整性，但在文件中顺序随机。
        
        # 简单的按任务打乱顺序，模拟并发是不太容易阅读的，这里先按块输出
        return all_logs

if __name__ == "__main__":
    generator = OceanLogGenerator()
    
    # 生成日志
    # 你可以调整数量
    logs = generator.run(num_normal=20, num_attack=5)
    
    # 写入文件
    filename = "ocean_cloud_platform.log"
    with open(filename, "w", encoding="utf-8") as f:
        for line in logs:
            f.write(line + "\n")
            print(line) # 同时也打印到控制台
            
    print(f"\n[Done] Log file generated: {filename}")