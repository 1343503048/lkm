---
subject: 'perf sched latency: Refine outputs, unit scaling, and histogram support'
id: sched-20260802-003
date: 2026-08-02
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: unknown
lore_url: unknown
authors:
- Aaron Tomlin
maintainers_involved:
- Namhyung Kim
current_version: v6
patch_series:
- version: v3
  msgid: unknown
  date: 2026-07-29
  summary: 补齐 pipe 模式所需的 .attr / .tracing_data / .build_id 回调；引入 pipe 后处理检查避免空表；给
    map_switch_event() 的 thread__get_runtime() 加 NULL 检查；修正列对齐；把 swapper 排除出 global_hist；把
    --time 过滤下移进 add_sched_in_event() 以保住任务状态机。
  review_outcome: 详细 review 意见推动了 v4 的多项修正。
- version: v4
  msgid: unknown
  date: 2026-07-29
  summary: 补上遗漏的 .feature 回调；复用未完成 work atom 修复内存泄漏；handlers 数组提升为文件作用域 latency_handlers[]
    并在 evsel->handler==NULL 时动态挂接；避免 pipe/非 pipe 模式下 wakeup 重复计数；补齐自动缩放格式串的尾部竖线。
  review_outcome: 仍有输出示例缺失与 patch 拆分粒度问题待解决。
- version: v5
  msgid: unknown
  date: 2026-07-30
  summary: 3 个 patch 的形态，pipe 模式处理与空表抑制仍合并在 Patch 1 中。
  review_outcome: Namhyung Kim 要求：涉及用户可见输出的改动应附 before/after 示例；并要求把 pipe 模式处理拆成独立
    patch。作者 7/31 回复 Acknowledged。
- version: v6
  msgid: <uid-14879@qq-imap>
  date: 2026-08-02
  summary: '按 Namhyung 意见把 pipe 模式 trace sample 处理从 Patch 1 拆为独立 Patch 2（系列由 3 patch
    变 4 patch）；给 pipe 模式 patch 补 Fixes: 27295592c22e；commit log 补充表头格式的 before/after
    图示。'
  review_outcome: v6 当日刚发出，暂无新 review 回帖。
upstream_commit: null
fixes_commit: 27295592c22e
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Namhyung Kim 尚未确认 v6 是否已完全满足 v5 提出的 before/after 示例要求（作者称已在 commit log 补充，但 reviewer
    未复核）。
  - Patch 4 引入 --histogram / --hist-mode / --time 三个新用户接口，接口设计本身尚未获得明确 ack；新增 CLI
    选项通常需要维护者对命名与语义单独把关。
  next_action: 等待 Namhyung Kim 对 v6 的复核；若 Patch 1/2 的 bug 修复部分先获 ack，可能出现前两个 patch
    先合、histogram 功能继续迭代的拆分合入。
contribution_opportunities:
- kind: testing
  description: 在 pipe 模式（perf record -o - | perf sched latency -i -）下验证 Patch 2 的动态
    handler 挂接是否覆盖所有 tracepoint，尤其检查 wakeup 是否仍存在重复计数——这是 v4 修过一次的问题，值得独立复验。
- kind: review
  description: 复核 Patch 3 自动缩放的单位切换阈值与列宽对齐：格式串需与表头逐字符对齐，这类改动极易在极端值（ns 级与 s 级混合）下错位，可构造混合量级数据集验证。
- kind: extend
  description: --hist-mode 目前只支持 log 与 100us 等宽 linear 两种分桶，可提出/实现用户自定义桶宽或百分位输出。
generated_at: '2026-08-03T00:15:00'
source_email_count: 6
related_articles:
- sched-20260731-009
- sched-20260801-008
tags:
- sched_debug
- perf
title: 'perf sched latency: Refine outputs, unit scaling, and histogram support'
layout: article
---

# perf sched latency v6: 输出精修、单位自动缩放与直方图支持

## TL;DR

**本文为增量更新** —— 完整背景见 `related_articles` 中的 `sched-20260731-009` 与 `sched-20260801-008`。v6 的核心变化是响应 Namhyung Kim 的 review：把 pipe 模式处理从 Patch 1 拆出成独立 patch（系列 3→4 个），补上 `Fixes:` 标签，并在 commit log 中加入表头格式的 before/after 图示。作为工具侧改进，合入可能性高。

## 背景与问题

（完整背景见关联文章，此处仅摘要）`perf sched latency` 存在四类问题：

