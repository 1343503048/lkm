---
id: sched-20261108-004
date: '2026-11-08'
subject: 'sched/mmcid: Synchronize exec MM teardown with affinity updates'
subsystem: sched
type: bug
status: under_review
severity: critical
thread_root_msgid: <20261108132634.2650642-2-bestswngs@gmail.com>
lore_url: https://lore.kernel.org/all/20261108132634.2650642-2-bestswngs@gmail.com/
authors:
- Weiming Shi
maintainers_involved:
- Mathieu Desnoyers
current_version: v2
patch_series:
- version: v1
  msgid: <20261106120846.2405936-1-bestswngs@gmail.com>
  date: '2026-11-06'
  summary: MM-CID 允许掩码更新推迟到 schedule-in + fork 同步，修复 mm/exec 竞速 UAF。
  review_outcome: 当日无评审
- version: v2
  msgid: <20261108132634.2650642-2-bestswngs@gmail.com>
  date: '2026-11-08'
  summary: 改为 exec 侧 runqueue-lock barrier，保持 affinity 更新同步，不动 sched 状态机。
  review_outcome: Mathieu 要求补文档/时序图/acquire-release 说明；作者承诺 v3 补齐
upstream_commit: null
fixes_commit: 7e019dcc470f
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需补时序图/内存序说明
  - 需 Mathieu 复核并认可锁副作用同步模式的正确性
  next_action: 作者发 v3（含文档与复现代码），等 Mathieu 确认
contribution_opportunities:
- kind: review
  description: 独立推演 exec 侧 runqueue-lock barrier 是否对所有 p->mm 读路径构成 acquire-release
    对
- kind: testing
  description: 基于 v3 复现代码跑 setaffinity 与 exec 竞速验证 UAF 消除
generated_at: '2026-11-09T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261106-012
tags:
- affinity
title: 'sched/mmcid: Synchronize exec MM teardown with affinity updates'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-012-sched-mmcid-defer-affinity-updates-until-schedule-in.html">sched-20261106-012</a>：Weiming Shi 修复 MM-CID 亲和性更新路径的 use-after-free（KASAN 已抓到、`panic_on_warn` 直接 panic）：`set_cpus_allowed_common()` 把远端任务的 `p->mm` 传给 `mm_update_cpus_allowed()`，但调度锁并不稳定这个指针——同一 owner 的 `sched_setaffinity()` 会与目标任务的 exec（替换并释放旧 mm）竞速，当前内核只是「碰巧」被 `futex_exec_done()` 取 `p->pi_lock`（且需 CONFIG_FUTEX=y）串行化，`CONFIG_FUTEX=n` 的合法配置仍然脆弱。v1 修复把 MM-CID 允许掩码更新推迟到任务的 schedule-in。带 `Fixes: 7e019dcc470f`、`Cc: stable`。
- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-004-sched-mmcid-synchronize-exec-mm-teardown-with-affinity-updat.html">sched-20261108-004</a>（今天）：**v2 发出，换了一个思路**——放弃 v1 的「推迟到 schedule-in」延迟方案，改为在 exec 侧「发布新 `p->mm` 后、丢弃旧 mm 前，取放一次任务的 runqueue 锁」作为 barrier（affinity 更新跨 `set_cpus_allowed_common()` 全程持该锁，barrier 会等任何已读旧 mm 的更新完成）。Mathieu Desnoyers（MM-CID 作者）当日评审：认可方向但要求补充文档、时序图与 acquire-release 内存序说明，否则「这个锁副作用作同步」的模式难以被信任；作者承诺 v3 补齐。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-012-sched-mmcid-defer-affinity-updates-until-schedule-in.html">sched-20261106-012</a>）KASAN 已抓到 UAF：`set_cpus_allowed_common()` 读远端任务 `p->mm` 时，该任务正在 exec、`setup_new_exec()` 里的 `mmput()` 已释放旧 mm，`Read of size 4` 命中 slab 释放对象。v1 通过在 sched 里推迟传播来规避。v2 递进：作者意识到还有「transient affinity expansion」在推迟方案下不可同步的问题，遂回到 exec 侧做同步。

## 技术方案

v2 核心（`fs/exec.c` +1、`include/linux/sched.h` +2、`kernel/sched/core.c` +6，共 9 行）：在 `exec_mmap()` 发布新 `p->mm` 之后、旧 mm 被丢弃之前，取放一次该任务的 runqueue lock。affinity 更新（`__set_cpus_allowed_ptr`）本就跨 `set_cpus_allowed_common()` 持有这把锁，因此这个 barrier 会等到「任何已读取旧 mm 的异地更新」完成；此后开始的更新观察到的是新 mm。相比 v1 的「推迟到 schedule-in + fork 同步」，v2 保持允许掩码更新同步（含瞬时 affinity 扩展），且不动 MM-CID 的 fork/exit/调度状态机。作者注明「LLM 协助开发」。

## 版本演进与当前进展

*current_version: v2（2026-11-08 发出，msgid 20261108132634.2650642-2）*。

- v1（2026-11-06）：「defer affinity updates until schedule-in」，把 MM-CID 允许掩码更新推迟到 schedule-in 并在 first run 前同步 fork 任务的共享 mm。当日无评审。
- v2（2026-11-08）：改为 exec 侧 runqueue-lock barrier（`sched_mm_cid_exec_mmap()`），放弃 v1 的推迟传播。当日获 Mathieu 评审、作者承诺 v3 补齐文档。

## Maintainer 意见与讨论焦点

- **Mathieu Desnoyers**（MM-CID 作者）：未 NAK，但指出「用锁的副作用来同步锁外数据是很有意思的模式，若真可行须彻底文档化」，并要求至少一张时序图解释其正确性 + acquire-release 内存序说明。
- 作者回应：v3 会补上文档、时序图、acquire-release 内存序说明与复现代码。

无 NAK；争议点是「lock side-effect as synchronization」这种非常规模式的正确性能否被论证清楚。

## 合入评估

*likelihood=medium*。真实 UAF、根因清晰、`Fixes`/`Cc: stable` 齐全，v2 比 v1 更内聚（不动 sched 状态机）；但新方案依赖争议性的锁副作用同步，需作者补齐 acquire-release 证明、且 MM-CID 作者尚未给 Reviewed-by。*blocking_issues*：① 需补时序图/内存序说明；② 需 Mathieu 复核并认可该同步模式的正确性。*next_action*：作者发 v3（含文档与复现代码），等 Mathieu 确认。

## 效果评估

KASAN 报告已抓到 UAF 且 `panic_on_warn` 触发内核 panic，复现可靠。v2 未附修后回归数据（说明偏机理，无「修复后 N 轮无 UAF」的数据）；作者承诺 v3 附复现代码。

## 我可以参与的点

- **review**：独立推演「exec 侧 runqueue-lock barrier」是否真的对所有 `p->mm` 读取路径构成 acquire-release 对（尤其 CONFIG_FUTEX=n、CONFIG_SCHED_MM_CID=y 的配置）。
- **testing**：在 v3 复现代码基础上跑 sched_setaffinity 与 exec 竞速，验证 UAF 消除。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261108132634.2650642-2-bestswngs@gmail.com/
- Mathieu 当日评审: https://lore.kernel.org/all/74b00dcc-113f-4532-81f5-e7e0814ddc4c@efficios.com/
- 前一版（v1）: https://lore.kernel.org/all/20261106120846.2405936-1-bestswngs@gmail.com/
