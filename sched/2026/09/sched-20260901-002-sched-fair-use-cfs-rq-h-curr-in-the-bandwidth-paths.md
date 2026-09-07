# sched/fair: Use cfs_rq->h_curr in the bandwidth paths

## TL;DR

Wanwu Li 修 single-runqueue 转换（`85570f10a4c6`）在 CFS bandwidth 路径上漏改的两处 `cfs_rq->curr`：`throttle_cfs_rq()` 因此对中间层级永远判不到「该层有运行实体」，配额耗尽时既不申请整 slice 也不布防 deferred throttle，任务可以**持续超出所属 cgroup 的 `cpu.max` 配额**。Aaron Lu 当天给出 `Reviewed-by` + `Tested-by`，并独立复现了配额超用现象。无任何人反对，是本日推进最干净的一个修复。

## 背景与问题

自 `85570f10a4c6 ("sched/eevdf: Move to a single runqueue")` 起，「本层级是否有实体在跑」的信息从 `cfs_rq->curr` 移到 `cfs_rq->h_curr`，`cfs_rq->curr` 只在 root cfs_rq 上维护。cgroup 层级仍被保留用于负载跟踪与带宽记账，因此**带宽路径成了唯一还会在每一层执行、又去读每层 current 的代码**。作者审计了 `kernel/sched/fair.c` 中全部 `cfs_rq->curr` 引用，指出只有两处仍在层级结构的每一层上执行：

1. `throttle_cfs_rq()` 读 `cfs_rq->curr` 判断被节流层是否有运行实体。对中间层 cfs_rq 该判断**恒为 false**，于是配额耗尽时不会申请一整个 `sched_cfs_bandwidth_slice()`、也不会通过 `task_throttle_setup_work()` 布防 deferred throttle task_work；一个正在运行的任务可以一直跑超它所在组的配额，直到下一次 pick 才把 work 布上。
2. `distribute_cfs_runtime()` 用 `cfs_rq->curr` 门控 clock 刷新与 runtime 记账，对 cgroup 的 cfs rq 永远不触发。自 `28ad5427682b ("sched/fair: Call update_curr() before unthrottling the hierarchy")` 之后 `unthrottle_cfs_rq()` 无条件追账，所以这条**当前不构成正确性漏洞**，但这段检查原本要做的刷新丢了。

影响范围：所有依赖 `cpu.max` 做严格配额约束的场景（容器 CPU 限额、混部隔离），在多层 cgroup 拓扑下表现为周期性超出配额的「逃逸」。

## 技术方案

两片都是把读取对象从 `cfs_rq->curr` 换成转换后的 `cfs_rq->h_curr`，不新增机制、不改数据结构：

- `1/2`：`throttle_cfs_rq()` —— 恢复「层级内有运行实体 → 预扣一个完整 slice + 布防 deferred throttle」的语义。
- `2/2`：`distribute_cfs_runtime()` —— 让 clock 刷新/runtime 记账在 cgroup 层真正生效。

关键取舍：作者刻意把改动限定为「补齐转换漏改的读取点」，而不是重新设计 throttling 判定；他同时说明其余 `cfs_rq->curr` 读者都被限制在 root 或单层路径上，因此无需一并改。这使补丁与 EEVDF/single-runqueue 的既有语义保持一致，评审面很小。

## 版本演进与当前进展

- **v1**（2026-08-31 18:11，cover `<20260831101141.391382-1-liwanwu@kylinos.cn>`，2 片），无新版本。
- **2026-09-01 10:38** Aaron Lu 回 cover：整系列 `Reviewed-by` + `Tested-by`，并给出复现描述；**12:09** 作者回复确认现象与「逃逸的 deferred-throttle 路径」完全吻合（当天发了两条内容相同的重复回帖）。
- 本日无 v2 需求：没有 review 意见要求改动代码。

## Maintainer 意见与讨论焦点

- **Aaron Lu（字节跳动）**：唯一实质性意见，且是认可 + 验证。他构造的场景很关键——把 `nop` 绑在单个 CPU 上，可以看到该任务**时不时用掉超过其配额的 CPU 时间**；打上系列后不再出现。作者回应："The periodic quota overshoot you observed matches the escaped deferred-throttle path exactly."
- 讨论焦点不在方案对错，而在**这类漏改为什么会发生**：cover letter 里作者自陈这是全量审计 `cfs_rq->curr` 的结果，等于把 single-runqueue 转换的收尾工作摊开。本日无人（包括 Peter Zijlstra）对这个判断提出异议。
- 无人 NAK，无人要求拆分，无人要求补充 benchmark。

## 合入评估

`likelihood = merged`（已合入 mainline，非预测）。**09-01 当日的确还没有维护者表态**，这一点当天判断正确；但补跑时按后续缓存核对，两片已经走完全程：

- 两片**都自带** `Fixes: 85570f10a4c6 ("sched/eevdf: Move to a single runqueue")`（`1/2` `<20260831101141.391382-2-liwanwu@kylinos.cn>`、`2/2` `<20260831101141.391382-3-liwanwu@kylinos.cn>`），因此不存在「缺 Fixes 指向」的问题；但两片也**没有** `Cc: stable`。
- **09-06 19:22** Ingo Molnar 的 `[GIT PULL] scheduler fixes`（`<ap1NEllrD8nMsFiB@gmail.com>`）从 `tip/sched/urgent` 拉出 `sched-urgent-2026-09-06`，`Wanwu Li (2)` 列出 `sched/fair: Use cfs_rq->h_curr in throttle_cfs_rq()` 与 `... in distribute_cfs_runtime()`；Ingo 给 Linus 的摘要里把两者写成 "Fix throttling/bandwidth calculation bug ..., caused by the recent single-runqueue conversion"——即回归定性由维护者背书，而非作者自陈。
- **09-07 02:11** pr-tracker-bot 确认该 pull 已合入 `torvalds/linux.git`，merge commit `88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8`。

