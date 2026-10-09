# sched/fair: avoid redundant updates for unchanged default slices

## TL;DR
Chengfeng Lin 发 RFC，优化 `sched_setparam()` 在参数未变时仍走参数更新路径的开销：当 SCHED_OTHER 任务用默认 slice 且 slice 未变时，直接走 no-change 捷径。作者原型把每次 `sched_setparam()` 调用成本从 618.18ns 降到 163.23ns（省 455ns、约 73.6%）。属合成 syscall 微基准，作者明确「不是应用加速」。当日无回帖。

## 背景与问题
对参数未变的重复 `sched_setparam()` 调用，`SCHED_OTHER` 默认 slice 任务仍走参数更新路径。作者调查一个 no-change 负载在 v6.12.95↔v7.2 间 6.5-7.1% 的耗时上升时发现：遗留包装 `_sched_setscheduler()` 把 `attr.sched_runtime` 留为 0（0 表示「用默认」，不是零长度 slice），而 `p->se.slice` 存的是实际时长；`__sched_setscheduler()` 拿两者比较，即使任务已用当前默认值也继续走更新。自定义 slice 时包装会拷贝实际时长，故既有 no-change 捷径有效——唯独默认 slice 失效。

## 技术方案
把 no-change 捷径扩展到未变的默认 slice：新增 case 要求「fair 调度类 + nice 未变 + 默认 slice 模式 + slice 匹配当前 base 值」。当一个隐含 uclamp 请求需要重置时（RT 优先级继承提升结束后）仍走完整更新；权限与 LSM 检查保持在捷径之前；显式 uclamp 更新与 reset-on-fork 处理不变。

## 版本演进与当前进展
v1（RFC，`<CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>`）。当日无回帖。作者明确标注这是 RFC、求feedback 的优化。

## Maintainer 意见与讨论焦点
当日无回帖，无维护者表态。作者自己划定的关键边界是「隐含 uclamp 重置（RT PI 结束后）必须仍走完整更新」——这一约束是否正确是合入前需要 reviewer 确认的点。

## 合入评估
*likelihood=unknown*。RFC 当日无回帖；且这是一个合成 syscall 微基准驱动的优化，社区对「为微基准增益引入的 no-change 捷径」往往要求评估真实收益与边界复杂度。*blocking_issues*：① 无 review；② 真实应用收益未知（作者自述「synthetic microbenchmark, not an application speedup」）。*next_action*：等维护者判断该捷径是否值得、边界是否完整。

## 效果评估
作者在 i7-12700KF 上用原始 v7.2 → 原型 → 原始 v7.2 的 A/B/A 测法（每 case 3 轮 warmup + 15 轮 × 500k 调用，GCC 15.2.0，full preemption、performance governor/EPP、Turbo off，CV < 0.19%）：

- 默认 slice：mean 619.40 → 163.23 → 616.97 ns/次
- 自定义 10ms slice（对照）：162.51 → 162.64 → 162.68 ns/次

作者强调这是合成 syscall 微基准、不代表应用加速；并另做了 sched_setattr() A/B/A。作者也诚实说明本补丁只测优化、不解释 v6.12.95↔v7.2 间耗时上升的根因。

## 我可以参与的点
- `review`：审「隐含 uclamp 重置必须走完整更新」的判断是否覆盖所有 PI 结束后的重置场景，以及默认 slice 捷径与 `nice`/优先级继承的交互。
- `discussion`：合成微基准收益是否足以正当化新增的 no-change 捷径分支（维护成本 vs 收益）。

## 参考链接
- lore thread: https://lore.kernel.org/all/CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com/

---
id: sched-20261009-008
date: '2026-10-09'
subject: 'sched/fair: avoid redundant updates for unchanged default slices'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>'
lore_url: 'https://lore.kernel.org/all/CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com/'
authors:
  - 'Chengfeng Lin'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>'
    date: '2026-10-09'
    summary: '默认 slice 未变时走 no-change 捷径'
    review_outcome: '当日无回帖'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无 review'
    - '真实应用收益未知'
  next_action: '等维护者判断捷径收益与边界完整性'
contribution_opportunities:
  - kind: review
    description: '审隐含 uclamp 重置与默认 slice 捷径的交互'
  - kind: discussion
    description: '微基准收益是否值得新增 no-change 捷径分支'
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles: []
tags:
  - cfs
  - eevdf
---