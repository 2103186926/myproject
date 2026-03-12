Json日志格式：
{
    "timestamp": "2025-09-14T19:30:01.123Z",  # 事件发生的高精度时间戳(ISO 8601格式)
    "eventType": "task_start"/"model_query"/"task_error"/"task_end",  # 日志事件的类型。这是进行分析和分类的核心字段
    "logLevel": "INFO",  # 日志级别 (如 INFO, WARN, ERROR)
    "serviceName" : "ComputationPlatform"/"ModelPredictionService",  # 产生日志的服务名称 (如 ModelPredictionService)
    "context": {    
        "userId": "attacker_01"  # 执行任务的用户ID
        "jobId" : "job_789"  # 任务所属的作业ID
        "taskId" : "task_abc123"  # 本次执行任务的唯一ID
        "sourceIp" : "203.0.113.10"  # 发起请求的源IP地址
    },
    "details":  # 事件详情,details对象的内容根据eventType的不同而变化，专门用于捕获攻击特征。（四选一）
        1.如果是task_start事件类型，
        作用: 标记一个潜在攻击序列的开始，并记录其初始声明的参数。
        {
          "taskName" : "malicious_inversion_attack.py",  # 任务的名称或脚本名称
          "modelName" : "ocean_ts_predictor_v1",  # 攻击者明确指定的目标模型
          "declaredParameters" : {  # 用户提交任务时声明的意图参数，例如目标坐标、深度范围等。这可以与后续实际的查询行为进行对比
                "target_lat":38.5,
                "target_lon":122.0,
                "depth_range":[0,500]
          }
    }
    
        2.如果是model_query事件类型 (最核心的日志)，
        作用:记录每一次对模型的精确调用。这是捕获所有关键攻击特征的数据来源。
        {
          "modelName" : "ocean_ts_predictor_v1"  # 被查询的模型名称
          "queryInput" : {  # 一个包含所有输入特征的对象
                "latitude":38.5012,  # 维度值
                "longitude":121.9987,  # 经度值
                "depth":0  # 深度值
          },
          "queryStatus" : "SUCCESS",  # 查询状态 (SUCCESS 或 FAILURE)。
          "executionTimeMs" : 210,  # 本次查询的执行耗时（毫秒）。
          "responseId" : "resp_001"  # 与本次查询对应的唯一响应ID，便于问题追溯。
    }

        3.如果是task_error事件类型
        作用: 记录任务执行期间发生的任何错误。
        {
          "errorCode" : 504,  # 错误的机器可读代码 (例如 504超时)。
          "errorMessage" : "Model response timeout"  # 详细的错误信息 (例如 Model response timeout)。
    }

        3.如果是task_end事件类型
        作用: 标记攻击序列的结束，并提供整个任务的摘要统计信息。
        {
          "finalStatus" : "COMPLETED",  # 任务的最终状态 (COMPLETED, FAILED)
          "totalQueries" : 500,  # 任务期间发起的总查询次数
          "successfulQueries" : 498,  # 成功的查询次数
          "totalExecutionTimeSec" : 128  # 任务总执行时间（秒）
    }
}