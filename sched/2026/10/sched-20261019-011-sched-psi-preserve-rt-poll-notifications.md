# sched/psi: Preserve RT poll notifications

## TL;DR

Hui Su 发往 sched/psi 的两补丁修复：特权 RT trigger 注册会先吞掉 pressure 记账、独立 worker 关闭路径会让 rate-limit 内的 pending 事件悬空。补丁 1 保留注册时的 pressure 变化并在到期评估后推进 consumed total；补丁 2 从 trigger 列表推导 pending deadline，投递后回到 idle。当日新发（与同日 007 `sched/psi: Keep average work scheduled for pending notifications` 同作者、方向相关但针对不同聚合器），暂无回帖。

## 背景与问题

特权 RT trigger 注册时先采样 per-cpu pressure，可能在既有 rtpoll worker 消费之前就吞掉记账，导致既有 trigger 漏数；另一条独立的 worker shutdown 路径会在 rate-limit 事件仍 pending 时让活动轮询过期、worker 变 idle，pending 通知不投递。带 `Fixes: e6df4ead85d9 ("psi: fix possible trigger missing in the window")`。

## 技术方案

两补丁（`kernel/sched/psi.c`，+157/−50）：

- **1/2 Preserve pressure accounting across RT trigger registration**：创建特权 trigger 时保留既有 trigger 的状态变化，注册采样之后才初始化新 trigger 窗口（不把注册前的 pressure 计进去）；每次评估到期无论采样有无状态变化都触发 trigger，评估后推进 `rtpoll_total` 避免重复计数。
- **2/2 Deliver pending RT poll events after polling expires**：从 trigger 列表计算 pending deadline（不再在 `psi_group` 存重复 deadline），保留 pending trigger 窗口、在被观察压力回归时恢复主动轮询，通知投递后回到 idle。

## 版本演进与当前进展

*current_version: v1*。两补丁当日新发（`<20261019104700.3296133-1-sh_def@163.com>`），暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无回帖。潜在评审点（无人提出）：新增 `rtpoll_pending_states` 字段与「从 trigger 列表推导 pending deadline」是否引入新的窗口/竞态。

## 合入评估

*likelihood=unknown*。改动集中在 psi.c、带 KUnit + QEMU 复现数据，但当日无 review，且与同作者 007 单补丁存在 psi.c 上的改动重叠，需要作者说明两系列间的关系与合并方式。*blocking_issues*：无 review、与 007 的 psi 改动关系待澄清。*next_action*：等 PSI 维护者（Johannes Weiner）review，并与 007 协调。

## 效果评估

作者测试：x86_64 KASAN/lockdep KUnit 候选 PSI 10/10 通过（基线 1/10）、refcount 4/4、无 KASAN 报告；QEMU cgroup PSI_POLL：基线第二次长事件在 2500ms 仍未出现（worker 日志 `pending=1`、`timer_pending=0`），候选在 2004.4ms 投递第二次事件、pending 清除、worker 回 idle，两轮静默期 pressure 均为 0、无意外第三次事件。

## 我可以参与的点

- `testing`：在 cgroup v2 PSI_POLL 真实负载下复现「注册吞记账」「pending 事件悬空」并验证两补丁分别修复。
- `review`：复核 2/2 从 trigger 列表推导 pending deadline 的正确性与竞态、以及 1/2 注册采样时序。

## 参考链接

- 封面信：https://lore.kernel.org/all/20261019104700.3296133-1-sh_def@163.com/

---
id: sched-20261019-011
subject: "sched/psi: Preserve RT poll notifications"
date: 2026-10-19
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261019104700.3296133-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20261019104700.3296133-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261019104700.3296133-1-sh_def@163.com>"
    date: 2026-10-19
    summary: "两补丁：保留注册时 pressure 记账并推进 consumed total；从 trigger 列表推导 pending deadline、投递后回 idle"
    review_outcome: "暂无回帖"
upstream_commit: null
fixes_commit: "e6df4ead85d9"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无 review", "与同日 007 的 psi 改动关系待澄清"]
  next_action: "等 PSI 维护者 review，与 007 协调后的合并方式"
contribution_opportunities:
  - kind: testing
    description: "cgroup v2 PSI_POLL 负载下复现并验证两补丁"
  - kind: review
    description: "复核 pending deadline 推导正确性/竞态与注册采样时序"
generated_at: "2026-10-20T01:30:00"
source_email_count: 3
related_articles: []
tags: [psi]
---