---
id: sched-20261001-001
date: '2026-10-01'
subject: 'sched/eevdf: Keep slice protection boundaries consistent'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261001134016.3881268-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261001134016.3881268-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261001134016.3881268-1-christian.loehle@arm.com>
  date: '2026-10-01'
  summary: 5 补丁：HRTICK 取 protection 较早者 + 共享 protection 计算 + cap 最短 slice + reweight
    保持过期 + SNT_NORMAL 恢复后更新
  review_outcome: Peter 反对 1/5 的 wakeup 启发式（主张稳态按论文）、追问 3/5 动机；作者回应中
upstream_commit: null
fixes_commit: 82e9d0456e06
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 对 1/5 的稳态行为反对未解决
  - 3/5 的动机未在 changelog 说明
  - 5/5 是否受 1/5 同一理由影响待确认
  next_action: 作者回应 1/5 取舍、补 3/5 动机后发 v3
contribution_opportunities:
- kind: review
  description: 就 1/5 稳态 vs wakeup 启发式取舍给出技术判断与折中方案
- kind: testing
  description: 用真实负载复测 3/5、4/5 数据面，回应人工 rt-app 局限
generated_at: '2026-10-09T01:00:00'
source_email_count: 10
related_articles:
- sched-20260930-008
- sched-20260930-009
tags:
- eevdf
- preempt
title: 'sched/eevdf: Keep slice protection boundaries consistent'
layout: article
---

> **subject**：`sched/eevdf: Keep slice protection boundaries consistent`

## TL;DR

Christian Loehle 把 9-30 的两枚独立修复（「Fix slice protection across state changes」v1 两补丁与「Take slice protection into account when arming HRTICK」单片）合并扩展为 5 补丁系列 v2「Keep slice protection boundaries consistent」：EEVDF slice protection 是绝对 vruntime 边界，但多条路径对该边界的处理与任务当前 slice、或与让调度器重新考虑 current 的定时器不一致。cover 附全套 rt-app 复现与量化数据（HRTICK 粒度 1005us→101us、100us 请求的 13-28ms 超额保护被 cap、441920 次权重变更零复活）。Peter Zijlstra 当晚即回帖：对 1/5 明确表达不喜欢（破坏稳态行为、偏向 wakeup 启发式），对 3/5 追问动机（changelog 未说明），作者回应中。

## 背景与问题

EEVDF 的 slice protection 是一个绝对的虚拟运行时边界（vprot）。该系列修复它在多条路径上的不一致：

- HRTICK 只武装到虚拟 deadline，protection 到期后若中间没有其他调度事件，重新考虑 current 的机会远晚于 protection 边界（前身单片，见 related <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-009-sched-fair-take-slice-protection-into-account-when-arming-hr.html">sched-20260930-009</a>）。
- 改变任务 slice 不丢弃其剩余 request：保留 100ms 相对 deadline、把 request 缩到 100us 后，control 给该任务 13-28ms 的新鲜保护（前身 1/2，见 related <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-008-sched-eevdf-fix-slice-protection-across-state-changes.html">sched-20260930-008</a>）。
- reweight 移动 vruntime 后「已过期」的 protection 会复活，让 current 越过有更早 deadline 的 runnable eligible 实体被选中（前身 2/2）。
- sched_setattr()（sched_change_begin/end）暂时 dequeue 又恢复 current 时（SNT_NORMAL 路径），protection 未被更新——Kayra Cizmeci 曾报告同一不变式失败。
- RUN_TO_PARITY 关闭时 vprot 标记 current 的最小进度量子，HRTICK 同样须在该边界重新考虑。

## 技术方案

v2 五片（`kernel/sched/fair.c` +44/−28，base-commit 01d1f30564aa）：

1. **1/5 `sched/fair: Take slice protection into account when arming HRTICK`**：fair hrtick 取「虚拟 deadline 与存活 protection」的较早者；protection 到期后回退到 deadline；same-task repick 重启定时器但不续 protection；wakeup 缩短 protection 后重算（含已激活定时器）。
2. **2/5 `sched/eevdf: Share the slice protection calculation`**：合并 fresh 与 update 两个 protection 计算路径（落实 v1 期间「1/2 与 update_protect_slice() 语义镜像、应合并」的自查结论）。
3. **3/5 `sched/eevdf: Cap protection when current has the shortest slice`**：无条件下限 protection 到当前 slice（含 current 自己持最短 slice 的情形），带 `Fixes: 82e9d0456e06`。
4. **4/5 `sched/eevdf: Keep expired protection expired across reweighting`**：reweight 移动 vruntime 后保持过期 protection 过期（延续 v1 2/2 的 `Fixes: 80390ead2080` 思路）。
5. **5/5 `sched/eevdf: Update protection after restoring current`**：SNT_NORMAL 恢复 current 后更新 protection；该更新使 protection 过期时请求 lazy rescheduling。

测试方法（cover 详述）：所有负载 pin 到 CPU1、SCHED_OTHER、controller 放另一物理核；rt-app 的 dl-runtime 值经 sched_getattr() 校验换算；启用 PREEMPT_SHORT、RUN_TO_PARITY、PLACE_REL_DEADLINE，HRTICK 与 NO_HRTICK 双跑（1/5 除外）；补 HZ=250/HZ=1000 矩阵回归测试。

