# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR
- sched-20260916-018：Klaus Kusche 反馈 Intel（Chen Yu）侧最新补丁后，其 AMD big/little 平台上 cache-aware 调度性能已基本追平无 cache-aware 内核、比早期 cache-aware 内核快约 2%，核心柱状图未见明显错放进程——偏正面的修复确认。
- sched-20260924-010（今天，增量更新）：Tim Chen 给出 Chen Yu 补丁之外的**替代补丁**（`sched/cache: Honor asym packing over cache aware scheduling on hybrid system`）：不再像之前那样整体关掉 cache-aware，而是在 hybrid 平台上让 asym packing 优先于 cache-aware——当迁移目标 CPU 优先级高于源组时放行迁移、跳过 LLC 亲和限制。他请 Klaus 在相同测试上试用这个新方向。

## 背景与问题
- sched-20260916-018：原始问题是 cache-aware 调度在 AMD big/little（Zen4/Zen4c 混合，如 1CCX 大小核混排）平台上表现不佳——进程被错放到不适合的核心，构建类负载变慢。完整技术背景见 sched-20260914-001。
- sched-20260924-010（今天）：Tim Chen 的新补丁把问题描述进一步具体化：AMD Ryzen AI HX 370 上跑 cache 密集的 Clang full-LTO link，小核频率低（3.3GHz vs 5.1GHz）且 L3 只有一半（8MB vs 16MB），把这种任务钉到小核 LLC 是「双重损失」，full-LTO 构建相比 cache-aware 之前的内核显著变慢。根源是 **asym packing 与 cache-aware 表达的是互相冲突的放置策略**。

## 技术方案
- sched-20260916-018：Chen Yu 侧补丁迭代（该日正文未含具体 patch）。
- sched-20260924-010（今天）：Tim Chen 的替代补丁让 asym packing 在 hybrid 上赢过 cache-aware。三处改动（kernel/sched/fair.c，+18/-3）：
  1. `can_migrate_llc_task()`：新增「若 `sched_asym(env->sd, dst_cpu, src_cpu)` 则直接 `return mig_unrestricted`」，即目标 CPU 相对源更高优先级时不再受 LLC 亲和限制。
  2. `llc_balance()`：在 `SD_ASYM_PACKING` 域且 `sgs->group_asym_packing`（目的 CPU 优先级高于源组所有 CPU）时 `return false`，跳过 cache-aware 的 LLC 聚合判定，让 asym packing 接管。
  3. `need_active_balance()`：把 `asym_active_balance(env)` 判断提到 `alb_break_llc(env)` 之前，优先响应 asym 的主动平衡。
  语义：asym packing 想让人物跑到最高优先级 CPU，而 cache-aware 想把人物的进程共置在一个 LLC（不论该 LLC 内 CPU 优先级），二者冲突时让 asym packing 赢。`Reported-by: Klaus Kusche`，`Closes:` 指向该线程。

## 版本演进与当前进展
- 本日（09-24）Tim Chen 发替代补丁并请 Klaus 复测；未见 Klaus 复测结果或维护者 ACK。

## Maintainer 意见与讨论焦点
- **Tim Chen（Intel）**：不再沿用「整体关 cache-aware」路线，改为主张「hybrid 上 asym packing 优先」的结构化取舍，并请报告者验证。
- 无 NAK；尚未见 Chen Yu/维护者对替代补丁的回应，也未定最终采用哪条路线。

## 合入评估
*likelihood=medium*。修复方向已在被实际用户验证（sched-20260916-018 追平基线），本日又给出更精细的替代方案；但「Chen Yu 原补丁 vs Tim Chen 替代补丁」的路线选择未定，仍需报告者复测背书并选边收敛。*blocking_issues*：asym packing vs cache-aware 的优先级策略需维护者统一裁决；替代补丁待实测。*next_action*：Klaus 在相同负载上测替代补丁并回帖，Intel/维护者据此选定路线。

## 效果评估
- 沿用 sched-20260916-018 的 Klaus 实测：两个构建测试几乎同速于无 cache-aware 内核、比早期 cache-aware 内核快约 2%，核心柱状图无错放进程。
- 本日无新增量化数据，等待 Klaus 对替代补丁的复测。

## 我可以参与的点
- kind=testing：在同类 AMD big/little（大小核混排）平台复测替代补丁，对比「关闭 cache-aware / Chen Yu 补丁 / Tim 替代补丁」三者在构建类负载上的表现并回帖。
- kind=review：核查 asym packing 优先的三处改动是否在所有 SD_ASYM_PACKING + cache-aware 组合下语义正确、无 LLM/主动平衡冲突。

## 参考链接
- lore (Tim 替代补丁): https://lore.kernel.org/all/7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com/
- lore (Klaus 反馈): https://lore.kernel.org/all/8aea0f25-0317-42ac-b59f-1a008c6eb106@computerix.info/

---
id: sched-20260924-010
date: '2026-09-24'
subject: 'Cache-aware scheduling does not work well with amd big/little cores'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: '<8aea0f25-0317-42ac-b59f-1a008c6eb106@computerix.info>'
lore_url: 'https://lore.kernel.org/all/7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com/'
authors:
  - 'Klaus Kusche'
maintainers_involved:
  - 'Tim Chen'
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Chen Yu 原补丁 vs Tim 替代补丁的路线选择未定'
    - '替代补丁待 Klaus 实测背书'
  next_action: 'Klaus 复测替代补丁并回帖，Intel/维护者选边收敛'
contribution_opportunities:
  - kind: testing
    description: '复测并对比关闭 CAS / Chen Yu 补丁 / Tim 替代补丁三段表现'
  - kind: review
    description: '核查 asym packing 优先三处改动在全部组合下的语义'
generated_at: '2026-09-25T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260916-018
  - sched-20260914-001
tags:
  - load_balance
  - cfs
---