# 实际运行记录

- 模式：mock
- 状态：incomplete
- 说明：save_plan 本次连续失败，保留成功步骤供续跑。

| 步骤 | 工具及参数 | 实际返回摘要 | 行动依据 | 后续动作 |
|---|---|---|---|---|
| 1 | search_assets {"query": "剪辑助手新品内容活动"} | {"ok": true, "count": 2} | [MOCK 预设规则] 先检索素材。 | estimate_plan |
| 2 | estimate_plan {"asset_ids": ["A01"], "script_service": "premium", "production": "polished"} | {"ok": true, "total_cost": 12, "total_minutes": 80, "fits_budget": true, "budget_gap": 0, "fits_deadline": true, "minutes_gap": 0} | [MOCK 预设规则] 测算首选方案。 | generate_script |
| 3 | generate_script {"candidate_id": "5d39dbb2751083caa152"} | {"ok": true, "script_id": "S-0e1085bb8ca0201f7cdc"} | [MOCK 预设规则] 复用可行测算和已成功步骤；遇临时失败仅重试失败步骤。 | save_plan |
| 4 | save_plan {"candidate_id": "5d39dbb2751083caa152"} | {"ok": false, "error": "injected_tool_failure", "retryable": true, "message": "save_plan 模拟临时故障，可由模型决定是否重试。"} | [MOCK 预设规则] 复用可行测算和已成功步骤；遇临时失败仅重试失败步骤。 | save_plan |
| 5 | save_plan {"candidate_id": "5d39dbb2751083caa152"} | {"ok": false, "error": "injected_tool_failure", "retryable": true, "message": "save_plan 模拟临时故障，可由模型决定是否重试。"} | [MOCK 预设规则] 复用可行测算和已成功步骤；遇临时失败仅重试失败步骤。 | finish |
| 6 | finish {"status": "incomplete", "message": "save_plan 本次连续失败，保留成功步骤供续跑。"} | {"ok": true, "status": "incomplete", "message": "save_plan 本次连续失败，保留成功步骤供续跑。"} | [MOCK 预设规则] 本次有限重试后停止。 | 结束：incomplete |

完整参数和结果见 trace.jsonl；每次模型实际收到的公开观察见 decision-inputs.jsonl。manifest.json 记录源代码、资料与输出哈希；哈希用于完整性校验，不是模型服务方签名。
