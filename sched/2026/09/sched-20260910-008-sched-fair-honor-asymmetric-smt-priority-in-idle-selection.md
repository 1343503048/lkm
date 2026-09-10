# sched/fair: Honor asymmetric SMT priority in idle selection

## TL;DR
本文为增量更新，完整背景见 related_articles 中的 sched-20260908-002 / sched-20260907-005（本线程与 sched-20260910-007 的 NVIDIA Olympus v5 是同一逻辑系列：v4 的 2/2 补丁标题即本 subject）。09-10 的唯一进展是 Andrea Righi 对 Vincent Guittot 的 static key 质疑正式让步：去掉新增 static key、改用既有的 sched_smt_active()，该改动将落入下一版。

## 背景与问题
POWER7 与 NVIDIA Olympus 在共享容量的 SMT 层用 SD_ASYM_PACKING 给硬件线程排序，但 idle CPU 选择不参考该顺序，任务可能唤醒在任意 sibling 上并滞留到负载均衡纠正为止；在这类系统上，初始选核错误会妨碍核进入偏好的低线程资源模式，造成大幅且持续的性能损失（引自线程中 Andrea 对问题史的回顾）。

## 技术方案
方案主体（select_idle_sibling() 之后按 sibling 优先级调整选核，即 select_idle_smt_cpu()）见 related_articles 与 sched-20260910-007。本日确定的设计修改：Vincent 质疑为启用该行为新增一个 static key 的必要性，Andrea 回复 "Makes sense, I'll remove the static key and use sched_smt_active()."——用既有的 SMT 激活态判断替代新增静态分支开关，减少一个全局静态键与对应的开关语义。

## 版本演进与当前进展
本线程对应 v4（2026-09-08，thread root `<20260908082345.103087-1-arighi@nvidia.com>`）的 2/2 补丁。09-09 Vincent 在该线程连续追问 static key 问题（本缓存仅捕获 Andrea 09-10 00:22 的答复，Vincent 的原话在引用中）；09-10 Andrea 确认移除 static key。与此同时系列封面已更名为 "Enable preferred SMT siblings on NVIDIA Olympus" 并演进到 v5——同日 Peter 已把 v5 从收取队列撤下（见 sched-20260910-007），static key 修改将与之合并进 v6。

## Maintainer 意见与讨论焦点
- Vincent Guittot：反对为单一平台行为新增 static key（认可调度器侧逻辑本身）。意见已被接受。
- 关联分歧（同系列、另一线程）：Will Deacon 拒绝 arm64 MIDR 检测——static key 的解决不改变该卡点。
- 本线程内无其他未决问题。

## 合入评估
likelihood: medium（仅就本线程的 static key 争议而言已解决；系列整体合入前景受制于 sched-20260910-007 记录的 arm64 检测机制僵局，Peter 已 drop v5）。blocking_issues：static key 移除尚未以新版本邮件形式发出；系列层面的 MIDR 替代机制未定。next_action：Andrea 在 v6 中以 sched_smt_active() 替换 static key，并与 arm64 侧检测方案一并解决。

## 效果评估
本线程无新数据。既有数据见 related_articles（Prateek 对 v5 的 Tested-by：4th gen EPYC 与 128C Ampere ARM 无性能影响）。

## 我可以参与的点
- 验证 sched_smt_active() 替代 static key 后，POWER7/Olympus 之外是否存在 SMT 激活但无 SD_ASYM_PACKING 排序的平台会被误伤（select_idle_smt_cpu() 是否在所有 SMT 机器上执行额外扫描），可在 v6 发出前把分析带回线程（review）。
- 其余参与点与 sched-20260910-007 相同（arm64 检测机制提案、跨平台测试），不重复。

## 参考链接
- Andrea 的让步答复（本日邮件）: https://lore.kernel.org/all/aqGHtIo2Bk2irSdu@gpd4/
- 被回复的 Vincent 邮件: https://lore.kernel.org/all/CAKfTPtASXty5hOOgmXokCh95w0idU0y12UDua1_vg9m8teF9Rg@mail.gmail.com/
- v4 系列封面（线程根）: https://lore.kernel.org/all/20260908082345.103087-1-arighi@nvidia.com/
- 同系列 v5 线程的当日进展: 见 sched-20260910-007

---
id: sched-20260910-008
date: 2026-09-10
subject: "sched/fair: Honor asymmetric SMT priority in idle selection"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260908082345.103087-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/aqGHtIo2Bk2irSdu@gpd4/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v4
generated_at: "2026-09-11T10:30:00"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Vincent Guittot"
patch_series:
  - version: v4
    msgid: "<20260908082345.103087-1-arighi@nvidia.com>"
    date: "2026-09-08"
    summary: "2/2 补丁：慢路径同样遵守 sibling 优先级，helper 定名 select_idle_smt_cpu()。"
    review_outcome: "09-09/09-10 Vincent 持续质疑新增 static key；09-10 Andrea 确认移除 static key、改用 sched_smt_active()，将落入下一版（与 v5 线程合流为 v6）。"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "static key 移除尚未以新版本发出"
    - "系列整体被 Peter 从收取队列 drop（见 sched-20260910-007），arm64 MIDR 检测替代机制未定"
  next_action: "v6 中以 sched_smt_active() 替换 static key，并连带解决 arm64 检测机制"
contribution_opportunities:
  - kind: review
    description: "分析 sched_smt_active() 替代 static key 后，SMT 激活但无 SD_ASYM_PACKING 排序的平台是否会在 select_idle_smt_cpu() 上付出无谓扫描，v6 发出前把结论带回线程"
source_email_count: 1
related_articles:
  - "sched-20260908-002"
  - "sched-20260907-005"
  - "sched-20260910-007"
tags:
  - arm64
  - topology
  - idle
  - hyperthreading
---
