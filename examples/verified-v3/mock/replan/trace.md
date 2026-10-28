# 实际运行记录

- 模式：mock
- 状态：completed
- 说明：方案已实际保存；活动制作仍为计划。

| 步骤 | 工具及参数 | 实际返回摘要 | 行动依据 | 后续动作 |
|---|---|---|---|---|
| 1 | search_assets {"query": "剪辑助手新品内容活动"} | {"ok": true, "count": 2} | [MOCK 预设规则] 先检索素材。 | estimate_plan |
| 2 | estimate_plan {"asset_ids": ["A01"], "script_service": "premium", "production": "polished"} | {"ok": true, "total_cost": 12, "total_minutes": 80, "fits_budget": false, "budget_gap": 2, "fits_deadline": true, "minutes_gap": 0} | [MOCK 预设规则] 测算首选方案。 | estimate_plan |
| 3 | estimate_plan {"asset_ids": ["A01"], "script_service": "standard", "production": "polished"} | {"ok": true, "total_cost": 8, "total_minutes": 65, "fits_budget": true, "budget_gap": 0, "fits_deadline": true, "minutes_gap": 0} | [MOCK 预设规则] 上一方案不满足约束，测算另一组合。 | generate_script |
| 4 | generate_script {"candidate_id": "d2244cfb20be723e3e59"} | {"ok": true, "script_id": "S-b73566930a2b5e655e7a"} | [MOCK 预设规则] 复用可行测算和已成功步骤；遇临时失败仅重试失败步骤。 | save_plan |
| 5 | save_plan {"candidate_id": "d2244cfb20be723e3e59"} | {"ok": true, "plan_id": "P-779aee97e0ab6f7b7049"} | [MOCK 预设规则] 复用可行测算和已成功步骤；遇临时失败仅重试失败步骤。 | 结束：completed |

完整参数和结果见 trace.jsonl；每次模型实际收到的公开观察见 decision-inputs.jsonl。manifest.json 记录源代码、资料与输出哈希；哈希用于完整性校验，不是模型服务方签名。
