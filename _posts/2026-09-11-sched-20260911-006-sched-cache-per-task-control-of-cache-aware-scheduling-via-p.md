---
id: sched-20260911-006
subject: 'sched/cache: Per-task control of cache aware scheduling via prctl'
date: '2026-09-11'
subsystem: sched
type: feature
status: rfc
severity: low
thread_root_msgid: <cover.1787955777.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
maintainers_involved: []
current_version: v1
patch_series:
- version: v1 (RFC)
  msgid: <cover.1787955777.git.tim.c.chen@linux.intel.com>
  date: 2026-08-27
  summary: RFC 0/7：prctl 级 per-task 缓存分组控制，PR_SCHED_CACHE_SHARE_FROM 按 pid 对指定共享来源；patch
    7 为文档。
  review_outcome: 09-09 Shrikanth 提出四问；09-11 Tim 逐条回应（腾讯跨进程功能分组用例、零改动可用、运行时可分组、拒绝
    cgroup 载体），Shrikanth 尚无跟进。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - CAS 在异构平台效果不佳无归因清楚的对照数据，接口收益无法量化
  - Shrikanth 对作者回答的跟进表态未出现
  - 拒绝 cgroup 载体为作者单方论证
  next_action: 等 reviewer 对回答的回应；跟踪 sched/cache 修复系列中预埋的 group 抽象先行落地情况
contribution_opportunities:
- kind: testing
  description: 验证仅凭 perf/proc/schedstat/L3 命中率能否判定线程分组，补「用户态决策依据」数据
- kind: review
  description: 对照 per-process NUMA prctl 方案核对两接口取舍一致性；核对 patch 7 文档的 pid 对语义
- kind: new_patch
  description: 若 prctl 覆盖不了不可改代码负载，提交 cgroup/sched_setattr 替代版本作讨论输入
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles:
- sched-20260909-016
- sched-20260831-008
- sched-20260829-002
tags:
- load_balance
- topology
- cgroup
title: 'sched/cache: Per-task control of cache aware scheduling via prctl'
layout: article
---

## TL;DR
Tim Chen 当日回复 Shrikanth Hegde 对该 RFC 0/7 的四个前置问题：给出腾讯（Vern Hao）跨进程按功能分组的真实用例、明确无需应用改码（管理员/守护进程用 PR_SCHED_CACHE_SHARE_FROM 按 pid 对分组）、运行时可分组、并重新陈述拒绝 cgroup 载体的理由。作者方首次正面回应，RFC 讨论从「接口要不要做」推进到「接口形状是否成立」。本文为增量更新，RFC 全貌见 sched-20260909-016。

## 背景与问题
CAS 默认按进程（mm）分组，但部分负载的正确分组只有用户知道：异构 L3 与大小核平台上内核难以推断任务间的数据共享意图，需要给应用/管理员一个 per-task 的分组入口。Shrikanth 在 09-09 提出四问：用户态现有工具能否支撑该决策、应用开发者依据什么判断分组、能否在应用运行后再分组、此前否决 cgroup 的理由是否仍成立。

## 技术方案
（RFC 0/7 的接口设计承 sched-20260909-016：以 prctl 暴露 per-task 的缓存分组控制，patch 7 为文档。）Tim 的回帖补充了设计动机与接口使用方式：

- 默认按进程分组在多数场景成立；需要自定义的是「用户了解负载特征、希望跨默认边界重组」的场景；
- 用例 1（腾讯，Vern Hao 提供）：同一业务有多个进程，其中部分任务负责数据库访问、部分负责加密、部分负责磁盘 IO——跨进程的同功能任务之间共享的数据多于同进程内任务；
- 用例 2：把共享内存的进程组归到一组；
- 另一判断入口：perf c2c 识别出数据共享的任务（回帖在此处截断于缓存正文，完整表述未获取到）；
- 接口使用：应用零改动——管理员或独立守护进程通过 prctl 指定要分组的 pid 对（PR_SCHED_CACHE_SHARE_FROM，见 patch 7 文档）即可。

## 版本演进与当前进展
current_version: v1（RFC 0/7，cover msgid `<cover.1787955777.git.tim.c.chen@linux.intel.com>`，08-27 发出）。

- 08-27：RFC 首发至 09-09 无回应；
- 09-09：Shrikanth 提出四问；
- 09-11（本文窗口）：Tim Chen 逐条回应（内容见上），无新版本发出。

## Maintainer 意见与讨论焦点
- **Tim Chen（作者方）**：正面回答全部四问。关于 cgroup：「没有强的理由支持数据共享的任务必须属于一个 cgroup；cgroup 覆盖不了我们想要的全部用例；用 prctl 的话管理员仍然可以把 cgroup 里的进程方便地分组（如果有意义），也不想无谓扰动 cgroup 接口」。
- **Shrikanth Hegde**（承 09-09）：四问已获回答，但尚未见到他对回答的跟进表态——四问中「运行后能否分组」已明确为可（daemon + prctl）。
- 分歧未闭合处：Shrikanth 是否接受这些答案、以及「不改代码的负载如何发现该分组」的实操依据仍缺数据支撑；cgroup vs prctl 的取舍论证是单方陈述，未见第三方评估。

## 合入评估
likelihood=unknown：RFC 阶段、无新版本、维护者（PeterZ 等）未入场。blocking_issues：接口的收益量化缺失（CAS 在异构平台效果不佳仍无归因清楚的对照数据）；作者与 Shrikanth 的问答尚无结论性后续；cgroup 载体被拒的理由是作者单方陈述。next_action：等 Shrikanth（或其他 reviewer）对回答的回应；关注 Tim 在 sched/cache 修复系列（sched-20260911-003）里预埋的「group 可挂到用户自定义分组」重构是否作为该 RFC 的前两补丁先行落地。

## 效果评估
暂无效果数据：回帖全部是动机与接口讨论，无 benchmark；腾讯用例为定性描述（哪些任务共享更多数据），未给出分组前后 LLC 命中率或延迟数字。

## 我可以参与的点
- kind=testing：在真实多线程应用上验证仅凭 perf/proc/schedstat 与 L3 命中率能否判定线程分组——这是「用户态有没有决策依据」一问的数据缺口（承 sched-20260909-016）。
- kind=review：对照同期 per-process NUMA balancing prctl 方案（sched-20260908-007），检查两个 per-task 接口在 cgroup 与 prctl 取舍上是否一致；核对 PR_SCHED_CACHE_SHARE_FROM 文档（patch 7）中 pid 对语义是否覆盖运行时重组。
- kind=new_patch：若结论是 prctl 覆盖不了不可改代码的负载，可提交 cgroup/sched_setattr 路线的替代版本作为讨论输入。

## 参考链接
- RFC 0/7 cover：https://lore.kernel.org/all/cover.1787955777.git.tim.c.chen@linux.intel.com/
- Tim Chen 09-11 回复：https://lore.kernel.org/all/bc2b92b6c9d0d63123adb9f5a2e29b6ec193792f.camel@linux.intel.com/
- Shrikanth 09-09 四问（未入当日缓存，链接承 sched-20260909-016）：未获取到
