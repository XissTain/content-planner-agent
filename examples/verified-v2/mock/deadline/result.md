# 内容活动方案

状态：**incomplete**

全部组合不满足约束；最小预算缺口 0，最小时长缺口 25 分钟。

- 主题：剪辑助手新品内容活动
- 预算：20
- 截止时间：2030-01-01T10:10:00+08:00

## 实际工具步骤

| 工具 | 最新状态 | 尝试次数 | 成功次数 |
|---|---|---:|---:|
| search_assets | succeeded | 1 | 1 |
| estimate_plan | succeeded | 6 | 6 |
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
      "minutes_gap": 70,
      "checked_at": "2030-01-01T10:00:00+08:00"
    },
    {
      "ok": true,
      "candidate_id": "d2244cfb20be723e3e59",
      "asset_ids": [
        "A01"
      ],
      "script_service": "standard",
      "production": "polished",
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
          "name": "production:polished",
          "cost": 4,
          "minutes": 45,
          "description": "精细制作"
        }
      ],
      "total_cost": 8,
      "total_minutes": 65,
      "fits_budget": true,
      "budget_gap": 0,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T11:05:00+08:00",
      "fits_deadline": false,
      "minutes_gap": 55,
      "checked_at": "2030-01-01T10:00:00+08:00"
    },
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
    },
    {
      "ok": true,
      "candidate_id": "b5766fb3427244ec7c9f",
      "asset_ids": [
        "A01"
      ],
      "script_service": "template",
      "production": "polished",
      "line_items": [
        {
          "name": "A01",
          "cost": 2,
          "minutes": 5
        },
        {
          "name": "script:template",
          "cost": 1,
          "minutes": 10,
          "description": "模板脚本服务"
        },
        {
          "name": "production:polished",
          "cost": 4,
          "minutes": 45,
          "description": "精细制作"
        }
      ],
      "total_cost": 7,
      "total_minutes": 60,
      "fits_budget": true,
      "budget_gap": 0,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T11:00:00+08:00",
      "fits_deadline": false,
      "minutes_gap": 50,
      "checked_at": "2030-01-01T10:00:00+08:00"
    },
    {
      "ok": true,
      "candidate_id": "84d6095e56171fe620d6",
      "asset_ids": [
        "A01"
      ],
      "script_service": "template",
      "production": "simple",
      "line_items": [
        {
          "name": "A01",
          "cost": 2,
          "minutes": 5
        },
        {
          "name": "script:template",
          "cost": 1,
          "minutes": 10,
          "description": "模板脚本服务"
        },
        {
          "name": "production:simple",
          "cost": 2,
          "minutes": 20,
          "description": "简洁制作"
        }
      ],
      "total_cost": 5,
      "total_minutes": 35,
      "fits_budget": true,
      "budget_gap": 0,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T10:35:00+08:00",
      "fits_deadline": false,
      "minutes_gap": 25,
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
      "minutes_gap": 45,
      "checked_at": "2030-01-01T10:00:00+08:00"
    }
  ],
  "script_ids": [],
  "scripts": []
}
```

