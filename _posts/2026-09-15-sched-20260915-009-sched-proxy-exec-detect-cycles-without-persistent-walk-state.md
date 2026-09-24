---
id: sched-20260915-009
date: '2026-09-15'
subject: 'sched/proxy_exec: detect cycles without persistent walk state'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <20260914165455.2126134-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260914165455.2126134-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260914165455.2126134-1-sh_def@163.com>
  date: '2026-09-15'
  summary: Brent checkpoint 算法直接嵌入真实 owner walk 检测 blocked_on 环，无持久状态
  review_outcome: 暂无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 短暂 blocked_donor 环的安全窗口未被独立论证
  - 与 v5 持久标记方案的取舍需维护者裁决
  next_action: 等 proxy_exec 维护者就该取舍表态，可补充更多调度交错下的证明或测试
contribution_opportunities:
- kind: review
  description: 复核短暂 blocked_donor 环在 rq->lock 持有期间是否可能被其它链读者观察到并误用
- kind: testing
  description: 在多层 mutex、并发 handoff 交错下做压力测试，验证环检测与 forced-stale revalidation
generated_at: '2026-09-16T01:05:00'
source_email_count: 2
related_articles: []
tags:
- proxy_execution
title: 'sched/proxy_exec: detect cycles without persistent walk state'
layout: article
---

## TL;DR
Hui Su 09-15 发 RFC（0/1）：用 Brent 环形检测算法直接在 find_proxy_task() 的真实 owner walk 里检测 blocked_on 链的环，避免 Zhidao Su v5 序列标记方案需要的 task_struct/rq 持久状态与激活时复位。核心取舍：允许 walk 短暂安装 blocked_donor 环，用延迟的 checkpoint 检测点来发现并 `__clear_task_blocked_on()` 脱环。作者给了与 v5 的同基对比数据（无环路径 ns/call 相当），并明确「不声称覆盖所有调度交错」。合入判断 unknown，尚未见维护者表态。

## 背景与问题
proxy execution 沿 blocked_on 关系找可运行 lock owner；若该链存在环，`find_proxy_task()` 会在持 rq->lock 的情况下无限循环。Zhidao Su 的 v5 用 task_struct 与 struct rq 里的序列状态检测重复、并在激活时复位任务标记；本 RFC 探索另一取舍：把环形检测状态完全保持在本 walk 的调用栈内，不加持久状态。

## 技术方案
把 Brent 的 checkpoint 算法直接用在既有 owner walk 上：checkpoint/power/span 均 invocation-local；环检测复用 walk 已做的 owner 解析，无需单独的 preflight 遍历。检测到 `owner == cycle_checkpoint` 时 `pr_warn_once("sched/pe: deadlock cycle detected, pid %d")` 并 `__clear_task_blocked_on(p, NULL)` 脱环后走 deactivate。既有的 `owner == p` wakeup-race 处理保持在环检测之前（该状态本身不证明死锁环）。kernel/sched/core.c 仅 +19 行。

## 版本演进与当前进展
本日为 RFC v1（`<20260914165455.2126134-1-sh_def@163.com>`），作为对 Zhidao Su v5（`20260722120346.93000-1-soolaugust@gmail.com`）的独立备选方案发出，暂无回复。

## Maintainer 意见与讨论焦点
本日无维护者回帖。作者的自我评估点（cover 原文）：Online Brent 会在延迟检测点之前短暂安装 blocked_donor 环；自然恢复路径下被选中的环成员在 mutex_unlock() 前 blocked_donor 已清除；强制的 forced-stale 对照确认既有 blocked_on revalidation 会拒绝 stale handoff。作者明确「不证明所有调度交错」——这是本 RFC 的核心待审争议点（接受短暂 backlink 窗口 vs 持久访问状态）。

## 合入评估
*likelihood=unknown*。RFC 且无人表态，方案取舍（短暂环窗口 vs v5 的持久标记）尚无维护者裁决。*blocking_issues*：短暂 blocked_donor 环的安全窗口未被独立论证；与 v5 的取舍需维护者判断。*next_action*：等 proxy_exec 相关维护者（John Stultz/Prateek 等）就该取舍表态；可补充更多调度交错下的证明或测试。

## 效果评估
作者给出与 v5 同基、同配置（x86_64、KVM、4 vCPU、host affinity 8-11）下无环 find_proxy_task() 的 ns/call 中位数对比（五轮取中位）：depth 16→442 vs 500（0.884）、32→612 vs 584（1.048）、64→988 vs 1314（0.752）、128→1942 vs 2276（0.853）、256→4815 vs 4561（1.056）、512→8396 vs 9338（0.899）、1024 深度在 cover 中未截全。总体与 v5 相当、互有胜负。作者注明这些是 staging 测试用例下的结果，不覆盖全部调度交错。

## 我可以参与的点
- kind=review：审查「短暂安装 blocked_donor 环」在 rq->lock 持有期间是否可能被其它 blocked_on 链读者观察到并误用（作者自述未发现该读者，可独立复核）。
- kind=testing：在更复杂的锁交错场景（多层 mutex、并发 handoff）下做压力测试，验证环检测与 forced-stale revalidation 的稳健性。

## 参考链接
- RFC cover：https://lore.kernel.org/all/20260914165455.2126134-1-sh_def@163.com/
- RFC patch 1/1：https://lore.kernel.org/all/20260914165455.2126134-2-sh_def@163.com/
- Zhidao Su v5：https://lore.kernel.org/r/20260722120346.93000-1-soolaugust@gmail.com/
