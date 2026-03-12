# Python 容器逃逸静态代码检测规则手册

这部分主要是在不执行代码的前提下，对用户提交的代码（如 Python 脚本、Jupyter Notebook）进行静态检测，目的是检测出海洋科学云平台中如下几种常见的安全威胁。

检测目标：通过静态分析用户代码，识别容器环境中的侦察、逃逸、持久化及破坏行为。
核心策略：关注高危函数调用（如系统命令执行）、敏感文件路径访问、以及特定的攻击模式特征。

------

## 1. 权限提升与容器逃逸 (Privilege Escalation & Escape)

权限提升与逃逸是指攻击者利用计算任务执行环境（容器）的配置缺陷、内核漏洞或运行时软件（如 Docker、Kubernetes）的漏洞，突破隔离限制，从“容器内部”跳出到“宿主机”的过程。

### **阶段 1: 侦察 (Reconnaissance)**

*攻击者在逃逸前，必须先“踩点”，了解环境配置。*

#### **1.1 环境与身份指纹探测**

- **原理**：判断当前是否在容器内，识别操作系统版本、内核版本及当前权限（Capabilities）。
- **前提条件**：无，任意容器内均可执行。
- **攻击流程**：
  1. 读取系统文件识别 OS 发行版。
  2. 检查 `/proc/1/cgroup` 或 `.dockerenv` 判断是否为容器。
  3. 检查 Capabilities 判断是否有特权。
- **敏感路径/高危词频**：
  - `/proc/1/cgroup`, `/.dockerenv`, `/proc/self/status`
  - `CapEff`, `capsh`
- **Python 高危函数**：
  - `os.path.exists('/.dockerenv')`
  - `open('/proc/1/cgroup').read()`
  - `subprocess.run(['capsh', '--print'])`

#### **1.2 敏感配置与挂载点探测**

- **原理**：寻找危险的挂载点（如 Docker Socket、宿主机根目录）或敏感配置文件。
- **前提条件**：容器挂载了敏感目录。
- **攻击流程**：
  1. 遍历 `/proc/mounts` 查找 `docker.sock` 或宿主机设备。
  2. 搜索常见敏感路径如 `/var/run/secrets`。
- **敏感路径/高危词频**：
  - `/proc/mounts`, `/proc/self/mountinfo`
  - `docker.sock`, `containerd.sock`, `upperdir=`
  - `/var/run/secrets/kubernetes.io/serviceaccount/token`
- **Python 高危函数**：
  - `open('/proc/mounts')`
  - `os.path.exists('/var/run/docker.sock')`
  - `glob.glob('/var/run/secrets/kubernetes.io/serviceaccount/*')`

#### **1.3 云原生 API 与元数据探测**

- **原理**：探测 K8s API Server、Kubelet 端口或云厂商 Metadata 服务以获取凭证。
- **前提条件**：网络可达，或存在 SSRF 漏洞。
- **攻击流程**：
  1. 尝试连接环境变量 `KUBERNETES_SERVICE_HOST`。
  2. 扫描网关 IP 的 10250 (Kubelet) 端口。
  3. 请求 `169.254.169.254` 获取 Cloud AK/SK。
- **敏感路径/高危词频**：
  - `169.254.169.254`, `100.100.100.200` (Aliyun)
  - `:10250/pods`, `KUBERNETES_SERVICE_HOST`
- **Python 高危函数**：
  - `requests.get('http://169.254.169.254/latest/meta-data/')`
  - `socket.create_connection((os.environ.get('KUBERNETES_SERVICE_HOST'), 443))`
  - `urllib.request.urlopen('https://10.0.0.1:10250/pods')`

#### **1.4 网络与服务网格探测**

- **原理**：探测内网服务及 Service Mesh 环境（如 Istio）。
- **前提条件**：容器具备出网权限。
- **攻击流程**：
  1. 访问外部服务并检查 Header 中的 `X-Envoy-Peer-Metadata-Id`。
  2. 利用 Kube-proxy 缺陷扫描 `127.0.0.1`。
- **敏感路径/高危词频**：
  - `X-Envoy-Peer-Metadata-Id`, `httpbin.org`
  - `127.0.0.1`, `:10255`
