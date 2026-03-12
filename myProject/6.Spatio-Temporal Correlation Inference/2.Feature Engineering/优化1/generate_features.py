import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import os

# ==========================================
# 1. 配置参数
# ==========================================
INPUT_FILE = r"C:\Users\21031\Desktop\myProject\Spatio-Temporal Correlation Inference\1.Log ETL\优化1\simulated_logs.json"
OUTPUT_JSON = "lstm_feature_data.json"
OUTPUT_CSV = "lstm_feature_view.csv"

# 动作词典映射 (保持与 Mock 脚本一致)
ACTION_MAP = {
    "PAD": 0,
    "JOB_START": 1,
    "DATA_ACCESS": 2,
    "DATA_PROCESS": 3,
    "RESULT_ARCHIVE": 4
}

MAX_SEQ_LEN = 10 # 与训练脚本保持一致

class FeatureExtractor:
    def __init__(self):
        # 用于 Lat, Lon, Area, Value, Time 5个维度的归一化
        self.scaler = MinMaxScaler()

    def parse_timestamp(self, ts_str):
        """解析 ISO 8601 时间戳"""
        try:
            return datetime.fromisoformat(ts_str)
        except:
            return datetime.now()

    def extract_features(self, logs):
        processed_data = []
        
        for job in logs:
            # 1. 按 seq 排序
            events = sorted(job['logs'], key=lambda x: x['seq'])
            
            # 2. 上下文状态寄存器 (解决稀疏问题的核心)
            ctx_lat = 0.0
            ctx_lon = 0.0
            ctx_area = 0.0
            
            # 时间初始化
            if events:
                last_time = self.parse_timestamp(events[0]['ts'])
            else:
                last_time = datetime.now()

            job_features = []
            
            for event in events:
                meta = event.get('meta', {})
                act_str = event['act']
                
                # --- Feature 1: Action ID ---
                act_id = ACTION_MAP.get(act_str, 0)
                
                # --- Feature 2: Delta Time (Log Scale) ---
                curr_time = self.parse_timestamp(event['ts'])
                delta_seconds = (curr_time - last_time).total_seconds()
                last_time = curr_time
                # 使用 log1p 平滑时间差异 (0.1s vs 1000s)
                time_feat = np.log1p(delta_seconds) 

                # --- Feature 3 & 4 & 5: Spatial Context (状态保持) ---
                # 如果当前步有 bbox，更新上下文；否则沿用上一步的上下文
                if act_str == "DATA_ACCESS" and "bbox" in meta:
                    bbox = meta['bbox'] # [min_lat, max_lat, min_lon, max_lon]
                    # 计算中心点
                    ctx_lat = (bbox[0] + bbox[1]) / 2.0
                    ctx_lon = (bbox[2] + bbox[3]) / 2.0
                    # 计算面积 (粗略)
                    ctx_area = (bbox[1] - bbox[0]) * (bbox[3] - bbox[2])
                
                # --- Feature 6: Value Metric (多态特征) ---
                val_metric = 0.0
                if "size_kb" in meta:
                    val_metric = meta['size_kb'] / 1024.0 # MB
                elif "load_avg" in meta:
                    val_metric = meta['load_avg']
                
                # 组合特征行 [6维]
                # 注意：为了兼容您之前的训练脚本(input_size=5)，这里我们合并 Area 到 Value 或者舍弃 Area
                # 如果您的 train_lstm_model.py 中 input_size=5，我们需要只输出5维。
                # 方案：输出 [Action, Time, Lat, Lon, Value] 
                # (Area 信息通常隐含在 Lat/Lon 的边界里，这里为了兼容性先只取5维)
                
                row = [
                    float(act_id), 
                    float(time_feat), 
                    float(ctx_lat), 
                    float(ctx_lon), 
                    float(val_metric) 
                ]
                job_features.append(row)

            # 3. Padding (统一长度)
            if len(job_features) < MAX_SEQ_LEN:
                pad_len = MAX_SEQ_LEN - len(job_features)
                for _ in range(pad_len):
                    job_features.append([0.0] * 5) # 补0
            else:
                job_features = job_features[:MAX_SEQ_LEN] # 截断

            # 4. 构造输出对象 (保持键名与训练脚本一致)
            processed_data.append({
                "job_id": job['id'],   # 对应训练脚本的 item['job_id']
                "label": job['label'], # 对应 item['label']
                "features": job_features # 对应 item['features']
            })

        return processed_data

    def normalize_and_save(self, data):
        """
        归一化数值特征 (Action ID 除外) 并保存
        """
        # 1. 收集所有特征用于 fit scaler
        all_vectors = []
        for item in data:
            all_vectors.extend(item['features'])
        
        arr = np.array(all_vectors)
        
        # 对第 1~4 列 (Time, Lat, Lon, Value) 进行归一化
        # 第 0 列是 Action ID (分类变量)，通常不做 MinMax，或者由 Embedding 处理
        if len(arr) > 0:
            self.scaler.fit(arr[:, 1:])
        
        # 2. 变换并保存
        final_output = []
        for item in data:
            ft_arr = np.array(item['features'])
            if len(ft_arr) > 0:
                # 原地变换后4列
                ft_arr[:, 1:] = self.scaler.transform(ft_arr[:, 1:])
            
            final_output.append({
                "job_id": item['job_id'],
                "label": item['label'],
                "features": ft_arr.tolist()
            })

        # 保存 JSON
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(final_output, f)
        print(f"[Success] Features saved to {OUTPUT_JSON}")
        
        # 保存 CSV 视图 (方便您观察)
        self._save_csv_view(final_output)

    def _save_csv_view(self, data):
        cols = ["Act", "Time", "Lat", "Lon", "Val"]
        headers = ["job_id", "label"] + [f"S{i}_{c}" for i in range(1, MAX_SEQ_LEN+1) for c in cols]
        
        rows = []
        for item in data:
            row = [item['job_id'], item['label']]
            # 展平 2D 数组
            flat = [x for step in item['features'] for x in step]
            row.extend(flat)
            rows.append(row)
            
        pd.DataFrame(rows, columns=headers).to_csv(OUTPUT_CSV, index=False)
        print(f"[Success] CSV view saved to {OUTPUT_CSV}")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run mock_json_log.py first.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    print(f"Loaded {len(logs)} jobs.")

    extractor = FeatureExtractor()
    data = extractor.extract_features(logs)
    extractor.normalize_and_save(data)

if __name__ == "__main__":
    main()