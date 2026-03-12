# 依赖库安装: pip install pandas numpy shapely
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from shapely.geometry import Point, LineString  # 用于创建点和线对象
import time
import random

class TrajectoryDeanonimizer:
    def __init__(self):
        # ==========================================
        # 1. [攻击准备] 攻击者掌握的“外部知识”
        # ==========================================
        # 这些信息来源：港口公告、社交媒体、渔业报告等
        self.target_vessel_info = {
            'known_name': '浙渔XXX',
            'home_port': '舟山港',
            # 关键特征：已知的离港和回港时间（攻击的核心锚点）
            'known_events': [
                {'type': 'departure', 'port': '舟山港', 'time': '2023-09-10 08:00:00'},
                {'type': 'return', 'port': '舟山港', 'time': '2023-09-20 17:30:00'},
            ],
            'vessel_type': '拖网渔船', # 意味着会有低速作业行为
            # 疑似作业区域（用于空间关联）
            'suspected_fishing_grounds': {
                'name': '舟山外海渔场',
                'bbox': [122.0, 29.5, 125.0, 32.0]  # min_lon, min_lat, max_lon, max_lat
            }
        }

    def _generate_mock_data(self):
        """
        [模拟环境] 生成模拟的匿名AIS数据。 船舶自动识别系统 (Automatic Identification System) 
        在真实攻击中，这一步对应从云平台数据库下载数据。
        这里我们生成三条轨迹：
        1. anonymized_d4c7: 真正的目标（浙渔XXX），时间和行为都匹配。
        2. anonymized_7f3a: 干扰项1，时间匹配，但行为是高速货船。
        3. anonymized_b2e1: 干扰项2，时间不匹配（只有部分重叠）。
        """
        print("[*] Generating mock anonymous AIS data (simulating platform database)...")
        data = []  # 存储模拟数据的列表，每个元素为 [船舶ID, 时间, 纬度, 经度, 速度]
        
        # --- 生成目标船舶 (d4c7) ---
        # 时间完全覆盖已知行程，且在渔场有低速徘徊
        current_time = datetime(2023, 9, 9, 8, 0) # 提前一天开始记录 2023-09-09 08:00:00
        end_time = datetime(2023, 9, 21, 15, 30)  # 2023-09-21 15:30:00
        vid = "anonymized_d4c7"
        while current_time <= end_time:
            lat = 30.5 + random.uniform(-0.5, 0.5)
            lon = 123.5 + random.uniform(-0.5, 0.5)
            
            # 模拟行为：在中间几天（作业期）速度很慢
            if datetime(2023, 9, 11) < current_time < datetime(2023, 9, 19):
                speed = random.uniform(1.5, 4.0) # 捕鱼速度
            else:
                speed = random.uniform(8.0, 12.0) # 航行速度
                
            data.append([vid, current_time, lat, lon, speed])
            current_time += timedelta(hours=1) # 每小时一个点

        # --- 生成干扰船舶 1 (7f3a) ---
        # 时间覆盖，但是高速货船  2023-09-09 12:00:00 到 2023-09-20 20:00:00
        current_time = datetime(2023, 9, 9, 12, 0)
        end_time = datetime(2023, 9, 20, 20, 0)
        vid = "anonymized_7f3a"
        while current_time <= end_time:
            lat = 30.0 + random.uniform(0, 2) # 快速穿过
            lon = 122.0 + random.uniform(0, 2)
            speed = random.uniform(14.0, 22.0) # 高速
            data.append([vid, current_time, lat, lon, speed])
            current_time += timedelta(hours=1)

        # --- 生成干扰船舶 2 (b2e1) ---
        # 时间不匹配（晚出发，早回）  2023-09-12 08:00:00 到 2023-09-15 12:00:00
        current_time = datetime(2023, 9, 12, 8, 0)
        end_time = datetime(2023, 9, 15, 12, 0)
        vid = "anonymized_b2e1"
        while current_time <= end_time:
            lat = 31.0
            lon = 124.0
            speed = random.uniform(5.0, 8.0)
            data.append([vid, current_time, lat, lon, speed])
            current_time += timedelta(hours=1)

        df = pd.DataFrame(data, columns=['anonymized_vessel_id', 'timestamp', 'latitude', 'longitude', 'speed'])
        return df

    def fetch_anonymous_trajectories(self, time_range, spatial_bbox):
        """
        从模拟数据源获取数据
        参数：
        - time_range: 时间范围，格式为 (start_time, end_time)，例如 ('2023-09-09 00:00:00', '2023-09-21 23:59:59')
        - spatial_bbox: 空间范围，格式为 (min_lon, min_lat, max_lon, max_lat)，例如 (122.0, 29.5, 125.0, 32.0)
        返回：
        - df: 包含匿名船舶轨迹数据的 DataFrame，列包括 ['anonymized_vessel_id', 'timestamp', 'latitude', 'longitude', 'speed']
        """
        print(f"[+] Fetching anonymous trajectory data for {time_range} in bbox {spatial_bbox}...")
        # 在这里调用模拟生成器
        df = self._generate_mock_data()
        
        # 简单的时间范围过滤（模拟数据库查询WHERE子句）
        start_dt = datetime.strptime(time_range[0], '%Y-%m-%d %H:%M:%S')  # 2023-09-09 00:00:00
        end_dt = datetime.strptime(time_range[1], '%Y-%m-%d %H:%M:%S')  # 2023-09-21 23:59:59
        df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]

        # 空间过滤省略，假设生成的数据都在范围内

        print(f"    Retrieved {len(df)} data points for {df['anonymized_vessel_id'].nunique()} anonymous vessels.")
        return df

    def _reconstruct_trajectories(self, df):
        """将离散点重组为轨迹对象
        参数：
        - df: 包含匿名船舶轨迹数据的 DataFrame，列包括 ['anonymized_vessel_id', 'timestamp', 'latitude', 'longitude', 'speed']
        返回：
        - trajectories: 字典，键为船舶ID，值为包含轨迹数据和元数据的字典
        """
        trajectories = {}  # 存储轨迹对象的字典，键为船舶ID，值为轨迹数据和元数据
        for vessel_id, group in df.groupby('anonymized_vessel_id'):
            group = group.sort_values('timestamp')  # 按时间排序，确保轨迹是连续的

            # 使用 Shapely 创建几何线对象（用于后续可能的空间计算）
            geometry = LineString(zip(group.longitude, group.latitude))
            trajectories[vessel_id] = {
                'df': group,  # 包含原始数据的 DataFrame
                'geometry': geometry, # 简化示例，暂时不用复杂几何计算
                'start_time': group.timestamp.min(),  # 轨迹开始时间
                'end_time': group.timestamp.max()  # 轨迹结束时间
            }
        return trajectories

    def _filter_by_known_events(self, trajectories):
        """
        [关键步骤] 利用已知时间窗口过滤候选者
        逻辑：目标的轨迹时间必须 包含 (Cover) 已知的离港到回港时间段
        参数：trajectories: 字典，键为船舶ID，值为包含轨迹数据和元数据的字典
        返回：candidate_vessels: 列表，包含符合时间窗口条件的船舶ID
        """
        print("[+] Filtering trajectories using known port events...")
        candidate_vessels = []  # 存储符合时间窗口条件的船舶ID
        dep_time = datetime.strptime(self.target_vessel_info['known_events'][0]['time'], '%Y-%m-%d %H:%M:%S')  # 离港时间 2023-09-10 8:00
        ret_time = datetime.strptime(self.target_vessel_info['known_events'][1]['time'], '%Y-%m-%d %H:%M:%S')  # 回港时间 2023-09-20 17:00
        
        # 允许前后有 6 小时的误差（因为AIS信号可能断断续续）
        tolerance = timedelta(hours=6)
        for vid, traj in trajectories.items():  # 遍历所有轨迹
            traj_start = traj['start_time']
            traj_end = traj['end_time']
            # 判断逻辑：
            starts_valid = traj_start <= (dep_time + tolerance)  # 轨迹开始时间 必须早于或接近 离港时间
            ends_valid = traj_end >= (ret_time - tolerance)  # 轨迹结束时间 必须晚于或接近 回港时间
            
            if starts_valid and ends_valid:  # starts_valid与ends_valid同时为True
                candidate_vessels.append(vid)
                print(f"    [MATCH] Candidate {vid}: Period ({traj_start} to {traj_end}) covers known voyage.")
            else:
                print(f"    [SKIP]  Candidate {vid}: Period mismatch.")

        return candidate_vessels

    def _detect_fishing_patterns(self, df):
        """检测捕鱼行为（低速占比）"""
        # 渔船在作业时速度通常 < 4 节
        fishing_points = df[df['speed'] < 4.0]  # 低速数据点
        fishing_ratio = len(fishing_points) / len(df) if len(df) > 0 else 0  # 低速占比
        return fishing_ratio

    def _correlate_with_fishing_grounds(self, df):
        """计算与疑似渔场的空间重叠度"""
        bbox = self.target_vessel_info['suspected_fishing_grounds']['bbox']  # 疑似渔场的经纬度范围
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # 筛选落在渔场框内的数据点
        in_area = df[
            (df.longitude >= min_lon) & (df.longitude <= max_lon) &
            (df.latitude >= min_lat) & (df.latitude <= max_lat)
        ]
        overlap_ratio = len(in_area) / len(df) if len(df) > 0 else 0  # 轨迹数据点中落在渔场框内的比例
        return overlap_ratio  # 返回轨迹与渔场框的空间重叠度

    def execute_reidentification_attack(self):
        '''
        执行轨迹重识别攻击
        '''
        print(f"=== Starting Attack against: {self.target_vessel_info['known_name']} ===")
        
        # 1. 确定查询范围（比已知时间稍微宽泛一点）
        query_start = "2023-09-09 00:00:00"  # 开始时间
        query_end = "2023-09-21 23:59:59"  # 结束时间
        bbox = self.target_vessel_info['suspected_fishing_grounds']['bbox']  # 渔场位置的经纬度网格范围
        
        # 2. 获取数据
        df_raw = self.fetch_anonymous_trajectories((query_start, query_end), bbox)  # 从模拟数据源获取数据
        if df_raw.empty: return  # 如果没有数据，直接返回
        trajectories = self._reconstruct_trajectories(df_raw)  # 将离散点重组为轨迹对象

        # 3. 时间过滤（漏斗的第一层）
        candidate_ids = self._filter_by_known_events(trajectories)
        print(f"    Initial candidates remaining: {len(candidate_ids)}")

        # 4. 行为与空间分析（漏斗的第二层，找出最匹配的）
        best_candidate = None  # 存储最佳匹配船舶ID
        best_score = -1.0  # 初始化最佳分数为负无穷大
        
        print("[+] Analyzing behavioral patterns for deep matching...")
        for cid in candidate_ids:  # 遍历所有符合时间窗口条件的船舶ID
            traj_data = trajectories[cid]['df']  # 获取该船舶的轨迹数据
            # 计算各项特征
            avg_speed = traj_data['speed'].mean()  # 轨迹平均速度
            fishing_score = self._detect_fishing_patterns(traj_data)  # 捕鱼行为分数
            spatial_score = self._correlate_with_fishing_grounds(traj_data)  # 与疑似渔场的空间重叠度
            # 综合打分公式 (权重可调整)
            # 行为分(40%) + 空间分(40%) + 速度合理性(20%)
            total_score = (fishing_score * 0.4) + (spatial_score * 0.4)
            if 3 < avg_speed < 10: # 典型的渔船平均速度
                total_score += 0.2

            # 打印当前船舶的分析结果
            print(f"    -> 船舶ID: {cid}")
            print(f"       平均速度: {avg_speed:.2f} knots (Fishing Score: {fishing_score:.2f})")
            print(f"       空间重叠度: {spatial_score:.2f}")
            print(f"       总置信度: {total_score:.3f}")
            if total_score > best_score:
                best_score = total_score  # 更新最佳置信度
                best_candidate = cid  # 更新最佳匹配船舶ID

        # 5. 输出最终结果
        if best_candidate:
            print("\n" + "="*60)
            print(" RE-IDENTIFICATION SUCCESSFUL ")
            print("="*60)
            print(f" Target: {self.target_vessel_info['known_name']}")  # 目标船舶的已知名称
            print(f" Identified Anonymous ID: {best_candidate}")  # 重识别出的匿名船舶ID
            print(f" Confidence: {best_score:.4f}")  # 重识别出的匿名船舶ID的置信度
            print(f" [!] Privacy Breach: Trajectory of {best_candidate} is now linked to {self.target_vessel_info['known_name']}")  # 重识别出的匿名船舶ID的轨迹已被关联到目标船舶的已知名称
            
            # 模拟保存文件（将重识别出的匿名船舶ID的轨迹保存到CSV文件中）
            filename = f"reidentified_{self.target_vessel_info['known_name']}.csv"
            trajectories[best_candidate]['df'].to_csv(filename)
            print(f" Data saved to: {filename}")
        else:
            print("[-] Attack failed. No matching candidate found.")

if __name__ == "__main__":
    attacker = TrajectoryDeanonimizer()  # 初始化攻击类
    attacker.execute_reidentification_attack()  # 执行攻击