---
id: sched-20260801-008
date: 2026-08-01
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <uid-13985@qq-imap>
lore_url: unknown
authors:
- Aaron Tomlin
maintainers_involved:
- Namhyung Kim
current_version: v5
patch_series:
- version: v5
  msgid: <uid-13985@qq-imap>
  date: 2026-07-30
  summary: 3 个 patch：1/3 让 perf_sched__read_events() 在 perf_session__has_traces()
    为假时提前返回错误码，避免在缺少 tracepoint 样本的 perf.data 上渲染空的 latency 表格；同时补上 pipe 模式所需的 .attr/.tracing_data/.build_id/.feature
    回调与动态 tracepoint handler 绑定。2/3 为 latency 与 runtime 输出列引入 ns/us/ms/s 自动单位换算，并精简列标题
  review_outcome: Namhyung Kim 要求把 1/3 中的 pipe 模式改动拆成独立 commit、把 thread__get_runtime()
    的 NULL 校验 squash 进去；对 2/3 要求补充改动前后的示例输出对比
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v5 1/3 需要按 maintainer 要求拆分为『修复空表格输出』与『支持 pipe 模式』两个 commit
  - v5 2/3 需要补充用户可见输出的前后对比示例
  next_action: 发 v6：拆分 1/3 的 pipe 模式改动、squash NULL 校验、并为 2/3 附上 before/after 输出示例
contribution_opportunities:
- kind: testing
  description: 用 pipe 模式（perf sched record | perf sched latency）与缺少 -R 的 perf.data
    两种输入验证修复效果，并把 before/after 输出贴到 thread——这正是 Namhyung 明确要求但作者尚未提供的材料
- kind: review
  description: 核对 2/3 的自动单位换算在跨量级边界（999ns / 1000ns、999us / 1ms）上的列宽对齐是否仍然正确，避免表格错位
generated_at: '2026-08-02T00:55:00'
source_email_count: 3
related_articles:
- sched-20260731-009
tags:
- sched_debug
- perf
title: 'perf sched: Suppress latency table output when trace samples are missing'
layout: article
---

## TL;DR

Aaron Tomlin 的 `perf sched latency` 输出改进系列走到 v5：修掉在无 tracepoint 样本时仍打印空表格的问题，并为延迟/运行时数值加上自动单位换算。Namhyung Kim 给出的都是可操作的形式性意见（拆 commit、补示例输出），方向已获认可，v6 应能收敛。

## 背景与问题

**1/3 解决的问题**：在一个缺少 tracepoint 样本的 `perf.data` 上执行 `perf sched latency`（例如录制时没加 `-R`，或文件里只有非 tracepoint 事件），`perf_session__has_traces()` 会正确地打印一条错误信息——但 `perf_sched__read_events()` 随后**继续往下走并返回 0（成功）**。于是 `perf_sched__lat()` 等调用方以为事件处理成功，接着渲染出一整套空的 latency 表头和汇总统计。用户看到的是「一条错误信息 + 一张看起来正常但全是空/零的表」，具有相当的误导性。

pipe 模式下情况更复杂：事件属性是在处理过程中动态收到的，`session->evlist` 在 `perf_session__process_events()` 之前根本没被填充，因此不能在处理前做 trace 检查。

**2/3 解决的问题**：`perf sched latency` 的 runtime 与 delay 值**只以毫秒显示**。延迟很小（微秒、纳秒级）或异常大（秒级）时，输出可读性都很差——前者退化成一串 0.00x，后者是一个巨大的数字。

## 技术方案

**1/3**：让 `perf_sched__read_events()` 在 `perf_session__has_traces()` 为假时提前返回合适的错误码，而不是 fall through 返回 0。为了同时支持 pipe 输入，做了三件配套工作：在 `cmd_sched()` 中注册缺失的 `.attr`、`.tracing_data`、`.build_id`、`.feature` 回调；把 handlers 数组提升为文件作用域的 `latency_handlers[]`，并在 `perf_sched__process_tracepoint_sample()` 中当 `evsel->handler` 为 NULL 时动态调用 `evlist__set_tracepoints_handlers()`；对 pipe 数据把 trace 检查改为**后置**（处理完再检查）。此外顺带在 `map_switch_event()` 中对 `thread__get_runtime()` 做 NULL 校验，防止空指针解引用。

