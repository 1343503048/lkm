---
id: sched-20260920-003
date: '2026-09-20'
subject: 'sched/doc: add a preemption model overview'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260920022003.1202546-1-quchaosheng000406@163.com>
lore_url: https://lore.kernel.org/all/20260920022003.1202546-1-quchaosheng000406@163.com/
authors:
- Quchaosheng
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260920022003.1202546-1-quchaosheng000406@163.com>
  date: '2026-09-20'
  summary: 新增 sched-preemption.rst，介绍四种抢占模型与 PREEMPT_LAZY 机制
  review_outcome: 首发，暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 缺 review 反馈，且 2/2 内容未获取到
  next_action: 等待文档维护者 review，核对 PREEMPT_LAZY 描述准确性
contribution_opportunities:
- kind: review
  description: 核对四种抢占模型及 PREEMPT_LAZY 表述与内核语义一致
generated_at: '2026-09-21T09:00:00'
source_email_count: 1
related_articles: []
tags:
- preempt
title: 'sched/doc: add a preemption model overview'
layout: article
---

## TL;DR
Quchaosheng 提交文档补丁（[PATCH 1/2]）：新增 `Documentation/scheduler/sched-preemption.rst`，系统介绍内核四种抢占模型（none/voluntary/full/lazy）及其运行时选择方式，并专门澄清最易被误解的 PREEMPT_LAZY（lazy 抢占）机制。本日为首发，暂无 review 意见。

## 背景与问题
现有调度文档只讲各调度类和调优旋钮，没有任何一处系统描述「抢占模型」本身；唯一提到抢占模型的地方是 `preempt=` 内核启动参数的 kernel-parameters 条目，但它只解释启动参数、不解释其选中的模型。作者希望补上这块空缺。

## 技术方案
新增 `Documentation/scheduler/sched-preemption.rst`（120 行，`create mode 100644`），并在 `Documentation/scheduler/index.rst` 中加入条目（`+    sched-preemption`）。内容要点：

- 定义四种抢占模型：none（仅在 cond_resched()/阻塞点抢占）、voluntary（none + might_sleep() 点）、full（未显式关抢占的任意段都可被抢占，含竞争自旋锁让步）、lazy（同 full，但 fair 调度器请求的 reschedule 不打断目标 CPU，在返回用户态或下一个 tick 时提交）。
- 说明 CONFIG_PREEMPT_DYNAMIC 开启时可用 `preempt=` 在启动时选择模型，无需重编内核。
- 澄清 PREEMPT_LAZY 易误解点：lazy reschedule 不发送跨 CPU 的 reschedule IPI，仅在返回用户态或下一个 tick 时提交；因此 tick 是 lazy 抢占延迟的上界，而常规实时延迟测试工具（唤醒固定在本 CPU 上的任务）根本不会触发它。

## 版本演进与当前进展
- v1（09-20，`<20260920022003.1202546-1-quchaosheng000406@163.com>`）：首发，1/2。当日缓存仅有 1/2；封面信（0/2）与 2/2 未获取到，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者或 reviewer 表态（v1 刚发出）。

## 合入评估
*likelihood=unknown*。文档类补丁、无实质风险，但尚无任何 review 反馈，合入可能性暂无法判断。*blocking_issues*：缺 review 反馈，且需确认 2/2 内容与整体系列完整性。*next_action*：等待调度文档维护者/资深成员 review，尤其核对 PREEMPT_LAZY 机制描述的准确性。

## 效果评估
暂无效果数据（纯文档，无运行时可度量项）。

## 我可以参与的点
- kind=review：核对 `sched-preemption.rst` 对四种抢占模型、尤其 PREEMPT_LAZY（lazy reschedule 不跨 CPU 发 IPI、tick 为上界）的表述是否与 `kernel/sched/core.c` 实际语义一致。

## 参考链接
- lore（patch 1/2）: https://lore.kernel.org/all/20260920022003.1202546-1-quchaosheng000406@163.com/
- cover letter（0/2）: 未获取到