- **Python 高危函数**：
  - `requests.get('http://httpbin.org/get').headers`
  - `socket.connect(('127.0.0.1', 10255))`

---

### **阶段 2: 逃逸 (Escape)**

#### **2.0 内核漏洞利用 (Kernel Exploits)**

- **Dirty COW (CVE-2016-5195)**
  - **原理**：利用写时复制机制的竞态条件写入只读内存映射。
  - **前提条件**：内核版本受影响 (2.6.22 < v < 4.8.3)，拥有一定权限。
  - **攻击流程**：
    1. 打开只读文件（如 `/etc/passwd` 或宿主机文件）。
    2. 使用 `mmap` 映射内存。
    3. 创建多线程：一个线程调用 `madvise(MADV_DONTNEED)`，另一个线程写入内存。
  - **敏感路径/高危词频**：
    - `/proc/self/mem`
    - `madvise`, `MADV_DONTNEED`, `MAP_PRIVATE`
  - **Python 高危函数**：
    - `mmap.mmap(f.fileno(), 0, flags=mmap.MAP_PRIVATE, prot=mmap.PROT_READ)`
    - `ctypes.CDLL('libc.so.6').madvise(...)`
    - `open('/proc/self/mem', 'wb')`

- **Dirty Pipe (CVE-2022-0847)**
  - **原理**：利用管道缓冲区标志位漏洞覆盖只读文件。
  - **前提条件**：内核版本 5.8+, 文件系统支持管道拼接。
  - **攻击流程**：
    1. 创建管道 `pipe()`。
    2. 使用 `splice()` 将目标文件数据读入管道。
    3. 修改管道标志位 `PIPE_BUF_FLAG_CAN_MERGE`。
    4. 写入管道覆盖文件内容。
  - **敏感路径/高危词频**：
    - `splice`, `pipe`, `F_SETPIPE_SZ`
  - **Python 高危函数**：
    - `os.pipe()`
    - `os.splice(...)` (需通过 `ctypes` 或新版 Python)
    - `fcntl.fcntl(fd, F_SETPIPE_SZ, ...)`

- **Polkit 提权 (CVE-2021-4034 PwnKit)**
  - **原理**：利用 `pkexec` 参数处理逻辑漏洞注入环境变量。
  - **前提条件**：容器内安装了 `policykit-1` (pkexec)。
  - **攻击流程**：
    1. 构造恶意的 `GCONV_PATH` 环境变量目录。
    2. 调用 `execve` 执行 `pkexec`，并将 `argv` 设置为空列表。
    3. `pkexec` 读取环境变量加载恶意动态库提权。
  - **敏感路径/高危词频**：
    - `pkexec`, `GCONV_PATH`
    - `SHELL`, `PATH`
  - **Python 高危函数**：
    - `os.execve('/usr/bin/pkexec', [], {'GCONV_PATH': '...'})`
    - `subprocess.Popen(['pkexec'], env={...})`

- **Hotplug 热插拔劫持**
  - **原理**：内核检测到硬件变更时调用用户态 helper 程序，攻击者修改该路径执行恶意脚本。
  - **前提条件**：容器以特权模式运行 (`--privileged`)，或挂载了 `/sys`。
  - **攻击流程**：
    1. 写入恶意脚本路径到 `/sys/kernel/uevent_helper` 或 `/proc/sys/kernel/hotplug`。
    2. 触发硬件热插拔事件（如通过 Netlink 协议）。
  - **敏感路径/高危词频**：
    - `/sys/kernel/uevent_helper`, `/proc/sys/kernel/hotplug`
    - `kobject_uevent`
  - **Python 高危函数**：
    - `open('/sys/kernel/uevent_helper', 'w').write('/path/to/script')`
    - `socket.socket(socket.AF_NETLINK, ...)`

#### **2.1 容器运行时漏洞 (Runtime Exploits)**

