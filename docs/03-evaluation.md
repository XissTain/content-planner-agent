# 03 · 实际效果评估

验证日期：2026-10-28（Asia/Shanghai）。Python 3.9.6；真实接入使用 codex-cli 0.164.0-alpha.11.1、ChatGPT 登录，客户端显式请求 gpt-6.1-sol、low 推理预算。CLI 没有提供独立服务端型号证明，Trace 记录实际请求配置与使用量。

## 当前技术证据

- 工程测试：**43 项通过，0 失败、0 错误**，见 [原始输出](../examples/test-results.txt) 和 [摘要](../examples/test-summary.json)。
- 离线验收：**15/15**，见 [实际报告](../examples/verified-v3/mock/evaluation.json)。
- 真实接入：**最近逐项验证 15/15 符合预期**，对应 **57 次真实模型动作**，见 [汇总及对应材料](../examples/verified-current.json)。
- 三个缺信息用例不调用模型；正常请求的附带重复执行也不调用模型。Mock 验证工程流程，不能作为真实模型决策证明。

**这不是首轮全部通过。** 当前实现的完整真实首轮为 11/15，四个未通过场景为临时工具故障、持续保存失败、截止时间不可行和截止时间重规划，原因均为模型响应超时。四项保留原始记录，增加单次响应上限后分批复验通过。小样本的最近逐项通过不能推出总体成功率为 100%。

## 复现命令

```bash
python3 scripts/test_report.py
python3 scripts/evaluate.py --mode mock --jobs 2
python3 scripts/evaluate.py --mode codex --model gpt-6.1-sol --model-timeout 180 --jobs 1
python3 scripts/check_submission.py
```

评估默认使用新的输出目录和空数据库，不覆盖提交证据。用 --case 可只复验指定场景。--jobs 只并行不同请求的独立数据库，不代表同一请求支持分布式并发。真实模型响应可能较慢，失败按实际状态返回。

## 真实接入验收逐项结果

| 场景 | 预期 / 实际 | 模型动作数 | 实际证据 |
|---|---|---:|---|
| 正常完成及重复执行 | completed / completed | 4 | [输入](../examples/verified-v3/codex/normal/input.json)、[输出](../examples/verified-v3/codex/normal/output.json)、[Trace](../examples/verified-v3/codex/normal/trace.md) |
| 预算重规划 | completed / completed | 5 | [输入](../examples/verified-v3/codex/replan/input.json)、[输出](../examples/verified-v3/codex/replan/output.json)、[Trace](../examples/verified-v3/codex/replan/trace.md) |
| 候选人确认的脚本优先 | completed / completed | 5 | [输入](../examples/verified-v3/codex/user-priority/input.json)、[输出](../examples/verified-v3/codex/user-priority/output.json)、[Trace](../examples/verified-v3/codex/user-priority/trace.md) |
| 相反偏好对照 | completed / completed | 5 | [输入](../examples/verified-v3/codex/opposite-priority/input.json)、[输出](../examples/verified-v3/codex/opposite-priority/output.json)、[Trace](../examples/verified-v3/codex/opposite-priority/trace.md) |
| 预算与截止时间都缺失 | needs_input / needs_input | 0 | [输入](../examples/verified-v3/codex/missing/input.json)、[输出](../examples/verified-v3/codex/missing/output.json)、[Trace](../examples/verified-v3/codex/missing/trace.md) |
| 单独缺预算 | needs_input / needs_input | 0 | [输入](../examples/verified-v3/codex/missing-budget/input.json)、[输出](../examples/verified-v3/codex/missing-budget/output.json)、[Trace](../examples/verified-v3/codex/missing-budget/trace.md) |
| 单独缺截止时间 | needs_input / needs_input | 0 | [输入](../examples/verified-v3/codex/missing-deadline/input.json)、[输出](../examples/verified-v3/codex/missing-deadline/output.json)、[Trace](../examples/verified-v3/codex/missing-deadline/trace.md) |
| 临时工具失败 | completed / completed | 5 | [输入](../examples/verified-v3-retry/codex/tool-failure/input.json)、[输出](../examples/verified-v3-retry/codex/tool-failure/output.json)、[Trace](../examples/verified-v3-retry/codex/tool-failure/trace.md) |
| 不可重试服务故障后换服务 | completed / completed | 6 | [输入](../examples/verified-v3/codex/service-fallback/input.json)、[输出](../examples/verified-v3/codex/service-fallback/output.json)、[Trace](../examples/verified-v3/codex/service-fallback/trace.md) |
| 持续保存失败 | incomplete / incomplete | 6 | [输入](../examples/verified-v3-retry-rest/codex/save-failure/input.json)、[输出](../examples/verified-v3-retry-rest/codex/save-failure/output.json)、[Trace](../examples/verified-v3-retry-rest/codex/save-failure/trace.md) |
| 预算不可行 | incomplete / incomplete | 3 | [输入](../examples/verified-v3/codex/impossible/input.json)、[输出](../examples/verified-v3/codex/impossible/output.json)、[Trace](../examples/verified-v3/codex/impossible/trace.md) |
| 截止时间不可行 | incomplete / incomplete | 4 | [输入](../examples/verified-v3-retry-rest/codex/deadline/input.json)、[输出](../examples/verified-v3-retry-rest/codex/deadline/output.json)、[Trace](../examples/verified-v3-retry-rest/codex/deadline/trace.md) |
| 截止时间重规划 | completed / completed | 6 | [输入](../examples/verified-v3-retry-rest/codex/deadline-replan/input.json)、[输出](../examples/verified-v3-retry-rest/codex/deadline-replan/output.json)、[Trace](../examples/verified-v3-retry-rest/codex/deadline-replan/trace.md) |
| 无相关素材 | needs_input / needs_input | 3 | [输入](../examples/verified-v3/codex/no-assets/input.json)、[输出](../examples/verified-v3/codex/no-assets/output.json)、[Trace](../examples/verified-v3/codex/no-assets/trace.md) |
| 跨进程失败步骤续跑 | completed / completed | 5 | [首次](../examples/verified-v3/codex/resume/trace.md)、[续跑](../examples/verified-v3/codex/resume-continued/trace.md) |

