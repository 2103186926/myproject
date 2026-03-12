import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import json
import random
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from scipy import stats

# ==========================================
# 1. 环境模拟：MockDataClient (保持 V2.0 逻辑)
# ==========================================
class MockDataset:
    def __init__(self, data_array):
        self.ship_count = data_array  # 船舶计数数组

class MockDataClient:
    """
    模拟云平台数据接口 (Target: Taiwan Strait)
    范围: Lat 22.0-26.0 N, Lon 117.0-122.0 E
    精度: 0.1 度
    """
    def __init__(self):
        # 定义敏感海域网格参数
        self.lat_min, self.lat_max = 22.0, 26.0  # 纬度范围
        self.lon_min, self.lon_max = 117.0, 122.0  # 经度范围
        self.grid_size = 0.1  # 网格大小为 0.1 度
        
        self.n_rows = int((self.lat_max - self.lat_min) / self.grid_size) # 40 行
        self.n_cols = int((self.lon_max - self.lon_min) / self.grid_size) # 50 列
        
        self.track_max_step = {}
        # 预生成真实的“Ground Truth”轨迹
        self.ground_truth_tracks = self._generate_realistic_tracks()

    def _latlon_to_grid(self, lat, lon):
        """经纬度转网格索引
        参数：
            lat (float): 纬度
            lon (float): 经度
        返回值：
            r (int): 网格行索引
            c (int): 网格列索引
        """
        r = int((self.lat_max - lat) / self.grid_size) # 纬度向下为正行数
        c = int((lon - self.lon_min) / self.grid_size)
        return r, c

    def _generate_realistic_tracks(self):
        """使用相关随机游走 (Correlated Random Walk) 生成符合物理规律的轨迹"""
        tracks = {}  # 存储所有轨迹的字典
        base_time = datetime.now() - timedelta(days=30)  # 从 30 天前开始模拟
        
        # --- Vessel A: 从厦门附近开往台湾南部 (东南向) ---
        path_A, max_A = self._simulate_crw_path(
            start_pos=(24.5, 118.2),  # 厦门附近
            speed_knots=12.0,  # 12 节 knot
            heading_deg=135,  # 东南
            duration_hours=120,  # 120 小时(5天)
            base_time=base_time  # 从 30 天前开始
        )
        tracks['Vessel_A'] = path_A  # 轨迹点列表
        self.track_max_step['Vessel_A'] = max_A  # 轨迹的相邻点最大步长
        
        # --- Vessel B: 在海峡中线附近巡逻 ---
        # tracks['Vessel_B'] = self._simulate_crw_path(
        #     start_pos=(23.5, 119.5),    # 海峡中线附近
        #     speed_knots=10.0,    # 10 节 knot
        #     heading_deg=45, # 东北
        #     duration_hours=120,   # 120 小时
        #     base_time=base_time,   # 从 30 天前开始
        #     turn_rate=15.0    # 15 度/小时
        # )
        return tracks

    #! 新增：tracks轨迹实现可视化
    def visualize_tracks(self, save_path='ground_truth_tracks.png'):
        '''
        可视化模拟的船舶轨迹。
        参数：
            save_path (str, 可选): 保存图片的路径，默认值为 'ground_truth_tracks.png'
        '''
        fig, ax = plt.subplots(figsize=(9, 8))
        ax.set_xlim(self.lon_min, self.lon_max)
        ax.set_ylim(self.lat_min, self.lat_max)
        ax.grid(True, linestyle='--', alpha=0.5)
        colors = ['#00ff00', '#00ffff', '#ff00ff', '#ffff00']
        for i, (vessel_id, points) in enumerate(self.ground_truth_tracks.items()):
            lats = [p['lat'] for p in points]
            lons = [p['lon'] for p in points]
            c = colors[i % len(colors)]
            ax.plot(lons, lats, marker='o', linestyle='-', color=c, linewidth=2, label=vessel_id, markersize=5)
            if lats and lons:
                ax.text(lons[0], lats[0], 'Start', fontsize=9, color='blue', fontweight='bold')
                ax.text(lons[-1], lats[-1], 'End', fontsize=9, color='red', fontweight='bold')
        ax.set_title('Generated Ground Truth Tracks (Taiwan Strait)')
        ax.set_xlabel('Longitude (E)')
        ax.set_ylabel('Latitude (N)')
        ax.legend()
        plt.tight_layout()
        plt.savefig(save_path, dpi=300)
        plt.show()

    def _simulate_crw_path(self, start_pos, speed_knots, heading_deg, duration_hours, base_time, turn_rate=5.0):
        """生成单条轨迹的核心算法
        参数：
            start_pos (tuple): 初始位置，格式为 (纬度, 经度)
            speed_knots (float): 速度，单位为 knot
            heading_deg (float): 初始航向角度，单位为度
            duration_hours (int): 轨迹持续时间，单位为小时
            base_time (datetime): 轨迹开始时间
            turn_rate (float, 可选): 随机转向角度，单位为度/小时，默认值为 5.0
        返回：
            list: 轨迹点的列表，每个点包含时间和经纬度
        """
        path = []  # 存储轨迹点的列表
        lat, lon = start_pos  # 初始位置
        # 航向角度、速度单位转换（最复杂但最重要的转换）
        heading = np.radians(heading_deg)  # 初始航向角度 (弧度)  numpy.radians将角度从度转换为弧度（比如：180度 = 3.14弧度）
        speed_deg = (speed_knots * 1.852) / 111.0  # 每小时移动的角度 (弧度)
        max_length = 0.0  # 相邻点最大步长
        for t in range(duration_hours):
            current_time = base_time + timedelta(hours=t)  # 当前时间
            path.append({'time': current_time, 'lat': lat, 'lon': lon})
            # 位置更新（核心移动公式）
            new_lat = lat + speed_deg * np.cos(heading)  # 纬度变化
            new_lon = lon + speed_deg * np.sin(heading)  # 经度变化

            step_len = float(np.sqrt((new_lat - lat) ** 2 + (new_lon - lon) ** 2))  # 经纬度平面上的欧氏距离（单位为度）
            if step_len > max_length:
                max_length = step_len  # 更新最大步长
            # 添加正态分布随机噪声：实现随机游走的关键部分
            noise = np.radians(np.random.normal(0, turn_rate))  # 随机转向角度 (弧度)  turn_rate越大，轨迹越曲折；越小，轨迹越直
            heading += noise  # 更新航向角度
            lat, lon = new_lat, new_lon
        return path, max_length

    def get_dataset(self, dataset_name, variables, aggregation, grid_size, time_range, anonymization_level):
        '''
        参数：
            dataset_name (str): 数据集名称
            variables (list): 要查询的变量，这里是船舶计数
            aggregation (str): 聚合方式，这里是网格聚合
            grid_size (float): 网格大小，这里是0.1度
            time_range (tuple): 查询时间范围，格式为('2023-01-01 00:00:00', '2023-01-02 00:00:00')
            anonymization_level (str): 匿名化级别，这里是高匿名化
        返回：
            MockDataset: 包含船舶计数的模拟数据集
        '''
        print(f"    [MockServer] Generating data for window {time_range}...")
        
        # 1. 生成稀疏背景噪声  lam=0.1表示平均每个网格有0.1艘船  lam越小，背景噪声越稀疏
        data = np.random.poisson(lam=0.05, size=(self.n_rows, self.n_cols)).astype(float)  # 泊松分布生成稀疏背景噪声 
        
        # 2. 注入真实轨迹信号
        q_start = datetime.strptime(time_range[0], '%Y-%m-%d %H:%M:%S')
        q_end = datetime.strptime(time_range[1], '%Y-%m-%d %H:%M:%S')
        
        for vessel_id, track in self.ground_truth_tracks.items():
            for point in track:
                if q_start <= point['time'] <= q_end:
                    r, c = self._latlon_to_grid(point['lat'], point['lon'])  # 经纬度转网格索引
                    if 0 <= r < self.n_rows and 0 <= c < self.n_cols:
                        # data[r, c] += 2.0  # 注入真实轨迹信号
                        # 将固定的 +2.0 改为加权随机数 1-5 ，权重为 [5,4,3,2,1] ，保证数值从 1 到 5 的出现频率逐步降低
                        data[r, c] += float(random.choices([1, 2, 3, 4, 5], weights=[5, 4, 3, 2, 1], k=1)[0])
        
        return MockDataset(data)  # 返回包含船舶计数的模拟数据集

