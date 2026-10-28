# 内容活动方案

状态：**incomplete**

Codex 模型调用超时；checkpoint 已保留，可重新执行续跑。

- 主题：剪辑助手新品内容活动
- 预算：20
- 截止时间：2030-01-01T10:45:00+08:00

## 实际工具步骤

| 工具 | 最新状态 | 尝试次数 | 成功次数 |
|---|---|---:|---:|
| search_assets | succeeded | 1 | 1 |
| estimate_plan | succeeded | 2 | 2 |
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
      "candidate_id": "5d39dbb2751083caa152",
      "asset_ids": [
        "A01"
      ],
      "script_service": "premium",
      "production": "polished",
      "line_items": [
        {
          "name": "A01",
          "cost": 2,
          "minutes": 5
        },
        {
          "name": "script:premium",
          "cost": 6,
          "minutes": 30,
          "description": "创意脚本服务"
        },
        {
          "name": "production:polished",
          "cost": 4,
          "minutes": 45,
          "description": "精细制作"
        }
      ],
      "total_cost": 12,
      "total_minutes": 80,
      "fits_budget": true,
      "budget_gap": 0,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T11:20:00+08:00",
      "fits_deadline": false,
      "minutes_gap": 35,
      "checked_at": "2030-01-01T10:00:00+08:00"
    },
    {
      "ok": true,
      "candidate_id": "ec24595c896cee43d34a",
      "asset_ids": [
        "A01"
      ],
      "script_service": "premium",
      "production": "simple",
      "line_items": [
        {
          "name": "A01",
          "cost": 2,
          "minutes": 5
        },
        {
          "name": "script:premium",
          "cost": 6,
          "minutes": 30,
          "description": "创意脚本服务"
        },
        {
          "name": "production:simple",
          "cost": 2,
          "minutes": 20,
          "description": "简洁制作"
        }
      ],
      "total_cost": 10,
      "total_minutes": 55,
      "fits_budget": true,
      "budget_gap": 0,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T10:55:00+08:00",
      "fits_deadline": false,
      "minutes_gap": 10,
      "checked_at": "2030-01-01T10:00:00+08:00"
    }
  ],
  "script_ids": [],
  "scripts": []
}
```

