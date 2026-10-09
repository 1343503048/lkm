---
id: sched-20261006-007
date: '2026-10-06'
subject: 'sched/core: Do not touch SMT siblings that have not joined the core yet'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20261006061253.1199941-1-snishika@redhat.com>
lore_url: https://lore.kernel.org/all/20261006061253.1199941-1-snishika@redhat.com/
authors:
- Seiji Nishikawa
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261006061253.1199941-1-snishika@redhat.com>
  date: '2026-10-06'
  summary: pick_next_task/forceidle 的 smt_mask 遍历跳过 rq->core 不同的 CPU
  review_outcome: 发布当日无回帖
related_articles: []
upstream_commit: null
fixes_commit: 3c474b3239f1
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 无维护者 review
  next_action: Peter/core scheduling 侧 review 后进修复通道
generated_at: '2026-10-07T01:00:00'
title: 'sched/core: Do not touch SMT siblings that have not joined the core yet'
layout: article
---

> **subject**：`sched/core: Do not touch SMT siblings that have not joined the core yet`

## TL;DR

Seiji Nishikawa（Red Hat）修复 core scheduling 与 CPU 上线的竞态窗口：新 CPU 上线时，`ap_starting()` 先 `set_cpu_sibling_map()`（把它加进兄弟的 `cpu_smt_mask()`）后 `notify_cpu_starting()`（触发 `sched_core_cpu_starting()` 把 `rq->core` 指向 core leader）——这个顺序是有意的，但两步之间，新 CPU 的 `rq->core` 仍指向自己，而其 `rq->core_enabled` 却早已被 `__sched_core_flip()` 设好（对所有 possible CPU 设置、下线不清）。此时兄弟 CPU 若在 `pick_next_task()` 里遍历 `cpu_smt_mask()`，会对这个尚未入组的新 CPU 调 `update_rq_clock()`/`pick_task()`/改 `core_pick`/`resched_curr()`——而它只持自己的 core 锁、不持新 CPU 的锁，lockdep 报 `update_rq_clock()` 处的 WARNING（syzbot 复现，QEMU 双 vCPU SMT 下约 100 秒必现）。修法：这些循环里跳过 `rq->core` 与本核不同的 CPU（新 helper `sched_core_sibling()`）；持核锁期间该判定结果不会变（`rq->core` 只在持 `sched_core_lock()`——即全 SMT mask rq 锁——或 stop_machine 下变更）。`Fixes: 3c474b3239f1`、`Cc: stable`，syzbot 复现器验证 2 小时无告警。

## 背景与问题

- **触发时序**：CPU 上线 → `set_cpu_sibling_map()`（新 CPU 进入兄弟的 `cpu_smt_mask()`）→ （窗口）→ `sched_core_cpu_starting()`（`rq->core` 指向 leader）。
- **窗口内状态**：新 CPU `rq->core = 自己`，但 `core_enabled` 已置（`__sched_core_flip()` 为所有 possible CPU 设置，offline 不清）；`__rq_lockp()` 返回自己的 `rq->__lock` 而非核宽锁。
- **踩窗者**：兄弟 CPU 的 `pick_next_task()` 遍历 SMT mask 检查所有 CPU——对窗口内的新 CPU 调 `update_rq_clock()`（lockdep 断言锁未持 → WARNING）、改 `rq_i->core_pick`、`resched_curr()`（同样的断言）；`__sched_core_account_forceidle()` 同样遍历。
- **下线侧无此问题**：`remove_siblinginfo()` 与 `sched_core_cpu_dying()` 都在 `take_cpu_down()` 的 stop_machine 里跑，无兄弟能同时在 `pick_next_task()`。
- syzbot 报告：`syz-executor251`，QEMU `-smp 2,sockets=1,cores=1,threads=2`（两 vCPU 为 SMT 兄弟）约 100 秒触发；触发前 debug 打印确认 CPU0 的循环看到 CPU1 的 `rq->core` 指向 CPU1 自己且 `cpu_online(CPU1)==false`。

## 技术方案

补丁（`<20261006061253.1199941-1-snishika@redhat.com>`，3 文件 +21/−0）：

- `kernel/sched/sched.h` 新增 `sched_core_sibling(rq, rq_i)`：判定 `rq_i->core == rq->core`（同一 core 组）。
- `pick_next_task()` 的三个 `for_each_cpu(i, smt_mask)` 循环（选任务/置 core_pick、reschedule 循环、forceidle 之后的循环）与 `__sched_core_account_forceidle()` 的循环：`if (!sched_core_sibling(rq, rq_i)) continue;`——跳过尚未入组（或已离组）的兄弟；reschedule 循环的既有注释本就预期这种情况。
- **判定的稳定性论证**：运行期 `rq->core` 只被 `sched_core_cpu_starting()`/`sched_core_cpu_deactivate()`（持 `sched_core_lock()`，其取整个 SMT mask 的 rq 锁）与 `sched_core_cpu_dying()`（stop_machine 下）改变——持本核锁期间结果不变，无 TOCTOU。
- 未入组的 CPU 自行 pick 自己的任务，不受影响。

## 版本演进与当前进展

- v1（10-06 14:12 北京）首发。syzbot Closes 链接与 `Reported-by` 齐全；QEMU 复现器验证：不打补丁约 100 秒告警、打补丁 2 小时+ 无告警（同一状态仍会出现）。当日无回帖。

## Maintainer 意见与讨论焦点

- **Seiji Nishikawa**（Red Hat，作者）：根因分析完整（上线顺序有意性、core_enabled 生命周期、下线侧对照）+ 判定稳定性论证。
- 无维护者回帖（Peter Zijlstra / core scheduling 侧未现）。
- 焦点：补丁选择「跳过」而非「延迟上线顺序」或「让 core_enabled 跟随 online」——跳过是最小侵入且与既有注释预期一致的方案，但「未入组 CPU 上的任务在核宽决策中被无视」的语义边界值得 review 时确认。

## 合入评估

*likelihood=medium*。syzbot 背书 + `Fixes: 3c474b3239f1` + `Cc: stable` + 复现验证充分；但无维护者 review，且 `3c474b3239f1` 的影响面（所有 core scheduling 用户）意味着回合 stable 需要谨慎核对。*blocking_issues*：无维护者表态。*next_action*：Peter/核心调度侧 review；确认 SD_ASYM/forceidle 路径无其它未守卫的 smt_mask 遍历。

## 效果评估

- 复现验证：QEMU 2 vCPU SMT、syzbot C 复现器——基线约 100 秒触发 lockdep WARNING；补丁后 2 小时以上无告警（同一中间状态仍可观测到，即竞态窗口本身仍存在，只是不再被踩）。
- 无性能数据（跳过分支仅在上线窗口内生效，稳态零成本）。

## 我可以参与的点

- `review`：grep kernel/sched/ 里其它 `for_each_cpu(...smt_mask...)` 遍历（如 `sched_core_share()` 路径），确认没有第四处未加 `sched_core_sibling()` 守卫的核宽遍历。
- `testing`：在真实多核 SMT 硬件上用 CPU 热插拔风暴 + core scheduling 负载复测——syzbot 场景是 2 vCPU，更大拓扑（多 core 多线程）下窗口密度更高。

## 参考链接

- 补丁: https://lore.kernel.org/all/20261006061253.1199941-1-snishika@redhat.com/
- syzbot 报告: https://syzkaller.appspot.com/bug?extid=681e729b2cf0d4860042
