---
id: sched-20261030-020
date: 2026-10-30
subject: Sleeping Owner Handling for Proxy Execution (v33)
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261023220431.1106611-1-jstultz@google.com>
lore_url: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
authors:
- John Stultz
maintainers_involved:
- Tejun Heo
current_version: v33
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 系列整体仍属 RFC，其余补丁争议未解
  - 1/7 是否拆独立提交需作者/维护者决定
  next_action: 可考虑将 1/7 作为独立 PSI 修复先行提交/合入
contribution_opportunities:
- kind: testing
  description: 用 psi-delayed.sh 复现脚本验证 1/7 修复
- kind: review
  description: 核对 1/7 对 TSK_MEMSTALL/TSK_IOWAIT 的保留语义与 psi_task_switch() 等价性
generated_at: '2026-10-31T09:00:00'
source_email_count: 1
related_articles:
- sched-20260922-002
- sched-20261024-001
- sched-20261025-010
- sched-20261026-006
tags:
- proxy_execution
- psi
title: Sleeping Owner Handling for Proxy Execution (v33)
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/22/sched-20260922-002-sleeping-owner-handling-for-proxy-execution-v32.html">sched-20260922-002</a>（v32）：John Stultz 发出 proxy execution 第 5 阶段「Sleeping Owner Handling」第 32 版：任务阻塞在 owner 睡眠的 mutex 上时，把 waiter 停用并挂到 owner 等待表，待 owner 唤醒时在同 rq 重新激活以提升 owner。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-001-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261024-001</a>（v33）：系列扩到 7 补丁（PSI 状态、远程 tick、无 owner/无 mutex、return migration、链循环检测等边界修复）；Peter/Andrea/Kayra 密集 review，仍属 RFC。
- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-010-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261025-010</a>：Kayra 对 5/7（链循环停用）补问是否缺 `Fixes` 标签。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-006-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261026-006</a>：K Prateek 密集 review（7 封），核心问题集中在 7/7 sleeping-owner 的 get/put、TASK_WAKING 竞态、DL 带宽记账。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-020-sleeping-owner-handling-for-proxy-execution-v33.html">sched-20261030-020</a>（今天）：Tejun Heo 对 **1/7（sched/psi: Preserve sleep-persistent PSI flags）** 给出 **Tested-by** 并附强证据：该补丁还修掉一个**无需 proxy execution 即可触发**的 PSI 告警路径（`switching_from_fair` 的 iowait 延迟 dequeue）；无补丁时 10/10 次 boot 一秒内复现 `psi: inconsistent task state!`，仅应用 1/7 后 0/10 次复现。

## 背景与问题
（承接 v32/v33）proxy execution 第 5 阶段处理「任务阻塞在 mutex 上而 owner 睡眠」：需在 owner 唤醒时重新激活 waiter 树。今日聚焦 1/7 的 PSI 补丁：`psi_dequeue()` 在 `DEQUEUE_SLEEP` 且 `TSK_ONCPU` 已清时，把 sleep-persistent 的 `TSK_IOWAIT` 等 PSI 标志整片清掉，唤醒时 `psi_enqueue()` 触发 `psi: inconsistent task state!` 检查。Tejun 进一步指出该缺陷**不依赖 proxy execution**：一个 fair 任务在 iowait 睡眠并被 delay-dequeue，随后 `sched_setscheduler()` 把它移到 SCHED_FIFO，`switching_from_fair()` 以 `DEQUEUE_SLEEP | DEQUEUE_DELAYED` dequeue，此时 `TSK_ONCPU` 已清，自 `c2ae8b0df2d1`（"sched/core: Fix psi_dequeue() for Proxy Execution"）以来 `psi_dequeue()` 会清掉全部 PSI 标志（含 TSK_IOWAIT），唤醒路径随即告警。

## 技术方案
（承接 v33 的 1/7）1/7 `sched/psi: Preserve sleep-persistent PSI flags on off-CPU sleeping dequeues`（`Fixes: c2ae8b0df2d1`）：把 sleep-persistent 的 `TSK_MEMSTALL` 等标志在 off-CPU sleeping dequeue 时**保留**（按 `psi_task_switch()` 的 runnable→sleeping 转换处理），避免迁移式整片清掉导致唤醒时 `TSK_MEMSTALL_RUNNING` 无对应 `TSK_MEMSTALL`、`psi.mem.full` 超过 `psi.mem.some`、`get_recent_times()` 下溢。今日无新代码，为 Tejun 对该补丁的独立验证。

## 版本演进与当前进展
*current_version: v33*（2026-10-23 发出）。今日 1/7 获 Tejun 强背书（Tested-by + 跨 CONFIG_SCHED_PROXY_EXEC=off 的复现/验证）。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：对 1/7 给 Tested-by，并用「无 proxy execution 也触发」的独立路径 + 10/10 vs 0/10 的量化复现，把该补丁从一个「proxy 相关边界修复」提升为「独立、可复现的 PSI 正确性修复」，价值显著上升。
- **遗留**：其余 6 补丁（尤其 7/7 sleeping-owner 的 get/put、TASK_WAKING 竞态、DL 带宽记账）仍处 RFC 争议中。

## 合入评估
*likelihood=unknown*。1/7 已具备独立合入价值（有 Tested-by + 独立复现路径），但整个 v33 仍属 RFC，1/7 是否会与其余补丁拆开独立先合，尚无明确表态。*blocking_issues*：系列整体 RFC，其余补丁的争议未解；1/7 是否拆独立需 John/维护者决定。*next_action*：可考虑把 1/7 作为独立 PSI 修复先行提交/合入。

## 效果评估
Tejun 实测：mainline `4dd16e31135e`、`CONFIG_SCHED_PROXY_EXEC` 关闭、每次全新 boot——无补丁时 10/10 次一秒内命中 `psi: inconsistent task state! task=1318:python3 ... psi_flags=0 clear=1 set=4`；仅应用 1/7 后 0/10 次命中；期间 `switching_from_fair()` 每 boot 对延迟 iowait 任务 dequeue 约 3500–16000 次。

## 我可以参与的点
- **testing**：用 Tejun 提供的 `psi-delayed.sh` 复现脚本（O_DIRECT 读 + SCHED_FIFO/OTHER 翻转）验证 1/7 修复。
- **review**：核对 1/7 对 `TSK_MEMSTALL`/`TSK_IOWAIT` 的保留语义与 `psi_task_switch()` 的等价性。

## 参考链接
- lore thread（v33）: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/
