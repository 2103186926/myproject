import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import time
import copy

# ==========================================
# 1. 基础设施定义 (模拟云平台环境)
# ==========================================

# 一个简单的海洋预测模型 (输入10个特征: 经度, 纬度, 深度, 时间... -> 输出1个值: 温度)
class SimpleOceanModel(nn.Module):
    def __init__(self):
        super(SimpleOceanModel, self).__init__()
        # 使用两层全连接网络，比单层更容易演示梯度及其非线性
        self.fc1 = nn.Linear(10, 20)
        self.fc2 = nn.Linear(20, 1)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# 联邦学习客户端基类
class FederalLearningClient:
    def __init__(self, client_id, local_data, local_label):
        self.client_id = client_id  # id
        self.local_data = local_data     # 真实数据
        self.local_label = local_label   # 真实标签
        self.model = SimpleOceanModel()

    def train(self, global_model_state_dict):
        """标准客户端的训练行为"""
        self.model.load_state_dict(global_model_state_dict)
        # ... 标准训练逻辑省略，恶意客户端会重写此方法 ...
        pass

# ==========================================
# 2. 恶意客户端代码 (梯度窃取核心)
# ==========================================

class MaliciousClient(FederalLearningClient):
    def __init__(self, client_id, local_data, local_label):
        super().__init__(client_id, local_data, local_label)  # 调用父类初始化

        self.attack_config = {
            'num_iterations': 30,      # 攻击迭代次数 (为了演示设为30，实际可能上千)
            'lr_reconstruction': 0.01,   # 攻击的学习率
            'target_gradient': None,    # 待窃取的目标梯度
            'dummy_label': None         # 虚拟标签
        }
        # 用于重构的虚拟数据
        self.dummy_data = None 

    def train(self, global_model_state_dict):
        """
        重写训练方法：
        1. 假装正常训练 (Camouflage)
        2. 执行梯度反演攻击 (Attack)
        """
        print(f"\n[Client {self.client_id}] >>> 收到全局模型，开始'本地训练'...")
        
        # --- 步骤 1: 正常本地训练 (伪装) ---
        # 目的：消耗正常的计算时间，产生正常的日志，掩盖攻击行为
        self.model.load_state_dict(global_model_state_dict)
        self.model.train()
        optimizer = torch.optim.SGD(self.model.parameters(), lr=0.01)
        criterion = nn.MSELoss()
        
        # 简单模拟一次前向反向传播
        optimizer.zero_grad()
        pred = self.model(self.local_data)
        loss = criterion(pred, self.local_label)
        loss.backward()
        optimizer.step()  # 攻击者在这里还做了一步模型参数更新，因为正常的训练是多轮迭代
        
        normal_grads = [p.grad.clone() for p in self.model.parameters()]
        print(f"[Client {self.client_id}] (伪装) 正常训练完成。Loss: {loss.item():.4f}")

        # --- 步骤 2: 梯度窃取攻击 (核心) ---
        if self.attack_config['target_gradient'] is not None:
            print(f"[Client {self.client_id}] [!!!] 发现目标梯度，启动梯度反演攻击...")
            start_time = time.time()
            
            # 执行攻击函数
            reconstructed_data = self._gradient_inversion_attack(
                self.attack_config['target_gradient'],   # 目标梯度
                global_model_state_dict  # 全局模型状态字典
            )
            
            duration = time.time() - start_time
            print(f"[Client {self.client_id}] 攻击结束。耗时: {duration:.2f}s")
            
            # 保存窃取结果
            self._save_reconstructed_data(reconstructed_data)
        
        # --- 步骤 3: 上传结果 ---
        # 攻击者通常会返回正常的权重更新，或者稍作修改的权重
        return self.model.state_dict()  # 返回一个包含模块完整状态引用的字典。

    def _gradient_inversion_attack(self, target_gradients, global_model_state_dict):
        """
        核心反演逻辑：通过优化 dummy_data 让其产生的梯度逼近 target_gradients
        """
        # 1. 初始化：生成随机噪声数据 (Dummy Data)
        # 它的形状必须和模型输入一致 (1, 10)
        # requires_grad=True 是关键！因为我们要对dummy_data求导并修改它
        input_dim = 10
        self.dummy_data = torch.randn(1, input_dim).requires_grad_(True)
        
        # 假设我们不知道标签，也初始化一个随机标签 (Dummy Label)
        # 在某些攻击中，标签也可以被恢复，这里简化为我们也优化标签
        dummy_label = torch.randn(1, 1).requires_grad_(True)
        
        # 2. 定义优化器
        # 注意：我们优化的对象是self.dummy_data，而不是模型参数！
        optimizer = torch.optim.LBFGS([self.dummy_data, dummy_label], lr=self.attack_config['lr_reconstruction'])  # L-BFGS算法？？？
        
        criterion = nn.MSELoss()
        
        print(f"    [Attack] 开始优化循环 (目标：让虚拟梯度 == 真实梯度)...")

        history = []  # 记录每轮迭代的损失值
        
        for iters in range(self.attack_config['num_iterations']):
            def closure():
                '''闭包（此处≠函数闭包）：需要多次计算虚拟梯度
                每次调用都会刷新self.dummy_data和dummy_label（这是LBFGS优化器的作用）
                '''
                optimizer.zero_grad()  # 清空的是self.dummy_data.grad
                
                # A. 前向传播：用现在的虚拟数据跑一遍模型
                dummy_pred = self.model(self.dummy_data)
                dummy_loss = criterion(dummy_pred, dummy_label)
                
                # B. 只计算虚拟梯度 (计算的是d(dummy_loss)/d(self.model.parameters()) = [d(dummy_loss)/d(w1), d(dummy_loss)/d(b1), ...])
                # create_graph=True 是必须的，因为我们需要对“模型梯度的损失差”再进行反向传播求梯度（二阶求导）
                dummy_gradients = torch.autograd.grad(
                    dummy_loss, 
                    self.model.parameters(), 
                    create_graph=True  # 允许对虚拟梯度进行二阶求导
                )
                
                # C. 计算“梯度距离损失” (Gradient Matching Loss)
                # 也就是：虚拟梯度 和 真实梯度 到底有多像？
                grad_diff = 0  # 初始化梯度差异损失
                for dg, tg in zip(dummy_gradients, target_gradients):
                    grad_diff += ((dg - tg) ** 2).sum()
                
                # D. 反向传播求梯度（更新self.dummy_data.grad）
                grad_diff.backward(retain_graph=True)  # 得到 d(梯度距离损失)/d(虚拟数据)，即self.dummy_data.grad
                return grad_diff  # 返回梯度差异损失
            
            # 更新self.dummy_data，朝着让虚拟梯度越来越接近目标梯度的方向更新
            loss_value = optimizer.step(closure)  # 每执行一次step，closure将会被调用多次？？？Why
            
            if iters % 1 == 0:
                current_loss = loss_value.item()
                history.append(current_loss)
                print(f"    Iteration {iters:3d} | Gradient Matching Loss: {current_loss:.8f}")
                
                if current_loss < 1e-8:
                    print("    [Attack] 梯度完全匹配！提前结束。")
                    break
                    
        return self.dummy_data.detach().numpy()  # detach()返回一个从当前图分离的新张量

    def _save_reconstructed_data(self, data):
        filename = f"stolen_data_{int(time.time())}.npy"
        np.save(filename, data)
        print(f"    [Result] 窃取的数据已保存至: {filename}")

