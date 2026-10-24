---
id: sched-20261024-001
date: 2026-10-24
subject: Sleeping Owner Handling for Proxy Execution (v33)
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261023220431.1106611-1-jstultz@google.com>
lore_url: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
authors:
- John Stultz
- Peter Zijlstra
- K Prateek Nayak
- Shubhang Kaushik (Ampere)
- zhidao su (Xiaomi)
- Hui Su
maintainers_involved:
- Peter Zijlstra
- Andrea Righi
current_version: v33
patch_series:
- version: v32
  msgid: <20260922024117.1514332-1-jstultz@google.com>
  date: 2026-09-22
  summary: 2 补丁：加入无 owner 激活 blocked donor；采纳 Atul 与 Peter guard() 风格整理
  review_outcome: 待 Peter 在两方案间表态
- version: v33
  msgid: <20261023220431.1106611-1-jstultz@google.com>
  date: 2026-10-24
  summary: 扩到 7 补丁：远程 tick 用 donor、无 owner/null mutex 激活、return migration 设 TASK_RUNNING、链回环+深度上限、Brent
    早检测
  review_outcome: Kayra 2/7+6/7 R-b；Peter 质疑 1/7 sched_delayed；Andrea 3/4/7 提 cookie/DL
    记账/offline 问题
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Peter 对 1/7 用 sched_delayed 判据有取舍意见
  - Andrea 指出 7/7 的 SCHED_DEADLINE bw 记账泄漏与 offline cpu 隐患
  - 3/7 短路 return 路径跳过 cookie 校验
  next_action: 作者回应 Peter/Andrea 意见，并补 cover 的 cycle-detection 对比测量
contribution_opportunities:
- kind: review
  description: 针对 Andrea 提出的 DL 带宽记账泄漏 / cookie 校验缺口给出分析或补丁
- kind: testing
  description: 启用代理执行的构建下压测 mutex/futex 阻塞唤醒与链回环路径
- kind: discussion
  description: 补 cover 提到的 sequence-marker 对比测量数据
generated_at: '2026-10-25T01:00:00'
source_email_count: 14
related_articles:
- sched-20260922-002
- sched-20260902-001
tags:
- proxy_execution
title: Sleeping Owner Handling for Proxy Execution (v33)
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-002-sleeping-owner-handling-for-proxy-execution-v32.html">sched-20260922-002</a>（v32）：John Stultz 发出 proxy execution 第 5 阶段「Sleeping Owner Handling」的第 32 版：任务阻塞在 owner 睡眠的 mutex 上时，把 waiter 停用并挂到 owner 的等待表，待 owner 唤醒时在同一 runqueue 重新激活以提升 owner。v32 新增 K Prateek 的「无 owner 时激活 blocked donor」补丁，并在 John 与 K Prateek 两套方案间等 Peter 表态。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-001-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261024-001</a>（今天，v33）：系列扩到 7 补丁，聚合 K Prateek、Shubhang、zhidao su、Hui Su、Peter 等多人修复，新增 proxy 链循环检测（Brent 算法 + 1024 深度上限）、远程 tick 改用 rq->donor，以及 sleeping-owner 路径的一批正确性修复。当天 Peter Zijlstra、Andrea Righi、Kayra Cizmeci 三人密集 review：Kayra 给 2/7、6/7 Reviewed-by，Peter 质疑 1/7 的 sched_delayed 判据，Andrea 在 3/4/7 提出 cookie 校验、DL 带宽记账、offline CPU 等未解决问题。仍属 RFC。

## 背景与问题
（承接 v32）proxy execution 提交路径分 10 个阶段推进：prep → 单 rq 代理 → 简单 donor 迁移 → 优化 donor 迁移 → sleeping owner 处理（当前阶段）→ core-sched 修复 → chain 平衡 → proxy rwsem → proxy futex 等。核心难点：任务阻塞在 mutex 上而 owner 本身在睡眠，此刻无法提升睡眠中的 owner，必须在 owner 唤醒时重新激活挂在其上的 waiter 树；且 waiters 可形成树状结构，树中间任务也可能被唤醒，级联唤醒需额外列表规避递归。v33 无新背景，但把系列从「核心补丁 + 少量延伸」扩为 7 补丁，纳入 PSI 状态、远程 tick、无 owner/无 mutex、return migration、链循环检测等一批边界修复。

## 技术方案
（承接 v32 + 今日 v33）v33 共 7 补丁：