1. **误导性空表**：`perf_session__has_traces()` 因缺少 tracepoint 事件而失败时，`perf_sched__read_events()` 却"贯穿"返回成功（0），导致调用者 `perf_sched__lat()` 以为处理成功，继续渲染出空的表头和全零的汇总统计。
2. **pipe 模式不可用**：pipe 模式下事件属性是在事件处理过程中动态收到的，`session->evlist` 在处理前尚未填充，导致 tracepoint handler 挂不上。
3. **单位固定为 ms**：所有 runtime 与 delay 值一律以毫秒显示，微秒级或秒级延迟都难以阅读。
4. **缺少分布视图**：只有均值/最大值，没有延迟分布。

## 技术方案

四个 patch 分工（v6 形态）：

- **Patch 1 — 抑制空表**：让 `perf_sched__read_events()` 在 `perf_session__has_traces()` 为假时提前中止并返回合适错误码。同时给 `map_switch_event()` 中的 `thread__get_runtime()` 加 NULL 检查以防内存分配失败下的空指针解引用。核心改动是把原来的 `if (has_traces) { ...process... }` 结构翻转为 `if (!has_traces) goto out_delete;` 的早退形式：

  ```c
  -	if (perf_session__has_traces(session, "record -R")) {
  -		int err = perf_session__process_events(session);
  -		...
  -	}
  +	if (!perf_session__has_traces(session, "record -R"))
  +		goto out_delete;
  +
  +	err = perf_session__process_events(session);
  ```

- **Patch 2 — pipe 模式流处理**（v6 新拆出）：在 `cmd_sched()` 中注册 `.attr` / `.tracing_data` / `.build_id` / `.feature` 四个回调以正确解析头部事件；把 handlers 数组提升为文件作用域 `latency_handlers[]`，并在 `perf_sched__process_tracepoint_sample()` 中当 `evsel->handler == NULL` 时动态调用 `evlist__set_tracepoints_handlers()`；pipe 数据的 trace 存在性检查改为后处理阶段执行，非 pipe 文件仍维持前置早退。
- **Patch 3 — 单位自动缩放**：Runtime / Avg delay / Max delay 三列按数值量级动态选择 ns / us / ms / s，表头相应去掉硬编码的 "ms" 后缀，格式符与表头逐字符对齐。
- **Patch 4 — 直方图与时间过滤**：新增 `--histogram`（`-H`）输出 ASCII 条形图、`--hist-mode`（`log` 或 100us 等宽 `linear` 分桶）、`--time`（限定 `[start,stop]` 时间窗）。

**关键设计取舍**：v5→v6 最重要的变化不是功能，而是**拆分粒度**。Namhyung 要求把 pipe 模式处理独立成 patch，本质是把"bug 修复"（Patch 1、2）与"功能增强"（Patch 3、4）在提交粒度上分离，便于前者单独走 urgent 路径、也便于 `Fixes:` 标签精确指向。作者照办并补上了 `Fixes: 27295592c22e`。

## 版本演进与当前进展

这是一个迭代密集的系列，**六天内从 v3 走到 v6**：

| 版本 | 日期 | 关键改动 | review 结果 |
|---|---|---|---|
| v3 | 07-29 | 补 pipe 回调、NULL 检查、列对齐、swapper 排除、`--time` 下移 | 推动 v4 多项修正 |
| v4 | 07-29 | 补 `.feature` 回调、修内存泄漏、handlers 提升为文件作用域、防 wakeup 重复计数 | 仍缺输出示例 |
| v5 | 07-30 | 3-patch 形态 | Namhyung 要求补 before/after 示例 + 拆分 pipe patch |
| **v6** | **08-02** | **拆出 Patch 2、补 Fixes 标签、commit log 加图示** | **待 review** |

v6 的 changelog 明确记录了三条变化，均直接对应 Namhyung 的意见：

> - Split pipe mode trace sample handling from Patch 1 into a standalone patch (Namhyung Kim)
> - Added a Fixes: tag to the pipe mode patch referencing commit 27295592c22e
> - Updated commit log with before and after illustrations of table header formatting

作者也附上了 v5 的 lore 链接：`https://lore.kernel.org/lkml/20260730185416.97166-1-atomlin@atomlin.com/`

## Maintainer 意见与讨论焦点

**Namhyung Kim**（perf 维护者）是本系列唯一活跃的 reviewer，态度是建设性的、逐版推进的，没有出现 NAK。

当日捕获到的关键交互（08-02 05:45，作者回复 Namhyung 07-31 15:01 的意见）：

> **Namhyung**: "It'd be nice if you could include example output when you touched user-visible area. Comparing before and after would be great."
>
> **Aaron**: "Acknowledged—will do."

