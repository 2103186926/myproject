# log_parser.py
import os
import re
import json
from datetime import datetime

# --- 配置 ---
INPUT_DIR = 'raw_logs'
OUTPUT_DIR = 'generated_data/parsed_json_logs'
# 正则表达式用于解析 log_generator.py 的日志格式
LOG_PATTERN = re.compile(r'\[(?P<timestamp>\d+\.\d+)\] (?P<logLevel>\w+): (?P<eventType>\w+): (?P<details>.*)')
TASK_ID_PATTERN = re.compile(r'TaskID=([a-f0-9]+)')

# --- 辅助函数 ---

def parse_log_line(line, task_id):
    """解析单行日志并返回结构化字典"""
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None
    
    data = match.groupdict()
    
    event_data = {
        "timestamp": float(data['timestamp']),
        "logLevel": data['logLevel'],
        "eventType": data['eventType'],
        "context": {"taskId": task_id},
        "details": {}
    }
    
    detail_str = data['details']
    
    if data['eventType'] == 'task_start':
        is_malicious_match = re.search(r'is_malicious=(True|False)', detail_str)
        event_data['details']['is_malicious'] = is_malicious_match.group(1) == 'True'
        
    elif data['eventType'] == 'model_query':
        # 提取 Query=X/Y, Confidence=Z, Features=[...]
        conf_match = re.search(r'Confidence=([\d\.]+)', detail_str)
        feat_match = re.search(r'Features=\[([^\]]+)\]', detail_str)
        
        event_data['details']['queryResponse'] = {
            "confidence": float(conf_match.group(1)) if conf_match else 0.0
        }
        # 注意: 这里的Features只用于标记，完整的featureVector留给generate_sequential_features.py处理，
        # 但我们仍然需要解析出部分信息，这里仅作为占位符/标记。
        
    elif data['eventType'] == 'internal_activity':
        # 提取 Type=attack_model_training
        type_match = re.search(r'Type=([\w_]+)', detail_str)
        event_data['details']['activityType'] = type_match.group(1) if type_match else 'unknown'
        
    elif data['eventType'] == 'task_end':
        # 提取 OutputSizeBytes
        size_match = re.search(r'OutputSizeBytes=(\d+)', detail_str)
        event_data['details']['finalOutputSizeBytes'] = int(size_match.group(1)) if size_match else 0
        
    return event_data

def parse_log_file(filepath):
    """解析整个日志文件，返回结构化事件列表"""
    task_id = TASK_ID_PATTERN.search(os.path.basename(filepath)).group(1)
    structured_logs = []
    
    with open(filepath, 'r') as f:
        for line in f:
            event = parse_log_line(line, task_id)
            if event:
                structured_logs.append(event)
                
    return structured_logs

# --- 主执行逻辑 ---

def main_parser():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.log')]
    
    total_files = len(log_files)
    
    for i, filename in enumerate(log_files):
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"Parsing {i+1}/{total_files}: {filename}...")
        
        structured_data = parse_log_file(filepath)
        
        output_filename = os.path.join(OUTPUT_DIR, f"{filename[:-4]}.json") # 替换.log为.json
        with open(output_filename, 'w') as f:
            json.dump(structured_data, f, indent=2)
            
    print("\n--- Parsing Complete ---")
    print(f"Structured JSON files saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main_parser()