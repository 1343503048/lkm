---
id: sched-20261026-006
date: 2026-10-26
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
  review_outcome: Kayra 2/7+6/7 R-b、5/7 补问 Fixes；Peter 质疑 1/7；Andrea 3/4/7 提问题；K Prateek
    今日对 1/3/4/7 深度 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Peter 对 1/7 sched_delayed 判据有取舍意见
  - Andrea 指出 7/7 DL bw 记账泄漏与 offline cpu 隐患
  - K Prateek 今日新增 7/7 TASK_WAKING 竞态与 dl_non_contending 判据疑问
  next_action: 作者回应 7/7 竞态与 DL 带宽问题，补 5/7 Fixes 标签与 cover 对比测量
contribution_opportunities:
- kind: review
  description: 核对 7/7 的 TASK_WAKING 竞态与 dl_non_contending 判残带宽是否充分
- kind: testing
  description: 启用代理执行的构建下压测 mutex/futex 阻塞唤醒与链回环路径
- kind: discussion
  description: 补 cover 提到的 sequence-marker 对比测量数据
generated_at: '2026-10-27T01:00:00'
source_email_count: 7
related_articles:
- sched-20260922-002
- sched-20261024-001
- sched-20261025-010
tags:
- proxy_execution
title: Sleeping Owner Handling for Proxy Execution (v33)
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-002-sleeping-owner-handling-for-proxy-execution-v32.html">sched-20260922-002</a>（v32）：John Stultz 发出 proxy execution 第 5 阶段「Sleeping Owner Handling」第 32 版：任务阻塞在 owner 睡眠的 mutex 上时，把 waiter 停用并挂到 owner 的等待表，待 owner 唤醒时在同一 runqueue 重新激活以提升 owner。v32 新增 K Prateek 的「无 owner 时激活 blocked donor」补丁，并在 John 与 K Prateek 两套方案间等 Peter 表态。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-001-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261024-001</a>（v33）：系列扩到 7 补丁，聚合 K Prateek、Shubhang、zhidao su、Hui Su、Peter 等多人修复，新增 proxy 链循环检测（Brent 算法 + 1024 深度上限）、远程 tick 改用 rq->donor，以及 sleeping-owner 路径一批正确性修复。当天 Peter Zijlstra、Andrea Righi、Kayra Cizmeci 密集 review：Kayra 给 2/7、6/7 Reviewed-by，Peter 质疑 1/7 的 sched_delayed 判据，Andrea 在 3/4/7 提 cookie 校验、DL 带宽记账、offline CPU 等未解决问题。仍属 RFC。
- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-010-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261025-010</a>：Kayra Cizmeci 对 5/7（链循环停用）补问是否缺 `Fixes` 标签，给出建议 commit `7de9d4f94638`。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-006-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261026-006</a>（今天）：K Prateek Nayak 密集 review（7 封），覆盖 1/7、3/7、4/7、7/7；Zhan Xusheng 补 1/7 一处 PSI worker wake_clock 疑问。核心新问题：7/7 的 sleeping-owner 处理在 `rq_lock`+RCU 下 get/put 是否必要、`TASK_WAKING` 与激活间的竞态、以及 DL 带宽用 `dl_non_contending` 判断残留带宽是否充分（问 Juri/Peter）。仍属 RFC。

## 背景与问题
（承接 v32/v33）proxy execution 提交路径第 5 阶段处理「任务阻塞在 mutex 上而 owner 在睡眠」：需在 owner 唤醒时重新激活挂在其上的 waiter 树，且 waiter 树可嵌套、需额外列表规避级联递归。v33 把系列扩为 7 补丁，纳入 PSI 状态、远程 tick、无 owner/无 mutex、return migration、链循环检测等边界修复。今日无新背景，为 7/7 核心补丁及 1/3/4 补丁的深度 review。

## 技术方案
（承接 v32 + v33）v33 共 7 补丁：

1. **sched/psi: Preserve sleep-persistent PSI flags on off-CPU sleeping dequeues**（`Fixes: c2ae8b0df2d1`）
2. **sched/core: Use the scheduling context for remote ticks**（Shubhang，`Fixes: 7de9d4f94638`）
3. **sched/core: Activate blocked donor when no owner is found**（K Prateek，`Fixes: f13beb010e4a`）
4. **sched/proxy: Set TASK_RUNNING when shortcutting return migration**（`Fixes: b049b81bdff6`）
5. **sched/proxy: Break cyclic proxy chains by deactivating blocked tasks**（zhidao su）
6. **sched/proxy: Detect cycles in proxy walks earlier**（Hui Su）
7. **sched/proxy: Add deactivated (sleeping) owner handling to find_proxy_task()**（Peter 原作核心补丁，v5→v33 多轮打磨）

今日无代码变更，为 review 交锋：K Prateek 在 1/7 建议「blocked donor 入睡需补设 PSI flags（做 `psi_sched_switch()` 漏掉的事）、可用 `DEQUEUE_DELAYED` 早退」；在 4/7 建议「`__ttwu_do_wakeup()` 收拢状态迁移，避免 sched_wakeup 无 sched_waking 成对出现」；在 7/7 质疑「rq_lock+RCU 下 get/put 是否必要、应只需 load acquire」并给出一个 `TASK_WAKING`/`ttwu_do_activate()` 与 `do_activate_blocked_waiter()` 的潜在乱序竞态。

## 版本演进与当前进展
*current_version: v33*（`<20261023220431.1106611-1-jstultz@google.com>`）。当日无新版本，进展为 K Prateek 与 Zhan 的深度 review。

