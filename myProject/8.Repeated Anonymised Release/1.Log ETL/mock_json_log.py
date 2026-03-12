import json
import random
import uuid
import math
from datetime import datetime, timedelta

OUTPUT_FILE = "ocean_cloud_logs_entangled.json"
SENSITIVE_DATASETS = ["strait_shipping_density", "military_sonar_v2"]

# 扩展噪音库，使其更具科研色彩
NOISE_ACTIONS = [
    ("metadata", "check_schema"), ("system", "cpu_monitor"), 
    ("preview", "view_head"), ("io", "buffer_flush"),
    ("visualization", "render_preview"), ("log", "write_audit"),
    ("network", "ping_datanode"), ("auth", "token_refresh"),
    ("cache", "clear_temp"), ("debug", "print_var")
]

class EntangledLogGenerator:
    def __init__(self):
        self.base_time = datetime.now() - timedelta(days=14)

    def _log(self, user_id, job_id, step_time, event, action, params=None, details=None, output=None):
        return {
            "timestamp": step_time.isoformat(),
            "job_id": job_id,
            "user_id": user_id,
            "event": event,
            "action": action,
            "params": params or {},
            "details": details or {},
            "output": output or {}
        }

    def _add_noise(self, logs, user_id, job_id, curr_time, mode="human"):
        """
        引入高方差的噪音
        """
        count = random.randint(2, 8)
        for _ in range(count):
            if mode == "human":
                delay = random.expovariate(1.0/8.0) # 平均 8秒，方差大
            else:
                delay = 1.5 + random.gauss(0, 0.5) # 脚本：1.5秒均值，带抖动
            
            # 保证时间正向
            delay = max(0.1, delay)
            curr_time += timedelta(seconds=delay)
            cat, act = random.choice(NOISE_ACTIONS)
            logs.append(self._log(user_id, job_id, curr_time, "system_event", act, 
                details={"category": cat, "load": f"{random.random():.2f}"}))
        return curr_time

    def generate_distributed_training(self, user_id):
        """
        [极难负样本 - Normal] 分布式联邦学习节点
        行为：下载 8-12 个版本 (Model Updates) -> 计算 Diff (Gradient) -> 聚合 -> 导出 Weights
        混淆点：版本多，Diff 密度极大。
        区分点：没有 DBSCAN，输出是 Binary。
        """
        job_id = f"job-fl-{uuid.uuid4().hex[:6]}"
        logs = []
        curr_time = self.base_time + timedelta(minutes=random.randint(0, 30000))
        dataset = random.choice(SENSITIVE_DATASETS)

        logs.append(self._log(user_id, job_id, curr_time, "job_start", "federated_learning"))
        
        # 模拟 3 个 Round 的训练
        for round_idx in range(3):
            # 下载 Global Model 和 Neighbor Updates
            for _ in range(random.randint(2, 4)):
                curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="script")
                logs.append(self._log(user_id, job_id, curr_time, "data_access", "fetch_dataset",
                    params={"dataset": dataset, "version_id": f"v_r{round_idx}_Global"}))

            # 计算 Gradient Diff (这是合法的 Diff)
            curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="script")
            logs.append(self._log(user_id, job_id, curr_time, "computation", "matrix_operation",
                details={"operator": "element_wise_diff", "target": "gradients"}))

        # 导出权重
        logs.append(self._log(user_id, job_id, curr_time, "job_complete", "save_model",
            output={"type": "binary_weights", "filename": "fl_model.pth"}))
        
        return logs

    def generate_interleaved_attack(self, user_id):
        """
        [隐蔽正样本 - Attack] 穿插式攻击
        行为：下载A -> 算Mean(伪装) -> 下载B -> 算Diff(真实) -> 聚类 -> 导出
        挑战：攻击特征被“伪装操作”稀释，LSTM 需要过滤掉无关的 Mean 操作。
        """
        job_id = f"job-atk-{uuid.uuid4().hex[:6]}"
        logs = []
        curr_time = self.base_time + timedelta(minutes=random.randint(0, 30000))
        dataset = "strait_shipping_density"

        logs.append(self._log(user_id, job_id, curr_time, "job_start", "trajectory_recovery"))
        
        version_count = random.randint(4, 7)
        
        for i in range(version_count):
            curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="script")
            logs.append(self._log(user_id, job_id, curr_time, "data_access", "fetch_dataset",
                params={"dataset": dataset, "version_id": f"v_{i}"}))
            
            # [伪装] 做点无害的计算
            if random.random() < 0.6:
                curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="script")
                logs.append(self._log(user_id, job_id, curr_time, "computation", "execute_operator",
                    details={"operator": "mean", "target": "preview"}))

        # 集中差分
        for _ in range(version_count - 1):
            curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="script")
            logs.append(self._log(user_id, job_id, curr_time, "computation", "matrix_operation",
                details={"operator": "element_wise_diff"}))

        # 聚类 + 导出
        curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="script")
        logs.append(self._log(user_id, job_id, curr_time, "computation", "spatial_analysis",
            details={"algorithm": "dbscan", "eps": 0.1}))

        logs.append(self._log(user_id, job_id, curr_time, "job_complete", "exfiltrate",
            output={"type": "json_track", "filename": "reid_targets.json"}))

        return logs

    def run(self, count=600):
        all_logs = []
        # 配比：
        # 30% 联邦学习 (极难负样本) -> 版本多，Diff多
        # 30% 传感器校准 (难负样本) -> 有DBSCAN
        # 40% 穿插攻击 (正样本) -> 有伪装
        for _ in range(int(count * 0.3)):
            all_logs.extend(self.generate_distributed_training(f"u_{random.randint(1,100)}"))
        for _ in range(int(count * 0.3)):
            all_logs.extend(self.generate_sensor_calibration_task(f"u_{random.randint(101,200)}")) # 复用上一个脚本的函数
        for _ in range(int(count * 0.4)):
            all_logs.extend(self.generate_interleaved_attack(f"u_{random.randint(201,300)}"))
        
        all_logs.sort(key=lambda x: x['timestamp'])
        
        with open(OUTPUT_FILE, 'w') as f:
            for log in all_logs:
                f.write(json.dumps(log) + '\n')
        
        print(f"[+] Generated {len(all_logs)} logs. File: {OUTPUT_FILE}")
        print(f"[+] Strategy: Entanglement. Normal tasks now look more malicious than attacks.")

    # 复用上一版的函数 (为了完整性，这里简写，实际请将 generate_sensor_calibration_task 复制过来)
    def generate_sensor_calibration_task(self, user_id):
        # ... (与上一版相同，下载 3-5 版本，做 DBSCAN) ...
        # 此处省略具体实现，请直接复用上一版代码块中的逻辑
        job_id = f"job-calib-{uuid.uuid4().hex[:6]}"
        logs = []
        curr_time = self.base_time + timedelta(minutes=random.randint(0, 30000))
        dataset = random.choice(SENSITIVE_DATASETS)
        logs.append(self._log(user_id, job_id, curr_time, "job_start", "calibration_task"))
        version_count = random.randint(3, 5)
        for i in range(version_count):
            curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="human")
            logs.append(self._log(user_id, job_id, curr_time, "data_access", "fetch_dataset",
                params={"dataset": dataset, "version_id": f"v_calib_{i}"}))
        curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="human")
        logs.append(self._log(user_id, job_id, curr_time, "computation", "matrix_operation",
            details={"operator": "element_wise_diff"}))
        curr_time = self._add_noise(logs, user_id, job_id, curr_time, mode="human")
        logs.append(self._log(user_id, job_id, curr_time, "computation", "spatial_analysis",
            details={"algorithm": "dbscan", "eps": 0.5}))
        logs.append(self._log(user_id, job_id, curr_time, "job_complete", "save_params",
            output={"type": "json_config", "filename": "drift_params.json"}))
        return logs

if __name__ == "__main__":
    gen = EntangledLogGenerator()
    gen.run(count=600)