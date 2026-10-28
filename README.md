# 内容任务规划 Agent · 小影校招第 2 题

项目仓库：[XissTain/content-planner-agent](https://github.com/XissTain/content-planner-agent)。

在预算和截止时间内形成一份内容活动方案。GPT 根据实际测算和工具错误选择下一步动作；Python 校验硬约束并保存结果。业务工具使用合成数据，模型通过已登录的 Codex CLI 调用，无需另配 API Key。

**本次业务取舍由候选人确认：预算不足时，优先保留创意脚本，先简化制作。** 相反偏好的对照用例用于验证模型是否根据需求改变方案，不将“更便宜”直接当作“更合适”。

当前技术验证：**43 项工程测试通过；离线 15/15；真实接入最近逐项 15/15**。真实首轮 11/15，四项超时的失败和复验均保留，详见评估文档；不把逐项复验通过当作单次成功率 100%。

## 评审先看

| 内容 | 入口 |
|---|---|
| 按题面逐项核对、可争取得分点、提交剩余项 | [提交审查](docs/06-submission-review.md) |
| 实际测试数量、模型结果、失败和修复 | [效果评估](docs/03-evaluation.md) |
| 最新模型运行记录与最终方案 | [验证材料入口](examples/README.md) |
| 人与 AI 的实际贡献边界 | [AI 使用记录](docs/04-ai-usage.md) |
| 候选人理解与复跑要点 | [个人复查与答辩](docs/07-review-and-defense.md) |

## 三分钟本地复跑

Python 3.9 或以上，无第三方 Python 依赖；在本目录执行：

```bash
python3 -m unittest discover -s tests -v
python3 run.py examples/inputs/user-priority.json --mode mock --db .runtime/demo.sqlite3 --out .runtime/demo
```

预期费用为 **10**：素材 2＋premium 脚本 6＋simple 制作 2。首选 premium/polished 测算为 12，重规划保留脚本偏好后重新测算为 10。最终方案见 `.runtime/demo/result.md`。

重新生成全套离线验收（默认写入新的运行目录，不覆盖提交证据）：

```bash
python3 scripts/evaluate.py --mode mock --jobs 2
```

`mock` 是明确标记的预设策略替身，只验证流程与工程边界。真实模型证据必须查看 [当前汇总](examples/verified-current.json) 指向的实际记录。

## 真实模型复跑

需要安装 Codex CLI，并使用自己的账号登录：

```bash
codex --version
codex login status
# 未登录时执行：codex login
python3 run.py examples/inputs/user-priority.json --mode codex --model gpt-6.1-sol --model-timeout 180 --db .runtime/live.sqlite3 --out .runtime/live
```

模型名可由 `--model` 或 `CODEX_MODEL` 指定，默认 `gpt-6.1-sol`；它是本项目验证的目标型号，不保证任意账号均有权限。默认单步推理预算为 `low`，可用 `--reasoning-effort` 调整。调用使用账号现有的 Codex 额度；离线模式完全不调用模型。

CLI 只负责返回一个结构化业务动作。主程序执行工具，将真实结果交给下一轮模型。调用时使用空临时目录、只读沙箱、`--ignore-user-config`，隔离桌面任务的线程和工具管道环境，关闭 apps、plugins、hooks、shell_tool、multi_agent；项目不读取或复制登录凭据。自定义 CLI provider、MCP 或 hooks 配置不在本项目接入范围。

保留系统/环境已有代理，不修改全局设置。网络不可用、模型超时或 CLI 失败会返回 `incomplete` 并保留本地 checkpoint；不能把连接失败计成业务成功。逐轮调用 CLI 存在启动延迟。

完整真实验收：

```bash
python3 scripts/evaluate.py --mode codex --model gpt-6.1-sol --model-timeout 180 --jobs 1
```

## 为什么具备动态决策

- 预算超限：模型先观察首选方案的实际测算，再选择另一组合并重新测算。
- 质量偏好：同为预算 10，保留脚本与保留制作的用户偏好应产生不同方案。
- 临时失败：模型决定重试、换方案或停止，运行器没有失败后自动重试的分支。
- 服务不可用：返回 `retryable=false`，模型应改用其他脚本服务并重新测算。
- 部分成功：保存失败后保留素材、测算和脚本；跨进程续跑只需再次保存。
- 硬约束由程序执行：不可移除必需素材，超预算/超时不可生成或保存，只有 SQLite 实际保存成功才完成。

## 故障、续跑与可审计输出

```bash
python3 run.py examples/inputs/normal.json --mode mock --db .runtime/resume.sqlite3 --out .runtime/first --fail save_plan:1 --max-steps 4
# 预期退出码 2；再次执行应只续跑保存：
python3 run.py examples/inputs/normal.json --mode mock --db .runtime/resume.sqlite3 --out .runtime/continued
```

不可原样重试的故障：`--fail-permanent generate_script@premium:10`。资料表可用 `--catalog` 替换；同一 request_id 变更输入或资料表会拒绝复用，需使用新 ID。

每次输出包含可读方案、完整 Trace、每步模型公开观察及 SHA-256 清单。独立核对器复算费用、时间、来源、依赖和观察链。哈希验证一致性，不声称是模型服务方签名。

默认每次最多 12 个动作；达到上限明确返回 `incomplete`。同一请求再次执行是一段新的有限运行，成功步骤复用。CLI 退出码：0 完成，2 需补信息或未完成，1 输入文件/配置错误。

## 时钟与业务范围

必填 `request_id`、`topic`、`budget`、带时区的 `deadline`。`replan_priority` 是可选软偏好：`preserve_script` / `preserve_production`。预算、截止时间、必需素材是硬约束，优先级不能覆盖它们。

提供 `start_at` 时使用固定模拟业务时钟，示例设为 2030 年便于复现。不提供时使用真实时钟，在每次决策前、生成和保存前刷新，旧测算过期不能继续保存。时间是串行整份方案的保守估计，不是生产排程或实际制作工时。

费用表在 [data/catalog.json](data/catalog.json)，采用整数模拟单位，包括素材、脚本、制作的计划估价，不是实际付费工具账单，也不包含模型费用。脚本业务工具为本地合成模板；制作只规划，不实际制作或发布。

## 提交与工程材料

```bash
python3 scripts/check_submission.py
python3 scripts/check_submission.py --published
python3 scripts/package_submission.py
```

第一个命令检查技术内容，第二个额外检查 GitHub URL、本地最终 commit、远程版本和未提交改动。正式提交须提供 **题号 2、GitHub URL、最终远程 commit SHA**；私有仓库须确保评审可读。ZIP 是辅助交付快照，不能替代 GitHub 项目。

[需求](docs/01-requirements.md) · [设计](docs/02-solution.md) · [评估](docs/03-evaluation.md) · [AI 使用](docs/04-ai-usage.md) · [复盘](docs/05-retrospective.md)

使用 Python 原生循环与 SQLite，没有 Agent 框架。已配置 Python 3.9/3.13 的离线 CI，线上结果以 [GitHub Actions](https://github.com/XissTain/content-planner-agent/actions) 的实际记录为准。运行时环境、实际命令和 CLI 版本见评估文档。

接入依据：[Codex 官方非交互模式说明](https://learn.chatgpt.com/docs/non-interactive-mode)。CI 配置参照 [checkout](https://github.com/actions/checkout) 和 [setup-python](https://github.com/actions/setup-python) 官方用法。