## 版本演进与当前进展

- 前身 A：单片 HRTICK fix v1（09-29，`<20260929194711.2689811-1-christian.loehle@arm.com>`，对应 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-009-sched-fair-take-slice-protection-into-account-when-arming-hr.html">sched-20260930-009</a>）。
- 前身 B：两补丁「Fix slice protection across state changes」v1（09-30，`<cover.1790756779.git.christian.loehle@arm.com>`，对应 <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-008-sched-eevdf-fix-slice-protection-across-state-changes.html">sched-20260930-008</a>）。
- v2（10-01，`<20261001134016.3881268-1-christian.loehle@arm.com>`）：按 v1 changelog 宣告的方向把两者合并扩展为 5 补丁——共享 protection 计算、修 slice 变更/reweight/SNT_NORMAL 恢复三处边界、SNT_NORMAL 过期时请求 lazy rescheduling、补 HZ/HRTICK 回归测试。
- 当日回帖：Peter 对 1/5、3/5 各一封（见下节），作者两封回应。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（对 1/5）：「Right, so I don't much like this. This wrecks the steady state behaviour in favour of our 'dodgy' wakeup heuristics. I would much rather we stick to the paper for steady state, and let wakeups be wakeups.」——明确反对 1/5 当前做法，主张稳态遵循 EEVDF 论文、wakeup 保持 wakeup 语义。
- **Peter Zijlstra**（对 3/5）：「Or, the new slice is only effective after the current expires. Is there a reason we care about this? Changelog didn't mention.」——提出备选语义（新 slice 在当前 request 到期后才生效）并追问动机。
- **Christian Loehle**（回复 3/5）：「Yeah I wasn't sure about this, it does make the tests a little more hairy as this obviously races...」；回复 1/5 时问「Alright, I guess the same reasoning then for 5/5?」并自陈这些全来自「拿一堆人工 rt-app 测试砸向 Vincent 的 patchset 看什么会粘上」。
- 核心分歧：1/5 的「稳态（按论文）vs wakeup 启发式」取舍，当日未收敛。

## 合入评估

*likelihood=medium*。机制缺陷真实、复现与数据完备、作者此前两轮快速迭代记录良好；但 Peter 对 1/5 有明确反对意见，3/5 的动机未在 changelog 说明，5/5 是否受同一理由影响待确认，系列需按意见再改。*blocking_issues*：1/5 与 Peter 的稳态取舍未解决；3/5 动机说明缺失；5/5 命运待确认。*next_action*：作者回应 1/5 意见（重做或放弃 wakeup 侧重算）、补 3/5 changelog 动机后发 v3。

## 效果评估

cover 数据（rt-app、pin CPU1、SCHED_OTHER）：

- **1/5**：两个等权任务（100us/1ms request）在 HZ=250 control 上，短任务 median sched_switch run interval 为 1005us（即使开 HRTICK）；打 1/5 后为 101us；两种情况下两任务都保持约一半 CPU——误差在 reconsideration 时间而非份额。
- **3/5**：request 缩到 100us 后的下一次 fresh SNT_PICK，control 授予 13-28ms 保护（因其自身 slice 为 runqueue 最小）；补丁 cap 到当前 request。trace-free 伴随测试中 control 的完整 post-change run interval 达 69-83ms（HRTICK 开），单 fix 后最大降到 3-4ms。
- **4/5**：三任务三 cgroup-v2 组（weight 10000/100/100），每 400ms 修改组 a 的 cpu.weight（序列 10000,1,100,1,10000,100,1,10000）：control 出现 32 次过期→存活 vprot 转换（16 次捕获）、7 次 current 越过有更早 deadline 的 runnable eligible peer；打补丁后 181 次捕获、441920 次 current 权重变更，零复活、零错误选择。
- **5/5**：Kayra 报告的 sched_change_begin() 不变式失败由相位循环复现（诊断 trace 记录 `__setparam_fair()` 入口 vprot <= vruntime，并检查随后 SNT_NORMAL 恢复不使 vprot 复活）。

## 我可以参与的点

- `review`：就 1/5 的「稳态（按论文）vs wakeup 启发式」取舍给出技术判断——wakeup 路径重算 hrtick 是否真的破坏稳态、有无折中方案（例如只在 protection 被缩短时重算）。
- `testing`：用更多样 slice 长度的真实负载（非人工 rt-app）复测 3/5、4/5 的数据面，回应作者自陈的「artificial tests」局限。

## 参考链接

- lore（v2 cover）: https://lore.kernel.org/all/20261001134016.3881268-1-christian.loehle@arm.com/
- Peter 对 1/5: https://lore.kernel.org/all/20261001134320.GR2009045@noisy.programming.kicks-ass.net/
- Peter 对 3/5: https://lore.kernel.org/all/20261001135529.GS2009045@noisy.programming.kicks-ass.net/
- 前身 HRTICK v1: https://lore.kernel.org/all/20260929194711.2689811-1-christian.loehle@arm.com/
- 前身 state-changes v1: https://lore.kernel.org/all/cover.1790756779.git.christian.loehle@arm.com/
