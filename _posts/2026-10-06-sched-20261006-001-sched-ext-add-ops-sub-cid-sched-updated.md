---
id: sched-20261006-001
date: '2026-10-06'
subject: 'sched_ext: Add ops.sub_cid_sched_updated()'
subsystem: sched_ext
type: feature
status: under_review
severity: none
thread_root_msgid: <20261005175520.2756986-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261005175520.2756986-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261005175520.2756986-1-tj@kernel.org>
  date: '2026-10-06'
  summary: ops.sub_cid_sched_updated() 通知父调度器 cid 上的占用变化；scx_qmap 配套展示实际用量
  review_outcome: 发布当日无回帖
related_articles: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: op 尚无第二人 review/测试
  next_action: Tejun 收编进 sched_ext/for-7.4
generated_at: '2026-10-07T01:00:00'
tags:
- sched_ext
- cgroup
title: 'sched_ext: Add ops.sub_cid_sched_updated()'
layout: article
---

> **subject**：`sched_ext: Add ops.sub_cid_sched_updated()`

## TL;DR

Tejun Heo 为 sched_ext 的 sub-scheduler（父子调度器）委派模型补上**用量可观测性**：把 CPU（cid）委派给子调度器的父调度器，此前无法知道各被委派方实际用了多少——按需调整委派规模的父调度器无法度量，想把一个 cid 从一个子转交给另一个子的父调度器也看不到该从谁手里拿。本系列（3 补丁，`[PATCHSET sched_ext/for-7.4]`，基线 3521f92ddd5f）新增 `ops.sub_cid_sched_updated()`：当某调度器视角下「跑在一个 cid 上的调度器」发生变化时通知它——NONE（其子树无任务在该 cid）/ SELF（自己的任务）/ 直接子级的 cgroup id；子级**子树内部**的变化不上报。开销：调度器不变时每次上下文切换仅一次指针比较；通知只发给看到变化的调度器；整个机制挂在 static key 后、仅当加载的调度器实现了该 op 时开启。2/3、3/3 给 scx_qmap 配套——大机器上 cid 区间 buffer 尺寸修正 + 展示每个参与者实际使用的 cid 时间与分配额的对照。

## 背景与问题

sched_ext 的 sub-scheduler 分层里，父调度器把 cid（CPU）委派给子调度器，但委派出去后的**实际用量是黑盒**。两类父调度器受害：

- 按需定尺寸（sizes its delegations by demand）的父调度器：无法度量每个 delegatee 的真实使用量，无从收缩/扩张委派；
- 想在子之间转移 cid 的父调度器：看不到「这个 cid 当前被哪个子占用」，无法判断从谁手里收回。

这是 sub-scheduler 机制走向实用化的可观测性缺口（grant/revoke caps 已有 `sub_caps_updated()`/`sub_ecaps_updated()` 通知，但占用状态没有通知）。

## 技术方案

3 补丁（`<20261005175520.2756986-1-tj@kernel.org>`，8 文件 +352/−11，git branch `sub-cid-sched`）：

1. **1/3 `ops.sub_cid_sched_updated()`**（kernel/sched/ext/，+222/−1）：
   - 触发点埋在上下文切换路径：`scx_start_task_running()`（任务开始被跟踪时调 `scx_cid_sched_update(rq, sch)`）、`put_prev_task_scx()` 切出 ext 类时置 NULL、`switched_from_scx()` 的运行中类切换分支置 NULL。
   - 通知语义：NONE/SELF/直接子 cgroup id；子树内部变化不上报（父级只关心「哪个直接子」，不关心孙级细节）。
   - 开销控制：调度器不变时每次切换一次指针比较；通知只达看到变化的调度器；机制整体在 static key 后（`scx_ops_cid_sched_updated_enable()/disable()` 分别在 root enable/disable 时切换），未实现该 op 的调度器零成本。
   - 生命周期安全：调度器任务清空后其 disable 会关闭所有仍指向它的 rq session，free 后无悬挂引用。
   - 与既有 sub ops 一致：仅 cid 形态、上下文切换路径持 rq 锁运行。
2. **2/3 scx_qmap 大机器 cid 区间 buffer 尺寸**：cid 数量随机器规模增长，qmap 的 cid 区间缓存按机器尺寸调整。
3. **3/3 scx_qmap 显示每参与者实际 cid 使用**：在分配额（partition 划给每个参与者多少 cid 时间）旁边展示实际用量——正是本系列机制的直接演示用例。

## 版本演进与当前进展

- v1（10-06 01:55 北京，`<20261005175520.2756986-1-tj@kernel.org>`）首发，3 补丁 + git branch。当日无回帖。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者 + 作者）：目标分支即自己维护的 `sched_ext/for-7.4`；系列自洽（op + 示例调度器配套改造）。
- 当日无其他人回帖；无争议。

## 合入评估

*likelihood=high*。作者即 sched_ext 顶层维护者、分支自管、机制开销有明确论证（指针比较 + static key 门控）、附示例调度器演示。*blocking_issues*：无硬阻塞；op 尚无第二人 review/测试。*next_action*：Tejun 自行收编进 `sched_ext/for-7.4`；sub-scheduler 使用者（如 Tao Cui 等）可在实机上验证通知语义。

## 效果评估

无运行时数据。开销论证为代码层面：调度器不变时一次指针比较/切换、static key 仅在 op 被实现时开启。scx_qmap 侧的「实际用量 vs 分配额」展示是功能演示而非 benchmark。

## 我可以参与的点

- `review`：核对 `switched_from_scx()`/`put_prev_task_scx()` 的 NULL 置位是否覆盖全部「ext 任务离开 cid」路径（如类切换、dequeue-to-idle），确认无「子任务走了但通知未发」的漏报窗口。
- `testing`：写一个小 BPF 调度器实现 `sub_cid_sched_updated()`，记录 NONE/SELF/child-cid 序列并与实际任务布局对照，验证通知语义与 cover letter 描述一致。

## 参考链接

- 系列 cover: https://lore.kernel.org/all/20261005175520.2756986-1-tj@kernel.org/
- patch 1/3: https://lore.kernel.org/all/20261005175520.2756986-2-tj@kernel.org/
- patch 3/3（scx_qmap 实际用量展示）: https://lore.kernel.org/all/20261005175520.2756986-4-tj@kernel.org/
