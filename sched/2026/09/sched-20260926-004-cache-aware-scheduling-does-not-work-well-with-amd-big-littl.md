# Cache-aware scheduling does not work well with amd big/little cores

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260916-018：Klaus 反馈 Chen Yu 侧补丁后 AMD big/little 上 cache-aware 性能基本追平基线。
- sched-20260924-010：Tim Chen 给出替代补丁（hybrid 上让 asym packing 优先于 cache-aware），请 Klaus 复测。
- sched-20260925-025：Klaus 报告替代补丁打 7.2.7 大段 fuzz、`fair.c` 编译失败，并质疑新增 `sched_asym` 调用不会真正内联。
- sched-20260926-004（今天）：Tim Chen 把补丁 rebase 到 v7.2.7（真·回移，两处适配），逐条反驳编译/内联质疑，请 Klaus 再测。

## 背景与问题

（承接 sched-20260924-010）cache-aware 调度在 AMD big/little（Ryzen AI HX 370）混合平台上把 cache 密集任务错放到小核 LLC——小核频率低（3.3 vs 5.1 GHz）、L3 只有一半（8 vs 16 MB），锁在小核 LLC 双重吃亏，Clang full-LTO link 相比无 cache-aware 内核大幅变慢。根源是 asym packing（要放最高优先级 CPU）与 cache-aware（要把同进程任务共置到同一 LLC、不论优先级）表达互相冲突的放置策略。

## 技术方案

（承接 sched-20260924-010）Tim Chen 替代补丁让 asym packing 在 hybrid 上优先于 cache-aware，三处改动：`can_migrate_llc_task()` 在 `sched_asym(...)` 时直接 unrestricted、`llc_balance()` 在 `SD_ASYM_PACKING` 且目的组 asym priority 更高时跳过 LLC 聚合、`need_active_balance()` 把 asym 判断提前。

今天的进展是把补丁做成一版真正的 v7.2.7 回移（非同一 diff）：(1) v7.2.7 的 `can_migrate_llc_task()` 签名是 `(src_cpu, dst_cpu, p)` 而非 `lb_env`，需显式传 `sched_domain` 并更新唯一调用点；(2) v7.2.7 的 `llc_balance()` 没有 `SD_ASYM_CPUCAPACITY` misfit early-out，新 asym 检查放在 `SD_SHARE_LLC` 检查之后。Tim Chen 附上了这版回移补丁，并说明原补丁是基于 Peter 的 sched/urgent 树（`fair.c` 布局不同）生成的，fuzz 即源于此。

## 版本演进与当前进展

- 09-24：Tim Chen 发替代补丁（针对 sched/urgent）。
- 09-25：Klaus 报 7.2.7 编译失败 + inline 质疑。
- 09-26：Tim Chen（`<c69168ffeeb1d6ea4399b1a9ed6da7b24ac69bb8.camel@linux.intel.com>`）给出 7.2.7 回移版，请 Klaus 复测（可测 sched/urgent 原版或邮件末尾的回移版）。

## Maintainer 意见与讨论焦点

- **Tim Chen**（补丁作者，Intel）：针对 Klaus 的 inline 质疑回应——前置声明后再定义同一文件的 `static inline` 是合法 C，编译期内联不受影响；他已反汇编确认 `sched_asym()` 确实被内联，且 `fair.c` 里 `cfs_rq_max_slice()`、`account_mm_sched()` 等已有同样的声明前置写法。
- 路线分歧（Chen Yu 原补丁 vs Tim Chen 替代补丁）仍未正式收敛；本日无独立维护者（Peter/Vincent）表态，仍需等 Klaus 在 7.2.7 上完成复测。

## 合入评估

*likelihood=medium*。修复方向有实测背书（16-018 追平基线），且今天已解决「7.2.7 无法编译」这一复测卡点。*blocking_issues*：Klaus 尚未对回移版给出复测结果；asym packing vs cache-aware 的优先级策略待调度维护者裁决。*next_action*：Klaus 用回移版复测 cache 密集负载；维护者选定路线。

## 效果评估

今日无新数据。沿用 16-018 实测：两个构建测试几乎同速于无 cache-aware 内核、比早期 cache-aware 约快 2%。

## 我可以参与的点

- `testing`：在 AMD Ryzen AI HX 370（或同类 Zen4/Zen4c 混合平台）上对回移版跑 Clang full-LTO link 等 cache 密集负载，给出与无 cache-aware、以及 Chen Yu 原补丁的三列对照。
- `review`：核对 v7.2.7 回移版两处适配（`can_migrate_llc_task` 签名、misfit early-out 位置）是否等价于 sched/urgent 原版语义，确认没有引入行为差异。

## 参考链接

- Tim Chen 回移版回帖: https://lore.kernel.org/all/c69168ffeeb1d6ea4399b1a9ed6da7b24ac69bb8.camel@linux.intel.com/
- Klaus 报编译失败: https://lore.kernel.org/all/e2c87de0-31f7-4ed0-b80e-7f9aa7d0e511@computerix.info/
- 线程根: https://lore.kernel.org/all/7b83cf0cd1704b552978af88d7de9c57970c23a1.camel@linux.intel.com/

---
id: sched-20260926-004
date: 2026-09-26
subject: "Cache-aware scheduling does not work well with amd big/little cores"
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "<c69168ffeeb1d6ea4399b1a9ed6da7b24ac69bb8.camel@linux.intel.com>"
lore_url: "https://lore.kernel.org/all/c69168ffeeb1d6ea4399b1a9ed6da7b24ac69bb8.camel@linux.intel.com/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: "2026-09-27T01:20:00"
authors:
  - "Tim Chen"
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Klaus 尚未对 v7.2.7 回移版给出复测结果"
    - "asym packing vs cache-aware 的优先级策略待调度维护者裁决"
  next_action: "Klaus 用回移版复测 cache 密集负载；维护者选定路线"
contribution_opportunities:
  - kind: testing
    description: "在 AMD Ryzen AI HX 370 上对回移版跑 Clang full-LTO link 等 cache 密集负载，给出三列对照"
  - kind: review
    description: "核对 v7.2.7 回移版两处适配与 sched/urgent 原版语义是否等价"
source_email_count: 1
related_articles:
  - "sched-20260925-025"
  - "sched-20260924-010"
  - "sched-20260916-018"
tags:
  - load_balance
  - cfs
  - x86
---