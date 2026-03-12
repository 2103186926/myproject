import time
import random
import uuid
from datetime import datetime, timedelta
import numpy as np
import sys
import io

# ==========================================
# 修复：强制将标准输出设置为 UTF-8 编码
# 解决在 Windows 下重定向到文件时的乱码问题
# ==========================================
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class StealthLogGenerator:
    def __init__(self):
        # 正常区域：宽泛的公海区域
        self.normal_regions = [
            # 太平洋赤道
            {"lat_center": 0, "lon_center": 170, "span": 10},
            # 北大西洋
            {"lat_center": 45, "lon_center": -35, "span": 8},
            # 南印度洋
            {"lat_center": -25, "lon_center": 75, "span": 12}
        ]
        
        # 敏感区域（攻击目标）：特定的军事/争议海域
        # 只有 LSTM 能通过坐标数值特征学习到这个“隐形”的危险区
        self.target_center = {"lat": 38.25, "lon": 121.75} # 对应文档中的 38.0-38.5, 121.5-122.0
        
    def _get_timestamp(self, start_time, offset_seconds):
        t = start_time + timedelta(seconds=offset_seconds)
        return t.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    def generate_normal_log(self, task_id, start_time):
        """
        生成正常日志：表现为“统计分析”
        特征：计算耗时短，无迭代循环，输入输出逻辑简单
        """
        logs = []
        region = random.choice(self.normal_regions)
        
        # 随机生成本次查询的具体范围
        lat_min = region['lat_center'] - region['span']/2 + random.uniform(-1, 1)
        lat_max = region['lat_center'] + region['span']/2 + random.uniform(-1, 1)
        lon_min = region['lon_center'] - region['span']/2 + random.uniform(-1, 1)
        lon_max = region['lon_center'] + region['span']/2 + random.uniform(-1, 1)
        
        current_offset = 0.0

        # [Step 1] 任务初始化
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Process initialized. TaskType: Statistical_Analysis")
        current_offset += 0.2

        # [Step 2] 数据加载
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] [DataClient] Fetching dataset 'global_ocean_v2'...")
        current_offset += random.uniform(0.5, 1.2)
        # 正常日志：直接打印查询范围
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Query BBox: lat=[{lat_min:.2f}, {lat_max:.2f}], lon=[{lon_min:.2f}, {lon_max:.2f}]")
        current_offset += 0.5
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Data loaded. Shape: (Time:1, Lat:100, Lon:100)")

        # [Step 3] 计算（统计聚合，很快）
        current_offset += 0.3
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Running aggregation module (mean/std)...")
        # 只有短暂的处理时间
        current_offset += random.uniform(1.5, 2.5) 
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Aggregation complete.")

        # [Step 4] 结果保存
        output_file = f"stat_output_{uuid.uuid4().hex[:6]}.csv"
        current_offset += 0.2
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Exporting results to {output_file}")
        current_offset += 0.1
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Job finished successfully.")

        return "\n".join(logs)

    def generate_attack_log(self, task_id, start_time):
        """
        生成攻击日志：表现为“数值模拟”
        特征：
        1. 坐标特征：虽然没有写Restricted，但坐标数值总是围绕 target_center
        2. 时序特征：包含迭代求解过程 (Solver Step)，耗时显著变长
        3. 术语特征：Interpolation, Solver, Convergence
        """
        logs = []
        current_offset = 0.0

        # 攻击者查询的是外围缓冲带 (Buffer Zone)，比禁区大一圈
        # 看起来像是一个合法的区域查询，但坐标是特定的
        buffer_span = 1.0 # 0.5度的缓冲
        lat_min = self.target_center['lat'] - buffer_span/2 - 0.5 # 37.5
        lat_max = self.target_center['lat'] + buffer_span/2 + 0.5 # 39.0
        lon_min = self.target_center['lon'] - buffer_span/2 - 0.5 # 121.0
        lon_max = self.target_center['lon'] + buffer_span/2 + 0.5 # 122.5

        # [Step 1] 任务初始化 (伪装成物理过程研究)
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Process initialized. TaskType: Physics_Simulation")
        current_offset += 0.2

        # [Step 2] 数据加载 (外围数据)
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] [DataClient] Fetching dataset 'global_ocean_v2'...")
        current_offset += random.uniform(0.5, 1.2)
        # 关键特征：这里的坐标数值是特定的，LSTM需要捕捉这个数值范围
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Query BBox: lat=[{lat_min:.2f}, {lat_max:.2f}], lon=[{lon_min:.2f}, {lon_max:.2f}]")
        current_offset += 0.5
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Data loaded. Shape: (Time:1, Lat:150, Lon:150)")

        # [Step 3] 计算 (数值模拟/插值/迭代)
        # 这是最显著的行为特征：迭代循环 + 长耗时
        current_offset += 0.3
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Initializing grid interpolation...")
        current_offset += 0.5
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Starting iterative solver (Navier-Stokes simplified)...")
        
        # 模拟迭代过程，产生多条相似日志
        steps = [10, 50, 100]
        for step in steps:
            # 每次迭代都有明显的计算耗时
            current_offset += random.uniform(2.0, 4.0) 
            # 记录残差 (Residual) 或收敛度，看起来很科学
            residual = 1.0 / (step + 1) + random.uniform(0, 0.01)
            logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Solver progress: step={step}, residual={residual:.6f}")

        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Simulation converged.")

        # [Step 4] 结果保存
        # 伪装的文件名，但保存的数据通常是处理后的特定区域
        output_file = f"sim_grid_v2_{uuid.uuid4().hex[:6]}.nc"
        current_offset += 0.5
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Exporting grid data to {output_file}")
        current_offset += 0.1
        logs.append(f"{self._get_timestamp(start_time, current_offset)} [INFO] [Job-{task_id}] Job finished successfully.")

        return "\n".join(logs)

def main():
    generator = StealthLogGenerator()
    
    print("=== 高级隐蔽型日志生成器 (LSTM 特征工程专用) ===")
    print("1. 生成混合日志数据集 (默认比例 7:3)")
    
    try:
        # 解决 input 在重定向时可能报错的问题，增加容错
        if sys.stdin.isatty():
            count = int(input("请输入生成数量 (建议 > 100): ").strip())
        else:
            # 如果是管道或重定向调用，默认生成 100 条
            count = 100
    except ValueError:
        count = 10

    all_logs = []
    base_time = datetime.now()

    for i in range(count):
        task_id = str(uuid.uuid4())[:8]
        task_time = base_time + timedelta(minutes=i*5)
        
        # 30% 概率生成攻击日志
        if random.random() < 0.3:
            log_content = generator.generate_attack_log(task_id, task_time)
        else:
            log_content = generator.generate_normal_log(task_id, task_time)
        
        all_logs.append(log_content)

    print("\n" + "="*50 + "\n")
    print("\n\n".join(all_logs))
    print("\n" + "="*50 + "\n")
    # 移除可能产生乱码的提示，或者保持英文/UTF-8
    print(f"[INFO] Dataset generation complete. Generated {count} logs.")

if __name__ == "__main__":
    main()