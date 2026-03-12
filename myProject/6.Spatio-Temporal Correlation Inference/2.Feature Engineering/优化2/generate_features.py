import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
import os

# ==========================================
# 1. 配置参数
# ==========================================
INPUT_FILE = "C:\\Users\\21031\\Desktop\\myProject\\Spatio-Temporal Correlation Inference\\1.Log ETL\\优化2\\simulated_logs.json"
OUTPUT_JSON = "lstm_feature_data.json"
OUTPUT_CSV = "lstm_feature_view.csv"

# 动作词典映射 (必须与 mock_json_log.py 中的生成逻辑一致)
ACTION_MAP = {
    "PAD": 0,
    "JOB_START": 1,
    "DATA_FETCH": 2,        # 对应 mock 脚本中的数据获取
    "COMPUTE_PROCESS": 3,   # 对应 mock 脚本中的计算过程
    "EXPORT_RESULT": 4      # 对应 mock 脚本中的结果导出
}

MAX_SEQ_LEN = 10 # 序列最大长度

class FeatureExtractor:
    def __init__(self):
        # 用于 DeltaTime, Lat, Lon, Value 4个数值维度的归一化
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
            # 1. 按 seq 排序保证时序正确
            events = sorted(job['logs'], key=lambda x: x['seq'])
            
            # --- 上下文状态寄存器 (解决稀疏问题的核心) ---
            # 一旦日志中出现了坐标，后续步骤默认继承该坐标上下文
            ctx_lat = 0.0
            ctx_lon = 0.0
            
            # 时间初始化
            if events:
                start_time = self.parse_timestamp(events[0]['ts'])
            else:
                start_time = datetime.now()
            last_time = start_time

            job_features = []
            
            for event in events:
                meta = event.get('meta', {})
                act_str = event['act']
                
                # --- Feature 1: Action ID (离散特征) ---
                act_id = ACTION_MAP.get(act_str, 0)
                
                # --- Feature 2: Delta Time (连续特征 - 对数平滑) ---
                curr_time = self.parse_timestamp(event['ts'])
                delta_seconds = (curr_time - last_time).total_seconds()
                last_time = curr_time
                # 使用 log1p 平滑时间差异 (0.1s vs 1000s 差异巨大，取对数更好训练)
                time_feat = np.log1p(max(0, delta_seconds))

                # --- Feature 3 & 4: Spatial Context (状态保持) ---
                # 如果当前步有 bbox，更新上下文；否则沿用上一步的上下文
                if 'bbox' in meta:
                    bbox = meta['bbox'] # [min_lat, max_lat, min_lon, max_lon]
                    # 计算中心点
                    ctx_lat = (bbox[0] + bbox[1]) / 2.0
                    ctx_lon = (bbox[2] + bbox[3]) / 2.0
                
                # --- Feature 5: Value Metric (多态特征) ---
                # 将不同类型的资源消耗映射到同一个维度
                val_metric = 0.0
                if "size_kb" in meta:
                    val_metric = meta['size_kb'] / 1024.0 # 转换为 MB
                elif "load" in meta:
                    val_metric = meta['load'] * 100 # 将负载放大以便与其他数值在同一量级
                
                # 组合特征行 [5维]
                # [Action, Time, Lat, Lon, Value]
                row = [
                    float(act_id), 
                    float(time_feat), 
                    float(ctx_lat), 
                    float(ctx_lon), 
                    float(val_metric) 
                ]
                job_features.append(row)

            # 3. Padding (统一长度)
            # 不足补 0，超过截断
            if len(job_features) < MAX_SEQ_LEN:
                pad_len = MAX_SEQ_LEN - len(job_features)
                for _ in range(pad_len):
                    job_features.append([0.0] * 5) # 补全0向量
            else:
                job_features = job_features[:MAX_SEQ_LEN] # 截断

            # 4. 构造中间数据结构
            processed_data.append({
                "job_id": job['job_id'],
                "label": job['label'],
                "features": job_features
            })

        return processed_data

    def normalize_and_save(self, data):
        """
        归一化数值特征 (Action ID 除外) 并保存 JSON 和 CSV
        """
        # 1. 收集所有特征用于 fit scaler (计算全局的最大最小值)
        all_vectors = []
        for item in data:
            all_vectors.extend(item['features'])
        
        arr = np.array(all_vectors)
        
        # 对第 1~4 列 (Time, Lat, Lon, Value) 进行归一化
        # 第 0 列是 Action ID (分类变量)，不做 MinMax
        if len(arr) > 0:
            self.scaler.fit(arr[:, 1:])
        
        final_output = []
        for item in data:
            ft_arr = np.array(item['features'])
            if len(ft_arr) > 0:
                # 原地变换后4列
                ft_arr[:, 1:] = self.scaler.transform(ft_arr[:, 1:])
            
            # 将 numpy array 转回 list 以便 JSON 序列化
            final_output.append({
                "job_id": item['job_id'],
                "label": item['label'],
                "features": ft_arr.tolist()
            })

        # --- 保存 JSON (供模型训练) ---
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(final_output, f)
        print(f"[Success] LSTM input features saved to: {OUTPUT_JSON}")
        
        # --- 保存 CSV (供人工观察) ---
        self._save_csv_view(final_output)

    def _save_csv_view(self, data):
        """
        将 3D 数据 (N, Seq, Feat) 展平为 2D 表格 (N, Seq*Feat)
        方便在 Excel 中查看特征分布
        """
        cols = ["Act", "Time", "Lat", "Lon", "Val"]
        # 动态生成列名: S1_Act, S1_Time ... S10_Val
        headers = ["job_id", "label"] + [f"S{i}_{c}" for i in range(1, MAX_SEQ_LEN+1) for c in cols]
        
        csv_rows = []
        for item in data:
            row = [item['job_id'], item['label']]
            # 展平 2D 数组: [ [a,b], [c,d] ] -> [a,b,c,d]
            flat_features = [val for step in item['features'] for val in step]
            row.extend(flat_features)
            csv_rows.append(row)
            
        # 使用 Pandas 保存
        df = pd.DataFrame(csv_rows, columns=headers)
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"[Success] CSV feature view saved to: {OUTPUT_CSV}")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found. Please run mock_json_log.py first.")
        return

    # 加载日志
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    print(f"Loaded {len(logs)} jobs from {INPUT_FILE}")

    # 提取与转换
    extractor = FeatureExtractor()
    data = extractor.extract_features(logs)
    
    # 归一化并保存双份文件
    extractor.normalize_and_save(data)

if __name__ == "__main__":
    main()