# sched_ext: cid: Represent clusters explicitly

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260926-005：Andrea Righi（sched_ext 维护者）为 sched_ext/for-7.4 新发的单枚补丁：让 sched_ext 的 CID 拓扑把「cluster」（同一 LLC 内共享 L2 等更紧资源的核组）显式表示为一段连续 CID 区间，并在 `struct scx_cid_topo` 里给出 cluster 归属。当时刚发出、尚无回帖。
- sched-20260927-001（今天）：Tejun Heo 对 v1/v2 给出密集 review（v2 review 明确标注 Claude 生成），核心诉求是让 cluster 层级「inclusive」——没有独立 cluster 层级的 core 自成 cluster（cluster_cid = core_cid）、与 LLC 同宽的 L2 保持一个 cluster；Righi 依次回以 v2（fallback 成自己为 cluster）和 v3（改用 inclusive mask），并基于 Tejun 的 `scx_bpf_cid_topo()` size 参数修复（for-7.3-fixes）重发。系列从「无回帖」进入活跃迭代，方向已收敛，值得继续跟进 v3 的审阅结果。

## 背景与问题

（承接 sched-20260926-005）sched_ext 的 CID 拓扑把每个拓扑层级（core / LLC / NUMA node）表示成一段**连续**的 CID 区间，但唯独对 **cluster**（同一 LLC 内共享 cache、比 LLC 其余 CPU 更紧密的核组，对应 `SD_CLUSTER` 调度域）不成立，`struct scx_cid_topo` 也没有字段标识 CPU 属于哪个 cluster。CID-form 调度器因此无法表达 cluster 级拓扑。

今天新增的讨论焦点是「没有独立 cluster 层级的 core 该如何表示」：v1 的做法（无 cluster 时 cluster_cid 取 LLC 自身、cluster_idx 置 -1、退化为单核 cluster）在 HMP 混合平台上有隐患，Tejun 指出更根本的语义问题——这在下面的「技术方案」展开。

## 技术方案

（承接 sched-20260926-005）核心是在 `kernel/sched/ext/cid.c` 里按 cluster 枚举核并新增 `cluster_cid`/`cluster_idx` 字段。今天的迭代集中解决「cluster 层级缺失」的表示语义，演进如下：

- **v1 做法**：无 cluster 时 cluster_cid 取 LLC 自身、cluster_idx 置 -1、无 cluster 层级的 CPU 视作单核 cluster。
- **Tejun 对 v1 的意见**：其他层级是 inclusive 的——对某 CPU 不存在的层级用下一层表示（非 SMT 机器的 core 就是 cpu）。cluster 也应如此：没有 cluster 层级的 core 自身是一个 cluster，`cluster_cid = core_cid` 且 cluster_idx 稠密。这样每个 cluster 都是连续 CID 区间、`cluster_idx` 可按 cluster 数组索引且无 -1 特殊值、真实 cluster 与 fallback CPU 之间不会发生 cluster_cid 别名。他还要求：`struct scx_cid_topo` 增长会破坏旧 BPF 二进制（kfunc 用内核 sizeof 拷出、程序用自己的 vmlinux.h 分配缓冲），因此先走 for-7.3-fixes 给 kfunc 加 size 参数，再让本系列叠在其上、新字段追加到结构体末尾。
- **Righi 采纳**：v2 改为「无独立 cluster 层级的 core 自成 cluster，cluster_cid = core_cid、cluster_idx 稠密」，并基于 size 参数修复重发。
- **Tejun 对 v2 的意见（Claude 生成 review）**：v2 的 fallback「inverts the hardware」——全部 core 共享同一 L2 的部件（单个 E-core 模块、或 L2 即 LLC 的 DSU）下，每个 core 都自成 cluster，找 L2 share 的调度器通过 cluster_cid 找不到任何东西；而 sched domain 在那里并不丢 cluster 层级，它丢的是 MC、保留 CLS。建议改为「inclusive mask」：`cpumask_or(cluster_scratch, topology_cluster_cpumask(xcpu), topology_sibling_cpumask(xcpu))` 再 `cpumask_and(..., llc_scratch)`，这样私有 L2 的 core 得到 core 自身、模块得到模块、与 LLC 同宽的 L2 每 LLC 一个 cluster，还顺带删掉带 NULL/empty 检查的 helper、把变量改成普通声明、去掉冗余的逐 LLC `cpumask_clear`。小项还有：kerneldoc 里 `scx_bpf_cid_override()` 仍写「core/LLC/node 被清零」需更新、测试段落可缩成一句、建议 subject 改为「sched_ext: Add the cluster level to the cid topology」。
- **v3 采纳**：改用 inclusive mask（「一个 core 若无更宽的 cluster 则自成一个，一个 LLC 宽的 cache 共享组构成一个 cluster」）；更新 `scx_bpf_cid_override` kerneldoc 与拓扑注释；补充说明 shard 可能切分 cluster、单靠 cluster_cid 无法判断是否存在更宽的 cluster 层级；遍历按 cluster 顺序而非 LLC 顺序，shard 仍在 core 边界切分。