## 关键行为的实际结果

- 脚本优先：首选 premium/polished 12 超预算；模型改为 premium/simple，重新测算 10、55 分钟，随后生成和保存。
- 相反偏好：同样预算 10，模型保留 polished 制作，改为 standard 脚本，测算 8、65 分钟。这体现需求影响决策，而不是固定输出同一答案。
- 不可原样重试的故障：premium 服务失败后，模型只尝试一次该失败服务，换脚本服务、重新测算并成功保存，素材检索没有重跑。
- 临时失败：模型观察工具错误后选择重试；运行器没有自动业务重试分支。持续保存失败则明确停止，已成功脚本没有重新生成。
- 跨进程续跑：首个 CLI 进程已生成脚本但保存失败；第二个进程 PID 不同，仅执行 save_plan 一次，脚本 ID 不变。
- 无预算或截止时间：返回 needs_input，工具和模型调用均为零。

## 独立校验与版本对应

每个最新版用例包含实际输入、资料表、可读方案、完整 Trace、每轮模型公开观察和 manifest。核对器检查文件 SHA-256、当前应用源码对应关系、上一步结果是否进入下一步输入，并由资料表重新计算最终费用、工时、必需素材、事实来源和依赖。故障配置不对模型可见。哈希是完整性检查，不是服务方签名。

工程测试另覆盖：SQLite 真实写入异常、重试次数在新运行中重置、模型等待与续跑时真实截止时间过期、同 ID 变输入或资料表、错误工具参数、越过依赖、未保存却声称成功，以及历史成功掩盖最新失败。

## 失败、修复与未过度声称的内容

- 初始接入曾出现代理与连接超时；旧记录保留在 examples/codex/model-timeout。
- verified-v2 扩展验收出现多次模型超时，并暴露旧脚本仅匹配 incomplete 状态造成的假阳性。它不作为当前版本通过依据。
- 之后隔离桌面环境、忽略无关 CLI 用户配置、显式指定目标模型并增加适配测试。这个组合处理未做完整单因素因果归因，不能断言某个变量为唯一原因。
- verified-v3 的首轮四项超时全部保留；tool-failure 的复验见 verified-v3-retry，另外三项见 verified-v3-retry-rest。提交检查按每项实际完成时间选择最近记录，不按“挑最好一次”选择。
- 业务工具是合成实现；没有真实制作、发布、收费账本或生产排程。真实时钟采用整份方案的保守工时估计，模拟样例使用固定 2030 年业务时间。
- 本地串行幂等不等于分布式外部副作用保证。CI 已配置，线上执行结果以仓库 Actions 的实际记录为准，不能用本地结果替代。
- 候选人已作真实需求取舍；个人复跑、个人手写代码和个人用时尚未报告，不虚构这些经历。公开仓库 URL 见 README，最终远程 SHA 用提交检查命令核对。
