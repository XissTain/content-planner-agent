# 实际运行记录

- 模式：mock
- 状态：completed
- 说明：方案已实际保存；活动制作仍为计划。

| 步骤 | 工具及参数 | 实际返回摘要 | 行动依据 | 后续动作 |
|---|---|---|---|---|
| 5 | save_plan {"candidate_id": "5d39dbb2751083caa152"} | {"ok": true, "plan_id": "P-6dca86e2bd4dda129013"} | [MOCK 预设规则] 复用可行测算和已成功步骤；遇临时失败仅重试失败步骤。 | 结束：completed |

完整参数和结果见 trace.jsonl；每次模型实际收到的公开观察见 decision-inputs.jsonl。manifest.json 记录源代码、资料与输出哈希；哈希用于完整性校验，不是模型服务方签名。
