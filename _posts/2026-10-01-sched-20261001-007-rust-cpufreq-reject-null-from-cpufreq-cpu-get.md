---
id: sched-20261001-007
date: '2026-10-01'
subject: 'rust: cpufreq: reject NULL from cpufreq_cpu_get()'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261001102213.45437-1-mehmet.mkoseoglu@gmail.com>
lore_url: https://lore.kernel.org/all/20261001102213.45437-1-mehmet.mkoseoglu@gmail.com/
authors:
- Mehmet Koseoglu
maintainers_involved:
- Viresh Kumar
current_version: v4
patch_series:
- version: v3
  msgid: <20260928162214.487564-1-xuyiwen14@gmail.com>
  date: '2026-09-28'
  summary: NonNull::new(...).ok_or(ENODEV)? 显式拒 NULL；由 spidermana 重发
  review_outcome: 已被 Viresh 应用于 0ba1ee052b3f（作者一度不知情）
- version: v4
  msgid: <20261001102213.45437-1-mehmet.mkoseoglu@gmail.com>
  date: '2026-10-01'
  summary: SAFETY 注释澄清 + Onur Özkan/spidermana Reviewed-by，替换树中 v3
  review_outcome: Viresh 承诺应用 v4 并丢弃旧版
upstream_commit: 0ba1ee052b3f
fixes_commit: 6ebdd7c93177
merged_branch: null
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: Viresh 应用 v4 并 drop 0ba1ee052b3f，跟踪替换 commit
contribution_opportunities:
- kind: testing
  description: 在 Rust cpufreq 绑定内核上跑 policy 热插拔/未注册场景验证不再 oops
generated_at: '2026-10-09T01:00:00'
source_email_count: 4
related_articles:
- sched-20260830-006
- sched-20260929-006
tags:
- cpufreq
title: 'rust: cpufreq: reject NULL from cpufreq_cpu_get()'
layout: article
---

