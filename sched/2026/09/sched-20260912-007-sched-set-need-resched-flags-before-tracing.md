# sched: Set need-resched flags before tracing

## TL;DR
Andrea Righi 修复 sched_set_need_resched_tp 在 TIF_NEED_RESCHED 置位前触发、可被 BPF 程序递归重入直至内核栈溢出的问题；Gabriele Monaco 当即指出这与 Sechang Noh 六月的系列是同一修复，Andrea 确认逐行相同并主动撤回——「We can ignore this one and go with Sechang's」。本补丁本身就此终止，真正的修复在 Sechang 的 v3 系列（未入缓存）。后续报道见 sched-20260913-004。

## 背景与问题
commit adcc3bfa8806（"sched: Adapt sched tracepoints for RV task model"）引入的 sched_set_need_resched_tp 在对应线程标志置位之前发出。若 BPF tracepoint 程序在离开 RCU 读临界区时又触发 rcu_read_unlock_special()（需推迟静息态时调 set_need_resched_current()），而 TIF_NEED_RESCHED 尚未置位，tracepoint 会再次发出并无限循环，直至内核栈溢出：`__trace_set_need_resched() → bpf_trace_run3() → rcu_read_unlock_migrate() → rcu_read_unlock_special() → set_need_resched_current() → set_tsk_need_resched() → __trace_set_need_resched()`。

## 技术方案
- set_tsk_need_resched()：tracepoint 使能时先置 TIF_NEED_RESCHED 再发 tracepoint；
- __resched_curr()：本地路径先 set_ti_thread_flag()/set_preempt_need_resched() 再发 tracepoint；远程路径保留 set_nr_and_not_polling() 的返回值，先置标志、发 tracepoint、再按返回值决定是否发 IPI——保证 tracing 始终先于 IPI 投递、且观察到已更新的标志。

## 版本演进与当前进展
current_version: v1（msgid `<20260911213300.1305763-1-arighi@nvidia.com>`，09-12 05:33 入缓存），随即被撤回。

- 09-12 05:33：Andrea 独立发出修复（Fixes: adcc3bfa8806，include/linux/sched.h + kernel/sched/core.c，+9/-3）；
- 09-12 15:13：Gabriele Monaco 指出与 2026-06-27 Sechang Noh 的补丁（lore 20260627081657.499781-1-rhkrqnwk98@gmail.com）基本相同、疑似被遗忘，且当时讨论的疑点不构成合并阻碍；
- 09-12 15:34：Andrea 确认「**exactly** the same fix! I hit the same issue and missed Sechang's series. There's also a v3: 20260630084750.2792851-1-rhkrqnwk98@gmail.com. We can ignore this one and go with Sechang's. Sorry for the noise.」

## Maintainer 意见与讨论焦点
- **Gabriele Monaco**：发现重复实现并指出 Sechang 原系列遗留的讨论疑点不构成阻塞；
- **Andrea Righi**：确认重复、撤回自己的版本、指向 Sechang v3；
- 无分歧。真正的评审对象是 Sechang Noh 的 v3 系列（本日缓存未收到，其修复内容与演进未获取到）。

## 合入评估
likelihood=low（对本补丁）：已被作者主动 superseded，合入可能性为零；问题本身的修复前景取决于 Sechang v3 的收取情况。blocking_issues：Sechang v3 系列的内容、review 状态与卡点均未入缓存，未获取到。next_action：跟踪 Sechang Noh v3 的评审与收取；对照本补丁 diff 可作为该系列修复正确性的独立参照（两者经 Andrea 确认等价）。

## 效果评估
无实测数据：补丁说明给出的是递归路径推演（栈溢出机理），无 BPF+RV 场景的复现日志或溢出样本；Gabriele 的评论亦未附复现结果。

## 我可以参与的点
- kind=review：对照 Sechang v3 与本补丁（Andrea 已确认等价）核对其最终形态是否覆盖 set_tsk_need_resched() 与 __resched_curr() 两个入口、远程 IPI 路径的顺序是否一致。
- kind=testing：在开 sched_set_need_resched_tp + BPF attach 的环境构造 rcu_read_unlock_special() 触发场景，验证修复前后是否复现递归（本线程自始至终没有实测复现）。

## 参考链接
- 本补丁（已撤回）：https://lore.kernel.org/all/20260911213300.1305763-1-arighi@nvidia.com/
- Gabriele 的发现：https://lore.kernel.org/all/71619AD0-A163-40DA-94B1-39052E808DDC@redhat.com/
- Andrea 的撤回确认（含 Sechang v3 链接）：https://lore.kernel.org/all/aqUAaH6fSMhHF0EF@gpd4/
- Sechang Noh v3：https://lore.kernel.org/all/20260630084750.2792851-1-rhkrqnwk98@gmail.com/
- Fixes 指向：adcc3bfa8806（"sched: Adapt sched tracepoints for RV task model"，hash 取自补丁正文）

---
id: sched-20260912-007
subject: 'sched: Set need-resched flags before tracing'
date: '2026-09-12'
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: '<20260911213300.1305763-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260911213300.1305763-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260911213300.1305763-1-arighi@nvidia.com>'
    date: 2026-09-12
    summary: 'set_tsk_need_resched()/__resched_curr() 在发 sched_set_need_resched_tp 前先置 TIF，防 BPF 递归重入致栈溢出；Fixes adcc3bfa8806。'
    review_outcome: 'Gabriele 指出与 Sechang Noh 06-27 补丁相同；Andrea 确认 exactly the same fix 并撤回，改用 Sechang v3（2026-06-30）。'
upstream_commit: null
fixes_commit: 'adcc3bfa8806'
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '本补丁已被作者主动撤回（与 Sechang v3 重复）'
    - 'Sechang v3 的 review 状态与卡点未入缓存，未获取到'
  next_action: '跟踪 Sechang Noh v3 的收取；以本补丁 diff 作等价性参照'
contribution_opportunities:
  - kind: review
    description: '核对 Sechang v3 最终形态覆盖两个入口且远程 IPI 顺序一致'
  - kind: testing
    description: 'BPF+RV 场景构造递归，验证修复前后是否复现栈溢出'
generated_at: '2026-09-14T12:40:00'
source_email_count: 3
related_articles:
  - 'sched-20260913-004'
tags:
  - preempt
  - crash
---
