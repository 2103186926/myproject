# malicious_trajectory_reidentification.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import Point, LineString
from platform_sdk.data_client import DataClient
import time

class TrajectoryDeanonimizer:
    def __init__(self):
        self.data_client = DataClient()
        # 从公开信息中收集到的目标船舶知识
        self.target_vessel_info = {
            'known_name': '浙渔XXX',
            'home_port': '舟山港',
            # 关键：已知的特定时间点信息（从公开报道、AIS历史网站等获取）
            'known_events': [
                {'type': 'departure', 'port': '舟山港', 'time': '2023-09-10 08:00:00'},
                {'type': 'return', 'port': '舟山港', 'time': '2023-09-20 17:30:00'},
                # 可能还有在特定渔市被观察到的报告
            ],
            # 已知的船舶特性（从公开资料获取）
            'vessel_type': '拖网渔船',
            'length': 45.2,  # 米
            # 已知的粗略作业区域（从渔业报告推断）
            'suspected_fishing_grounds': {
                'name': '舟山外海渔场',
                'bbox': [122.0, 29.5, 125.0, 32.0]  # min_lon, min_lat, max_lon, max_lat
            }
        }

    def fetch_anonymous_trajectories(self, time_range, spatial_bbox):
        """从平台获取匿名化的轨迹数据"""
        print(f"[+] Fetching anonymous trajectory data for {time_range} in bbox {spatial_bbox}...")
        try:
            # 假设平台提供聚合查询接口，返回的是匿名轨迹段
            # 每条轨迹有一个随机化的 vessel_id，无法直接关联真实船舶
            query = f"""
            SELECT 
                anonymized_vessel_id, 
                timestamp,
                latitude,
                longitude,
                speed,
                course
            FROM 
                anonymous_ais_data
            WHERE 
                timestamp BETWEEN '{time_range[0]}' AND '{time_range[1]}'
                AND longitude BETWEEN {spatial_bbox[0]} AND {spatial_bbox[2]}
                AND latitude BETWEEN {spatial_bbox[1]} AND {spatial_bbox[3]}
            ORDER BY 
                anonymized_vessel_id, timestamp
            """
            df = self.data_client.execute_query(query)
            print(f"    Retrieved {len(df)} data points for {df['anonymized_vessel_id'].nunique()} anonymous vessels.")
            return df
        except Exception as e:
            print(f"    Query failed: {e}")
            return pd.DataFrame()

    def _reconstruct_trajectories(self, df):
        """将数据点按匿名ID分组，重建为轨迹对象"""
        trajectories = {}
        for vessel_id, group in df.groupby('anonymized_vessel_id'):
            group = group.sort_values('timestamp')
            geometry = LineString(zip(group.longitude, group.latitude))
            trajectories[vessel_id] = {
                'df': group,
                'geometry': geometry,
                'start_time': group.timestamp.min(),
                'end_time': group.timestamp.max()
            }
        return trajectories

    def _filter_by_known_events(self, trajectories):
        """利用已知的离港/到港时间过滤候选轨迹"""
        print("[+] Filtering trajectories using known port events...")
        candidate_vessels = []
        dep_time = datetime.strptime(self.target_vessel_info['known_events'][0]['time'], '%Y-%m-%d %H:%M:%S')
        ret_time = datetime.strptime(self.target_vessel_info['known_events'][1]['time'], '%Y-%m-%d %H:%M:%S')
        time_tolerance = timedelta(hours=6)  # 允许的时间误差

        for vid, traj in trajectories.items():
            # 检查轨迹时间范围是否覆盖已知的航行期
            covers_voyage = (traj['start_time'] <= dep_time + time_tolerance) and (traj['end_time'] >= ret_time - time_tolerance)
            
            # 更精确的检查：轨迹在离港时间后不久是否在港口附近消失（离港）
            # 在返港时间前不久是否出现在港口附近（返港）
            # 这里简化处理
            if covers_voyage:
                candidate_vessels.append(vid)
                print(f"    Candidate Vessel ID {vid}: Covers voyage period ({traj['start_time']} to {traj['end_time']})")

        return candidate_vessels

    def _analyze_behavioral_patterns(self, trajectory_df):
        """分析轨迹行为模式（如捕鱼行为），与目标船舶类型匹配"""
        print("[+] Analyzing behavioral patterns...")
        # 计算一些统计特征
        stats = {
            'avg_speed': trajectory_df['speed'].mean(),
            'max_speed': trajectory_df['speed'].max(),
            'std_speed': trajectory_df['speed'].std(),
            'avg_daily_distance': self._calculate_daily_distance(trajectory_df),
            'fishing_behavior_score': self._detect_fishing_patterns(trajectory_df)
        }
        return stats

    def _calculate_daily_distance(self, df):
        """估算日均航行距离"""
        df = df.sort_values('timestamp')
        daily_dist = 0
        prev_pos = None
        prev_time = None
        for _, row in df.iterrows():
            curr_pos = (row['latitude'], row['longitude'])
            curr_time = row['timestamp']
            if prev_pos is not None:
                # 简化计算，使用 Haversine 公式更佳
                dist = np.sqrt((curr_pos[0]-prev_pos[0])**2 + (curr_pos[1]-prev_pos[1])**2) * 111 # 近似公里
                time_diff = (curr_time - prev_time).total_seconds() / 3600
                if time_diff < 1:  # 忽略时间间隔过大的点
                    daily_dist += dist
            prev_pos = curr_pos
            prev_time = curr_time
        voyage_days = (df.timestamp.max() - df.timestamp.min()).days
        return daily_dist / voyage_days if voyage_days > 0 else 0

    def _detect_fishing_patterns(self, df):
        """检测轨迹中的捕鱼行为模式（如低速、盘旋）"""
        # 简单规则：低速(<2节)点占比
        low_speed_points = df[df['speed'] < 2] # 2 knots
        fishing_score = len(low_speed_points) / len(df) if len(df) > 0 else 0
        
        # 更高级的方法可分析轨迹转弯率、循环等
        return fishing_score

    def _correlate_with_fishing_grounds(self, trajectory_gdf):
        """分析轨迹与疑似渔场的重叠度"""
        fishing_ground_bbox = self.target_vessel_info['suspected_fishing_grounds']['bbox']
        min_lon, min_lat, max_lon, max_lat = fishing_ground_bbox
        
        points_in_ground = trajectory_gdf[
            (trajectory_gdf.longitude >= min_lon) & 
            (trajectory_gdf.longitude <= max_lon) & 
            (trajectory_gdf.latitude >= min_lat) & 
            (trajectory_gdf.latitude <= max_lat)
        ]
        overlap_ratio = len(points_in_ground) / len(trajectory_gdf) if len(trajectory_gdf) > 0 else 0
        return overlap_ratio

    def execute_reidentification_attack(self):
        """执行重识别攻击"""
        print(f"[+] Starting trajectory re-identification attack for vessel: {self.target_vessel_info['known_name']}")
        
        # 1. 根据已知事件确定查询的时间和空间范围
        time_range = (
            (datetime.strptime(self.target_vessel_info['known_events'][0]['time'], '%Y-%m-%d %H:%M:%S') - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            (datetime.strptime(self.target_vessel_info['known_events'][1]['time'], '%Y-%m-%d %H:%M:%S') + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        )
        spatial_bbox = self.target_vessel_info['suspected_fishing_grounds']['bbox'] # 主要查询渔场区域
        spatial_bbox = [spatial_bbox[0]-1, spatial_bbox[1]-1, spatial_bbox[2]+1, spatial_bbox[3]+1] # 扩大范围

        # 2. 获取匿名轨迹数据
        df_raw = self.fetch_anonymous_trajectories(time_range, spatial_bbox)
        if df_raw.empty:
            return
        trajectories = self._reconstruct_trajectories(df_raw)

        # 3. 基于已知事件进行初步过滤
        candidate_ids = self._filter_by_known_events(trajectories)
        print(f"    Initial candidates after time filtering: {len(candidate_ids)} vessels.")

        # 4. 对候选轨迹进行详细分析
        best_candidate = None
        best_score = -1
        candidate_results = []

        for cid in candidate_ids:
            print(f"    Analyzing candidate vessel {cid}...")
            traj_data = trajectories[cid]
            behavior_stats = self._analyze_behavioral_patterns(traj_data['df'])
            fishing_ground_overlap = self._correlate_with_fishing_grounds(traj_data['df'])

            # 计算一个综合匹配分数
            score = 0
            # 规则1：如果是拖网渔船，低速（可能正在作业）时间占比应该较高
            if self.target_vessel_info['vessel_type'] == '拖网渔船':
                score += behavior_stats['fishing_behavior_score'] * 0.4
            
            # 规则2：与已知渔场的重叠度
            score += fishing_ground_overlap * 0.4

            # 规则3：平均速度应符合渔船特征（不是高速货轮）
            if 5 < behavior_stats['avg_speed'] < 15: # 假设渔船的合理航速范围
                score += 0.2

            print(f"        Score: {score:.3f} (Fishing Behavior: {behavior_stats['fishing_behavior_score']:.3f}, Ground Overlap: {fishing_ground_overlap:.3f})")
            
            candidate_results.append({'id': cid, 'score': score, 'stats': behavior_stats})
            
            if score > best_score:
                best_score = score
                best_candidate = cid

        # 5. 输出结果
        if best_candidate:
            print("="*60)
            print(" RE-IDENTIFICATION RESULT ")
            print("="*60)
            print(f" Target Vessel: {self.target_vessel_info['known_name']}")
            print(f" Most Likely Anonymous ID: {best_candidate}")
            print(f" Confidence Score: {best_score:.4f}")
            print(f" Trajectory Period: {trajectories[best_candidate]['start_time']} to {trajectories[best_candidate]['end_time']}")
            print(" Top Candidates:")
            candidate_results.sort(key=lambda x: x['score'], reverse=True)
            for i, cr in enumerate(candidate_results[:3]): # 显示前三名
                print(f"  {i+1}. ID: {cr['id']}, Score: {cr['score']:.4f}")
            print("="*60)

            # 保存推断出的轨迹
            output_file = f"reidentified_trajectory_{self.target_vessel_info['known_name'].replace(' ', '_')}.csv"
            trajectories[best_candidate]['df'].to_csv(output_file, index=False)
            print(f" Reidentified trajectory saved to {output_file}")
        else:
            print("[-] Re-identification attempt unsuccessful. No strong candidate found.")

def main():
    attacker = TrajectoryDeanonimizer()
    attacker.execute_reidentification_attack()

if __name__ == "__main__":
    main()