这条针对的是 v5 的 Patch 2（自动缩放）。v6 的 changelog 声称已"在 commit log 中补充表头格式的 before/after 图示"，但**这属于作者的自我声明，Namhyung 尚未复核确认是否满足要求**。

**尚未被讨论的风险点**（如实标注为空白而非分歧）：

1. **新增 CLI 接口未获明确 ack**。Patch 4 一次引入三个用户可见选项（`--histogram` / `--hist-mode` / `--time`），选项命名、`hist-mode` 只提供 log 与 100us linear 两种固定分桶的设计，都还没有维护者表态。perf 工具的 CLI 接口一旦合入就是长期兼容负担，这类改动通常需要单独把关。
2. **v4 修过的 wakeup 重复计数问题无回归验证**。v4 changelog 提到"避免 pipe 与非 pipe 模式下重复计数 wakeup（即忽略 `sched:sched_wakeup`）"，但后续版本没有人提供验证数据说明该问题确已消除。
3. **v6 拆分后 Patch 1 与 Patch 2 的依赖关系未说明**。既然是从同一个 patch 拆出，两者是否可独立 apply、能否单独回合，邮件未交代。

## 合入评估

合入可能性 **high**：

- 唯一 reviewer 态度积极，每轮意见作者都在下一版落实，节奏健康；
- Patch 1、2 是有 `Fixes:` 标签的实质 bug 修复（空表误导 + pipe 模式失效），价值明确；
- 改动完全局限在 `tools/perf/builtin-sched.c`，不触及内核代码，回归风险低；
- 迭代已进行到 v6，主要架构性意见（拆分、回调补齐、内存泄漏）都已解决。

**但需注意合入形态可能是分批的**：Patch 1、2 作为 bug 修复更容易先获 ack 进 `perf/urgent`，Patch 3、4 尤其是引入新 CLI 的 Patch 4 可能继续迭代。这不是坏消息 —— 恰恰是 v6 拆分带来的好处。

卡点只剩程序性的两条：Namhyung 对 v6 的复核，以及 histogram 接口设计的表态。

## 效果评估

**无任何量化数据，这是本系列的一个客观短板。**

作为工具侧改进，通常的效果论证方式是展示 before/after 输出对比 —— 而这正是 Namhyung 在 v5 明确要求、作者承诺在 v6 补上的内容。截至当日抓取的邮件，v6 封面信中未直接包含输出示例（作者称已放入各 patch 的 commit log）。

可以确认的定性改进：

- 空表问题：改动后 `perf_session__has_traces()` 失败会返回错误码而非 0，行为正确性可从代码直接判定；
- 单位可读性：ns/us/ms/s 自动切换对微秒级延迟的可读性提升是显然的，但**没有实际输出样例佐证列对齐是否在所有量级下都正确**。

作者未提供任何性能开销数据（直方图统计会增加每事件的处理成本），也未见 reviewer 提出此问题。**暂无效果数据支撑，属于设计合理但未经实测的状态。**

## 我可以参与的点

- **pipe 模式实测**（最具体）：跑 `perf record -e 'sched:*' -o - -- workload | perf sched latency -i -`，验证 Patch 2 的动态 handler 挂接是否覆盖全部 tracepoint。重点关注 wakeup 是否仍有重复计数 —— 这是 v4 修过一次的问题，无人复验。若能给出 pipe 与非 pipe 模式下统计数字一致的对比数据，正是这个系列现在最缺的证据。
- **极端量级下的列对齐验证**：构造同时包含 ns 级与 s 级延迟的数据集，检查 Patch 3 的格式串是否与表头逐字符对齐。这类改动在混合量级下最易错位，而作者的测试覆盖情况未知。
- **参与 histogram 接口设计讨论**：`--hist-mode` 目前只有 log 和固定 100us linear 两档。可以提出自定义桶宽、或直接输出 p50/p99 百分位（对 SRE 场景更实用）的建议。接口尚未定型，此时提意见成本最低。
- **后续扩展 patch**：直方图基础设施建立后，扩展到 `perf sched map` 或按 CPU 维度分组统计是自然的下一步。

这是当前几个系列中参与门槛最低、反馈周期最快的一个 —— 纯用户态工具，无需特殊硬件，改动可本地编译验证。

## 参考链接

- lore thread (v5): https://lore.kernel.org/lkml/20260730185416.97166-1-atomlin@atomlin.com/
- lore thread (v4): https://lore.kernel.org/lkml/20260729144451.38286-1-atomlin@atomlin.com/
- lore thread (v6): 未获取到（IMAP 邮件头未暴露原始 Message-ID）
- tip-bot commit: 未获取到
- stable backport: 未获取到
