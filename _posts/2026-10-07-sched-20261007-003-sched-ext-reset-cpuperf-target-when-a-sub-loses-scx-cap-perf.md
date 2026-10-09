---
id: sched-20261007-003
date: '2026-10-07'
subject: 'sched_ext: Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies'
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: <20261004012721.615419-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/4bc0c5e88d602dcbc886b1214c676c8d@kernel.org/
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20261004012721.615419-1-cui.tao@linux.dev>
  date: '2026-10-04'
  summary: 持有者退场时内核复位 cpuperf target（irq_work + disable 扫描）
  review_outcome: 触发方向性讨论
- version: v2
  msgid: <20261006142834.2815197-1-cui.tao@linux.dev>
  date: '2026-10-06'
  summary: 四锚点加固：锁序/RCU/回线恢复/垂死写者拒绝
  review_outcome: 10-07 Tejun 裁决：内核不应代选值，恢复归父级；系列被 caps-clear 取代
upstream_commit: null
fixes_commit: 86094b95efcf
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 维护者否决「内核代选复位值」路线
  next_action: 作者放弃本系列；关注接棒的 caps-clear 补丁
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: review
  detail: 审 caps-clear 补丁的摘 caps 时机是否覆盖所有早退路径
- kind: extend
  detail: 为示例调度器补父级恢复 target 的契约参考实现
source_email_count: 1
related_articles:
- sched-20261004-004
- sched-20261006-006
tags:
- sched_ext
- cpufreq
- dvfs
title: 'sched_ext: Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies'
layout: article
---

> **subject**：`sched_ext: Reset cpuperf_target when a sub loses SCX_CAP_PERF or dies`
> 本文为增量更新，完整脉络见下。

## TL;DR

- <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.html">sched-20261004-004</a>：Tao Cui 报告并修复 sched_ext 子调度器生命周期漏洞——持有 `SCX_CAP_PERF` 的子调度器把 cpuperf target 写低后消失（cap 回收/kill/detach/cgroup 移除），target 残留：`scx_bpf_sub_revoke()` 只清 caps 位图、`scx_sub_disable()` 重定任务但都不碰 `rq->scx.cpuperf_target`；读侧门 `scx_cpuperf_target()` 只测全局 `scx_enabled()`，root 调度器运行期间 schedutil 持续消费陈旧 target，switched-all 模式下 CPU 被钉死在低频。v1 以 irq_work + disable 扫描双路复位，`Fixes: 86094b95efcf`。
- <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261006-006</a>：v2 发出，修复面扩大——disable 扫描持 `scx_enable_mutex + cpus_read_lock()` + RCU 读侧、`scx_online_ecaps()` 回线恢复中性基、revoke 写门关闭点同步折叠回中性基、`scx_bpf_cidperf_set()` 拒绝垂死调度器写入。实测 kill 后立即回 `SCX_CPUPERF_ONE`、十轮加载/卸载 + hotplug 交织 lockdep/KASAN 干净。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-003-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261007-003</a>（今天）：**Tejun Heo 裁决否决「内核代选复位值」的路线**——cpuperf target 是「last-writer-wins、无 owner 跟踪」的状态，内核唯一强加的值是 enable 时的初始化；父调度器 grant 了 `SCX_CAP_PERF` 就应预期子级改写过 target，revoke 后或 `ops.sub_detach()` 里的恢复是**父调度器的责任**（root 持所有 cap、能 grant PERF 的父级必然持有 PERF，重写总有权限）。但 Tejun 同时承认内核侧有一个真实缺口：`ops.sub_detach()` 跑在子级 `ops.exit()` 之前、子级尚未失去 kfunc 访问，子级 timer 或 `ops.exit()` 仍可在父级清理后写入——**他将发一枚补丁在 `ops.sub_detach()` 前摘掉垂死子级的 caps**，让父级收到通知时子级已「惰化」。Tao Cui 的系列就此被取代（次日正式放弃，见 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/04/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.html">sched-20261004-004</a> → <a class="article-ref" href="/lkm/2026/10/06/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261006-006</a>）bug 本身无争议：子调度器退场后 cpuperf target 残留、schedutil 消费陈旧值、switched-all 下 CPU 低频钉死。争议的是**修复责任的归属**——Tao 的 v1/v2 让内核在持有者退场时主动恢复中性基；Tejun 的裁决把模型定为：cpuperf target 是 last-writer-wins 状态，值的恢复属于「grant 了 cap 的那一方」（父调度器的 BPF 代码），内核只负责保证契约可执行（子级真正不能再写）。

## 技术方案

（承接 v1/v2 的机制描述）v1/v2 的内核侧复位路径（revoke 时 irq_work 排队 reset、disable 时持锁扫描 pshard cmasks、回线恢复中性基、折叠点回写）在裁决后**整体废弃**。

裁决确立的替代契约：

