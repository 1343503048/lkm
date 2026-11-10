# tools/sched_ext: robustness fixes from cold review

## TL;DR

Tao Cui（麒麟）发 9 补丁系列，修复 sched_ext 四个示例调度器（scx_flatcg / scx_pair / scx_qmap / scx_userland）在 cold review 中发现的一批健壮性问题：非法 stats interval 导致 100% CPU 忙旋、usage synopsis 漏选项、restart 后 pair_id/hier stats baseline 未复位、batch size 0 被静默接受导致任务堆积等。均为工具层小修，多数带 `Fixes:`，无内核改动。

## 背景与问题

这些示例调度器是 sched_ext 的参考实现与测试载体，工具层的参数校验缺陷会误导使用者或让调度器进入异常状态。典型两例：`scx_flatcg` 的 `-i` interval 用 `strtod()` 解析后经 `(float)` 转型切成 timespec，负值或无法经受 float 往返的值（如 2^24+1）会产生负的 tv_sec/tv_nsec 或 `tv_nsec >= 1e9`，`nanosleep()` 返回 EINVAL 却从不检查，stats 循环直接 100% CPU 忙旋；`scx_userland` 的 `-b 0` 被静默接受、batch_size 保持 0，`dispatch_batch()` 永远不把任务从 vruntime 链表搬进 dispatched 队列，任务不断堆积。

## 技术方案

逐调度器修：`scx_flatcg` patch 1/2 复位并校验 stats interval（负值/超界直接报错退出，nsec 从 double 而非 float 计算，堵住舍入洞）；`scx_pair` patch 3-5 处理 dispatching cgroup 消失时不再 abort、中断初始化后不再 attach、restart 时 reset pair_id；`scx_qmap` patch 6/7 补 usage synopsis 缺的 `-C/-B/-q` 选项并复位 hier stats baseline；`scx_userland` patch 8/9 在插入前检查 dispatch buffer 槽位、拒绝 batch size 0。8 个补丁带 `Fixes:` 指向此前引入对应功能的 commit。

## 版本演进与当前进展

*current_version: v1（2026-11-10，`<20261110125001.4167503-1-cui.tao@linux.dev>`）*。9 补丁首次成组发出，当日无评审回复。当日缓存只收到 2/9-7/9 与 9/9 共 7 封（缺 1/9、8/9 与 cover）。

## Maintainer 意见与讨论焦点

当日缓存无维护者回复。sched_ext 工具链由 Tejun Heo 维护；这些示例调度器修复与内核无关、风险低，常规评审即可。无 NAK。

## 合入评估

*likelihood=medium*。属低风险工具层收尾，多数带 Fixes 可直接套 stable；但尚未获 Tejun 或 sched_ext 维护者评审。*blocking_issues*：① 尚无维护者 look；② 两个补丁（1/9、8/9）未入当日缓存，需确认整系列完整性。*next_action*：等待 Tejun 评审后收款到 sched_ext 工具树。

## 效果评估

无性能数据。价值在正确性：堵住 100% CPU 忙旋与任务堆积这类工具层缺陷，cover 未给 benchmark。

## 我可以参与的点

- **testing**：逐个跑 scx_flatcg/scx_pair/scx_qmap/scx_userland 的修复事项（如 `scx_flatcg -i -0.5`、`scx_userland -b 0`）验证不再忙旋/堆积。
- **review**：确认 patch 1/9 与 8/9（当日缓存缺失）的内容与其余补丁一致、同属「robustness」主题。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110125001.4167503-1-cui.tao@linux.dev/

---
id: sched-20261110-004
date: '2026-11-10'
subject: "tools/sched_ext: robustness fixes from cold review"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261110125001.4167503-1-cui.tao@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261110125001.4167503-1-cui.tao@linux.dev/"
authors: [Tao Cui]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261110125001.4167503-1-cui.tao@linux.dev>"
    date: '2026-11-10'
    summary: "9 补丁修复四个示例调度器的健壮性问题"
    review_outcome: "当日无评审回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "尚无维护者 look"
  next_action: "等待 Tejun 评审后收款到 sched_ext 工具树"
contribution_opportunities:
  - kind: testing
    description: "验证 scx_flatcg -i 负值、scx_userland -b 0 等修复事项不再忙旋/堆积"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 7
related_articles: []
tags: [sched_ext]
---