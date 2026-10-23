---
id: sched-20261023-001
date: 2026-10-23
subject: 'sched: small changes'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261023023105.28829-1-laoar.shao@gmail.com>
lore_url: https://lore.kernel.org/all/20261023023105.28829-1-laoar.shao@gmail.com/
authors:
- Yafang Shao
maintainers_involved:
- Vincent Guittot
- Gregory Price
current_version: v1
patch_series:
- version: v1
  msgid: <20261023023105.28829-1-laoar.shao@gmail.com>
  date: 2026-10-23
  summary: 修复 !CONFIG_SCHED_CACHE 下 get_pref_llc() stub 签名 + 翻转 NUMA tick static key
    极性
  review_outcome: patch1 三人 Reviewed-by；patch2 被 Vincent 质疑极性（应 unlikely）
upstream_commit: null
fixes_commit: b636fef85bda
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - patch 2 static_branch_likely 与 Vincent 主张的 unlikely 惯例不一致
  next_action: patch 1 待收取；patch 2 与 Vincent 定夺极性后合入
contribution_opportunities:
- kind: discussion
  description: 就 sched_numa_balancing 静态 key 的 likely/unlikely 极性给出判断依据
- kind: review
  description: 确认 !CONFIG_SCHED_CACHE 构建下 get_pref_llc() stub 签名对齐后无遗漏调用点
generated_at: '2026-10-24T09:00:00'
source_email_count: 6
related_articles: []
tags:
- numa_balancing
- cfs
title: 'sched: small changes'
layout: article
---

## TL;DR
Yafang Shao 发往 sched 的两补丁小系列（cover 标题「sched: small changes」），均来自其 BPF-NUMA 系列实现中顺手发现的改进、可独立应用：patch 1 修复 `!CONFIG_SCHED_CACHE` 下 `get_pref_llc()` stub 仍持旧 `mm_struct` 参数的死代码（`Fixes: b636fef85bda`、`Cc: stable #7.2.x`，已获 Gregory Price / Chen Yu / Tim Chen 三人 Reviewed-by）；patch 2 把 NUMA balancing tick 检查从 `static_branch_unlikely()` 翻转为 `static_branch_likely()`（Acked-by Gregory Price）。分歧集中在 patch 2——Vincent Guittot 认为应与其他 static key 保持一致用 unlikely，Gregory 反驳「其他所有 `sched_numa_balancing` 检查都用 likely，这就是纯清理」。patch 1 无争议可收，patch 2 待 Vincent 定夺。

## 背景与问题
两项改动都源自作者正在推进的 BPF-NUMA 系列（链接见 cover 的 LWN [0]）实现过程，与主系列无关、可独立合入：

- **patch 1**：commit `b636fef85bda`（"sched/cache: Introduce task_struct->sched_cache_grp to fix UAF"）把 `get_pref_llc()` 的入参从 `struct mm_struct *` 改成 `struct sched_cache_group *`，但只更新了 `CONFIG_SCHED_CACHE` 分支定义和调用点，`!CONFIG_SCHED_CACHE` 分支的 stub 仍保留旧的 `mm_struct` 参数——死代码签名与实现不一致。
- **patch 2**：`task_tick_fair()` 每个 tick 都检查 `sched_numa_balancing`。当前用 `static_branch_unlikely()` 标注，为「未启用」情形保留了 nop，导致默认配置（`NUMA_BALANCING_DEFAULT_ENABLED=y`，NUMA balancing 默认开启）下每次 tick 都要付一次 taken jump。翻转为 `static_branch_likely()` 让快路径与默认一致。

## 技术方案
单文件（`kernel/sched/fair.c`，+2/-2）两处：

1. `get_pref_llc()` 的 `!CONFIG_SCHED_CACHE` stub 参数从 `struct mm_struct *mm` 改为 `struct sched_cache_group *grp`，与实现、调用点签名对齐。
2. `task_tick_fair()` 中 `sched_numa_balancing` 的 static key 极性从 `static_branch_unlikely()` 改为 `static_branch_likely()`。

## 版本演进与当前进展
*current_version: v1*。当日以 `[PATCH 0/2]` 形式连发（cover `<20261023023105.28829-1-laoar.shao@gmail.com>`）。这两个补丁此前曾以独立补丁形式在 10-21/10-22 单独发过并累积了 review 标签，本次合并为带 cover 的系列重发。

## Maintainer 意见与讨论焦点
- **patch 1 无争议**：Gregory Price、Chen Yu、Tim Chen 三人已给 Reviewed-by。
- **patch 2 有分歧**（核心焦点）：
  - Vincent Guittot：`static_branch_unlikely` 是 `sched_cluster_active`、`sched_cache_active`、`__sched_core_enabled`、`sched_asym_cpucapacity` 等其他 static key 的默认用法，「不启用它们的系统不在使用它时不付跳转，我不明白 numa 为什么该不同」；并在第二封回帖补充「其他有些地方可能挂在另一个 key 后面，但这里就应该是 unlikely()；其他 key 也是默认开启的」。
  - Gregory Price：其他所有检查 `sched_numa_balancing` 的地方用的都是 `likely()`，这里是「唯一例外的那个」；numa balancing 默认开启；「这在我看来就是纯清理」。

分歧实质：Vincent 强调与其他 static key 用法一致（unlikely 是惯例），Gregory/Yafang 强调 `sched_numa_balancing` 这一特定 key 的其他所有检查点都用 likely 且默认开启。双方对「默认开启」这一前提都认可，但对「该向哪个惯例看齐」看法不同。

## 合入评估
*likelihood=medium*。patch 1（stale stub 修复）已有三重 Reviewed-by 且带 stable 标签，可独立收取；patch 2 的极性翻转被 Vincent 反对，卡在惯例之争。*blocking_issues*：patch 2 的 `static_branch_likely()` 与 Vincent 主张的 `unlikely()` 惯例不一致。*next_action*：patch 1 待维护者收取；patch 2 需作者与 Vincent 就极性达成一致（或拆分后仅合入 patch 1）。

## 效果评估
patch 2 的作者论证是「默认配置下每次 tick 省一次 taken jump」——属静态分支极性的微优化，**邮件中无 benchmark 数据支撑**（作者主观判断）。patch 1 为纯签名对齐，无行为/性能变化。

## 我可以参与的点
- *kind: discussion*：就 `sched_numa_balancing` 静态 key 该用 likely 还是 unlikely（跟「其他 static key 惯例」还是「本 key 其他检查点惯例」）给出判断依据，帮收敛 patch 2 的极性之争。
- *kind: review*：确认 patch 1 的 `get_pref_llc()` stub 签名对齐后 `!CONFIG_SCHED_CACHE` 构建无遗漏调用点。

## 参考链接
- cover: https://lore.kernel.org/all/20261023023105.28829-1-laoar.shao@gmail.com/
- patch 1: https://lore.kernel.org/all/20261023023105.28829-2-laoar.shao@gmail.com/
- patch 2: https://lore.kernel.org/all/20261023023105.28829-3-laoar.shao@gmail.com/
- Vincent 回帖 1: https://lore.kernel.org/all/CAKfTPtD7UsFkH=YPp9Faf0LX8ppNDw6hkVgFd-0Y30oSBYdgfg@mail.gmail.com/
- Vincent 回帖 2: https://lore.kernel.org/all/CAKfTPtAkN06AKxQZrTCT+_C=x7v8f+S3EC=nkcdyJpuspfop3A@mail.gmail.com/
- Gregory 回帖: https://lore.kernel.org/all/179276890032.2252127.6836118712740428624.b4-reply@b4/
