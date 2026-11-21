---
id: sched-20261121-009
date: '2026-11-21'
subject: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261121041507.39582-2-qyousef@layalina.io>
lore_url: https://lore.kernel.org/all/20261121041507.39582-2-qyousef@layalina.io/
authors:
- Qais Yousef
maintainers_involved: []
current_version: v6
patch_series:
- version: v5
  msgid: <20261103005953.56271-1-qyousef@layalina.io>
  date: '2026-11-03'
  summary: 4 补丁：竞态修复 + UCLAMP_FLAG_IDLE wrapper + RFC revert RT nr_running 越界 + 移出
    core.c 配对
  review_outcome: 无外部 review
- version: v6
  msgid: <20261121041507.39582-2-qyousef@layalina.io>
  date: '2026-11-21'
  summary: 3 补丁：进 idle 校正竞态、wrapper 化、uclamp_rq_{inc,dec} 移出 core.c 与 nr_running 配对；删
    RFC RT revert
  review_outcome: 2/3 获 Kayra Cizmeci Reviewed-by；1/3、3/3 待 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无调度维护者 review
  - RT group 节流遗留未闭环
  next_action: 等 Peter/相关维护者对 v6 1/3 与 3/3 的 review
contribution_opportunities:
- kind: review
  description: 核对 3/3 与 nr_running 配对是否覆盖所有绕过 core 的 enqueue/dequeue 路径
- kind: testing
  description: 开启 uclamp + RT/CFS 带宽节流的负载验证计数不再失衡、无 idle 回归
generated_at: '2026-11-22T01:00:00+08:00'
source_email_count: 91
related_articles:
- sched-20261102-021
- sched-20261103-016
tags:
- uclamp
- rt
- cgroup
title: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261025-001</a>：Qais Yousef 修 uclamp static key 非原子翻转导致的 rq 计数失衡竞态。
- <a class="article-ref" href="/lkm/2026/10/26/sched-20261026-002-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261026-002</a>（v2）：修链接错误、idle 检测改 WARN_ON。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-001-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261029-001</a>（v4）：拆 1/2（竞态）+2/2（wrapper）；Christian 指出 CFS 带宽节流不调 `uclamp_rq_dec()`。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-004-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261030-004</a>：上升为 CFS/RT 带宽节流 partial-dequeue 绕过 core {en,de}queue 的问题；Peter 提议节流路径自补 `uclamp_rq_{dec,inc}`。
- <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-021-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261102-021</a>：Qais 给出新方案——把 `uclamp_rq_{inc,dec}()` 与 `{add,sub}_nr_running()` 配对，RT 侧部分 revert `f4ebcbc0d7e00`。
- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-016-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261103-016</a>（v5）：扩为 4 补丁（含 RFC revert RT nr_running 越界管理），暂无外部 review。
- <a class="article-ref" href="/lkm/2026/11/21/sched-20261121-009-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261121-009</a>（今天）：**v6 收敛为 3 补丁**——1/3 竞态修复（进 idle 时校正）、2/3 UCLAMP_FLAG_IDLE wrapper（已获 Kayra Cizmeci Reviewed-by）、3/3 把 `uclamp_rq_{inc,dec}()` 移出 core.c 并与 `{add,sub}_nr_running()` 配对；**不再含 v5 的 RFC RT revert**，RT group 节流明确「留待后续（有提案标记其 broken）」不处理。仍无调度维护者 review。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/02/sched-20261102-021-sched-uclamp-fix-race-condition-leading-to-imbalanced-uclamp.html">sched-20261102-021</a> … 20261103-016）static key `sched_uclamp_used` 非原子翻转使各 CPU/调用点对 `uclamp_is_used()` 返回不一致，`uclamp_rq_inc` 与 `dec` 不对称（inc 无 dec 会留下损坏的 uclamp_rq）；同时 CFS/RT 带宽节流绕开 core enqueue/dequeue 造成 partial-dequeue 计数错乱。v5 起方案从「事后纠错」升级为「结构性配对」。

## 技术方案

v6（3 补丁）：
- **1/3**：接受 static key 翻转的非原子性，改在**进入 idle 时**做校正动作，保证该瞬态只在 `uclamp_sched_used` 使能后短暂存在（`init_uclamp_rq()` 改为非 static 供 idle 路径调用）。
- **2/3**：用 `uclamp_rq_is_idle()/set_idle()/clear_idle()` wrapper 替换 `UCLAMP_FLAG_IDLE` 的 open coding（可读性）。
- **3/3**：把 `uclamp_rq_{inc,dec}()` 从 core.c 移出并与 `{add,sub}_nr_running()` 配对——每个关心 uclamp 的类在更新 nr_running 时同步更新 rq uclamp 状态；RT 侧用 `{inc,dec}_tasks()`；RT group 节流因「不真正 dequeue、只对 nr_running 撒谎」留待后续（有提案标记其 broken）；顺带删掉 `sched_delayed` 守卫与 `flags` 参数（现已在恰当时机做操作）。

相较 v5：去掉了 RFC 性质的 RT revert（3/4），结构更收敛。

## 版本演进与当前进展

*current_version: v6（2026-11-21，`<20261121041507.39582-2-qyousef@layalina.io>`，3 补丁）*。v5（4 补丁）→ v6（3 补丁）：删 RFC RT revert，1/3 改为 idle 进入时校正，2/3 已获 Reviewed-by。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci（reviewer）**：对 2/3 wrapper 化给 Reviewed-by。
- 无 NAK。此前 Peter 的方向性建议（节流路径自补 uclamp 计数）已在 3/3 的配对中体现；但 1/3 的「idle 校正」与 3/3 的「与 nr_running 配对」是否满足 Peter 预期、RT group 节流的遗留是否可接受，仍无维护者表态。

## 合入评估

*likelihood=medium*。v6 结构收敛、2/3 已有 Reviewed-by，但 1/3 竞态修法与 3/3 配对尚缺调度维护者（Peter 等）评审。*blocking_issues*：无维护者 review；RT group 节流遗留未闭环。*next_action*：等 Peter/相关维护者对 v6 的 review，尤其 1/3 与 3/3。

## 效果评估

无性能数据；属正确性修复（uclamp 计数失衡、节流 bypass）。1/3 注释说明竞态「unlikely but ensure uclamp_rq state 在每次进 idle 时被校正」。

## 我可以参与的点

- **review**：核对 3/3 把 `uclamp_rq_{inc,dec}()` 与 `{add,sub}_nr_running()` 配对是否覆盖所有绕过 core 的 enqueue/dequeue 路径（尤其 RT group 节流）。
- **testing**：在开启 uclamp + RT/CFS 带宽节流的负载上验证计数不再失衡、无 idle 路径回归。

## 参考链接

- lore thread（v6 1/3）: https://lore.kernel.org/all/20261121041507.39582-2-qyousef@layalina.io/
- v5 cover: https://lore.kernel.org/all/20261103005953.56271-1-qyousef@layalina.io/
