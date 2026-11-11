---
id: sched-20261111-015
date: '2026-11-11'
subject: 'sched/mmcid: Synchronize MM teardown with affinity updates'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: <20261110183809.3308868-1-bestswngs@gmail.com>
lore_url: https://lore.kernel.org/all/20261110183809.3308868-1-bestswngs@gmail.com/
authors:
- Weiming Shi
maintainers_involved:
- Mathieu Desnoyers
current_version: v3
patch_series:
- version: v3
  msgid: <20261110183809.3308868-1-bestswngs@gmail.com>
  date: '2026-11-10'
  summary: 用 p->pi_lock 作 grace period，覆盖 exit_mm/kthread_unuse_mm，补文档与顺序说明
  review_outcome: Mathieu 补 Cc tglx，尚未对 v3 实质评审
upstream_commit: null
fixes_commit: 7e019dcc470f
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Mathieu/tglx 对 v3 的确认待给
  - 'p->pi_lock grace period 的合法性待核（Cc: stable）'
  next_action: Mathieu 与 tglx 评审 v3 的 acquire/release 顺序
contribution_opportunities:
- kind: review
  description: 复核 exit_mm/kthread_unuse_mm 两条路径的锁顺序与 set_cpus_allowed_common 一致性
- kind: testing
  description: 用作者 PoC 在 CONFIG_FUTEX=n 配置上验证 KASAN UAF 已修复
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261106-012
- sched-20261108-004
tags:
- affinity
title: 'sched/mmcid: Synchronize MM teardown with affinity updates'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-012-sched-mmcid-defer-affinity-updates-until-schedule-in.html">sched-20261106-012</a>：Weiming Shi 修复 MM-CID 亲和性更新路径的 use-after-free（KASAN 抓到、`panic_on_warn` 直接 panic）：`set_cpus_allowed_common()` 把远端任务的 `p->mm` 传给 `mm_update_cpus_allowed()`，但调度锁不稳定该指针——同一 owner 的 `sched_setaffinity()` 与目标任务的 exec（替换并释放旧 mm）竞速；`CONFIG_FUTEX=n` 的合法配置下仍脆弱。v1 把 MM-CID 允许掩码更新推迟到 schedule-in。带 `Fixes: 7e019dcc470f`、`Cc: stable`。
- <a class="article-ref" href="/lkm/2026/11/08/sched-20261108-004-sched-mmcid-synchronize-exec-mm-teardown-with-affinity-updat.html">sched-20261108-004</a>：v2 换思路——不再「推迟到 schedule-in」，改为在 exec 侧「发布新 `p->mm` 后、丢弃旧 mm 前，取放一次 runqueue 锁」作 barrier。Mathieu Desnoyers（MM-CID 作者）要求补充文档、时序图与 acquire-release 内存序说明。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-015-sched-mmcid-synchronize-mm-teardown-with-affinity-updates.html">sched-20261111-015</a>（今天）：**v3 发出**——按 Mathieu 要求补上 `p->pi_lock` grace period 与 acquire/release 顺序的完整文档说明；改用 `p->pi_lock` 直接同步，并把覆盖范围扩到 `exit_mm()` 与 `kthread_unuse_mm()`（针对 shoot-down lazy TLB MM 的架构）；刷新 KASAN trace 并附带独立 reproducer。Mathieu 当日只补 Cc 了 Thomas Gleixner，尚未给实质评审。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-012-sched-mmcid-defer-affinity-updates-until-schedule-in.html">sched-20261106-012</a> / 20261108-004）KASAN 已抓到 UAF：`set_cpus_allowed_common()` 读远端任务 `p->mm` 时，该任务正在 exec、`setup_new_exec()` 里的 `mmput()` 已释放旧 mm，`Read of size 4` 命中 slab 释放对象，`panic_on_warn` 直接 panic。根本原因是 `p->mm` 的加载到完整使用之间，`p->pi_lock` 没有稳定这个指针对抗 MM 替换；`CONFIG_FUTEX=n` 时 `futex_exec_done()` 不再提供「碰巧」的串行化。

