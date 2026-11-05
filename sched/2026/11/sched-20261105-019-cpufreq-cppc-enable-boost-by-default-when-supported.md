# cpufreq: CPPC: Enable boost by default when supported

## TL;DR

Pengjie Zhang 的 v2 想让 CPPC cpufreq 驱动在平台支持 boost 时默认启用全局 boost（而非默认关闭）。今日讨论焦点落在「全局 boost 文件的语义」：Loehle 指出全局 boost=1 只是「允许 boost 的许可」而非「boost 被支持」，并顺带发现 power-orion-o6 上全局 boost 文件读写自相矛盾（写 1/0 都 -EINVAL）的另一个 bug；Pengjie 请 Viresh/Rafael 定夺是保留 boot 扫描还是静态置 `boost_enabled=true`；Rafael 表示无具体倾向但要求「各驱动与核心语义一致」。

## 背景与问题

CPPC 平台的全局 boost 默认是关闭的，即便平台支持 boost。作者希望默认启用，让支持 boost 的平台开箱即用。争议在于全局 `boost` sysfs 的语义：文档（Documentation/admin-guide/pm/cpufreq.rst）规定 1 只是「允许使用 boost 机制（可能因其它原因仍不生效）」的许可，0 表示「完全禁用」，而「平台是否支持 boost」是另一回事——默认 1 是否会误导用户、与 per-policy boost 的状态如何协调需要理清。

## 技术方案

v2 的做法是：boot 时扫描平台是否支持 boost，支持则置全局 boost=1。今日讨论给出两个待选项：保留 boot 扫描（不支持 boost 的平台保持 0），或干脆静态 `boost_enabled = true`。

## 版本演进与当前进展

*current_version: v2（2026-10-22 发出，今日讨论）*。今日 Loehle、Pengjie、Rafael 三方讨论语义与实现取向，无新版本。

## Maintainer 意见与讨论焦点

- **Rafael J. Wysocki（cpufreq 维护者）**：对 boost 支持无具体倾向，但明确要求「各驱动与核心的 boost 语义保持一致」——这是对本补丁的软约束，倾向先统一语义再谈默认值。
- **Christian Loehle（ARM）**：指出 amd-pstate 已能全局 boost=1 而 per-policy 读 0，语义已不自洽；另发现 power-orion-o6 上全局 boost 文件读 0、写 1 或 0 都 -EINVAL、再读却变 1 的 bug，表示自己会去修。
- **Pengjie Zhang**：请 Viresh/Rafael 就「保留 boot 扫描 vs 静态置位」拍板。

## 合入评估

*likelihood=medium*。维护者未反对但要求先统一跨驱动语义；实现取向（boot 扫描 vs 静态）未定。*blocking_issues*：① 全局 boost 语义需与 amd-pstate 等驱动对齐；② boot 扫描 vs 静态置位未定。*next_action*：待 Rafael/Viresh 就语义与实现取向表态，作者据此改版。

## 效果评估

无性能数据；这是默认行为与控制面语义的改动。

## 我可以参与的点

- discussion：梳理各驱动（amd-pstate/intel_pstate/CPPC）全局 boost 语义差异，帮维护者形成「一致语义」的具体建议。
- review：核对 boot 扫描与静态置位在「不支持 boost 平台」下的行为差异。

## 参考链接

- lore thread（v2 补丁）: https://lore.kernel.org/all/20261022075901.3436021-1-zhangpengjie2@huawei.com/
- Rafael 的表态: https://lore.kernel.org/all/CAJZ5v0j1YpOu9SnjAF4VFVOVFEr6bLzRWaqCJ3jmFP4-01s1LQ@mail.gmail.com/

---
id: sched-20261105-019
date: 2026-11-05
subject: "cpufreq: CPPC: Enable boost by default when supported"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261022075901.3436021-1-zhangpengjie2@huawei.com>"
lore_url: "https://lore.kernel.org/all/20261022075901.3436021-1-zhangpengjie2@huawei.com/"
authors: [Pengjie Zhang]
maintainers_involved: [Rafael J. Wysocki]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261022075901.3436021-1-zhangpengjie2@huawei.com>"
    date: 2026-10-22
    summary: "支持 boost 的 CPPC 平台默认启用全局 boost。"
    review_outcome: "Rafael 要求跨驱动语义一致；Loehle 指出语义不自洽并另报 boost 文件 bug。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "全局 boost 语义需与 amd-pstate 等驱动对齐"
    - "boot 扫描 vs 静态置位未定"
  next_action: "待 Rafael/Viresh 就语义与实现取向表态"
contribution_opportunities:
  - kind: discussion
    description: "梳理各驱动全局 boost 语义差异，形成一致语义建议"
  - kind: review
    description: "核对 boot 扫描与静态置位在无 boost 平台的行为差异"
generated_at: "2026-11-06T09:00:00+08:00"
source_email_count: 3
related_articles: []
tags: [cpufreq]
---