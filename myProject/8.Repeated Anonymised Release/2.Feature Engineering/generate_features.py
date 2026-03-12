import json
import pandas as pd
import numpy as np
import math
from datetime import datetime

INPUT_FILE = r"C:\Users\21031\Desktop\myProject\Repeated Anonymised Release\1.Log ETL\ocean_cloud_logs_entangled.json"
OUTPUT_JSON = "lstm_feature_data_entangled.json"
OUTPUT_CSV = "lstm_features_entangled.csv"

# 风险分进一步压缩，让差异微乎其微
OP_RISK_MAP = {
    "element_wise_diff": 0.45, 
    "dbscan": 0.55,           
    "mean": 0.2,
    "fetch_dataset": 0.3,
    "check_schema": 0.1
}

class ResearchFeatureExtractor:
    def __init__(self):
        self.sessions = {}

    def load_data(self):
        with open(INPUT_FILE, 'r') as f:
            for line in f:
                log = json.loads(line)
                jid = log['job_id']
                if jid not in self.sessions: self.sessions[jid] = []
                self.sessions[jid].append(log)

    def _extract_features(self, logs):
        features = []
        
        # 衰减状态
        decay_ver_intensity = 0.0
        decay_diff_intensity = 0.0
        
        timestamps = []
        
        for i, log in enumerate(logs):
            curr_ts = datetime.fromisoformat(log['timestamp'])
            timestamps.append(curr_ts.timestamp())
            
            op = log.get("details", {}).get("operator") or log.get("action") or log.get("details", {}).get("algorithm", "")
            
            # --- Feat 1: Decaying Version Intensity ---
            # 这是一个带遗忘机制的计数器。
            # 如果连续下载，值会飙升；如果中间插了伪装操作，值会下降。
            # 这就是 LSTM 必须“拼命记住”的地方。
            is_fetch = 1.0 if log['action'] == "fetch_dataset" else 0.0
            decay_ver_intensity = decay_ver_intensity * 0.9 + is_fetch # Decay factor 0.9
            
            # --- Feat 2: Decaying Diff Intensity ---
            is_diff = 1.0 if "diff" in op else 0.0
            decay_diff_intensity = decay_diff_intensity * 0.85 + is_diff
            
            # --- Feat 3: Time Variance (Rolling Window) ---
            # 窗口大小 5，计算 Log(Variance)
            feat_time_var = 0.0
            if len(timestamps) >= 5:
                recent = np.diff(timestamps[-5:])
                var = np.var(recent)
                feat_time_var = math.log1p(var) # Script -> Low Var, Human -> High Var
                # 归一化到 0-1 左右 (假设 Var 在 0-100 之间)
                feat_time_var = min(1.0, feat_time_var / 5.0)

            # --- Feat 4: Op Risk (Noisy) ---
            base_risk = OP_RISK_MAP.get(op, 0.0)
            noise = np.random.normal(0, 0.1) # 增加噪声幅度
            feat_op_risk = max(0.0, min(1.0, base_risk + noise))
            
            # --- Feat 5: Output (Ambiguous) ---
            out_type = log.get("output", {}).get("type", "")
            feat_out = 0.0
            if "json" in out_type: feat_out = 0.6 
            if "binary" in out_type: feat_out = 0.3 # Model weights
            
            row = [
                round(decay_ver_intensity, 4),
                round(decay_diff_intensity, 4),
                round(feat_time_var, 4),
                round(feat_op_risk, 4),
                round(feat_out, 4)
            ]
            features.append(row)
            
        return features

    def process(self):
        X, y = [], []
        csv_rows = []
        max_len = 0
        
        feature_names = ["ver_decay", "diff_decay", "time_var", "op_risk", "out_score"]
        
        for jid, logs in self.sessions.items():
            seq = self._extract_features(logs)
            if len(seq) > max_len: max_len = len(seq)
            X.append(seq)
            
            # Ground Truth
            # 攻击：Filename 是 reid_targets.json
            # 正常：Filename 是 drift_params.json 或 fl_model.pth
            str_logs = json.dumps(logs)
            is_malicious = 1 if "reid_targets.json" in str_logs else 0
            y.append(is_malicious)
            
            row = {"job_id": jid, "label": is_malicious, "len": len(seq)}
            for t, f in enumerate(seq):
                for fi, val in enumerate(f):
                    row[f"s{t}_{feature_names[fi]}"] = val
            csv_rows.append(row)
            
        X_padded = []
        feat_dim = 5
        for seq in X:
            pad = [[0.0]*feat_dim for _ in range(max_len - len(seq))]
            X_padded.append(seq + pad)
            
        data = {"meta": {"feature_names": feature_names}, "X": X_padded, "y": y}
        
        with open(OUTPUT_JSON, 'w') as f: json.dump(data, f)
        pd.DataFrame(csv_rows).to_csv(OUTPUT_CSV, index=False)
        print(f"[+] Features Extracted. Max Len: {max_len}. Saved to {OUTPUT_JSON}")

if __name__ == "__main__":
    ext = ResearchFeatureExtractor()
    ext.load_data()
    ext.process()