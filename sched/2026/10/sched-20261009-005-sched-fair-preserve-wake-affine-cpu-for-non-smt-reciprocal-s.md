# sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups

## TL;DR
Shubhang Kaushik（Ampere）发 v5，让 narrow reciprocal 的 `WF_SYNC` 唤醒（pipe 式 ping-pong：A 唤醒 B、B 唤醒 A 循环）在非 SMT 系统上保住在 wake-affine 选中/保持的 waker CPU，而不是被后续 `select_idle_sibling()` 的空闲 CPU 搜索搬走。v5 基于最新 mainline 重基线并刷新 `perf bench sched pipe` 数据：80 核非 SMT Ampere Altra 上 mean 从 3.651 → 2.204 usec/op（约 39.6% 提升）。当日无回帖。

## 背景与问题
`WF_SYNC` 唤醒下 `wake_affine()` 可能选中 waker CPU，但 CFS 唤醒路径仍把该 target 交给 `select_idle_sibling()`，其空闲 CPU 搜索可能把 wakee 从 wake-affine target 搬走。对 pipe 式 ping-pong 负载，wakee 在两个任务间来回交接，此时把 wakee 搬到别的空闲 CPU 的代价可能高于保住 wake-affine 的 waker CPU。这是该系列（早期以「prefer waker CPU」为名，v1-v4）长期打磨的主题；作者为回应社区对「不要定义通用 WF_SYNC 放置规则」的关切，把范围收窄到「只处理 narrow reciprocal case，非 SMT」。

## 技术方案
利用既有的 `last_wakee` 与 `wake_wide()` 状态识别 narrow reciprocal `WF_SYNC` 唤醒（A→B、B→A 循环）。只对非 SMT 系统处理这一窄场景：一旦 wake-affine 路径选定或保持了 waker CPU，且 waker rq 无其它可运行任务，就在进入 `select_idle_sibling()` 之前返回 waker CPU，避免空闲搜索把这次 handoff 搬离 wake-affine target。明确不做通用 `WF_SYNC` 放置规则（通用 `WF_SYNC` 仍走既有 wake_affine + select_idle_sibling），SMT 系统也仍走 select_idle_sibling（借助 SMT 拓扑处理兄弟/核）；非对称容量系统上仍要求 wakee 能装进 waker CPU。v5 变化：重基线到最新 mainline、刷新 perf 数据、把 WF_SYNC 语义文档化为 advisory（无放置契约、无通用策略）。

## 版本演进与当前进展
*current_version: v5*（`<20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>`）。此前迭代（v1-v4）以「prefer waker CPU for non-SMT reciprocal sync wakeups」为名于 7-8 月发出过；v5 更名重基线。当日无回帖，尚未有维护者 review。

## Maintainer 意见与讨论焦点
当日无回帖。此前迭代中社区对「通用 WF_SYNC 放置规则」持谨慎态度，作者已在 v5 把文档措辞收窄为 advisory、并明确仅处理 narrow reciprocal 非 SMT 场景，以此回应这一关切。

## 合入评估
*likelihood=unknown*。v5 刚发出、当日无回帖，尚无维护者（Vincent/Peter）表态；此前迭代的「通用 WF_SYNC 规则」关切是否已被 v5 的收窄完全化解，需等新一轮 review 确认。*next_action*：等 sched 维护者 review v5 的窄化范围与数据。

## 效果评估
作者在 80 核非 SMT Ampere Altra 上给出 `perf bench sched pipe -l 1000000`（30 轮）数据（基线 tip/sched/core `4a3b51aab6e2`）：

- 默认：mean 3.651→2.204 usec/op（+39.6%），median 3.733→2.200（+41.1%）
- `taskset -c 78,79`：mean 3.820→2.691（+29.6%），median 3.887→2.444（+37.1%）
- `taskset -c 79`（单核）：mean 2.292→2.113（+7.8%）

Schbench（normal 8/40/80/240 workers、pipe 1/2/4/8）三轮 15s 无明显回退；pipe 1/2 worker 十轮 30s 确认，worker transfer median 变化 -0.3%/-2.4%、无唤醒时延回退；hackbench process/thread pipe 1/2/4/8 组亦跑过（未纳入对比）。

## 我可以参与的点
- `testing`：在其它非 SMT 平台（尤其非 x86/ARM 服务器类）复跑 perf bench pipe，确认 39.6% 的可迁移性；在 SMT 系统验证「仍走 select_idle_sibling」的约束不被破坏。
- `review`：审 narrow reciprocal 识别的边界（来回交接节奏、wake_wide 阈值）在长链任务下是否误判。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org/

---
id: sched-20261009-005
date: '2026-10-09'
subject: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org/'
authors:
  - 'Shubhang Kaushik'
maintainers_involved: []
current_version: v5
patch_series:
  - version: v5
    msgid: '<20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>'
    date: '2026-10-09'
    summary: 'narrow reciprocal WF_SYNC 非 SMT 保住 waker CPU；重基线并刷新 perf 数据'
    review_outcome: '当日无回帖'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'v5 当日无回帖，尚无维护者 review'
  next_action: '等 sched 维护者 review v5 的窄化范围与数据'
contribution_opportunities:
  - kind: testing
    description: '非 SMT 平台复跑 perf bench pipe 验证可迁移性'
  - kind: review
    description: '审 narrow reciprocal 识别边界是否误判长链任务'
generated_at: '2026-10-10T01:30:00'
source_email_count: 1
related_articles: []
tags:
  - cfs
  - affinity
---