1. **sched/psi: Preserve sleep-persistent PSI flags on off-CPU sleeping dequeues**（`Fixes: c2ae8b0df2d1`，Reported-by David Stevens）：psi_dequeue() 在 `DEQUEUE_SLEEP` 且 `TSK_ONCPU` 已清时把 sleep-persistent 的 `TSK_MEMSTALL` 当迁移整片清掉，导致唤醒时 `TSK_MEMSTALL_RUNNING` 无对应 `TSK_MEMSTALL`、psi.mem.full 超过 psi.mem.some、get_recent_times() 下溢。改为按 psi_task_switch() 的 runnable→sleeping 转换处理。
2. **sched/core: Use the scheduling context for remote ticks**（Shubhang，`Fixes: 7de9d4f94638`）：sched_tick_remote() 改用 rq->donor 取代 rq->curr，因 full dynticks 下 proxy 会使 curr != donor，去掉 WARN_ON_ONCE。
3. **sched/core: Activate blocked donor when no owner is found**（K Prateek，`Fixes: f13beb010e4a`）：mutex 慢路径未观察到 owner（或 null blocked_on/mutex）时唤醒 blocked donor 抢锁，避免 donor 被停用后要等成为 first waiter 才被自然唤醒而中断代理；v33 新增 null mutex 情况。
4. **sched/proxy: Set TASK_RUNNING when shortcutting return migration**（`Fixes: b049b81bdff6`）：return migration 短路直接运行任务前补设 `WRITE_ONCE(p->__state, TASK_RUNNING)`。
5. **sched/proxy: Break cyclic proxy chains by deactivating blocked tasks**（zhidao su）：链回环时清当前 blocked_on 关系并停用该 blocked 任务；`MAX_PROXY_CHAIN_DEPTH 1024` 对齐 rtmutex 的 max_lock_depth。
6. **sched/proxy: Detect cycles in proxy walks earlier**（Hui Su）：把 Brent 检查点状态内联进 owner walk 做早检测，复用已有 owner 解析、无需单独 preflight，不新增 task_struct/rq 状态。
7. **sched/proxy: Add deactivated (sleeping) owner handling to find_proxy_task()**（Peter 原作核心补丁，v5→v33 多轮打磨）：链解析到睡眠 owner 时停用 donor 并挂到 owner，owner 唤醒时再激活。

## 版本演进与当前进展
*current_version: v33*。v32（`<20260922024117.1514332-1-jstultz@google.com>`，2 补丁，09-22）→ v33（`<20261023220431.1106611-1-jstultz@google.com>`，7 补丁，10-24）。v33 相对 v32 的关键扩展：纳入 Shubhang 远程 tick 用 donor、K Prateek 无 owner/null mutex 激活、zhidao su 链深度上限 + 回环停用、Hui Su Brent 早检测；并修复 activate_blocked_waiters() 的 PSI 状态问题，以及「do_activate_blocked_waiter() 显著延迟导致任务越出 affinity mask 执行」的潜在 crasher。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（1/7）：质疑 PSI dequeue 是否非得用 sched_delayed 判断——「Must this really be sched_delayed, that is, cannot p->is_blocked be used here? I'm trying to push sched_delayed into fair.c if at all possible」。
- **Kayra Cizmeci**：2/7 给 *Reviewed-by*（用 donor 更干净、可去掉 WARN_ON_ONCE 与注释）；6/7 给 *Reviewed-by*（亲自验证 Brent 检测在 TA/TB 互锁场景正确），但建议 cover 里「Validation of this trade-off and comparative measurements ... are included in the cover letter」这句要么补结果要么删。
- **Andrea Righi**：3/7 质疑短路 return 路径在中间 owner 上跳过了函数末尾的 `sched_cpu_cookie_match()` 检查（CONFIG_SCHED_CORE 下可能运行未 cookie 校验的任务）；4/7 建议直接复用 `ttwu_do_wakeup(p)`（含 trace_sched_wakeup）而非内联一组易分叉的状态迁移；7/7 提了多处：SCHED_DEADLINE 带宽记账泄漏（`__set_task_cpu()` 跳过 `migrate_task_rq_dl()` 使 old rq 漏 `sub_rq_bw()`、新 rq `add_rq_bw()`）、`ttwu_state_match()` 失败时 owner 的 `task_cpu()` 可能已 offline、以及两处 typo（entitiy/usage her）。

未解决分歧：Peter 对 1/7 的 sched_delayed/is_blocked 取舍、Andrea 的 DL 记账与 cookie 校验缺口，均无作者回应。

## 合入评估
*likelihood=unknown*。仍属 proxy execution 的 RFC 阶段；即便 Peter 已在 LPC 上同意先用「相对简单」的方案，睡 owner 核心补丁 7/7 的复杂度与 Andrea 指出的 DL 带宽/cookie/offline 问题尚未解决，短期内不会进 tip。*blocking_issues*：Peter 对 1/7 判据有取舍意见；Andrea 指出 7/7 的 DL bw 记账泄漏与 offline cpu 隐患；3/7 跳过 cookie 校验。*next_action*：作者回应 Peter/Andrea 意见，7/7 的 DL 记账与唤醒竞态给出方案，并按 Kayra 建议补 cycle-detection 对比测量数据。

## 效果评估
无性能数据，属正确性功能补丁。5/7 提到链回环复现器：修复前 guest 90s vng 超时内无法完成，修复后打印 `sched/pe: deadlock cycle detected, pid 128` 且同 CPU 心跳 kthread 继续运行——属功能验证而非量化收益。

## 我可以参与的点
- *kind: review*：作者明确征求简化建议（7/7 的 locking 尤其别扭），可针对 Andrea 提出的 DL bw 记账泄漏与 cookie 校验缺口给出分析或补丁。
- *kind: testing*：在启用 SCHED_PROXY_EXECUTION 的构建上压测 mutex 阻塞/唤醒与 futex 场景，验证 sleeping owner 路径与链回环处理。
- *kind: discussion*：对 Kayra 提到的「comparative measurements against the sequence-marker approach」提供基准对比数据。

## 参考链接
- v33 cover: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
- Peter 1/7 回帖: https://lore.kernel.org/all/20261024114422.GA6775@noisy.programming.kicks-ass.net/
- K Prateek 替代方案: https://lore.kernel.org/lkml/20260826062901.2137-1-kprateek.nayak@amd.com/
- 前文: <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-002-sleeping-owner-handling-for-proxy-execution-v32.html">sched-20260922-002</a> / <a class="article-ref" href="/lkm/2026/09/02/sched-20260902-001-sleeping-owner-handling-for-proxy-execution-v31.html">sched-20260902-001</a>
