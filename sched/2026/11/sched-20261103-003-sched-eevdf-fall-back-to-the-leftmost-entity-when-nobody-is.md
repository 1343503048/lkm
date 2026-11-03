# sched/eevdf: fall back to the leftmost entity when nobody is eligible

## TL;DR

Aleksei Fedorov 的 RFC 补丁：`pick_eevdf()` 在多个实体 runnable 但无人 eligible（含 curr）时返回 NULL，调用方随后解引用崩溃；补丁在 NULL 时回退取最左实体并 `WARN_ON_ONCE`。Peter Zijlstra 明确否定：这个 WARN 杀伤力和 NULL 解引用一样大，应该找根因而不是打补丁。

## 背景与问题

在 Ubuntu linux-aws 6.8.0-1066.69 与 6.8.0-1063.66 上，`pick_eevdf()` 返回 NULL 后被解引用：`pick_next_task_fair+0x91, mov r14,[rax+0xa0], RAX = 0, CR2 = 0xa0`。一个 Xen HVM guest 在 2026-10-24 至 10-28 出现 5 次 oops。commit `1560d1f6eb6b`（"sched/eevdf: Prevent vlag from going out of bounds in reweight_eevdf()"）在两个内核里都有，但没能阻止 NULL 返回。

## 技术方案

在 `pick_eevdf()` 末尾追加：`if (unlikely(!best)) { best = __pick_first_entity(cfs_rq); WARN_ON_ONCE(best); }`，让 `schedule()` 能完成。作者明确承认：这只记录替换，不修复把每个实体都判成 ineligible 的 eligibility 状态。

## 版本演进与当前进展

*current_version: v1（RFC，2026-11-03 发出，msgid 20261103124242.102319-1-ring.zero.sh@gmail.com）*。当日 Peter Zijlstra 即回应。

## Maintainer 意见与讨论焦点

Peter Zijlstra 否定方案：「这个 WARN 很可能和 NULL 解引用一样地杀死你」；强调「陷入这种状态本身就说明哪里坏了，去找根因、修根因」；并建议先「试个新一点的内核，6.8 以来有 *一大堆* 改动」。核心分歧：作者只想止血，Peter 要求根本性修复。

## 合入评估

*likelihood=low*。Peter 明确排斥打补丁式止血，要求定位 eligibility 状态的根因；且作者基线是 6.8 老内核，很可能已在新内核被修复。*next_action*：作者需在较新内核（主线）上复现，若不再触发则结题；若复现则提供更完整的 eligibility 状态分析。

## 效果评估

作者在打了补丁的 guest 上（2026-10-31 16:08:42 UTC）WARN 触发一次（`pick_eevdf+0x22d`），至 2026-11-03 guest 仍运行、无进一步 oops——但这是「WARN 代替 oops」，并非根因修复。

## 我可以参与的点

- testing：在主线/newer kernel 上复现，确认该 NULL 返回是否已被后续改动消除。
- discussion：帮助分析「多实体 runnable 却无人 eligible」的 eligibility/vlag 状态何时出现。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103124242.102319-1-ring.zero.sh@gmail.com/

---
id: sched-20261103-003
date: 2026-11-03
subject: "sched/eevdf: fall back to the leftmost entity when nobody is eligible"
subsystem: sched
type: fix
status: rfc
severity: critical
thread_root_msgid: "<20261103124242.102319-1-ring.zero.sh@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261103124242.102319-1-ring.zero.sh@gmail.com/"
authors: [Aleksei Fedorov]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103124242.102319-1-ring.zero.sh@gmail.com>"
    date: 2026-11-03
    summary: "pick_eevdf() 返回 NULL 时回退取最左实体并 WARN_ON_ONCE，避免解引用崩溃。"
    review_outcome: "Peter 否定：要求找根因，且基线 6.8 太老。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["Peter 要求根因修复而非止血；基线 6.8 可能已被新内核修复"]
  next_action: "在主线复现并给出 eligibility 状态根因分析。"
contribution_opportunities:
  - kind: testing
    description: "在主线/newer kernel 复现 NULL 返回是否仍存在。"
  - kind: discussion
    description: "分析多实体 runnable 却无人 eligible 的触发条件。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [eevdf, crash]
---