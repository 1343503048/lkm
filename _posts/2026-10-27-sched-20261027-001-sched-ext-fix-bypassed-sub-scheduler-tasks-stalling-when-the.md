---
id: sched-20261027-001
date: 2026-10-27
subject: 'sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks
  caps'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261027001749.1821379-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261027001749.1821379-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v4
patch_series:
- version: v1
  msgid: <20261022213836.2259069-1-tj@kernel.org>
  date: 2026-10-22
  summary: 首个版本，bypass stall 修复
  review_outcome: 无当日 review
- version: v2
  msgid: <20261023052452.2889061-1-tj@kernel.org>
  date: 2026-10-23
  summary: 15 patches，按 Sashiko review 修订 rescue slice
  review_outcome: Sashiko review 已吸收
- version: v3
  msgid: <20261023175608.4120910-1-tj@kernel.org>
  date: 2026-10-23
  summary: '17 patches + 18/17~20/17 跟进，全部 Reported-by: Sashiko'
  review_outcome: 'Andrea 对 #17 提设计疑问'
- version: v4
  msgid: <20261027001749.1821379-1-tj@kernel.org>
  date: 2026-10-27
  summary: rebase 到 for-7.4-fixes，拆出 watchdog 修复；fold 18/17、新增 20/17；18 patches +
    19/18、20/18 跟进
  review_outcome: 刚发出，暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 缺 v4 这一版的独立 review
  next_action: 等 Andrea/sashiko 对 v4 review 收取后合入 for-7.4-fixes
contribution_opportunities:
- kind: testing
  description: 多层 sched_ext 层级下复现并验证 bypass/cap 撤销路径（尤其 19/18、20/18 跟进）
- kind: review
  description: 核对 v4 相对 v3 的 change 是否自洽
generated_at: '2026-10-28T09:00:00'
source_email_count: 8
related_articles:
- sched-20261023-008
- sched-20261024-002
- sched-20261025-008
tags:
- sched_ext
title: 'sched_ext: Fix bypassed sub-scheduler tasks stalling when the host lacks caps'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-008-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261023-008</a>（v1+v2，15 patches）：Tejun Heo 发往 sched_ext/for-7.4 的 bypass stall 修复系列。bypassing 子调度器的任务经其 host（最近的非 bypassing 祖先）的 per-cpu bypass DSQ 运行，而 caps 是 per-CPU、某 CPU 的 dispatch 只在 host 持 `SCX_CAP_BASE` 时下钻——bypass 放置与 bypass 负载均衡此前忽略这点，导致任务被排到「host 无 BASE」的 CPU 上卡死或循环；修复把 `SCX_CAP_BASE` 定为 bypassed 任务所需唯一 cap，让 rescue 路径与 bypass 负载均衡都 cap 感知。
- <a class="article-ref" href="/lkm/2026/10/24/sched-20261024-002-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261024-002</a> / <a class="article-ref" href="/lkm/2026/10/25/sched-20261025-008-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261025-008</a>（v3，17 patches + 18/17~20/17 跟进）：按 Sashiko 与 Andrea Righi 的 review 增补修正。
- <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-001-sched-ext-fix-bypassed-sub-scheduler-tasks-stalling-when-the.html">sched-20261027-001</a>（今天，v4）：**扩到 18 patches**，同日另发 19/18、20/18 两枚跟进；watchdog 修复已单独抽出并合入 for-7.4-fixes（见 <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-002-sched-ext-fix-the-stall-watchdog-testing-and-blaming-the-wro.html">sched-20261027-002</a>）。系列在 Tejun 自有树 `bypass-caps-v4` 迭代，仍缺外部 review 回收入。

## 背景与问题
（承接 v2/v3）bypassing 调度器的任务走 host 的 per-cpu bypass DSQ，但 CPU dispatch 只在 host 持 `SCX_CAP_BASE` 时下钻，因此「host 无 BASE」的 CPU 上某个 bypass DSQ 永远不会被消费。此前的 bypass 放置与 bypass 负载均衡未意识到这点：bypassed 任务可能被排到或被搬到这样的 CPU 上原地卡住，直到 host 重新获得 cap 或 bypass 窗口结束；「host 有 BASE 但无 ENQ」时任务会在 bypass DSQ 与 reject drain 之间无限循环。被 bypass 的任务更依赖 rescue slice 运行，放大了 rescue 路径的既有缺陷（CPU 空转带 runnable rescuee、kernel slice 写入一个 tick 一个 tick 地喂 grant、调度器把 grant 扩展到超带宽）。

v4 的增量背景：v3 的 19/17（stall watchdog 误责 bypassing owner）被拆出、单独发为 watchdog 修复（已合入 for-7.4-fixes，见本日另一篇），v3 的 18/17（NONE rescuee 离开 sched_ext 留下悬空 `rescue.curr`）被并入 v4 的 #13。