# ==========================================
# 3. 模拟执行脚本 (运维检测视角)
# ==========================================
if __name__ == "__main__":
    # --- 场景准备 ---
    print("=== 模拟联邦学习场景：梯度窃取攻击 ===")
    
    # 1. 初始化全局模型
    global_model = SimpleOceanModel()
    global_state = global_model.state_dict()  # 返回一个包含模块完整状态引用的字典。
    
    # 2. [受害者]：一个拥有敏感数据的诚实客户端
    # 敏感数据：某特定海域的真实温度记录 (1行数据，10个特征)
    victim_true_data = torch.tensor([[0.5, -0.2, 0.9, 0.1, -0.5, 0.3, 0.7, -0.1, 0.0, 0.4]])
    victim_true_label = torch.tensor([[24.5]]) # 真实温度
    print(f"\n[Victim] 拥有敏感数据: {victim_true_data.numpy().flatten()}")
    
    # [受害者] 计算并上传梯度 (这是攻击者梦寐以求的 Target Gradient)
    victim_model = copy.deepcopy(global_model)  # 创建对象的完全独立副本
    criterion = nn.MSELoss()
    pred = victim_model(victim_true_data)
    loss = criterion(pred, victim_true_label)
    # 获取真实的梯度
    target_gradients = torch.autograd.grad(loss, victim_model.parameters(), create_graph=True)  # 返回一个元组，每个元素是对应参数的梯度
    # 这里的 target_gradients 就是攻击者通过抓包或共谋拿到的东西
    print("[Victim] 已计算并上传梯度 (Target Gradient)。")

    # 3. [攻击者]：初始化
    # 攻击者本地只有一些无意义的公开数据
    attacker_dummy_local_data = torch.randn(1, 10)  # 10个特征的随机数据
    attacker_dummy_local_label = torch.randn(1, 1)  # 随机标签
    
    malicious_client = MaliciousClient("malicious_01", attacker_dummy_local_data, attacker_dummy_local_label)
    
    # 4. [攻击者] 设置目标梯度 (Inject Target Gradient)
    malicious_client.attack_config['target_gradient'] = target_gradients
    
    # 5. [攻击者] 开始执行任务 (包含攻击)
    # 这里的 train 方法中，你会看到日志输出大量的 Iteration，这就是异常行为！
    malicious_client.train(global_state)

    # 6. 验证结果：对比窃取的数据和真实数据
    print("\n=== 攻击效果验证 ===")
    stolen_data = malicious_client.dummy_data.detach().numpy()
    print(f"真实敏感数据: {victim_true_data.numpy().flatten()}")
    print(f"窃取还原数据: {stolen_data.flatten()}")
    
    mse = ((victim_true_data.numpy() - stolen_data)**2).mean()
    print(f"还原误差 (MSE): {mse:.6f}")
    if mse < 0.01:
        print(">>> 警告：攻击非常成功！原始数据几乎被完整重构。")
    else:
        print(">>> 提示：攻击部分成功，还原了数据的大致分布。")