也就是说：无需 Peter Zijlstra / Vincent Guittot 另行收取，`tip/sched/urgent` 路径已经走完；剩下的唯一悬空点是 stable——由于没有 `Cc: stable`，是否回合取决于 stable 维护者是否自己从 `Fixes:` 追下来。

## 效果评估

有验证性结果，无量化数字。Aaron Lu 的 `Tested-by` 给出的是**行为级观测**：单 CPU 绑定 `nop` 时，修复前可观测到任务用超配额、修复后不再出现；作者确认这与 deferred throttle 逃逸路径完全对应。没有给出「超用了多少百分比」「节流频率变化」之类的数字，邮件中也未出现任何 benchmark。其余收益描述（throttling 语义恢复、记账刷新回归）属机制性推论。

## 我可以参与的点

- **回合自查（最相关）**：只要分支带过 single-runqueue / `h_curr` 那一层转换，就必须同时核对 `throttle_cfs_rq()` 与 `distribute_cfs_runtime()` 两处读取点。只回合转换而漏这两片，现象是「偶发过度节流 / 配额算错 / 容器 CPU 限额被跑穿」，从现象侧很难定位到根因——这是本条对你最直接的价值。
- **把复现做成回归测试**：现有验证是单 CPU + `nop` 的人工观察。可以补一个多层级（父组配额 + 子组负载）+ 嵌套 throttle 的自动化脚本，量测超用比例，回帖作为 `Tested-by` 的补充数据；这类数据对 Ingo 决定是否 `Cc: stable` 有用。
- **顺着作者的审计做延伸**：作者只审计了 `fair.c` 里的 `cfs_rq->curr`。可以检查 `cfs_bandwidth` 相关路径与 `CONFIG_CFS_BANDWIDTH=n`/burst 组合下的分支是否同样存在漏改，必要时另发补丁。

## 参考链接

- cover letter: https://lore.kernel.org/all/20260831101141.391382-1-liwanwu@kylinos.cn/
- Aaron Lu 的 Reviewed-by + Tested-by: https://lore.kernel.org/all/20260901023851.GA4059187@bytedance.com/
- 作者确认现象吻合: https://lore.kernel.org/all/20260901040927.773631-1-liwanwu@kylinos.cn/
- Ingo Molnar 09-06 的 tip/sched/urgent pull: https://lore.kernel.org/all/ap1NEllrD8nMsFiB@gmail.com/
- 09-07 pr-tracker-bot 合入确认（mainline merge commit `88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8`）: https://lore.kernel.org/all/178871829440.1639575.4127304395444817583.pr-tracker-bot@kernel.org/
- tip-bot 逐片 commit hash: 未获取到（缓存内只有 pull 的 merge commit）
- stable backport: 未获取到（两片带 `Fixes: 85570f10a4c6` 但无 `Cc: stable`）

---
subject: "sched/fair: Use cfs_rq->h_curr in the bandwidth paths"
id: sched-20260901-002
date: '2026-09-01'
subsystem: sched
type: bug
status: merged_tip
severity: high
thread_root_msgid: "<20260831101141.391382-1-liwanwu@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20260831101141.391382-1-liwanwu@kylinos.cn/"
authors: [Wanwu Li, Aaron Lu]
maintainers_involved: [Aaron Lu, Ingo Molnar]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260831101141.391382-1-liwanwu@kylinos.cn>"
    date: '2026-08-31'
    summary: '2 片：throttle_cfs_rq() 与 distribute_cfs_runtime() 改读 cfs_rq->h_curr，补齐 85570f10a4c6 single-runqueue 转换的漏改；作者审计 fair.c 全部 cfs_rq->curr 引用后确认只有这 2 处仍逐层执行'
    review_outcome: 'Aaron Lu 给整系列 Reviewed-by + Tested-by（单 CPU 绑 nop 可观测到用超配额，打补丁后消失）；无人反对，无人要求改动；09-06 由 Ingo Molnar 收进 tip/sched/urgent，09-07 合入 mainline'
upstream_commit: "88405f0ad1d5c680afe3ea0ce9345fa9e1deaac8"
fixes_commit: "85570f10a4c6"
merged_branch: "tip/sched/urgent (tag sched-urgent-2026-09-06) -> torvalds/linux.git"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "确认两片在自家分支的回合顺序（须先有 single-runqueue/h_curr 转换）；如需 stable 覆盖，可补一份可量化的超用数据回帖"
contribution_opportunities:
  - kind: new_patch
    description: "核对自有分支在引入 single-runqueue/h_curr 转换后，throttle_cfs_rq() 与 distribute_cfs_runtime() 是否同步改用 cfs_rq->h_curr（直接影响 cgroup cpu.max 节流与带宽重分配）"
  - kind: testing
    description: "把 Aaron Lu 的单 CPU nop 观察升级为多层级嵌套配额的自动化回归测试，量化超用比例并回帖"
  - kind: review
    description: "延伸审计 cfs_bandwidth 与 burst 组合路径下是否还有同类漏改点"
source_email_count: 5
related_articles: [sched-20260831-004, sched-20260831-003]
tags:
- cfs
- cgroup
- eevdf
generated_at: '2026-09-07'
---
