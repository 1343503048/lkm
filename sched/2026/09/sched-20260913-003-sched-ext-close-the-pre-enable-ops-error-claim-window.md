# sched_ext: Close the pre-enable ops error claim window

## TL;DR
Qiurong Fang（kylinos）修复 sched_ext 使能路径上「ops 错误认领窗口」的系列，09-13 23:59 被 Tejun Heo 应用到 `sched_ext/for-7.3-fixes`（仅做 minor wording cleanups），三天内走完 v1→v3 并合入维护者树。需要说明：该系列的原始补丁邮件未进入本邮箱缓存（v1/v2/v3 均未收到），本文基于 Tejun 的三轮回帖与合入回执重建脉络，补丁 diff 与 commit 细节未获取到。

## 背景与问题
从 Tejun 的回帖可以确定的线程事实：该补丁处理 sched_ext 使能（scx enable）路径中 ops->priv 发布与使能状态转换（SCX_ENABLING）的先后关系——在这个顺序之下，「使能完成前 ops 错误被认领（claim）」的窗口是否存在、以及分配失败时该走本地回退还是完整 disable。Tejun 在 v2 回帖中给出所有权边界：「所有分配失败都发生在 ops->priv 发布之前，因此不可能有 disable 竞争，状态必然仍是 SCX_ENABLING」；v1 回帖则指出某处错误处理路径不可达。补丁本身的 diff、commit message 与 Fixes 标签未获取到。

## 技术方案
依据回帖可推断的方案要点（细节未获取到）：

- 调整使能状态转换与 ops->priv 发布的顺序，使 SCX_ENABLING 先于 ops->priv 发布，从而关闭「pre-enable ops error claim window」——标题即由此而来；
- 错误路径收缩：v1 中 Tejun 要求删掉一处 hunk（「一旦 SCX_ENABLING 先于 ops->priv 发布，scx_tryset_enable_state() 在该处不可能失败」），并保留分配失败时的重置；
- v2 中 Tejun 给出具体断言写法：分配失败回退处用 `WARN_ON_ONCE(scx_set_enable_state(SCX_DISABLED) != SCX_ENABLING)` 断言状态仍为 ENABLING，同时更新被移动的注释；「分配失败仍本地回退（unwind locally），完整 disabling 只在 scx_alloc_and_add_sched() 成功之后才适用」。

## 版本演进与当前进展
current_version: v3。时间线（原始补丁均未入邮箱缓存，日期为对应 Tejun 回帖时间）：

- v1（不晚于 09-11）：Tejun 09-11 05:40 回复，要求删掉一处不可达错误路径的 hunk、移动既有状态转换并保留分配失败时的重置。
- v2（不晚于 09-11 深夜）：Tejun 09-11 23:24 回复，给出 WARN_ON_ONCE 断言写法并要求更新被移动的注释，澄清「无 disable 竞争」的依据。
- v3（09-12 发出，msgid 20260912131518.3428032-1）：09-13 23:59 Tejun 回复「Applied to sched_ext/for-7.3-fixes with minor wording cleanups」。合入。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：三轮全部是具体、收敛的评审意见——v1 指出不可达路径，v2 给出断言实现并解释无竞争原因，v3 直接应用。无分歧、无保留意见，评审在两轮内完成。
- 无其他参与者出现在本邮箱收到的线程邮件中；原始补丁的完整实现未获取到，无法评估是否还有未讨论的角落。

## 合入评估
likelihood=merged（已成事实）：`status=merged_tip`，合入分支 `sched_ext/for-7.3-fixes`（Tejun 应用，带 minor wording cleanups）。blocking_issues：无——该修复已进维护者树；落到 Linus 树的时点与随哪个 pull 进入 mainline 未获取到。next_action：跟踪 `sched_ext/for-7.3-fixes` 的后续 pull；回合该分支的内部分支以合入后的最终形态（含 wording cleanup）为准。

## 效果评估
未获取到。线程邮件中没有测试数据或复现信息；属使能错误路径的正确性收尾修复，预期影响仅限使能失败场景的报错与状态一致性。

