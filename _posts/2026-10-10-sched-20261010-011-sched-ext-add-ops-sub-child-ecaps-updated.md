---
id: sched-20261010-011
date: '2026-10-10'
subject: 'sched_ext: Add ops.sub_child_ecaps_updated()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261008093228.2015427-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261008093228.2015427-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
current_version: v3
patch_series:
- version: v2
  msgid: <20261008093228.2015427-1-tj@kernel.org>
  date: '2026-10-08'
  summary: ops.sub_child_ecaps_updated() + scx_qmap 复位 cpuperf，砍掉 disable 报告
  review_outcome: Andrea 抛 bypass revoke 上报与 detach 复位误伤两边界
- version: v3
  msgid: null
  date: '2026-10-10'
  summary: 2/2 取 v3；disable 由 ops.sub_detach() 收尾的契约论证成立
  review_outcome: Applied 1-2 到 sched_ext/for-7.4，两枚加 Andrea R-b
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: high
  blocking_issues:
  - detach 复位误伤 holder 的修复留到下一版本
  next_action: 随 sched_ext/for-7.4 上行；后续版本落实 detach 复位跳 pool
contribution_opportunities:
- kind: testing
  description: 复测子级 enable/disable/层级 bypass 三场景的上报时序
- kind: review
  description: 在 shared pool 多 holder 场景复现 detach 复位误伤
generated_at: '2026-10-11T09:00:00'
source_email_count: 5
related_articles:
- sched-20261008-004
- sched-20261009-016
tags:
- sched_ext
title: 'sched_ext: Add ops.sub_child_ecaps_updated()'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-004-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261008-004</a>：Tejun Heo 为 sched_ext sub-scheduler 补上「父级何时得知 grant/revoke 生效」的缺口——新增 `ops.sub_child_ecaps_updated()` 回调，v1→v2 快速迭代（v2 砍掉 disable 报告与 sleep lock），吸收 Tao Cui 实测与 Tejun 的 last-writer-wins 裁决。
- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-016-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261009-016</a>：Andrea Righi 首次 review，抛两个边界问题——① 子级 bypassing 但父级不 bypass 时 revoke 生效是否还应通知父级；② `qa.rr_cids` 覆盖整个 shared pool，child A 在 child B 的回合 detach 会误复位仍持 PERF 的 B 的 cpuperf target。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-011-sched-ext-add-ops-sub-child-ecaps-updated.html">sched-20261010-011</a>（今天）：**Tejun 论证「disable-only」契约后，两枚补丁被 applied**——1/2 按 v1、2/2 按 v3，均加 `Reviewed-by: Andrea Righi`，进入 `sched_ext/for-7.4`；对 Andrea 的 detach 复位误伤，Tejun 承诺下一版跳过被其它子级持有的 pool。

## 背景与问题
（承接）grant/revoke 只记录目标值、真正生效要等 cid 下一次 dispatch，父调度器此前无从得知生效时刻。v2 方案新增 `ops.sub_child_ecaps_updated()`、disabled 子级不报告、由父级从 `ops.sub_detach()` 恢复。今天收敛的关键问题是：子级何时会「bypass 且父级 active」？Tejun 论证——子级只在其自身 enable、自身 disable、或整个层级（含父级）一起 bypass 时 bypass；自身 enable 的 bypass 会被解除并重放，层级 bypass 时父级也在 bypass，所以只剩「disable」一种情形；v1 报告 disabling 子级的 revoke 之所以「nasty」，是因为调用上下文与 sync 路径不同（dispatch kfuncs 需要上下文、嵌套 sub dispatch 要门控、避开 PM bypass 要持可能卡 suspend 的锁）。因此「disable 由 `ops.sub_detach()` 覆盖」是唯一简单自洽的契约。

## 技术方案
（承接 v2）1/2 新增 `ops.sub_child_ecaps_updated()`（子级 `sub_ecaps_updated()` 后投递直接父级，携带变更前/后 caps；bypass 期间抑制、解除后重放；disabled 不报告）；2/2 scx_qmap 在 PERF 被回收时把 cpuperf target 复位为 `SCX_CPUPERF_ONE`、detach 场景从 `ops.sub_detach()` 复位。今天的两个落点：

- **disable 报告只由 sub_detach 覆盖**（Tejun 论证，Andrea 认可）：`ops.sub_detach()` 运行时子级所有 caps 已清理，父级从那里恢复曾委派的状态。
- **detach 复位误伤 holder**（Andrea 提出，Tejun 认可）：`qa.rr_cids` 覆盖整个 shared pool，child A 在 child B 回合 detach 会误复位 B 的目标；Tejun 确认「transient——detach 的 repartition 也会回收 pool、handler 又复位一次，但中间 B 的目标被 clobber」，承诺**下一版本跳过被其它子级持有的 pool**。

结果：**Applied 1-2 to sched_ext/for-7.4**（2/2 取 v3），两枚均加 `Reviewed-by: Andrea Righi`。

## 版本演进与当前进展
- v1/v2（10-08）：见 related_articles。
- 10-09：Andrea 抛两边界问题（bypass revoke 上报、detach 复位误伤）。
- 今天：Tejun 论证 disable-only 契约（`<75b599f5c3e38cc62e33c4bf370a1d84@kernel.org>`）；Andrea 对 1/2 给 R-b（`<aslLP_r6bl6TC8u1@gpd4>`）、对 v3 2/2 给 R-b（`<asle5goFd3CRujUA@gpd4>`）；Tejun 回 2/2（`<871113fbf23f16c8b291bbb06e9d6f36@kernel.org>`）承诺下一版跳过被其它子级持有的 pool；Tejun applied 1-2（`<2b60fc415bbe7299f8637fb19724d769@kernel.org>`）。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（维护者+作者）：论证「子级只在自身 enable/disable 或层级 bypass 时 bypass → 只剩 disable」的契约成立，据此砍掉 v1 的 disable 报告；对 detach 复位误伤承诺下一版修。
- **Andrea Righi**（联合维护者）：认可 disable-only 论证与 sub_detach 收尾，两枚均 R-b。
- 无 NAK、无剩余方向性争议；唯一待办是 detach 复位跳 pool 的「下一版本」小修。

## 合入评估
*likelihood=high*。两枚已 applied 到 `sched_ext/for-7.4`、均带 Andrea R-b、前身补丁有 Tao Cui 独立实测背书；只剩 detach 复位跳 pool 的小修在后续版本跟进。*blocking_issues*：detach 复位误伤 holder 的修复留到下一版本。*next_action*：随 sched_ext/for-7.4 上行，并在后续版本落实 detach 复位跳 pool。

## 效果评估
无性能数据；正确性由 Tao Cui 前身补丁实测（caps-clear 在 SIGTERM 后父级正确复位、两轮 lockdep 干净，见 related_articles）背书。

## 我可以参与的点
- 复测 `ops.sub_child_ecaps_updated()` 在子级 enable/disable/层级 bypass 三种场景下的上报时序；
- 在 shared pool 多 holder 场景复现并验证「detach 复位误伤」是否如 Tejun 所述为 transient。

## 参考链接
- PATCHSET v2 cover: https://lore.kernel.org/all/20261008093228.2015427-1-tj@kernel.org/
- Tejun applied: https://lore.kernel.org/all/2b60fc415bbe7299f8637fb19724d769@kernel.org/
- Tejun disable-only 论证: https://lore.kernel.org/all/75b599f5c3e38cc62e33c4bf370a1d84@kernel.org/
- Andrea R-b (2/2 v3): https://lore.kernel.org/all/asle5goFd3CRujUA@gpd4/
