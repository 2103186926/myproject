# train_lstm_model.py
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping

# 设置 matplotlib 支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体显示中文
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

def train_lstm(data_filepath=r'../模拟日志特征提取/lstm_feature_data.json'):
    """
    加载LSTM序列特征数据，构建、训练并评估LSTM诊断模型。
    """
    # 1. 加载和准备数据
    try:
        with open(data_filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 特征文件 '{data_filepath}' 未找到。请确保文件存在。")
        return

    features = data.get('features', {})
    labels = data.get('labels', {})
    metadata = data.get('metadata', {})

    if not features or not labels:
        print("错误: JSON文件中缺少'features'或'labels'键。")
        return

    # 从元数据中获取维度信息
    seq_length = metadata.get('max_seq_length')
    num_features = metadata.get('num_features_per_step')

    # 将数据转换为NumPy数组，确保特征和标签一一对应
    task_ids = list(features.keys())
    X = np.array([features[tid] for tid in task_ids])
    y = np.array([labels[tid] for tid in task_ids])

    print(f"数据加载完成: {X.shape[0]}个样本, 序列长度={X.shape[1]}, 每个时间步有{X.shape[2]}个特征。")
    print("-" * 50)

    # 2. 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )
    print(f"数据集划分完成: {len(X_train)}个训练样本, {len(X_test)}个测试样本。")
    print("-" * 50)

    # 3. 特征缩放 (对神经网络至关重要)
    scaler = StandardScaler()
    # 将3D数据变形为2D以适应scaler
    X_train_reshaped = X_train.reshape(-1, num_features)
    scaler.fit(X_train_reshaped)
    
    # 分别对训练集和测试集进行缩放和变形
    X_train_scaled = scaler.transform(X_train_reshaped).reshape(X_train.shape)
    X_test_scaled = scaler.transform(X_test.reshape(-1, num_features)).reshape(X_test.shape)
    print("特征缩放完成。")
    print("-" * 50)

    # 4. 构建LSTM模型
    model = Sequential([
        Input(shape=(seq_length, num_features)),
        LSTM(64, return_sequences=False),
        Dropout(0.4),
        Dense(32, activation='relu'),
        Dropout(0.4),
        Dense(1, activation='sigmoid') # Sigmoid激活函数用于二元分类
    ])

    model.compile(optimizer='adam',
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    model.summary()
    print("-" * 50)

    # 5. 训练模型
    print("开始训练LSTM模型...")
    # 使用EarlyStopping回调函数防止过拟合，当验证集损失在5个轮次内不再改善时停止训练
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    
    history = model.fit(
        X_train_scaled, y_train,
        epochs=20,
        batch_size=16,
        validation_split=0.2, # 从训练集中分出20%作为验证集
        callbacks=[early_stopping],
        verbose=2
    )
    print("模型训练完成。")
    print("-" * 50)

    # 6. 评估模型
    print("--- 在测试集上进行最终评估 ---")
    loss, accuracy = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"测试集准确率 (Accuracy): {accuracy:.4f}")

    # 获取预测概率并转换为类别（阈值为0.5）
    y_pred_proba = model.predict(X_test_scaled)
    y_pred = (y_pred_proba > 0.5).astype("int32")

    print("\n分类报告 (Classification Report):")
    print(classification_report(y_test, y_pred, target_names=['正常任务 (0)', '恶意任务 (1)'], zero_division=0))

    print("\n混淆矩阵 (Confusion Matrix):")
    cm = confusion_matrix(y_test, y_pred)
    print(cm)

    # 可视化混淆矩阵
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['预测为正常', '预测为恶意'], 
                yticklabels=['实际为正常', '实际为恶意'])
    plt.title('LSTM 模型 - 混淆矩阵')
    plt.ylabel('实际标签')
    plt.xlabel('预测标签')
    plt.show()

if __name__ == '__main__':
    train_lstm()