> **subject**：`rust: cpufreq: reject NULL from cpufreq_cpu_get()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/30/sched-20260830-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260830-006</a> / <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260929-006</a>：Mehmet Koseoglu 的 Rust cpufreq 绑定修复走到 v3（由 spidermana 重发、标签归属引发 Miguel Ojeda 疑问、Elowen Xu 给 SAFETY 注释 nit 与 `Reviewed-by`）——`PolicyCpu::from_cpu()` 的 `from_err_ptr()` 只拒 `ERR_PTR` 不拒 NULL，查表失败时用 NULL 构造可变引用，drop 时把非法指针传给 `cpufreq_cpu_put()` 在 `kobject_put()` oops；改法 `NonNull::new(...).ok_or(ENODEV)?`。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-007-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20261001-007</a>（今天）：剧情反转——Viresh Kumar（cpufreq 维护者）发现 v3 其实**几周前已被应用为 commit `0ba1ee052b3f`**（度假前收的、自己忘了），请作者重发完整版；Mehmet 随即发 **v4**：澄清 SAFETY 注释（指针非 NULL 且 `cpufreq_cpu_get()` 已取引用）、补上 Onur Özkan 与 spidermana（更正版）两个 `Reviewed-by`，Viresh 将应用 v4 并丢弃旧 v3。带 `Fixes: 6ebdd7c93177`、`Cc: stable`、`Assisted-by: LLM`。

## 背景与问题

（承接）缺陷位于 `rust/kernel/cpufreq.rs` 的 `PolicyCpu::from_cpu()`：`cpufreq_cpu_get()` 契约是「返回带引用的 policy 或 NULL」，原实现 `from_err_ptr(...)?` 只对 `ERR_PTR` 报错、NULL 被当作有效指针走 `Policy::from_raw_mut(ptr)`，随后 `PolicyCpu` drop 时把 NULL 交给 `cpufreq_cpu_put()` 在 `kobject_put()` 里 oops。触发条件是 policy 查表失败等错误路径。今天的新事实：v3 已作为 `0ba1ee052b3f` 进入 cpufreq 树（因此 oops 风险已解除），剩余工作是把「SAFETY 注释澄清 + 汇齐 review 标签」的 v4 换掉树里的旧版。

## 技术方案

（承接）核心改法不变：`NonNull::new(unsafe { bindings::cpufreq_cpu_get(u32::from(cpu)) }).ok_or(ENODEV)?` 显式拒 NULL（`NonNull<T>` 在构造点建立「指针非 NULL」不变式），错误码 `ENODEV` 与「该 CPU 无 policy」一致，import 改内核竖排风格。v4 的增量：SAFETY 注释改写为「`ptr` is non-NULL and `cpufreq_cpu_get()` took a reference on it, so it is valid for writing and remains valid for the lifetime of the returned reference」；补 `Reviewed-by: Onur Özkan <work@onurozkan.dev>` 与 `Reviewed-by: spidermana <xuyiwen14@gmail.com>`（采用其更正后的归属）。

## 版本演进与当前进展

- v1（08-29，`<20260829161013.102967-1-mehmet.mkoseoglu@gmail.com>`，线程根）→ v2（08-28 重发，竖排 import）→ v3（09-28 由 spidermana 重发，`Cc: stable`；标签归属引发 Miguel 疑问，见 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-006-rust-cpufreq-reject-null-from-cpufreq-cpu-get.html">sched-20260929-006</a>）。
- 10-01：Mehmet 问 Viresh「v3 已被应用为 0ba1ee052b3f，后续是 follow-up 补注释还是 v4 重发」（`<DLTEONSHWRPQ.1U2Y6GDBRURFX@gmail.com>`）→ Viresh：「Oops, I thought I haven't applied it yet. I did that couple of week ago before I went on vacation :( You can resend the patch and I will apply the new one and drop the old one.」（`<ar4ux5SVxjlzTGvL@vireshk-B250M-D3H>`）→ Mehmet 发 v4（`<20261001102213.45437-1-mehmet.mkoseoglu@gmail.com>`）。

## Maintainer 意见与讨论焦点

- **Viresh Kumar**（cpufreq 维护者）：确认 v3 已应用为 `0ba1ee052b3f`；要求重发完整版（此前 09-29 已说过「Please resend the patch with all the fixes / tags / improvements」），将应用新版并丢弃旧版。
- **Mehmet Koseoglu**（作者）：v4 落实 SAFETY 注释澄清与两个 `Reviewed-by`，`Assisted-by: LLM`。
- 09-29 遗留的署名归属问题（Miguel 的 From/tag 疑问）在 v4 中以「spidermana 更正版标签」收口；Miguel 未再回帖。
- 无 NAK。

## 合入评估

*likelihood=merged*。修复本体已以 `0ba1ee052b3f` 落入 cpufreq 树；v4（注释澄清 + 标签齐全）在维护者明确「应用新版丢弃旧版」的承诺下，等价于已定案的替换操作。*blocking_issues*：无（v4 的正式应用通告尚未出现，属事务性收尾）。*next_action*：Viresh 应用 v4 并 drop 0ba1ee052b3f；跟踪替换 commit。

## 效果评估

本日无新数据。既有证据：KUnit 负控在原转换下复现 oops、改后通过；作者自报「Validated on a VM」；复现器「available on request」未公开。v4 与 v3 功能等价（注释/标签差异），不改变行为。

## 我可以参与的点

- `testing`：在启用 Rust cpufreq 绑定的内核上跑 CPU policy 热插拔/未注册场景，验证 `0ba1ee052b3f`（及 v4 替换后）不再 oops——`Assisted-by: LLM` 的补丁多一份人工实测更有说服力。

## 参考链接

- Mehmet v4: https://lore.kernel.org/all/20261001102213.45437-1-mehmet.mkoseoglu@gmail.com/
- Viresh 的回复（应用新版丢旧版）: https://lore.kernel.org/all/ar4ux5SVxjlzTGvL@vireshk-B250M-D3H/
- Mehmet 的确认请求: https://lore.kernel.org/all/DLTEONSHWRPQ.1U2Y6GDBRURFX@gmail.com/
- v3 线程根: https://lore.kernel.org/all/20260829161013.102967-1-mehmet.mkoseoglu@gmail.com/
