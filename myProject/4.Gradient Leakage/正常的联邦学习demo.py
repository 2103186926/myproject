import torch
import torch.nn as nn
import torch.optim as optim
import copy
import numpy as np
import time

# ==========================================
# 1. 基础组件定义
# ==========================================

# 简单的神经网络：预测海洋温度
class SimpleOceanModel(nn.Module):
    def __init__(self):
        super(SimpleOceanModel, self).__init__()
        # 输入：10个海洋特征（如经纬度、深度、盐度、叶绿素等）
        # 输出：1个预测值（温度）
        self.fc1 = nn.Linear(10, 20)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(20, 1)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out

# 模拟数据集生成器
def generate_ocean_data(num_samples):
    # X: 随机特征, Y: 简单的线性关系 + 噪声
    X = torch.randn(num_samples, 10)
    # 假设真实规律是：温度 = 特征1 * 2 + 特征2 - 1.5
    true_weights = torch.randn(10, 1) 
    Y = torch.matmul(X, true_weights) + 0.1 * torch.randn(num_samples, 1)
    return X, Y

# ==========================================
# 2. 诚实客户端 (Honest Client)
# ==========================================

class NormalClient:
    def __init__(self, client_id, dataset, epochs=5, lr=0.01):
        self.client_id = client_id  # 客户端ID
        self.local_data, self.local_labels = dataset  # 本地数据集
        self.epochs = epochs  # 本地训练轮数
        self.lr = lr  # 学习率
        self.model = SimpleOceanModel()  # 正常情况的话，该模型是从服务器下载的全局模型
        self.criterion = nn.MSELoss()  # 损失函数：均方误差损失

    def train(self, global_model_state_dict):
        """
        标准训练流程：
        1. 加载全局模型
        2. 使用本地数据进行几轮迭代 (Epochs)
        3. 返回更新后的模型权重
        """
        # 记录开始时间（用于运维监控对比）
        start_time = time.time()
        
        # 加载服务器发来的“最新参数”
        self.model.load_state_dict(global_model_state_dict)
        self.model.train() # 开启训练模式
        
        optimizer = optim.SGD(self.model.parameters(), lr=self.lr)

        # === 核心差异点：这里优化的是模型参数 (Parameters)，而不是输入数据 ===
        for epoch in range(self.epochs):
            # A. 前向传播
            optimizer.zero_grad()
            outputs = self.model(self.local_data)  # X:[50,10]  Y:[50,1]
            loss = self.criterion(outputs, self.local_labels)
            
            # B. 反向传播 (计算梯度) 
            loss.backward()  # model.parameters().grad （同optimizer.param_groups中的params.grad]）
            
            # C. 更新参数 
            optimizer.step()  # model.parameters()（同optimizer.param_groups中的params）
        
        train_time = time.time() - start_time
        
        # 计算 Loss 变化（仅用于日志展示）
        print(f"[Client {self.client_id}] 正常训练完成 | 耗时: {train_time:.4f}s | 最终 Loss: {loss.item():.4f}")

        # 计算目标模型的梯度
        # target_gradients = torch.autograd.grad(loss, self.model.parameters())  # 返回一个元组，每个元素是对应参数的梯度
        
        # 返回训练好的模型参数 (即上传更新)
        return self.model.state_dict()

# ==========================================
# 3. 中央服务器 (Server)
# ==========================================

class CentralServer:
    def __init__(self, num_clients):
        self.global_model = SimpleOceanModel()  # 全局模型
        self.num_clients = num_clients  # 客户端数量
        print("[Server] 初始化全局模型...")

    def aggregate(self, client_weights):
        """
        FedAvg 算法：将收到的所有客户端权重进行平均
        """
        print(f"[Server] 收到 {len(client_weights)} 个客户端的更新，开始聚合 (FedAvg)...")
        
        # 初始化聚合权重字典
        avg_weights = copy.deepcopy(client_weights[0])
        
        # 遍历模型的每一层参数 (key: layer_name)
        for key in avg_weights.keys():
            for i in range(1, len(client_weights)):
                # 将其他客户端的权重加起来
                avg_weights[key] += client_weights[i][key]
            # 除以客户端数量，求平均
            avg_weights[key] = torch.div(avg_weights[key], len(client_weights))
        
        # 更新全局模型
        self.global_model.load_state_dict(avg_weights)
        print("[Server] 全局模型已更新。\n" + "-"*50)

# ==========================================
# 4. 模拟联邦学习全流程 (Main Loop)
# ==========================================

if __name__ == "__main__":
    # --- 配置 ---
    NUM_CLIENTS = 3
    ROUNDS = 3  # 联邦学习进行的轮数 (Round)

    # 1. 初始化服务器
    server = CentralServer(NUM_CLIENTS)

    # 2. 初始化客户端 (模拟分发给不同的科考船/浮标)
    clients = []
    for i in range(NUM_CLIENTS):
        # 每个客户端拥有自己独特的本地数据 (私有数据)
        local_dataset = generate_ocean_data(num_samples=50) 
        clients.append(NormalClient(client_id=f"Ship_{i+1}", dataset=local_dataset))

    # 3. 开始联邦学习循环
    for round_idx in range(ROUNDS):
        print(f"\n=== Round {round_idx + 1} / {ROUNDS} ===")
        
        # 获取当前全局模型参数
        global_weights = server.global_model.state_dict()
        
        client_updates = []  # 存储所有客户端的更新权重
        
        # --- 客户端并行训练阶段 ---
        for client in clients:
            # 客户端下载模型 -> 本地训练 -> 上传新权重
            # 注意：在真实系统中，这里是并行发生的
            updated_weights = client.train(global_weights)
            client_updates.append(updated_weights)
        
        # --- 服务器聚合阶段 ---
        # 服务器收集所有更新 -> 算出新模型
        server.aggregate(client_updates)

    print("\n[Finished] 联邦学习任务正常结束。")