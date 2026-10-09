---
id: sched-20261002-002
date: '2026-10-02'
subject: 'sched/eevdf: Keep expired protection expired across reweighting'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261001134016.3881268-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261001164609.244156-1-kayracizmeci@gmail.com/
authors:
- Christian Loehle
- Kayra Cizmeci
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261001134016.3881268-1-christian.loehle@arm.com>
  date: '2026-10-01'
  summary: 5 补丁「Keep slice protection boundaries consistent」
  review_outcome: Peter 反对 1/5、追问 3/5 动机
- version: v2-rework
  msgid: <20261002145729.11981-1-kayracizmeci@gmail.com>
  date: '2026-10-02'
  summary: 系列解体：4/5 由 Kayra squash 重发；1/5 与 3+5/5 弃；2/5 refactor 独立发
  review_outcome: 双方达成一致，合并版补丁待发
upstream_commit: null
fixes_commit: 80390ead2080
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Kayra 的合并版补丁未发出
  - 存活 protection 不被 reweight 的缺口未定性
  next_action: Kayra 发 squash 后修复补丁，Christian 独立发 refactor
contribution_opportunities:
- kind: review
  description: 核对 squash 后 reweight 路径双分支覆盖与新 base 适配
- kind: review
  description: 定性存活 protection 不被 (!expired) reweight_eevdf() 处理是否为缺口
generated_at: '2026-10-03T01:00:00'
source_email_count: 3
related_articles:
- sched-20260930-008
- sched-20260930-009
- sched-20261001-001
tags:
- eevdf
title: 'sched/eevdf: Keep expired protection expired across reweighting'
layout: article
---

> **subject**：`sched/eevdf: Keep expired protection expired across reweighting`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-008-sched-eevdf-fix-slice-protection-across-state-changes.html">sched-20260930-008</a>：Christian Loehle 两枚 EEVDF slice-protection 边界修复——1/2 让每次新授予的 protection 无条件下限到最小 slice，2/2 保持「已过期的 protection」在 reweight 移动 vruntime 后仍是过期态；当日 Kayra 追问 2/2 的 reweight 路径反例。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-009-sched-fair-take-slice-protection-into-account-when-arming-hr.html">sched-20260930-009</a>：Christian 单片 HRTICK 修复——fair hrtick 取「虚拟 deadline 与存活 protection」较早者，否则短 request 任务被反复 repick、调度粒度变粗。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-001-sched-eevdf-keep-slice-protection-boundaries-consistent.html">sched-20261001-001</a>：两轮合并扩展为 5 补丁 v2「Keep slice protection boundaries consistent」，Peter 对 1/5 明确不喜欢（破坏稳态、偏向 wakeup 启发式）、对 3/5 追问动机。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-002-sched-eevdf-keep-expired-protection-expired-across-reweighti.html">sched-20261002-002</a>（今天）：系列开始解体重组——Kayra Cizmeci 指出 v2 4/5 所依赖的 `(!curr)` 分支已被她自己 9 月的补丁从 tip sched/core 删掉、且其 reweight 反例证明 4/5 所修问题真实存在；Christian 承认「你说得对」，并主动提议把 4/5 折叠进 Kayra 的修复由她署名重发（自加 Co-developed-by/Signed-off-by）。Christian 同时透露：1/5 与 3/5+5/5 已被放弃，只剩 refactor（2/5）将作为独立补丁重发。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-008-sched-eevdf-fix-slice-protection-across-state-changes.html">sched-20260930-008</a>）EEVDF 的 slice protection 是绝对 vruntime 边界。4/5 修的是：`reweight_eevdf()` 缩放「存活」protection、但 reweight 移动 vruntime 时「已过期」的 vprot 原样不动，可让旧 vprot 重新复活、current 越过有更早 deadline 的 eligible 实体被选中。今天 Kayra 的增量有两点：其一，4/5 补丁代码里 `__enqueue_entity(cfs_rq, se)` 后的 `(!curr)` 分支已被她的补丁（`https://patch.msgid.link/20260911155449.1249726-1-kayracizmeci@gmail.com`）从 tip sched/core 移除——「So, heads-up」，v2 的 base 已经陈旧；其二，alive（live）protection 存在时 `(!expired)` 的 `reweight_eevdf()` 不走 on_rq 路径、存活 protection 未被 reweight——这个缺口正是她 9-30 提出的反例的延续，且 Christian 的 commit message 自己也写着 ff38424030f9「handled live protection, but left the expired case unchanged」。

## 技术方案

（承接）4/5 的方案：把「已过期的 current 实体」protection 锚定在新 vruntime（`vprot = vruntime`），使 `protect_slice()` 保持 false；对存活 protection 保留既有缩放。

