---
id: sched-20261120-017
date: '2026-11-20'
subject: 'sched/topology: Avoid unsequenced accesses to jiffies in sd_init()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org>
lore_url: https://lore.kernel.org/all/20261119224129.GA1660308@ax162
authors:
- Nathan Chancellor
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org>
  date: '2026-11-16'
  summary: 把两处 jiffies 初始化移出 initializer 加序列点
  review_outcome: Peter 质疑必要性，Nathan 坚持并愿改 changelog
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 对修法必要性的质疑未化解
  next_action: Nathan 改好 commit message 后重发说服 Peter
contribution_opportunities:
- kind: discussion
  description: 就 jiffies volatile 存废与 READ_ONCE 风格给出工程判断或 C 标准佐证
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles:
- sched-20261115-005
- sched-20261118-007
tags:
- topology
title: 'sched/topology: Avoid unsequenced accesses to jiffies in sd_init()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/15/sched-20261115-005-sched-topology-avoid-unsequenced-accesses-to-jiffies-in-sd-i.html">sched-20261115-005</a>：Nathan Chancellor 修 clang `-Wunsequenced` 构建破坏——`sd_init()` designated initializer 里两处 `= jiffies` 对 volatile 变量未定序访问（Fixes: 2b4cfe64dee0，Cc: stable）。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-007-sched-topology-avoid-unsequenced-accesses-to-jiffies-in-sd-i.html">sched-20261118-007</a>：v2 引发 Peter 对「修法是否必要 / volatile 存废」的元讨论。
- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-017-sched-topology-avoid-unsequenced-accesses-to-jiffies-in-sd-i.html">sched-20261120-017</a>（今天）：**Nathan 坚持补丁必要并愿意改进 commit message**——回应 cast 也不解决问题（访问仍 unsequenced）、与 David Laight 指出的「一致性隐患」；讨论仍停留在「编译器告警要不要迁就」的元层面，未见收敛与新版本。

## 背景与问题

（承接）clang 改进 volatile 未定序访问告警后，`sd_init()` 的 designated initializer 里两处 `= jiffies` 触发 `-Wunsequenced`（未定序 side effect，属 UB），`CONFIG_WERROR=y`/`W=1` 下构建失败。讨论焦点从「怎么修」升级到「该不该修 / jiffies 是否该继续是 volatile」。

## 技术方案

今日为讨论、无新代码：Nathan 回应「即便 cast 也不解决问题——访问仍是 unsequenced」；对 David Laight 指出的「两次读 jiffies 可能得到不同值」的一致性隐患，Nathan 认为 clang 的告警「确实在帮忙」，并给出两个清晰选择：要么用局部变量读一次再用于 initializer（本补丁做法），要么把每次访问移出 initializer（他的 v1 做法）；表示愿意配合把 commit message 改得更好。

## 版本演进与当前进展

*current_version: v2（2026-11-16，`<20261116-topology-wunsequenced-v2-1-54611119172b@kernel.org>`，单补丁）*。今日为讨论日、无新版本；作者坚持必要性并承诺改进 changelog。

## Maintainer 意见与讨论焦点

- **Nathan Chancellor（作者，ClangBuiltLinux 维护者）**：坚持补丁必要（UB 防御），cast 不解决问题，愿意改 commit message。
- **Peter Zijlstra（sched maintainer）**：前情质疑「修法是否必要」、主张问题在 clang 告警过激。
- **David Laight**：前情指出两次读 jiffies 的一致性隐患。
- 无 NAK；「迁不迁就编译器告警」的元分歧未收敛。

## 合入评估

*likelihood=medium*。构建破坏修复动机充分、作者专业（ClangBuiltLinux 维护者），但 Peter 对「修法本身」的保留尚未化解，需在 commit message 与「为何必须改」上说服维护者。*blocking_issues*：Peter 对修法必要性的质疑未化解。*next_action*：Nathan 改好 commit message 后重发，说服 Peter 收取。

## 效果评估

无性能数据；价值在消除 UB 与构建告警，使 `W=1`/`WERROR` 构建通过。

## 我可以参与的点

- **discussion**：就「jiffies 继续声明为 volatile vs 改用 READ_ONCE 风格」给出工程判断，或佐证 clang 告警的 C 标准依据。

## 参考链接

- lore thread（Nathan 回复）: https://lore.kernel.org/all/20261119224129.GA1660308@ax162
