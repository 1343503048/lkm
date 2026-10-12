---
id: sched-20261012-025
date: '2026-10-12'
subject: 'sched: rt.c: kernel-doc warning'
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <20261005072738.2902503-2-manuelebnerli@mailbox.org>
lore_url: https://lore.kernel.org/all/20261005072738.2902503-2-manuelebnerli@mailbox.org/
authors:
- Manuel Ebner
maintainers_involved:
- K Prateek Nayak
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 尚无补丁，仅为问答
  next_action: Manuel 按建议给 max_rt_runtime 打 __maybe_unused 并发补丁
contribution_opportunities:
- kind: new_patch
  description: 发补丁给 kernel/sched/rt.c 的 max_rt_runtime 标注 __maybe_unused（或等价修法），消除
    W=1 告警
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20261005-007
tags:
- rt
title: 'sched: rt.c: kernel-doc warning'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/05/sched-20261005-007-sched-rt-c-kernel-doc-warning.html">sched-20261005-007</a>：Manuel Ebner 在 `make W=1` 遇到 `max_rt_runtime defined but not used` 告警并公开求解——该变量文件后面明明用了两处（`tg_set_rt_bandwidth()` 配额上限检查、`sched_rt_global_validate()` 全局校验），为何还报未使用。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-025-sched-rt-c-kernel-doc-warning.html">sched-20261012-025</a>（今天）：K Prateek Nayak 解答——若 `CONFIG_RT_GROUP_SCHED` 与 `CONFIG_SYSCTL` 都被禁用，那两处使用不会编进来，编译器便报未使用；建议用 `__maybe_unused` 标注。

## 背景与问题

（承接 20261005-007）`max_rt_runtime` 的两处使用都被 config 门控（`CONFIG_RT_GROUP_SCHED`/`CONFIG_SYSCTL`），二者同时关闭时变量只定义不引用，触发 `-Wunused-const-variable=`。

## 技术方案

Prateek 建议：给 `max_rt_runtime` 标注 `__maybe_unused` 保持构建干净。尚无补丁。

## 版本演进与当前进展

v1 问答（10-05）→ 今日（10-12）Prateek 给出答案；问题已解，若需彻底消除告警还需落一个小补丁。

## Maintainer 意见与讨论焦点

无分歧；Prateek 给出明确修法。

## 合入评估

*likelihood=unknown*。仅为问答、尚无补丁。*blocking_issues*：无补丁。*next_action*：Manuel 发补丁标注 `__maybe_unused`。

## 效果评估

无数据（构建告警类）。

## 我可以参与的点

- `new_patch`：发补丁给 `kernel/sched/rt.c` 的 `max_rt_runtime` 标注 `__maybe_unused`（Prateek 已指明修法，可直接落地）。

## 参考链接

- lore（Prateek 解答）: https://lore.kernel.org/all/0c57bf52-2c28-4379-9c1b-4f35a8540c3b@amd.com/
