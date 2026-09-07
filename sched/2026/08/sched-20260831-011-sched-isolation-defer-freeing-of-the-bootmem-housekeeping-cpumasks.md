# sched/isolation: Defer freeing of the bootmem housekeeping cpumasks

## TL;DR

本文为增量更新（见 sched-20260802-001 / sched-20260803-013）。这条追查了大半个月的 nohz_full 启动期 cpumask 释放问题**当天正式收尾**：Ionut Nechita（Wind River）宣布撤回自己的补丁——同一问题早已被 Waiman Long 的 `2b58c749b8c5` ("sched/isolation: Defer freeing of cpumask memblock memory to initcall") 修掉，该 commit 由 Peter 收进 `sched/urgent` 并已在 **v7.3-rc1** 发布；作者同时会在 8/3 准备 v2 时才发现，明确表示"please drop this one, there will be no v2"，并把 bug 221804 关成 RESOLVED/CODE_FIX。**结论：不需要任何新代码，需要的是确认目标分支是否已含 `2b58c749b8c5`。**

## 背景与问题

`isolated_cpus`/nohz_full 的 housekeeping cpumask 在启动早期由 bootmem（memblock）分配；如果释放动作发生在页分配器已经初始化之后，就会用 bootmem 的释放路径去还已经被伙伴系统管理的内存，属于启动期内存管理错误。原线程（8/2 首见、8/3 出 v2 讨论）跟踪的就是这个"stale bootmem mask 延迟释放"问题，作者当时得到的反馈是一个 Ack 加若干注释级 nit。

本日给出的真实根因状态是：**该问题主线已有修法**——`2b58c749b8c5` 把过期 bootmem mask 记录到一个 `__initdata llist` 上，再由 `pure_initcall`（initcall level 0）释放；因为 level 0 的 initcall 从 `do_initcalls()`（位于 `do_basic_setup()`）里执行，时点在 `page_alloc_init_late()` **之后**，所以既不会在 bootmem 阶段提前还，也不会在页分配器就绪前触碰伙伴系统。

## 技术方案

本补丁被撤回，实际生效的方案是主线既有的 `2b58c749b8c5`。其做法（由本日邮件作者转述）：

- 用 `__initdata llist` 挂住需要延迟释放的 bootmem cpumask；
- 在 `pure_initcall`（level 0）里统一释放，保证跑在 `page_alloc_init_late()` 之后；
- 该 commit 由 Waiman Long 写于 2026-07-01，经 Peter Zijlstra 收进 `sched/urgent`，随 v7.3-rc1 发布。

被放弃的备选：Ionut 自己的延迟释放实现（含已获 Ack 的 v1 与准备中的 v2），原因是重复劳动。

## 版本演进与当前进展

- 8/2、8/3：本线程首见与 v2 讨论（见 related_articles）。
- 8/31 14:55：Ionut Nechita 发帖撤回（`<20260831065510.10645-1-ionut.nechita@windriver.com>`），说明"没有 v2"。
- 系列状态：**superseded**（由主线既有 commit 覆盖），不再推进。

## Maintainer 意见与讨论焦点

- 本日内没有 maintainer 回帖；线程中先前的实质意见是 Peter Zijlstra 的 Ack 与注释 nit（在被撤回的这封邮件里被作者转述）。
- 唯一的"意见"来自作者自我更正："I should have re-checked mainline before posting"——这实际上也说明了维护者为什么会接这个 Ack：主线当时的历史不容易一眼看出 `sched/urgent` 里已经有一条同名相近的修复（两者 subject 高度相似："Defer freeing of the bootmem housekeeping cpumasks" vs "Defer freeing of cpumask memblock memory to initcall"）。
- 值得记下的分歧/风险：两笔修复的 subject 几乎同义但实现路径不同，若下游只按 subject 检索，很容易误判"已修"或"未修"。

## 合入评估

**unlikely**（本补丁不会被合入，作者已撤回）。需要合的是主线既有的 `2b58c749b8c5`，它已经在 `sched/urgent` 且已随 v7.3-rc1 发布。对本人的实际含义：任何基于 v7.3-rc1 之前的分支若启用了 nohz_full/isolcpus，都应核对是否已回合该 commit；未回合的分支这个问题依然存在。

## 效果评估

无效果数据，也不该有——这是一次"避免重复修复"的更正，没有新的代码行为变化。原问题的可观测症状（启动期 bootmem 释放路径被误用）在主线由 `2b58c749b8c5` 消除，本日邮件未给出前后对比数据。

## 我可以参与的点

- **下游核对（最直接）**：在 OLK/内部分支上确认 `2b58c749b8c5` 是否已在，且 `pure_initcall` 与 `page_alloc_init_late()` 的先后关系在你的启动路径上是否成立（有些下游会改 initcall 顺序或引入早期 cpumask 使用者）。
- **流程性贡献**：本例是"补丁与主线既有修复 subject 近义重复、拿到 Ack 后才发现"的典型；如果社区有人关心，可以建议对 `sched/isolation` 这类低流量路径的修复加 `Link:` 到 bug 条目以便交叉检索——本邮件里 bug 221804 与 commit 的对应关系正是靠作者手工补齐。
- 除此之外当前阶段没有可参与的代码工作，系列已终止。

## 参考链接

- lore thread（撤回说明）: https://lore.kernel.org/all/20260831065510.10645-1-ionut.nechita@windriver.com/
- 被撤回的补丁（线程父帖）: https://lore.kernel.org/all/anA7GhzjZoi293Yy@kernel.org/
- 实际生效的主线修复: `2b58c749b8c5` ("sched/isolation: Defer freeing of cpumask memblock memory to initcall")，经 `sched/urgent`，v7.3-rc1
- 缺陷跟踪: bug 221804（作者称将关为 RESOLVED/CODE_FIX，具体 URL 未获取到）
- stable backport: 未获取到

---
id: sched-20260831-011
date: '2026-08-31'
subject: "sched/isolation: Defer freeing of the bootmem housekeeping cpumasks"
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: "<anA7GhzjZoi293Yy@kernel.org>"
lore_url: "https://lore.kernel.org/all/20260831065510.10645-1-ionut.nechita@windriver.com/"
authors: [Ionut Nechita]
maintainers_involved: [Peter Zijlstra, Waiman Long]
current_version: v1
patch_series:
  - version: v1
    msgid: "<anA7GhzjZoi293Yy@kernel.org>"
    date: 2026-08-02
    summary: "延迟释放 nohz_full/isolcpus 的 bootmem housekeeping cpumask"
    review_outcome: "曾获 Ack 与注释级 nit；作者 8/31 发现主线 2b58c749b8c5 已修同一问题，撤回并声明不发 v2"
upstream_commit: "2b58c749b8c5"
fixes_commit: null
merged_branch: "sched/urgent"
merge_assessment:
  likelihood: low
  blocking_issues:
    - "作者主动撤回：主线已有等价修复 2b58c749b8c5（v7.3-rc1）"
  next_action: "无（本补丁终止）；下游应核对是否已回合 2b58c749b8c5"
contribution_opportunities:
  - kind: review
    description: "在内部/长期分支上核对 2b58c749b8c5 是否已回合，并确认 pure_initcall 与 page_alloc_init_late() 的先后在该分支仍然成立"
generated_at: "2026-09-07T21:16:22"
source_email_count: 1
related_articles: [sched-20260802-001, sched-20260803-013]
tags: [nohz, affinity, crash]
---
