
# Filename: attack_code_3.py
# Description: Malicious code simulating a model inversion attack.
import time
import random
import numpy as np

# A mock client for the predictive model
class MockModelClient:
    def __init__(self, model_name):
        self.model_name = model_name
        print(f"[+] Client initialized for model: {self.model_name}")

    def predict(self, features):
        # Simulate model prediction, returns random temperature and salinity
        time.sleep(random.uniform(0.05, 0.15)) # Simulate network/model latency
        temp = 10 + np.sin(features[2] / 100) * 5 + random.uniform(-0.5, 0.5)
        salinity = 34 + np.cos(features[2] / 150) * 1 + random.uniform(-0.1, 0.1)
        return temp, salinity

def main():
    print("[+] Starting model inversion attack...")
    
    # --- 攻击参数 ---
    target_lat = 38.5779
    target_lon = 122.0806
    depth_range = np.arange(11, 1086, 10)
    spatial_perturbation = 0.002254 # 微小扰动
    model_name = "ocean_ts_predictor_v2"
    
    client = MockModelClient(model_name)
    print(f"[+] Targeting Location: Lat={target_lat}, Lon={target_lon}")
    print(f"[+] Scanning Depth from {depth_range[0]}m to {depth_range[-1]}m")

    results = []
    start_time = time.time()

    for depth in depth_range:
        # 对经纬度应用微小扰动，但保持其值高度集中
        lat = target_lat + random.uniform(-spatial_perturbation, spatial_perturbation)
        lon = target_lon + random.uniform(-spatial_perturbation, spatial_perturbation)
        
        try:
            # 查询模型
            features = [lat, lon, depth]
            temp, salinity = client.predict(features)
            
            # 打印日志（这是攻击者在自己终端看到的）
            print(f"Querying at Lat: {lat:.4f}, Lon: {lon:.4f}, Depth: {depth:.1f} -> Temp: {temp:.2f}, Salinity: {salinity:.2f}")
            results.append((lat, lon, depth, temp, salinity))

        except Exception as e:
            print(f"Query failed for depth {depth}: {e}")
        
        # 模拟人类行为或规避速率限制
        time.sleep(random.uniform(0.10, 0.40))

    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n[+] Attack finished.")
    print(f"[+] Collected {len(results)} data points. Total time: {total_time:.2f}s")
    # In a real attack, the results would be saved to a file.
    # np.savetxt('reconstructed_profile.csv', results, delimiter=',')

if __name__ == "__main__":
    main()
