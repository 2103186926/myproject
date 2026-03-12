### 脚本升级点详解
    1.自动维度推断 (load_and_parse_data):
        不再依赖硬编码的数字。脚本加载 JSON 后，通过 X.shape[2] 自动获取特征维度（例如 5 或 6），并更新全局配置。这意味着如果您将来在 generate_features.py 中增加了新特征（例如加入了“CPU利用率”），无需修改此训练脚本即可直接运行。
    2.封装的 TimeSeriesScaler:
        针对 LSTM 的 3D 输入数据 (Sample, Time, Feature)，标准的 sklearn.StandardScaler 无法直接处理。我编写了这个类，它会在内部自动执行 reshape -> fit/transform -> reshape back 的操作，保证了数据处理的正确性。
    3.学习率调度 (Scheduler):
        使用了 ReduceLROnPlateau。当验证集的 Loss 不再下降时，自动减半学习率。这能帮助模型在训练后期跳出局部最优解，收敛得更精细。
    4.梯度裁剪 (Gradient Clipping):
        在 train_epoch 中增加了 nn.utils.clip_grad_norm_。这是训练 LSTM 的标配，能有效防止因序列过长导致的梯度爆炸问题，使训练过程极其稳定。
    5.完善的日志系统:
        使用 Python 标准库 logging 替代了 print。日志不仅会输出到屏幕，还会自动保存到 training.log 文件中，方便您事后回溯实验记录。