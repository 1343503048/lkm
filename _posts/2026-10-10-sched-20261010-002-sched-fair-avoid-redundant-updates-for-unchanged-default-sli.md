---
id: sched-20261010-002
date: '2026-10-10'
subject: 'sched/fair: avoid redundant updates for unchanged default slices'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com/
authors:
- Chengfeng Lin
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>
  date: '2026-10-09'
  summary: sched_setparam() 参数未变时走 no-change 捷径，默认 slice 未变化的 SCHED_OTHER 任务
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  - 真实应用收益未知（作者自述 synthetic microbenchmark）
  next_action: 等维护者判断捷径价值并确认 uclamp 重置边界
contribution_opportunities:
- kind: review
  description: 复核 no-change 捷径与 RT PI 结束后 uclamp 重置边界的交互
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
- sched-20261009-008
tags:
- cfs
title: 'sched/fair: avoid redundant updates for unchanged default slices'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-008-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261009-008</a>：Chengfeng Lin 发 RFC，优化 `sched_setparam()` 在参数未变时仍走参数更新路径的开销——SCHED_OTHER 任务用默认 slice 且 slice 未变时直接走 no-change 捷径；原型把每次 `sched_setparam()` 调用成本从 618.18ns 降到 163.23ns（省 455ns、约 73.6%）。属合成 syscall 微基准，作者明确「不是应用加速」。当日无回帖。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-002-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261010-002</a>（今天）：作者重发——上一封内联 patch 经邮件传输丢失了 tab 缩进，今天补上「保留原始格式」的 patch，`git apply --check` 对 v7.2 通过；代码与测试结果不变，属格式性重发，仍无维护者回帖。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-008-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261009-008</a>）`sched_setparam()` 在参数未变化时仍会走完整的参数更新路径，带来无谓开销。作者用合成 syscall 微基准量化：每次调用的成本 618.18ns → 163.23ns（省 455ns）。作者自己划定的关键边界：隐含的 uclamp 重置（RT PI 结束后）必须仍走完整更新——这一约束是否正确是合入前需 reviewer 确认的点。今天无新的技术内容，仅补发格式正确的 patch。

## 技术方案
（承接）当 SCHED_OTHER 任务使用默认 slice 且 slice 未变时，直接走 no-change 捷径，跳过冗余的参数更新。今天作者在原内联 patch 之外补发了保留 tab 缩进的原始 patch（`git apply --check` 对 v7.2 通过），代码逻辑与测试结果不变。

## 版本演进与当前进展
*current_version: v1*（RFC）。今天 Chengfeng Lin 自回帖（`<CANGjgdmmH6SypmZCXHKv_7pDWRPGRnPdT9-opAc+34uqUB8r_Q@mail.gmail.com>`）：说明上一封内联 patch 的 tab 缩进在发送时丢失，本次附上保留格式的原始 patch，`git apply --check` 对 v7.2 通过；代码与测试结果不变。无其他社区回帖。

## Maintainer 意见与讨论焦点
当日无回帖、无维护者表态。仍需 reviewer 确认的核心边界：no-change 捷径是否会绕过「RT PI 结束后隐含 uclamp 重置必须走完整更新」的需求。

## 合入评估
*likelihood=unknown*。RFC 当日无回帖；且这是合成 syscall 微基准驱动的优化，社区对「为微基准增益引入 no-change 捷径」通常要求评估真实收益与边界复杂度。*blocking_issues*：无 review；真实应用收益未知（作者自述「synthetic microbenchmark, not an application speedup」）。*next_action*：等维护者判断该捷径是否值得、边界（尤其 uclamp 重置）是否完整。

## 效果评估
作者的合成微基准：每次 `sched_setparam()` 调用成本 618.18ns → 163.23ns（省 455ns、约 73.6%）。作者明确标注这是合成微基准、非应用加速；今日重发未新增数据。

## 我可以参与的点
- 复核 no-change 捷径与 uclamp 重置（RT PI 结束后）边界的交互是否正确；
- 若有真实调 `sched_setparam()` 频率较高的负载，可测一下应用层收益是否可观。

## 参考链接
- RFC v1（lore）: https://lore.kernel.org/all/CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com/
- 今日格式重发: https://lore.kernel.org/all/CANGjgdmmH6SypmZCXHKv_7pDWRPGRnPdT9-opAc+34uqUB8r_Q@mail.gmail.com/
