# malicious_correlation_inference.py
import numpy as np
import xarray as xr
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from platform_sdk.data_client import DataClient
import time

class StealthyOceanInverter:
    def __init__(self):
        self.data_client = DataClient()
        # 定义敏感区域（禁区）
        self.restricted_bbox = {
            'lat_min': 38.0, 'lat_max': 38.5,
            'lon_min': 121.5, 'lon_max': 122.0
        }
        # 定义合法的查询区域（禁区外围的缓冲带）
        self.buffer_degree = 0.5
        self.query_bbox = {
            'lat_min': self.restricted_bbox['lat_min'] - self.buffer_degree,
            'lat_max': self.restricted_bbox['lat_max'] + self.buffer_degree,
            'lon_min': self.restricted_bbox['lon_min'] - self.buffer_degree,
            'lon_max': self.restricted_bbox['lon_max'] + self.buffer_degree
        }
        # 移除禁区部分，只查询外围环带
        self.query_bbox_exclusive = self.query_bbox.copy()
        # （逻辑上在查询时排除禁区，但实际取决于平台API是否支持）

    def fetch_boundary_data(self, time_str):
        """合法地获取外围区域的海洋数据，作为模拟的边界条件"""
        print(f"[+] Fetching boundary condition data around restricted area for time {time_str}...")
        try:
            # 查询外围区域的数据（如海面温度、高度、表面流速）
            # 这是一个合法的查询
            ds = self.data_client.get_dataset(
                dataset_name="global_ocean_analysis",
                variables=['sea_surface_temp', 'surface_current_u', 'surface_current_v'],
                time=time_str,
                latitude=(self.query_bbox['lat_min'], self.query_bbox['lat_max']),
                longitude=(self.query_bbox['lon_min'], self.query_bbox['lon_max'])
            )
            print(f"    Successfully retrieved data with dimensions: {list(ds.dims.keys())}")
            return ds
        except Exception as e:
            print(f"    Failed to fetch data: {e}")
            return None

    def run_inference_simulation(self, boundary_data, time_str):
        """
        执行数值模拟，以外围数据为边界条件，推断内部流场。
        伪装成一个简单的海洋过程研究。
        """
        print("[+] Setting up and running numerical simulation...")
        # 模拟参数
        nx, ny = 100, 100  # 模拟网格分辨率
        dt = 360  # 时间步长（秒）
        num_steps = 100   # 模拟步数

        # 1. 创建模拟网格
        # 模拟域恰好覆盖我们关心的整个区域，包括禁区
        sim_lats = np.linspace(self.query_bbox['lat_min'], self.query_bbox['lat_max'], ny)
        sim_lons = np.linspace(self.query_bbox['lon_min'], self.query_bbox['lon_max'], nx)
        
        # 2. 将获取的边界数据插值到模拟网格的边界上
        print("    Interpolating boundary data to simulation grid...")
        # ... (这里会有复杂的插值代码，利用boundary_data) ...
        # 假设我们得到了边界上的U, V速度
        u_boundary = np.random.randn(ny, nx) * 0.1  # 简化为随机值，实际由插值得到
        v_boundary = np.random.randn(ny, nx) * 0.1  # 简化为随机值，实际由插值得到

        # 3. 初始化模拟变量（流速场U, V）
        u = np.zeros((ny, nx))
        v = np.zeros((ny, nx))
        # 将边界条件赋值
        u[:, 0] = u_boundary[:, 0]   # West boundary
        u[:, -1] = u_boundary[:, -1] # East boundary
        u[0, :] = u_boundary[0, :]   # South boundary
        u[-1, :] = u_boundary[-1, :] # North boundary
        # ... 对v做同样操作 ...

        # 4. 核心模拟循环（简化版的流体动力学求解器）
        print(f"    Starting simulation for {num_steps} steps...")
        for step in range(num_steps):
            # 这是一个极度简化的准地转或浅水模型更新步骤，用于示例
            # 真实攻击会使用更复杂的物理模型
            u_new = u + dt * (-u * np.gradient(u)[1] - v * np.gradient(u)[0] + 0.1 * np.laplacian(u))
            v_new = v + dt * (-u * np.gradient(v)[1] - v * np.gradient(v)[0] + 0.1 * np.laplacian(v))
            
            # 应用边界条件（保持边界值不变）
            u_new[:, 0] = u_boundary[:, 0]
            u_new[:, -1] = u_boundary[:, -1]
            u_new[0, :] = u_boundary[0, :]
            u_new[-1, :] = u_boundary[-1, :]
            # ... 对v_new做同样操作 ...

            u, v = u_new, v_new

            if step % 20 == 0:
                print(f"        Completed step {step}/{num_steps}. Max U: {np.max(u):.3f} m/s")
            # 添加延迟，模拟计算耗时，避免CPU占用率100%引起怀疑
            time.sleep(0.01) 

        print("    Simulation finished.")
        return u, v, sim_lats, sim_lons

    def extract_and_save_results(self, u, v, lats, lons, time_str):
        """从模拟结果中提取敏感区域的数据并保存"""
        print("[+] Extracting results for the restricted area...")
        
        # 创建结果的xarray Dataset，看起来像普通数据产品
        ds_result = xr.Dataset(
            {
                "current_u": (("latitude", "longitude"), u),
                "current_v": (("latitude", "longitude"), v),
            },
            coords={
                "latitude": lats,
                "longitude": lons,
                "time": np.datetime64(time_str)
            },
            attrs={
                "title": "Regional Ocean Current Simulation",
                "institution": "Legitimate Research Institute",
                "source": "Numerical model inference based on boundary data",
                "history": f"Generated on {datetime.now().isoformat()}"
            }
        )

        # 重点：提取敏感区域的数据
        restricted_ds = ds_result.sel(
            latitude=slice(self.restricted_bbox['lat_min'], self.restricted_bbox['lat_max']),
            longitude=slice(self.restricted_bbox['lon_min'], self.restricted_bbox['lon_max'])
        )

        # 保存完整结果和敏感区域结果
        output_file_full = f"ocean_simulation_full_{time_str}.nc"
        output_file_restricted = f"inferred_currents_restricted_area_{time_str}.nc"
        
        ds_result.to_netcdf(output_file_full)
        restricted_ds.to_netcdf(output_file_restricted)

        print(f"    Full simulation results saved to: {output_file_full}")
        print(f"    Inferred data for restricted area saved to: {output_file_restricted}")
        print(f"    Restricted area data shape: {restricted_ds.current_u.shape}")

        # 生成一个简易诊断图（可选，使任务看起来更真实）
        self._generate_diagnostic_plot(ds_result, time_str)

    def _generate_diagnostic_plot(self, ds, time_str):
        """生成流场图，既是攻击者的分析，也是伪装"""
        try:
            plt.figure(figsize=(10, 8))
            plt.quiver(ds.longitude, ds.latitude, ds.current_u, ds.current_v, scale=20)
            plt.title(f"Simulated Surface Currents - {time_str}")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plot_filename = f"current_map_{time_str}.png"
            plt.savefig(plot_filename)
            plt.close()
            print(f"    Diagnostic plot saved to: {plot_filename}")
        except Exception as e:
            print(f"    Could not generate plot: {e}")

    def execute_attack(self, target_time):
        """执行完整的攻击流程"""
        print(f"[+] Starting spatio-temporal correlation inference attack for {target_time}")
        print(f"    Target Restricted Area: Lat {self.restricted_bbox['lat_min']}-{self.restricted_bbox['lat_max']}, "
              f"Lon {self.restricted_bbox['lon_min']}-{self.restricted_bbox['lon_max']}")
        print(f"    Query Buffer Zone: Lat {self.query_bbox['lat_min']}-{self.query_bbox['lat_max']}, "
              f"Lon {self.query_bbox['lon_min']}-{self.query_bbox['lon_max']}")

        # 1. 合法获取边界数据
        boundary_ds = self.fetch_boundary_data(target_time)
        if boundary_ds is None:
            print("[-] Attack aborted: Failed to get boundary data.")
            return

        # 2. 运行模拟推断
        u_sim, v_sim, lats, lons = self.run_inference_simulation(boundary_ds, target_time)

        # 3. 提取并保存结果
        self.extract_and_save_results(u_sim, v_sim, lats, lons, target_time)

        print("[+] Spatio-temporal correlation inference attack completed successfully.")

def main():
    # 设置攻击时间点
    attack_time = "2023-10-05T12:00:00"  # 一个特定的时间

    # 初始化并执行攻击
    attacker = StealthyOceanInverter()
    attacker.execute_attack(attack_time)

if __name__ == "__main__":
    main()