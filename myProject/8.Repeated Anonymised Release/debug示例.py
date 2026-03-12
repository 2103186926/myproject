import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import json
import os
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN

# ==========================================
# 1. 模拟环境：MockDataClient
# 用于替代真实的 platform_sdk，生成模拟的匿名数据
# ==========================================
class MockDataset:
    """模拟返回的数据集对象"""
    def __init__(self, data_array):
        self.ship_count = data_array # 模拟 xarray 或 pandas 的数据结构

class MockDataClient:
    """
    模拟云平台的数据接口。
    它会生成带有“噪声”和一条“隐藏轨迹”的网格数据。
    """
    def get_dataset(self, dataset_name, variables, aggregation, grid_size, time_range, anonymization_level):
        """
        模拟获取数据集的方法。
        参数：
            dataset_name (str): 数据集名称
            variables (list): 要查询的变量列表，这里是船舶计数
            aggregation (str): 聚合方式，这里是网格聚合
            grid_size (float): 网格大小，这里是0.1度
            time_range (tuple): 查询时间范围，格式：(开始时间, 结束时间)
            anonymization_level (str): 匿名化级别，这里是高匿名化
        返回：
            MockDataset: 模拟的数据集对象，包含船舶计数数据
        """
        print(f"    [MockServer] Generating data for range {time_range}...")

        # 创建一个 20x20 的网格区域
        grid_shape = (20, 20)
        # 1. 利用泊松分布生成背景噪声 (模拟正常的海洋交通或波浪干扰)
        data = np.random.poisson(lam=0.5, size=grid_shape).astype(float)
        
        # 2. 注入特定目标的移动轨迹 (这是攻击者想要还原的“敏感信息”)
        # 解析时间，根据时间步长移动“目标船舶”
        start_date = datetime.strptime(time_range[0], '%Y-%m-%d')  # 格式：2025-11-07
        # 简单模拟：根据天数决定船的位置。船从 (5,5) 开始，向右下方移动
        base_day = datetime.now() - timedelta(days=30)  # 基准时间为30天前
        day_diff = (start_date - base_day).days  # 计算查询时间与基准时间的天数差
        
        # 模拟船舶移动：每过一天，横纵坐标各+1
        ship_x = (5 + day_diff) % 20
        ship_y = (5 + day_diff) % 20
        
        # 在网格中增加这艘船的计数 (假设这是一个很大的信号)
        if 0 <= ship_x < 20 and 0 <= ship_y < 20:
            data[ship_x, ship_y] += 5.0 # 船只信号强度
            
        return MockDataset(data)