## 版本演进与当前进展

- v1（2026-09-26，`<20260926152306.3190774-1-arighi@nvidia.com>`）：首发，cluster_idx 置 -1 的 fallback，无回帖（对应 sched-20260926-005）。
- 09-27 03:23：Tejun 回复 v1，提出 inclusive 语义 + 先给 kfunc 加 size 参数。
- 09-27 03:58：Righi 同意改成「core 自成 cluster」，并说明会叠在 size 参数修复上重发；另回应 Sashiko 关于丢 `__uninit` 的评论，认为 verifier 仍检查 out 缓冲读访问，属 false positive。
- v2（09-27，`<20260926212017.3351797-1-arighi@nvidia.com>`）：fallback 改为 core 自为 cluster。
- 09-27 07:27：Tejun 回复 v2（Claude 生成 review），指出 fallback 反转硬件覆盖，建议 inclusive mask。
- 09-27 14:12：Righi 同意改用 inclusive mask、去冗余 clear、变量改普通声明，预告 v3。
- v3（09-27，`<20260927133719.3458770-1-arighi@nvidia.com>`）：inclusive mask + kerneldoc 更新 + shard 切分说明。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者，两条实质 review，v2 那条标注 Claude 生成）：核心关注**fallback 语义与调度域对齐**——要求 cluster 层级与 core/LLC/node 一致地「inclusive」，否则在 L2 宽于 core 且窄于 LLC 的部件上会反转覆盖。其次是**ABI 前向兼容**：struct 增长会破坏旧 BPF 调度器，坚持先以 size 参数修复（for-7.3-fixes）打底、新字段追加到末尾。小项（kerneldoc、注释、代码整洁）也给了具体清单。
- **Andrea Righi**（作者/维护者）：对 Tejun 每条意见都明确采纳并落版（v2、v3），无分歧残留；唯一保留的是没按 Tejun 建议改 subject（仍用 `cid:` 前缀），并认为 Sashiko 关于 `__uninit` 的意见是 false positive。
- 未解决项：v3 尚未收到 Tejun 的审阅；subject 命名建议未被采纳（可能再被提）。

## 合入评估

*likelihood=high*。作者与维护者同为 sched_ext 维护者，迭代节奏快（一天内 v1→v3），方向（inclusive cluster 表示）已由 Tejun 明确敲定、无实质分歧；且已叠在「size 参数」修复之上解决 ABI 隐患。*blocking_issues*：v3 尚未过 Tejun 审阅；subject 命名是否调整未定；`CONFIG_SCHED_CLUSTER=n` 与非 x86 平台的边界行为需覆盖。*next_action*：等 Tejun 审阅 v3 的 inclusive mask 实现，确认后应能进 sched_ext/for-7.4。

## 效果评估

无性能数据（拓扑描述类 feature）。作者给出 Intel Core i7-13800H（P-core 6×SMT + E-core 8×2 模块、共 20 CPU 一个 LLC）的结构验证：P-core 对形成 two-CID cluster、E-core 模块形成 four-CID cluster、cluster_idx 在全部 8 个 cluster 上稠密。正确性属拓扑描述验证，未见量化指标。

