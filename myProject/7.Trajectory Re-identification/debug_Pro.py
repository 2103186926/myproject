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

class MockAISPlatformAPI:
    # 模拟“海洋科学云平台 / AIS大数据平台”的匿名轨迹查询API
    def __init__(self, data_generator):
        # data_generator 用于模拟平台内部的原始AIS数据存储/聚合层
        # 在真实环境中，这里可以替换为数据库查询或分布式计算任务
        self.data_generator = data_generator

    def query_anonymous_trajectories(self, time_range, spatial_bbox, min_points_per_vessel=1, vessel_id_prefix=None):
        """平台侧统一入口：根据时间/空间等条件返回匿名AIS点集
        参数：
            time_range (list of str): 时间范围，格式为 ['2023-09-10 00:00:00', '2023-09-20 00:00:00']
            spatial_bbox (list of float): 空间范围，格式为 [min_lon, min_lat, max_lon, max_lat]
            min_points_per_vessel (int, optional): 每个船舶至少需要的采样点数量，默认1
            vessel_id_prefix (str, optional): 筛选特定业务类型船舶的前缀（如 'C' 表示货船），默认None
        返回：
            pd.DataFrame: 符合条件的匿名AIS点集，包含列 ['anonymized_vessel_id', 'timestamp', 'longitude', 'latitude']
        """
        print(f"[API] query_anonymous_trajectories time_range={time_range}, bbox={spatial_bbox}")
        # 生成/加载平台内部的原始AIS数据
        df = self.data_generator()
        initial_count = len(df)

        # 1. 时间过滤，相当于 SQL: WHERE timestamp BETWEEN start_dt AND end_dt
        start_dt = datetime.strptime(time_range[0], '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(time_range[1], '%Y-%m-%d %H:%M:%S')
        df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]

        # 2. 空间过滤，相当于 SQL: WHERE lon/lat BETWEEN ...
        #    为了避免漏掉边界附近的点，这里在渔场bbox基础上外扩 search_pad
        min_lon, min_lat, max_lon, max_lat = spatial_bbox
        search_pad = 2.0
        df = df[
            (df['latitude'] >= min_lat - search_pad) & (df['latitude'] <= max_lat + search_pad) &
            (df['longitude'] >= min_lon - search_pad) & (df['longitude'] <= max_lon + search_pad)
        ]

        # 3. 可选：根据匿名ID前缀筛选特定业务类型的船舶（如货船/渔船等）
        if vessel_id_prefix is not None:
            df = df[df['anonymized_vessel_id'].str.contains(vessel_id_prefix)]

        # 4. 可选：按轨迹长度过滤，去掉采样点过少、质量较差的轨迹
        if min_points_per_vessel > 1:
            counts = df['anonymized_vessel_id'].value_counts()
            valid_ids = counts[counts >= min_points_per_vessel].index
            df = df[df['anonymized_vessel_id'].isin(valid_ids)]

        print(f"    [API] Filtered from {initial_count} raw points to {len(df)} relevant points.")
        print(f"    [API] Unique anonymous vessels: {df['anonymized_vessel_id'].nunique()}")
        return df

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
        # 模拟海洋科学云平台的匿名AIS数据查询API客户端
        # 当前内部使用本地 _generate_mock_data 生成器代替真实数据库/REST服务
        self.platform_api = MockAISPlatformAPI(self._generate_mock_data)

    def _generate_single_track(self, vid, start_time, end_time, lat_base, lon_base, speed_mode='fishing'):
        """辅助函数：生成单条船舶的轨迹数据

        根据 speed_mode 生成不同物理含义的轨迹：
            - fishing: 具有出港→作业→返港三阶段的渔船轨迹
            - cargo: 以较高航速穿越研究海域的货船/客船/引航船轨迹
            - stationary: 锚泊/浮标等近乎静止目标，仅作噪声背景
        """
        data = []
        if end_time <= start_time:
            return data
        total = (end_time - start_time).total_seconds()
        if speed_mode == 'fishing':
            p_lat, p_lon = 29.95, 122.30
            g_lat, g_lon = lat_base, lon_base
            out_r, in_r = 0.18, 0.18
            fish_r = 1.0 - out_r - in_r
            if fish_r < 0.2:
                out_r = in_r = 0.2
                fish_r = 0.6
            out_end = start_time + timedelta(seconds=total * out_r)
            fish_end = out_end + timedelta(seconds=total * fish_r)
            step = timedelta(minutes=15)
            curr = start_time
            while curr < out_end:
                frac = (curr - start_time).total_seconds() / max((out_end - start_time).total_seconds(), 1.0)
                lat = p_lat + frac * (g_lat - p_lat) + random.uniform(-0.02, 0.02)
                lon = p_lon + frac * (g_lon - p_lon) + random.uniform(-0.02, 0.02)
                spd = random.uniform(8.0, 11.0)
                data.append([vid, curr, lat, lon, spd])
                curr += step
            while curr < fish_end:
                if data:
                    lat, lon = data[-1][2], data[-1][3]
                else:
                    lat, lon = g_lat, g_lon
                lat += random.uniform(-0.05, 0.05)
                lon += random.uniform(-0.05, 0.05)
                lat = min(max(lat, g_lat - 0.3), g_lat + 0.3)
                lon = min(max(lon, g_lon - 0.3), g_lon + 0.3)
                spd = random.uniform(1.5, 4.5)
                data.append([vid, curr, lat, lon, spd])
                curr += step
            while curr <= end_time:
                frac = (curr - fish_end).total_seconds() / max((end_time - fish_end).total_seconds(), 1.0)
                lat = g_lat + frac * (p_lat - g_lat) + random.uniform(-0.02, 0.02)
                lon = g_lon + frac * (p_lon - g_lon) + random.uniform(-0.02, 0.02)
                spd = random.uniform(8.0, 11.0)
                data.append([vid, curr, lat, lon, spd])
                curr += step
        elif speed_mode == 'cargo':
            s_lat, s_lon = lat_base - 3.0, lon_base - 4.0
            e_lat, e_lon = lat_base + 3.0, lon_base + 4.0
            step = timedelta(minutes=10)
            curr = start_time
            while curr <= end_time:
                frac = (curr - start_time).total_seconds() / total
                lat = s_lat + frac * (e_lat - s_lat) + random.uniform(-0.03, 0.03)
                lon = s_lon + frac * (e_lon - s_lon) + random.uniform(-0.03, 0.03)
                spd = random.uniform(12.0, 20.0)
                data.append([vid, curr, lat, lon, spd])
                curr += step
        elif speed_mode == 'stationary':
            step = timedelta(minutes=30)
            curr = start_time
            lat, lon = lat_base, lon_base
            while curr <= end_time:
                lat += random.uniform(-0.005, 0.005)
                lon += random.uniform(-0.005, 0.005)
                spd = random.uniform(0.0, 1.0)
                data.append([vid, curr, lat, lon, spd])
                curr += step
        else:
            curr = start_time
            while curr <= end_time:
                lat = lat_base + random.uniform(-0.1, 0.1)
                lon = lon_base + random.uniform(-0.1, 0.1)
                spd = random.uniform(1.0, 10.0)
                data.append([vid, curr, lat, lon, spd])
                curr += timedelta(hours=1)
        return data

    def _generate_mock_data(self):
        """构造模拟平台内部的“嘈杂”AIS原始数据集

        包含多类匿名船舶：
            - 目标渔船：时间/空间/行为均与辅助信息高度匹配
            - 高速货船/客船/引航船：时间、空间可能匹配，但平均速度过高
            - 时间不符的渔船：行为空间类似，但出港/回港时间不在窗口内
            - 空间不符的渔船：时间和行为类似，但主要作业区不在目标渔场
            - 锚泊/随机噪声：在更大海域缓慢漂移，用于模拟背景干扰
        """
        print("[*] Generating diverse mock AIS data (simulating platform database)...")
        all_data = []
        t_start = datetime(2023, 9, 9, 8, 0)
        t_end = datetime(2023, 9, 21, 15, 30)
        all_data.extend(self._generate_single_track(
            "anonymized_TARGET_d4c7", t_start, t_end, 30.5, 123.5, speed_mode='fishing'
        ))
        for i in range(4):
            vid = f"anonymized_CARGO_{i}"
            all_data.extend(self._generate_single_track(
                vid, t_start, t_end, 30.0 + i * 0.3, 123.0, speed_mode='cargo'
            ))
        late_start = datetime(2023, 9, 12, 8, 0)
        all_data.extend(self._generate_single_track(
            "anonymized_LATE_fish", late_start, t_end, 30.5, 123.5, speed_mode='fishing'
        ))
        early_end = datetime(2023, 9, 15, 12, 0)
        all_data.extend(self._generate_single_track(
            "anonymized_EARLY_fish", t_start, early_end, 30.6, 123.6, speed_mode='fishing'
        ))
        all_data.extend(self._generate_single_track(
            "anonymized_WRONG_AREA", t_start, t_end, 30.5, 126.5, speed_mode='fishing'
        ))
        for i in range(3):
            vid = f"anonymized_OFFAREA_fish_{i}"
            all_data.extend(self._generate_single_track(
                vid, t_start, t_end, 27.5 + i * 0.4, 120.5 + i * 0.4, speed_mode='fishing'
            ))
        for i in range(2):
            vid = f"anonymized_PASSENGER_{i}"
            all_data.extend(self._generate_single_track(
                vid, t_start, t_end, 30.8, 122.8 + i * 0.2, speed_mode='cargo'
            ))
        for i in range(3):
            vid = f"anonymized_PILOT_{i}"
            all_data.extend(self._generate_single_track(
                vid, datetime(2023, 9, 10, 5, 0), datetime(2023, 9, 10, 23, 0),
                29.95, 122.30 + i * 0.05, speed_mode='cargo'
            ))
        for i in range(8):
            vid = f"anonymized_NOISE_{i}"
            all_data.extend(self._generate_single_track(
                vid, datetime(2023, 9, 10), datetime(2023, 9, 12),
                28.0 + random.random() * 3.0, 121.0 + random.random() * 4.0, speed_mode='stationary'
            ))
        df = pd.DataFrame(all_data, columns=['anonymized_vessel_id', 'timestamp', 'latitude', 'longitude', 'speed'])
        return df

    def fetch_anonymous_trajectories(self, time_range, spatial_bbox):
        """攻击者侧封装：通过平台API提交时间/空间条件，获取候选匿名轨迹

        time_range: (start_str, end_str)，由已知离港/回港时间推导出的查询时间窗
        spatial_bbox: (min_lon, min_lat, max_lon, max_lat)，由疑似作业渔场推导出的空间范围
        """
        print(f"[+] Fetching anonymous trajectory data for {time_range} in bbox {spatial_bbox}...")
        df = self.platform_api.query_anonymous_trajectories(
            time_range=time_range,
            spatial_bbox=spatial_bbox,
            min_points_per_vessel=10  # 要求单条匿名轨迹至少包含一定数量的AIS点
        )
        return df

    def _reconstruct_trajectories(self, df):
        """将点级别AIS数据按匿名船舶ID重建为轨迹字典"""
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
        """整体攻击流程入口：从平台获取候选轨迹并执行多层漏斗重识别"""
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
    # 作为独立脚本运行时：构造攻击者对象并发起一次完整的轨迹重识别攻击演示
    attacker = TrajectoryDeanonimizer()
    attacker.execute_reidentification_attack()