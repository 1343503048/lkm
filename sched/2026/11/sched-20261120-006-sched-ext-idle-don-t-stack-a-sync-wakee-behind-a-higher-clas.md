# sched_ext: idle: Don't stack a sync wakee behind a higher-class task

## TL;DR

Hang Zhengyang 发 2 补丁系列（sched_ext/for-7.5）：sched_ext 默认 idle CPU 选择会把 sync wakee 放到 waker 所在 CPU，即使 waker 是仍在运行的 RT/DL 任务——wakee 在其它 CPU 都空闲时被迫等待（实测最长 1.5s）。patch 1 对更高 class 的 waker 停止该捷径，patch 2 加 selftest。作者给出完整前后对比数据（16/16 迟 169ms-1.5s → ≤0.6ms）。刚发出，未获维护者 review。

## 背景与问题

sched_ext 空闲 CPU 选择捷径为「WF_SYNC」同步唤醒把 wakee 放在 waker 的 CPU 上以利用缓存/近邻。但当 waker 是 RT 或 DL 任务且继续运行时，被唤醒的（fair 类）wakee 只能在同 CPU 排队等待，哪怕其它 CPU 空闲——实测 RT waker 的 pipe 场景下 16/16 次 wakee 留在 CPU 0 且迟 169ms-1.5s。捷径自 sched_ext 引入即存在（故无 Fixes tag），改变了任务运行位置但不算内核正确性 bug。

## 技术方案

- **patch 1/2** `sched_ext: idle: Don't stack a sync wakee behind a higher-class task`（kernel/sched/ext/idle.c，+11 行）：当 waker 是更高调度类（RT/DL）任务时不走该 sync 捷径，让 wakee 落到空闲 CPU。
- **patch 2/2** `selftests/sched_ext: Test sync wakeups from an RT task`：新增 `sync_wake_rt` selftest（257 行），无 patch 1 时失败。

代价：更高 class 任务 sync 唤醒后，wakee 不再跑在 waker CPU 上（`WF_SYNC` 本就不承诺这一点）。pipe ping-pong（RT↔EXT）往返从 ~6.5µs 增到 ~9.8µs，但 CFS 同场景约 10µs；大非-SMT 机器差距可能更大。作者提示 Hui Su 的 patch「Honor SCX_PICK_IDLE_CORE」改动了相邻一行，后应用的补丁需小幅 rebase。作者用 Claude Code 辅助找问题/写补丁/跑测试，并在 bare metal 复现。

## 版本演进与当前进展

*current_version: v1（2026-11-20，`<20261120-scx-fix75-v1-0-254f782ff9b0@gmail.com>`，2 补丁）*。首版，未获 review。

## Maintainer 意见与讨论焦点

暂无维护者/评审表态（当日缓存仅含系列邮件，未见 Tejun/Andrea 回复）。作者披露了与 Hui Su 补丁的 rebase 冲突及 [1] 引用的「fair 侧检测互唤任务对」的可复用性。

## 合入评估

*likelihood=unknown*。补丁有完整测试与再现数据、方向合理（修复 sync wakee 被高优先级任务挡住的明显延迟），但当日无任何维护者表态，属 RFC 无人表态阶段。*blocking_issues*：无 review 反馈；与 Hui Su 相邻补丁存在 rebase 冲突。*next_action*：等 Tejun/Andrea 评审；确认与 `SCX_PICK_IDLE_CORE` 补丁的合并顺序。

## 效果评估

作者给出量化对比（8 vCPU KVM guest、非 debug 内核、各 boot 两次）：RT waker pipe 16/16 在 CPU 0、迟 169ms-1.5s → 空闲 CPU、≤0.6ms；ALWAYS_ENQ_IMMED 16/16 迟 16-483ms → ≤0.6ms；partial fair waker 一半 ~930ms 迟 → ≤0.6ms；`sync_wake_rt` 8/3/2 vCPUs 由 fail 转 pass；其它 sched_ext selftests 无变化。KASAN+lockdep v7.4-rc2 下同样修复且无告警。bare metal 上未打补丁的 distro v7.0 复现（reader 等 168ms+）。

## 我可以参与的点

- **testing**：在真实多核/大非-SMT 机器上复测 pipe ping-pong 往返时间（作者承认 ~6.5→9.8µs 的代价在此类机器可能更大），并验证 bare metal 上的改善。
- **review**：评估「仅对更高 class waker 跳过捷径」的判据是否应推广到 fair 侧互唤任务对（作者 [1] 引用的系列）。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20261120-scx-fix75-v1-0-254f782ff9b0@gmail.com/

---
id: sched-20261120-006
date: '2026-11-20'
subject: "sched_ext: idle: Don't stack a sync wakee behind a higher-class task"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261120-scx-fix75-v1-0-254f782ff9b0@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261120-scx-fix75-v1-0-254f782ff9b0@gmail.com/"
authors: [Hang Zhengyang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261120-scx-fix75-v1-0-254f782ff9b0@gmail.com>"
    date: '2026-11-20'
    summary: "2 补丁：更高 class waker 不走 sync 捷径，新增 sync_wake_rt selftest"
    review_outcome: "无 review 反馈"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无 review 反馈", "与 Hui Su 的 SCX_PICK_IDLE_CORE 补丁存在 rebase 冲突"]
  next_action: "等 Tejun/Andrea 评审并确认与相邻补丁的合并顺序"
contribution_opportunities:
  - kind: testing
    description: "真实多核/大非-SMT 机器复测 pipe 往返代价与 bare metal 改善"
  - kind: review
    description: "评估 skips 判据是否推广到 fair 侧互唤任务对"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: []
tags: [sched_ext, idle]
---