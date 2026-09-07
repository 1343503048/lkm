# sched/numa: Fix time unit mismatch in scan staggering

## TL;DR
Hui Su 的单补丁修复：`init_numa_balancing()` 里 `node_stamp` 以纳秒存储，而 `task_scan_max()`/`numa_scan_period` 是毫秒，现有 `min_t()` 拿毫秒和纳秒直接比，新线程的 NUMA 扫描错峰间隔被算成约 30 万分之一（2000 ms 目标错成 60000 ns），多线程 workload 的初始扫描几乎完全扎堆。带 Fixes 标签，当日无人回复。

## 背景与问题
NUMA balancing 对共享同一 mm 的新线程做 scan 错峰（staggering）：`node_stamp` 初值取 `min(task_scan_max(p), 上一线程的 node_stamp + 间隔)`。该比较两侧单位不一致（ms vs ns）；且 `min_t(unsigned int, ...)` 会把 >UINT_MAX 的纳秒值截断，32 位系统上乘法还会先溢出。作者给了具体算例：默认 scan 周期、2 个 mm 使用者，预期错峰 2000 ms，实际得到 60000 ns，加上两个 tick 的偏移后 `node_stamp` 仅约 2.06 ms（HZ=1000）——错峰形同虚设，多线程初始阶段 PTE 扫描集中放大抖动。

## 技术方案
先用 u64 在毫秒域完成 min 比较，选定后再转纳秒，保持 `task_tick_numa()` 消费 `node_stamp` 的单位契约。改动仅 `kernel/sched/fair.c` 9 行。

## 版本演进与当前进展
v1（本日，msgid `<20260827095902.2645166-1-sh_def@163.com>`），暂无 review。`Fixes: 137844759843`（"sched/numa: Stagger NUMA balancing scan periods for new threads"）。

## Maintainer 意见与讨论焦点
无人表态。单位错误有算例支撑，预期不会有方向性争议；潜在讨论点只是是否值得走 stable。

## 合入评估
**likely**。逻辑正确性修复、有 Fixes、diff 极小；作者同日还有一封同类修复（sched-20260827-008），且前一对 DL server 修复已拿到 Juri 的 Ack（见 sched-20260827-016/017），说明该作者的微观修复线正在被接受。`next_action`：等 review。

## 效果评估
邮件给出的量化的是**错误**本身（2000 ms vs 60000 ns、HZ=1000 下 2.06 ms），修复后的扫描分布改善未附数据——修复动机充分，收益幅度属合理推断、未见实测。

## 我可以参与的点
- 对多线程 fork 风暴场景（容器批量起进程）敏感：OLK-6.6 若含 `137844759843` 同源代码，NUMA 机器上可用 `numactl --stats`/perf 数扫描脉冲验证；确认后按 OLK 规范（Fixes 引用 OLK commit）回合。

## 参考链接
- lore: https://lore.kernel.org/all/20260827095902.2645166-1-sh_def@163.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260827-009
date: '2026-08-27'
subject: "sched/numa: Fix time unit mismatch in scan staggering"
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "<20260827095902.2645166-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20260827095902.2645166-1-sh_def@163.com/"
authors: [Hui Su]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260827095902.2645166-1-sh_def@163.com>"
    date: 2026-08-27
    summary: "错峰比较改在毫秒域以 u64 进行，选定后再转纳秒，消除 ns/ms 混比与 32-bit 截断"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: "137844759843"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待维护者 review/收队列"
contribution_opportunities:
  - kind: testing
    description: "多线程 fork 风暴下验证扫描扎堆是否消失，回帖数据"
generated_at: "2026-09-07T22:05:00"
source_email_count: 1
related_articles: [sched-20260827-008]
tags: [numa_balancing]
---
