# sched/core: Do not touch SMT siblings that have not joined the core yet

## TL;DR

Seiji Nishikawa 的修复针对 core scheduling 里 `pick_next_task()` 会扫描尚未 join core 的 SMT 兄弟 CPU（其 `core_pick` 为 NULL）而导致的空指针崩溃。Peter Zijlstra 认可其思路、给出 `for_each_core_cpu_wrap` 的封装建议；Seiji 实测 Peter 的初版建议仍会复现 KASAN crash（约 60 秒），改用封装后的版本在约 1250 秒 / 6100 次 CPU offline/online 循环中不再触发。Peter 表示「已经拿到，等 0-day 把当前一批 sched/urgent 过完」，合入概率高。

## 背景与问题

core scheduling（core_sched）下，`pick_next_task()` 会遍历一个核内（SMT 域）的所有兄弟 CPU 做强制 idle 与任务选择。在 CPU hotplug 的窗口期，一个 SMT 兄弟尚未完成 `join core` 时它的 `core_pick` 仍为 NULL，此时被选中参与比较/强制 idle 就会解引用 NULL 指针。syzbot 的 C reproducer 可稳定触发：CPU 上线瞬间，`__schedule+0x439a` 处空指针 GPF（KASAN 报 null-ptr-deref）。替该 bug 的同时还有 Ahmed 的另一版补丁。

## 技术方案

Seiji 的方案是在 `pick_next_task()` 的多处遍历里改用 `for_each_cpu_and(i, smt_mask, cpu_online_mask)`（首次遍历用 `cpu_online()`）过滤掉尚未 join core 的 SMT 兄弟，并在 `__sched_core_account_forceidle()` 里做同样处理。Peter 反馈「四处在做同一件事，建议封装起来」，给出用 `for_each_core_cpu_wrap()` 替代的写法（并移除 `smt_mask` 局部变量）。Seiji 采纳并验证。

## 版本演进与当前进展

*current_version: v1（RESEND）*。原始 `[PATCH RESEND]` 的 msgid 未出现在当日缓存中（当日仅含回帖）。今日进展：Peter 比较了 Ahmed 与 Seiji 两版、给出封装建议；Seiji 先验证 Peter 的朴素版本仍 crash（满足「把窗口加宽 mdelay(2) 后 60 秒即崩」），再验证封装版本 1250 秒无告警。Peter 表示已收下、等 0-day 放行。

## Maintainer 意见与讨论焦点

Peter Zijlstra 明确倾向 Seiji 的版本（「更一致」），核心意见是「不要在同一处逻辑重复四遍，封装成 `for_each_core_cpu_wrap`」。无反对意见；Ahmed 的替代版本被 Peter 的偏好所取代。

## 合入评估

*likelihood=high*。维护者已给出明确偏好与封装建议，作者已完成验证，Peter 表示「I have it」，仅等 0-day 对当前 sched/urgent 批量的测试放行。*blocking_issues*：暂无实质性阻塞，仅剩流程性等待。*next_action*：作者确认封装版本即可，由 Peter 收取入 sched/urgent。

## 效果评估

Seiji 在 v7.4-rc1 + syzbot C reproducer 上验证：Peter 的朴素版本（两次遍历间加 mdelay(2) 加宽窗口、二次遍历 NULL core_pick 时 pr_warn_once）在 CPU1 上线后约 60 秒复现空指针 GPF；`for_each_core_cpu_wrap` 封装版本在约 1250 秒（约 6100 次 CPU1 offline/online 循环）内告警未触发。

## 我可以参与的点

- **testing**：在开核（SMT/hyperthreading）平台配合 CPU hotplug 压测复跑，确认封装版本在更多拓扑下稳定。
- **review**：对比 Ahmed 补丁与本修复的行为差异，确认 `for_each_core_cpu_wrap` 不会漏掉应参与强制 idle 的 CPU。

## 参考链接

- 原始 [PATCH RESEND] 的 msgid 未获取到（当日缓存仅含回帖，线程根 msgid 无法追溯）。
- Peter 的封装建议回帖: https://lore.kernel.org/all/20261105101018.GM1813469@noisy.programming.kicks-ass.net/

---
id: sched-20261105-004
date: 2026-11-05
subject: "sched/core: Do not touch SMT siblings that have not joined the core yet"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/20261105101018.GM1813469@noisy.programming.kicks-ass.net/"
authors: [Seiji Nishikawa]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-11-05
    summary: "RESEND：过滤未 join core 的 SMT 兄弟，避免 pick_next_task 空指针。"
    review_outcome: "Peter 建议 for_each_core_cpu_wrap 封装，封装版 1250s 无复现。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 0-day 放行后由 Peter 收入 sched/urgent"
contribution_opportunities:
  - kind: testing
    description: "在开核平台 + CPU hotplug 压测复跑，验证更多拓扑下稳定"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 4
related_articles: []
tags: [core_sched, crash]
---