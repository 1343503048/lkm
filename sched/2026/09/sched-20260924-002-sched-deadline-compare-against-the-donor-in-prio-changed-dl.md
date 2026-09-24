# sched/deadline: Compare against the donor in prio_changed_dl()

## TL;DR
Zhan Xusheng 的一致性修复：`prio_changed_dl()` 的 else 分支询问「p 是否应抢占当前调度上下文」，在 proxy execution 下该上下文是 `rq->donor`，但代码仍与 `rq->curr` 比较。补丁把它改为与 `rq->donor` 比较，与同 commit 已修好的 `prio_changed_rt()` 对齐。作者声明无行为变化意图，并在 `CONFIG_SCHED_PROXY_EXEC` 开/关两种配置下验证（关闭时 `build_policy.o` 字节级一致）。本日新发、无 review。

## 背景与问题
commit `af0c8b2bf67b`（"sched: Split scheduler and execution contexts"）把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）拆分后，`prio_changed_dl()` 只在 dispatch 条件处改用 `task_current_donor()`，而 else 分支的抢占判定仍比较 `rq->curr`。在 proxy execution 下，`rq->curr` 可能是「借用 donor 参数运行的 mutex owner」，与真正决定抢占关系的 donor 不是同一个任务，比较对象用错。同一 commit 已经把 `prio_changed_rt()` 的对应分支改成 `rq->donor`，deadline.c 这里被遗漏。

## 技术方案
把 `prio_changed_dl()` else 分支的判定从 `!dl_task(rq->curr) || dl_time_before(p->dl.deadline, rq->curr->dl.deadline)` 改为与 `rq->donor` 比较。作者明确「无行为变化意图」：donor 是「最早 deadline 实体」，donor 测试蕴含 curr 测试，当前代码只是多加了不必要的 reschedule；该顺序来自 pick 而非此处。改动 2 行（kernel/sched/deadline.c）。

作者还指出同 commit 在 deadline.c 遗漏的另外两处（都在某次基于 `rq->donor` 的 `update_curr()` 调用下方几行）：

- `dl_server_timer()`：`if (!dl_task(dl_se->rq->curr) || dl_entity_preempt(dl_se, &dl_se->rq->curr->dl))`
- `dl_server_start()`：`if (!dl_task(dl_se->rq->curr) || dl_entity_preempt(dl_se, &rq->curr->dl))`

作者因该区域正在围绕 `dl_rq->curr` 重做而暂未改这两处，表示「say the word and I will send them too」。

## 版本演进与当前进展
v1 本日发出（`<20260924121213.106673-1-zhanxusheng@xiaomi.com>`，base-commit `a9b3c7570564`），暂无 review 回复。

## Maintainer 意见与讨论焦点
本日无维护者回复。作者自行声明并验证了「无行为变化」：`CONFIG_SCHED_PROXY_EXEC=y` 与 `=n` 均构建通过；`=n` 时两个 rq 成员是匿名 union，`build_policy.o` 字节级一致。无争议点。

## 合入评估
*likelihood=medium*。一致性修复、风险低（作者声明无行为变化且 `=n` 构建字节级一致），但为 proxy-execution 相关改动的早期审查，且是否顺带修掉 `dl_server_*()` 两处遗漏点尚未定。*blocking_issues*：无明确反对；待维护者确认「先只改 prio_changed_dl 还是连同 dl_server 两处一起」。*next_action*：维护者表态是否要作者把 `dl_server_timer()`/`dl_server_start()` 两处一并补上。

## 效果评估
无性能数据。作者给出的是正确性/一致性论证与构建验证（`=n` 下 `build_policy.o` 字节级一致），未见运行时测试。

## 我可以参与的点
- kind=new_patch：作者已明确指出 `dl_server_timer()`/`dl_server_start()` 两处同类遗漏，可按同方式补上并发后续补丁。
- kind=review：核对 `rq->donor` 比较在 proxy execution 下的语义是否与 `prio_changed_rt()` 完全对齐。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260924121213.106673-1-zhanxusheng@xiaomi.com/

---
id: sched-20260924-002
date: '2026-09-24'
subject: 'sched/deadline: Compare against the donor in prio_changed_dl()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260924121213.106673-1-zhanxusheng@xiaomi.com>'
lore_url: 'https://lore.kernel.org/all/20260924121213.106673-1-zhanxusheng@xiaomi.com/'
authors:
  - 'Zhan Xusheng'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260924121213.106673-1-zhanxusheng@xiaomi.com>'
    date: '2026-09-24'
    summary: 'prio_changed_dl 抢占判定从 rq->curr 改为 rq->donor'
    review_outcome: '暂无 review 回复'
upstream_commit: null
fixes_commit: 'af0c8b2bf67b'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '维护者表态是否一并修 dl_server_timer/dl_server_start 两处遗漏'
contribution_opportunities:
  - kind: new_patch
    description: '按同方式补上 dl_server_timer()/dl_server_start() 两处遗漏'
  - kind: review
    description: '核对 rq->donor 比较语义与 prio_changed_rt 对齐'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - deadline
  - proxy_execution
---