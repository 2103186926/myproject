'''
核心改造：
    1.放弃绝对特征：不再使用 Is_Train 等。
    2.引入统计特征：计算时间间隔的 Rolling Mean (滑动均值) 和 Rolling Std (滑动标准差)。
        逻辑：合法脚本的标准差极小（非常规律）；人类的标准差极大（非常随机）；攻击者介于两者之间（伪随机）。这是 LSTM 需要捕捉的微妙特征。
    3.注入高斯噪声：在最终输出前，给所有特征加上 noise ~ N(0, 0.05)，强行模糊边界，模拟真实世界的传感器误差或网络抖动。
'''

import json
import pandas as pd
import numpy as np
from datetime import datetime

INPUT_FILE = "C:\\Users\\21031\\Desktop\\myProject\\Model Stealing\\1.Log ETL\\优化2\\simulated_logs_hard.json"
OUTPUT_JSON = "lstm_feature_data.json"
OUTPUT_CSV = "features_debug.csv"

def parse_timestamp(ts_str):
    return datetime.fromisoformat(ts_str)

def extract_features(session_logs):
    vectors = []
    start_time = parse_timestamp(session_logs[0]['timestamp'])
    last_time = start_time
    
    # 状态追踪列表（用于计算滑动窗口统计量）
    history_deltas = []
    history_counts = []
    
    cumulative_queries = 0
    
    for log in session_logs:
        curr_time = parse_timestamp(log['timestamp'])
        details = log.get('details', {})
        
        # 1. Time Delta (基础特征)
        time_delta = (curr_time - last_time).total_seconds()
        last_time = curr_time
        
        # 2. Query Count (基础特征)
        q_count = details.get('count', 0)
        cumulative_queries += q_count
        
        # 更新历史窗口 (Window Size = 5)
        history_deltas.append(time_delta)
        history_counts.append(q_count)
        if len(history_deltas) > 5: history_deltas.pop(0)
        if len(history_counts) > 5: history_counts.pop(0)
        
        # 3. Delta Regularity (统计特征 - 关键！)
        # 计算最近5次请求的时间间隔标准差。
        # 脚本(Script) -> Std 接近 0
        # 人类(Human) -> Std 很大
        # 攻击者(Attacker) -> Std 中等 (伪造的随机)
        delta_std = np.std(history_deltas) if len(history_deltas) > 1 else 0
        
        # 4. Delta Mean (统计特征)
        delta_mean = np.mean(history_deltas) if len(history_deltas) > 0 else 0
        
        # 5. Throughput (衍生特征)
        # 当前时刻的平均吞吐量
        elapsed = (curr_time - start_time).total_seconds() + 0.1
        throughput = cumulative_queries / elapsed

        # --- 注入噪声 (Noise Injection) ---
        # 这是为了防止过拟合，模拟真实环境的不确定性
        # 给每个特征加上微小的随机扰动
        noise_factor = 0.05
        
        feat_delta = time_delta + np.random.normal(0, 0.1)
        feat_q_count = q_count # 整数特征通常不加噪声，或者加很小的
        feat_cum_q = cumulative_queries 
        feat_delta_std = delta_std + np.random.normal(0, noise_factor)
        feat_delta_mean = delta_mean + np.random.normal(0, noise_factor)
        feat_throughput = throughput + np.random.normal(0, noise_factor)
        
        # 6. Burstiness (突发性)
        # 检查当前请求量是否显著高于平均值
        mean_count = np.mean(history_counts) if len(history_counts) > 0 else 1
        burst_ratio = q_count / (mean_count + 1e-5)

        # 组合特征向量 (7维)
        # 注意：这里完全没有 label leak (如 is_train, file_name)
        row = [
            max(0, feat_delta),      # 1. 时间间隔
            feat_q_count,            # 2. 单次查询量
            feat_cum_q,              # 3. 累计查询量
            feat_delta_std,          # 4. 间隔规律性 (Std)
            feat_delta_mean,         # 5. 平均间隔
            max(0, feat_throughput), # 6. 吞吐量
            burst_ratio              # 7. 突发比率
        ]
        vectors.append(row)
        
    return vectors

def main():
    print(f"[+] Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    final_samples = []
    max_len = 0
    
    feature_names = ["Time_Delta", "Q_Count", "Cum_Q", "Delta_Std", "Delta_Mean", "Throughput", "Burst_Ratio"]
    
    print("[+] Extracting noisy features...")
    for session in raw_data:
        feats = extract_features(session['logs'])
        if len(feats) > max_len: max_len = len(feats)
        
        label = 1 if session['label'] == 'malicious' else 0
        
        final_samples.append({
            "session_id": session['session_id'],
            "label": label,
            "features": feats
        })
        
    print(f"    Max Seq Len: {max_len}")
    
    # 导出
    output = {
        "feature_names": feature_names,
        "samples": final_samples
    }
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(output, f)
        
    # 生成 CSV 用于观察
    csv_rows = []
    for s in final_samples:
        # 取前50步做快照
        flat = {"id": s['session_id'], "label": s['label']}
        steps = min(len(s['features']), 50)
        for i in range(steps):
            for j, fname in enumerate(feature_names):
                flat[f"t{i}_{fname}"] = s['features'][i][j]
        csv_rows.append(flat)
        
    pd.DataFrame(csv_rows).to_csv(OUTPUT_CSV, index=False)
    print(f"[+] Done. Noisy data saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()