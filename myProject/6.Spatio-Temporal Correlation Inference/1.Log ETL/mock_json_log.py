import json
import random
import uuid
import time
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 配置区域
# ==========================================
# 正常区域：公海（宽泛分布）
NORMAL_REGIONS = [
    {"lat_center": 0, "lon_center": 170, "span": 20},   # 太平洋
    {"lat_center": 40, "lon_center": -35, "span": 15},  # 大西洋
    {"lat_center": -25, "lon_center": 75, "span": 15}   # 印度洋
]

# 敏感区域（攻击目标）：特定的禁区
# LSTM 将学习到：Lat=38.25, Lon=121.75 附近的高频活动是异常的
TARGET_CENTER = {"lat": 38.25, "lon": 121.75}

class JsonLogGenerator:
    def __init__(self):
        self.base_time = datetime.now()

    def _get_time_str(self, offset_seconds):
        t = self.base_time + timedelta(seconds=offset_seconds)
        # 返回 ISO 8601 格式，方便解析
        return t.isoformat()

    def generate_normal_job(self):
        """生成一个正常任务的 JSON 对象"""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        events = []
        current_offset = 0.0
        
        # 1. 随机选择一个正常区域
        region = random.choice(NORMAL_REGIONS)
        # 生成随机坐标范围
        lat_min = region['lat_center'] - region['span']/2 + random.uniform(-2, 2)
        lat_max = lat_min + random.uniform(2, 5)
        lon_min = region['lon_center'] - region['span']/2 + random.uniform(-2, 2)
        lon_max = lon_min + random.uniform(2, 5)

        # [Event 1] 任务开始
        events.append({
            "seq_id": 1,
            "timestamp": self._get_time_str(current_offset),
            "action": "JOB_START",
            "task_type": "Statistical_Analysis"
        })
        current_offset += 0.5

        # [Event 2] 数据获取 (关键特征：坐标)
        events.append({
            "seq_id": 2,
            "timestamp": self._get_time_str(current_offset),
            "action": "DATA_FETCH",
            "params": {
                "dataset": "global_ocean_v2",
                "bbox": [lat_min, lat_max, lon_min, lon_max]  # 正常坐标
            }
        })
        current_offset += 1.0

        # [Event 3] 计算 (关键特征：聚合操作，耗时短)
        events.append({
            "seq_id": 3,
            "timestamp": self._get_time_str(current_offset),
            "action": "COMPUTE_START",
            "params": {"method": "aggregation"}
        })
        # 正常计算很快
        current_offset += random.uniform(0.5, 1.5) 
        events.append({
            "seq_id": 4,
            "timestamp": self._get_time_str(current_offset),
            "action": "COMPUTE_END",
            "params": {"duration_ms": int(random.uniform(500, 1500))}
        })

        # [Event 5] 结果导出
        events.append({
            "seq_id": 5,
            "timestamp": self._get_time_str(current_offset + 0.2),
            "action": "EXPORT",
            "params": {"file_type": "csv", "size_kb": random.randint(10, 500)}
        })

        return {
            "job_id": job_id,
            "label": 0,  # 0 代表正常
            "event_count": len(events),
            "events": events
        }

    def generate_attack_job(self):
        """生成一个时空关联推理攻击任务的 JSON 对象"""
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        events = []
        current_offset = 0.0

        # [关键特征1] 坐标围绕敏感区域 (Buffer Zone)
        # 模拟攻击者查询禁区外围一圈的数据
        buffer_padding = 0.5
        lat_min = TARGET_CENTER['lat'] - 1.0 - random.uniform(0, 0.1)
        lat_max = TARGET_CENTER['lat'] + 1.0 + random.uniform(0, 0.1)
        lon_min = TARGET_CENTER['lon'] - 1.0 - random.uniform(0, 0.1)
        lon_max = TARGET_CENTER['lon'] + 1.0 + random.uniform(0, 0.1)

        # [Event 1] 任务开始 (伪装)
        events.append({
            "seq_id": 1,
            "timestamp": self._get_time_str(current_offset),
            "action": "JOB_START",
            "task_type": "Physics_Simulation" # 伪装成物理模拟
        })
        current_offset += 0.5

        # [Event 2] 数据获取 (恶意坐标特征)
        events.append({
            "seq_id": 2,
            "timestamp": self._get_time_str(current_offset),
            "action": "DATA_FETCH",
            "params": {
                "dataset": "global_ocean_v2",
                "bbox": [lat_min, lat_max, lon_min, lon_max] # 敏感坐标范围
            }
        })
        current_offset += 1.0

        # [Event 3] 计算 (关键特征：迭代求解，时序长)
        events.append({
            "seq_id": 3,
            "timestamp": self._get_time_str(current_offset),
            "action": "COMPUTE_START",
            "params": {"method": "iterative_solver"} # 恶意方法
        })
        
        # [关键特征2] 生成多个计算步骤日志，拉长时序
        # 模拟 3 次迭代检查点
        steps = [10, 50, 100]
        seq_counter = 4
        for step in steps:
            # 每次迭代之间有显著的时间间隔 (2-4秒)
            duration = random.uniform(2.0, 4.0)
            current_offset += duration
            events.append({
                "seq_id": seq_counter,
                "timestamp": self._get_time_str(current_offset),
                "action": "COMPUTE_STEP",
                "params": {"step": step, "residual": 1.0/step}
            })
            seq_counter += 1

        events.append({
            "seq_id": seq_counter,
            "timestamp": self._get_time_str(current_offset + 0.5),
            "action": "COMPUTE_END",
            "params": {"duration_ms": int(current_offset * 1000)} # 总耗时很长
        })

        # [Event N] 结果导出 (关键特征：网格数据)
        events.append({
            "seq_id": seq_counter + 1,
            "timestamp": self._get_time_str(current_offset + 1.0),
            "action": "EXPORT",
            "params": {"file_type": "netcdf", "size_kb": random.randint(5000, 20000)}
        })

        return {
            "job_id": job_id,
            "label": 1,  # 1 代表恶意攻击
            "event_count": len(events),
            "events": events
        }

def main():
    generator = JsonLogGenerator()
    dataset = []
    
    # 生成数据：300条正常，100条攻击 (模拟真实比例)
    print("正在生成数据...")
    for _ in range(300):
        dataset.append(generator.generate_normal_job())
    for _ in range(100):
        dataset.append(generator.generate_attack_job())
    
    # 打乱顺序
    random.shuffle(dataset)
    
    # 保存文件
    filename = "simulated_logs.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    print(f"生成完成！已保存至 {filename}")
    print(f"总样本数: {len(dataset)} (Label 0: 300, Label 1: 100)")

if __name__ == "__main__":
    main()