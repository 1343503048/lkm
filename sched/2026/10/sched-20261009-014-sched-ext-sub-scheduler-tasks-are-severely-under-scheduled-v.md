# sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261008-006：Tao Cui 报告疑似 dispatch 饥饿：父子 cid 调度里，busy-loop 任务在子调度器 attach **之前**进 cgroup 时，子调度器每轮都 claim 到该任务但运行 duty 只有 ~0.3%（10s 窗口 0 或 ~20-27 tick），同属 root 的等价任务 ~100%；attach 之后移入则正常，饥饿比约 300x。Tejun 回复要求补全调度器源码与完整复现步骤。
- sched-20261009-014（今天）：**Tao Cui 交出完整材料**——`scx_k2`（单二进制、parent/root 与 child/sub 两模式）源码、KVM 环境（`-cpu host -smp 4`、HZ=1000）、for-7.4 内核 + caps-clear 补丁的具体 commit（`f55a5ae74ca6` + `cda36da11910`），以及 11 步可复现流程。待 Tejun 定位。

## 背景与问题

（承接 sched-20261008-006）报告针对 sub-scheduler attach 流程的 dispatch 饥饿：attach 之前移入 cgroup 的任务走 enable walk 的 handover 路径、几乎饿死；attach 之后移入走迁移路径、正常。今天的增量是作者补齐了 Tejun 要求的可复现材料，使报告从「不可用」变为「可定位」。

## 技术方案

本日仍是问题报告而非补丁。作者补充的复现材料要点：

- 调度器 `scx_k2`：单二进制两模式。parent/root 通过 cgroup 向 child/sub grant `SCX_CAP_PERF | SCX_CAP_ENQ_IMMED`；child 只在 `ops.tick()` 里写 cpuperf target 1；两个调度器每 2s 打印计数器。
- 环境：x86_64 KVM（`-enable-kvm -cpu host -M pc -smp 4 -m 4G`）、CONFIG_HZ_1000、默认 NO_HZ idle、cgroup2。内核为 for-7.4 `f55a5ae74ca6` + caps-clear 补丁 `cda36da11910`。
- 复现（11 步）：起 parent → 把 pin 到 CPU0 的 spinner 移进 cgroup（attach 之前）→ 起 pin 到 CPU2 的 root-owned spinner → attach child → 等 6s → 读 `/proc/<pid>/stat` 的 utime+stime 与两调度器计数器。

## 版本演进与当前进展

单条 `[REPORT]`，无补丁。今天作者补齐 Tejun 要求的材料（源码 + 完整复现步骤），报告进入「待 Tejun 定位」阶段。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：昨日要求补材料；今日尚未对补齐后的材料给出结论。
- 未决：handover 路径的 ~0.3% duty 是真实内核缺陷、子调度器使用方式问题，还是已知限制，待 Tejun 用新材料判定。

## 合入评估

*likelihood=unknown*。作者已补齐可复现材料，但 Tejun 尚未判定结论；尚无补丁。*blocking_issues*：待 Tejun 用新材料定位根因。*next_action*：Tejun 分析复现、判定 handover 路径是否存在饥饿；若有内核缺陷则出修复。

## 效果评估

（承接）作者此前给出：attach-before 场景 child-owned 任务 ~0.3% duty vs root-owned ~100%（约 300x 饥饿比）；attach-after 无饥饿。今天补充了完整复现脚本与调度器源码，材料已可独立验证。

## 我可以参与的点

- `testing`：用作者给的 `scx_k2` + 11 步流程独立复现，验证饥饿比与 root.log/sub.log 计数器。
- `discussion`：分析 enable walk 的 handover 路径在 slice 消耗/再入队上的差异，帮助定位 ~0.3% duty 来源。

## 参考链接

- 作者今日复现材料: https://lore.kernel.org/all/3e044142-8f2c-45a2-8d5f-75d301526023@linux.dev/
- 原报告: https://lore.kernel.org/all/163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev/

---
id: sched-20261009-014
date: '2026-10-09'
subject: 'sched_ext: sub-scheduler tasks are severely under-scheduled vs root-owned tasks'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: '<163e2397-0e3e-4cc0-842b-0d36598d13d7@linux.dev>'
lore_url: 'https://lore.kernel.org/all/3e044142-8f2c-45a2-8d5f-75d301526023@linux.dev/'
authors:
  - 'Tao Cui'
maintainers_involved:
  - 'Tejun Heo'
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '待 Tejun 用新材料定位根因'
  next_action: 'Tejun 判定 handover 路径是否饥饿'
contribution_opportunities:
  - kind: testing
    description: '用 scx_k2 + 11 步流程独立复现饥饿'
  - kind: discussion
    description: '分析 handover 路径 slice 消耗/再入队差异'
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles:
  - sched-20261004-004
  - sched-20261007-004
  - sched-20261008-006
tags:
  - sched_ext
---