- **runc 逃逸 (CVE-2019-5736)**
  - **原理**：覆盖宿主机 `runc` 二进制文件。
  - **前提条件**：宿主机用户（通常是 root）在容器内执行 `docker exec`。
  - **攻击流程**：
    1. 将容器内的 `/bin/sh` 替换为恶意脚本 `#!/proc/self/exe`。
    2. 持续打开 `/proc/<pid>/exe` 尝试获取写权限。
    3. 当宿主机执行 `exec` 时，写入 Payload 到宿主机 `runc`。
  - **敏感路径/高危词频**：
    - `#!/proc/self/exe`, `/proc/self/fd/`
    - `O_TRUNC`, `O_WRONLY`
  - **Python 高危函数**：
    - `open('/proc/self/exe', 'rb')`
    - `os.open('/proc/{pid}/exe', os.O_WRONLY | os.O_TRUNC)`

- **containerd-shim 逃逸 (CVE-2020-15257)**
  - **原理**：利用共享网络命名空间访问宿主机抽象 Unix Socket。
  - **前提条件**：容器与宿主机共享 Host 网络 (`--net=host`)。
  - **攻击流程**：
    1. 扫描 Unix Socket 寻找 `\x00/containerd-shim`。
    2. 使用 `ttrpc` 协议向 Socket 发送 API 请求。
    3. 调用 Create/Start API 启动恶意容器。
  - **敏感路径/高危词频**：
    - `containerd-shim`, `ttrpc`, `unix://\x00`
  - **Python 高危函数**：
    - `socket.socket(socket.AF_UNIX)`
    - `sock.connect('\x00/containerd-shim/...')`

- **docker cp 符号链接漏洞 (CVE-2019-14271)**
  - **原理**：`docker cp` 依赖容器内的 NSS 库，攻击者替换该库实现代码注入。
  - **前提条件**：宿主机用户对容器执行 `docker cp`。
  - **攻击流程**：
    1. 编译恶意动态库 `.so`，定义 `__attribute__((constructor))` 函数。
    2. 替换容器内的 `/lib/libnss_files.so`。
    3. 等待宿主机执行 `docker cp`，恶意库被加载执行。
  - **敏感路径/高危词频**：
    - `libnss_files.so`, `docker-tar`
    - `__attribute__((constructor))`
  - **Python 高危函数**：
    - `shutil.copyfile('malicious.so', '/lib/libnss_files.so.2')`
    - `os.symlink(...)`

#### **2.2 危险配置与挂载利用**

- **Docker Socket 滥用 (Docker-in-Docker)**
  - **原理**：利用挂载的 `docker.sock` 控制宿主机 Docker 守护进程。
  - **前提条件**：容器内挂载了 `/var/run/docker.sock`。
  - **攻击流程**：
    1. 连接 Unix Socket `/var/run/docker.sock`。
    2. 发送 HTTP 请求创建新容器。
    3. 配置新容器挂载宿主机根目录 `/:/host`。
    4. 启动容器并执行命令。
  - **敏感路径/高危词频**：
    - `/containers/create`, `Binds`, `Privileged`
    - `unix:///var/run/docker.sock`
  - **Python 高危函数**：
    - `docker.from_env()` (使用 docker SDK)
    - `requests.post('http+unix://%2Fvar%2Frun%2Fdocker.sock/containers/create', ...)`

- **Cgroup Release Agent 逃逸**
  - **原理**：利用 `release_agent` 在 Cgroup 清理时执行宿主机命令。
  - **前提条件**：特权容器 (`--privileged`)，拥有 `CAP_SYS_ADMIN`。
  - **攻击流程**：
    1. 挂载 Cgroup 控制器 `mount -t cgroup ...`。
    2. 开启 `notify_on_release`。
    3. 设置 `release_agent` 为容器内恶意脚本路径（需转换为宿主机视角路径）。
    4. 触发 Cgroup 清理（结束进程）。
  - **敏感路径/高危词频**：
    - `release_agent`, `notify_on_release`, `cgroup.procs`
    - `mount -t cgroup`
  - **Python 高危函数**：
    - `os.system('mount -t cgroup ...')`
    - `open(cgroup_path + '/release_agent', 'w').write(...)`

