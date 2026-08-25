# Tejun 把 scx 仓库领先内核的工具头文件同步回内核树（`tools/sched_ext/include/scx`）


## TL;DR
Tejun 把 scx 仓库领先内核的工具头文件同步回内核树（`tools/sched_ext/include/scx`），修复 64 位 enum 恢复、v6.18+ `is_migration_disabled()` 少报等问题。已基于 `sched_ext/for-7.3-fixes`，属常规同步。

## 背景与问题
scx 仓库维护的 `tools/sched_ext/include/scx` 头文件积累了若干修复与改进，内核副本缺失，导致基于旧内核的 BPF 调度器在兼容性上落后。

## 技术方案
两封补丁同步回内核：
- `common.bpf.h` (+140)、`compat.bpf.h` (+68)、`compat.h` (+97)、`enum_defs.autogen.h` (+5)、`enums_abi.autogen.h` (+223)。
- `__COMPAT_read_enum()` 借新增 autogen 枚举 ABI 表，可在缺 `BTF_KIND_ENUM64` 的内核恢复 64 位 scx enum。
- `is_migration_disabled()` 修复 v6.18+ `!PREEMPT_RCU` 内核（BPF prolog 不再禁用 migration）下对当前任务少报。
- 纳入 Gavin/Changwoo 的 `scx_bpf_dsq_peek()` 版本门与 `scx_bpf_reenqueue_local_from_anywhere()`（已合 review 反馈）。
- 恢复 `__COMPAT_scx_bpf_cpu_curr()` 供 pre-v6.18 调度器；rq clock helper 文档化 idle CPU 的 stale-read 行为。

## 版本演进与当前进展
v1（2026-08-19），Tejun 自行提交，基于 `sched_ext/for-7.3-fixes (5f01293930d1)`，分支 `scx-tools-header-sync`。

## Maintainer 意见与讨论焦点
无争议（工具头同步，作者即维护者）。

## 合入评估
已基于 `sched_ext/for-7.3-fixes`，合入可能性 merged。随该分支进主线。

## 效果评估
无独立 benchmark；属兼容性修复，关键收益是 pre-v6.18 / 缺 ENUM64 BTF 内核上的 BPF 调度器不再踩兼容坑。

## 我可以参与的点
- 在 v6.18+ `!PREEMPT_RCU` 内核验证 `is_migration_disabled()` 行为；或帮测旧内核调度器兼容性。

## 参考链接
- git branch: git://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git scx-tools-header-sync
- lore thread: 未获取到

---
id: sched-20260819-009
date: 2026-08-19
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "把 scx 仓库中领先内核副本的 tools/sched_ext/include/scx 头文件同步回内核树：__COMPAT_read_enum() 现可在 BTF 缺 BTF_KIND_ENUM64 的内核上恢复 64 位 scx enum（新增 autogen 枚举 ABI 表）；is_migration_disabled() 修复 v6.18+ !PREEMPT_RCU 下当前任务少报；纳入 Gavin/Changwoo 的 scx_bpf_dsq_peek() 版本门与 scx_bpf_reenqueue_local_from_anywhere()（已合 review）；恢复 __COMPAT_scx_bpf_cpu_curr() 供 pre-v6.18 调度器，rq clock helper 文档化 idle CPU 的 stale-read 行为。基于 sched_ext/for-7.3-fixes (5f01293930d1)。"
    review_outcome: "Tejun 自行提交，含两封补丁；属于工具头同步，无争议。"
upstream_commit: "未获取到（已基于 for-7.3-fixes 分支）"
fixes_commit: null
merged_branch: "sched_ext/for-7.3-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: ["已基于 for-7.3-fixes，属常规头同步"]
  next_action: "随 sched_ext/for-7.3-fixes 进入主线。"
contribution_opportunities:
  - kind: testing
    description: "可在 v6.18+ !PREEMPT_RCU 内核上验证 is_migration_disabled() 不再少报当前任务。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 1
related_articles: ["sched-20260818-002"]
tags: [sched_ext, compatibility]
---
