为了有效捕获上述特征，我们设计了以下事件驱动的JSON日志格式。

{
    "timestamp": "2025-09-15T10:00:01.123Z",  # 事件发生的高精度时间戳(ISO 8601格式)
    "eventType": "task_start | model_query | internal_activity | task_end",   # 日志事件的类型。这是进行分析和分类的核心字段
    "logLevel": "INFO",  # 日志级别 (如 INFO, WARN, ERROR)
    "serviceName": "ComputationPlatform | ModelPredictionService",  # 产生日志的服务名称 (如 ModelPredictionService)
    "context": {  # 包含所有关联信息的上下文对象
        "userId": "string",   # 执行任务的用户ID
        "jobId": "string",   # 任务所属的作业ID
        "taskId": "string",  # 本次执行任务的唯一ID
        "sourceIp": "string"  # 发起请求的源IP地址
    },

    "details":   # 事件详情,details对象的内容根据eventType的不同而变化，专门用于捕获攻击特征。（四选一）
        1.当eventType为 "task_start" 时:
        作用: 标记攻击序列开始，记录基本信息。
        {
            "taskName": "membership_inference_attack.py",  # 任务的名称或脚本名称
            "targetModel": "seabed_terrain_classifier",  # 攻击者明确指定的目标模型
            "targetSampleHash": "a1b2c3d4e5f6...", // 目标敏感样本的哈希值，用于追踪
        }

        2.当eventType为"model_query"时:
        作用: 记录核心的查询行为和模型响应。
        {
            "modelName": "seabed_terrain_classifier",  # 被查询的模型名称
            "queryInput": {  # 一个包含所有输入特征的对象
                "featureVector": [0.85, 2450.0, 12.7, 0.23, ...]  # 输入模型的特征向量，一个包含多个数值的数组
            },
            "queryResponse": {  # 模型对输入特征的预测结果
                "confidence": 0.9876,  # 模型预测的最高置信度，一个0到1之间的数值
                "predictedClass": 3  # 模型预测的类别，一个整数表示分类结果
            },
            "executionTimeMs": 45.23,  # 模型处理此查询所需的时间（毫秒）
        }

        3.当eventType为"internal_activity" 时:
        作用: 显式记录任务内部的关键恶意行为，如模型训练。
        {
            "activityType": "attack_model_training",  # 活动类型，这里是攻击模型训练
            "activityDescription": "Task initiated training of a local RandomForestClassifier model.",  # 活动的详细描述，这里是攻击模型训练的详细信息
        }

        4.当eventType为"task_end" 时:
        作用: 记录任务结束时的摘要信息，用于计算聚合特征。
        {
            "finalStatus": "COMPLETED",  # 任务的最终状态，这里是成功完成
            "totalQueries": 151,  # 任务执行过程中进行的总查询次数
            "totalExecutionTimeSec": 128.45,  # 任务的总执行时间（秒）
            "summaryStats": {  # 任务执行过程中的统计摘要
                "confidenceVariance": 0.0256,  # 所有查询响应置信度的方差，一个0到1之间的数值，用于评估模型对成员样本的区分能力
                "attackModelTrained": true    # 是否检测到内部模型训练，一个布尔值，true表示检测到
            },
        "finalOutputSizeBytes": 88  # 任务最终输出的大小（字节），这里是一个小文件（88字节）
    }
}