---
id: sched-20260910-006
date: 2026-09-10
subject: 'sched/fair: Reset NUMA fault locality after scan period update'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/178903125575.623050.1039816034392719069.tip-bot2@tip-bot2/
upstream_commit: e81ee06308379a5f2ededf997bcf17551bce5db7
fixes_commit: null
merged_branch: tip/sched/core
current_version: v1
generated_at: '2026-09-11T10:20:00'
authors:
- Eric Kim
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v1
  msgid: null
  date: '2026-08-18'
  summary: update_task_scan_period() 早退分支 return 改 goto out，确保 numa_faults_locality
    总是被清空；原始投递 msgid 未获取到。
  review_outcome: 中间评审未获取到；09-10 Peter Zijlstra 合入 tip/sched/core 并 Cc stable。
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入主线与 stable 回合
contribution_opportunities:
- kind: new_patch
  description: 评估向自家分支回合该修复（缺陷长期存在且 Cc stable），回合时注意 out 标签重构与本地代码的差异
- kind: testing
  description: 构造迁移失败后恢复局部访问的负载，对比修复前后 numa_scan_period 演进，验证回合效果
source_email_count: 1
related_articles: []
tags:
- numa_balancing
- cfs
title: 'sched/fair: Reset NUMA fault locality after scan period update'
layout: article
---

## TL;DR
Eric Kim 的 NUMA balancing 修复被 Peter Zijlstra 合入 tip/sched/core（commit e81ee0630837，09-10 11:01 +0200，Cc stable）：update_task_scan_period() 的早退路径漏清 p->numa_faults_locality，导致扫描周期被无意拉长直至上限。本系列此前未被日报覆盖（原始投递邮件未进入缓存），本文以合入信息为准做首次记录。

## 背景与问题
NUMA balancing 用 p->numa_faults_locality[] 统计上一个扫描窗口内的 remote/local 故障数与迁移失败次数（下标 2），update_task_scan_period() 据此决定加快还是放慢扫描。当「无故障记录或上次窗口有迁移失败」时走早退分支：把 numa_scan_period 直接翻倍（封顶 numa_scan_period_max）后 return。问题在于该早退路径跳过了函数末尾的 `memset(p->numa_faults_locality, 0, ...)`：陈旧的非零 locality 计数（尤其 numa_faults_locality[2] 迁移失败标记）会残留到下一个窗口，使任务在后续每次评估中都继续命中早退分支，numa_scan_period 被 unintentionally 一路翻倍到 numa_scan_period_max——即使实际上既没有迁移失败也没有故障。后果是 NUMA balancing 对这类任务近乎停摆。触发条件：开启 automatic NUMA balancing、任务经历一次迁移失败或空窗口后进入正常局部性模式。

我在本地主线工作区（kernel/sched/fair.c，commit e1ba4c925742 基线）核对：早退分支仍是裸 `return;`（fair.c:3470 附近），memset 只在函数正常路径末尾（fair.c:3516），缺陷确实存在，与本修复描述一致。

## 技术方案
最小修复：把早退分支的 `return;` 改为 `goto out;`，并把 memset 移到 out: 标签下，保证两条路径都清空 numa_faults_locality。diffstat：kernel/sched/fair.c | 7 +++++--（5 insertions, 2 deletions）。没有引入新状态或接口，语义上是「locality 统计窗口与扫描周期更新严格同步」。

## 版本演进与当前进展
原始补丁 AuthorDate 2026-08-18（Eric Kim），由 Binwon Song 报告（Reported-by，Closes 指向 2025-04-04 的报告线程）。09-10 以 tip-bot 通知形式确认合入 tip/sched/core：Commit-ID e81ee06308379a5f2ededf997bcf17551bce5db7，CommitterDate 09-10 11:01:30 +0200，带 Cc: stable@vger.kernel.org。原始投递邮件与中间评审过程未进入本缓存，版本演进细节未获取到；合入邮件中无 Fixes: 标签。

## Maintainer 意见与讨论焦点
本日缓存中仅有 tip-bot 合入通知，committer 为 Peter Zijlstra，可确认其已接受该修复；中间评审意见未获取到。无可见分歧。

## 合入评估
已合入：tip/sched/core，commit e81ee06308379a5f2ededf997bcf17551bce5db7（likelihood: merged），且 Cc stable，预计会回合到 stable 分支。走 sched/core 而非 urgent，说明定级为常规修复而非紧急回归。

## 效果评估
合入邮件未附 benchmark。可推断的收益：受影响任务的 numa_scan_period 不再被陈旧计数锁死在上限，NUMA balancing 恢复正常的周期调节。具体量化数据未获取到。

## 我可以参与的点
- 自家分支（OLK-6.6 等）若启用了 NUMA balancing，可评估回合该修复：缺陷自 numa_faults_locality 引入以来长期存在且带 Cc stable，回合价值明确（new_patch）。
- 构造「一次迁移失败后恢复局部访问」的负载，对比修复前后 numa_scan_period 的演进曲线，验证 stable 回合效果（testing）。

## 参考链接
- tip-bot 合入通知: https://lore.kernel.org/all/178903125575.623050.1039816034392719069.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/e81ee06308379a5f2ededf997bcf17551bce5db7
- 原始问题报告（Closes）: https://lore.kernel.org/all/20250404095354.311156-1-qlsdnjs236@chungbuk.ac.kr/
- 原始补丁投递邮件: 未获取到（tip-bot 通知中 Link 字段损坏，缓存内无该邮件）
