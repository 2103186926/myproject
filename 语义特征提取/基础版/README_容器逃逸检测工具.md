# Python容器逃逸静态检测 - 语义特征提取工具

## 项目简介

这是一个专门用于检测Python代码中容器逃逸行为的静态分析工具。基于《Python容器逃逸静态检测规则手册》，该工具能够从Python代码的AST（抽象语法树）中提取128维的语义特征向量，并自动评估容器逃逸风险等级。

## 核心功能

### 🔍 静态代码分析
- 无需执行代码，纯静态分析
- 基于AST深度遍历和模式匹配
- 支持大规模批量扫描

### 🎯 容器逃逸检测
- 覆盖完整攻击链：侦察 → 逃逸 → 持久化 → 破坏
- 检测30+种容器逃逸攻击模式
- 识别内核漏洞利用（Dirty COW, Dirty Pipe等）
- 检测运行时漏洞（runc, containerd-shim等）
- 发现配置缺陷（Docker Socket, Cgroup等）

### 📊 特征向量提取
- 128维语义特征向量
- 三个维度：函数调用、攻击模式、路径访问
- 适用于机器学习模型训练

### ⚠️ 风险评估
- 自动计算风险分数
- 五级风险等级：CRITICAL / HIGH / MEDIUM / LOW / SAFE
- 生成详细的JSON格式报告

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Python源代码                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   AST解析器                              │
│              (抽象语法树生成)                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          ContainerEscapeFeatureExtractor                 │
│              (容器逃逸特征提取器)                         │
├─────────────────────────────────────────────────────────┤
│  1. 敏感函数频次特征提取 (32维)                          │
│     - system_commands                                    │
│     - process_control                                    │
│     - dangerous_libs                                     │
│     - network_recon                                      │
│     - file_access                                        │
│     - kernel_syscalls                                    │
│     - container_runtime                                  │
│     - k8s_operations                                     │
│                                                          │
│  2. 攻击模式序列特征提取 (64维)                          │
│     - cmd_execution                                      │
│     - file_fingerprint / file_escape                     │
│     - lib_dangerous / lib_container                      │
│     - net_recon                                          │
│     - exploit_kernel / exploit_runtime                   │
│     - k8s_privilege / k8s_persistence                    │
│     - cred_theft                                         │
│     - dos_attack                                         │
│                                                          │
│  3. 路径配置特征提取 (32维)                              │
│     - container_runtime_paths                            │
│     - proc_sensitive_paths                               │
│     - cgroup_paths                                       │
│     - k8s_secret_paths                                   │
│     - host_mount_paths                                   │
│     - kernel_config_paths                                │
│     - container_fingerprint_paths                        │
│     - credential_paths                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              特征向量 (128维 .npy)                       │
│                      +                                   │
│          风险评估报告 (.json)                            │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 安装依赖

```bash
pip install numpy scikit-learn
```

### 基本使用

```bash
# 1. 将Python代码转换为AST JSON（需要自行实现或使用现有工具）
python convert_to_ast.py your_code.py your_code.ast.json

# 2. 运行特征提取和风险检测
python semantic_feature_extractor.py your_code.ast.json -r your_code.py

# 3. 查看结果
# - your_code_container_escape_features.npy (特征向量)
# - your_code_container_escape_features_risk_report.json (风险报告)
```

### 命令行参数

```
usage: semantic_feature_extractor.py [-h] [-c CFG] [-r HIGH_RISK] 
                                      [-o OUTPUT] [--no-report]
                                      ast_json_file

参数说明:
  ast_json_file         AST JSON文件路径 (必需)
  -c, --cfg            CFG元数据文件路径 (可选)
  -r, --high_risk      高危测试文件路径 (可选，用于增强检测)
  -o, --output         输出文件路径 (可选)
  --no-report          不生成风险评估报告
```

## 检测规则

### 规则分类

工具实现了《Python容器逃逸静态检测规则手册》5.2节定义的所有规则：

#### CE-CMD: 系统命令执行
- **CE-CMD-01** [HIGH]: 敏感系统命令调用 (nsenter, mount, docker, kubectl)
- **CE-CMD-02** [HIGH]: 反弹Shell特征 (os.dup2, pty.spawn)
- **CE-CMD-03** [MEDIUM]: 危险的Fork操作

#### CE-FILE: 文件与路径操作
- **CE-FILE-01** [CRITICAL]: 容器环境指纹探测 (/.dockerenv, /proc/1/cgroup)
- **CE-FILE-02** [CRITICAL]: 宿主机敏感路径访问 (/var/run/docker.sock, /host/)
- **CE-FILE-03** [HIGH]: 内核参数/Cgroup修改 (release_agent, devices.allow)
- **CE-FILE-04** [HIGH]: 自身可执行文件写入 (/proc/self/exe, /proc/self/mem)

#### CE-LIB: 危险库调用
- **CE-LIB-01** [CRITICAL]: Ctypes加载Libc (ctypes.CDLL('libc.so.6'))
- **CE-LIB-02** [CRITICAL]: 敏感系统调用 (setns, unshare, mount, ptrace)
- **CE-LIB-03** [HIGH]: Docker SDK滥用 (docker.from_env())
- **CE-LIB-04** [HIGH]: K8s Client滥用 (kubernetes.client)

#### CE-NET: 网络行为检测
- **CE-NET-01** [HIGH]: 云元数据服务请求 (169.254.169.254)
- **CE-NET-02** [HIGH]: K8s组件端口扫描 (:10250, :2375, :2379)
- **CE-NET-03** [MEDIUM]: 本地回环网络探测 (127.0.0.1)

### 漏洞覆盖

