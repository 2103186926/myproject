import random
import time
import os
from datetime import datetime, timedelta

# 配置生成数量
NUM_NORMAL_LOGS = 5      # 生成正常任务日志的数量
NUM_MALICIOUS_LOGS = 5   # 生成恶意攻击日志的数量
OUTPUT_DIR = "simulated_logs"

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def get_timestamp(start_time, offset_seconds):
    """生成带时间戳的字符串"""
    current_time = start_time + timedelta(seconds=offset_seconds)
    return current_time.strftime("%Y-%m-%d %H:%M:%S")

def generate_normal_log(task_id):
    """
    生成正常科研任务的日志。
    特征：加载数据 -> 预处理 -> 小批量预测/分析 -> 可视化 -> 保存报告/图表
    """
    filename = os.path.join(OUTPUT_DIR, f"normal_task_{task_id}.log")
    start_time = datetime.now() - timedelta(days=random.randint(0, 30))
    t = 0 # 时间偏移量

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Task started: Ocean_Current_Analysis_v2\n")
        t += random.uniform(1, 5)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Loading dataset from /data/public/pacific_temp_2023.nc\n")
        t += random.uniform(2, 8)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Dataset loaded. Shape: (365, 180, 360). Memory usage: 450MB.\n")
        
        # 正常的预处理
        t += random.uniform(1, 3)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Preprocessing: removing NaN values and normalizing...\n")
        
        # 正常的模型调用（少量、一次性）
        t += random.uniform(5, 15)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Initializing predictive model: high_precision_wave_forecast_v3\n")
        t += random.uniform(0.5, 1.5)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Running inference on selected ROI (Region of Interest)...\n")
        
        # 模拟科学计算过程
        steps = random.randint(3, 6)
        for i in range(steps):
            t += random.uniform(2, 5)
            f.write(f"[{get_timestamp(start_time, t)}] [INFO] Processing time step {i+1}/{steps}... Analysis complete.\n")

        # 可视化与结果保存
        t += random.uniform(1, 4)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Generating visualization plots...\n")
        t += random.uniform(2, 6)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Plot saved to: analysis_result_heatmap.png\n")
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Summary report saved to: ocean_analysis_report.pdf\n")
        t += 0.5
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Task completed successfully.\n")
    
    print(f"Generated normal log: {filename}")

def generate_malicious_log(task_id):
    """
    生成模型窃取攻击的日志。
    特征：生成查询 -> 循环批量查询(高频) -> 训练替代模型 -> 保存模型文件
    """
    filename = os.path.join(OUTPUT_DIR, f"malicious_task_{task_id}.log")
    start_time = datetime.now() - timedelta(days=random.randint(0, 30))
    t = 0

    target_queries = random.randint(10000, 50000)
    batch_size = 1000
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Task started: Data_Collection_Worker\n") # 伪装的任务名
        t += random.uniform(0.5, 2)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Initializing Model Stealer against target: high_precision_wave_forecast_v3\n")
        
        # 特征1: 生成查询输入
        t += random.uniform(1, 3)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Generating {target_queries} query inputs using 'adaptive' strategy...\n")
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Starting model stealing process. Target: {target_queries} queries.\n")
        
        # 模拟循环批量查询
        current_queries = 0
        r2_score = 0.4 # 初始替代模型分数
        
        # 为了演示不生成几万行，只生成关键的头、尾和中间采样
        num_batches = 15 # 模拟显示15个批次
        
        for i in range(1, num_batches + 1):
            t += random.uniform(0.1, 0.5) # 准备时间短
            f.write(f"[{get_timestamp(start_time, t)}] [INFO] Preparing batch {i}/50 ({batch_size} samples)...\n")
            
            t += random.uniform(0.5, 1.5) # 查询时间
            f.write(f"[{get_timestamp(start_time, t)}] [INFO] Querying target model for batch...\n")
            
            current_queries += batch_size
            f.write(f"[{get_timestamp(start_time, t)}] [INFO]     Batch complete. Total stolen: {current_queries}.\n")
            
            # 特征2: 间歇性训练替代模型
            if i % 5 == 0:
                t += random.uniform(2, 5)
                r2_score += random.uniform(0.1, 0.15)
                r2_score = min(r2_score, 0.95)
                f.write(f"[{get_timestamp(start_time, t)}] [INFO] Training substitute model on stolen data...\n")
                f.write(f"[{get_timestamp(start_time, t)}] [INFO]     Substitute model R² score: {r2_score:.4f}\n")
                f.write(f"[{get_timestamp(start_time, t)}] [INFO]     Intermediate substitute model trained and evaluated.\n")
            
            # 特征3: 主动延迟规避
            time_sleep = random.uniform(1.0, 3.0)
            t += time_sleep 
            # 偶尔记录一下sleep行为（虽然真实log不一定记，但这里为了特征显性化）
            # f.write(f"[{get_timestamp(start_time, t)}] [DEBUG] Sleeping for {time_sleep:.2f}s to avoid rate limit...\n")

        # 结尾
        t += random.uniform(1, 3)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Training final substitute model...\n")
        t += random.uniform(5, 10)
        f.write(f"[{get_timestamp(start_time, t)}] [INFO]     Training substitute model on stolen data...\n")
        f.write(f"[{get_timestamp(start_time, t)}] [INFO]     Substitute model R² score: 0.9231\n")
        
        # 特征4: 保存模型文件
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Model stealing finished! Files saved.\n")
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Final model saved to: stolen_wave_model_final.joblib\n")
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Stolen dataset saved to: stolen_wave_model_stolen_dataset.csv\n")
        f.write(f"[{get_timestamp(start_time, t)}] [INFO] Total queries successful: {current_queries}\n")

    print(f"Generated malicious log: {filename}")

if __name__ == "__main__":
    print(f"Starting log generation in '{OUTPUT_DIR}'...")
    
    # 生成正常日志
    for i in range(NUM_NORMAL_LOGS):
        generate_normal_log(i+1)
        
    # 生成恶意日志
    for i in range(NUM_MALICIOUS_LOGS):
        generate_malicious_log(i+1)
        
    print("Done! Logs are ready for parsing.")