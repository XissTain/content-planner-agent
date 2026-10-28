# 实际运行记录

- 模式：mock
- 状态：needs_input
- 说明：没有相关素材，请补充素材或更改主题。

| 步骤 | 工具及参数 | 实际返回摘要 | 行动依据 | 后续动作 |
|---|---|---|---|---|
| 1 | search_assets {"query": "深海潜艇科普"} | {"ok": true, "count": 0} | [MOCK 预设规则] 先检索素材。 | finish |
| 2 | finish {"status": "needs_input", "message": "没有相关素材，请补充素材或更改主题。"} | {"ok": true, "status": "needs_input", "message": "没有相关素材，请补充素材或更改主题。"} | [MOCK 预设规则] 检索为空。 | 结束：needs_input |

完整参数和结果见 trace.jsonl；每次模型实际收到的公开观察见 decision-inputs.jsonl。manifest.json 记录源代码、资料与输出哈希；哈希用于完整性校验，不是模型服务方签名。