- ✅ **Dirty COW** (CVE-2016-5195): madvise竞态条件
- ✅ **Dirty Pipe** (CVE-2022-0847): 管道缓冲区漏洞
- ✅ **Polkit提权** (CVE-2021-4034): pkexec环境变量注入
- ✅ **runc逃逸** (CVE-2019-5736): 覆盖宿主机runc
- ✅ **containerd-shim** (CVE-2020-15257): Unix Socket劫持
- ✅ **docker cp** (CVE-2019-14271): NSS库替换
- ✅ **Cgroup Release Agent**: 容器逃逸经典方法
- ✅ **Docker Socket滥用**: Docker-in-Docker攻击
- ✅ **Hotplug劫持**: 内核热插拔机制利用

## 输出示例

### 控制台输出

```
============================================================
容器逃逸静态检测 - 语义特征提取工具
============================================================

[1/3] 检测容器逃逸风险...
检测到容器逃逸模式 'file_host_sensitive': 2个匹配
检测到容器逃逸模式 'cmd_sensitive_binary': 1个匹配
检测到容器逃逸模式 'lib_ctypes_libc': 1个匹配
⚠️  容器逃逸风险等级: CRITICAL
   风险摘要: 发现 2 个严重风险, 发现 3 个高风险

[2/3] 检测代码混淆...

[3/3] 提取语义特征向量...
容器逃逸语义特征向量已保存至: sample_container_escape_features.npy
容器逃逸风险评估报告已保存至: sample_risk_report.json
风险等级: CRITICAL, 风险分数: 25.0

============================================================
处理完成！
============================================================
```

### 风险报告 (JSON)

```json
{
  "risk_level": "CRITICAL",
  "risk_score": 25.0,
  "indicators": {
    "CRITICAL": [
      {
        "rule_id": "CE-FILE-02",
        "pattern": "file_host_sensitive",
        "matches": 2,
        "samples": ["/var/run/docker.sock", "/host/"]
      },
      {
        "rule_id": "CE-LIB-01",
        "pattern": "lib_ctypes_libc",
        "matches": 1,
        "samples": ["ctypes.CDLL('libc.so.6')"]
      }
    ],
    "HIGH": [
      {
        "rule_id": "CE-CMD-01",
        "pattern": "cmd_sensitive_binary",
        "matches": 1,
        "samples": ["nsenter"]
      }
    ]
  },
  "summary": "发现 2 个严重风险, 发现 3 个高风险",
  "total_patterns": 6
}
```

## 应用场景

### 1. CI/CD安全门禁

```yaml
# .gitlab-ci.yml
security_scan:
  stage: test
  script:
    - python semantic_feature_extractor.py code.ast.json -r code.py
    - python check_risk.py code_risk_report.json
  only:
    - merge_requests
```

### 2. 云平台代码审查

适用于海洋科学云平台等容器化环境，自动审查用户提交的Jupyter Notebook或Python脚本。

### 3. 机器学习模型训练

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# 加载特征向量
X_train = [np.load(f) for f in training_files]
y_train = [label for label in labels]

# 训练分类器
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# 预测新样本
new_features = np.load('new_sample.npy')
is_escape = clf.predict([new_features])[0]
```

### 4. 威胁情报分析

分析已知的容器逃逸攻击样本，提取特征用于威胁检测和溯源。

## 项目文件

```
.
├── semantic_feature_extractor.py          # 主程序
├── 容器逃逸特征提取工具使用说明.md        # 详细文档
├── 快速开始指南.md                        # 快速上手
├── Python容器逃逸静态检测规则.md          # 检测规则手册
├── 测试示例_容器逃逸代码.py               # 测试样本
├── 修改总结.md                            # 修改说明
└── README_容器逃逸检测工具.md             # 本文档
```

## 技术特点

- ✅ **规则驱动**: 基于标准化的检测规则手册
- ✅ **全攻击链**: 覆盖侦察、逃逸、持久化、破坏全阶段
- ✅ **多维特征**: 函数、模式、路径三维度特征提取
- ✅ **风险量化**: 自动计算风险分数并分级
- ✅ **可扩展**: 易于添加新规则和模式
- ✅ **高性能**: 纯静态分析，无需代码执行
- ✅ **易集成**: 标准化输入输出，易于集成到现有系统

## 局限性

1. **静态分析局限**: 无法检测运行时动态生成的恶意代码
2. **误报可能**: 基于模式匹配，可能对正常代码产生误报
3. **语言限制**: 目前仅支持Python语言
4. **混淆对抗**: 高度混淆的代码可能降低检测准确率

## 最佳实践

1. **结合源代码**: 使用 `-r` 参数提供源代码文件以提高检测准确率
2. **人工复核**: 对MEDIUM及以上风险的代码进行人工审查
3. **白名单机制**: 为已知安全的代码模式建立白名单
4. **持续更新**: 定期更新检测规则以覆盖最新漏洞
5. **多层防御**: 结合动态分析、沙箱等其他安全措施

## 后续规划

- [ ] 支持更多编程语言（Go, Java, Node.js）
- [ ] 集成动态分析能力
- [ ] 开发Web可视化界面
- [ ] 支持Jupyter Notebook格式
- [ ] 与SIEM系统集成
- [ ] 添加更多最新CVE检测规则
- [ ] 支持自定义规则配置

## 参考资料

- [Python容器逃逸静态检测规则手册](Python容器逃逸静态检测规则.md)
- [CDK - Container Development Kit](https://github.com/cdk-team/CDK)
- [MITRE ATT&CK for Containers](https://attack.mitre.org/matrices/enterprise/containers/)
- [容器安全最佳实践](https://kubernetes.io/docs/concepts/security/)

## 许可证

请参考项目根目录的LICENSE文件。

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**⚠️ 安全提示**: 本工具仅用于合法的安全测试和研究目的。请勿用于非法活动。
