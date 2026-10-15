---
id: sched-20261015-026
date: 2026-10-15
subject: 'sched/numa: fix several NUMA balancing issues'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261014094347.99157-1-lizhe.67@bytedance.com>
lore_url: https://lore.kernel.org/all/20261014094347.99157-1-lizhe.67@bytedance.com/
authors:
- Li Zhe
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261014094347.99157-1-lizhe.67@bytedance.com>
  date: 2026-10-14
  summary: 0/6 修复 scan-period、tiering promotion 反馈、execve locality 三方向问题
  review_outcome: Gregory Price 逐补丁要求性能数据；作者计划拆分并收敛到 tiering 专属
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 5/6 allnoconfig 构建错误；性能论证缺失；系列需拆分
  next_action: 修 5/6 构建错误，拆分严重修复、收敛到 memory-tiering 场景后重提交
contribution_opportunities:
- kind: review
  description: 核对 5/6 csky/hexagon allnoconfig 构建错误根因
- kind: testing
  description: memory-tiering 负载验证 4/6 可配置 bypass，补齐性能数据
generated_at: '2026-10-16T01:05:00'
source_email_count: 7
related_articles:
- sched-20261014-002
tags:
- numa_balancing
- cfs
title: 'sched/numa: fix several NUMA balancing issues'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-002-sched-numa-fix-several-numa-balancing-issues.html">sched-20261014-002</a>：Li Zhe（字节跳动）发 0/6 系列，修复 NUMA balancing 在 scan-period 调整、memory-tiering promotion 反馈、陈旧 task-placement 状态三方向的多个问题（含 memory hotplug 下可复现除零）；Gregory Price 逐补丁回帖，普遍要求补「用户可见性能影响」数据。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-026-sched-numa-fix-several-numa-balancing-issues.html">sched-20261015-026</a>（今天）：Li Zhe 逐条回应——坦承 3/6、5/6、6/6 无说服力性能数据、纯语义正确性；计划把「严重修复」与「启发式改动」拆开，将其余收敛到 memory-tiering 专属；并请 Gregory 把 Sashiko 的正确性意见转到列表。同时 kernel test robot 报出 5/6 在 csky/hexagon allnoconfig 的构建错误。

## 背景与问题
（承接 20261014-002）系列覆盖三类缺陷：scan-period 分母与共享 fault 语义（1–3/6，含 memory hotplug 后 `for_each_online_node()` 跳过下线节点留下的除零窗口）；memory-tiering promotion 反馈污染（4–6/6，free-space bypass 无视 hotness/rate-limit）；陈旧 task-placement 状态（execve 不重置 locality）。

## 技术方案
（承接 20261014-002）六补丁（`kernel/sched/fair.c` 等）。今日作者回应后的计划性收敛：
- 1/6（execve 清 locality）：作者定位为「补齐 Eric Dumazet 已经修过的同类 stale locality 问题的另一个 reset 边界」，影响 transient；
- 2/6（scan-period 分母校验）：作者解释这是有意改 fallback 条件，把「local+shared」混合物拆成「local+remote / private+shared」两个真实分母；
- 3/6（shared fault 语义）：作者承认无广泛收益数据，动机是 scan-period 决策的一致性；
- 4/6（free-space bypass 可配置）：作者倾向改 per-cgroup policy（指向 Yafang 的 BPF per-cgroup NUMA 模式 RFC），而非全局 sysctl；
- 5/6、6/6：作者承认缺数值、将由「严重修复」拆分下另行处理；6/6 请 Gregory 转述 Sashiko 的正确性反馈。
- kernel test robot：5/6 在 csky-allnoconfig（GCC 16.1.0）与 hexagon-allnoconfig（clang 24）构建报错，base tip/sched/core，需修 config 相关崩溃。

## 版本演进与当前进展
- v1（2026-10-14，0/6）→ 今日：作者回应全部 review，计划拆分「严重修复 vs 启发式改动」、收敛到 memory-tiering 专属；并发现 5/6 两处 allnoconfig 构建错误。

## Maintainer 意见与讨论焦点
Gregory Price（reviewer，非作者方）此前要求补性能数据、否定 4/6 全局 sysctl 方向。今日作者实质让步：承认 3/5/6 无性能数据、愿意拆开严重修复与启发式改动、接受 per-cgroup 方向。构建错误（kernel test robot）属必须修复的硬性阻塞。

## 合入评估
*likelihood=medium*。作者响应积极、方向在收敛，但系列还需拆分、补数据、修构建错误，尚无维护者 ACK。*blocking_issues*：5/6 allnoconfig 构建错误；性能论证缺失；系列需拆分。*next_action*：修 5/6 构建错误，按「严重修复优先」拆分出可独立合入的子集，其余收敛到 memory-tiering 专属场景后重提交。

## 效果评估
无量化数据；作者明确「无可信用户可见性能数字」。除零问题在 v7.3-rc1 QEMU guest 上 hot-remove NUMA 节点复现（作者自述）。

## 我可以参与的点
- *review*：核对 5/6 在 csky/hexagon allnoconfig 的构建错误根因（疑似缺失 config 分支的符号引用）。
- *testing*：在 memory-tiering（CXL + DRAM）负载上验证 4/6 的可配置 bypass 对带宽分布的影响，补齐作者缺的性能数据。

## 参考链接
- 系列 cover：https://lore.kernel.org/all/20261014094347.99157-1-lizhe.67@bytedance.com/
- 5/6 构建错误报告：https://lore.kernel.org/all/202610151319.LxjGvN6y-lkp@intel.com/
