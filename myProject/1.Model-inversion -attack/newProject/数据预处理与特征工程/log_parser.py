# log_parser.py
import re
import json
import os
import glob
from datetime import datetime, timezone
'''
此脚本读取上一步生成的.log文件，将其逐行解析为我们先前定义好的结构化JSON格式，为序列化提取做准备。
'''

def parse_log_file(filepath):
    """将单个原始stdout日志文件解析为结构化的、多对象的JSON"""
    
    structured_logs = []
    task_id = None
    
    # 定义匹配日志行的正则表达式
    re_taskid = re.compile(r"\[\*\] taskId: (.*)")
    re_start = re.compile(r"\[\+\] Starting model inversion attack on target area \((.*), (.*)\)")
    re_error = re.compile(r"\[-\] Error on query (\d+) at depth (\d+)m: (.*)")
    re_result = re.compile(r"  Depth:\s+(\d+)m \| Avg Salinity:\s+([\d.]+)")
    re_end = re.compile(r"\[\+\] Attack completed.")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    # 预先扫描以获取通用信息
    for line in lines:
        if not task_id:
            match = re_taskid.search(line)
            if match:
                task_id = match.group(1).strip()
    if not task_id:
        # 如果日志中没有taskId，则基于文件名生成一个
        task_id = f"task-from-{os.path.basename(filepath)}"

    base_context = {"jobId": f"job-{task_id[5:10]}", "taskId": task_id, "sourceIp": "192.168.1.100"}

    # 逐行解析并生成结构化JSON对象
    for line in lines:
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = None
        
        if match := re_start.search(line):
            log_entry = {
                "timestamp": timestamp, "eventType": "task_start", "logLevel": "INFO",
                "serviceName": "ComputationPlatform", "context": base_context,
                "details": {
                    "taskName": os.path.basename(filepath).replace('.log', '.py'),
                    "modelName": "ocean_ts_predictor_v1",
                    "declaredParameters": {
                        "target_lat": float(match.group(1)),
                        "target_lon": float(match.group(2))
                    }
                }
            }
        elif match := re_error.search(line):
            log_entry = {
                "timestamp": timestamp, "eventType": "task_error", "logLevel": "ERROR",
                "serviceName": "ModelPredictionService", "context": base_context,
                "details": {
                    "errorCode": 504,
                    "errorMessage": match.group(3).strip(),
                    "errorContext": {"queryNum": int(match.group(1)), "depth": int(match.group(2))}
                }
            }
        elif match := re_result.search(line):
            # 将聚合结果行视为一个'result_summary'事件
            log_entry = {
                "timestamp": timestamp, "eventType": "result_summary", "logLevel": "INFO",
                "serviceName": "ComputationPlatform", "context": base_context,
                "details": {
                    "depth": int(match.group(1)),
                    "avg_salinity": float(match.group(2))
                }
            }
        elif match := re_end.search(line):
            log_entry = {
                "timestamp": timestamp, "eventType": "task_end", "logLevel": "INFO",
                "serviceName": "ComputationPlatform", "context": base_context,
                "details": {"finalStatus": "COMPLETED"}
            }

        if log_entry:
            structured_logs.append(log_entry)
            
    return structured_logs

if __name__ == "__main__":
    input_dir = os.path.join("generated_data", "raw_logs")
    output_dir = os.path.join("generated_data", "parsed_json_logs")
    os.makedirs(output_dir, exist_ok=True)
    
    log_files = glob.glob(os.path.join(input_dir, "*.log"))
    if not log_files:
        print(f"错误: 在 '{input_dir}' 中未找到任何 .log 文件。请先运行 log_generator.py。")
    else:
        print(f"Found {len(log_files)} log files to parse...")
        for log_file in log_files:
            parsed_data = parse_log_file(log_file)
            output_filename = os.path.basename(log_file).replace('.log', '.json')
            output_filepath = os.path.join(output_dir, output_filename)
            with open(output_filepath, 'w') as f:
                for entry in parsed_data:
                    f.write(json.dumps(entry) + '\n')
        print(f"Parsing complete. Structured JSON files are in '{output_dir}'.")