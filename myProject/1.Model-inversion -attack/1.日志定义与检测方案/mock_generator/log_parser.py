# log_parser.py
import re
import json
import argparse

def parse_attack_log(log_filepath):
    """解析单个模型逆向攻击日志文件并提取关键特征"""
    
    # 用于存储提取特征的字典
    features = {
        "source_log_file": log_filepath,
        "attack_target": {},
        "scan_pattern": {},
        "statistics": {},
        "reconstructed_profile": [],
        "output_file": None
    }
    
    # 用于匹配不同日志行的正则表达式
    # 特征：对单一或少数几个经纬度点... 
    re_start = re.compile(r"Starting model inversion attack on target area \((.*), (.*)\)")
    # 特征：...进行高分辨率的深度维度的系统性遍历查询。 
    re_probe = re.compile(r"Probing depth from (\d+)m to (\d+)m with step (\d+)m")
    # 特征：对同一个空间点...发起多次...查询。 
    re_completed = re.compile(r"Collected (\d+) data points")
    re_error = re.compile(r"Error on query")
    # 特征：输出（积累了大量高精度的预测值）的信息量极大。 
    re_profile_line = re.compile(r"Depth:\s+(\d+)m\s+\|\s+Avg Salinity:\s+([\d.]+)")
    re_save = re.compile(r"Reconstructed salinity profile saved to (.*)")

    error_count = 0
    
    try:
        with open(log_filepath, 'r') as f:
            for line in f:
                match_start = re_start.search(line)
                if match_start:
                    features["attack_target"] = {
                        "latitude": float(match_start.group(1)),
                        "longitude": float(match_start.group(2))
                    }
                    continue

                match_probe = re_probe.search(line)
                if match_probe:
                    features["scan_pattern"] = {
                        "start_depth_m": int(match_probe.group(1)),
                        "end_depth_m": int(match_probe.group(2)),
                        "depth_step_m": int(match_probe.group(3))
                    }
                    continue

                if re_error.search(line):
                    error_count += 1
                    continue
                    
                match_completed = re_completed.search(line)
                if match_completed:
                    features["statistics"]["total_queries"] = int(match_completed.group(1))
                    continue
                    
                match_profile = re_profile_line.search(line)
                if match_profile:
                    features["reconstructed_profile"].append({
                        "depth_m": int(match_profile.group(1)),
                        "avg_salinity_psu": float(match_profile.group(2))
                    })
                    continue
                    
                match_save = re_save.search(line)
                if match_save:
                    features["output_file"] = match_save.group(1)
                    continue
        
        # 补全统计信息
        features["statistics"]["error_count"] = error_count
        features["statistics"]["successful_depth_points"] = len(features["reconstructed_profile"])

    except FileNotFoundError:
        return {"error": f"File not found: {log_filepath}"}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}
        
    return features

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a model inversion attack log file and output structured JSON.")
    parser.add_argument("logfile", help="Path to the log file to be parsed.")
    args = parser.parse_args()

    parsed_features = parse_attack_log(args.logfile)
    
    # 以美化的格式将JSON输出到标准输出
    print(json.dumps(parsed_features, indent=4))