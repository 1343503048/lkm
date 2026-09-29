# sched: Enable preferred SMT siblings on NVIDIA Olympus

> **subject**：`sched: Enable preferred SMT siblings on NVIDIA Olympus`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260921-004：Andrea Righi 的「在 NVIDIA Olympus 上启用优先 SMT 兄弟」系列（v6）获 Breno Leitao 完整 Tested-by 与 Dietmar Eggemann 对 Spatial SMT 收益机制的追问。
- sched-20260929-019（今天）：Andrea 逐条回复 Dietmar——POWER7 已通过处理器版本寄存器在 SMT 域自设 `SD_ASYM_PACKING`、无需 boot 选项；boot 选项只服务固件不描述 sibling 偏好的 Olympus；并补充 88 线程 benchmark 的负载模型（NVPL 约 2.6K 中断睡眠/唤醒 + 3K futex wait，GEMM OpenBLAS 仅约 250），解释了为何 NVPL 收益更大。

## 背景与问题

（承接 sched-20260921-004）NVIDIA 的 Spatial SMT 会动态把物理核切分为两个「兄弟」逻辑核，传统 `sched_smt_asym_packing` 语义不适用，需要在 idle 选择路径上优先选择低编号（PE0）兄弟，让 PE0 保持全资源单线程模式、PE1 空闲。今天无新代码，进展是作者对 Dietmar 此前追问的逐条澄清。

## 技术方案

（承接）本日无新代码，Andrea 的回复进一步厘清方案的适用边界：POWER7 已通过处理器版本寄存器识别并自行在 SMT 域设置 `SD_ASYM_PACKING`、不需要 boot 选项；boot 选项仅针对固件当前不描述 sibling 偏好的 Olympus 这类平台。传统对称 SMT（siblings 对称、无架构定义优先级）不预期开启该选项有任何收益。

## 版本演进与当前进展

- 系列 v6（09-17，thread root `<20260917140707.3807229-1-arighi@nvidia.com>`）。
- 09-29：Andrea 回复 Dietmar（`<aruvoVH59aZ4vL1Y@gpd4>`），逐条回答 POWER7 机制、boot 选项范围、SMT 收益前提、benchmark 负载模型与睡眠/唤醒模式。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（作者）：澄清 POWER7 无需 boot 选项（自身设 `SD_ASYM_PACKING`）；Olympus 上低编号逻辑兄弟即 PE0，持续优先它能降低两个 PE 的激活、让 PE0 保持全资源模式；并给出 benchmark 细节——两个 benchmark 都用 88 线程跑满 88 物理核、两 sibling 均可选；per-thread 调度 trace + perf 计数显示 PE 优先化使放置偏向 PE0、ST/SMT 模式切换一致下降（早前五轮对比 ST/SMT 切换下降约 ~80%）；NVPL 跑出约 2.6K 中断睡眠/唤醒 + 3K futex wait，GEMM OpenBLAS 仅约 250 睡眠/唤醒 + futex wait，反复唤醒给了调度器更多选择 sibling 的机会，故 NVPL 收益更大。
- **Dietmar Eggemann**（ARM 调度维护者，前一日）：此前追问 88 线程 benchmark 负载模型与 Spatial SMT 收益机制。今日得到作者的详细回复。
- 无 NAK；讨论进入「机制解释与数据补强」阶段，still 缺的是新的吞吐量化对比。

## 合入评估

*likelihood=medium*。功能正确性已有独立平台 Tested-by，作者也对 Dietmar 的机制/负载模型追问做了详实澄清；仍缺**新一版吞吐量化数据**（此前 Breno 未测、Dietmar 追问的正是这一点）。*blocking_issues*：缺少 throughput 对比数据。*next_action*：作者补充 Olympus 上的吞吐对比数字，进一步坐实 Spatial SMT 收益的普适性。

## 效果评估

功能层面：唤醒重定向 800/800 命中（vs 基线 13/800）、ST/SMT 切换下降 ~80%；作者给出负载模型的睡眠/唤醒计数（NVPL ~2.6K/3K vs GEMM ~250），但吞吐提升的具体数字仍未给出。

## 我可以参与的点

- `testing`：在 NVIDIA Spatial SMT 或任何具备非对称 SMT 优先级的平台上补测吞吐/延迟对比并回帖，这是当前最缺的一块。
- `review`：围绕作者给出的负载模型（反复唤醒 → 更多 sibling 选择机会）分析 Spatial SMT 收益的适用范围与潜在反例。

## 参考链接

- lore（thread root）: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/
- lore（Andrea 回复）: https://lore.kernel.org/all/aruvoVH59aZ4vL1Y@gpd4/

---
id: sched-20260929-019
date: '2026-09-29'
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260917140707.3807229-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/aruvoVH59aZ4vL1Y@gpd4/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Dietmar Eggemann'
current_version: v6
patch_series:
  - version: v6
    msgid: '<20260917140707.3807229-1-arighi@nvidia.com>'
    date: '2026-09-17'
    summary: 'v6 封面：Enable preferred SMT siblings；patch 1/2 为 Honor asymmetric SMT priority in idle selection'
    review_outcome: 'Breno Tested-by；Dietmar 追问吞吐与负载模型；09-29 Andrea 逐条澄清机制与 benchmark 细节'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '仍缺新一版吞吐量化对比数据'
  next_action: '作者补充 Olympus 上的吞吐对比数字，坐实 Spatial SMT 收益普适性'
contribution_opportunities:
  - kind: testing
    description: '在非对称 SMT 优先级平台补测吞吐/延迟对比并回帖（当前最缺吞吐数字）'
  - kind: review
    description: '围绕负载模型分析 Spatial SMT 收益适用范围与潜在反例'
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles:
  - sched-20260921-004
tags:
  - topology
  - idle
  - hyperthreading
---