---
id: sched-20261013-004
subject: 'sched/numa: Add per-process automatic NUMA balancing control'
date: 2026-10-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
lore_url: https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
authors:
- Li Zhe
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260908122446.56708-1-lizhe.67@bytedance.com>
  date: 2026-09-08
  summary: prctl 式逐进程自动 NUMA balancing 控制（0/4），逐进程跟踪模式
  review_outcome: 昨日 Chen Yu/Yafang Shao 讨论接口形态，方向未收敛
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 接口形态未定：prctl vs 三元全局键 vs BPF-cgroup，维护者尚未表态
  next_action: 作者回应方向建议、明确接口与粒度后再推进
contribution_opportunities:
- kind: discussion
  description: 提供生产环境中 NUMA balancing 属性应由谁/以什么方式设置的实际输入
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- numa_balancing
title: 'sched/numa: Add per-process automatic NUMA balancing control'
layout: article
---

> **subject**：sched/numa: Add per-process automatic NUMA balancing control

## TL;DR
Li Zhe（字节跳动）9 月 8 日发出的「per-process 自动 NUMA balancing 控制」系列（0/4，prctl 式逐进程开关）在昨日迎来新一轮讨论：Chen Yu（Intel）建议把全局开关扩展成三元（类比 THP 的 always/advise/never），避免逐进程关闭 NUMA balancing 的负担；Yafang Shao 则基于 THP 与 LLC-aware 调度的生产经验，主张从一开始就做成 BPF-cgroup 式可扩展语义而非 prctl。方向（prctl vs cgroup/BPF vs 三元全局键）未收敛，属设计路线讨论。

## 背景与问题
全局 `numa_balancing` 开关对每个 workload 一视同仁，无法在不同（或不同生命周期阶段的）进程间差异化控制自动 NUMA balancing。Li Zhe 的系列引入 per-process 控制（`sched/numa: Track per-process automatic NUMA balancing mode` 跟踪逐进程模式）。昨日讨论聚焦这套接口的形态：

- 逐进程开启/关闭在规模场景下是负担——需要在整个系统里挨个关。
- prctl 式接口未必适配所有 use case（尤其 mTHP 等新内存语义）。
- 生产上（LLC-aware 调度）希望按 cgroup 而非全局粒度控制。

## 技术方案
作者系列（0/4）以逐进程 prctl 风格控制 NUMA balancing 模式。昨日讨论提出三路线：

- **Chen Yu**：全局键扩展为三元（`always/advise/never`），echo 0/1 保持向后兼容；类比已有 cache-aware 调度的同类提案。这样用户不必逐进程关闭。
- **Yafang Shao**：因 prctl 不贴合 mTHP 等场景，且他们在生产上用 LLC-aware 调度希望 per-cgroup 控制，建议「从一开始做成 BPF-based 特性」，语义可随新 use case 演进（他已有 `sched: add per-cgroup NUMA balancing mode selection via BPF` 的 RFC）。
- **Chen Yu（对 1/4 的实现）**：`tasklist_lock` 的写锁会阻塞 fork/exec，建议改用 RCU read lock 避免干扰频繁 fork/exec 的 agent。

## 版本演进与当前进展
原系列 0/4 为 v1（无版本号，`<20260908122446.56708-1-lizhe.67@bytedance.com>`，9 月 8 日发出），早于本简报窗口；本窗口为首次分析，昨日（2026-10-13）为该系列的新一轮讨论，无新版本补丁发出。

## Maintainer 意见与讨论焦点
- 无维护者（Peter/Juri/Dietmar 等）明确表态。
- **Chen Yu / Yafang Shao**（均为社区资深开发者）：分别主张「三元全局键」与「BPF-cgroup per-cgroup 语义」，实际在推动接口从 per-process prctl 向可扩展方向收敛；Chen Yu 还提出用 RCU 替代 `tasklist_lock` 写锁的实现建议。

## 合入评估
*likelihood=unknown*。无维护者表态，接口形态（prctl vs 三元键 vs BPF-cgroup）尚未收敛，与 Yafang 的并行 RFC 关系待理清。*blocking_issues*：方向未定、无 pull 信号。*next_action*：作者回应 Chen Yu/Yafang 的方向建议，明确接口与粒度选择后再推进。

## 效果评估
暂无效果数据；讨论为接口设计，无 benchmark 数字。

## 我可以参与的点
- discussion：接口形态（per-process prctl vs 三元全局键 vs per-cgroup BPF）是关键分歧，可结合生产场景（K8s 或其他调度器如何设置 NUMA balancing 属性）提供输入——Chen Yu 明确抛出了「生产环境会由谁、以什么方式设置」的问题，目前无人作答。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
- Chen Yu 引用的 cache-aware 调度提案：https://lore.kernel.org/lkml/fd341106e7e6cbd2f047656650f43ee87c6633c1.1787955777.git.tim.c.chen@linux.intel.com/
- Yafang 的 BPF-cgroup RFC：https://lore.kernel.org/lkml/20261012120438.52849-1-laoar.shao@gmail.com/
