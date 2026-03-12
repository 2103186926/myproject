# malicious_membership_inference.py
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from platform_sdk.model_client import PredictiveModelClient

def generate_shadow_data(sensitive_sample, num_shadow_samples=150, perturbation_factor=0.05):
    """
    生成影子数据：通过给敏感样本添加噪声，创建一批非成员样本
    
    参数:
    sensitive_sample: 敏感样本（例如，一个特征向量）
    num_shadow_samples: 要生成的影子样本数量（默认150）
    perturbation_factor: 用于添加噪声的因子（默认0.05）
    
    返回:
    shadow_data: 生成的影子数据数组（形状为 (num_shadow_samples, 特征维度)）
    """
    shadow_data = []
    for _ in range(num_shadow_samples):
        # 添加随机噪声来创建影子样本
        noise = np.random.normal(0, perturbation_factor, sensitive_sample.shape)
        shadow_sample = sensitive_sample + noise
        # 确保数据在有效范围内（例如，地形特征值非负）
        shadow_sample = np.clip(shadow_sample, 0, None)  # clip：裁剪到非负范围
        shadow_data.append(shadow_sample)
    return np.array(shadow_data)

def query_model_prediction(features):
    """查询目标模型并获取预测置信度"""
    client = PredictiveModelClient(model_name="seabed_terrain_classifier")  # 海底地形分类模型
    try:
        # 假设模型返回一个包含各类别概率的字典或数组
        prediction_probs = client.predict(features)
        # 获取最高预测概率（置信度）
        confidence = np.max(prediction_probs)  # 返回最大值
        # 获取预测的类别
        predicted_class = np.argmax(prediction_probs)  # 返回最大值的索引
        return confidence, predicted_class, prediction_probs
    except Exception as e:
        print(f"Error querying model: {e}")
        return None, None, None

def main():
    # --- 阶段 1: 准备数据 ---
    # 假设这是攻击者拥有的敏感数据样本（例如，一个特征向量）
    # 例如，[侧扫声纳强度, 水深, 坡度, 粗糙度, ...]
    X_sensitive = np.array([0.85, 2450.0, 12.7, 0.23, ...]) 

    print(f"[+] Target sensitive sample shape: {X_sensitive.shape}")
    print(f"[+] Generating shadow data...")

    # 生成影子数据（非成员数据）
    X_shadow = generate_shadow_data(X_sensitive, num_shadow_samples=150)
    # 将敏感数据和非成员数据合并
    X_candidate = np.vstack([X_sensitive.reshape(1, -1), X_shadow])   # 数组的拼接操作
    # 创建标签：1 代表成员（敏感数据），0 代表非成员（影子数据）
    y_candidate = np.array([1] + [0] * len(X_shadow)) 

    # --- 阶段 2: 查询目标模型，获取“行为特征” ---
    print(f"[+] Querying the target model for predictions...")
    attack_features = [] # 用于训练攻击模型的特征
    attack_labels = []   # 对应的标签（1=成员，0=非成员）

    for i, x in enumerate(X_candidate):
        confidence, pred_class, full_probs = query_model_prediction(x)
        if confidence is not None:
            # 关键步骤：将模型的响应作为攻击模型的特征
            # 特征可以包括：置信度、预测类别、熵、以及原始特征等
            feature_vector = [
                confidence,           # 最高类别概率
                pred_class,           # 预测的类别
                # np.argmax(full_probs), # 或者直接使用概率向量
                # np.std(full_probs),    # 概率分布的标准差
                # 可以加入原始特征的一部分来提供上下文
                # x[0], x[2] 
            ]
            attack_features.append(feature_vector)
            attack_labels.append(y_candidate[i])
        # 添加延迟，避免被速率限制检测到
        time.sleep(0.2) 

    attack_features = np.array(attack_features)
    attack_labels = np.array(attack_labels)

    print(f"[+] Collected {len(attack_features)} model responses.")

    # --- 阶段 3: 训练攻击模型 ---
    print(f"[+] Training the membership inference attack model...")
    # 使用一个简单的分类器，如随机森林
    attack_model = RandomForestClassifier(n_estimators=50, random_state=42)  # 树的数量50, 随机种子42 分类器
    attack_model.fit(attack_features, attack_labels)  # 训练攻击模型

    # --- 阶段 4: 进行推断 ---
    # 现在，用训练好的攻击模型来判断敏感样本是否被认为是成员
    sensitive_feature = attack_features[0] # 第一个就是我们关心的敏感样本的特征
    # 或者重新查询一次以获取最新数据
    confidence_sensitive, _, _ = query_model_prediction(X_sensitive)
    sensitive_feature_recent = [confidence_sensitive, ...] # 构建与攻击模型训练时相同的特征向量

    membership_score = attack_model.predict_proba([sensitive_feature_recent])[0][1] # 属于类别1（成员）的概率
    is_member = membership_score > 0.5 # 根据阈值判断

    print("="*50)
    print(" Membership Inference Attack Result ")
    print("="*50)
    print(f" Target Sample: {X_sensitive[:4]}...") # 打印前几个特征值
    print(f" Model Confidence on Target: {confidence_sensitive:.4f}")
    print(f" Attack Model Membership Score: {membership_score:.4f}")
    print(f" Conclusion: The sample is {'LIKELY' if is_member else 'UNLIKELY'} a member of the training set.")
    print("="*50)

    # 记录结果
    with open("membership_inference_result.log", "w") as f:
        f.write(f"Membership Score: {membership_score}\n")
        f.write(f"Is Member: {is_member}\n")
        f.write(f"Sample Features (first 5): {X_sensitive[:5]}\n")

if __name__ == "__main__":
    main()