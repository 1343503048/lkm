# sched/numa: Apply remote socket distance averaging for Hygon CPUs

# sched/numa: Hygon 平台远程 socket 距离修正（v2）

## 摘要

Guo Chaohong（Hygon/海光）的系列推进到 **v2**：修正 Hygon（海光，基于 AMD Zen 同源）平台上 **NUMA 远程 socket 距离（distance）的误报**，该误报影响 `sched/numa` 的 task 放置与 `load_balance` 的跨节点偏好判断。

要点：
- **v2 变化**：根据 Prateek（AMD）的 review，把平台距离判断从「硬编码 Hygon 厂商」改成基于 ACPI SLIT 表的实际 distance 读取，避免对非 Hygon 平台误伤；Peter 要求把「distance 修正」做成通用 helper（按 SLIT 归一化），而非 Hygon-only 特例。
- 问题背景：Hygon 多 socket 平台在某些 BIOS/ACPI 配置下，`node_distance()` 返回的远程 socket 距离与真实内存访问延迟不匹配（偏大或偏小），导致 NUMA 平衡把任务放在更远的节点，或 `load_balance` 跨节点迁移决策失真，性能退化。
- v2 还修正了 `sched_init_numa()` 里基于 distance 的 `sched_domains` 层级构建，使其与真实 SLIT 一致。

## 技术细节

v2 思路（示意）：
```
// 不再硬编码厂商，改用 SLIT 实际 distance
if (acpi_table_present("SLIT"))
    dist = acpi_node_distance(a, b);
else
    dist = default_distance(a, b);
normalize_numa_distance(dist);   // 通用 helper，Peter 要求
```

Prateek 的反馈：需确认不会让其他 AMD/Zen 平台（同样 distance 表）行为变化；建议加一个 per-platform 的 distance 覆盖表而非全局改写。

## 影响与风险

- 影响面：Hygon 多 socket 平台的 NUMA 任务放置与跨节点 load_balance；其他平台若 distance 表异常也可能受益（但需谨慎）。
- 风险：中。NUMA 距离改动直接影响任务布局，误改会全局退化；需保证只修正「误报」而非覆盖所有平台。
- 收益：使 Hygon 平台 NUMA 平衡基于真实内存延迟，改善跨 socket 任务放置与性能。

## 评价

方向合理（修正真实平台 distance 误报），reviewer（Prateek/Peter）已要求「通用化 + 基于 SLIT + 避免误伤其他平台」。合入可能性中等，建议落实 Peter 的通用 helper 与 Prateek 的 per-platform 覆盖表后再推进。属 fix，仍处 review。

---
subject: "sched/numa: Apply remote socket distance averaging for Hygon CPUs"
id: sched-20260806-014
date: "2026-08-06"
title: "sched/numa: Hygon 平台远程 socket 距离修正（v2）"
series: "sched/numa: Fix remote socket distance on Hygon platforms"
type: fix
status: under_review
severity: medium
merge_likelihood: medium
tags: [cfs, numa, load_balance]
authors: ["Guo Chaohong <guochohong@hygon.cn>", "Zhan Xusheng <xusheng.zhan@hygon.cn>", "K Prateek Nayak <kprateeknayak@amd.com>", "Peter Zijlstra <peterz@infradead.org>"]
reviewers: ["K Prateek Nayak <kprateeknayak@amd.com>", "Peter Zijlstra <peterz@infradead.org>"]
related_articles: []
emails: ["uid-23502@qq-imap", "uid-23783@qq-imap", "uid-23676@qq-imap"]
---
