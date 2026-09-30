# sched/eevdf: Fix slice protection across state changes

> **subject**：`sched/eevdf: Fix slice protection across state changes`

## TL;DR

Christian Loehle 的两枚 EEVDF slice-protection 边界修复（测试 Vincent Guittot 系列边界用例时发现）：1/2 让每次新授予的 protection 都无条件下限到最小 slice（当前任务自己持有最短 slice 时，既有 `slice != se->slice` 条件会漏掉 cap，让保护延续到旧 deadline）；2/2 保持「已过期的 protection」在 reweight 移动 vruntime 后仍是过期态（否则旧的绝对 vprot 重新复活，让 current 越过有更早 deadline 的 eligible 实体被选中）。分别补完 aae2a33ea662 与 80390ead2080 的边界。1/2 带 `Fixes: 82e9d0456e06`、2/2 带 `Fixes: 80390ead2080`。当日 Kayra 追问 2/2 的一个 reweight 路径反例，作者表示 1/2 与 update_protect_slice() 语义已镜像、需合并重发 v2。

## 背景与问题

两处 slice protection 边界会因 request-size 或 weight 变化而变陈旧：

1. 改变任务 slice 不丢弃其剩余 request。用 `PLACE_REL_DEADLINE` 时，`sched_setattr()` 缩短 slice 后，被保留的 deadline 可越过新 slice；`set_protect_slice()` 只在「另一个实体 slice 更短」时才应用 cap，若 current 自己最短，后续 pick 能保护它到旧 request 结束，`update_curr()` 也就不必在竞争者变为 eligible 时再请求重选。例如把 request 从 100 ms 减到 100 us 的任务，仍可与 1 ms 任务竞争时获得超过 26 ms 的新鲜保护。aae2a33ea662 只留下了 `slice == se->slice` 这一未覆盖分支。
2. `reweight_eevdf()` 缩放「存活」slice protection，但在移动 vruntime 时对「已过期」的 vprot 原样不动。reweight 可把 vruntime 移到旧 vprot 之后（如降低有正 lag 的实体的 weight），使 `protect_slice()` 重新为真——尽管并没有新授予 protection，current 会再次越过有更早 deadline 的 eligible 实体被选中。ff38424030f9 处理了存活 case、留下过期 case 未变。

## 技术方案

1. **1/2 `sched/eevdf: Cap protection when current has the shortest slice`**：无条件应用最小 slice 的 cap，包括 current 自己的 slice；仅在 `PREEMPT_SHORT` 且有更短 slice 竞争时保留更早的 ineligibility 边界。既保留 outstanding request，又限住每次新 pick 的保护。
2. **2/2 `sched/eevdf: Keep expired protection expired across reweighting`**：把「已过期的 current 实体」的 protection 锚定在新 vruntime（`vprot = vruntime`），使 `protect_slice()` 保持 false；对仍存活的 protection 保留既有缩放，不碰非 current 实体。

## 版本演进与当前进展

v1 刚发出（cover `<cover.1790756779.git.christian.loehle@arm.com>`，1/2、2/2 均在当日缓存）。当日有两人次回帖：

- Kayra 对 2/2：给出 `sched_change_end()` 激活 `task_a` 时（Fair 类、weight 不同于 h_load.weight）`enqueue_task_fair()` 以 `on_rq=false` 调 `reweight_eevdf()`（该块不生效）、随后 `place_entity()` 令 vruntime 回退，`set_next_task()` 走 `SNT_NORMAL` 不调 `set_protect_slice()` 的路径，怀疑「vruntime 倒退但 vprot 不被覆盖」的情形是否遗漏；询问应折进 2/2 还是他单独发补丁。
- 作者（对 1/2）：Elif 指出除 slice protection 边界与 vruntime 之外，此逻辑现已镜像 `update_protect_slice()`，应合并成一个函数，将重发。

## Maintainer 意见与讨论焦点

当日无维护者表态。讨论焦点：1/2 与 `update_protect_slice()` 语义重复、应合并（作者自认并决定重发）；2/2 的 reweight-vruntime 倒退反例由 Kayra 提出、待作者确认。无 NAK。

## 合入评估

*likelihood=medium*。两枚都是 `kernel/sched/fair.c`（+7/−5）的小幅、带 `Fixes:` 的边界修复，基于 Vincent 系列的既有上游方向，1/2/2/2 逻辑清晰；但作者已自认 1/2 需与 `update_protect_slice()` 合并重发，2/2 有 Kayra 的反例待澄清，尚未有维护者（Vincent/Peter）表态。*blocking_issues*：1/2 需合并函数后重发；2/2 的 Kayra 反例待澄清。*next_action*：作者发 v2（合并 1/2 与 update_protect_slice、回应 Kayra 的 2/2 反例）。

## 效果评估

作者给出两个机制示例：case1 任务 request 从 100 ms 减到 100 us 时，与 1 ms 任务竞争可获超过 26 ms 的新鲜保护；case2 定向 cgroup weight 变更可让过期 protection 复活并影响选择。无 benchmark 量化数据（属行为正确性修复）。

## 我可以参与的点

- `review`：跟进 Kayra 对 2/2 的 reweight 路径反例，判断 `vprot = vruntime` 锚定在 `sched_change_end()` 的 `SNT_NORMAL` 路径下是否仍成立或需补写 vprot。
- `testing`：用 rt-app 复现「四任务 100 us/1 ms/10 ms/100 ms 混合 + HRTICK」下 current 被错误 repick 的场景，验证 2/2 后不再越过更早 deadline 的 eligible 实体。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/cover.1790756779.git.christian.loehle@arm.com/
- lore（1/2）: https://lore.kernel.org/all/dd46b8eddbd760b4d5f2cb7d0eb5027bf70fad32.1790756779.git.christian.loehle@arm.com/
- lore（2/2）: https://lore.kernel.org/all/78ce8f8ceb4f5c7fda14216d3dff9d74e17f55ac.1790756779.git.christian.loehle@arm.com/
- Kayra 对 2/2: https://lore.kernel.org/all/20260930133716.214471-1-kayracizmeci@gmail.com/

---
id: sched-20260930-008
date: '2026-09-30'
subject: 'sched/eevdf: Fix slice protection across state changes'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<cover.1790756779.git.christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/cover.1790756779.git.christian.loehle@arm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<cover.1790756779.git.christian.loehle@arm.com>'
    date: '2026-09-30'
    summary: '1/2 无条件下限 protection 到最小 slice；2/2 保持过期 protection 在 reweight 后过期'
    review_outcome: 'Kayra 对 2/2 提 reweight 反例；作者自认 1/2 需与 update_protect_slice 合并重发'
upstream_commit: null
fixes_commit: '82e9d0456e06'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '1/2 需与 update_protect_slice() 合并后重发'
    - '2/2 的 Kayra 反例（sched_change_end/SNT_NORMAL 路径）待澄清'
  next_action: '作者发 v2：合并 1/2、回应 Kayra 的 2/2 反例'
contribution_opportunities:
  - kind: review
    description: '跟进 Kayra 对 2/2 的 reweight 路径反例，判断 vprot=vruntime 锚定在 SNT_NORMAL 路径下是否成立'
  - kind: testing
    description: '用 rt-app 复现四任务混合 + HRTICK 下 current 被错误 repick，验证 2/2 后不再越过更早 deadline 实体'
generated_at: '2026-10-01T01:00:00'
source_email_count: 5
related_articles: []
tags:
  - eevdf
---