# ==========================================
# 2. 攻击者逻辑: AnonymityBreaker (Pro with Visualization)
# ==========================================
class AnonymityBreaker:
    def __init__(self):
        self.data_client = MockDataClient()  # 模拟数据客户端
        self.dataset_versions = {}  # 存储不同版本数据集的字典
        self.differential_results = {}  # 存储不同版本数据集差异的字典
        # 坐标系统参数 （台湾海峡区域）
        self.lat_max = 26.0
        self.lat_min = 22.0
        self.lon_min = 117.0
        self.lon_max = 122.0
        self.grid_size = 0.1
        
        # [恢复功能] 用于存储累积的差分热力图数据
        # 40行 x 50列
        self.n_rows = int((self.lat_max - self.lat_min) / self.grid_size)
        self.n_cols = int((self.lon_max - self.lon_min) / self.grid_size)
        self.cumulative_diff_matrix = np.zeros((self.n_rows, self.n_cols))  # 存储累积差分信号的矩阵

    def _grid_to_latlon(self, row, col):
        """网格索引转真实经纬度"""
        lat = self.lat_max - (row * self.grid_size) - (self.grid_size/2)  # 纬度 = 最大纬度 - 行索引 * 网格大小 - 网格大小/2
        lon = self.lon_min + (col * self.grid_size) + (self.grid_size/2)  # 经度 = 最小经度 + 列索引 * 网格大小 + 网格大小/2
        return round(lat, 3), round(lon, 3)  # 返回四舍五入到3位小数的纬度和经度

    def fetch_anonymous_releases(self, dataset_name, version_count=5):
        """[Step 1] 获取数据：滑动窗口查询
        参数：
            dataset_name (str): 数据集名称
            version_count (int): 要获取的版本数量，默认5个版本
        """
        print(f"[+] Fetching {version_count} versions of {dataset_name} (Taiwan Strait Area)...")
        base_time = datetime.now() - timedelta(days=30)  # 从当前时间开始，往前推30天
        
        for i in range(version_count):
            version_id = f"v_seq_{i}"  # 每个版本的版本ID，格式为v_seq_0, v_seq_1, ..., v_seq_{version_count-1}
            t_start = base_time + timedelta(hours=i)  # 每个版本的查询开始时间，从base_time开始，每个版本间隔1小时
            t_end = base_time + timedelta(hours=i+1)  # 每个版本的查询结束时间，从base_time开始，每个版本间隔1小时
            time_str_fmt = '%Y-%m-%d %H:%M:%S'  # 时间格式，这里是'年-月-日 时:分:秒'
            
            try:
                anonymous_data = self.data_client.get_dataset(
                    dataset_name=dataset_name,   # 数据集名称
                    variables=['ship_count'],    # 要查询的变量，这里是船舶计数
                    aggregation='grid',  # 聚合方式，这里是网格聚合
                    grid_size=0.1,    # 网格大小，这里是0.1度
                    time_range=(t_start.strftime(time_str_fmt), t_end.strftime(time_str_fmt)),  # 查询时间范围
                    anonymization_level='high'  # 匿名化级别，这里是高匿名化
                )

                self.dataset_versions[version_id] = anonymous_data  # 存储每个版本的匿名数据集
                print(f"    Acquired {version_id}: {t_start.strftime('%H:%M')} -> {t_end.strftime('%H:%M')}")
                time.sleep(0.1)  # 模拟查询延迟，避免对服务器压力过大
            except Exception as e:
                print(f"    Failed: {e}")

    def differential_analysis(self):
        """[Step 2] 差分分析与信号提取"""
        print("[+] Performing statistical differential analysis...")
        versions = list(self.dataset_versions.keys())  # 获取所有版本的ID
        for v_id in versions:
            data = self.dataset_versions[v_id].ship_count  # 获取当前版本的船舶计数数据
            
            # [恢复功能] 累积差分信号用于热力图
            # 这里的逻辑是：将每帧检测到的“非背景”信号叠加起来
            # 这样热力图就能显示出船只经过的“痕迹” （大于0.5的信号被认为是船只）
            self.cumulative_diff_matrix += np.where(data > 0.5, 1.0, 0.0)  # 对大于0.5的信号进行二值化，再进行累加
            
            # 统计学去噪与信号提取
            mu = np.mean(data)  # 求二维数组中所有元素的平均值
            sigma = np.std(data)  # 求二维数组中所有元素的标准差
            potential_targets = []  # 存储所有潜在目标的列表
            rows, cols = data.shape
            
            for r in range(rows):  # 遍历每一行
                for c in range(cols):  # 遍历每一列
                    val = data[r, c]  # 遍历每个网格值
                    if val > 0.5: # 简化版Z-Score，假设背景很干净
                        lat, lon = self._grid_to_latlon(r, c)  # 将网格索引转换为真实经纬度
                        potential_targets.append({
                            'grid_r': r, 'grid_c': c, 'lat': lat, 'lon': lon, 'val': val, 'version': v_id
                        })
            
            self.differential_results[v_id] = potential_targets
            print(f"    Analyzing {v_id}: Found {len(potential_targets)} potential signals")

    def track_reconstruction(self):
        """[Step 3] 轨迹重建"""
        print("[+] Attempting multi-target trajectory reconstruction...")
        all_points = []  # 存储所有潜在目标点的列表
        for vid, points in self.differential_results.items():  # 遍历字典中每一个K-V对
            for p in points:  # 遍历列表中每一个值
                p['time_idx'] = int(vid.split('_')[-1])  # 从版本ID中提取时间索引，例如v_seq_0 -> 0
                all_points.append(p)  # 将每个点又加入了列表中，每个点都有了时间索引
        
        if not all_points: return {}  # 如果没有任何潜在目标点，直接返回空字典
        
        df = pd.DataFrame(all_points)
        
        # DBSCAN 空间聚类
        coords = df[['lat', 'lon']].values
        #!  新增：聚类 eps 动态绑定到最大步长
        eps_val = max(self.data_client.track_max_step.values()) if self.data_client.track_max_step else 0.2
        clustering = DBSCAN(eps=eps_val, min_samples=2).fit(coords)  # 对所有潜在目标点进行空间聚类，eps=0.2表示半径为0.2度，min_samples=5表示一个簇至少要有5个点
        df['cluster'] = clustering.labels_  # 为每个点分配聚类标签，-1表示噪声点
        
        reconstructed_tracks = {}  # 存储所有重建轨迹的字典
        unique_clusters = set(df['cluster'])  # 获取所有唯一的聚类标签(set无序不重复)
        if -1 in unique_clusters: unique_clusters.remove(-1)  # 从唯一聚类标签中移除噪声点（簇为-1的标签）
        
        print(f"    Identified {len(unique_clusters)} distinct vessel tracks.")
        
        for cluster_id in unique_clusters:  # N个簇对应N条轨迹
            track_points = df[df['cluster'] == cluster_id].sort_values('time_idx')  # 布尔索引+排序，获取当前簇的所有点，按时间索引升序排列
            processed_track = []  # 存储当前簇的轨迹点列表
            for _, row in track_points.iterrows():
                confidence = 0.5 + (0.3 if abs(row['val'] - 1.0) < 0.1 else 0)  # 若信号值接近1.0，则置信度高0.3，否则0.5
                processed_track.append({
                    'lat': row['lat'], 'lon': row['lon'],
                    'time_seq': row['time_idx'], 'confidence': confidence
                })  # 为每个点添加置信度

            reconstructed_tracks[f"Target_{cluster_id}"] = processed_track  # 为当前簇添加轨迹到字典中

            start, end = processed_track[0], processed_track[-1]  # 获取轨迹的起始点和结束点
            print(f"    [Target_{cluster_id}] Path: ({start['lat']},{start['lon']}) -> ... -> ({end['lat']},{end['lon']})")

        return reconstructed_tracks

    def visualize_results(self, tracks):
        """
        [恢复功能] 生成双视图：左侧热力图，右侧轨迹图
        """
        print("[+] Generating combined visualization: attack_result_visualization.png")
        try:
            # 创建 1行2列 的图布
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
            
            # --- 子图 1: 差分累积热力图 (Differential Heatmap) ---
            # 使用 extent 将网格索引映射回经纬度范围
            # 注意：imshow 默认原点在左上角 (Row 0)，对应的应该是 lat_max
            # 所以 extent 顺序是 [left, right, bottom, top] = [lon_min, lon_max, lat_min, lat_max]
            im = ax1.imshow(
                self.cumulative_diff_matrix,  # 差分累积矩阵
                cmap='hot',   # 热图颜色映射，值越高越红
                interpolation='nearest',  # 最近邻插值，避免像素化
                extent=[self.lon_min, self.lon_max, self.lat_min, self.lat_max],  # 经纬度范围
                aspect='auto'  # 自动调整纵横比，保持网格单元格的正方形
            )
            ax1.set_title(f'Cumulative Activity Heatmap (Grid Precision: {self.grid_size}°)')
            ax1.set_xlabel('Longitude (E)')
            ax1.set_ylabel('Latitude (N)')
            ax1.grid(True, linestyle='--', alpha=0.3)  # 绘制网格线，透明度0.3
            plt.colorbar(im, ax=ax1, label='Signal Accumulation Count')  # 为热力图添加颜色条，显示信号累加计数

            # --- 子图 2: 重建轨迹图 (Reconstructed Trajectories) ---
            # 绘制背景
            ax2.set_xlim(self.lon_min, self.lon_max)  # 设置x轴范围为经纬度范围
            ax2.set_ylim(self.lat_min, self.lat_max)  # 设置y轴范围为经纬度范围
            ax2.grid(True, linestyle='--', alpha=0.5)  # 绘制网格线，透明度0.5
            
            colors = ['#00ff00', '#00ffff', '#ff00ff', '#ffff00', '#ff0000', '#0000ff', '#00ff00'] # 鲜艳的颜色方便观察
            
            # 绘制每条识别出的轨迹
            for i, (target_id, points) in enumerate(tracks.items()):
                lats = [p['lat'] for p in points]  # 提取轨迹点的纬度列表
                lons = [p['lon'] for p in points]  # 提取轨迹点的经度列表
                c = colors[i % len(colors)]  # 为每个轨迹分配不同颜色，循环使用颜色列表
                
                # 绘制线段和点
                # marker='o'表示每个点都用圆圈标记
                # linestyle='-'表示用实线连接点
                # linewidth=2表示线宽为2
                # label=target_id表示为每条轨迹添加标签，用于图例
                # markersize=5表示每个点的标记大小为5
                ax2.plot(lons, lats, marker='o', linestyle='-', color=c, linewidth=2, label=target_id, markersize=5)  
                
                # 标记起点和终点
                ax2.text(lons[0], lats[0], 'Start', fontsize=9, color='blue', fontweight='bold')
                ax2.text(lons[-1], lats[-1], 'End', fontsize=9, color='red', fontweight='bold')

            ax2.set_title('Reconstructed Vessel Trajectories (Taiwan Strait)')
            ax2.set_xlabel('Longitude (E)')
            ax2.set_ylabel('Latitude (N)')
            ax2.legend()

            plt.tight_layout()
            plt.savefig('attack_result_visualization.png', dpi=300)
            print("    Visualization saved to 'attack_result_visualization.png'")
            plt.show()
            
        except Exception as e:
            print(f"    Viz Error: {e}")
            import traceback
            traceback.print_exc()

    def execute_attack(self):
        print("[+] Starting Batch Anonymous Data Re-identification (Target: Taiwan Strait)...")
        #! 新增：可视化原始轨迹
        self.data_client.visualize_tracks(save_path='ground_truth_tracks.png')

        # 1. 获取数据 (10个时间切片)
        self.fetch_anonymous_releases('strait_shipping_density', version_count=10)
        # 2. 统计分析
        self.differential_analysis()
        # 3. 轨迹重建
        tracks = self.track_reconstruction()
        # 4. 可视化与导出
        if tracks:
            self.visualize_results(tracks)
            with open('strait_targets.json', 'w') as f:
                json.dump(tracks, f, indent=2)
            print("[+] Attack Completed. Sensitive targets exported.")

if __name__ == "__main__":
    attacker = AnonymityBreaker()
    attacker.execute_attack()