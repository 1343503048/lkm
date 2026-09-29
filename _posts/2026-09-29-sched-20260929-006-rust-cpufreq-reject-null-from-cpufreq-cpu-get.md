---
id: sched-20260929-006
date: '2026-09-29'
subject: 'rust: cpufreq: reject NULL from cpufreq_cpu_get()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260829161013.102967-1-mehmet.mkoseoglu@gmail.com>
lore_url: https://lore.kernel.org/all/20260829161013.102967-1-mehmet.mkoseoglu@gmail.com/
authors:
- spidermana
maintainers_involved:
- Miguel Ojeda
current_version: v3
patch_series:
- version: v3
  msgid: <20260928162214.487564-1-xuyiwen14@gmail.com>
  date: '2026-09-28'
  summary: NonNull::new(...).ok_or(ENODEV)? 显式拒 NULL，错误码 ENODEV，按竖排 import 风格
  review_outcome: Elowen Xu Reviewed-by + SAFETY 注释 nit；Miguel 指出 From/tag 归属不匹配；spidermana
    更正标签
upstream_commit: null
fixes_commit: 6ebdd7c93177
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Miguel 关于 From/tag 归属的疑问待澄清
  - SAFETY 注释 nit 待处理
  next_action: 作者澄清署名归属、微调 SAFETY 注释后等 Miguel 收取
contribution_opportunities:
- kind: review
  description: 核对 NonNull/ok_or(ENODEV) 对 cpufreq_cpu_get 返回 ERR_PTR 的处理是否完备
- kind: testing
  description: 在启用 Rust cpufreq 绑定的内核上跑 policy 热插拔/未注册场景验证不再 oops
generated_at: '2026-09-30T01:15:00'
source_email_count: 3
related_articles:
- sched-20260830-006
tags:
- cpufreq
title: 'rust: cpufreq: reject NULL from cpufreq_cpu_get()'
layout: article
---

> **subject**：`rust: cpufreq: reject NULL from cpufreq_cpu_get()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/30/sched-20260830-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260830-006</a>：Mehmet Koseoglu 的 Rust cpufreq 绑定修复走到 v3——`PolicyCpu::from_cpu()` 把 `cpufreq_cpu_get()` 返回值交给只拒 `ERR_PTR`、不拒 NULL 的 `from_err_ptr()`，查表失败时会用 NULL 构造可变引用，析构时把非法指针传给 `cpufreq_cpu_put()` → `kobject_put()` 处 oops；改法是用 `NonNull::new(...).ok_or(ENODEV)?` 显式拒 NULL。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260929-006</a>（今天）：补丁改由 spidermana（`xuyiwen14@gmail.com`）重发 v3，Miguel Ojeda（Rust-for-Linux 维护者）指出某个 Reviewed-by 标签的 From 与标签邮箱不匹配；一位 reviewer（Elowen Xu）给出一处 SAFETY 注释措辞 nit 并 `Reviewed-by`；spidermana 更正了自己的标签归属。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/08/30/sched-20260830-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260830-006</a>）缺陷位置 `rust/kernel/cpufreq.rs` 的 `PolicyCpu::from_cpu()`：`cpufreq_cpu_get()` 契约是「返回带引用的 policy 或 NULL」，原实现 `from_err_ptr(...)?` 只对 `ERR_PTR` 报错、NULL 被当作有效指针走 `Policy::from_raw_mut(ptr)`，随后 `PolicyCpu` drop 时把 NULL 交给 `cpufreq_cpu_put()` 在 `kobject_put()` 里 oops。触发条件是 policy 查表失败等错误路径。今天无新背景，属前序版本评审的收尾。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/08/30/sched-20260830-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260830-006</a>）改法不变：用 `NonNull::new(unsafe { bindings::cpufreq_cpu_get(...) }).ok_or(ENODEV)?` 显式拒 NULL（`NonNull<T>` 在构造点建立「指针非 NULL」不变式，`Policy::from_raw_mut` 的前置条件才成立），错误码 `ENODEV` 与「该 CPU 无 policy」一致，另将 import 改成内核竖排风格。带 `Fixes: 6ebdd7c93177`、`Cc: stable`。今天的新进展是评审收尾：一位 reviewer 建议把 SAFETY 注释改写为「`ptr` 非 NULL 且 `cpufreq_cpu_get()` 已对其取引用，故可写且在返回引用生命周期内有效」。

## 版本演进与当前进展

- v3 由 spidermana（`xuyiwen14@gmail.com`）于 09-28 重发（线程根 `<20260829161013.102967-1-mehmet.mkoseoglu@gmail.com>` 为 Mehmet 的 v1）。作者由 Mehmet 变更为 spidermana（或代发），Miguel 的疑问正是指向这一归属变化。

## Maintainer 意见与讨论焦点

- **Miguel Ojeda**（Rust-for-Linux 维护者）：对某 Reviewed-by 标签提出「The From: doesn't seem to match the email of the tag, is that intended?」，涉及补丁/标签的署名归属一致性。
- **Elowen Xu**（reviewer，非维护者）：`Reviewed-by: Elowen Xu <malanalyzing@gmail.com>`，另给一处 SAFETY 注释措辞 nit，并称「Either way, looks good to me」（还附了自己也踩到该问题的复现链接 Rust-for-Linux/linux#1258）。
- **spidermana**（作者）：更正自己此前的标签，「正确的标签是 `Reviewed-by: spidermana <xuyiwen14@gmail.com>`」。
- 无 NAK。剩余为署名/标签归属的收尾，代码本身无反对。

## 合入评估

*likelihood=high*。修复逻辑早已定型、有多位 reviewer 的 `Reviewed-by`（Elowen Xu、spidermana）、有复现佐证，无代码级反对；卡点只剩署名/标签归属澄清（Miguel 的疑问）与 SAFETY 注释 nit。*blocking_issues*：Miguel 关于 From/tag 归属的问题待澄清；SAFETY 注释 nit 待处理。*next_action*：作者澄清署名归属、按 nit 微调 SAFETY 注释后，等 Miguel 收取。

## 效果评估

无量化性能数据；正确性证据是「原转换下 KUnit 负控可复现 oops、改动后通过」及作者自报「Validated on a VM」。复现器仍为「available on request」，未公开。

## 我可以参与的点

- `review`：核对 `NonNull::new(...).ok_or(ENODEV)` 在 `cpufreq_cpu_get()` 返回 `ERR_PTR` 时是否被正确处理（与 `from_err_ptr` 的配合）。
- `testing`：在启用 Rust cpufreq 绑定的内核上跑 CPU policy 热插拔/未注册场景，验证不再 oops。

## 参考链接

- lore（v3 线程根）: https://lore.kernel.org/all/20260829161013.102967-1-mehmet.mkoseoglu@gmail.com/
- Miguel Ojeda 回复: https://lore.kernel.org/all/CANiq72ki8M1KmxhO4vSkMUfLcuqOMvZtuTNdDpS-UcJy8rqWpA@mail.gmail.com/
- spidermana 更正标签: https://lore.kernel.org/all/20260929095539.1398671-1-xuyiwen14@gmail.com/
