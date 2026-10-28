# 内容活动方案

状态：**incomplete**

Codex 模型调用超时；checkpoint 已保留，可重新执行续跑。

- 主题：剪辑助手新品内容活动
- 预算：20
- 截止时间：2030-01-01T10:10:00+08:00

## 实际工具步骤

| 工具 | 最新状态 | 尝试次数 | 成功次数 |
|---|---|---:|---:|
| search_assets | succeeded | 1 | 1 |
| estimate_plan | succeeded | 1 | 1 |
| generate_script | pending | 0 | 0 |
| save_plan | pending | 0 | 0 |

已保留成果：

```json
{
  "asset_ids": [
    "A01",
    "A02"
  ],
  "estimates": [
    {
      "ok": true,
      "candidate_id": "b92e7ce3e5b83b432697",
      "asset_ids": [
        "A01"
      ],
      "script_service": "standard",
      "production": "simple",
      "line_items": [
        {
          "name": "A01",
          "cost": 2,
          "minutes": 5
        },
        {
          "name": "script:standard",
          "cost": 2,
          "minutes": 15,
          "description": "标准脚本服务"
        },
        {
          "name": "production:simple",
          "cost": 2,
          "minutes": 20,
          "description": "简洁制作"
        }
      ],
      "total_cost": 6,
      "total_minutes": 40,
      "fits_budget": true,
      "budget_gap": 0,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T10:40:00+08:00",
      "fits_deadline": false,
      "minutes_gap": 30,
      "checked_at": "2030-01-01T10:00:00+08:00"
    }
  ],
  "script_ids": [],
  "scripts": []
}
```

