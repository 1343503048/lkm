---
id: sched-20260828-008
date: '2026-08-28'
subject: 'cpuidle: teo: Do not return a disabled idle state'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <20260827090505.3703860-1-luoxueqin@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260828032457.2317326-1-luoxueqin@kylinos.cn/
authors:
- Xueqin Luo
maintainers_involved:
- Rafael J. Wysocki
- Christian Loehle
current_version: v2
patch_series:
- version: v1
  msgid: <20260827090505.3703860-1-luoxueqin@kylinos.cn>
  date: '2026-08-27'
  summary: 选定状态被禁用时回退到最浅启用状态 idx0
  review_outcome: Rafael J. Wysocki 要求改为在钳制前抬高 constraint_idx 下界
- version: v2
  msgid: <20260828032457.2317326-1-luoxueqin@kylinos.cn>
  date: '2026-08-28'
  summary: constraint_idx 至少等于 idx0；teo.c 11 行纯新增；changelog 注明建议来自 Rafael
  review_outcome: Christian Loehle Reviewed-by（8/28 23:49）；Rafael 未再回帖
upstream_commit: null
fixes_commit: c410a9a142f1
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 无技术分歧，仅等 cpuidle 队列节奏
  - 是否回 stable 无人表态（缓存不含收件人，未见 Cc stable 证据）
  next_action: 等 Rafael 应用；产品侧提供禁用 state0 + 紧 QoS 的触发用例可支撑 stable
contribution_opportunities:
- kind: new_patch
  description: 在 OLK-6.6 上核对 teo_select() 同型缺陷并近乎原样回合这 11 行
- kind: testing
  description: 构造 state0 disable + PM QoS 小于所有启用状态 exit_latency 的用例，验证是否真进入禁用状态
- kind: review
  description: 推进停在 v1 的 menu governor 姊妹修复，两份成对回合
generated_at: '2026-09-07T22:40:00'
source_email_count: 2
related_articles:
- sched-20260827-014
- sched-20260827-015
tags:
- idle
title: 'cpuidle: teo: Do not return a disabled idle state'
layout: article
---

## TL;DR

**本文为增量更新**（完整背景见 sched-20260827-014）。Xueqin Luo（KylinOS）8/28 发出的 **v2 逐字采纳了 Rafael J. Wysocki 8/27 的替代写法**：不再在决策完成后"事后回退到最浅启用状态"，而是在约束钳制之前先把下界抬高——`if (constraint_idx < idx0) constraint_idx = idx0;`，其中 `idx0` 就是主循环顺带记录的"第一个启用 idle state 下标"。改动是单文件 11 行纯新增，changelog 明确标注 "(suggested by Rafael J. Wysocki)"，`Fixes: c410a9a142f1` 保留。ARM 的 Christian Loehle 当晚给出 **`Reviewed-by`**，这是该补丁拿到的第一个 review 标签。方案分歧已消失，剩下只是队列节奏。**OLK-6.6 的 `teo_select()` 有同一处缺陷**（已在本地树核对，见末节）。

## 背景与问题

`teo_select()` 的主扫描循环**从 state 1 开始**（`for (i = 1; ...)`），循环里只做两件事：记录第一个未禁用状态到 `idx0`、把满足 `latency_req` 的最深状态记进 `constraint_idx`（初值 0）。收尾时用一个钳位把候选状态压到约束之内：

```
if (idx > constraint_idx)
        idx = constraint_idx;
```

于是有一个组合会漏：state 0 被禁用（`dev->states_usage[0].disable`），且**没有任何启用状态满足 PM QoS 延迟约束**——此时 `constraint_idx` 从未被赋值，停在 0，钳位把候选压成 0，而 0 恰恰是被禁用的那个状态。cpuidle 核心层对 governor 返回的下标**不再校验 disable 标志**，CPU 就真的进入了一个管理员/策略显式关掉的状态（通常是 POLL/最浅状态）。

v1 的写法是在选出状态被禁用时回退到 `idx0`。Rafael 8/27 的反对意见是形态问题：不该事后打补丁，而应让约束检查本身产出合法候选。

## 技术方案

v2 把这句话变成代码，插在指标统计循环之后、钳位之前：

```
+       /*
+        * If the latency constraint does not allow any of the enabled idle
+        * states to be used, the candidate state index will be capped to 0
+        * by the check below, but state 0 may be disabled.  To prevent the
+        * selection of a disabled state in that case, ensure that
+        * constraint_idx is at least equal to the index of the first
+        * enabled idle state.
+        */
+       if (constraint_idx < idx0)
+               constraint_idx = idx0;
```

语义上的差别是这版能被"一眼证明正确"：`constraint_idx` 从此表示"在延迟约束下允许的最深启用状态"，下界被 `idx0` 兜住，钳位后的候选**永远不可能落在禁用状态上**，所以不需要任何后续回退分支。代价是多一次比较（在选择路径的热线上，但只是寄存器比较，无额外循环）。

`drivers/cpuidle/governors/teo.c | 11 +++++++++++`，1 file changed, 11 insertions(+)，无删除——比 v1 的"事后回退"少了改判逻辑。

