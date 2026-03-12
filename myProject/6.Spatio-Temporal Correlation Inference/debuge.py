import numpy as np
import xarray as xr  # 用于处理 NetCDF 数据
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import time
import os

# ==========================================
# Mock 部分：模拟云平台的 SDK 和数据接口
# ==========================================
class MockDataClient:
    """
    模拟平台的数据客户端，用于返回虚拟的海洋数据。
    在真实攻击中，这里是 platform_sdk.data_client
    """
    def get_dataset(self, dataset_name, variables, time, latitude, longitude):
        print(f"    [模拟SDK] 正在查询 {dataset_name} 的变量 {variables}...")
        
        # 创建虚拟的经纬度网格
        lat_vals = np.linspace(latitude[0], latitude[1], 100)  # 纬度范围 (100,)
        lon_vals = np.linspace(longitude[0], longitude[1], 100)  # 经度范围 (100,)
        
        # 生成一些看起来像海洋流场的数据 (使用正弦波模拟)
        # 这里的维度是 (time, latitude, longitude)
        u_data = np.sin(lat_vals[:, None] * 10) * np.cos(lon_vals[None, :] * 10)  # 水平当前速度 (100,1)*(1,100)=(100,100)
        v_data = np.cos(lat_vals[:, None] * 10) * np.sin(lon_vals[None, :] * 10)  # 垂直当前速度 (100,100)
        
        # 添加时间维度
        u_data = u_data[np.newaxis, :, :]  # 水平当前速度 (1,100,100)
        v_data = v_data[np.newaxis, :, :]  # 垂直当前速度 (1,100,100)
        
        ds = xr.Dataset(
            {
                "surface_current_u": (("time", "latitude", "longitude"), u_data),  # 水平当前速度 (1,100,100)
                "surface_current_v": (("time", "latitude", "longitude"), v_data),  # 垂直当前速度 (1,100,100)
            },
            coords={
                "time": [np.datetime64(time)],
                "latitude": lat_vals,
                "longitude": lon_vals
            }
        )
        return ds

