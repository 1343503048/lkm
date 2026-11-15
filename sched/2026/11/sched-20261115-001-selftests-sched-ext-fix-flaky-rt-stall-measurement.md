# selftests/sched_ext: Fix flaky rt_stall measurement

## TL;DR

Jonathan Bastari Thamrin 发 v2 修 rt_stall selftest 的 CI flake：根因是 CORE_ID 上 DL server budget 被其它 FAIR/EXT 任务共享、父任务未 pin 走、以及用 /proc/stat 的 USER_HZ(10ms) 粗粒度计时导致比例失真。v2 改用 clock_getcpuclockid() 精确计时并把父任务 pin 到 CORE_ID 之外。sched_ext 维护者 Andrea Righi 已 Reviewed-by，仅剩措辞与注释两个小改动，合入 for-7.4-fixes 可能性高。

## 背景与问题

rt_stall.c 的 sched_stress_test() 验证 RT 任务与 EXT 任务竞争 5 秒窗口内 EXT 能否拿到 >=4% 的 CPU 时间。三个因素共同导致 CI flake：(1) CORE_ID 上 DL server budget 与其它 FAIR/EXT 任务（含未 pin 的父任务）共享；(2) 父任务要等 DL server 才到 sleep()，启动慢；(3) 每任务 runtime 按 fork 以来的累计值、以 USER_HZ(10ms) 粒度读取。CI 上 EXT 任务只拿到 ~0.18s（3.0-3.9% 份额），低于 4% 阈值；作者另观察到父任务 pin 到 CORE_ID 时 RT 任务 sleep() 前已跑 ~0.95s 被记为 5.69s，EXT 份额掉到 ~4.2%。

## 技术方案

v2 把 runtime 测量从 /proc/<pid>/stat 改为 clock_getcpuclockid() + clock_gettime() 读每任务 CPU 时钟，取 sleep() 前后 delta 得到精确测量窗口；并把父任务用 sched_setaffinity() pin 到 CORE_ID 之外的 CPU（不再共享 DL server budget）。rt_stall.c 一处 +65/-23。4% 阈值保持不变（v2 实测 4.86-5.10%/20 次运行）。

## 版本演进与当前进展

*current_version: v2（2026-11-15，`<20261115-scx-rt-stall-v2-1-926678b214c6@gmail.com>`）*。

- v1（11-14）：用 /proc/<pid>/stat 读 runtime，父任务未 pin，USER_HZ 粗粒度计时。
- v2（11-15）：按 Andrea 建议改 CPU 时钟 + pin 父任务出 CORE_ID；阈值不变，作者未能复现 CI 的 kthread 噪音，表示可接受降阈值到 3%。

## Maintainer 意见与讨论焦点

- **Andrea Righi（sched_ext 维护者）**：认可改进方向，但指出 CORE_ID 上的 per-CPU kthread 仍可能消耗 budget，未必能完全消除 CI flake；建议 changelog 措辞从 "fix CI flakes" 改为 "reduce measurement noise"（后续仍 flaky 再降阈值），并请补一条说明 dl_server budget 与 CORE_ID 上其它 EXT/FAIR 任务共享的注释。给出 *Reviewed-by*。

## 合入评估

*likelihood=high*。维护者已 Reviewed-by，方向与实现均被认可，仅剩文案与注释两个小改动。*blocking_issues*：需按 Righi 意见调整 changelog 措辞并补注释。*next_action*：作者提交 v3 调整措辞与注释后，可由 Righi 收取进 sched_ext for-7.4-fixes。

## 效果评估

v2 后父任务 pin 走、RT 测 ~4.75s、EXT 份额 4.86%-5.10%（20 次运行），稳定高于 4% 阈值。作者未能复现 CI 上的 kthread 噪音干扰，Righi 认为这属「降低测量噪音」而非彻底修复。

## 我可以参与的点

- **testing**：在带 per-CPU kthread 干扰的真实 CI / 多核环境复跑 rt_stall，验证 EXT 份额是否仍会低于 4%；若仍 flaky 可回帖支持进一步降低阈值。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261115-scx-rt-stall-v2-1-926678b214c6@gmail.com/
- v1: https://lore.kernel.org/r/20261114-scx-rt-stall-v1-1-4188a9378067@gmail.com

---
id: sched-20261115-001
date: '2026-11-15'
subject: "selftests/sched_ext: Fix flaky rt_stall measurement"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261115-scx-rt-stall-v2-1-926678b214c6@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261115-scx-rt-stall-v2-1-926678b214c6@gmail.com/"
authors: [Jonathan Bastari Thamrin]
maintainers_involved: [Andrea Righi]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261114-scx-rt-stall-v1-1-4188a9378067@gmail.com>"
    date: '2026-11-14'
    summary: "用 /proc/<pid>/stat 读 runtime，父任务未 pin，USER_HZ 粗粒度计时"
    review_outcome: "Andrea 建议改用 CPU 时钟 + pin 父任务"
  - version: v2
    msgid: "<20261115-scx-rt-stall-v2-1-926678b214c6@gmail.com>"
    date: '2026-11-15'
    summary: "改用 clock_getcpuclockid() 精确计时并把父任务 pin 出 CORE_ID"
    review_outcome: "Andrea Reviewed-by，要求改措辞并补注释"
upstream_commit: null
fixes_commit: "be621a76341c"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "需按 Righi 意见把 changelog 措辞改为 'reduce measurement noise' 并补 dl_server budget 共享注释"
  next_action: "作者提交 v3 调整文案与注释后由 Righi 收取进 sched_ext for-7.4-fixes"
contribution_opportunities:
  - kind: testing
    description: "在带 per-CPU kthread 干扰的多核/CI 场景复跑 rt_stall，验证 EXT 份额是否仍低于 4%"
generated_at: "2026-11-16T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [sched_ext, dl_server]
---