## 技术方案

v3 核心（承接 v2，改走 `p->pi_lock` 作 grace period）：

- 发布新 `p->mm`（或置 NULL）之后、丢弃旧 mm 引用之前，teardown 侧取放一次 `p->pi_lock` 作为 release；affinity updater 的 `__set_cpus_allowed_ptr` 本就跨 `set_cpus_allowed_common()` 持 `p->pi_lock`，其解锁即 release。
- 顺序保证：updater 先取锁读到 `old_mm` → teardown 发布新 mm 后取 `p->pi_lock` 会等待 updater 完成 `mm_update_cpus_allowed()` 并解锁 → 之后才 `mmput/mmdrop(old_mm)`，old_mm 全程存活。若 teardown 先序，其 unlock 的 release 使后来的 updater 观察到 new_mm 或 NULL。
- 该 grace period 只需 `p->pi_lock`（runqueue 锁不参与 `p->mm` 生命周期顺序），置于 `exec_mmap()`、`exit_mm()`、`kthread_unuse_mm()` 三个发布点。
- v3 新增：补 `p->pi_lock` grace period 与 acquire/release 顺序的文档注释；覆盖 `exit_mm()` 与 `kthread_unuse_mm()`（shoot-down 架构上 lazy TLB MM 有同样生命周期缺口）；`Fixes: 7e019dcc470f`、`Cc: stable`。

## 版本演进与当前进展

*current_version: v3（2026-11-10，`<20261110183809.3308868-1-bestswngs@gmail.com>`）*。v3 落实 Mathieu 在 v2 的要求（文档 + 顺序说明），改回用 `p->pi_lock` 并扩覆盖到 exit/kthread_unuse 路径。作者附 848 字节 ET_EXEC 的 memfd + execveat 独立 reproducer（stochastic race，约 52.60s 触发 UAF），并注明「LLM 协助开发」。

## Maintainer 意见与讨论焦点

- **Mathieu Desnoyers（MM-CID 作者）**：当日仅补 Cc 了 Thomas Gleixner（+CC tglx），尚未对 v3 给实质评审；其在 v2 阶段的核心要求（文档/时序图/acquire-release 顺序）v3 已回应。
- 无 NAK。焦点仍是「用锁副作用做同步」这一模式是否可被长期信任（Mathieu 在 v2 明确表达过顾虑），有待其审阅 v3 文档后表态。

## 合入评估

*likelihood=medium*。v3 已补齐 v2 评审要求的文档与顺序说明，但 Mathieu 与 tglx 尚未对 v3 实质评审，且「锁副作用同步」的模式仍需 MM/time 维护者背书。*blocking_issues*：Mathieu/tglx 对 v3 的确认；`p->pi_lock` 作 grace period 的合法性与可回退性（Cc: stable）待核。*next_action*：Mathieu 与 Thomas Gleixner 评审 v3 的 acquire/release 顺序是否正确。

## 效果评估

作者给出确定性 KASAN 复现（CONFIG_SCHED_MM_CID=y + CONFIG_FUTEX=n + 8 vCPU @ 4 host CPU 2:1 overcommit，约 52.60s 触发 UAF，最后 10 秒窗口已有 2,096,128 次成功 affinity 更新与 18,975 次完成的 exec）。修复本身是正确性修复，无性能数据。

## 我可以参与的点

- **review**：复核 v3 的 `p->pi_lock` acquire/release 顺序论证——尤其 `exit_mm()` 与 `kthread_unuse_mm()` 这两条新增覆盖路径的锁顺序是否与 `set_cpus_allowed_common()` 一致。
- **testing**：用作者附带的 memfd+execveat PoC 在 `CONFIG_FUTEX=n` 配置上验证不再出现 KASAN UAF。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110183809.3308868-1-bestswngs@gmail.com/
- 作者的独立 reproducer: https://lore.kernel.org/all/20261110183809.3308868-2-bestswngs@gmail.com/
- Mathieu +CC tglx: https://lore.kernel.org/all/bd1a4a21-bc1f-4a46-b6bb-80a76ac48814@efficios.com/
