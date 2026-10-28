# 验证材料入口

评审请先看 [当前汇总](verified-current.json)，它指向每个场景最近的实际验证。具体用例目录内 result.md 可直接阅读最终方案，trace.md 可查看决策过程。

- `verified-v3/mock/`：当前实现的全套离线验收，不能证明真实模型决策能力。
- `verified-v3/codex/`：当前实现的真实首轮验收（11/15）；缺信息与重复请求不计入模型动作数。
- `verified-v3-retry/codex/`、`verified-v3-retry-rest/codex/`：四项首轮超时的实际复验记录；最近结果全部符合预期。原始超时未删除。
- `test-results.txt`、`test-summary.json`：当前实现的工程测试实际输出与源码对应信息。
- `verified-v2/`：优化过程中保留的上一轮原始证据，含多次模型超时。不可代替当前版本通过证明；旧脚本对预期 incomplete 的判定不够严格，已在新版修正。
- `mock/`、`codex/`：最初版本的验证材料与首次模型接入失败记录，作为开发历史保留。
- `inputs/`：供 CLI 复跑的合成输入；`user-priority.json` 包含候选人在对话中确认的业务取舍。

最新单个用例包含：

| 文件 | 用途 |
|---|---|
| input.json / catalog.json | 此次实际输入、实际使用的资料和费用表 |
| output.json / result.md | 结构化实际输出、可读活动方案 |
| trace.jsonl / trace.md | 动作参数、工具实际结果、简短依据、后续动作 |
| decision-inputs.jsonl | 模型每步实际接收的公开观察，不含故障配置或内部推理 |
| manifest.json | 源码、资料及产物 SHA-256、时间、运行上限与故障配置 |

完整性哈希用于发现文件不一致，不是服务端签名。评估脚本默认将新运行写入 `.runtime/evaluations/`，不会覆盖这里的交付证据。
