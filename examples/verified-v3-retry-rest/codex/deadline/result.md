# 内容活动方案

状态：**incomplete**

已评估的两种方案均满足预算但超时：premium＋polished 需80分钟，超时70分钟；template＋simple 需35分钟，超时25分钟。尚无可行方案，未生成脚本或保存。其余组合未经测算，不能断言35分钟是全局最短耗时；在保留必选素材A01和当前截止时间的条件下，本次未完成。

- 主题：剪辑助手新品内容活动
- 预算：20
- 截止时间：2030-01-01T10:10:00+08:00

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
      "minutes_gap": 70,
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
    }
  ],
  "script_ids": [],
  "scripts": []
}
```

