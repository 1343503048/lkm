---
id: sched-20260804-019
date: 2026-08-04
subsystem: perf
type: feature
status: under_review
severity: none
thread_root_msgid: "<20250730074016.9373-1-renmoluo@oktetlabs.ru>"
lore_url: "https://lore.kernel.org/lkml/20250730074016.9373-1-renmoluo@oktetlabs.ru"
authors: [Artem Savkov, Aaron Tomlin]
maintainers_involved: [Arnaldo Carvalho de Melo, Namhyung Kim]
current_version: v7
patch_series:
  - version: v7
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "perf sched latency v7 仅修正直方图中位数零点偏差。（详见 08-03-010）"
    review_outcome: "08-03-010 已覆盖。"
  - version: v7
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "08-04 上有 review：为什么 global hist 排除 swapper 线程（建议改查 tid==0）；并讨论 --histogram/--time/--CPU 输出细节。仍有小澄清待作者处理。"
    review_outcome: "Aaron Tomlin 等参与 review，提出 swapper 排除逻辑应改查 tid==0 而非 comm 比较；作者待修订。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["swapper 排除逻辑改用 tid==0 的小修订待作者处理"]
  next_action: "等待作者按 review 修订 swapper 排除逻辑后合入（已迭代 7 版，临近）。"
contribution_opportunities:
  - kind: testing
    description: "可验证 v7 直方图排除 swapper 的修正（改用 tid==0）是否正确覆盖所有 idle 统计，回帖 tested-by。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: ["sched-20260803-010-perf-sched-latency-refine-outputs-unit-scaling-histogram-v7"]
tags: [perf, histogram]
---

# perf sched latency: v7 中位数与 swapper 排除

## TL;DR
`perf sched latency` v7（08-03-010）在 08-04 收到 review：global 直方图排除 swapper 线程的方式（比较 comm 字符串）被建议改为检查 `tid==0`；另讨论 `--histogram/--time/--CPU` 输出细节。已 7 版，合入可能性 high，待小修订。

## 背景与问题
`perf sched latency --histogram` 把等待延迟分布到 log/linear 桶并显示 ASCII 柱状图。`--CPU` 可过滤到指定 CPU。原始实现在累计 global histogram 时跳过 `comm == "swapper"` 的线程，但用字符串比较判断 idle 线程不够稳健（comm 可能被截断/重命名）。

## 技术方案
- v7：修正直方图中位数的零点偏差（08-03-010）。
- 08-04 review 建议：把「排除 swapper」改为检查 `thread__tid == 0`（更稳健地识别 idle 线程），而非比较 comm 字符串。

## 版本演进与当前进展
- 08-03：v7 中位数修正（08-03-010）。
- 08-04：Aaron Tomlin 等 review 提出 swapper 排除应改用 tid==0，并讨论输出细节。

## Maintainer 意见与讨论焦点
Aaron Tomlin：指出 swapper 排除用 comm 比较不妥，建议 `tid==0`。属实现稳健性 refine，无方向反对。

## 合入评估
合入可能性 high。纯工具侧打磨，已 7 版，仅剩 swapper 排除的小修订。

## 效果评估
无新 benchmark；属工具正确性与输出细节打磨。

## 我可以参与的点
- 验证 v7 直方图排除 swapper 的修正（改 tid==0）是否覆盖所有 idle 统计场景，回帖 tested-by。

## 参考链接
- 08-03 文章：sched-20260803-010-perf-sched-latency-refine-outputs-unit-scaling-histogram-v7
- v1 根: https://lore.kernel.org/lkml/20250730074016.9373-1-renmoluo@oktetlabs.ru
