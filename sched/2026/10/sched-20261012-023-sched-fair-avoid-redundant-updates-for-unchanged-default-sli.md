# sched/fair: avoid redundant updates for unchanged default slices

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261009-008 / 20261010-002：Chengfeng Lin 发 RFC——`sched_setparam()` 在参数未变时仍走参数更新路径，SCHED_OTHER 任务用默认 slice 且 slice 未变时直接走 no-change 捷径；原型把每次调用从 618.18ns 降到 163.23ns（省 455ns，约 73.6%）。
- sched-20261012-023（今天）：Peter Zijlstra 吐槽「太多文字才能找到问题点」，质疑实现难读、可能错误（`attr->sched_runtime == se->slice` 但 `!se->custom_slice`、或 slice 相同但仍需因 uclamp 更新），并给出更简的条件表达；同时追问「是否因为此改动看到 PI cost 增加」。

## 背景与问题

（承接 20261009-008/20261010-002）优化 `sched_setparam()` 在参数未变时的冗余路径开销。今日 Peter 的关切是：判断「是否真的无变化」的条件必须精确覆盖 custom_slice 与 uclamp 等情形。

## 技术方案

（承接 20261009-008/20261010-002）Peter 给出建议的简化条件：先 `if (!!attr->sched_runtime != !!se->custom_slice) return true;`，再 `if (attr->sched_runtime && attr->sched_runtime != se->slice) return true;`——用「是否设置了 runtime」与「custom_slice 是否一致」作为变化判定，避免漏判 uclamp 等场景。

## 版本演进与当前进展

v1（10-09）→ 今日（10-12）Peter 负评 + 给简化条件；尚无 v2。

## Maintainer 意见与讨论焦点

Peter Zijlstra：批评可读性（「Egads, this is unreadable」）、指出条件可能的正确性漏洞（custom_slice/uclamp）、追问 PI cost 增加是否属实；给出更简洁的重写方向。

## 合入评估

*likelihood=low*。RFC 阶段、维护者负评，需按建议重写。*blocking_issues*：可读性 + 正确性 + PI cost 疑点。*next_action*：作者按简化条件重写并回应 PI cost。

## 效果评估

无新数据；此前 618.18ns→163.23ns 的合成 syscall 微基准仍在（作者明说非应用加速）。

## 我可以参与的点

- `review`：核对 Peter 的简化条件在 uclamp、custom_slice 组合下的完备性，以及原实现是否真的会漏更新。

## 参考链接

- lore（Peter 负评 + 简化条件）: https://lore.kernel.org/all/20261012105953.GR4121339@noisy.programming.kicks-ass.net/

---
id: sched-20261012-023
date: '2026-10-12'
subject: 'sched/fair: avoid redundant updates for unchanged default slices'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com/
authors:
- Chengfeng Lin
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter 批评实现难读、条件可能错误（custom_slice/uclamp 情形），并追问 PI cost 增加
  next_action: 作者按 Peter 给出的简化条件重写并澄清 PI cost 增加
contribution_opportunities:
- kind: review
  description: 核对 Peter 提出的简化条件（!!attr->sched_runtime != !!se->custom_slice 等）与 uclamp 交互
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20261009-008
- sched-20261010-002
tags:
- cfs
---
