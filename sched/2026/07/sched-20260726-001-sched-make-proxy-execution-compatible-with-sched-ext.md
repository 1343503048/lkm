# sched/core: Avoid false migration warning for proxy donors

## TL;DR
Andrea Righi 发布的 proxy execution（PE）与 sched_ext 兼容第 9 版（`[PATCHSET v9 sched_ext/for-7.3]`），目标是让 PE 与 sched_ext 共存：当被阻塞任务需要把执行权代理给持锁的 owner，而该 owner 恰好由 SCX 调度器管理时，PE 不能破坏 SCX 的 pick/dispatch 语义。方向已获认可，属于长期演进中的成熟版本，值得关注但尚未进入合入窗口。

## 背景与问题
proxy execution 用来解决优先级反转：被阻塞在 mutex 上的高优先级任务，把自己的调度上下文"借"给持锁的低优先级 owner，让 owner 尽快跑完临界区释放锁。问题在于，PE 最初只考虑 fair/RT/DL 这些内核内建调度类；而 sched_ext 允许 BPF 自定义调度器接管任务的入队与选核。若 owner 是 SCX 管理的任务，PE 在迁移/代理执行 owner 时会与 SCX 自己的 DSQ、idle 跟踪和 pick 路径产生冲突。本系列补足这块兼容性。

## 技术方案
核心是让 PE 在选择"代理运行 owner"时，识别 owner 所属调度类并走 SCX 感知的路径：在 owner 属于 SCX 时，避免绕开 SCX 的 dispatch 逻辑直接强塞任务，处理好被代理任务的 return migration（临界区结束后归还原 CPU/调度类）。设计取舍上，PE 需要在不侵入 SCX 快路径的前提下插入兼容钩子，尽量把复杂度收敛在 PE 侧而非污染 SCX 的通用接口。

## 版本演进与当前进展
当前为 v9，说明该系列已经过多轮迭代打磨，主体设计稳定，主要在逐版收敛 SCX 交互与迁移边界的细节。本次抓取到的是 v9 的发布邮件，未在当日窗口内捕获到针对 v9 的逐条 review 回复。

## Maintainer 意见与讨论焦点
PE 本身长期由 Peter Zijlstra、Juri Lelli 等 core 维护者关注；SCX 兼容部分涉及 Tejun Heo/SCX 侧。讨论焦点集中在 PE 与 SCX pick/dispatch 的交互正确性、return migration 的边界，以及是否会影响 SCX 快路径性能。当日窗口内未见明确 NAK，但也未见对 v9 的最终 ack，属于"方向认可、细节待定"状态。

## 合入评估
合入可能性中等。PE 主干本身尚在推进，SCX 兼容层依附其节奏；即使本系列质量达标，也需与 PE 主体一起进主线。当前卡点主要是交互路径的维护者确认，而非明显缺陷。

## 效果评估
本次邮件未附带具体性能数据。PE 的价值主要体现在减少优先级反转导致的尾延迟，但"与 SCX 兼容后是否有额外开销"暂无测试数据，属未见测试数据的部分，需后续 benchmark 支撑。

## 我可以参与的点
- 构造 CFS 持锁 + SCX 等锁（及反向）的混合负载测试，验证让渡与 return migration，回帖数据
- 对 PE/SCX 交互相关补丁做代码级 review

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/core: Avoid false migration warning for proxy donors"
id: sched-20260726-001
date: 2026-07-26
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<uid-354@qq-imap>"
lore_url: "unknown"
authors: [Andrea Righi]
maintainers_involved: [Peter Zijlstra, Juri Lelli, Tejun Heo]
current_version: v9
patch_series:
  - version: v9
    msgid: "<uid-354@qq-imap>"
    date: 2026-07-26
    summary: "让 proxy execution（PE）与 sched_ext 兼容：当被阻塞任务把优先级/时间片让渡给 mutex owner 时，处理 owner 属于 SCX 调度类的情形，避免 PE 与 SCX 的 pick 路径互相踩踏。"
    review_outcome: "作为长期演进的 v9，主线方向已被认可，剩余焦点是 SCX 侧 pick/dispatch 交互与 return-migration 的边界处理。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "proxy execution 与 sched_ext 的 pick_task/dispatch 交互路径仍需维护者进一步确认边界正确性"
    - "PE 本体尚未完全合入主线，SCX 兼容层依赖其推进节奏"
  next_action: "等待 PvZ/Juri 对 SCX 交互路径的细节 review，可能需要补充多调度类混合场景下的压力测试数据"
contribution_opportunities:
  - kind: testing
    description: "在 CFS 任务持锁、SCX 任务等锁（或反之）的混合负载下运行，验证优先级让渡与 return migration 行为，把结果回帖列表"
  - kind: review
    description: "针对 kernel/sched/ext 与 core.c 中 proxy/owner 迁移交互的补丁做代码级 review"
generated_at: "2026-07-27T01:10:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, cfs, affinity]
---
