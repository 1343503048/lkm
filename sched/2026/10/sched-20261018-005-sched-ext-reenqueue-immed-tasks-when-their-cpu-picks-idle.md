# sched_ext: Reenqueue IMMED tasks when their CPU picks idle

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261017-003：Andrea Righi 发 `sched_ext: Don't report a forced-idle CPU as open for IMMED tasks`——core scheduling 强制某 CPU idle 时 `rq_is_open()` 误报开放，`SCX_ENQ_IMMED` 任务被插进本地 DSQ、parked 在更高类任务之后而不回 BPF 调度器；方案是加 `higher_class_runnable()` 预测 pick、让 `rq_is_open()` 报忙。
- sched-20261018-005（今天）：Tejun Heo review 否决了「预测 pick」方向（重复 core pick 顺序、漏打 tag 的 IMMED 任务自身 cookie 强制 idle 的情形），建议「对 pick 做反应」；Andrea 认同并据此重写为 v2 `Reenqueue IMMED tasks when their CPU picks idle`——CPU pick idle 且本地 DSQ 有 IMMED 任务时，从 `__scx_update_idle()` 触发一次本地 DSQ 重入队，带 `Fixes: 98d709cba319`、`Cc: stable # v7.1+`。

## 背景与问题

（承接 20261017-003）core scheduling 能强制一个 CPU idle、而更高优先级类任务仍在其上 runnable：未打 tag 的 core-wide max 下，不兼容的 pick 被换成 idle 且不尝试找兼容任务。此时 `rq->next_class` 是 idle，`rq_is_open()` 把该 CPU 报为开放，`SCX_ENQ_IMMED` 任务被插进其本地 DSQ、parked 在更高类任务之后，而不是立即回 BPF 调度器另找 CPU。此前的修复思路是「预测」：加 `higher_class_runnable()` 让 `rq_is_open()` 报忙。

Tejun 今天指出「预测」方向的问题：它在 sched_ext 里重复了 core pick 顺序（含 dl_server 次序），脆弱；且漏掉「IMMED 任务自身 cookie 强制 CPU idle」的情形——如打 tag 的 IMMED 任务在 sibling 跑未打 tag 的 RT 任务时，本 CPU 上 ext 之上没有 runnable 任务，预测法抓不到。作者复现：SMT 对两兄弟都设 ext server runtime 为 0，一个未打 tag 的 SCHED_FIFO 任务在一个兄弟上自旋、强制另一个兄弟 idle，两种方式（其上有打 tag 的 SCHED_FIFO 任务 runnable；无更高类任务但有打 tag IMMED 任务）下，插进 forced-idle 兄弟本地 DSQ 的 IMMED 任务整个测试窗口内都 parked、从未被 reenqueue。

## 技术方案

（承接 20261017-003，方案由「预测」改为「反应」）v2 单补丁（`kernel/sched/ext/`）：CPU pick idle 且本地 DSQ 上有 IMMED 任务，就意味着它们没立即跑（无论原因）。`__scx_update_idle()` 在每次 idle pick 上都被调用（task→idle 切换与 idle→idle re-pick 皆然），故从那里调度一次本地 DSQ 重入队，新增内部 `SCX_REENQ_IDLE_PICK` 标志让 `reenq_local()` 跳过 `rq_is_open()`（否则 idle rq 会被报为开放、IMMED 任务留在队头）。修复后 IMMED 任务立即被重入队、由 BPF 调度器放到其他 CPU 上跑。`Fixes: 98d709cba319`（"sched_ext: Implement SCX_ENQ_IMMED"）、`Cc: stable # v7.1+`。

## 版本演进与当前进展

*current_version: v2*。