## 我可以参与的点

- `review`：核查 v3 的 inclusive mask 语义（`topology_cluster_cpumask` ∪ `topology_sibling_cpumask` 再 ∩ llc）在「私有 L2 / 模块级 L2 / LLC 宽 L2」三类部件下是否与 `SD_CLUSTER` 的丢域规则一致，尤其 `CONFIG_SCHED_CLUSTER=n`（L2 mask 仍存在、sched domain 却不存在）时表现。
- `testing`：在 AMD 混合（Zen4/Zen4c）或非 x86 平台上验证 `scx_bpf_cid_topo()` 的 cluster_cid/cluster_idx 输出，确认 fallback（core 自为 cluster）与稠密索引行为。

## 参考链接

- v3 补丁: https://lore.kernel.org/all/20260927133719.3458770-1-arighi@nvidia.com/
- v2 补丁: https://lore.kernel.org/all/20260926212017.3351797-1-arighi@nvidia.com/
- v1 补丁（线程根）: https://lore.kernel.org/all/20260926152306.3190774-1-arighi@nvidia.com/
- Tejun 对 v2 的 review: https://lore.kernel.org/all/134cbadbf6412d22d6bf34686f7cb422@kernel.org/
- Tejun 对 v1 的 review: https://lore.kernel.org/all/23db458c1526966f521d41322ab47056@kernel.org/

---
id: sched-20260927-001
date: 2026-09-27
subject: "sched_ext: cid: Represent clusters explicitly"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260926152306.3190774-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20260927133719.3458770-1-arighi@nvidia.com/"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Tejun Heo"
current_version: v3
patch_series:
  - version: v1
    msgid: "<20260926152306.3190774-1-arighi@nvidia.com>"
    date: 2026-09-26
    summary: "首发：按 cluster 枚举核新增 cluster_cid/cluster_idx；无 cluster 时 cluster_cid 取 LLC 自身、cluster_idx 置 -1、退化为单核 cluster。"
    review_outcome: "无回帖（当日）。"
  - version: v2
    msgid: "<20260926212017.3351797-1-arighi@nvidia.com>"
    date: 2026-09-27
    summary: "fallback 改为「无独立 cluster 层级的 core 自成 cluster，cluster_cid = core_cid、cluster_idx 稠密」，基于 size 参数修复重发。"
    review_outcome: "Tejun 回复：fallback 反转硬件覆盖（L2 宽于 core 的部件每 core 自成 cluster），建议改 inclusive mask。"
  - version: v3
    msgid: "<20260927133719.3458770-1-arighi@nvidia.com>"
    date: 2026-09-27
    summary: "改用 inclusive mask（core 无更宽 cluster 自成一个、LLC 宽 L2 合成一个 cluster），更新 kerneldoc/注释，说明 shard 可能切分 cluster；遍历改 cluster 顺序。"
    review_outcome: "尚未收到 Tejun 对 v3 的审阅。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "v3 尚未过 Tejun 审阅"
    - "subject 命名（是否采用 'Add the cluster level to the cid topology'）未定"
    - "CONFIG_SCHED_CLUSTER=n 与非 x86 平台边界行为需覆盖"
  next_action: "等 Tejun 审阅 v3 的 inclusive mask 实现，确认后进 sched_ext/for-7.4"
contribution_opportunities:
  - kind: review
    description: "核查 v3 inclusive mask 在私有 L2/模块级 L2/LLC 宽 L2 三类部件下是否与 SD_CLUSTER 丢域规则一致，尤其是 CONFIG_SCHED_CLUSTER=n 时"
  - kind: testing
    description: "在 AMD 混合或非 x86 平台验证 scx_bpf_cid_topo() 的 cluster_cid/cluster_idx 输出与 fallback/稠密索引行为"
generated_at: "2026-09-28T09:00:00"
source_email_count: 6
related_articles:
  - sched-20260926-005
tags:
  - sched_ext
  - topology
---