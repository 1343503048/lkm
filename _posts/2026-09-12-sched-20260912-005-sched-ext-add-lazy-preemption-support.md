---
id: sched-20260912-005
subject: 'sched_ext: Add lazy preemption support'
date: '2026-09-12'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260911195800.974364-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260911195800.974364-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260911195800.974364-1-arighi@nvidia.com>
  date: 2026-09-12
  summary: SCX_ENQ_PREEMPT_LAZY/SCX_KICK_PREEMPT_LAZY/SCX_OPS_LAZY_SLICE_EXPIRY 让
    BPF 调度器获得 fair 同款 lazy 抢占；拒绝立即+lazy 与 lazy+KICK_WAIT 组合；未知 kick flag 拒绝化；配套 623
    行 kick selftest（fexit 探针校验 reschedule TIF）。瞄准 sched_ext/for-7.4。
  review_outcome: 当日零回帖。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 零 review；Tejun 未表态
  - 未知 kick flag 拒绝化对存量 BPF 调度器的影响未核对
  next_action: 等 SCX 社区首轮 review；关注行为收紧项的兼容性结论
contribution_opportunities:
- kind: review
  description: 核对 flag 拒绝化的存量影响与 lazy/立即并存的合并语义
- kind: testing
  description: 启用 LAZY_SLICE_EXPIRY 实测 250Hz 下内核态长任务延迟变化
generated_at: '2026-09-14T12:40:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
- preempt
title: 'sched_ext: Add lazy preemption support'
layout: article
---

## TL;DR
Andrea Righi 直接投递到 sched_ext/for-7.4 树的双补丁系列：给 BPF 调度器补上 fair 类已有的「惰性抢占」能力——新增 SCX_ENQ_PREEMPT_LAZY / SCX_KICK_PREEMPT_LAZY 与 SCX_OPS_LAZY_SLICE_EXPIRY，slice 过期后调度边界可推迟到返回用户态或下个 tick；配套一个 623 行的 kick selftest（fexit 探针校验精确的 reschedule TIF）。当日无回帖。

## 背景与问题
fair 调度类支持 lazy rescheduling：lazy 请求不在下一个内核抢占点立即抢占，而是推迟到返回用户空间或被下一个 tick 升级为立即抢占，避免不必要的内核态抢占同时约束调度延迟。sched_ext 此前只向 BPF 调度器暴露立即抢占，无法做同样的取舍。

## 技术方案
- patch 1（kernel/sched/ext，+149/-33）：
  - 新增 SCX_ENQ_PREEMPT_LAZY 与 SCX_KICK_PREEMPT_LAZY：与立即抢占一样清掉当前任务 slice，但改用 resched_curr_lazy()；非本地 DSQ 的 lazy enqueue 保留 head-insertion 语义；
  - 新增 SCX_OPS_LAZY_SLICE_EXPIRY：task_tick_scx() 中 slice 耗尽时请求 lazy 重调度（对齐 fair 的 update_curr() 行为）；默认仍为立即，sched_ext 关闭过程中也保持立即；
  - 语义收紧：立即+lazy 组合请求被拒；lazy kick + SCX_KICK_WAIT 被拒（等待 lazy 边界的契约无界）；未知 kick flags 由忽略改为拒绝；
  - lazy kick 记在独立掩码（cpus_to_kick 之外），区分纯 lazy 与与普通/抢占 kick 并存的情况；立即抢占盖过已排队的 lazy；普通 kick 立即重调度但不动 slice，lazy 请求继续清 slice——两者兼得；
- patch 2（selftests，新增 kick.bpf.c 144 行 + kick.c 479 行）：在 __resched_curr() 挂 fexit 探针记录实际 reschedule TIF，配合 stopping callback 覆盖立即/ lazy kick、两种顺序的合并、tick 驱动的 slice 过期与非法 flag 组合；内核不含对应 flag 时跳过对应模式。

## 版本演进与当前进展
*current_version: v1（cover msgid `<20260911195800.974364-1-arighi@nvidia.com>`，09-12 03:56 入缓存）*，v1 刚发出、暂无 review 意见。subject 前缀 `[PATCHSET sched_ext/for-7.4]` 表明系列瞄准 Tejun 的 for-7.4 分支。

## Maintainer 意见与讨论焦点
当日缓存内零回帖，未获取到任何维护者表态。可关注的评审点（系列自身暴露的设计选择）：立即与 lazy 请求并存时的合并语义、KICK_WAIT 拒绝的边界、未知 flag 从忽略改为拒绝的兼容性影响（对已有 BPF 调度器是行为变化）。

## 合入评估
*likelihood=unknown*：无 review 可依据；投递目标为维护者树（for-7.4）说明作者预期直接进树，但 Tejun 未表态。*blocking_issues*：未知 kick flag 拒绝化对存量 BPF 调度器的影响需要核对；selftest 对 fexit 探针的依赖需要在无 BTF/精简内核上验证。*next_action*：等 Tejun/SCX 社区首轮 review；关注行为收紧项是否被要求回退或加兼容层。

## 效果评估
暂无 benchmark 数据：cover 描述的是能力对齐（与 fair 同等 lazy 选择权）而非性能数字；selftest 验证的是语义正确性（TIF 记录、合并顺序），无延迟/吞吐对比。

## 我可以参与的点
- kind=review：核对「未知 kick flags 拒绝化」对存量 BPF 调度器（scx_simple、scx_qmap 等）的影响，以及 lazy 与立即并存时的 slice 清除/保留组合是否符合直觉——这是系列最可能被追问的两处。
- kind=testing：在自定义 BPF 调度器中启用 SCX_OPS_LAZY_SLICE_EXPIRY，实测 250Hz 下内核态长任务（IO/锁密集）的调度延迟变化，补系列缺失的量化数据。

## 参考链接
- cover letter：https://lore.kernel.org/all/20260911195800.974364-1-arighi@nvidia.com/
- patch 1/2：https://lore.kernel.org/all/20260911195800.974364-2-arighi@nvidia.com/
- patch 2/2（kick selftest）：未获取到（未入当日缓存，msg-id 形如 …974364-3-…，未缓存不做推断）