## 我可以参与的点
- 回合确认（new_patch）：若内部分支/产品分支回合 sched_ext，待该 commit 随 `sched_ext/for-7.3-fixes` 进入 mainline 后核对最终形态并评估是否需要同步（注意 Tejun 应用时带了 minor wording cleanups，与lore 上的 v3 版本可能有措辞差异）。
- 当前阶段暂无其他明显参与空间：评审已闭环、无遗留分歧，可持续观察该分支随下一个 pull 进主线。

## 参考链接
- lore thread（v3 线程根，原始补丁邮件未入邮箱缓存，msgid 取自合入回执 In-Reply-To）: https://lore.kernel.org/all/20260912131518.3428032-1-fangqiurong@kylinos.cn/
- Tejun 对 v1 的评审: https://lore.kernel.org/all/c3b851d927a8be1a0038cb208d33349b@kernel.org/
- Tejun 对 v2 的评审（WARN_ON_ONCE 断言与无竞争论证）: https://lore.kernel.org/all/664afc289472acecc783762fdf7a9baa@kernel.org/
- 09-13 合入回执（Applied to sched_ext/for-7.3-fixes）: https://lore.kernel.org/all/f5041873e1431184067cc977634e51ab@kernel.org/
- 原始补丁 v1/v2/v3 正文: 未获取到（未进入 QQ 邮箱）

---
id: sched-20260913-003
date: 2026-09-13
subject: 'sched_ext: Close the pre-enable ops error claim window'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260912131518.3428032-1-fangqiurong@kylinos.cn>'
lore_url: 'https://lore.kernel.org/all/20260912131518.3428032-1-fangqiurong@kylinos.cn/'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.3-fixes'
current_version: v3
generated_at: '2026-09-14T10:24:00'
authors:
  - 'Qiurong Fang'
maintainers_involved:
  - 'Tejun Heo'
patch_series:
  - version: v1
    msgid: null
    date: null
    summary: '关闭 sched_ext 使能路径的 pre-enable ops 错误认领窗口（原始补丁未入邮箱缓存，要点取自 Tejun 回帖：调整使能状态转换与 ops->priv 发布顺序、收缩不可达错误路径）。'
    review_outcome: 'Tejun Heo 09-11 05:40：删掉一处 hunk（SCX_ENABLING 先于 ops->priv 发布后 scx_tryset_enable_state() 不可能失败，错误路径不可达），移动既有转换并保留分配失败时的重置。'
  - version: v2
    msgid: null
    date: null
    summary: '按 Tejun 意见调整（原始补丁未入邮箱缓存）；分配失败回退处改用 WARN_ON_ONCE(scx_set_enable_state(SCX_DISABLED) != SCX_ENABLING) 断言。'
    review_outcome: 'Tejun Heo 09-11 23:24：确认分配失败均先于 ops->priv 发布、无 disable 竞争，给出断言写法并要求更新被移动的注释。'
  - version: v3
    msgid: '<20260912131518.3428032-1-fangqiurong@kylinos.cn>'
    date: 2026-09-12
    summary: '原始补丁未入邮箱缓存，仅知 msgid（取自合入回执 In-Reply-To）与发出日期；diff 与 commit message 未获取到。'
    review_outcome: '09-13 23:59 Tejun Heo 回复 Applied to sched_ext/for-7.3-fixes with minor wording cleanups。'
merge_assessment:
  likelihood: merged
  blocking_issues:
    - '无：已进 Tejun 的 sched_ext/for-7.3-fixes 分支'
    - '进 Linus 树的时点与所在 pull 未获取到'
  next_action: '跟踪 sched_ext/for-7.3-fixes 随后续 pull 进 mainline；回合分支以合入后最终形态为准'
contribution_opportunities:
  - kind: new_patch
    description: '内部分支回合 sched_ext 时核对该 commit 最终形态（含 minor wording cleanups）并评估同步'
source_email_count: 3
related_articles: []
tags:
  - sched_ext
---