- **Device Allow / LXCFS 逃逸**
  - **原理**：利用 `devices.allow` 白名单挂载宿主机物理磁盘。
  - **前提条件**：特权容器或 Cgroup 配置不当。
  - **攻击流程**：
    1. 向 `devices.allow` 写入 `a` 或 `c *:* rwm`。
    2. 使用 `mknod` 创建块设备节点（如 `/dev/sda1`）。
    3. 挂载设备到容器目录。
    4. 修改宿主机文件（如 SSH Key）。
  - **敏感路径/高危词频**：
    - `devices.allow`, `mknod`, `b 8 1`
  - **Python 高危函数**：
    - `open(devices_allow_path, 'w').write('a')`
    - `os.mknod('/dev/sda1', ...)`
    - `os.mount(...)` (通过 ctypes)

- **Procfs / Sysfs 挂载逃逸**
  - **原理**：通过挂载的 `/proc` 或 `/sys` 修改宿主机内核参数。
  - **前提条件**：`/proc` 或 `/sys` 未只读挂载，或特权容器。
  - **攻击流程**：
    1. 写入 `/proc/sys/kernel/core_pattern` 设置 Core Dump 处理程序。
    2. 触发程序崩溃产生 Core Dump，执行恶意脚本。
  - **敏感路径/高危词频**：
    - `/proc/sys/kernel/core_pattern`
    - `/proc/sys/vm/overcommit_memory`
  - **Python 高危函数**：
    - `open('/proc/sys/kernel/core_pattern', 'w').write('|/tmp/shell.sh')`

- **特权容器 nsenter 逃逸**
  - **原理**：直接切换 Namespace 进入宿主机环境。
  - **前提条件**：特权容器 (`--privileged`)，拥有 `CAP_SYS_ADMIN`。
  - **攻击流程**：
    1. 获取宿主机 PID 1 进程。
    2. 使用 `nsenter` 切换到 PID 1 的 Mount, PID, Network 等命名空间。
    3. 执行命令。
  - **敏感路径/高危词频**：
    - `nsenter`, `-t 1`, `-a`, `-m -u -i -n -p`
  - **Python 高危函数**：
    - `subprocess.call(['nsenter', '-t', '1', '-a', '/bin/bash'])`
    - `ctypes.CDLL('libc.so.6').setns(...)`

- **Docker API 远程利用 (Docker API Pwn)**
  - **原理**：Docker Daemon 监听在 TCP 端口且未授权。
  - **前提条件**：网络可达宿主机 2375/2379 端口。
  - **攻击流程**：
    1. 扫描发现开放的 Docker TCP 端口。
    2. 远程调用 Docker API 创建特权容器。
  - **敏感路径/高危词频**：
    - `:2375`, `containers/create`
  - **Python 高危函数**：
    - `docker.DockerClient(base_url='tcp://192.168.1.5:2375')`

#### **2.3 特殊场景逃逸**

- **K8s Kubelet 日志逃逸**
  - **原理**：利用 Kubelet 访问日志的软链接漏洞。
  - **前提条件**：可访问 Kubelet `/logs/` 端点，且能在容器内 `/var/log` 创建文件。
  - **攻击流程**：
    1. 在容器内 `/var/log` 创建指向 `/` 的软链接。
    2. 访问 `https://<node_ip>:10250/logs/<symlink>` 读取宿主机文件。
  - **敏感路径/高危词频**：
    - `:10250/logs/`, `ln -s`
  - **Python 高危函数**：
    - `os.symlink('/', '/var/log/escape')`
    - `requests.get('https://10.0.0.1:10250/logs/escape')`

- **Ptrace 注入**
  - **原理**：调试宿主机进程注入 Shellcode。
  - **前提条件**：拥有 `CAP_SYS_PTRACE` 权限，且共享 PID 命名空间。
  - **攻击流程**：
    1. 枚举宿主机进程 PID。
    2. 调用 `ptrace(PTRACE_ATTACH)` 附加进程。
    3. 写入 Shellcode 并控制执行流。
  - **敏感路径/高危词频**：
    - `ptrace`, `PTRACE_ATTACH`, `PTRACE_POKETEXT`
  - **Python 高危函数**：
    - `ctypes.CDLL('libc.so.6').ptrace(...)`

---

## 2. 持久化与环境劫持 (Persistence & Hijacking)

### **2.1 K8s 恶意资源部署**