**2/3**：引入 `scnprintf_latency_unit()`，按数值大小自动选择单位：

```c
if (nsecs < 1000)            return scnprintf(buf, size, "%6" PRIu64 " ns", nsecs);
if (nsecs < NSEC_PER_MSEC)   return scnprintf(buf, size, "%6.3f us", (double)nsecs / NSEC_PER_USEC);
if (nsecs < NSEC_PER_SEC)    return scnprintf(buf, size, "%6.3f ms", (double)nsecs / NSEC_PER_MSEC);
...
```

统一 `%6` 宽度以保持列对齐；列标题从 "Runtime ms" / "Avg delay ms" / "Max delay ms" 改为 "Runtime" / "Avg delay" / "Max delay"（单位已在每个数值上），并调整间距、去掉每行格式串中冗余的前缀。改动集中在 `tools/perf/builtin-sched.c`，2/3 为 30 增 12 删。

## 版本演进与当前进展

系列已迭代到 **v5**（2026-07-30 发出），当日（08-01 05:59 / 06:03）收到 Namhyung Kim 对 1/3 和 2/3 的 review。作者 Aaron Tomlin 在 06:03 有回复动作。v6 尚未发出。

前四个版本的具体演进内容不在本次采样范围内。本系列在 07-31 日报中已作为 v5 记录过（见 related_articles），本文为 08-01 收到 maintainer review 后的进展更新。

## Maintainer 意见与讨论焦点

**Namhyung Kim**（perf 工具 maintainer）给出了三条明确意见，全部是形式与呈现层面的，没有质疑任何技术方向：

1. **对 1/3**：「Can you please split the pipe mode changes into a separate commit?」——修复「空表格」与「支持 pipe 模式」是两件事，应当拆成两个 commit。这是合理的要求：前者是 bug 修复（可能需要 backport），后者是功能增强，混在一起不利于回溯。
2. **对 1/3**：`thread__get_runtime()` 的 NULL 校验「small enough to be squashed」——太小了，直接并进去即可，不必单列。
3. **对 2/3**：「It'd be nice if you could include example output when you touched user-visible area. Comparing before and after would be great.」——改动了用户可见区域就应该在 commit message 里附上前后对比输出。

**没有争议点，没有 NAK，没有技术方向上的分歧**。三条意见都是「怎么组织提交」而非「该不该这么做」，这是一个方向已被接受、只差最后打磨的系列。

## 合入评估

合入可能性 **high**。判断依据：

- maintainer 本人已经在 review 并给出建设性意见，没有质疑动机或实现；
- 两条意见（拆 commit、squash 小改动）是纯机械操作，第三条（补示例输出）只需跑一遍命令粘贴结果；
- 改动完全局限在 `tools/perf/builtin-sched.c`，不触碰内核代码，风险低；
- 修复的是明确的用户可见问题（误导性的空表格）。

当前阻塞项就是那两件待办：拆分 1/3 的 pipe 模式改动、为 2/3 补 before/after 示例。作者发出 v6 后大概率可以合入。

## 效果评估

**暂无量化效果数据**，但这类工具输出改进本身也不需要 benchmark。

需要指出的是：v5 的 2/3 恰恰**缺少 maintainer 明确要求的那种"效果展示"**——改动前后的实际输出对比。这不是性能数据，而是可读性改进的直接证据。Namhyung 的意见本质上就是在说「你声称输出变好读了，但没让人看到」。这个空白正是 v6 需要补上的。

## 我可以参与的点

- **测试（直接对应 maintainer 的未满足要求）**：用两种输入验证修复——（a）不加 `-R` 录制的 `perf.data`，确认修复后不再打印空表格而是干净退出；（b）pipe 模式 `perf sched record | perf sched latency`，确认 handler 动态绑定与后置 trace 检查工作正常。同时截取 2/3 改动前后的 latency 表格输出贴到 thread。**Namhyung 明确要求了 before/after 示例而作者尚未提供，这是眼下最直接的贡献点。**
- **Review**：核对 2/3 的自动单位换算在跨量级边界上的列宽表现——`999 ns` 与 `1.000 us`、`999.999 us` 与 `1.000 ms` 这些相邻值使用不同格式串（`%6 PRIu64` 整数 vs `%6.3f` 浮点），需要确认加上单位后缀后各列在混合量级的表格中仍然对齐，不会出现错位。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
