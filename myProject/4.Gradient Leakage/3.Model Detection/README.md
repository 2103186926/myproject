## train_lstm_model.py  -- LSTM模型基础版
    1.数据预处理的“隐形翅膀” —— 标准化 (Standardization)
        在 V3.0 的特征中，step_gap 可能是 100，而 time_per_index 可能是 0.005。这种量级差异会让 LSTM 的梯度下降变得极其困难。
        解决方案：代码中实现了 standardize_features 函数。重要的是，它遵循了机器学习的黄金法则：Fit on Train, Transform on Test。我们只用训练数据计算均值和方差，然后应用到验证集，严防数据泄露。

    2.动态序列处理 (Dynamic Padding)
        使用了 pad_sequence 和 collate_fn。这意味着我们不需要手动把所有序列截断或填充到固定长度（如 20），而是根据每个 Batch 中最长的序列动态调整。这极大地提高了训练效率，也保留了长序列的完整信息。

    3.K-Fold 交叉验证的逻辑
        我们没有仅仅训练一次。StratifiedKFold 确保了每一折中“恶意样本”的比例与整体一致（这对于处理非平衡数据很重要）。
        代码会循环 5 次，训练 5 个模型，并时刻监控验证集的 Loss。如果 Loss 不再下降（Patience=10），则触发 Early Stopping，防止过拟合。

    4.独立测试集的“终极大考”
        代码开头就将 20% 的数据完全隔离 (X_test)。这部分数据不参与任何训练或参数调整。
        最后，我们加载交叉验证中表现最好的模型权重 (best_lstm_model.pth)，在这个独立测试集上跑分。这个分数才是模型真实能力的体现。

    5.模型架构 (LSTM + Dropout)
        使用了双层 LSTM (num_layers=2) 以提取更抽象的时序特征。
        加入了 dropout=0.2，在层之间随机丢弃神经元，这是防止小样本数据过拟合的有效手段。