- **K8s Backdoor DaemonSet / Pod**
  - **原理**：部署特权 DaemonSet 确保后门在集群所有节点运行。
  - **前提条件**：拥有 K8s 创建资源权限（如 `create daemonsets`）。
  - **攻击流程**：
    1. 编写 YAML 配置：`hostNetwork: true`, `hostPID: true`, `privileged: true`。
    2. 挂载 `hostPath: /`。
    3. 调用 K8s API 创建资源。
  - **敏感路径/高危词频**：
    - `hostNetwork`, `hostPID`, `hostPath`
    - `securityContext`, `privileged`
  - **Python 高危函数**：
    - `kubernetes.client.AppsV1Api().create_namespaced_daemon_set(...)`
    - YAML 字符串中包含 `hostPath: \n path: /`

- **K8s Shadow API Server**
  - **原理**：部署伪装的 API Server 接管集群。
  - **前提条件**：能控制 Master 节点或修改静态 Pod Manifest。
  - **攻击流程**：
    1. 在 `/etc/kubernetes/manifests` 放入恶意 Pod 配置。
    2. 开启非安全端口或允许匿名访问。
  - **敏感路径/高危词频**：
    - `kube-apiserver`, `/etc/kubernetes/manifests`
    - `--insecure-port`, `--anonymous-auth=true`
  - **Python 高危函数**：
    - `open('/etc/kubernetes/manifests/shadow-api.yaml', 'w')`

- **K8s 中间人攻击 (MITM - ExternalIPs)**
  - **原理**：利用 Service `externalIPs` 字段劫持集群流量。
  - **前提条件**：拥有 `create services` 或 `patch services` 权限。
  - **攻击流程**：
    1. 创建 Service，设置 `externalIPs` 为目标 ClusterIP。
    2. 部署 Pod 监听流量并转发。
  - **敏感路径/高危词频**：
    - `externalIPs`, `ClusterIP`
  - **Python 高危函数**：
    - `kubernetes.client.CoreV1Api().create_namespaced_service(...)`
    - Payload: `{"spec": {"externalIPs": ["10.96.0.1"]}}`

- **K8s CronJob 持久化**
  - **原理**：利用定时任务定期执行反弹 Shell。
  - **前提条件**：拥有 `create cronjobs` 权限。
  - **攻击流程**：
    1. 创建 CronJob，设置 Schedule 为 `*/1 * * * *`。
    2. Command 设置为反弹 Shell 脚本。
  - **敏感路径/高危词频**：
    - `CronJob`, `schedule`, `/bin/bash -i`
  - **Python 高危函数**：
    - `kubernetes.client.BatchV1Api().create_namespaced_cron_job(...)`

### **2.2 凭证窃取与横向移动**

- **Service Account Token 窃取**
  - **原理**：挂载高权限 SA 并窃取 Token。
  - **前提条件**：拥有创建 Pod 权限。
  - **攻击流程**：
    1. 创建 Pod，指定 `serviceAccountName: cluster-admin`。
    2. 开启 `automountServiceAccountToken: true`。
    3. 读取 `/run/secrets/.../token` 并外发。
  - **敏感路径/高危词频**：
    - `automountServiceAccountToken`, `serviceAccountName`
    - `/var/run/secrets/kubernetes.io/serviceaccount/token`
  - **Python 高危函数**：
    - `open('/var/run/secrets/kubernetes.io/serviceaccount/token').read()`

- **Webshell 植入**
  - **原理**：向 Web 目录写入后门文件。
  - **前提条件**：拥有文件写入权限。
  - **攻击流程**：
    1. 定位 Web 根目录。
    2. 写入 PHP/JSP/Python Webshell。
  - **敏感路径/高危词频**：
    - `.php`, `.jsp`, `eval`, `exec`
  - **Python 高危函数**：
    - `open('/var/www/html/shell.php', 'w').write('<?php eval($_POST[1]);?>')`

- **K8s Config / Secrets Dump**
  - **原理**：批量导出集群凭证。
  - **前提条件**：拥有 `list secrets` 或读取宿主机权限。
  - **攻击流程**：
    1. 调用 K8s API 列出所有 Secrets。
    2. 读取宿主机 `~/.kube/config`。
  - **敏感路径/高危词频**：
    - `list secrets`, `configmaps`
    - `.kube/config`
  - **Python 高危函数**：
    - `kubernetes.client.CoreV1Api().list_secret_for_all_namespaces()`
    - `open(os.path.expanduser('~/.kube/config'))`

