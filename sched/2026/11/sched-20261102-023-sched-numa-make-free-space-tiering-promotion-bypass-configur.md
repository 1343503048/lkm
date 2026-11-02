# sched/numa: make free-space tiering promotion bypass configurable

## TL;DR

Li Zhe（字节）的 v2 系列（3 patches）让 NUMA 内存 tiering 中「顶层有空闲就绕过 hotness/rate-limit 检查、直接 promote」的 free-space bypass 行为可配置：为有意把 DRAM/CXL 按计划比例摆放（而非依赖自然 spillover）的部署保留原有 hotness 与限速检查。作者今天回帖感谢 Bharata 的认可，并请求维护者进一步反馈该系列是否可接受。

## 背景与问题

现有 NUMA tiering 的 free-space bypass：只要顶层（DRAM）有空闲空间，短冷访问也会被 promote 回补。这适合依赖「满则溢出」的经典部署，但不利于「编排层主动规划 DRAM/CXL 比例、为后续放置/其它工作负载保留 DRAM 余量」的场景——此时顶层仍有 free space，却不希望冷访问仅因 bypass 存在就立即回填。作者希望这类部署能继续走 hotness + rate-limit 检查。

## 技术方案

把 free-space tiering promotion bypass 做成可配置项（可开关），使需要保留 top-tier headroom 的部署能禁用 bypass、沿用既有的 hotness 与限速判定。具体配置文件未在今日窗口出现（仅收到 reply），据 v1/v2 根线索该系列含 3 个 patch。

## 版本演进与当前进展

v1（2026-10-28）→ v2（本窗口 1/3 被回复）。Bharata B Rao（AMD reviewer）已认可作者关于部署模型的说明（「a useful conclusion to reach」）。

## Maintainer 意见与讨论焦点

Bharata 认可部署合理性；但尚未有 NUMA 维护者（Peter Meltachian / Sean Christopherson 等）正式 review 或表态。作者今日正是在等这个。

## 合入评估

likelihood=unknown。方向得到 reviewer 认可，但缺维护者判定，合入前景未明。

## 效果评估

无性能数据；属行为可配置化，无直接测量。

## 我可以参与的点

- review：审阅 v2 三 patch 的配置语义（per-task/per-cgroup 粒度、默认值是否兼容旧行为）。
- discussion：为「free-space bypass 可配置」在非规划部署下的回归风险提供测试。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261028041253.74839-1-lizhe.67@bytedance.com/

---
type: feature
status: under_review
severity: none
thread_root_msgid: <20261028041253.74839-1-lizhe.67@bytedance.com>
authors:
- Li Zhe
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <3318a7f7-4dec-431b-9284-ec7c2807151c@bytedance.com>
  date: '2026-11-02'
  summary: free-space tiering promotion bypass 可配置（3 patches 系列）
  review_outcome: Bharata 认可部署模型，等待 NUMA 维护者正式 review
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 缺 NUMA 维护者正式 review/表态
  next_action: 等待维护者 feedback 后再定
contribution_opportunities:
- kind: review
  description: 审阅配置粒度/默认值/旧行为兼容性
- kind: discussion
  description: 评估非规划部署下的回归风险
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 1
related_articles: []
tags:
- numa
- numa_balancing
- cgroup
id: sched-20261102-023
subject: 'sched/numa: make free-space tiering promotion bypass configurable'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
---
