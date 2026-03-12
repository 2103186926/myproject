import pandas as pd
import numpy as np

# --- 1. 参数定义 ---
NUM_SAMPLES_TOTAL = 200
# 我们故意创建一个不平衡的数据集，这更接近现实
# 100个正常 + 50个模糊良性 = 150个良性 (Label 0)
# 50个高隐蔽性恶意 = 50个恶意 (Label 1)
SAMPLES_CONFIG = {
    'normal_benign': 100,
    'ambiguous_benign': 50,
    'concealed_malicious': 50
}
OUTPUT_FILENAME = 'advanced_static_feature_vectors.csv'

# --- 2. 模拟三类“用户画像”的特征分布 ---
# (均值mean, 标准差std)

# 画像0: 正常科研用户 (Benign - Normal)
# 特征: 相似度低, 方差小, 速率低, 输出比正常 (不高不低)
params_normal = {
    'avg_cosine_similarity': {'mean': 0.3, 'std': 0.15},
    'confidence_variance': {'mean': 0.005, 'std': 0.002},
    'query_rate_per_sec': {'mean': 0.2, 'std': 0.1},
    'output_to_query_ratio': {'mean': 1.0, 'std': 0.3} # e.g., 150MB output / 150 queries
}

# 画像1: 行为模糊的良性用户 (Benign - Ambiguous)
# 场景: 研究员做"敏感性分析"
# 特征: 相似度高(像攻击), 方差小(不像攻击), 速率高(像攻击), 输出比正常(不像攻击)
params_ambiguous = {
    'avg_cosine_similarity': {'mean': 0.99, 'std': 0.005}, # 像攻击
    'confidence_variance': {'mean': 0.002, 'std': 0.001}, # 不像攻击
    'query_rate_per_sec': {'mean': 1.5, 'std': 0.3},      # 像攻击
    'output_to_query_ratio': {'mean': 0.8, 'std': 0.2}   # 不像攻击
}

# 画像2: 高隐蔽性的恶意攻击者 (Malicious - Concealed)
# 场景: "聪明的"攻击者, 故意放慢速率
# 特征: 相似度高(攻击特征), 方差高(攻击特征), 速率低(伪装), 输出比极低(攻击特征)
params_malicious = {
    'avg_cosine_similarity': {'mean': 0.998, 'std': 0.001}, # 攻击特征
    'confidence_variance': {'mean': 0.025, 'std': 0.005}, # 攻击特征
    'query_rate_per_sec': {'mean': 0.3, 'std': 0.1},      # 伪装 (看起来像正常用户)
    'output_to_query_ratio': {'mean': 0.01, 'std': 0.005} # 攻击特征 (e.g., 1KB output / 150 queries)
}


def generate_data(num_samples, params):
    """根据指定的参数生成模拟数据"""
    data = {}
    
    # 1. avg_cosine_similarity
    sim = np.random.normal(loc=params['avg_cosine_similarity']['mean'],
                           scale=params['avg_cosine_similarity']['std'],
                           size=num_samples)
    data['avg_cosine_similarity'] = np.clip(sim, 0, 1)

    # 2. confidence_variance
    var = np.random.normal(loc=params['confidence_variance']['mean'],
                           scale=params['confidence_variance']['std'],
                           size=num_samples)
    data['confidence_variance'] = np.clip(var, 0, None)

    # 3. query_rate_per_sec
    rate = np.random.normal(loc=params['query_rate_per_sec']['mean'],
                            scale=params['query_rate_per_sec']['std'],
                            size=num_samples)
    data['query_rate_per_sec'] = np.clip(rate, 0, None)

    # 4. output_to_query_ratio (新特征, 替换了 is_parasitic_training_detected)
    ratio = np.random.normal(loc=params['output_to_query_ratio']['mean'],
                             scale=params['output_to_query_ratio']['std'],
                             size=num_samples)
    data['output_to_query_ratio'] = np.clip(ratio, 0, None)

    return pd.DataFrame(data)

def main():
    """主函数，生成并保存数据"""
    print("开始生成高级静态聚合特征向量...")

    # 生成 画像0: 正常
    df_normal = generate_data(SAMPLES_CONFIG['normal_benign'], params_normal)
    df_normal['is_malicious'] = 0
    print(f"已生成 {SAMPLES_CONFIG['normal_benign']} 行 [正常] 样本。")

    # 生成 画像1: 模糊 (良性)
    df_ambiguous = generate_data(SAMPLES_CONFIG['ambiguous_benign'], params_ambiguous)
    df_ambiguous['is_malicious'] = 0
    print(f"已生成 {SAMPLES_CONFIG['ambiguous_benign']} 行 [模糊-良性] 样本。")

    # 生成 画像2: 隐蔽 (恶意)
    df_malicious = generate_data(SAMPLES_CONFIG['concealed_malicious'], params_malicious)
    df_malicious['is_malicious'] = 1
    print(f"已生成 {SAMPLES_CONFIG['concealed_malicious']} 行 [隐蔽-恶意] 样本。")

    # 合并所有数据
    df_final = pd.concat([df_normal, df_ambiguous, df_malicious], ignore_index=True)

    # 随机打乱数据顺序
    df_final = df_final.sample(frac=1).reset_index(drop=True)

    # 保存到CSV文件
    df_final.to_csv(OUTPUT_FILENAME, index=False)
    
    print("-" * 30)
    print(f"成功生成CSV文件: {OUTPUT_FILENAME}")
    print(f"总行数: {len(df_final)}")
    print(f"标签分布 (0=良性, 1=恶意):\n{df_final['is_malicious'].value_counts()}")
    print("-" * 30)
    print("文件内容预览 (随机样本):")
    print(df_final.head())
    print("-" * 30)


if __name__ == '__main__':
    main()