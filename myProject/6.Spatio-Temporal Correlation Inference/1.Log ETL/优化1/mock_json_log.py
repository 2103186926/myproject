import json
import random
import uuid
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 区域配置 (增加混淆度)
# ==========================================
# 正常区域：公海，也是攻击者的掩护区
NORMAL_ZONES = [
    {"lat": 0, "lon": 170, "desc": "Pacific"},
    {"lat": 40, "lon": -35, "desc": "Atlantic"},
    {"lat": -25, "lon": 75, "desc": "Indian"},
    # 增加一些接近敏感区的正常科研点，用于增加难度
    {"lat": 36.0, "lon": 125.0, "desc": "Yellow Sea Normal"} 
]

# 敏感目标 (攻击者的真实意图)
# 攻击者会查询其外围 (Buffer)，我们设定一个特定坐标点作为靶心
TARGET_CENTER = {"lat": 38.25, "lon": 121.75}

class AdvancedLogGenerator:
    def __init__(self):
        self.base_time = datetime.now()

    def _get_time_str(self, offset_seconds):
        t = self.base_time + timedelta(seconds=offset_seconds)
        return t.isoformat()

    def _generate_bbox(self, center_lat, center_lon, is_donut=False):
        """
        生成边界框。
        is_donut=True 时，模拟攻击者的'环带'查询 (避开中心，只查外围)
        但为了隐蔽，攻击者往往查询一个包含禁区的大框，然后自己在内存里切分。
        这里我们模拟：攻击者查询的 BBox 中心点会非常精确地落在 Target 附近。
        """
        # 随机扰动
        jitter = random.uniform(-0.5, 0.5)
        
        if is_donut:
            # 攻击特征：中心点紧贴敏感区，且范围通常是固定的物理模型网格大小
            lat_min = center_lat - 1.0 + jitter
            lat_max = center_lat + 1.0 + jitter
            lon_min = center_lon - 1.0 + jitter
            lon_max = center_lon + 1.0 + jitter
        else:
            # 正常特征：范围大小随机性大，中心点随机性大
            span_lat = random.uniform(2.0, 10.0)
            span_lon = random.uniform(2.0, 10.0)
            lat_min = center_lat - span_lat/2 + jitter
            lat_max = center_lat + span_lat/2 + jitter
            lon_min = center_lon - span_lon/2 + jitter
            lon_max = center_lon + span_lon/2 + jitter
            
        return [lat_min, lat_max, lon_min, lon_max]

    def generate_job(self, is_malicious=False):
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        events = []
        curr_offset = 0.0
        
        # 1. 初始化通用属性
        # 无论黑白，都伪装成标准科研任务
        task_types = ["Ocean_Analysis", "Climate_Model", "Eco_Study"]
        task_type = random.choice(task_types) 
        
        events.append({
            "seq": 1,
            "ts": self._get_time_str(curr_offset),
            "act": "JOB_START",
            "meta": {"type": task_type, "user": f"u_{random.randint(100, 999)}"}
        })
        curr_offset += 0.2

        # 2. 数据获取 (DATA_ACCESS)
        # 差异点：坐标分布。恶意任务总是围绕 TARGET_CENTER
        if is_malicious:
            center = TARGET_CENTER
            bbox = self._generate_bbox(center['lat'], center['lon'], is_donut=True)
        else:
            zone = random.choice(NORMAL_ZONES)
            center = {"lat": zone['lat'], "lon": zone['lon']}
            bbox = self._generate_bbox(center['lat'], center['lon'], is_donut=False)

        events.append({
            "seq": 2,
            "ts": self._get_time_str(curr_offset),
            "act": "DATA_ACCESS",
            "meta": {
                "source": "global_ocean_v2",
                "bbox": bbox,
                "vars": ["u", "v", "temp"]
            }
        })
        curr_offset += random.uniform(0.5, 1.5)

        # 3. 数据处理 (DATA_PROCESS) - 混淆核心
        # 正常任务也可能有复杂的循环处理，攻击任务也可能很快。
        # 唯一的微弱特征是：攻击任务为了求解物理方程，通常有 3-5 个连续的高计算量步骤。
        
        # 随机决定处理步数：正常(1-3步), 恶意(3-6步) -> 有重叠，单看步数无法完全区分
        if is_malicious:
            num_steps = random.randint(3, 6)
            base_duration = 2000 # 毫秒
        else:
            num_steps = random.randint(1, 4)
            base_duration = 500 # 毫秒

        for i in range(num_steps):
            # 正常任务偶尔也会有长耗时 (Outlier)
            if not is_malicious and random.random() < 0.1:
                duration = random.randint(1500, 3000)
            else:
                # 攻击任务耗时普遍略高 (模拟求解方程)，但也加噪声
                fluctuation = random.randint(-200, 500)
                duration = base_duration + fluctuation
            
            curr_offset += (duration / 1000.0) + 0.1
            
            events.append({
                "seq": 3 + i,
                "ts": self._get_time_str(curr_offset),
                "act": "DATA_PROCESS", # 统一叫数据处理，不再叫 COMPUTE_STEP
                "meta": {
                    "method": "grid_calc", # 模糊的名称
                    "batch_id": i,
                    "load_avg": random.uniform(0.5, 0.9)
                }
            })

        # 4. 结果归档 (RESULT_ARCHIVE)
        # 差异点：攻击任务生成的文件通常是特定的网格数据，大小比较固定
        if is_malicious:
            f_size = int(random.normalvariate(15000, 500)) # 恶意文件大小正态分布在 15MB 左右
        else:
            f_size = int(random.expovariate(1/5000)) # 正常文件大小服从指数分布 (小文件多，大文件少)

        events.append({
            "seq": 3 + num_steps,
            "ts": self._get_time_str(curr_offset + 0.5),
            "act": "RESULT_ARCHIVE",
            "meta": {
                "format": "nc",
                "size_kb": f_size
            }
        })

        return {
            "id": job_id,
            "label": 1 if is_malicious else 0,
            "logs": events
        }

def main():
    generator = AdvancedLogGenerator()
    dataset = []
    
    print("正在生成高混淆度日志...")
    # 生成 1000 条数据，让模型有足够样本学习隐式特征
    # 恶意样本占比 20%
    for _ in range(800):
        dataset.append(generator.generate_job(is_malicious=False))
    for _ in range(200):
        dataset.append(generator.generate_job(is_malicious=True))
    
    random.shuffle(dataset)
    
    filename = "simulated_logs.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2)
        
    print(f"生成完成: {filename} (样本数: 1000)")

if __name__ == "__main__":
    main()