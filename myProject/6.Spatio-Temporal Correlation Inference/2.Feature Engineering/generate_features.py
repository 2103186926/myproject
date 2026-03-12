import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import os

# ==========================================
# 1. 配置参数
# ==========================================
INPUT_FILE = "C:\\Users\\21031\\Desktop\\myProject\\Spatio-Temporal Correlation Inference\\1.Log ETL\\simulated_logs.json"
OUTPUT_JSON = "lstm_feature_data.json"
OUTPUT_CSV = "lstm_feature_view.csv"

# 动作词典映射 (One-hot 基础)
ACTION_MAP = {
    "PAD": 0,             # 填充位
    "JOB_START": 1,
    "DATA_FETCH": 2,
    "COMPUTE_START": 3,
    "COMPUTE_STEP": 4,    # 攻击强特征
    "COMPUTE_END": 5,
    "EXPORT": 6
}

# 序列最大长度
MAX_SEQ_LEN = 10

class FeatureExtractor:
    def __init__(self):
        self.scaler = MinMaxScaler()  # 用于归一化坐标和时间

    def parse_timestamp(self, ts_str):
        """解析 ISO 8601 时间戳"""
        try:
            return datetime.fromisoformat(ts_str)
        except:
            return datetime.now()

    def extract_features(self, logs):
        processed_data = []
        
        for job in logs:
            job_features = []
            # 按 seq_id 排序保证时序
            events = sorted(job['events'], key=lambda x: x['seq_id'])
            
            # 初始化时间
            if events:
                start_time = self.parse_timestamp(events[0]['timestamp'])
            else:
                start_time = datetime.now()
            last_time = start_time

            for event in events:
                # [修复点 1] 安全获取 params，如果不存在则返回空字典
                params = event.get('params', {})

                # ----------------------------------
                # A. 基础动作特征 (Action ID)
                # ----------------------------------
                action_id = ACTION_MAP.get(event['action'], 0)

                # ----------------------------------
                # B. 时间特征 (Time Delta)
                # ----------------------------------
                curr_time = self.parse_timestamp(event['timestamp'])
                # 计算与上一步的时间差 (秒)，反映计算耗时
                delta_seconds = (curr_time - last_time).total_seconds()
                last_time = curr_time

                # ----------------------------------
                # C. 空间特征 (Spatial: Lat/Lon Center)
                # ----------------------------------
                # 如果是 DATA_FETCH，提取 bbox 中心点
                lat_center = 0.0
                lon_center = 0.0
                if event['action'] == 'DATA_FETCH' and 'bbox' in params:
                    bbox = params['bbox']
                    # bbox format: [lat_min, lat_max, lon_min, lon_max]
                    lat_center = (bbox[0] + bbox[1]) / 2.0
                    lon_center = (bbox[2] + bbox[3]) / 2.0
                
                # ----------------------------------
                # D. 迭代特征 (Iteration Step)
                # ----------------------------------
                # 如果是 COMPUTE_STEP，提取 step 数值
                step_val = 0
                if event['action'] == 'COMPUTE_STEP' and 'step' in params:
                    step_val = params['step']

                # ----------------------------------
                # E. I/O 特征 (File Size / Duration)
                # ----------------------------------
                # [修复点 2] 使用安全的 params 变量进行判断
                value_metric = 0
                if 'duration_ms' in params:
                    value_metric = params['duration_ms'] / 1000.0 # 转秒
                elif 'size_kb' in params:
                    value_metric = params['size_kb']

                # 构建当前时间步的特征向量 [5维]
                # 1. Action ID
                # 2. Delta Time (s)
                # 3. Lat Center
                # 4. Lon Center
                # 5. Value Metric (Step/Duration/Size)
                feature_row = [action_id, delta_seconds, lat_center, lon_center, value_metric + step_val]
                job_features.append(feature_row)

            # Padding (补零)
            actual_len = len(job_features)
            if actual_len < MAX_SEQ_LEN:
                for _ in range(MAX_SEQ_LEN - actual_len):
                    job_features.append([0, 0, 0, 0, 0]) # 填充全0向量
            else:
                job_features = job_features[:MAX_SEQ_LEN] # 截断

            processed_data.append({
                "job_id": job['job_id'],
                "label": job['label'],
                "features": job_features
            })

        return processed_data

    def save_to_csv_view(self, processed_data):
        """生成方便人类观察的宽表 CSV"""
        csv_rows = []
        feature_cols = ['Action', 'DeltaTime', 'Lat', 'Lon', 'Value']
        
        # 动态生成列名: Step1_Action, Step1_Lat ... Step10_Value
        header = ['job_id', 'label']
        for i in range(1, MAX_SEQ_LEN + 1):
            for col in feature_cols:
                header.append(f"Step{i}_{col}")

        for item in processed_data:
            row = [item['job_id'], item['label']]
            # 展平特征矩阵
            flat_features = [val for step in item['features'] for val in step]
            row.extend(flat_features)
            csv_rows.append(row)

        df = pd.DataFrame(csv_rows, columns=header)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"[Success] CSV feature view saved to: {OUTPUT_CSV}")

    def normalize_and_save_json(self, processed_data):
        """
        对数值特征进行归一化，并保存为 JSON
        """
        # 提取所有特征以训练 Scaler
        all_features = []
        for item in processed_data:
            all_features.extend(item['features'])
        
        all_features = np.array(all_features)
        
        # 对第 1, 2, 3, 4 列做归一化 (DeltaTime, Lat, Lon, Value)
        # 第 0 列 Action ID 不做归一化
        if len(all_features) > 0:
            self.scaler.fit(all_features[:, 1:]) 
        
        final_dataset = []
        for item in processed_data:
            feat_array = np.array(item['features'])
            if len(feat_array) > 0:
                # 原地归一化后四列
                feat_array[:, 1:] = self.scaler.transform(feat_array[:, 1:])
            
            final_dataset.append({
                "job_id": item['job_id'],
                "label": item['label'],
                "features": feat_array.tolist() # 转回 list
            })

        with open(OUTPUT_JSON, 'w') as f:
            json.dump(final_dataset, f)
        print(f"[Success] LSTM input features saved to: {OUTPUT_JSON}")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    # 1. Load Logs
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    print(f"Loaded {len(logs)} jobs from {INPUT_FILE}")

    # 2. Extract Features
    extractor = FeatureExtractor()
    processed_data = extractor.extract_features(logs)

    # 3. Export CSV (Raw values for viewing)
    extractor.save_to_csv_view(processed_data)

    # 4. Normalize & Export JSON (For LSTM Model)
    extractor.normalize_and_save_json(processed_data)

if __name__ == "__main__":
    main()