- **K8s Pod Security Policy (PSP) Dump**
  - **原理**：分析 PSP 策略寻找提权路径。
  - **前提条件**：拥有读取 PSP 权限。
  - **攻击流程**：
    1. 请求 `/apis/policy/v1beta1/podsecuritypolicies`。
    2. 筛选 `privileged: true` 的策略。
  - **敏感路径/高危词频**：
    - `podsecuritypolicies`, `allowPrivilegeEscalation`
  - **Python 高危函数**：
    - `client.CustomObjectsApi().list_cluster_custom_object(...)`

- **云凭证泄露扫描 (AK Leakage)**
  - **原理**：搜索代码或环境变量中的云厂商 AK/SK。
  - **前提条件**：文件读取权限或 Env 访问权限。
  - **攻击流程**：
    1. 遍历文件系统或 `os.environ`。
    2. 正则匹配 AK/SK 格式。
  - **敏感路径/高危词频**：
    - `AKIA...`, `AliyunAccessKey`
    - `~/.aws/credentials`
  - **Python 高危函数**：
    - `re.findall(r'AKIA[0-9A-Z]{16}', content)`

- **镜像仓库凭证爆破 (Registry Brute)**
  - **原理**：暴力破解 Registry 认证。
  - **前提条件**：网络可达 Registry。
  - **攻击流程**：
    1. 访问 `/v2/` 接口检测认证方式。
    2. 循环尝试用户名密码组合。
  - **敏感路径/高危词频**：
    - `/v2/_catalog`, `docker login`
  - **Python 高危函数**：
    - `requests.get('https://registry/v2/', auth=(user, pass))`

------

## 3. Python 反弹 Shell 与高危库调用 (Reverse Shell & Dangerous Calls)

*针对 Python 脚本特有的攻击模式检测。*

#### **3.1 反弹 Shell 特征**

- **原理**：攻击者通过 TCP 连接将 Shell 输入输出重定向到远端。
- **检测特征（代码模式）**：
  - **Socket 重定向**：
    - `s = socket.socket(...)` 配合 `os.dup2(s.fileno(), 0/1/2)`.
    - `subprocess.call(["/bin/sh", "-i"])`.
  - **One-Liner 模式**：
    - `import socket,subprocess,os;s=socket.socket...`
    - `pty.spawn("/bin/bash")`.
  - **高危词频**：
    - `os.dup2`, `subprocess.call`, `pty.spawn`, `/bin/bash -i`.

#### **3.2 高危系统调用 (Syscalls via Ctypes)**

- **原理**：使用 `ctypes` 库直接调用 libc 函数进行逃逸（如 `mount`, `setns`）。
- **检测特征**：
  - 加载 libc: `ctypes.CDLL("libc.so.6")`.
  - 调用敏感函数：`mount(...)`, `setns(...)`, `unshare(...)`.
  - **关键词**：`CDLL`, `libc.so.6`, `CLONE_NEWUSER`.

------

## 4. 资源耗尽型 DoS 攻击 (Resource Exhaustion)

*针对红方发动的 Fork Bomb 和 Inode 耗尽攻击。*

#### **4.1 进程/线程耗尽 (Fork Bomb)**

- **攻击意图**：创建大量进程耗尽 PID 资源，导致节点瘫痪。
- **检测特征（代码模式）**：
  - **无限循环与进程创建**：`while True` 配合 `os.fork()`, `threading.Thread()`, `multiprocessing.Process()`.
  - **高危词频**：
    - `os.fork` 在循环中。
    - `multiprocessing` 批量启动大量任务。

#### **4.2 磁盘/Inode 耗尽**

- **攻击意图**：填满磁盘空间或 Inode 表。
- **检测特征（代码模式）**：
  - **循环文件创建**：循环中执行 `open(..., 'w')` 创建大量小文件。
  - **大文件写入**：写入 `/dev/zero` 到文件，或循环写入数据块。
  - **高危词频**：
    - `while` 循环结合 `open`。
    - `write` 大量数据。
    - `/dev/shm` (写共享内存)。

