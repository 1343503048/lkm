---
id: sched-20260806-010
date: '2026-08-06'
title: 'sched_ext: scx_qmap: Add proxy execution support'
series: sched_ext proxy execution（7.3）
type: feature
status: under_review
severity: none
merge_likelihood: high
tags:
- sched_ext
- proxy_execution
- core_sched
authors:
- Andrea Righi <arighi@nvidia.com>
- Tejun Heo <tj@kernel.org>
reviewers:
- Tejun Heo <tj@kernel.org>
related_articles:
- sched-20260805-001
- sched-20260804-001
emails:
- uid-24168@qq-imap
- uid-23945@qq-imap
- uid-23843@qq-imap
- uid-22920@qq-imap
layout: article
---

# sched_ext: proxy execution 系列 review 推进（07/15 转向保守 terminate）

## 摘要

Andrea Righi 的 sched_ext proxy execution 大系列（目标 7.3）在 08-06 继续推进 review 往返，可见对 07/15、14/15、12/15、10/15 的回复。延续 08-05-001 的「reject DSQ 泛化 + 跨类切换阻断」收尾，本日出现一个**重要方向调整**：

- **10/15（24168）**：`scx_reenq_reject()` 泛化 re-enqueue 路径 review 往返——reject DSQ 机制的 move/change 拆分讨论继续。
- **07/15（23945）** — 关键转折：此前 08-05-001 里 Andrea 主张「跨调度类切换不能无条件阻断 proxy donor（RT/DL PI 需要跨类保留）」，Tejun 当时提示用 per-class 能力位泛化。本日 Andrea 在 07/15 的回复中**改弦更张**：鉴于跨类 proxy donor 的语义复杂性与正确性风险，倾向于在 `sched_change_begin()`（类/亲和切换的 guard）里**直接 terminate proxy**（结束代理执行），而不是试图保留 donor 跨类存活。即采用更保守的「在类切换边界结束代理」路径，避开 RT/DL PI 的跨类代理难题。
- **12/15、14/15**：scx 内部状态机与 proxy 生命周期的 review 细节继续打磨。

## 技术细节

07/15 的语义转变（示意）：
```
// 旧（08-05-001 讨论）：跨类切换保留 proxy donor（per-class 能力位）
// 新（本日）：在 sched_change_begin 边界终止代理
sched_change_begin():
    if (task_is_proxy_running(p))
        terminate_proxy(p);   // 结束代理，O 回归自身调度上下文
    ...
```
这意味着 proxy execution 在 sched_ext 下的边界被收紧到「同一调度类内代理」，跨类场景退回非代理执行，规避 RT/DL PI 跨类代理的未决正确性问题。

## 影响与风险

- 影响面：仅 sched_ext 的 proxy execution 内部路径 + `sched_change` guard 交互。
- 风险：低（相对之前更保守）。终止代理比「跨类保留 donor」更容易证明正确，且不影响非 SCX 任务。
- 收益：消除跨类 proxy donor 的 PI 正确性风险，使系列更易合入。

## 评价

从「跨类保留 donor」转向「类边界 terminate」，是 Tejun review 引导下的理性收敛。方向更稳、合入概率高。建议 Andrea 在 v-next 落实 terminate-on-sched_change 并同步更新文档/注释。与 08-05-001 / 08-04-001 同系列延续。