## Maintainer 意见与讨论焦点
当日无维护者（Peter/Andrea）新回帖，但 K Prateek 的意见直指 7/7 核心补丁的正确性：

- **K Prateek Nayak（1/7）**：给 nits——建议把变量声明上移、用单一 `psi_task_change(p, clear, set)` 收拢并去掉 early return；另回 Peter 此前的 sched_delayed 质疑：「blocked donor 入睡需要补设 PSI flags（补 `psi_sched_switch()` 漏掉的），而 `p->se.sched_delayed` 任务虽已设好这些 indicator、仍可能从 `sched_change_begin()` 的 `dequeue_task(SLEEP|DELAYED)` 到达此处——这些情况 dequeue flags 会带 `DEQUEUE_DELAYED`，可直接用它早退」。
- **Zhan Xusheng（1/7）**：`psi_task_switch()` 在入睡任务是 `psi_avgs_work()` worker 时也会清 `wake_clock`，防止 worker 重 arm 自己的工作；但 `psi_task_change()` 恒传 `wake_clock=true`，该检查在此丢失。worker 可因持 `group->avgs_lock` 睡眠而阻塞在 sleeping owner 上、经此分支出队。代价是多一个聚合周期而非 ping-pong，但会让平均时钟在 idle 时不停转。问：该分支是否也应做 `PF_WQ_WORKER` 检查？
- **K Prateek Nayak（3/7）**：回 Andrea——「你说得对，应把所有 `return p` 收拢到 `sched_cpu_cookie_match()` 检查」。
- **K Prateek Nayak（4/7）**：回 Andrea 的 `ttwu_do_wakeup()` 复用建议——「好主意，但发 `sched_wakeup` trace 而没有对应的 `sched_waking` trace 会坑到某些 tracing 脚本；有个 `__ttwu_do_wakeup()` 来收拢任务状态迁移确实更好」。
- **K Prateek Nayak（7/7，两封）**：(1) 质疑为何 `p->dl.dl_non_contending` 不足以判断 prev CPU 是否残留带宽（自 commit `209a0cbda7a0` 起如此），列了 non-contending 的几种来源并问 Juri/Peter「是否漏了什么微妙之处」；(2) 指出 sleeping-owner 处理里「rq_lock 下 + RCU 保护，看到 `p->sleeping_owner` 时 get/put 可能没必要、只需 load acquire」；并给出一段 `p->__state = TASK_WAKING` 与 `do_activate_blocked_waiter()` 的乱序时序，担心「任务被激活的同时又被挂到 sleeping owner 队列」，建议把这些检查也移入 `p->blocked_lock` 内（多 4 个 loads、代价可接受）、并把某处换成 `wakeup_preempt()`。他同时说「有足够防御机制、正确性上大概率无碍，但技术上可能发生，值得指出」。

未解决分歧：Peter 对 1/7 的 sched_delayed/is_blocked 取舍、Andrea 的 DL 记账/cookie/offline、以及今日新增的 7/7 sleeping-owner 竞态与 DL 带宽判据——作者均未回应。

## 合入评估
*likelihood=unknown*。仍属 proxy execution 的 RFC 阶段；K Prateek 今日对 7/7 核心补丁提出「激活/挂队列竞态」与「DL 带宽判据」两处实质疑问，作者尚未回应。*blocking_issues*：Peter 对 1/7 判据有取舍；Andrea 指出 7/7 DL bw 记账泄漏/offline 隐患；K Prateek 今日新增 7/7 的 TASK_WAKING 竞态与 dl_non_contending 判据疑问。*next_action*：作者回应 K Prateek/Peter/Andrea 的 7/7 竞态与 DL 带宽问题，并补 5/7 的 Fixes 标签与 cover 的 cycle-detection 对比测量。

## 效果评估
无性能数据，属正确性功能补丁。5/7 链回环复现器此前已示功能验证（修复前 90s 超时内无法完成，修复后打印 cycle detected 且心跳 kthread 继续运行）。

## 我可以参与的点
- *kind: review*：核对 K Prateek 提出的 7/7「`TASK_WAKING` 与 `do_activate_blocked_waiter()` 竞态」是否真可发生、以及 DL 带宽用 `dl_non_contending` 判残留是否充分（他明确向 Juri/Peter 求证）。
- *kind: testing*：启用 `SCHED_PROXY_EXECUTION` 的构建上压测 mutex/futex 阻塞唤醒与链回环路径。
- *kind: discussion*：补 cover 提到的 sequence-marker 对比测量数据。

## 参考链接
- v33 cover: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
- K Prateek 7/7 竞态回帖: https://lore.kernel.org/all/9847c389-3014-4c7c-a1dc-f41de2ce17d3@amd.com/
- K Prateek 7/7 DL 带宽回帖: https://lore.kernel.org/all/267d3f71-7f60-48d2-b8dc-bf87f403b94f@amd.com/
- K Prateek 1/7 PSI 回帖: https://lore.kernel.org/all/58521a9f-2f05-4176-8b14-96c7b5f0e212@amd.com/
- Zhan Xusheng 1/7 PSI worker 回帖: https://lore.kernel.org/all/20261026051605.1997313-1-zhanxusheng1024@gmail.com/
- 前文: <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-010-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261025-010</a> / <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-001-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261024-001</a> / <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-002-sleeping-owner-handling-for-proxy-execution-v32.html">sched-20260922-002</a>