# ==========================================
# 2. 攻击类：AnonymityBreaker
# 实现了批量匿名数据重识别的核心逻辑
# ==========================================
class AnonymityBreaker:
    def __init__(self):
        # 初始化模拟的客户端
        self.data_client = MockDataClient()  # 模拟云平台数据接口
        self.dataset_versions = {}  # 存储不同版本的数据
        self.differential_results = {}  # 存储差分分析结果
        
    def fetch_anonymous_releases(self, dataset_name, version_count=5):
        """
        [Step 1] 获取多个版本的匿名化数据发布
        对应恶意行为：攻击者系统性地下载同一数据集的多个版本 [cite: 184]。
        参数：
            dataset_name (str): 数据集名称
            version_count (int): 要获取的版本数量，默认5个版本
        """
        print(f"[+] Fetching {version_count} versions of {dataset_name}...")
        for i in range(version_count):  # 循环获取多个版本的数据
            # 模拟生成不同时间切片的版本ID
            version_id = f"v{datetime.now().strftime('%Y%m%d')}_{i}"  # 版本ID格式：vYYYYMMDD_i

            # 构造查询时间窗口，模拟滑动窗口查询
            # 这里的关键是：每次查询的时间窗口略有不同，从而包含最新的位置信息
            start_time = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
            end_time = (datetime.now() - timedelta(days=28-i)).strftime('%Y-%m-%d')
            
            try:
                # 获取数据
                anonymous_data = self.data_client.get_dataset(
                    dataset_name=dataset_name,  # 数据集名称
                    variables=['ship_count'],  # 要查询的变量，这里是船舶计数
                    aggregation='grid',  # 聚合方式，这里是网格聚合
                    grid_size=0.1,  # 网格大小，这里是0.1度
                    time_range=(start_time, end_time),  # 查询时间范围，格式：(开始时间, 结束时间)
                    anonymization_level='high'  # 匿名化级别，这里是高匿名化
                )
                
                self.dataset_versions[version_id] = anonymous_data
                print(f"    Acquired version {version_id}: Grid Shape {anonymous_data.ship_count.shape}")
                
                # 模拟正常请求间隔，规避速率限制
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    Failed to get version {i}: {e}")
                continue
    
    def differential_analysis(self):
        """
        [Step 2] 执行差分分析
        对应恶意行为：对获取的多版本数据进行逐网格的差分计算 。
        """
        print("[+] Performing differential analysis between versions...")
        
        versions = list(self.dataset_versions.keys())  # 获取所有版本ID
        if len(versions) < 2:  # 版本长度不够
            print("    Need at least 2 versions for differential analysis")
            return
        
        for i in range(len(versions)-1):  # -1是因为下标
            v1, v2 = versions[i], versions[i+1]  # 前后版本对比
            data1 = self.dataset_versions[v1].ship_count  # 版本v1的船舶数量
            data2 = self.dataset_versions[v2].ship_count  # 版本v2的船舶数量
            
            print(f"    Comparing {v1} vs {v2}...")
            
            # [关键攻击逻辑] 计算绝对差异
            # 如果 data2 中船移动到了新位置，新位置会 +5，旧位置会 -5 (或归零)
            diff_absolute = data2 - data1
            
            # 识别显著变化的网格点(挑选出那些变化幅度超过阈值threshold的网格点)
            significant_changes = self._identify_significant_changes(data1, data2, diff_absolute,threshold=3.0)
            
            self.differential_results[f"{v1}_{v2}"] = {
                'absolute_diff': diff_absolute,  # 版本v2与版本v1的绝对差异
                'significant_changes': significant_changes  # 显著变化的网格点列表
            }
            print(f"        Found {len(significant_changes)} significant changes")
    
    def _identify_significant_changes(self, data1, data2, diff_absolute, threshold=3.0):
        """
        辅助函数：识别统计显著的变化点
        参数：
            data1 (pd.DataFrame): 版本v1的船舶数量
            data2 (pd.DataFrame): 版本v2的船舶数量
            diff_absolute (pd.DataFrame): 版本v2与版本v1的绝对差异
            threshold (float): 变化阈值，默认3.0
        返回：
            significant_points (list): 显著变化的网格点列表，每个点包含：
                - grid_i, grid_j: 网格坐标
                - abs_change: 绝对变化值
                - v1_val, v2_val: 对应版本的船舶数量
        """
        significant_points = []  # 显著变化的网格点列表
        rows, cols = diff_absolute.shape  # 网格形状，rows为纬度，cols为经度
        
        for i in range(rows):
            for j in range(cols):
                change_val = diff_absolute[i, j]  # 获取网格(i,j)的绝对变化值
                
                # 如果变化幅度超过阈值，记录为可疑点
                # 这通常意味着有一艘船进入或离开了该网格
                if abs(change_val) > threshold:
                    significant_points.append({
                        'grid_i': i,  # 纬度坐标
                        'grid_j': j,  # 经度坐标
                        'abs_change': float(change_val), # 转换为float以便JSON序列化
                        'v1_val': float(data1[i,j]),  # 版本v1的船舶数量
                        'v2_val': float(data2[i,j])   # 版本v2的船舶数量
                    })
        return significant_points
    
    def track_reconstruction(self):
        """
        [Step 3] 轨迹重建
        对应恶意行为：利用差分信息逐步还原原始轨迹或识别敏感区域 [cite: 178]。
        """
        print("[+] Attempting trajectory reconstruction...")
        
        all_changes = []  # 所有“正向变化”变化的网格点列表
        for key, result in self.differential_results.items():
            # 我们只关心“正向变化”（即有船只进入的网格）来作为轨迹点
            # 负向变化意味着船只离开
            for point in result['significant_changes']:
                if point['abs_change'] > 0: 
                    # 将 key (v1_v2) 作为时间戳的替代
                    point['version_pair'] = key
                    all_changes.append(point)
        
        if not all_changes:  # 如果all_changes为空
            print("    No significant changes found for reconstruction")
            return {}
        
        changes_df = pd.DataFrame(all_changes)
        
        # [关键攻击逻辑] 聚类分析
        # 使用 DBSCAN 识别空间上聚集的点，去除噪声
        # 对应恶意行为：执行空间聚类分析来识别变化点的空间模式 。
        coords = changes_df[['grid_i', 'grid_j']].values
        if len(coords) > 0:
            # eps=2 表示距离在2个网格内的点算作一类
            clustering = DBSCAN(eps=2, min_samples=1).fit(coords)
            changes_df['cluster'] = clustering.labels_
        else:
            changes_df['cluster'] = -1  # 无聚类结果时，设为-1

        # 简单的轨迹提取：按版本顺序连接聚类中心
        vessel_tracks = []  # 重建的船舶轨迹列表
        sorted_df = changes_df.sort_values('version_pair')  # 按版本对排序，确保按时间顺序连接
        
        print("    Reconstructed Path (Grid Coordinates):")
        for idx, row in sorted_df.iterrows():
            track_point = {
                'grid_x': int(row['grid_i']),
                'grid_y': int(row['grid_j']),
                'confidence': 0.95,  # 模拟高置信度
                'timestamp_idx': row['version_pair']
            }
            vessel_tracks.append(track_point)
            print(f"      -> Time {track_point['timestamp_idx']}: ({track_point['grid_x']}, {track_point['grid_y']})")
            
        return {'vessel_tracks': vessel_tracks, 'raw_changes': changes_df}

    def visualize_results(self, reconstruction_results):
        """可视化：生成热力图和轨迹图"""
        print("[+] Generating visualizations...")
        try:
            # 绘制累积差异图
            combined_diff = np.zeros((20, 20))  # 初始化20x20的差异矩阵
            for result in self.differential_results.values():  
                combined_diff += np.abs(result['absolute_diff'])  # 累加每个版本的绝对差异
            
            plt.figure(figsize=(20, 10))  # 创建20x10的图像窗口
            
            # 子图1：差异热力图
            plt.subplot(1, 2, 1)  # 1行2列的子图，当前为第1个
            plt.imshow(combined_diff, cmap='hot', interpolation='nearest')  # 显示差异热力图
            plt.title('Cumulative Differential Activity')  # 子图1标题
            plt.colorbar(label='Change Magnitude')  # 
            
            # 子图2：重建的轨迹
            plt.subplot(1, 2, 2)  # 1行2列的子图，当前为第2个
            tracks = reconstruction_results.get('vessel_tracks', [])  # 如果键不存在，返回空列表[]
            if tracks:
                xs = [t['grid_y'] for t in tracks] # 注意 matplotlib x是列(j), y是行(i)
                ys = [t['grid_x'] for t in tracks]
                plt.plot(xs, ys, 'b-o', label='Reconstructed Track')
                plt.xlim(0, 19)
                plt.ylim(19, 0) # 翻转Y轴以匹配矩阵视角
                plt.grid(True)
                plt.title('Reconstructed Vessel Trajectory')
                plt.legend()
            
            plt.tight_layout()
            # 保存图片而不是只显示，方便查看
            plt.savefig('attack_result_visualization.png')
            print("    Saved visualization to 'attack_result_visualization.png'")
            plt.show() 
            
        except Exception as e:
            print(f"    Visualization failed: {e}")

    def execute_attack(self):
        """执行完整攻击流程"""
        print("[+] Starting repeated release reidentification attack...")
        
        # 1. 获取数据：获取多个版本的匿名化数据发布
        self.fetch_anonymous_releases('anonymous_ship_aggregation', version_count=5)
        
        # 2. 差分分析：对比不同版本的匿名化数据发布，识别显著变化
        self.differential_analysis()
        
        # 3. 轨迹重建：利用差分信息逐步还原原始轨迹或识别敏感区域
        results = self.track_reconstruction()
        
        # 4. 可视化
        if results:  # 轨迹重建结果不为空
            self.visualize_results(results)  # 可视化重建的轨迹

            # 5. 保存结果 (模拟数据窃取)
            # 对应恶意行为：输出包含高精度的位置信息和重建的轨迹模式 [cite: 193]。
            with open('reidentification_results.json', 'w') as f:
                # 简单处理用于序列化
                serializable_tracks = results['vessel_tracks']
                json.dump(serializable_tracks, f, indent=2)  # 
            print("[+] Results saved to reidentification_results.json")
        
        print("[+] Reidentification attack completed successfully")

# ==========================================
# 程序入口
# ==========================================
if __name__ == "__main__":
    attacker = AnonymityBreaker()  # 初始化攻击类
    attacker.execute_attack()   # 执行攻击流程