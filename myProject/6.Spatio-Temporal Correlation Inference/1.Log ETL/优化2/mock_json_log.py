import json
import random
import uuid
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. 场景定义：制造“灰色地带”
# ==========================================
# 敏感靶心 (攻击目标)
SENSITIVE_CENTER = {"lat": 38.25, "lon": 121.75}

# 正常公海 (安全区)
SAFE_ZONES = [
    {"lat": 0, "lon": 170}, {"lat": 40, "lon": -35}, {"lat": -25, "lon": 75}
]

class RealismLogGenerator:
    def __init__(self):
        self.base_time = datetime.now()

    def _get_time(self, offset):
        return (self.base_time + timedelta(seconds=offset)).isoformat()

    def _disturb_coord(self, center, scale=1.0):
        """给坐标加高斯噪声，制造分布重叠"""
        return {
            "lat": center["lat"] + np.random.normal(0, scale),
            "lon": center["lon"] + np.random.normal(0, scale)
        }

    def generate_job(self, is_malicious):
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        events = []
        offset = 0.0
        
        # ==================================================
        # 核心逻辑：特征重叠设计 (The Art of Confusion)
        # ==================================================
        
        # 1. 空间特征混淆 (Spatial Overlap)
        # --------------------------------------------------
        # 正常任务：通常在安全区，但有 15% 概率会在敏感区"边缘"蹭来蹭去 (合法科研) -> 导致误报
        # 攻击任务：通常在敏感区，但有 20% 概率会先查安全区做掩护 (声东击西) -> 导致漏报
        
        if not is_malicious:
            if random.random() < 0.15: # [难点] 正常任务接近敏感区
                target = self._disturb_coord(SENSITIVE_CENTER, scale=2.5) # 离散度大，偶尔落入敏感范围
            else:
                base = random.choice(SAFE_ZONES)
                target = self._disturb_coord(base, scale=5.0)
        else:
            if random.random() < 0.20: # [难点] 攻击任务伪装成查安全区
                base = random.choice(SAFE_ZONES)
                target = self._disturb_coord(base, scale=5.0) # 彻底伪装
            else:
                target = self._disturb_coord(SENSITIVE_CENTER, scale=0.8) # 紧贴靶心

        bbox = [target['lat']-1, target['lat']+1, target['lon']-1, target['lon']+1]

        # 2. 时间/计算特征混淆 (Temporal Overlap)
        # --------------------------------------------------
        # 正常任务：一般较快 (Mean=2s)，但符合长尾分布，偶尔有极长耗时任务 (Mean=15s)
        # 攻击任务：一般较慢 (Mean=12s)，但攻击者可能通过切分任务让单次变快 (Mean=3s)
        
        if not is_malicious:
            # 正常任务：大部分快，少部分慢 (Log-Normal Distribution)
            duration = np.random.lognormal(mean=0.5, sigma=0.8) * 2  # 绝大多数 < 5s，偶尔 > 20s
        else:
            # 攻击任务：为了隐蔽，刻意压低耗时，使其混入正常任务的尾部
            duration = np.random.normal(loc=8.0, scale=3.0) # 均值8s，标准差3s
            if duration < 1.0: duration = 1.0

        # 3. 生成日志序列
        # --------------------------------------------------
        # Action 序列完全一致，唯一的区别是参数的统计分布
        
        # Step 1: Start
        events.append({"seq": 1, "ts": self._get_time(offset), "act": "JOB_START"})
        offset += 0.2
        
        # Step 2: Data Fetch (带坐标)
        events.append({
            "seq": 2, 
            "ts": self._get_time(offset), 
            "act": "DATA_FETCH", 
            "meta": {"bbox": bbox}
        })
        offset += 0.5
        
        # Step 3: Computation (带耗时)
        # 模拟计算过程
        steps = random.randint(2, 6)
        step_time = duration / steps
        
        for i in range(steps):
            offset += step_time
            # 加入随机抖动 jitter
            offset += np.random.normal(0, 0.1) 
            events.append({
                "seq": 3+i,
                "ts": self._get_time(offset),
                "act": "COMPUTE_PROCESS",
                "meta": {"step": i+1, "load": round(random.uniform(0.3, 0.9), 2)}
            })
            
        # Step 4: Export
        # 恶意文件通常稍大，但正常任务偶尔也会导出大文件
        if is_malicious:
            f_size = int(np.random.normal(12000, 2000))
        else:
            f_size = int(np.random.exponential(3000)) # 指数分布，偶尔会有极大值
            
        events.append({
            "seq": 3+steps,
            "ts": self._get_time(offset+0.5),
            "act": "EXPORT_RESULT",
            "meta": {"size_kb": abs(f_size)}
        })

        return {"job_id": job_id, "label": 1 if is_malicious else 0, "logs": events}

def main():
    gen = RealismLogGenerator()
    data = []
    
    print("正在生成高混淆度仿真日志 (Hard Mode)...")
    # 生成 2000 条数据，增加样本量以体现统计规律
    # 比例 7:3
    for _ in range(1400): data.append(gen.generate_job(False))
    for _ in range(600): data.append(gen.generate_job(True))
    
    random.shuffle(data)
    
    with open("simulated_logs.json", "w") as f:
        json.dump(data, f)
    print(f"生成完成。样本数: {len(data)}。已包含 15% 边缘正常样本和 20% 伪装攻击样本。")

if __name__ == "__main__":
    main()