- 前身（2026-10-17，见 related 003）：`Don't report a forced-idle CPU as open for IMMED tasks`，预测法 + `higher_class_runnable()`。
- v2（2026-10-18，本日）：按 Tejun 建议改为反应法，丢弃 `higher_class_runnable()`，新增 `SCX_REENQ_IDLE_PICK` 标志。当日刚发，暂无回帖。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）对前身 patch 的 review 是本次方案转向的直接来源：他明确指出「这重复了 sched_ext 里的 core pick 顺序（含 dl_server 次序），脆弱」「漏掉 IMMED 任务自身 cookie 强制 idle 的情形」，并提出反应法框架——「CPU pick idle 且本地 DSQ 有 IMMED 任务 = 它们没立即跑」、在 `__scx_update_idle()` 里 `if (idle && unlikely(rq->scx.nr_immed)) scx_schedule_reenq_local(rq, ...)`，并提示 forced idle 之外 `nr_immed` 应为 0。Andrea 认可「Ah, right，打 tag 的 IMMED 任务会卡住……这看起来稳健得多」，随即发 v2 落实。无分歧。

## 合入评估

*likelihood=high*。方案由维护者 Tejun 亲自提出并获作者采纳，方向已收敛；`Fixes:` + `Cc: stable # v7.1+` 表明是 for-7.3-fixes 的正确性修复，且与已应用的 `Don't leave balance callbacks...`（for-7.3-fixes）同族。*blocking_issues*：v2 刚发，Tejun 尚未对 v2 落地形态再给一轮确认。*next_action*：Tejun review v2 后应用到 `sched_ext/for-7.3-fixes`（并随之进 7.3 stable）。

## 效果评估

作者给出复现与消除：两种 forced-idle 场景下 IMMED 任务此前整个测试窗口内 parked、从不 reenqueue；修复后立即被 reenqueue 并由 BPF 调度器放到其他 CPU。无量化延迟数字。

## 我可以参与的点

- `testing`：在 SMT + SCHED_CORE 机器上复现（ext server runtime=0 + 未打 tag SCHED_FIFO 自旋 + 打 tag IMMED 任务），验证 v2 下 IMMED 任务不再 parked，并回归检查 forced-idle 之外 `nr_immed` 保持为 0。
- `review`：`SCX_REENQ_IDLE_PICK` 标志与 `rq_is_open()` 的交互（尤其 forced idle 与真实 idle 的边界）值得复核。

## 参考链接

- v2 补丁：https://lore.kernel.org/all/20261017221924.3908922-1-arighi@nvidia.com/
- Tejun 对前身 patch 的 review：https://lore.kernel.org/all/49d76a6ae49b2e0d5359edc831ffaf60@kernel.org/
- Andrea 认可并转向：https://lore.kernel.org/all/atPpCyLMK3rnvNqF@gpd4/

---
id: sched-20261018-005
date: 2026-10-18
subject: "sched_ext: Reenqueue IMMED tasks when their CPU picks idle"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261017221924.3908922-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261017221924.3908922-1-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo", "Andrea Righi"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261017124749.3608468-1-arighi@nvidia.com>"
    date: 2026-10-17
    summary: "前身 Don't report a forced-idle CPU as open for IMMED tasks：预测法 + higher_class_runnable()"
    review_outcome: "Tejun 否决预测法，建议改为反应法"
  - version: v2
    msgid: "<20261017221924.3908922-1-arighi@nvidia.com>"
    date: 2026-10-18
    summary: "反应法：CPU pick idle 且 nr_immed 时从 __scx_update_idle() 调度本地 DSQ 重入队，新增 SCX_REENQ_IDLE_PICK 标志"
    review_outcome: "当日刚发，暂无回帖"
upstream_commit: null
fixes_commit: "98d709cba319"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["v2 待 Tejun 再确认落地形态"]
  next_action: "Tejun review v2 后应用到 sched_ext/for-7.3-fixes 并进 7.3 stable"
contribution_opportunities:
  - kind: testing
    description: "SMT+SCHED_CORE 复现验证 v2 下 IMMED 任务不再 parked，并回归检查 forced-idle 外 nr_immed 为 0"
  - kind: review
    description: "复核 SCX_REENQ_IDLE_PICK 与 rq_is_open() 在 forced idle 与真实 idle 边界的交互"
generated_at: "2026-10-19T09:00:00"
source_email_count: 4
related_articles: ["sched-20261017-003"]
tags: [sched_ext, core_sched]
---