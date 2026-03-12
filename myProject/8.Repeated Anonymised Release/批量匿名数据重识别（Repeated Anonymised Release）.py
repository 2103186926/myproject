# malicious_repeated_release.py
import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime, timedelta
import geopandas as gpd
from scipy import stats
import matplotlib.pyplot as plt
from platform_sdk.data_client import DataClient

class AnonymityBreaker:
    def __init__(self):
        self.data_client = DataClient()
        self.dataset_versions = {}  # 存储不同版本的数据
        self.differential_results = {}
        
    def fetch_anonymous_releases(self, dataset_name, version_count=5):
        """获取多个版本的匿名化数据发布"""
        print(f"[+] Fetching {version_count} versions of {dataset_name}...")
        
        for i in range(version_count):
            # 模拟获取不同版本的数据（可能通过不同时间查询或不同聚合参数）
            version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
            try:
                # 获取匿名聚合数据 - 例如网格化的船舶计数
                anonymous_data = self.data_client.get_dataset(
                    dataset_name=dataset_name,
                    variables=['ship_count'],
                    aggregation='grid',
                    grid_size=0.1,  # 0.1度网格
                    time_range=(
                        (datetime.now() - timedelta(days=30-i*2)).strftime('%Y-%m-%d'),
                        (datetime.now() - timedelta(days=28-i*2)).strftime('%Y-%m-%d')
                    ),
                    anonymization_level='high'
                )
                
                self.dataset_versions[version_id] = anonymous_data
                print(f"    Acquired version {version_id}: {anonymous_data.ship_count.shape}")
                
                # 添加随机延迟，模拟正常数据访问模式
                time.sleep(np.random.uniform(1, 3))
                
            except Exception as e:
                print(f"    Failed to get version {i}: {e}")
                continue
    
    def differential_analysis(self):
        """执行差分分析，识别版本间的差异"""
        print("[+] Performing differential analysis between versions...")
        
        versions = list(self.dataset_versions.keys())
        if len(versions) < 2:
            print("    Need at least 2 versions for differential analysis")
            return
        
        for i in range(len(versions)-1):
            v1, v2 = versions[i], versions[i+1]
            data1 = self.dataset_versions[v1]['ship_count']
            data2 = self.dataset_versions[v2]['ship_count']
            
            print(f"    Comparing {v1} vs {v2}...")
            
            # 计算绝对差异
            diff_absolute = data2 - data1
            diff_relative = (data2 - data1) / (data1 + 1e-10)  # 避免除零
            
            # 识别显著变化的网格点
            significant_changes = self._identify_significant_changes(data1, data2)
            
            self.differential_results[f"{v1}_{v2}"] = {
                'absolute_diff': diff_absolute,
                'relative_diff': diff_relative,
                'significant_changes': significant_changes
            }
            
            print(f"        Found {len(significant_changes)} significant changes")
    
    def _identify_significant_changes(self, data1, data2, threshold=2.0):
        """识别统计显著的变化点"""
        significant_points = []
        
        # 将数据转换为二维网格
        if hasattr(data1, 'values'):
            data1 = data1.values
            data2 = data2.values
        
        for i in range(data1.shape[0]):
            for j in range(data1.shape[1]):
                val1, val2 = data1[i, j], data2[i, j]
                
                # 忽略缺失值
                if np.isnan(val1) or np.isnan(val2):
                    continue
                
                # 简单的显著性检测：大的绝对变化或相对变化
                abs_change = abs(val2 - val1)
                if val1 > 0:
                    rel_change = abs_change / val1
                else:
                    rel_change = abs_change
                
                # 检测显著变化点
                if abs_change > threshold or rel_change > 0.5:  # 可调整阈值
                    significant_points.append({
                        'grid_i': i,
                        'grid_j': j,
                        'value_v1': val1,
                        'value_v2': val2,
                        'abs_change': abs_change,
                        'rel_change': rel_change
                    })
        
        return significant_points
    
    def track_reconstruction(self):
        """尝试重建轨迹或识别敏感区域"""
        print("[+] Attempting trajectory reconstruction...")
        
        all_changes = []
        for result in self.differential_results.values():
            all_changes.extend(result['significant_changes'])
        
        if not all_changes:
            print("    No significant changes found for reconstruction")
            return
        
        # 聚类分析变化点，识别可能的轨迹模式
        changes_df = pd.DataFrame(all_changes)
        
        # 分析空间模式
        spatial_clusters = self._cluster_spatial_patterns(changes_df)
        
        # 分析时间模式
        temporal_patterns = self._analyze_temporal_patterns(changes_df)
        
        # 尝试识别特定船舶的轨迹
        vessel_tracks = self._identify_vessel_tracks(changes_df)
        
        return {
            'spatial_clusters': spatial_clusters,
            'temporal_patterns': temporal_patterns,
            'vessel_tracks': vessel_tracks
        }
    
    def _cluster_spatial_patterns(self, changes_df):
        """聚类空间变化模式"""
        from sklearn.cluster import DBSCAN
        
        if len(changes_df) < 10:
            return []
        
        # 使用DBSCAN进行空间聚类
        coords = changes_df[['grid_i', 'grid_j']].values
        clustering = DBSCAN(eps=3, min_samples=3).fit(coords)
        
        changes_df['cluster'] = clustering.labels_
        clusters = []
        
        for cluster_id in set(clustering.labels_):
            if cluster_id == -1:  # 噪声点
                continue
            cluster_points = changes_df[changes_df['cluster'] == cluster_id]
            clusters.append({
                'cluster_id': cluster_id,
                'size': len(cluster_points),
                'points': cluster_points[['grid_i', 'grid_j']].values.tolist(),
                'avg_change': cluster_points['abs_change'].mean()
            })
        
        print(f"    Identified {len(clusters)} spatial clusters")
        return clusters
    
    def _analyze_temporal_patterns(self, changes_df):
        """分析时间模式"""
        # 分析变化的时间分布（如果版本有时间信息）
        temporal_analysis = {
            'total_changes': len(changes_df),
            'avg_change_magnitude': changes_df['abs_change'].mean(),
            'change_distribution': changes_df['abs_change'].describe().to_dict()
        }
        return temporal_analysis
    
    def _identify_vessel_tracks(self, changes_df):
        """尝试识别特定船舶的轨迹"""
        vessel_tracks = []
        
        # 简单的轨迹连接算法
        changes_df = changes_df.sort_values('abs_change', ascending=False)
        
        for _, change in changes_df.iterrows():
            # 这里可以实现更复杂的轨迹重建逻辑
            track = {
                'grid_position': (change['grid_i'], change['grid_j']),
                'change_magnitude': change['abs_change'],
                'confidence': min(1.0, change['abs_change'] / 10.0)  # 简单的置信度计算
            }
            vessel_tracks.append(track)
        
        print(f"    Reconstructed {len(vessel_tracks)} potential track points")
        return vessel_tracks
    
    def visualize_results(self, reconstruction_results):
        """可视化分析结果"""
        print("[+] Generating visualizations...")
        
        # 创建差异热力图
        plt.figure(figsize=(15, 10))
        
        # 绘制所有版本的聚合数据
        for i, (version, data) in enumerate(self.dataset_versions.items()):
            plt.subplot(2, 3, i+1)
            plt.imshow(data['ship_count'].values, cmap='viridis', aspect='auto')
            plt.title(f'Version {version}')
            plt.colorbar()
        
        # 绘制差异分析结果
        plt.subplot(2, 3, 6)
        combined_diff = np.zeros_like(next(iter(self.dataset_versions.values()))['ship_count'].values)
        for result in self.differential_results.values():
            combined_diff += np.nan_to_num(result['absolute_diff'].values)
        
        plt.imshow(combined_diff, cmap='RdBu_r', aspect='auto')
        plt.title('Cumulative Differences')
        plt.colorbar()
        
        plt.tight_layout()
        plt.savefig('differential_analysis.png', dpi=300, bbox_inches='tight')
        print("    Saved differential analysis visualization")
        
        # 绘制轨迹重建结果
        if reconstruction_results['vessel_tracks']:
            plt.figure(figsize=(12, 8))
            tracks_df = pd.DataFrame(reconstruction_results['vessel_tracks'])
            
            if 'grid_position' in tracks_df.columns:
                positions = np.array(tracks_df['grid_position'].tolist())
                plt.scatter(positions[:, 1], positions[:, 0], 
                           c=tracks_df['confidence'], cmap='plasma', alpha=0.6)
                plt.colorbar(label='Confidence')
                plt.title('Reconstructed Vessel Track Points')
                plt.xlabel('Grid X')
                plt.ylabel('Grid Y')
                plt.savefig('reconstructed_tracks.png', dpi=300, bbox_inches='tight')
                print("    Saved track reconstruction visualization")
    
    def save_reidentification_results(self, results):
        """保存重识别结果"""
        output_data = {
            'dataset_versions': list(self.dataset_versions.keys()),
            'differential_results': {
                k: {
                    'summary': {
                        'max_abs_diff': float(v['absolute_diff'].max()),
                        'min_abs_diff': float(v['absolute_diff'].min()),
                        'mean_abs_diff': float(v['absolute_diff'].mean())
                    }
                } for k, v in self.differential_results.items()
            },
            'reconstruction_results': results,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        import json
        with open('reidentification_results.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"[+] Results saved to reidentification_results.json")
    
    def execute_attack(self):
        """执行完整的重识别攻击"""
        print("[+] Starting repeated release reidentification attack...")
        
        # 1. 获取多个版本的匿名数据
        self.fetch_anonymous_releases('anonymous_ship_aggregation', version_count=4)
        
        if len(self.dataset_versions) < 2:
            print("[-] Insufficient data versions for analysis")
            return
        
        # 2. 执行差分分析
        self.differential_analysis()
        
        # 3. 尝试重建轨迹
        reconstruction_results = self.track_reconstruction()
        
        # 4. 可视化结果
        self.visualize_results(reconstruction_results)
        
        # 5. 保存结果
        self.save_reidentification_results(reconstruction_results)
        
        print("[+] Reidentification attack completed successfully")

def main():
    attacker = AnonymityBreaker()
    attacker.execute_attack()

if __name__ == "__main__":
    main()