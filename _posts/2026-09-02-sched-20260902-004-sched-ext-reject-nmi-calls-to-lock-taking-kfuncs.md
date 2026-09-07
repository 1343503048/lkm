---
id: sched-20260902-004
date: '2026-09-02'
subject: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- liwanwu
- Wanwu Li
- Tejun Heo
- Andrea Righi
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: high
  blocking_issues:
  - 承诺的 follow-up patch 未发出：三个 any 类 kfunc 以 scx_locked_rq() 非空推断已持 rq 锁，Tejun Heo
    已指出
  - NMI 可达性只有推论，线程内无实测栈或触发率数据
  next_action: 等并发出 scx_locked_rq() 的 follow-up，并补一条 NMI 路径的 scx selftest 验证
contribution_opportunities:
- 跟进 scx_locked_rq() 持锁推断的 follow-up 补丁（Tejun Heo 已点名，目前无人落地）
- 在 sched_ext selftests 中构造 NMI 上下文调用会拿锁的 kfunc，验证 -EBUSY 与调度器终止行为
- '关联 review sched_ext: Use atomic cpumask_clear_cpu in scx_idle_test_and_clear_cpu()'
source_email_count: 11
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Reject NMI calls to lock-taking kfuncs'
layout: article
---

## TL;DR

拒绝在 NMI 上下文调用会拿锁的 sched_ext kfunc。9/2 一天内走完 v1→v2→v3，Tejun Heo 9/3 07:05 明确
"Applied to sched_ext/for-7.4 with the following changes" —— 维护者已接收，但留了一个 follow-up 补丁
没解决。值得跟，因为它是 sched_ext 健壮性边界的定义性改动。

## 背景与问题

sched_ext 的若干 BPF kfunc 内部会获取锁（如 rq 锁、dsq 锁）。在 NMI 上下文调用这些
kfunc 会破坏锁协议、导致死锁或状态不一致。本期把「NMI 上下文调用会拿锁的 kfunc」显式
拒绝，提升 sched_ext 的健壮性。

## 技术方案

- 主补丁 `sched_ext: Reject NMI calls to lock-taking kfuncs`：在 kfunc 入口检测
  `in_nmi()` 并对会拿锁的 kfunc 返回错误 / 拒绝调用。
- 演进：v2（UID 72739）→ v3（UID 72748）；同日多条 Re:（72334/72340/72408/73046/
  74212）为评审交流。
- 关联小补丁 `sched_ext: Use atomic cpumask_clear_cpu in scx_idle_test_and_clear_cpu()`
  （71683 Re:），把空闲测试/清除改成原子操作，与 NMI 安全主题呼应。

## 版本演进与当前进展

- 当前状态：**under_review**（v3）。
- 合入可能性 medium/high；属明确的健壮性修复，争议点少。
- 与 005（vtime 排序约束）、006（NULL deref）同为当日 sched_ext 修复集群。

## Maintainer 意见与讨论焦点

- 分歧不在「要不要挡 NMI」，而在**收窄方式**。Andrea Righi（72272）提出：'AFAICS, the lock-taking and
  state-changing kfuncs do not have a meaningful use from BPF_PROG_TYPE_TRACING. We could move them o…'
  （截断）——即把这些 kfunc 移出可被 NMI 触达的类别，而不是只加一层判断。Tejun 72313、Andrea 72339 就此
  往返一轮，最终 v3 走的是「加判断」这条更保守的路。
- Tejun Heo 的具体意见（72404/73059）：`-EBUSY` 的返回值意义不大（"The return value doesn't matter much
  as the scheduler is being terminate…"）；`scx_bpf_destroy_dsq()` 要写 "unlikely(!sch) like the other kfuncs."
- 作者 liwanwu 74156 汇总了落地项："v3 folds in your three points (single scx_kf_allowed_ctx() macro with
  no wrapper, one reject in bpf_iter_scx_dsq_new(), unlikely(!sch) in scx_bpf_destroy_dsq())."
- **未解决**：Tejun 75364 指出三个 "any" 类 kfunc 用 `scx_locked_rq()` 非空来推断「已持 rq 锁」不成立，
  作者 75648 认下："Thanks for the correction and the guidance. I'll send a follow-up patch to fix the
  remaining issues." 无 NAK。

## 合入评估

**已进维护者树**（sched_ext/for-7.4，非主线）。卡点只剩一个：那封承诺的 follow-up patch 尚未发出，
处理 `scx_locked_rq()` 被当作持锁凭据的问题。另外 Tejun 接收时改动了提交信息（75523），主线化前不会有
额外阻力。

## 效果评估

全线程无性能或触发率数据；连 crash 都只是从 e06ece82d7b0 的可达性推论得出，没有人贴出过 NMI 路径下的
实际栈。属作者与维护者共同认可的定性判断，未见测试数据。

## 我可以参与的点

- 盯并发出那封 follow-up：`scx_locked_rq()` 语义问题已被 Tejun 点名，目前只有承诺没有补丁。
- 在 scx selftests / scxtest 里补一条 NMI 触发路径（如 bpf_send_signal 从 NMI 进来）验证 `-EBUSY` 行为，
  这条线程缺的就是这个。
- 顺带看同主题小补丁 `Use atomic cpumask_clear_cpu in scx_idle_test_and_clear_cpu()`（9/2 Andrea Righi
  71820、Michał Błaszczyk 73268 在回），它和本系列共享「NMI 安全」这个前提。

## 参考链接

- 005 sched_ext：文档化并强制 vtime 排序约束（v3）
- 006 sched_ext：修复 select_cpu_and 子调度空指针解引用
