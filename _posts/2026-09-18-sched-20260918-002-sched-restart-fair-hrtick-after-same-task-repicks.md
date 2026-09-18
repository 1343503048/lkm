---
id: sched-20260918-002
date: '2026-09-18'
subject: 'sched: Restart fair hrtick after same-task repicks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org>
lore_url: https://lore.kernel.org/all/20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved:
- Zhan Xusheng
current_version: v4
patch_series:
- version: v1
  msgid: <20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>
  date: '2026-08-13'
  summary: 首版：重启 fair hrtick
  review_outcome: 暂无记录
- version: v2
  msgid: <20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>
  date: '2026-09-11'
  summary: 用 SNT_REPICK 取代 fair 专用状态，fair/DL 都重启
  review_outcome: 无
- version: v3
  msgid: <20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>
  date: '2026-09-15'
  summary: 移除 SCHED_DEADLINE 的 SNT_REPICK 重启
  review_outcome: 获 Zhan Xusheng Reviewed-by
- version: v4
  msgid: <20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org>
  date: '2026-09-17'
  summary: 澄清 fair/DL 重启差异原因，文档化 SNT_* 调用点语义
  review_outcome: 本日刚发出，暂无新 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 核心维护者尚未对 SNT_REPICK 复用路径表态
  next_action: 等待 Peter/Vincent 等维护者 review，按反馈出 v5
contribution_opportunities:
- kind: testing
  description: 在 arm64/riscv + HRTICK 平台复测 v4 抢占延迟与 DL 行为
- kind: review
  description: 审查 SNT_REPICK 对各 sched class（尤其 sched_ext）的影响
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles:
- sched-20260917-005
- sched-20260916-017
tags:
- cfs
- deadline
- preempt
title: 'sched: Restart fair hrtick after same-task repicks'
layout: article
---

## TL;DR
增量更新：Shubhang Kaushik 的 fair hrtick 修复系列推出 v4（新增 SNT_REPICK 复用 set_next_task_fair() 重启 one-shot hrtick；明确 fair 可重启而 DL 不可的原因；文档化 SNT_NORMAL/SNT_PICK/SNT_REPICK 语义）。本日 v4 刚发出、暂无新 review；此前已获 Zhan Xusheng 的 Reviewed-by，并带 HRTICK 延迟 90/99 分位实测数据。

## 背景与问题
背景见 sched-20260917-005：fair hrtick 是 one-shot 定时器，hrtick 到期后若 pick_task_fair() 又选中同一个任务（same-task repick），put_prev_set_next_task() 因 next==prev 提前返回、跳过 set_next_task_fair()，导致下一个 fair 抢占点没有 hrtick 被重新武装，抢占粒度丢失。

## 技术方案
- 引入 `SNT_REPICK` 复用路径：`put_prev_set_next_task()` 在 next==prev 时调用 `next->sched_class->set_next_task(rq, next, SNT_REPICK)`，`set_next_task_fair()` 跳过任务切换工作、仅调用 `hrtick_start_fair()` 重启 hrtick；`hrtick_start()` 在 schedule() 期间记录 delay，`hrtick_schedule_exit()` 重新武装定时器。
- 明确不为 SCHED_DEADLINE 重启 SNT_REPICK hrtick：DL picker 没有对应的 current-runtime 刷新，重启会用陈旧的 `dl_se->runtime` 推迟下一次 runtime 强制点；而 fair 在 pick 前已刷新选中 entity。
- 改动涉及 `kernel/sched/{core.c,deadline.c,fair.c,idle.c}` 与 `ext/ext.c`。

## 版本演进与当前进展
- v1（2026-08-13，`<20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>`）：首版。
- v2（2026-09-11，`<20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>`）：用 SNT_REPICK 取代 fair 专用重启状态，fair/DL 都重启，删除 delayed-dequeue runnable-count 条件。
- v3（2026-09-15，`<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>`）：从 v2 移除 SCHED_DEADLINE 的 SNT_REPICK 重启。
- v4（2026-09-17，`<20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org>`）：澄清 fair 可重启/DL 不可重启的原因，文档化 SNT_NORMAL/SNT_PICK/SNT_REPICK 调用点语义，build-test CONFIG_SCHED_CLASS_EXT=y。

## Maintainer 意见与讨论焦点
- 本日 v4 无新回复。此前系列演进的核心反馈是：DL 的 SNT_REPICK 重启会读到陈旧 runtime（作者已在 v3/v4 中据此移除 DL 重启并说明理由）。
- 已获 **Zhan Xusheng** 的 Reviewed-by。暂无维护者明确 NAK 或阻塞意见。

## 合入评估
likelihood=medium。方向明确、逻辑自洽、带实测数据且有 Reviewed-by，但尚未获得 Peter/Vincent 等核心维护者的 Ack。blocking_issues：核心维护者尚未表态；SNT_REPICK 复用路径的接口改动需要维护者确认。next_action：等待维护者 review；如有意见按反馈出 v5。

## 效果评估
作者 v3 实测（HRTICK + DELAY_DEQUEUE，base_slice_ns=3000000）：p90 从 3.998ms 降到 3.053ms，p99 从 5.144ms 降到 4.533ms；HRTICK_DL stress-ng 冒烟 2691 bogo ops 无新 dmesg 告警；CONFIG_HIGH_RES_TIMERS=n（禁用 HRTICK）内核可正常启动、30 秒 stress-ng 无新告警。

## 我可以参与的点
- kind=testing：在启用 HRTICK 的 arm64/riscv 平台上复测 v4 的抢占延迟与 DL 行为（现有数据来自 x86）。
- kind=review：审查 SNT_REPICK 复用 `set_next_task()` 路径对各 sched class（尤其 sched_ext）的影响。

## 参考链接
- lore（v4）: https://lore.kernel.org/all/20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org/
- lore（v3）: https://lore.kernel.org/r/20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org
