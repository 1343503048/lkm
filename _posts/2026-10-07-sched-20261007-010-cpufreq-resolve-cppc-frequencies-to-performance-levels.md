---
id: sched-20261007-010
date: '2026-10-07'
subject: 'cpufreq: Resolve CPPC frequencies to performance levels'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260929102957.2591657-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved:
- Jeremy Linton
- Vanshidhar Konda
current_version: v1
patch_series:
- version: v1
  msgid: <20260929102957.2591657-1-christian.loehle@arm.com>
  date: '2026-09-29'
  summary: resolve_freq 回调 + CPPC 仿射预计算 + 冗余回调跳过，3 补丁
  review_outcome: Mario R-b + Peter No objection 在前；Zhongqiu 实现层三点、Jeremy/Vanshidhar
    前提级 spec 质疑在后，作者零回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 前提级 spec 质疑（Optional/信息性字段用于控制决策）未回应
  - 作者对全部 review 零回复
  next_action: 作者回答字段定位问题或重设计（控制留在 perf 空间）
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: discussion
  detail: 实证 Jeremy 的极值状态舍入追问
- kind: review
  detail: 梳理主线既有 freq 字段控制面使用，为双方论据补位
source_email_count: 2
related_articles:
- sched-20260929-010
- sched-20261001-006
- sched-20261002-005
tags:
- cpufreq
- cppc
title: 'cpufreq: Resolve CPPC frequencies to performance levels'
layout: article
---

> **subject**：`cpufreq: Resolve CPPC frequencies to performance levels`
> 本文为增量更新，完整脉络见下。

## TL;DR

- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-010-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20260929-010</a>：Christian Loehle 的 3 补丁系列——table-less 的 cppc-cpufreq 缺少「频率→性能级」解析，不同 kHz 请求 miss schedutil 频率缓存却写同一个 Desired Performance 值；新增 `->resolve_freq()` 回调、CPPC 预计算仿射转换、schedutil limits 未变时跳过冗余回调。实测 schbench mean p99 降 10%、`cppc_set_perf()` 调用降 23.8%。
- <a class="article-ref" href="/lkm/2026/10/01/sched-20261001-006-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261001-006</a>：Mario Limonciello 给整系列 `Reviewed-by`；Peter Zijlstra 对 kernel/sched/ 部分「No objection」，预期走 cpufreq 维护者通道。
- <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-005-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261002-005</a>：Qualcomm 的 Zhongqiu Han 加入评审——1/3 直接 `Reviewed-by`；2/3 指出两套 perf↔kHz 转换并存（最多差 999 kHz）且 `cppc_cpufreq_perf_limits()` 混用；3/3 指出 1 字节 `xchg()` 在 sparc 等架构不支持。作者当日未回复。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-010-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261007-010</a>（今天，含 10-06 未成文的评审）：**ARM 生态两位评审对系列前提发起 spec 级质疑**——Jeremy Linton（ARM，10-06）指出 cppc_cpufreq 因此更重地依赖 lowest_freq/nominal_freq 做**控制决策**，而 ACPI 把这些字段定位为「reporting aids rather than control inputs」，CPPC perf 才是抽象控制空间、可能编码频率之外的平台行为，长期应远离这种频率合成；Vanshidhar Konda（Ampere，10-07）补充这些字段在 spec 里标 **Optional**，并引 ACPI 6.6 Table 8-23 原文「not for functional decisions or platform communication」。Jeremy 另建议把 `cppc_khz_to_perf()` 从 cppc_acpi.c 挪进本模块、用 perf map 的逆运算保留舍入语义，并问舍入是否可能让 HW 永远到不了固件给的 highest/lowest 状态。**作者（同为 ARM）对两轮质疑均未回复**。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-010-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20260929-010</a> → <a class="article-ref" href="/lkm/2026/10/02/sched-20261002-005-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261002-005</a>）系列的收益建立在「用 lowest_freq/nominal_freq 做仿射预计算」之上；Zhongqiu 的 10-02 意见是**实现层**不一致（两套转换、xchg 原语），而 10-06/10-07 两轮意见打在**前提层**：ACPI 6.6 对 Nominal Frequency 的定义是「Optional……只应用于以绝对频率报告处理器性能，不用于功能决策或平台通信」——系列恰恰在用它做功能决策（解析控制用的频率）。若该立场成立，正确方向是把控制决策留在 CPPC 抽象 perf 空间、只在报告侧换算频率，系列需要重新设计而非修补。

## 技术方案

（承接系列三补丁框架）今天的讨论不新增代码，给出两个替代/修正方向：

