# cpufreq: Use hardware feedback for cpuinfo_avg_freq

> **subject**：`cpufreq: Use hardware feedback for cpuinfo_avg_freq`

## TL;DR

Chuyi Zhou（ByteDance）发起的 3 补丁系列中的 2/3 在本日迎来 Beata Michalska 的 review：补丁让 `cpuinfo_avg_freq` 采用硬件反馈（hardware feedback），Beata 追问 changelog 里「temporary sampling gaps」的具体含义，并质疑「是否需要为读取该属性而唤醒 target CPU」。本片正文与 cover 不在当日缓存，仅有一则 review，证据有限。

## 背景与问题

本语境证据有限：当日缓存只有 Beata 对 patch 2/3 的 review 回复，补丁与 cover 均未取到。从 subject 与 review 可推断：该系列（3 补丁，作者 Chuyi Zhou）目标是让 `cpuinfo_avg_freq` 使用硬件反馈信息，涉及 sampling（采样）与「gaps（采样缺失）」的处理，以及是否要唤醒 target CPU 来读特定属性。

## 技术方案

当日无补丁正文，无法描述具体实现。Beata 的 review 指向两处需要澄清的契约：

1. 「temporary sampling gaps」语义含糊——是「采样没发生」、还是「样本过期/某种程度无效」？且这一点是否已由前一句暗示。
2. 是否存在「为读取该特定属性而唤醒 target」的场景，Beata 认为不需要。

## 版本演进与当前进展

- 系列 v1 于 09-16 发出（线程根 `<20260916142623.359336-1-zhouchuyi@bytedance.com>`，2/3 为 `<20260916142623.359336-3-zhouchuyi@bytedance.com>`），早期版本与其余补丁不在本次分析窗口内。
- 09-29：Beata Michalska 对 2/3 提出上述 review，作者尚未回复。

## Maintainer 意见与讨论焦点

- **Beata Michalska**（reviewer，ARM cpufreq/EAS 相关）：对 changelog 措辞与非必要唤醒提出澄清要求，语气为审阅性提问，无 NAK。
- 作者 Chuyi Zhou 当日未回复。

## 合入评估

*likelihood=unknown*。仅有一则 review、补丁正文不在缓存、系列从 v1 发出已隔约两周，进度与合入倾向均无法判断。*blocking_issues*：Beata 的措辞/语义澄清未回应；补丁正文未在窗口内。*next_action*：作者回应 Beata 的两处澄清后，跟踪系列后续版本。

## 效果评估

无数据（当日仅 review 回复，无 benchmark 或复现数字）。

## 我可以参与的点

- `review`：若补全补丁正文，可核对「用硬件反馈算 avg_freq」在 CPU 离线/boost/采样缺失场景下的语义。
- `discussion`：就 Beata 提到的「是否该为属性读取唤醒 target」给出分析。

## 参考链接

- lore（Beata 回复）: https://lore.kernel.org/all/arvFb8kJoWT98Suj@arm.com/
- lore（系列线程根）: https://lore.kernel.org/all/20260916142623.359336-1-zhouchuyi@bytedance.com/

---
id: sched-20260929-020
date: '2026-09-29'
subject: 'cpufreq: Use hardware feedback for cpuinfo_avg_freq'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260916142623.359336-1-zhouchuyi@bytedance.com>'
lore_url: 'https://lore.kernel.org/all/arvFb8kJoWT98Suj@arm.com/'
authors:
  - 'Chuyi Zhou'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260916142623.359336-1-zhouchuyi@bytedance.com>'
    date: '2026-09-16'
    summary: '3 补丁系列（使 cpuinfo_avg_freq 采用硬件反馈）；正文与 cover 不在当日缓存'
    review_outcome: 'Beata 对 2/3 提措辞与「是否需唤醒 target」的澄清'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - 'Beata 的语义澄清未回应'
    - '补丁正文不在窗口内'
  next_action: '作者回应 Beata 的澄清后跟踪后续版本'
contribution_opportunities:
  - kind: review
    description: '补全正文后核对硬件反馈算 avg_freq 在采样缺失/boost 场景的语义'
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles: []
tags:
  - cpufreq
---