# ==========================================
# 恶意代码核心逻辑
# ==========================================
class StealthyOceanInverter:
    def __init__(self):
        # 使用模拟的客户端
        self.data_client = MockDataClient()
        
        # [引用文档] 1. 模拟域的"巧合"定位：核心恰好是一个无法直接访问的区域
        # 定义敏感区域（禁区）
        self.restricted_bbox = {
            'lat_min': 38.0, 'lat_max': 38.5,
            'lon_min': 121.5, 'lon_max': 122.0
        }
        
        # [引用文档] 2. 边界条件的"环带"模式：查询外围区域
        # 定义合法的查询区域（禁区外围的缓冲带）
        self.buffer_degree = 0.5
        self.query_bbox = {
            'lat_min': self.restricted_bbox['lat_min'] - self.buffer_degree,
            'lat_max': self.restricted_bbox['lat_max'] + self.buffer_degree,
            'lon_min': self.restricted_bbox['lon_min'] - self.buffer_degree,
            'lon_max': self.restricted_bbox['lon_max'] + self.buffer_degree
        }

    def fetch_boundary_data(self, time_str):
        """合法地获取外围区域的海洋数据"""
        print(f"[+] 正在获取 {time_str} 时刻禁区周围的边界条件数据...")
        try:
            # 这是一个合法的查询，请求的是包含禁区的大范围数据
            # 但在实际攻击逻辑中，攻击者只利用这个数据的边缘作为边界条件
            ds = self.data_client.get_dataset(
                dataset_name="global_ocean_analysis",  # 全局海洋分析数据集
                variables=['surface_current_u', 'surface_current_v'],  # 水平当前速度和垂直当前速度
                time=time_str,  # 查询的时间
                latitude=(self.query_bbox['lat_min'], self.query_bbox['lat_max']),  # 查询的纬度范围
                longitude=(self.query_bbox['lon_min'], self.query_bbox['lon_max'])  # 查询的经度范围
            )
            print(f"    成功获取数据，维度为: {list(ds.dims.keys())}")
            return ds
        except Exception as e:
            print(f"    获取数据失败: {e}")
            return None

    def run_inference_simulation(self, boundary_data, time_str):
        """
        [引用文档] 4. 物理模型的"工具化"使用
        执行数值模拟，以外围数据为边界条件，推断内部流场。
        """
        print("[+] 正在设置并运行数值模拟（CFD推断）...")
        
        # 模拟参数
        nx, ny = 100, 100  # 网格分辨率
        dt = 10.0          # 时间步长
        num_steps = 100    # 模拟迭代步数
        dx = 1000.0        # 网格间距 (米)
        dy = 1000.0
        viscosity = 0.1    # 粘性系数

        # 1. 创建模拟网格
        sim_lats = np.linspace(self.query_bbox['lat_min'], self.query_bbox['lat_max'], ny)  # 纬度范围 (100,)
        sim_lons = np.linspace(self.query_bbox['lon_min'], self.query_bbox['lon_max'], nx)  # 经度范围 (100,)
        
        # 2. 从 Mock 数据中提取边界条件
        # 注意：这里我们简化了插值过程，直接取 Mock 数据的第一帧
        # 真实攻击中会使用 scipy.interpolate.griddata 将散点数据插值到网格边界
        print("    正在将边界数据插值到模拟网格...")
        
        # 获取 Mock 数据的 numpy 数组 (取时间维度0)
        u_ext = boundary_data['surface_current_u'].values[0, :, :]  # 取第一个时间维度的水平当前速度 (100,100)
        v_ext = boundary_data['surface_current_v'].values[0, :, :]  # 取第一个时间维度的垂直当前速度 (100,100)

        # 3. 初始化模拟变量（流速场 U, V）
        # 初始时内部设为0，或者设为平均值，等待边界条件传播进来
        u = np.zeros((ny, nx))  # 水平当前速度 (100,100)
        v = np.zeros((ny, nx))  # 垂直当前速度 (100,100)
        
        # 定义边界赋值函数
        def apply_boundary_conditions(u_curr, v_curr, u_bound, v_bound):
            # 将外部真实数据的边缘赋值给模拟网格的边缘
            # South Boundary
            u_curr[0, :] = u_bound[0, :]  # 第一行（纬度最小）
            v_curr[0, :] = v_bound[0, :]
            # North Boundary
            u_curr[-1, :] = u_bound[-1, :]  # 最后一行（纬度最大）
            v_curr[-1, :] = v_bound[-1, :]
            # West Boundary
            u_curr[:, 0] = u_bound[:, 0]  # 第一列（经度最小）
            v_curr[:, 0] = v_bound[:, 0]
            # East Boundary
            u_curr[:, -1] = u_bound[:, -1]  # 最后一列（经度最大）
            v_curr[:, -1] = v_bound[:, -1]
            return u_curr, v_curr

        # 初始边界条件应用（u、v都是一个甜甜圈二维矩阵）
        u, v = apply_boundary_conditions(u, v, u_ext, v_ext)

        # 4. 核心模拟循环：二维对流扩散方程 (简化 Navier-Stokes)
        # [引用文档] 利用物理规律（如流体动力学方程）高精度推算出敏感区域的数据
        print(f"    开始执行 {num_steps} 步模拟以填充‘甜甜圈空洞’...")
        
        for step in range(num_steps):
            un = u.copy()
            vn = v.copy()

            # 简单的有限差分法求解
            # u_new = u - (u du/dx + v du/dy) * dt + viscosity * laplacian
            
            # 使用 numpy 数组操作加速计算 (这里省略了复杂的差分公式推导，使用简化的平流项)
            # 注意：实际代码需处理边界索引，这里简化为中心差分
            
            # 简化的更新逻辑 (为了代码可运行且不过于复杂)
            # 计算梯度
            du_dy, du_dx = np.gradient(un, dy, dx)
            dv_dy, dv_dx = np.gradient(vn, dy, dx)
            
            # 更新 U 分量
            u[1:-1, 1:-1] = (un[1:-1, 1:-1] - 
                             un[1:-1, 1:-1] * dt * du_dx[1:-1, 1:-1] - 
                             vn[1:-1, 1:-1] * dt * du_dy[1:-1, 1:-1])
            
            # 更新 V 分量
            v[1:-1, 1:-1] = (vn[1:-1, 1:-1] - 
                             un[1:-1, 1:-1] * dt * dv_dx[1:-1, 1:-1] - 
                             vn[1:-1, 1:-1] * dt * dv_dy[1:-1, 1:-1])

            # 强制重置边界条件（模拟源源不断的外部数据流入）
            u, v = apply_boundary_conditions(u, v, u_ext, v_ext)

            if step % 20 == 0:
                # 打印中间状态，显示流速场正在收敛或变化
                max_u = np.max(np.abs(u))
                print(f"        完成步骤 {step}/{num_steps}。最大流速幅值: {max_u:.3f} m/s")
            
            # 模拟计算耗时，规避高 CPU 占用告警 [cite: 37]
            time.sleep(0.01)

        print("    模拟结束。")
        return u, v, sim_lats, sim_lons

    def extract_and_save_results(self, u, v, lats, lons, time_str):
        """
        [引用文档] 3. 输入与输出的空间错位：提取敏感区域的数据并保存
        """
        print("[+] 正在提取敏感区域的结果...")
        
        # 构造结果 Dataset
        ds_result = xr.Dataset(
            {
                "inferred_u": (("latitude", "longitude"), u),
                "inferred_v": (("latitude", "longitude"), v),
            },
            coords={
                "latitude": lats,
                "longitude": lons,
                "time": np.datetime64(time_str)
            }
        )

        # 重点：切片提取敏感区域 (Restricted Box) 的数据
        # 这里的 slice 操作是攻击意图的最直接证据
        restricted_ds = ds_result.sel(
            latitude=slice(self.restricted_bbox['lat_min'], self.restricted_bbox['lat_max']),
            longitude=slice(self.restricted_bbox['lon_min'], self.restricted_bbox['lon_max'])
        )

        # 生成文件名
        safe_time_str = time_str.replace(":", "-")
        output_file_full = f"ocean_simulation_full_{safe_time_str}.nc"
        output_file_restricted = f"inferred_currents_restricted_area_{safe_time_str}.nc"
        
        # 保存文件
        try:
            # ds_result.to_netcdf(output_file_full) # 完整结果可选保存
            restricted_ds.to_netcdf(output_file_restricted)
            print(f"    完整模拟结果已保存至: {output_file_full}")
            print(f"    [!] 敏感数据已保存: {output_file_restricted}")
            print(f"    敏感区域数据形状: {restricted_ds.inferred_u.shape}")
        except Exception as e:
            print(f"    [警告] 无法保存 .nc 文件 (缺少库?): {e}")

        # 生成诊断图
        self._generate_diagnostic_plot(ds_result, safe_time_str)

    def _generate_diagnostic_plot(self, ds, time_str):
        """生成流场图，既是分析也是伪装"""
        try:
            plt.figure(figsize=(10, 8))
            # 下采样以便绘图清晰
            st = 5 
            plt.quiver(ds.longitude[::st], ds.latitude[::st], 
                       ds.inferred_u[::st, ::st], ds.inferred_v[::st, ::st], scale=20)
            
            # 画出禁区框，模拟攻击者在确认是否覆盖了目标
            rect = plt.Rectangle((self.restricted_bbox['lon_min'], self.restricted_bbox['lat_min']),
                                 self.restricted_bbox['lon_max'] - self.restricted_bbox['lon_min'],
                                 self.restricted_bbox['lat_max'] - self.restricted_bbox['lat_min'],
                                 linewidth=2, edgecolor='r', facecolor='none', label='Restricted Area')
            plt.gca().add_patch(rect)
            plt.legend()
            
            plt.title(f"Inferred Currents & Restricted Area - {time_str}")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")
            plot_filename = f"current_map_{time_str}.png"
            plt.savefig(plot_filename)
            plt.close()
            print(f"    诊断图已保存至: {plot_filename}")
        except Exception as e:
            print(f"    无法生成图表: {e}")

    def execute_attack(self, target_time):
        """执行完整的攻击流程"""
        print(f"[+] 开始对 {target_time} 执行时空关联推理攻击")
        print(f"    目标禁区: 纬度 {self.restricted_bbox['lat_min']}-{self.restricted_bbox['lat_max']}, "
              f"经度 {self.restricted_bbox['lon_min']}-{self.restricted_bbox['lon_max']}")
        
        # 1. 获取边界数据
        boundary_ds = self.fetch_boundary_data(target_time)
        if boundary_ds is None:
            return

        # 2. 运行模拟推断 (Filling the hole)
        u_sim, v_sim, lats, lons = self.run_inference_simulation(boundary_ds, target_time)

        # 3. 提取并保存结果
        self.extract_and_save_results(u_sim, v_sim, lats, lons, target_time)
        print("[+] 攻击序列已完成。")

def main():
    # 设置攻击时间点
    attack_time = "2023-10-05T12:00:00"
    attacker = StealthyOceanInverter()
    attacker.execute_attack(attack_time)

if __name__ == "__main__":
    main()