## 版本演进与当前进展

| 时间 | 事件 |
|---|---|
| 8/27 17:05 | v1 `<20260827090505.3703860-1-luoxueqin@kylinos.cn>`，选定状态禁用时回退到 `idx0` |
| 8/27 18:39 | Rafael J. Wysocki 回帖给出 `if (idx0 < constraint_idx) constraint_idx = idx0;` 形式的替代写法 |
| 8/28 11:24 | **v2** `<20260828032457.2317326-1-luoxueqin@kylinos.cn>`，changelog 记 "Instead of falling back to idx0 after the candidate index has been capped to a disabled state, ensure that constraint_idx is at least equal to idx0 before the capping check (suggested by Rafael J. Wysocki)" |
| 8/28 23:49 | Christian Loehle（ARM）`Reviewed-by: Christian Loehle <christian.loehle@arm.com>` |

同作者的姊妹补丁 `cpuidle: menu: Do not return a disabled idle state`（menu governor 提前返回分支短路 disable 检查，站内 sched-20260827-015）**到 9/5 缓存末尾仍未出现 v2**，两封没有被打包推进。

## Maintainer 意见与讨论焦点

- **Rafael J. Wysocki**：唯一实质意见（实现形态），v2 已完全照做，本人对 v2 未再回帖——在这个子系统里"作者按建议重发 + 无进一步意见"通常就是接受。
- **Christian Loehle**：`Reviewed-by`，未附带任何条件或建议。需要注意的是该标签没有覆盖"全部状态都被禁用"的极端组合——那条走的是 `idx < 0` 时直接 `idx = 0; goto out_tick;` 的既有早退分支，v2 未触碰它，所以 `constraint_idx` 的下界抬升在其中不起作用。
- 仍未被回答的问题：v2 之后**没有出现 `Cc: stable` 的痕迹**（本地缓存只保存正文，不含收件人列表，无法判断），也没有针对"哪些产品配置会真的触发"的复现报告。

## 合入评估

**likelihood: likely**。

- 有利：改法由维护者指定；11 行纯新增、无删除、无接口改动；已有一个 `Reviewed-by`；`Fixes:` 指向明确的既有 commit（`c410a9a142f1` "cpuidle: teo: Change the main idle state selection logic"）。
- 卡点：只剩队列节奏（cpuidle 修复通常走 next 分支而非 urgent）。以及"是否有必要同时回 stable"这一层没人表态。
- `next_action`：等 Rafael 应用并 posting；若产品侧能提供"禁用 state0 + 紧 QoS"的实际触发案例，可支撑 stable 申请。

## 效果评估

无性能与功能测量数据，作者也没提供——这是一条纯行为正确性修复，触发条件由代码推导得出（禁用 state 0 且无启用状态满足延迟约束），缓存内没有 syzbot/oops/现场报告佐证其真实发生过。

## 我可以参与的点

- **直接确认 OLK-6.6 同样受影响并准备本地回合同**：已在本地树核对——OLK-6.6 的 `drivers/cpuidle/governors/teo.c` 里 `int constraint_idx = 0;`（386 行）、循环 `for (i = 1; i < drv->state_count; i++)` 内 `idx0 = i; /* first enabled state */`（457 行）与 `constraint_idx = i;`（462 行）、收尾 `if (idx > constraint_idx) idx = constraint_idx;`（560-561 行）**结构与 upstream 完全一致，且中间没有任何 `constraint_idx < idx0` 的下界保护**。也就是说这 11 行可以近乎原样回合，风险只在同一函数内的本地改动（OLK 侧该函数还有 `first_suitable_idx` 等本地逻辑）。
- **做一条可验证的触发用例**：用 `/sys/devices/system/cpu/cpuN/cpuidle/state0/disable` + 把 PM QoS 需求压到小于所有启用状态的 `exit_latency`，读 `time`/`usage` 计数确认是否进入了被禁用状态。这类实测回帖对该补丁的 stable 论证有直接价值，缓存里至今没人给出。
- **顺手看一眼自家 menu governor**：姊妹补丁 `cpuidle: menu` 至今停在 v1 无人推进，如果内部树同时用了 menu，这个 bug 类的两份修复应该成对回合。

## 参考链接

- v2: https://lore.kernel.org/all/20260828032457.2317326-1-luoxueqin@kylinos.cn/
- Christian Loehle 的 Reviewed-by: https://lore.kernel.org/all/d5f96d83-b5c4-4795-9675-7779f35be78f@arm.com/
- v1: https://lore.kernel.org/all/20260827090505.3703860-1-luoxueqin@kylinos.cn/
- Rafael J. Wysocki 的替代写法: https://lore.kernel.org/all/CAJZ5v0gcsx6nsCBWfDjP7OEez2jM3-hNj8kSSm=xH5nS_fNSug@mail.gmail.com/
- `Fixes:` 指向的 commit `c410a9a142f1`: lore 链接未获取到
- tip-bot commit / stable backport: 未获取到
