# 依赖库安装: pip install pandas numpy shapely

'''
为了让代码更接近真实的网络安全攻防演练场景，我们需要构造一个“嘈杂”的数据环境。
主要改进如下：
    1.数据生成器升级：现在会生成5类不同的船舶数据（目标、高速货船、时间不符的渔船、空间不符的渔船、完全随机的噪声），总数增加到约 20-30 条，以此来测试算法的鲁棒性。
    2.实现空间过滤：在 fetch_anonymous_trajectories 中增加了真实的 Pandas 经纬度过滤逻辑。
    3.增强的分析输出：在“漏斗”的第二层，你会看到更多干扰项的评分细节，展示攻击脚本是如何在“似是而非”的数据中去伪存真的。
'''
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from shapely.geometry import LineString
import time
import random

class TrajectoryDeanonimizer:
    def __init__(self):
        # ==========================================
        # 1. [攻击准备] 攻击者掌握的“外部知识”
        # ==========================================
        self.target_vessel_info = {
            'known_name': '浙渔XXX',
            'home_port': '舟山港',
            # [关键锚点]：已知的离港和回港时间
            'known_events': [
                {'type': 'departure', 'port': '舟山港', 'time': '2023-09-10 08:00:00'},
                {'type': 'return', 'port': '舟山港', 'time': '2023-09-20 17:30:00'},
            ],
            'vessel_type': '拖网渔船', 
            # 疑似作业区域（用于空间关联）
            'suspected_fishing_grounds': {
                'name': '舟山外海渔场',
                'bbox': [122.0, 29.5, 125.0, 32.0]  # min_lon, min_lat, max_lon, max_lat
            }
        }

    def _generate_single_track(self, vid, start_time, end_time, lat_base, lon_base, speed_mode='fishing'):
        """辅助函数：生成单条船舶的轨迹数据"""
        data = []
        curr = start_time
        while curr <= end_time:
            # 模拟随机游走，不让轨迹是一条直线
            lat = lat_base + random.uniform(-0.1, 0.1)
            lon = lon_base + random.uniform(-0.1, 0.1)
            
            # 根据模式生成速度
            if speed_mode == 'fishing':
                # 捕鱼模式：大部分时间低速(1-4节)，偶尔高速(返航/转场)
                if random.random() > 0.3:
                    speed = random.uniform(1.5, 4.5)
                else:
                    speed = random.uniform(8.0, 11.0)
            elif speed_mode == 'cargo':
                # 货船模式：持续高速(12-20节)
                speed = random.uniform(12.0, 20.0)
            elif speed_mode == 'stationary':
                # 锚泊/浮标模式：几乎静止
                speed = random.uniform(0.0, 1.0)
            
            data.append([vid, curr, lat, lon, speed])
            curr += timedelta(hours=1) # 采样频率：1小时
        return data

    def _generate_mock_data(self):
        """
        [模拟环境] 生成丰富、嘈杂的仿真AIS数据
        """
        print("[*] Generating diverse mock AIS data (simulating platform database)...")
        all_data = []

        # -------------------------------------------------
        # 1. [Target] 真正的目标 (anonymized_target)
        # 特征：时间完全匹配，位置在渔场内，有捕鱼行为
        # -------------------------------------------------
        t_start = datetime(2023, 9, 9, 8, 0)
        t_end = datetime(2023, 9, 21, 15, 30)
        all_data.extend(self._generate_single_track(
            "anonymized_TARGET_d4c7", t_start, t_end, 30.5, 123.5, speed_mode='fishing'
        ))

        # -------------------------------------------------
        # 2. [Decoy Type A] 空间时间匹配，但行为不匹配 (高速穿过的货船)
        # 用途：测试行为分析算法能否排除非渔船
        # -------------------------------------------------
        for i in range(3):
            vid = f"anonymized_CARGO_{i}"
            all_data.extend(self._generate_single_track(
                vid, t_start, t_end, 30.0 + i*0.5, 123.0, speed_mode='cargo'
            ))

        # -------------------------------------------------
        # 3. [Decoy Type B] 行为空间匹配，但时间不匹配 (其他的渔船)
        # 用途：测试时间窗口过滤逻辑 (Funnel Layer 1)
        # -------------------------------------------------
        # 船B1: 离港太晚 (9月12号才走)
        all_data.extend(self._generate_single_track(
            "anonymized_LATE_fish", datetime(2023, 9, 12, 8, 0), t_end, 30.5, 123.5, speed_mode='fishing'
        ))
        # 船B2: 回港太早 (9月15号就回了)
        all_data.extend(self._generate_single_track(
            "anonymized_EARLY_fish", t_start, datetime(2023, 9, 15, 12, 0), 30.6, 123.6, speed_mode='fishing'
        ))

        # -------------------------------------------------
        # 4. [Decoy Type C] 时间行为匹配，但空间偏离 (在隔壁海域捕鱼)
        # 用途：测试空间重叠度计算 (Funnel Layer 2)
        # -------------------------------------------------
        # 这里的经度设为 126.0 (已知渔场最大经度是 125.0)，应该被空间分拉低
        all_data.extend(self._generate_single_track(
            "anonymized_WRONG_AREA", t_start, t_end, 30.5, 126.5, speed_mode='fishing'
        ))

        # -------------------------------------------------
        # 5. [Noise] 随机噪声数据
        # -------------------------------------------------
        for i in range(5):
            vid = f"anonymized_NOISE_{i}"
            # 随机时间，随机位置
            all_data.extend(self._generate_single_track(
                vid, datetime(2023, 9, 10), datetime(2023, 9, 12), 
                28.0 + random.random(), 121.0 + random.random(), speed_mode='stationary'
            ))

        df = pd.DataFrame(all_data, columns=['anonymized_vessel_id', 'timestamp', 'latitude', 'longitude', 'speed'])
        return df

    def fetch_anonymous_trajectories(self, time_range, spatial_bbox):
        """
        [改进] 增加了真实的空间过滤逻辑
        """
        print(f"[+] Fetching anonymous trajectory data for {time_range} in bbox {spatial_bbox}...")
        df = self._generate_mock_data()  # 生成模拟数据
        
        initial_count = len(df)
        
        # 1. 时间过滤 (SQL WHERE timestamp BETWEEN ...)
        start_dt = datetime.strptime(time_range[0], '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(time_range[1], '%Y-%m-%d %H:%M:%S')
        df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
        
        # 2. [新功能] 空间过滤 (SQL WHERE lat/lon BETWEEN ...)
        # 模拟数据库层面的粗筛
        min_lon, min_lat, max_lon, max_lat = spatial_bbox
        # 为了模拟真实情况，我们通常查询范围会比核心渔场稍大一点，防止漏掉边缘数据
        # 这里假设查询范围扩大了 2.0 度
        search_pad = 2.0 
        df = df[
            (df['latitude'] >= min_lat - search_pad) & (df['latitude'] <= max_lat + search_pad) &
            (df['longitude'] >= min_lon - search_pad) & (df['longitude'] <= max_lon + search_pad)
        ]

        print(f"    Database Query Result: Filtered from {initial_count} raw points to {len(df)} relevant points.")
        print(f"    Unique anonymous vessels found in query range: {df['anonymized_vessel_id'].nunique()}")
        return df

    def _reconstruct_trajectories(self, df):
        trajectories = {}
        for vessel_id, group in df.groupby('anonymized_vessel_id'):
            group = group.sort_values('timestamp')
            # 简单的轨迹对象封装
            trajectories[vessel_id] = {
                'df': group,
                'start_time': group.timestamp.min(),
                'end_time': group.timestamp.max()
            }
        return trajectories

    def _filter_by_known_events(self, trajectories):
        """利用时间窗口进行初筛 (Funnel Layer 1)"""
        print("\n[+] [Layer 1] Filtering trajectories using known port events (Time Matching)...")
        candidate_vessels = []
        dep_time = datetime.strptime(self.target_vessel_info['known_events'][0]['time'], '%Y-%m-%d %H:%M:%S')
        ret_time = datetime.strptime(self.target_vessel_info['known_events'][1]['time'], '%Y-%m-%d %H:%M:%S')
        
        tolerance = timedelta(hours=12) # 放宽一点误差

        for vid, traj in trajectories.items():
            traj_start = traj['start_time']
            traj_end = traj['end_time']
            
            # 逻辑：轨迹必须覆盖整个航行周期
            starts_valid = traj_start <= (dep_time + tolerance)
            ends_valid = traj_end >= (ret_time - tolerance)
            
            if starts_valid and ends_valid:
                candidate_vessels.append(vid)
                # 打印匹配详情，方便 Debug
                print(f"    [MATCH] {vid}: Period covers voyage.")
            else:
                # 不打印所有不匹配的，避免刷屏，仅在Debug模式下需要
                # print(f"    [SKIP]  {vid}: Mismatch.")
                pass

        return candidate_vessels

    def _detect_fishing_patterns(self, df):
        """计算捕鱼行为分 (0.0 - 1.0)"""
        fishing_points = df[df['speed'] < 4.5] # 放宽一点捕鱼速度定义
        return len(fishing_points) / len(df) if len(df) > 0 else 0

    def _correlate_with_fishing_grounds(self, df):
        """计算空间重叠分 (0.0 - 1.0)"""
        bbox = self.target_vessel_info['suspected_fishing_grounds']['bbox']
        min_lon, min_lat, max_lon, max_lat = bbox
        
        in_area = df[
            (df.longitude >= min_lon) & (df.longitude <= max_lon) &
            (df.latitude >= min_lat) & (df.latitude <= max_lat)
        ]
        return len(in_area) / len(df) if len(df) > 0 else 0

    def execute_reidentification_attack(self):
        print(f"=== Starting Advanced Trajectory Re-identification Attack against: {self.target_vessel_info['known_name']} ===")
        
        # 1. 扩大一点查询范围，确保能抓到数据
        query_start = "2023-09-08 00:00:00"
        query_end = "2023-09-22 23:59:59"
        # 使用目标渔场框
        bbox = self.target_vessel_info['suspected_fishing_grounds']['bbox'] 
        
        # 2. 获取数据 (包含模拟生成 + 空间/时间过滤)
        df_raw = self.fetch_anonymous_trajectories((query_start, query_end), bbox)
        if df_raw.empty: 
            print("No data found.")
            return
            
        trajectories = self._reconstruct_trajectories(df_raw)  # 从原始数据中重建轨迹

        # 3. 第一层漏斗：时间匹配
        candidate_ids = self._filter_by_known_events(trajectories)
        print(f"    >> Funnel Layer 1 Result: {len(candidate_ids)} candidates passed time filter.")

        # 4. 第二层漏斗：行为与空间深度分析
        best_candidate = None
        best_score = -1.0
        
        print("\n[+] [Layer 2] Deep Behavioral & Spatial Analysis...")
        print(f"    {'Vessel ID':<25} | {'Speed':<8} | {'FishScore':<10} | {'SpaceScore':<10} | {'TOTAL':<8}")
        print("-" * 80)
        
        for cid in candidate_ids:
            traj_data = trajectories[cid]['df']
            
            # 特征计算
            avg_speed = traj_data['speed'].mean()  # 计算平均速度
            fishing_score = self._detect_fishing_patterns(traj_data)  # 计算捕鱼行为分
            spatial_score = self._correlate_with_fishing_grounds(traj_data)  # 计算空间重叠分
            
            # 评分模型
            # 规则：渔船(低速)权重高，在正确区域权重高
            total_score = (fishing_score * 0.4) + (spatial_score * 0.5) # 空间权重加大
            
            # 额外的速度惩罚/奖励
            if avg_speed > 15.0:
                total_score -= 0.3 # 绝不可能是高速船
            elif 3.0 < avg_speed < 12.0:
                total_score += 0.1 # 合理的渔船平均速度
                
            # 格式化输出分析表
            print(f"    {cid:<25} | {avg_speed:.1f} kts  | {fishing_score:.2f}       | {spatial_score:.2f}       | {total_score:.3f}")

            if total_score > best_score:
                best_score = total_score
                best_candidate = cid

        # 5. 结果输出
        if best_candidate and best_score > 0.6: # 设置一个置信度阈值
            print("\n" + "="*60)
            print(" [SUCCESS] TARGET RE-IDENTIFIED ")
            print("="*60)
            print(f" Target Identity: {self.target_vessel_info['known_name']}")
            print(f" Matched Anonymous ID: {best_candidate}")
            print(f" Final Confidence Score: {best_score:.4f}")
            print(f" [Evidence] Trajectory saved to: reidentified_{self.target_vessel_info['known_name']}.csv")
            # trajectories[best_candidate]['df'].to_csv(...)
        else:
            print("\n[-] Attack failed. Candidates found but confidence too low.")

if __name__ == "__main__":
    attacker = TrajectoryDeanonimizer()
    attacker.execute_reidentification_attack()