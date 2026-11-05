# cpufreq: tegra194: add Tegra264 support

## TL;DR

Sumit Gupta 的 9 补丁系列给 tegra194-cpufreq 驱动加入 Tegra264 支持。Tegra264 延续「BPMP 提供 NDIV 上限、驱动从 core clock + 参考计数器推导当前频率」的既有模型，但频率读取改走 64 位 AMU 计数器、频率请求改走 MMIO（CCPLEX 的 core_freq_req 寄存器，每个寄存器对应一个两核 cluster）。纯驱动侧新增 SoC 支持，刚发出、暂无评审。

## 背景与问题

tegra194-cpufreq 现支持 Tegra194/234 等 SoC，需要新增 Tegra264。Tegra264 的频率读取走系统寄存器（64 位 AMU 计数器，参考计数器按 CNTFRQ 频率走），频率请求走 MMIO（像 Tegra234），每个 core_freq_req 寄存器控制一个由两个单 CPU cluster 共享的 cluster-clock 单元，因此两个 CPU 组成一个 cpufreq policy。

## 技术方案

9 补丁分四组：1 个修复（patch 1，读 MPIDR 挪到 CPU hotplug 回调）、对计数器采样循环去重（patch 2）、per-SoC 计数器 mask（patch 4）、MMIO mapping 从 ACTMON offset 拆出（patch 5）、从设备树推导频率域（patch 7）、以及 Tegra264 支持主体（patch 8）。

## 版本演进与当前进展

*current_version: v1（2026-11-04 发出）*。刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无任何回复，本日无讨论。

## 合入评估

*likelihood=unknown*。刚发出的驱动侧新增 SoC 支持，无评审信号。*blocking_issues*：暂无（等待评审）。*next_action*：等 cpufreq 子系统维护者（Viresh/Rafael）评审；可关注 patch 1 的「MPIDR 读取挪到 hotplug 回调」是否与驱动现行初始化时序一致。

## 效果评估

无性能数据（新 SoC 使能）。

## 我可以参与的点

- review：核对频率推导（AMU 参考计数器 vs core clock）与 MMIO 请求路径的簇共享语义是否正确。
- testing：在有 Tegra264 的板子上验证 cpufreq 变频、policy 成对性。

## 参考链接

- lore thread（系列 cover）: https://lore.kernel.org/all/20261104181521.3003578-1-sumitg@nvidia.com/

---
id: sched-20261105-021
date: 2026-11-05
subject: "cpufreq: tegra194: add Tegra264 support"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261104181521.3003578-1-sumitg@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261104181521.3003578-1-sumitg@nvidia.com/"
authors: [Sumit Gupta]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261104181521.3003578-1-sumitg@nvidia.com>"
    date: 2026-11-04
    summary: "9 补丁：为 tegra194-cpufreq 加 Tegra264 支持（AMU 读频 + MMIO 请求）。"
    review_outcome: "刚发出，暂无 review。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等 cpufreq 维护者评审"
contribution_opportunities:
  - kind: review
    description: "核对 AMU 参考计数器 vs core clock 的推导与簇共享语义"
  - kind: testing
    description: "在 Tegra264 板验证变频与 policy 成对性"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 9
related_articles: []
tags: [cpufreq]
---