## 技术方案
v4 共 18 patches（`kernel/sched/ext/*` + sched.h + tools autogen，9 files +569/−221）+ 19/18、20/18 两枚跟进：

- **0001-0002 准备**：把 `scx_ent_flags` 多 bit 字段打包到顶部使单 bit 标志连续；在 claim 被确认处清 `holding_cpu`。
- **0003**：把 bypassing 调度器的 reenqueue 排除在 reenqueue 上限之外（kernel 负责放置，bypass 下 strand 会 deadlock disable）。
- **0004**：用 `SCX_ENQ_IMMED` 消费 bypass DSQ，使「有 BASE 无 ENQ」的 host 直接运行而非循环。
- **0005-0010 修 rescue slice**：served time 从 charged runtime 计、`ops.stopping()` 后恢复余量、避免 CPU 带着 runnable rescuee 空转、把 grant 标记为 kernel-owned slice（不可延长只能缩短）。
- **0011-0012**：`put_prev_task_scx()` 走 plain insert 排到 local DSQ 后也重新调度该 CPU；dispatch_one() 里对 bypassing prev 的 slice 于 keep 测试前过期。
- **0013**：host 无 BASE 时把 bypassed 任务送入 rescue。
- **0014-0017**：bypass 负载均衡 cap 感知——容量与 donees 只来自 BASE cpus、抽出 `bypass_lb_move()`、支持搬移 homed on other cpus 的任务、host 失 BASE 时 drain 该 CPU 的 bypass DSQ。
- **0018**：处理 lone IMMED 任务排在 kept prev 之后的问题。
- **19/18、20/18**：修 NONE rescuee 离开 sched_ext 后 `rescue.curr` 悬空导致的 use-after-free；修 rescue overload pick 误 eject 无关 sub（rescue 时间改记到实际运行该任务的 sched）。

## 版本演进与当前进展
*current_version: v4*（`<20261027001749.1821379-1-tj@kernel.org>`，同日 19/18、20/18 跟进）。

- v1（2026-10-22）：首个版本。
- v2（2026-10-23）：15 patches，按 Sashiko 的 review 修订 rescue slice。
- v3（2026-10-23）：17 patches + 18/17~20/17 跟进，全部 `Reported-by: Sashiko`。
- v4（2026-10-27）：rebase 到 for-7.4-fixes，拆出 watchdog 修复单独合入；fold 18/17 → #13、新增 20/17 → #18；按 Andrea 对 #17 的意见改为「跳过 donee 会拒绝的任务」而非回 home 重排。

## Maintainer 意见与讨论焦点
今日无新的外部 reviewer 表态（v4 刚发）。v3 阶段的焦点：Andrea Righi 对 #17 提过设计疑问（失 BASE 时是否应保留旧 head 或走普通负载均衡），v4 已按此改动；watchdog 修复获 Andrea `Reviewed-by`（已合入，见 <a class="article-ref" href="/lkm/2026/10/27/sched-20261027-002-sched-ext-fix-the-stall-watchdog-testing-and-blaming-the-wro.html">sched-20261027-002</a>）。

## 合入评估
*likelihood=high*。系列在 Tejun 自有树（`git://…/tj/sched_ext.git bypass-caps-v4`）迭代，目标合入 sched_ext/for-7.4-fixes；v4 已轮到 rebase 后的阶段，dagestad 依赖的 watchdog 修复已在 10-27 合入。*blocking_issues*：暂无硬性阻断，缺 v4 这一版的独立 review。*next_action*：等 Andrea/sashiko 对 v4 的 review 收取后合入。

## 效果评估
cover 说明测试覆盖：三层调度层级循环 bypass + pinned spinners、fork 与 context-switch 风暴、带 queued tasks 的 cap 撤销；balancer 的 remote move 与 drain 有过演练，`holding_cpu` 握手、cap-revoke 放置与 rescue keep 经小规模 model check。无定量性能数据（正确性修复系列）。

## 我可以参与的点
- *kind: testing*：在多层 sched_ext 层级下复现并验证 bypass/cap 撤销路径（尤其 19/18、20/18 两个新跟进）。
- *kind: review*：核对 v4 相对 v3 的 change（#3/#13/#17/#18 描述与 kerneldoc 修改）是否自洽。

## 参考链接
- v4 cover: https://lore.kernel.org/all/20261027001749.1821379-1-tj@kernel.org/
- watchdog 修复（已合入）: https://lore.kernel.org/all/20261026204300.3618150-1-tj@kernel.org/
- v3: https://lore.kernel.org/r/20261023175608.4120910-1-tj@kernel.org
