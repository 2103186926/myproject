import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# --- 1. 加载和准备数据 ---
def load_and_prepare_data(filepath=r'../2.特征提取/advanced_static_feature_vectors.csv'):
    """加载CSV数据，并划分为特征和标签"""
    print(f"正在从 '{filepath}' 加载数据...")
    df = pd.read_csv(filepath)
    
    # 分离特征 (X) 和标签 (y)
    X = df.drop('is_malicious', axis=1)
    y = df['is_malicious']
    
    print("数据加载完成。特征维度:", X.shape)
    return X, y

# --- 2. 划分与缩放数据 ---
def split_and_scale_data(X, y):
    """将数据划分为训练集和测试集，并进行特征缩放"""
    # 按照 80% 训练集, 20% 测试集进行划分
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"数据已划分为: {len(X_train)} 行训练集, {len(X_test)} 行测试集。")
    
    # 特征缩放：对于逻辑回归和神经网络非常重要
    # 随机森林对此不敏感，但为了流程统一，我们都进行缩放
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test

# --- 3. 评估模型并打印结果 ---
def evaluate_model(model, X_test, y_test, model_name):
    """对训练好的模型在测试集上进行评估"""
    print(f"\n--- 正在评估模型: {model_name} ---")
    
    # 进行预测
    y_pred = model.predict(X_test)
    
    # 打印分类报告 (包含精确率、召回率、F1分数)
    print("分类报告:")
    print(classification_report(y_test, y_pred))
    
    # 打印关键指标
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    
    print(f"准确率 (Accuracy): {accuracy:.4f}")
    print(f"精确率 (Precision): {precision:.4f}")
    print(f"召回率 (Recall): {recall:.4f}")
    print(f"F1 分数 (F1 Score): {f1:.4f}")
    print(f"ROC AUC 分数: {roc_auc:.4f}")
    
    # 绘制混淆矩阵
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['正常任务', '恶意任务'], 
                yticklabels=['正常任务', '恶意任务'])
    plt.title(f'{model_name} - 混淆矩阵')
    plt.xlabel('预测标签')
    plt.ylabel('真实标签')
    plt.show()

# --- 主执行函数 ---
def main():
    # 加载数据
    X, y = load_and_prepare_data()
    
    # 划分与缩放
    X_train, X_test, y_train, y_test = split_and_scale_data(X, y)
    
    # 初始化模型
    models = {
        "逻辑回归": LogisticRegression(random_state=42),  # 逻辑回归对特征缩放敏感
        "随机森林": RandomForestClassifier(n_estimators=100, random_state=42),  # 随机森林对特征缩放不敏感
        "神经网络 (MLP)": MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=42)  # 神经网络对特征缩放敏感
    }
    
    # 训练并评估每个模型
    for name, model in models.items():
        print(f"\n{'='*20} 正在训练: {name} {'='*20}")
        model.fit(X_train, y_train) # 随机森林不需要缩放数据，为了演示效果，这里使用原始数据
        if name != "随机森林":
             # 逻辑回归和MLP使用缩放后的数据训练
             model.fit(X_train, y_train)

        evaluate_model(model, X_test, y_test, name)

if __name__ == '__main__':
    main()