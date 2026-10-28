# 06 · 提交审查与得分依据

本页按题面要求审查，不是官方评分表；试卷没有提供各项分值，不能保证满分或虚构预计分数。技术完成与 GitHub 正式提交分别判断，最终以实际验收报告和提交检查为准。

当前技术检查通过：43 项工程测试、15 项离线验收，以及 15 项真实接入场景的最近结果均符合预期；真实完整首轮为 11/15，四项模型超时经复验通过，原始失败保留。详见 [实际评估](03-evaluation.md)。

## 必做项与证据映射

| 题面要求 | 本项目实现 | 主要证据 |
|---|---|---|
| 正常完成 | 素材、测算、脚本和方案保存，逐项成本与计划依赖 | [正常 Trace](../examples/verified-v3/codex/normal/trace.md) |
| 缺预算或截止时间 | 分别校验，不自行补值，不调用模型 | [缺预算](../examples/verified-v3/codex/missing-budget/output.json)、[缺截止时间](../examples/verified-v3/codex/missing-deadline/output.json) |
| 工具失败与保留成果 | 失败成为模型观察，保留已有素材和测算 | [临时失败](../examples/verified-v3-retry/codex/tool-failure/trace.md) |
| 预算超限 | 模型观察实际测算后改变方案并再次测算 | [用户优先级](../examples/verified-v3/codex/user-priority/trace.md) |
| 无可行方案与缺口 | 明确未完成，结构化列出已评估方案缺口，不冒充全局最优 | [预算不可行](../examples/verified-v3/codex/impossible/output.json) |
| 重复执行 | 唯一请求、输入和资料表指纹、0 次新调用、1 份方案 | [重复输出](../examples/verified-v3/codex/repeat/output.json) |
| 真正模型动态决策 | 每次动作由 Codex/GPT 返回，工具结果进入下一轮 | [模型输入](../examples/verified-v3/codex/user-priority/decision-inputs.jsonl)、[完整动作](../examples/verified-v3/codex/user-priority/trace.jsonl) |
| 至少两条决策路径 | 正常、预算、服务不可用、截止时间调整等实际路径 | [最新版评估报告](../examples/verified-current.json) |
| 有执行上限 | 上限后 incomplete/step_limit，成功结果保留 | [续跑前](../examples/verified-v3/codex/resume/output.json) |
| 至少三组输入/输出/记录 | 当前套件覆盖 15 个主场景，重复与续跑附带额外记录 | [材料入口](../examples/README.md) |
| 统一仓库规范 | README、src、tests、examples、data、五份文档、依赖说明、env 示例 | [README](../README.md) |
| AI 范围与个人贡献 | 标明 AI 实现与测试，候选人的实际业务决策可追溯 | [AI 使用](04-ai-usage.md)、[结构化贡献](contributions.json) |
| 实际用时、未完成与限制 | 分阶段记录辅助会话窗口，不虚构个人投入；明确范围 | [AI 使用](04-ai-usage.md)、[评估限制](03-evaluation.md) |
| GitHub URL、最终 SHA、评审可读 | 公开仓库已创建，最终远程版本由检查命令核对 | `python3 scripts/check_submission.py --published` |

## 已针对性加强的得分机会

### 业务理解：合理重规划，而非只压低价格

候选人决定优先保留创意脚本，落实成实际输入字段和对照验证。预算是硬约束，质量取舍是软偏好；可行方案之间的选择要符合运营目标。脚本和制作是不同费用项，不能笼统地声称模型“优化了成本”。

### Agent 决策：错误类型不同，后续动作不同

临时失败可以有限重试；retryable=false 时应换服务并重新测算。时间超限与预算超限都有实际测算反馈。运行器只守边界，不替模型硬编码所有恢复路线。

### 工程实现：真实保存状态与可恢复成果

不仅演示注入失败，还用真正拒绝 SQLite 写入的测试验证不会伪报成功。最新失败不被历史成功掩盖。输入和资料变更拒绝复用旧方案，真实时钟不会在续跑后冻结。

### 明确加分项：跨进程失败步骤续跑

两个独立 CLI 进程；第一次脚本已成功、保存失败并达到上限，第二次只有保存动作；脚本 ID 不变。这比在同一个内存对象中继续执行更有说服力。

### 效果验证：可复算、可追查、可区分失败原因

模型看到的公开输入、工具实际返回、下一动作相互关联；独立核对器从资料表重算费用、工时与事实来源。源码变更使旧证据失效。模型断线不能冒充“业务无解”通过，历史失败也保留并解释。

### 学习改进：展示真实问题和修复

复盘记录状态汇总误判、重试耗尽后无法续跑、冻结时钟、评估只看状态的假阳性，以及模型环境耦合与隔离验证。说明具体问题、修改与验证，不用“学会了某框架”代替工程证据。

## 不为堆功能增加的内容

题面不要求 UI、线上部署、多 Agent 或生产 Runtime，因此没有把时间用于这些部分。合成业务工具是被允许的，不伪装为已经对接真实发布或付费平台。离线 CI 是便于复跑的工程补充，未执行前不宣称线上 CI 已通过。

## 正式提交信息

候选人已创建公开仓库 [XissTain/content-planner-agent](https://github.com/XissTain/content-planner-agent)。正式提交填写题号 2、该 URL 和上传后核对的最终远程 commit SHA。公开仓库便于评审读取；ZIP 不能替代这些字段。

个人参与已如实记录为需求和业务优先级决策；亲自复跑、个人代码修改与个人用时尚未报告。建议理解 [复查与答辩](07-review-and-defense.md) 后再补充实际记录，不能预填已经完成。