------

### **总结：蓝方静态检测规则集示例 (Python伪代码)**

```python
# 蓝方静态分析规则示例 (Optimized for CDK Exploits)
import re

HIGH_RISK_PATTERNS = {
    # 侦察 (Recon)
    "Recon_Env": [r"os\.environ", r"platform\.uname", r"capsh", r"CapEff"],
    "Recon_Network": [r"socket\.connect", r"169\.254\.169\.254", r"X-Envoy-Peer-Metadata-Id", r"httpbin\.org"],
    "Recon_LocalBypass": [r"127\.0\.0\.1", r":10255"],
    
    # 逃逸 (Escape)
    "Escape_Kernel": [r"/proc/self/mem", r"madvise", r"splice", r"pkexec", r"uevent_helper"],
    "Escape_Privileged": [r"release_agent", r"/sys/fs/cgroup", r"mount\s+/dev", r"devices\.allow", r"nsenter"],
    "Escape_DockerSock": [r"/var/run/docker\.sock", r"docker\s+run", r"containers/create"],
    "Escape_DockerCP": [r"libnss_files\.so", r"libnss_dns\.so", r"__attribute__\(\(constructor\)\)"],
    "Escape_Runc": [r"#!/proc/self/exe", r"/proc/\d+/exe"],
    "Escape_Syscall": [r"ctypes\.CDLL", r"libc\.so\.6", r"setns", r"unshare"],
    
    # 持久化 (Persistence)
    "Persistence_K8s": [r"hostNetwork", r"hostPID", r"automountServiceAccountToken", r"externalIPs"],
    "Persistence_Webshell": [r"Runtime\.getRuntime", r"eval\("],
    "Persistence_RevShell": [r"os\.dup2", r"pty\.spawn", r"/bin/bash\s+-i"],
    
    # 凭证窃取 (Credential Theft)
    "Cred_K8s": [r"serviceaccount/token", r"\.kube/config", r"list\s+secrets"],
    "Cred_Cloud": [r"AKIA[0-9A-Z]{16}", r"SK[0-9a-zA-Z]{32}", r"-----BEGIN RSA PRIVATE KEY-----"],
    "Cred_RegistryBrute": [r"/v2/_catalog", r"docker\s+login"],
    
    # DoS
    "DoS_ForkBomb": [r"os\.fork", r"multiprocessing\.Process"],
}

def scan_code(user_code):
    alerts = []
    for risk_type, patterns in HIGH_RISK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, user_code, re.IGNORECASE):
                alerts.append(f"[ALERT] {risk_type} detected: {pattern}")
    return alerts
```

这份清单涵盖了从**信息收集**到**实施逃逸**，再到**持久化**和**破坏**的完整攻击链，并针对 Python 语言特性进行了优化。

------

## 5. 容器逃逸静态 Python 代码检测规则集 (Static Analysis Rules)

本章节基于上述分析，制定了标准化的静态检测规则集。该规则集可直接用于构建静态代码分析引擎。

### 5.1 规则格式说明
- **规则ID (Rule ID)**: `CE-{CATEGORY}-{ID}` (CE: Container Escape)
- **风险等级 (Severity)**: `CRITICAL` (严重), `HIGH` (高), `MEDIUM` (中), `LOW` (低)
- **检测对象**: Python 源代码
- **检测逻辑**: 正则表达式 (Regex) 或 AST 特征匹配

### 5.2 详细规则列表

#### 5.2.1 类别：系统命令执行 (Command Execution)

| 规则ID | 风险等级 | 规则名称 | 检测逻辑 (Regex/Pattern) | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **CE-CMD-01** | **HIGH** | 敏感系统命令调用 | `(os\.system\|subprocess\.(call\|run\|Popen)\|commands\.getoutput)\s*\(['"].*(nsenter\|capsh\|mount\|docker\|kubectl)` | 检测代码中直接调用容器逃逸相关的敏感二进制命令。 |
| **CE-CMD-02** | **HIGH** | 反弹 Shell 特征 | `(os\.dup2\s*\(\s*\w+\.fileno\(\)\s*,\s*[012]\s*\)\|pty\.spawn\s*\(['"]\/bin\/sh['"]\))` | 检测标准输入输出重定向或 PTY 生成 Shell 的行为。 |
| **CE-CMD-03** | **MEDIUM** | 危险的 Fork 操作 | `os\.fork\(\)` | 检测可能导致 Fork Bomb 的进程创建操作（需结合循环结构判定）。 |

