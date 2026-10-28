# 内容活动方案

状态：**incomplete**

无法在预算 1 内完成：必需素材 A01 单项费用为 2，已超过预算。已测算的模板脚本＋简洁制作方案总费用为 5，预算缺口为 4，预计 10:35 完成，满足截止时间；该方案并非已验证的全局最低价。未生成脚本或保存方案。

- 主题：剪辑助手新品内容活动
- 预算：1
- 截止时间：2030-01-01T18:00:00+08:00

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
      "fits_budget": false,
      "budget_gap": 4,
      "catalog_version": "synthetic-v1",
      "finish_at": "2030-01-01T10:35:00+08:00",
      "fits_deadline": true,
      "minutes_gap": 0,
      "checked_at": "2030-01-01T10:00:00+08:00"
    }
  ],
  "script_ids": [],
  "scripts": []
}
```

