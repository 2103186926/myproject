# train_models.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# 导入模型
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

def train_and_evaluate_models(csv_filepath=r'../2.特征提取/feature_vectors.csv'):
    """
    加载特征向量CSV文件，训练并评估多个分类模型。
    """
    # 1. 加载和准备数据
    try:
        data = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"错误: CSV文件 '{csv_filepath}' 未找到。请确保文件存在于正确的位置。")
        return

    print("数据加载成功，前5行预览:")
    print(data.head())
    print("-" * 50)

    # 划分特征 (X) 和标签 (y)
    # taskId 是标识符，不作为训练特征
    X = data.drop(['taskId', 'is_malicious'], axis=1)
    y = data['is_malicious']

    # 划分训练集和测试集 (80% 训练, 20% 测试)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"数据集划分完成: {len(X_train)}个训练样本, {len(X_test)}个测试样本。")
    print("-" * 50)

    # 2. 特征缩放
    # 对于逻辑回归和神经网络等模型，特征缩放至关重要
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 3. 初始化模型
    models = {
        "逻辑回归 (Logistic Regression)": LogisticRegression(random_state=42),
        "随机森林 (Random Forest)": RandomForestClassifier(random_state=42),
        "XGBoost": XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')
    }

    # 4. 循环训练和评估每个模型
    for name, model in models.items():
        print(f"--- 开始训练模型: {name} ---")
        
        # 训练模型
        model.fit(X_train_scaled, y_train)
        
        # 在测试集上进行预测
        y_pred = model.predict(X_test_scaled)
        
        # 评估结果
        print("\n[评估结果]")
        accuracy = accuracy_score(y_test, y_pred)
        print(f"准确率 (Accuracy): {accuracy:.4f}")
        
        # 打印详细的分类报告 (精确率, 召回率, F1分数)
        print("\n分类报告 (Classification Report):")
        print(classification_report(y_test, y_pred, target_names=['正常任务 (0)', '恶意任务 (1)']))
        
        # 打印混淆矩阵
        print("混淆矩阵 (Confusion Matrix):")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        # 可视化混淆矩阵
        plt.figure(figsize=(6, 4))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=['预测为正常', '预测为恶意'], 
                    yticklabels=['实际为正常', '实际为恶意'])
        plt.title(f'{name} - 混淆矩阵')
        plt.ylabel('实际标签')
        plt.xlabel('预测标签')
        plt.show()

        # 特别针对随机森林，显示特征重要性
        if name == "随机森林 (Random Forest)":
            print("\n[随机森林] 特征重要性:")
            importances = pd.DataFrame({
                'Feature': X.columns,
                'Importance': model.feature_importances_
            }).sort_values('Importance', ascending=False)
            print(importances)
            print("\n")

if __name__ == '__main__':
    train_and_evaluate_models()