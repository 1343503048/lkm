# perf sched latency refine outputs unit scaling histogram v7

# perf sched latency: v7 直方图中位数零点修正


## TL;DR
`perf sched latency` 在 v6（08-02）基础上发 v7，仅修正直方图中位数计算的零点偏差。属工具侧打磨，已迭代 7 版，合入可能性高。这是 08-02 系列 003 的后续版本。

## 背景与问题
`perf sched latency` 新增直方图与单位缩放后，直方图的**中位数（median）**在 v6 的实现中因未对样本差值做零点修正，导致中位数落在区间错误位置，影响延迟分布读数的准确性。

## 技术方案
v7 仅一处改动：直方图中位数计算时，对样本差值加零点修正，使中位数落在正确区间。其余（输出精炼、单位自动缩放、直方图分箱）维持 v6 行为。系列仍由 Artem Savkov 维护。

## 版本演进与当前进展
- 08-02 发出 v6（对应 08-02 系列 003）。
- 08-03 发出 v7，仅零点修正。

已迭代到 v7，工具侧 review 接近完成。

## Maintainer 意见与讨论焦点
尚未见 v7 的新 NAK；工具侧 maintainer（Arnaldo / Namhyung）此前对 v6 的接受表明方向认可。焦点在中位数修正的正确性确认。

## 合入评估
合入可能性 high。纯工具侧打磨，已 7 版打磨，无内核风险。

## 效果评估
邮件未给新基准；v6 已有功能描述。v7 属「正确性修正」（中位数落点），效果以直方图读数准确衡量。无新量化数据。

## 我可以参与的点
- 可用已知延迟分布的 perf.data 验证 v7 直方图 median 落点正确，回帖 tested-by（作者未附 runs）。

## 参考链接
- v6 文章：sched-20260802-003-perf-sched-latency-refine-outputs-unit-scaling-histogram-v6
- lore (v1 根): https://lore.kernel.org/lkml/20250730074016.9373-1-renmoluo@oktetlabs.ru

---
subject: "perf sched latency refine outputs unit scaling histogram v7"
id: sched-20260803-010
date: 2026-08-03
subsystem: perf
type: feature
status: under_review
severity: none
thread_root_msgid: "<20250730074016.9373-1-renmoluo@oktetlabs.ru>"
lore_url: "https://lore.kernel.org/lkml/20250730074016.9373-1-renmoluo@oktetlabs.ru"
authors: [Artem Savkov]
maintainers_involved: [Arnaldo Carvalho de Melo, Namhyung Kim]
current_version: v7
patch_series:
  - version: v6
    msgid: "<unknown>"
    date: 2026-08-02
    summary: "perf sched latency 新增直方图、单位缩放、输出精炼；v6 已发出。"
    review_outcome: "v6 接受 review。"
  - version: v7
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "v7 仅一处修改：把直方图样本中值（median）计算后的差值输出加上零点修正，使中位数落在正确区间；其余维持 v6 的输出精炼与单位缩放。"
    review_outcome: "v7 小幅修正，待 tools/perf maintainer 接收。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Arnaldo/Namhyung 接收；属工具侧优化，已迭代 7 版，合入近在咫尺。"
contribution_opportunities:
  - kind: testing
    description: "可对 v7 直方图 median 计算的零点修正做小规模验证（生成已知延迟分布的 trace，确认中位数落点正确），回帖 tested-by。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: ["sched-20260802-003-perf-sched-latency-refine-outputs-unit-scaling-histogram-v6"]
tags: [perf, histogram]
---
