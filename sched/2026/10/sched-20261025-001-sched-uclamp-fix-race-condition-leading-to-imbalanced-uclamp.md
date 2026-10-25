# sched/uclamp: Fix race condition leading to imbalanced uclamp_rq

## TL;DR
Qais Yousef 发单补丁修 uclamp 的 static key 非原子翻转导致的 runqueue 计数失衡竞态：`sched_uclamp_used` 使能瞬间部分 CPU 走 uclamp 快路径、部分不走，跨 CPU 的 enqueue/dequeue 不对称会使 `uclamp_rq` 计数永久错位。方案不试图堵住竞态，改为「视为既成事实 + idle 入口纠错」。kernel test robot 当日报出 arm/arc allnoconfig 下的 `init_uclamp_rq` 重复符号**链接错误**，需先修。

## 背景与问题
static key 跨 CPU 并不保证原子使能，`sched_uclamp_used` 打开时，有些 CPU 的 `uclamp_is_used()` 已返回 true、有些还没，导致 `uclamp_rq_{inc,dec}_id` 不对称。减而无增是安全的（代码注释已说明），但**增而无减**会破坏 `uclamp_rq` 状态。这个增而无减的竞态含义是：某 CPU 看到 key 翻转后在 enqueue 任务时递增，而该任务在另一个尚未看到翻转的 CPU 上 dequeue——作者提醒「这可能是更深问题的症状，需警惕」。真正堵住竞态很难（作者引用了 [1] 的讨论）。`Fixes: 46609ce227039`（"sched/uclamp: Protect uclamp fast path code with static key"），`Reported-by: Wei Wang <wvw@google.com>`。

## 技术方案
不堵竞态，而是把失衡当作既成事实，在**进入 idle 时做纠错动作**，保证该状态只在 `sched_uclamp_used` 使能后的很短时间内瞬时存在。作者用 `sched_feat` 强制注入额外 inc 制造失衡来测试：可见 WARN 出现、cpufreq 频率 spike；关闭该 sched_feat 后 idle entry 的 reset 能把状态修复。

## 版本演进与当前进展
*current_version: v1*（`<20261024233945.74794-1-qyousef@layalina.io>`，UTC 10-24 23:39 发出，北京时间 10-25 进入缓存）。尚无 reviewer 表态，kernel test robot 当日连续回 3 封构建报告。

## Maintainer 意见与讨论焦点
无维护者表态。kernel test robot（lkp）报三封构建结果：`arm-allnoconfig`（clang）报 **build ERROR**——`init_uclamp_rq` 重复符号，在 `core.c`/`fair.c`/`build_utility.c`/`build_policy.c` 各定义一次、链接冲突；`arm-allnoconfig`（clang）与 `arc-allnoconfig`（gcc）各报 W=1 构建 **warning**，提示 `init_uclamp_rq` 应声明 `static`。

## 合入评估
*likelihood=medium*。方向有理（static key 非原子性是既定事实），但当前有链接错误需先修。*blocking_issues*：`init_uclamp_rq` 在 `!CONFIG_UCLAMP` 下成了 header 内非 static 的 stub，多 translation unit 各自定义导致重复符号；作者需改为 `static` 或做正确的声明/实现分离。*next_action*：作者修复 `init_uclamp_rq` 重复符号后重发。

## 效果评估
无量化数据。作者定性描述：强制失衡时可见 WARN 与 cpufreq 频率 spike，关闭注入后 idle reset 修复。属正确性修复。

## 我可以参与的点
- *kind: review*：帮忙确认 `init_uclamp_rq` 在 `!CONFIG_UCLAMP` 构建下的正确修法（static 声明 vs 移入实现文件）。
- *kind: testing*：在启用 uclamp 的构建上验证 idle 入口纠错逻辑，确认失衡只瞬时存在、不会累积。

## 参考链接
- patch: https://lore.kernel.org/all/20261024233945.74794-1-qyousef@layalina.io/
- lkp build ERROR（arm-allnoconfig）: https://lore.kernel.org/all/202610252327.6QJlXAiY-lkp@intel.com/
- 竞态讨论 [1]: https://lore.kernel.org/lkml/CANDhNCqyXsZ6G77z+9s=rTO6BZifRG9+hVxMTah+tAv6pB6h3w@mail.gmail.com/

---
id: sched-20261025-001
date: 2026-10-25
subject: 'sched/uclamp: Fix race condition leading to imbalanced uclamp_rq'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261024233945.74794-1-qyousef@layalina.io>'
lore_url: 'https://lore.kernel.org/all/20261024233945.74794-1-qyousef@layalina.io/'
authors:
  - 'Qais Yousef'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261024233945.74794-1-qyousef@layalina.io>'
    date: 2026-10-24
    summary: 'idle 入口做 uclamp_rq 失衡纠错，堵不住 static key 非原子竞态就事后修复'
    review_outcome: 'lkp 报 init_uclamp_rq 重复符号链接错误'
upstream_commit: null
fixes_commit: '46609ce227039'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'init_uclamp_rq 在 !CONFIG_UCLAMP 下非 static 导致多 TU 重复符号链接错误'
  next_action: '作者修复 init_uclamp_rq 重复符号后重发'
contribution_opportunities:
  - kind: review
    description: '确认 init_uclamp_rq 在 !CONFIG_UCLAMP 下的正确修法'
  - kind: testing
    description: '启用 uclamp 的构建上验证 idle 纠错逻辑，失衡只瞬时存在'
generated_at: '2026-10-26T09:00:00'
source_email_count: 4
related_articles: []
tags:
  - uclamp
  - cfs
---