1. **last-writer-wins**：内核不在 enable 初始化之外的任何时点强加 cpuperf 值；无 owner 跟踪。
2. **父级负责恢复**：父调度器 grant `SCX_CAP_PERF` 给子级，就应预期 target 被改写；revoke 后或 `ops.sub_detach()` 回调里由父级 BPF 代码复位（root 持所有 cap；父级能 grant PERF 的地方必然持有 PERF，重写永远有权限）。
3. **内核补缺口**（Tejun 预告新补丁，即 <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-004-sched-ext-clear-a-sub-scheduler-s-caps-before-ops-sub-detach.html">sched-20261007-004</a>）：`ops.sub_detach()` 目前早于子级 `ops.exit()` 且子级尚未失去 kfunc 访问——子级 timer/`ops.exit()` 可在父级清理后继续写。修法是在 `ops.sub_detach()` 之前摘掉垂死子级的 caps，使父级被通知时子级已无写能力，契约闭合。

## 版本演进与当前进展

- v1（10-04）：双路复位（<a class="article-ref" href="/lkm/2026/10/04/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.html">sched-20261004-004</a>）。
- v2（10-06）：四锚点加固（<a class="article-ref" href="/lkm/2026/10/06/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261006-006</a>）。
- 10-07：Tejun 裁决（本篇）——路线否决，转向「父级恢复 + 内核惰化垂死子级」。同日 Tejun 发出预告的 caps-clear 补丁（<a class="article-ref" href="/lkm/2026/10/07/sched-20261007-004-sched-ext-clear-a-sub-scheduler-s-caps-before-ops-sub-detach.html">sched-20261007-004</a>）。
- 10-08：Tao Cui 实测 caps-clear 补丁并给 Tested-by/Reviewed-by，正式放弃本系列（<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>）。

## Maintainer 意见与讨论焦点

**Tejun Heo**（sched_ext 首席维护者）10-07 03:31 裁决原文要点：

- 「I don't think the kernel should be picking a value here」——直接否决内核代选复位值。
- 责任划分：「restoring them after a revoke or in ops.sub_detach() is the parent's responsibility」。
- 权限论证：「The root holds every cap and a sub-sched parent holds PERF wherever it could grant it, so the rewrite always has the cap」——父级恢复不存在权限死角。
- 承认真缺口：「ops.sub_detach() runs before the child's ops.exit() and before the child loses kfunc access, so a child timer or its ops.exit() can still write after the parent has cleaned up」——这是 v1/v2 报告的问题里唯一需要内核修的部分，但修法是「惰化写者」而非「代写值」。

焦点：**状态归属语义**（谁拥有 cpuperf target 的终值）压倒了**工程完备性**（v2 已把窗口封得很干净）。维护者选择了契约清晰、机制最小的模型，代价是 BPF 调度器侧多一份恢复责任。

## 合入评估

*likelihood=rejected*（本系列不再以当前形态推进）。*status=superseded*——被 Tejun 的 caps-clear 补丁（<a class="article-ref" href="/lkm/2026/10/07/sched-20261007-004-sched-ext-clear-a-sub-scheduler-s-caps-before-ops-sub-detach.html">sched-20261007-004</a>）+ 父级恢复契约取代，作者次日确认放弃。*next_action*：关注 caps-clear 补丁的 review 与落地；若 OLK-6.6 需要同类修复，Tao 的 v2 仍可作为「内核托管恢复」的参考实现，但方向上应跟随上游契约。

## 效果评估

v2 的实测数据（kill 即回 `SCX_CPUPERF_ONE`、离线期间 kill 的 CPU 回线恢复、十轮交织 lockdep/KASAN 干净）依然有效地证明了 bug 真实性与可修复性；但裁决后「效果」的判据变了——预期效果改为：caps-clear 落地后，父调度器在 `ops.sub_detach()` 里做恢复时不再被垂死子级的迟到写入覆盖。

## 我可以参与的点

- `review`：审 <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-004-sched-ext-clear-a-sub-scheduler-s-caps-before-ops-sub-detach.html">sched-20261007-004</a> caps-clear 补丁的「摘 caps 时机」是否覆盖所有早退路径（timer、`ops.exit()`、kfunc 并发），这正是 v2 曾封过、新方案必须重新保证的窗口。
- `extend`：为 scx_qmap 等示例调度器补「grant PERF 的父级在 sub_detach 恢复 target」的参考实现，把新契约示范出来——这是裁决后最缺的配套件。
- 回合视角：OLK-6.6 无 sub-scheduler 机制（近期特性），本系列与 caps-clear 均不适用。

## 参考链接

- Tejun 的裁决: https://lore.kernel.org/all/4bc0c5e88d602dcbc886b1214c676c8d@kernel.org/
- v2 补丁: https://lore.kernel.org/all/20261006142834.2815197-1-cui.tao@linux.dev/
- v1 补丁: https://lore.kernel.org/all/20261004012721.615419-1-cui.tao@linux.dev/
- 相关文章：<a class="article-ref" href="/lkm/2026/10/04/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.html">sched-20261004-004</a>（v1）、<a class="article-ref" href="/lkm/2026/10/06/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.html">sched-20261006-006</a>（v2）、<a class="article-ref" href="/lkm/2026/10/07/sched-20261007-004-sched-ext-clear-a-sub-scheduler-s-caps-before-ops-sub-detach.html">sched-20261007-004</a>（接棒的 caps-clear）、<a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>（放弃确认与后续）