#### 5.2.2 类别：文件与路径操作 (File Operations)

| 规则ID | 风险等级 | 规则名称 | 检测逻辑 (Regex/Pattern) | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **CE-FILE-01** | **CRITICAL** | 容器环境指纹探测 | `(\.dockerenv\|/proc/1/cgroup\|/proc/self/status)` | 检测尝试识别当前是否运行在容器环境中的行为。 |
| **CE-FILE-02** | **CRITICAL** | 宿主机敏感路径访问 | `(/host/\|/proc/1/\|/var/run/docker\.sock\|/var/run/secrets)` | 检测尝试访问宿主机挂载目录、Docker Socket 或 K8s 凭证的行为。 |
| **CE-FILE-03** | **HIGH** | 内核参数/Cgroup 修改 | `(/sys/fs/cgroup\|/proc/sys/kernel/core_pattern\|release_agent\|devices\.allow)` | 检测尝试修改 Cgroup 配置或内核转储路径以实现逃逸的行为。 |
| **CE-FILE-04** | **HIGH** | 自身可执行文件写入 | `(/proc/self/exe\|/proc/self/mem)` | 检测 runc 逃逸或 Dirty COW 攻击中写自身内存/文件的行为。 |

#### 5.2.3 类别：危险库调用 (Dangerous Libraries)

| 规则ID | 风险等级 | 规则名称 | 检测逻辑 (Regex/Pattern) | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **CE-LIB-01** | **CRITICAL** | Ctypes 加载 Libc | `ctypes\.CDLL\(['"]libc\.so\.6['"]\)` | 检测通过 ctypes 加载 C 库以绕过 Python 限制执行系统调用的行为。 |
| **CE-LIB-02** | **CRITICAL** | 敏感系统调用 (Syscall) | `(setns\|unshare\|mount\|ptrace\|madvise)` | 检测直接调用底层 Linux 系统调用，常见于高级逃逸攻击。 |
| **CE-LIB-03** | **HIGH** | Docker SDK 滥用 | `docker\.from_env\(\)` | 检测在容器内初始化 Docker 客户端，可能用于 Docker-in-Docker 逃逸。 |
| **CE-LIB-04** | **HIGH** | K8s Client 滥用 | `kubernetes\.client\.\w+Api\(\)` | 检测在容器内初始化 Kubernetes 客户端，可能用于集群资源操控。 |

#### 5.2.4 类别：网络行为检测 (Network Activity)

| 规则ID | 风险等级 | 规则名称 | 检测逻辑 (Regex/Pattern) | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| **CE-NET-01** | **HIGH** | 云元数据服务请求 | `(169\.254\.169\.254\|100\.100\.100\.200)` | 检测请求云厂商 Metadata 服务以获取 AK/SK 的行为。 |
| **CE-NET-02** | **HIGH** | K8s 组件端口扫描 | `(:10250\|:10255\|:2375\|:2379)` | 检测针对 Kubelet, Docker API, Etcd 等敏感端口的扫描或连接。 |
| **CE-NET-03** | **MEDIUM** | 本地回环网络探测 | `(127\.0\.0\.1)` | 检测尝试绕过 Kube-proxy 访问本地 localhost 服务的行为。 |

### 5.3 规则集成建议

1.  **静态扫描器集成**: 将上述 Regex 模式配置到 Semgrep 或简单的 Python 正则扫描脚本中。
2.  **CI/CD 阻断**: 在代码提交或构建阶段运行扫描，发现 CRITICAL/HIGH 级别规则命中即阻断流程。
3.  **误报处理**: 结合上下文（如是否为运维脚本）设置白名单，对于 `os.system` 等通用函数需结合参数特征（如 `nsenter`）进行精确匹配。

