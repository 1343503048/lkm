# [Question] Userspace throttling + "sched/fair: Combine detach into dequeue when migrating task" causes guest boot hang

## TL;DR
本文为增量更新（完整背景见 related_articles）。chenjinghuang（Huawei）与 Aaron Lu（ByteDance）在 08-27 把 guest 启动挂起问题的边界钉得更实：复现需要 **CPU 超额订阅 + 大量 vCPU**，96 vCPU 不复现、128 vCPU 复现；必须同时 revert `e1f078f50478`（Combine detach into dequeue）与 userspace throttling 的 `sched/fair: Switch to task based throttle model` 才能修复。Aaron 在 Intel 机上未能直接复现挂起（256 vCPU/4 CPU 配额能启动但满屏 softlockup），问题聚焦到"qemu 任务在 task-based throttle 下拿到的时间片过短"这一方向。仍未定位到根因，无补丁。

## 背景与问题
08-25 首报：host 开 userspace throttling（cgroup `cpu.max`）时，mainline guest 启动挂起；5.10 同配置（400000 quota / 128 vCPU VM）正常。git bisect 首轮指向 `e1f078f50478`（Combine detach into dequeue when migrating task），但单独 revert 后 v7.2 仍挂；二次 bisect 追到 task-based throttle 模型改动，**两者一起 revert 才恢复**。

## 技术方案
无修复方案（问题讨论线程）。08-27 新增的事实：
- chenjinghuang：ARM64 host、无 SMT、96 物理核；VM 配 128 vCPU（典型超额订阅）。**VM 配 96 vCPU 不复现**。host 上除起 VM 的任务外空载，但因超额订阅所有 96 CPU 上都有任务在跑（多数利用率 <10%），host 没有多少真正 idle 的 CPU。
- 他的猜想：任务在每个周期里"刚拿到一小段时间片就被 throttle"。
- Aaron Lu：现象与**任务数量**相关（vCPU 越多、qemu 线程越多）。他把自己 64core/128cpu Intel 机的 vCPU 加到 256、quota 4 CPU：**能启动**，但启动过程有多次 softlockup——他解读为 qemu 任务确实缺 CPU 时间，并推断再增 vCPU 或再减 quota 最终也会挂；另反问 chenjinghuang 的 guest 是否没开 softlockup 检测器（首报没有 softlockup 转储）。

## 版本演进与当前进展
非补丁系列，是跨 08-25 至 08-27 的调试线程（references 根 `<20260825120629.2472938-1-chenjinghuang2@huawei.com>`）。08-26 完成双 revert 定位（见 sched-20260826-004），08-27 完成规模边界（96 vs 128 vCPU）与跨机型对照（Intel 机不复现但出现同方向 softlockup）。当前无人提出候选修复。

## Maintainer 意见与讨论焦点
调度维护者未介入，参与者均非 sched maintainer。未解决点：(1) `e1f078f50478` 与 task-based throttle 两者叠加时的具体交互路径没走通——为什么 detach 合入 dequeue 会放大 throttle 的时间片碎片化；(2) guest 侧缺 softlockup 转储导致缺第一手现场；(3) "task gets throttled shortly after receiving a small time slice"仍只是猜想，无 ftrace 证据。

## 合入评估
无补丁可评估（**unclear** 作为问题推进度）。推进所需：在 v7.2 上抓 host 侧 qemu 任务的 enqueue/dequeue/throttle 序列（`sched_switch` + `cpu.max` 统计），确认时间片长度分布与 throttled 时机的因果，然后再看该出 fix 还是设计澄清。此问题对华为场景（ARM64 大核数 + cgroup cpu 配额 + VM 超额订阅）是潜在雷区。

## 效果评估
无数值数据；复现条件本身是唯一硬信息：ARM64 96C 无 SMT、128 vCPU、quota 400000 复现；96 vCPU 不复现；Intel 64C/128T、256 vCPU、quota 4 CPU 不挂但有 softlockup。

## 我可以参与的点
- **高对口**：本线程由 Huawei 同学发起、场景与 cpuset/cpu cgroup 生产环境重合，OLK-6.6 若已回合 `e1f078f50478` 或 task-based throttle，值得自查；
- 抓一份 host 侧 ftrace/perf 时序（qemu vCPU 线程被 throttle 的时刻 vs 时间片长度）回帖，可以直接把"小时间片+秒 throttle"猜想坐实或证伪——目前线程里没人给出这个证据；
- 在有 softlockup 检测的 guest 配置下复现一次，补上首报缺失的转储。

## 参考链接
- chenjinghuang 08-27 补充复现边界: https://lore.kernel.org/all/bc90cc67-93d0-463c-adf9-53b00a932d56@huawei.com/
- Aaron Lu 的 Intel 侧对照: https://lore.kernel.org/all/20260827111557.GB3616635@bytedance.com/
- Aaron 前一天提问（被回复）: https://lore.kernel.org/all/20260826100009.GA3616635@bytedance.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-005
date: '2026-08-27'
subject: '[Question] Userspace throttling + "sched/fair: Combine detach into dequeue when migrating task" causes guest boot hang'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<20260825120629.2472938-1-chenjinghuang2@huawei.com>"
lore_url: "https://lore.kernel.org/all/bc90cc67-93d0-463c-adf9-53b00a932d56@huawei.com/"
authors: [chenjinghuang, Aaron Lu]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: "e1f078f50478"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "根因未定位，无候选补丁；需 host 侧 throttle 时序证据"
    - "guest 无 softlockup 转储，现场信息缺失"
  next_action: "抓 qemu 任务 enqueue/dequeue/throttle 序列验证小时间片猜想"
contribution_opportunities:
  - kind: testing
    description: "OLK-6.6 自查是否同时回合了 e1f078f50478 与 task-based throttle；超额订阅场景压测"
  - kind: discussion
    description: "回帖 ftrace 时序数据或补 softlockup 转储"
generated_at: "2026-09-07T22:05:00"
source_email_count: 2
related_articles: [sched-20260826-004]
tags: [cgroup, cfs, hang, arm64]
---
