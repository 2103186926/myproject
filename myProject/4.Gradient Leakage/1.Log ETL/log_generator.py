import random
import datetime
import argparse
import sys

# 定义输出文件名
OUTPUT_FILE = "federated_learning_raw.log"

class LogSimulator:
    def __init__(self):
        self.current_time = datetime.datetime.now()

    def _get_timestamp(self, delta_ms=0):
        """生成递增的时间戳，模拟真实运行时间"""
        self.current_time += datetime.timedelta(milliseconds=delta_ms)
        return self.current_time.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

    def _log(self, level, message, client_id, source="CLIENT"):
        """日志格式：时间戳 - 级别 - [源] [Client ID] 消息"""
        ts = self._get_timestamp(random.randint(5, 50)) # 默认微小的处理时间
        return f"{ts} - {level} - [{source}] [Client {client_id}] {message}"

    def generate_normal_session(self, client_id, round_id):
        """
        生成一次完整的【正常】联邦学习任务日志
        """
        logs = []
        logs.append(self._log("INFO", f"Round {round_id}: Received global model. Starting local training (Standard FL).", client_id))
        
        # 1. 正常的本地训练 (短耗时)
        num_epochs = 5
        for epoch in range(num_epochs):
            time_cost = random.randint(150, 400) # 毫秒级
            self._get_timestamp(time_cost) 
            loss = 3.0 * (0.7 ** epoch) + random.random() * 0.05 # Loss 下降
            # 正常日志：只关注 Prediction Loss，没有 Iteration 循环
            logs.append(self._log("DEBUG", f"Training Epoch {epoch+1}/{num_epochs} | Prediction Loss: {loss:.4f}", client_id))
        
        # 2. 正常上传
        logs.append(self._log("INFO", "Local training finished. Uploading model updates.", client_id))
        self._get_timestamp(random.randint(50, 100)) 
        logs.append(self._log("INFO", "Upload successfully completed.", client_id))
        
        return logs

    def generate_attack_session(self, client_id, round_id):
        """
        生成一次完整的【梯度窃取攻击】任务日志
        """
        logs = []
        logs.append(self._log("INFO", f"Round {round_id}: Received global model. Starting local training (Malicious).", client_id))
        
        # 1. 伪装训练：快速完成
        self._get_timestamp(random.randint(100, 300))
        logs.append(self._log("INFO", "Local training finished. Moving to gradient analysis phase.", client_id))
        
        # 2. 攻击阶段：梯度反演 (Gradient Inversion)
        logs.append(self._log("ATTACK", "Launch: Gradient Leakage Attack initiated.", client_id))
        logs.append(self._log("INFO", "Optimization target: Minimizing Gradient Matching Loss.", client_id)) # 注入关键 Loss 类型
        
        total_iterations = 500
        grad_loss = 25.0
        
        # 模拟漫长的优化循环 (计算耗时异常)
        for i in range(0, total_iterations + 1, 50): 
            # 关键特征：这里的时间流逝非常慢 (每次迭代组模拟 1-3 秒的计算时间)
            self._get_timestamp(random.randint(1000, 3000)) 
            
            grad_loss = grad_loss * 0.85 + random.random() * 0.01 # Loss 下降
            
            # 关键特征：Iteration 循环和 Gradient Loss 关键字
            logs.append(self._log("DEBUG", f"ITERATION {i:4d}/{total_iterations} | Gradient Loss: {grad_loss:.6f} | Data Regularization (TV) Loss: 0.00123", client_id))
            
        logs.append(self._log("ATTACK", "Optimization finished. Target data reconstructed.", client_id))
        
        # 3. 窃取结果保存 (I/O 异常)
        filename = f"reconstructed_ocean_data_{client_id}_{random.randint(1000,9999)}.npy"
        logs.append(self._log("WARNING", f"[FILE_IO] Stolen data saved as {filename}. This should not occur in FL.", client_id)) # 注入异常 I/O 关键字
        
        # 4. 延迟上传 (时序异常)
        logs.append(self._log("INFO", "Uploading final model updates...", client_id))
        self._get_timestamp(random.randint(100, 200)) 
        
        # 5. 服务器端记录上传延迟 (关键特征：服务器视角)
        server_ts = self._get_timestamp(random.randint(500, 1000)) # 模拟服务器接收时间
        logs.append(f"{server_ts} - WARNING - [SERVER] [Client {client_id}] Upload delay detected. Straggler identified (+{random.randint(30, 150)}s lag compared to average).") # 注入延迟警告
        
        return logs

def main():
    # 默认配置：生成 12 条正常日志和 4 条攻击日志
    num_normal = 12
    num_attack = 4
    
    print(f"Generating {num_normal} normal sessions and {num_attack} attack sessions...")
    
    simulator = LogSimulator()
    all_logs = []
    
    # 保证攻击和正常日志交叉出现
    session_types = ['normal'] * num_normal + ['attack'] * num_attack
    random.shuffle(session_types)
    
    client_counter = {'normal': 0, 'malicious': 0}
    
    for session_type in session_types:
        if session_type == 'normal':
            client_counter['normal'] += 1
            client_id = f"NormalNode_{client_counter['normal']:02d}"
            logs = simulator.generate_normal_session(client_id, round_id=random.randint(1, 10))
        else:
            client_counter['malicious'] += 1
            client_id = f"MaliciousNode_{client_counter['malicious']:02d}"
            # 重置时间，让攻击任务分散在不同的时间段
            logs = simulator.generate_attack_session(client_id, round_id=random.randint(1, 10))
        
        all_logs.extend(logs)
        all_logs.append("") 

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in all_logs:
            f.write(line + "\n")
            
    print(f"Successfully generated log file: {OUTPUT_FILE}")
    print("--- 样本日志尾部片段 ---")
    for line in all_logs[-15:]:
        print(line)

if __name__ == "__main__":
    main()