今天的重组决定：
- **4/5 并入 Kayra 的修复**：Christian 提议「do you wanna fold mine into your fix and send that out? (I think it looks better squashed but feel free to just pick mine up as your 1/2 if you disagree)」——把 Christian 的改动 squash 进 Kayra 9-30 反例对应的修复补丁，由 Kayra 署名发出，trailer 加 Christian 的 Co-developed-by + Signed-off-by。
- **1/5、3/5+5/5 放弃**：Christian 明确「With 1/5 and 3+5/5 dropped there's only the refactor remaining and I might as well send that as standalone」——呼应 Peter 10-01 对 1/5 的反对与 3/5 的动机追问，直接弃掉这两片（及连带受同一理由影响的 5/5）。
- **2/5（共享 slice protection 计算）独立重发**。
- 另外 Kayra 点出的「存活 protection 不被 reweight」若确认为缺口，可能成为又一枚独立补丁（「If I'm not tho that can mean a patch. :-). But IDK if that's intentional or not」）。

## 版本演进与当前进展

- 前身 A：单片 HRTICK fix v1（09-29，<a class="article-ref" href="/lkm/2026/09/30/sched-20260930-009-sched-fair-take-slice-protection-into-account-when-arming-hr.html">sched-20260930-009</a>）。
- 前身 B：两补丁「Fix slice protection across state changes」v1（09-30，<a class="article-ref" href="/lkm/2026/09/30/sched-20260930-008-sched-eevdf-fix-slice-protection-across-state-changes.html">sched-20260930-008</a>）。
- v2：5 补丁「Keep slice protection boundaries consistent」（10-01，<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-001-sched-eevdf-keep-slice-protection-boundaries-consistent.html">sched-20261001-001</a>，`<20261001134016.3881268-1-christian.loehle@arm.com>`）；Peter 反对 1/5、追问 3/5。
- 10-02（今天）：
  - Kayra（00:46，`<20261001164609.244156-1-kayracizmeci@gmail.com>`）：heads-up `(!curr)` 分支已从 tip 删除；reweight 反例确认 4/5 必要。
  - Christian（05:51，`<ac4671ff-18a7-4447-84e6-30d35df1c7af@arm.com>`）：承认 base 过时（所需 fixes 已进 sched/core）；提议折叠；宣布 1/5 与 3+5/5 弃、refactor 独立发。
  - Kayra（22:57，`<20261002145729.11981-1-kayracizmeci@gmail.com>`）：接受 squash，将加 Co-developed-by 与 Signed-off-by 后发出。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched 维护者）：10-01 对 1/5 的反对（「wrecks the steady state behaviour in favour of our 'dodgy' wakeup heuristics」）今天的实际后果显现——1/5 被作者放弃。当日无新回帖。
- **Christian Loehle**（ARM，作者）：主动让渡 4/5 的署名给 Kayra（「it looks better squashed」），体现收敛速度；确认 series 解体方案。
- **Kayra Cizmeci**（独立 reviewer）：以两处代码事实（分支删除、reweight 反例）推动重组，将负责发出合并后的补丁。
- 焦点变化：从「5 补丁系列怎么改」变成「拆成几枚独立补丁、各自由谁署名」——分歧收敛中，无 NAK。

## 合入评估

*likelihood=medium*。Peter 的核心反对（1/5 稳态 vs wakeup）已通过放弃该补丁消除；4/5 有 Kayra 反例佐证 + 双方协作重发；refactor（2/5）低风险。但合并后的新补丁尚未发出，且「存活 protection 不被 reweight」是否为真实缺口待确认。*blocking_issues*：Kayra 的合并版补丁未发出；存活 protection reweight 缺口未定性。*next_action*：Kayra 发 squash 后的修复补丁（含 Christian 的 Co-developed-by/Signed-off-by）；Christian 独立发 refactor；两人对存活 protection 缺口给出结论。

## 效果评估

本日无新数据。既有数据（10-01 cover）：4/5 对应测试 441920 次权重变更零复活、零错误选择（v2 语境）；1/5 的 1005us→101us、3/5 的 13-28ms cap 数据随补丁放弃不再直接相关。

## 我可以参与的点

- `review`：Kayra 的合并版补丁发出后，核对 squash 后的 reweight 路径是否同时覆盖「过期 protection 锚定」与「存活 protection 缩放」两分支，及与 tip sched/core 新 base（无 `(!curr)` 分支）的适配。
- `review`：定性「存活 protection 不被 `(!expired)` reweight_eevdf() 处理」是否为缺口——若确认，可抢先给出补丁（当前无人认领）。

## 参考链接

- Kayra 的反例+分支删除提示: https://lore.kernel.org/all/20261001164609.244156-1-kayracizmeci@gmail.com/
- Christian 的折叠提议: https://lore.kernel.org/all/ac4671ff-18a7-4447-84e6-30d35df1c7af@arm.com/
- Kayra 接受 squash: https://lore.kernel.org/all/20261002145729.11981-1-kayracizmeci@gmail.com/
- v2 系列 cover（10-01）: https://lore.kernel.org/all/20261001134016.3881268-1-christian.loehle@arm.com/