1. **Jeremy 的结构建议**：`cppc_khz_to_perf()` 的所有 caller 都在本模块——把实现从 `cppc_acpi.c` 挪过来，用 `cppc_cpufreq_init_perf_map()` 生成 map 后按逆运算 `perf = (freq − map->offset) * map.div / map.mul` 计算，可保留现有舍入语义（若理解无误）。
2. **Jeremy 的边界追问**：不直接取 `min_perf = caps->lowest_perf`、`max_perf = nominal/highest` 的实际后果是什么——舍入是否可能让 HW 永远收不到固件提供的最高/最低状态指令？
3. **Vanshidhar 的 spec 依据**：lowest/nominal frequency 字段标 Optional（ACPI 6.6 Table 8-23），拿 Optional 字段做控制决策意味着部分平台根本不提供这些值，系列在该类平台上的行为需要澄清。

## 版本演进与当前进展

- v1（09-29，3 补丁，<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-010-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20260929-010</a>）→ 10-01 Mario 全系列 R-b + Peter「No objection」（<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-006-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261001-006</a>）→ 10-02 Zhongqiu 三点（<a class="article-ref" href="/lkm/2026/10/02/sched-20261002-005-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261002-005</a>）。
- 10-06：Jeremy Linton 的前提级 review（`<fcfc5d26-b3ec-47dc-9d17-0e4c1d9a36ae@arm.com>`，当日未单独成文）。
- 10-07：Vanshidhar Konda 补 spec 引文并表态「additional concerns」（`<20261006-electric-ibex-of-beauty-5aadbf-vanshikonda@os.amperecomputing.com>`）。
- **作者 Christian Loehle 对 10-02 以来的全部质疑零回复**；无 v2。

## Maintainer 意见与讨论焦点

- **Jeremy Linton**（ARM）：前提级质疑（控制 vs 报告的字段定位）+ 结构建议（挪函数、逆运算）+ 边界追问（舍入是否挡住 HW 极值状态）。
- **Vanshidhar Konda**（Ampere）：spec 级佐证（Optional 字段 + 原文引用），与 Jeremy 形成同向双重压力。
- 焦点从「转换算得对不对」（Zhongqiu）升级为「该不该用这些字段做控制」（Jeremy/Vanshidhar）。Mario 的 R-b 与 Peter 的 No objection 都在这些意见**之前**给出，是否被撤回/重议待观察。Rafael/Viresh（cpufreq 通道）仍零表态。

## 合入评估

*likelihood=low*（从 medium 下调）。系列前提（用 freq 字段做控制决策）被两位 ARM 生态评审以 ACPI spec 原文质疑，且作者持续沉默；即便实现层的 Zhongqiu 三点全修，前提不动摇也难获收取。*blocking_issues*：前提级质疑未回应；作者对全部 review 零回复。*next_action*：Christian 必须先回答「为什么可以用 Optional/信息性字段做控制」或改走「控制留在 perf 空间、报告侧换算」的重设计；否则系列大概率搁置。

## 效果评估

原有效果数据（schbench mean p99 −10%、`cppc_set_perf()` −23.8%）依然成立，但前提动摇后其「收益归属」存疑——同样的冗余调用削减或许能在不依赖 freq 字段的方案下实现。今日无新数据。

## 我可以参与的点

- `discussion`： Jeremy 的边界追问是可实证的——构造「请求固件 lowest/highest 对应频率」的场景，测舍入路径是否真的挡住 HW 极值状态指令，给质疑/辩护双方一个数据点。
- `review`：核对主线 cppc-cpufreq 现状里 lowest_freq/nominal_freq 已有的使用面（`amd_pstate` 走 quirk、cppc-cpufreq 走 nominal_khz）——若既有代码已在控制路径用这些字段，可作为「系列只是延续现状」的反驳论据替作者补位。
- 回合视角：系列未定稿，不适用。

## 参考链接

- Vanshidhar 的 spec 质疑: https://lore.kernel.org/all/20261006-electric-ibex-of-beauty-5aadbf-vanshikonda@os.amperecomputing.com/
- Jeremy 的前提级 review（10-06）: https://lore.kernel.org/all/fcfc5d26-b3ec-47dc-9d17-0e4c1d9a36ae@arm.com/
- 系列补丁: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/
- ACPI 6.6 Table 8-23: https://uefi.org/specs/ACPI/6.6/08_Processor_Configuration_and_Control.html#continuous-performance-control-package-values
- 相关文章：<a class="article-ref" href="/lkm/2026/09/29/sched-20260929-010-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20260929-010</a>（v1）、<a class="article-ref" href="/lkm/2026/10/01/sched-20261001-006-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261001-006</a>（R-b）、<a class="article-ref" href="/lkm/2026/10/02/sched-20261002-005-cpufreq-resolve-cppc-frequencies-to-performance-levels.html">sched-20261002-005</a>（Zhongqiu 三点）
