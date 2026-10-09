# sched/numa: Ngid is reported as a global pid inside a pid namespace

## TL;DR

Maoyi Xie 报告一个 pid namespace 隔离缺口：`/proc/<pid>/status` 的 `Ngid` 字段（NUMA group id）没有像同函数打印的其他 pid 一样做 namespace 转换——`task_state()` 里 ppid/tgid 都走 `task_*_nr_ns(p, ns)`，唯独 `ngid = task_numa_group_id(p)` 返回的是 **init pid namespace** 视角的创建者 pid。作者在 qemu（双 NUMA 节点、numa_balancing 开启）中于主线 5e0f8396d480 复现：`unshare -Urpf` 后新 namespace 里任务 pid 为 1-17，`/proc/self/task/<tid>/status` 却读出 `Ngid: 421`。同类 CodeQL 检查还命中 `sched_show_numa()`（`/proc/<pid>/sched` 打印同一值）。作者给出两种修法方向并自测过其一，明确表示「愿意自己发补丁，也可以留给你们」，等待维护者表态。

## 背景与问题

- `fs/proc/array.c` 的 `task_state()`：`ppid = task_ppid_nr_ns(p, ns)`、`tgid = task_tgid_nr_ns(p, ns)` 都做了 ns 转换；`ngid = task_numa_group_id(p)` 直接取 `p->signal->numa_group_id`（由 `task_numa_group()` 建组时从 **`p->pid`**——init namespace 的全局 pid——赋值）。
- 影响：pid namespace 内的 unprivileged 工作负载可读到全局 pid 编号（信息泄露类 namespace 隔离缺口）；且语义上「Ngid 在 procfs 实例的 namespace 里无意义」。
- 触发条件低：numa_balancing 开启 + 任务组队即可，无需内核改动。作者同时列出今年已合入的三个同类修复佐证该问题模式成立：keys（`0d6a4268b060`）、io_uring（`3799c2570982`）、netdev（`1f24c0d01db2`）。
- `Documentation/filesystems/proc.rst` 文档 `Ngid: 0` 表示「无 group」，这约束了修法二（非初始 ns 打 0）的语义空间。

## 技术方案

作者提出两个候选方向（尚未定稿）：

1. **保留 struct pid**：NUMA group 里保存 `struct pid` 而非裸 gid，打印时走 `pid_nr_ns()` 转换——与 ppid/tgid 的处理方式一致，语义最正，但要改 `task_numa_group()` 的存储结构。
2. **非初始 namespace 打 0**：procfs 实例不属于 init pid namespace 时打印 0——作者已测试可行，但 `proc.rst` 文档规定 0 表示「无 group」，会把「有 group 但不可见」与「无 group」混为一谈，语义受损。

另有附带发现：`sched_show_numa()`（`/proc/<pid>/sched`）打印同一未转换值，属同一缺口。

## 版本演进与当前进展

- 10-03 首报（`<20261002194833.1069966-1-maoyixie.tju@gmail.com>`），无回帖。无补丁发出（作者明确先征求方向意见）。

## Maintainer 意见与讨论焦点

- 尚无维护者回帖。报告直接指向 sched/numa（`task_numa_group()`）与 fs/proc 交界，需 Peter Zijlstra 或 NUMA balancing 侧（Mel Gorman 等）表态方向。

## 合入评估

*likelihood=unknown*。问题真实且已复现、报告者有同型修复合入记录，但方向二义（struct pid vs 打 0）、无维护者表态、无补丁。*blocking_issues*：修法方向未定（语义 vs 工程量取舍）。*next_action*：维护者选定方向后作者发补丁（其自述愿意）。

## 效果评估

复现结果具体：qemu 双 NUMA 节点、numa_balancing 开启、主线 5e0f8396d480、`unshare -Urpf --propagation private --mount-proc` 下新 ns 任务 pid 1-17 读出 `Ngid: 421`。无性能影响讨论（纯信息展示路径）。

## 我可以参与的点

- `new_patch`：作者已公开邀请（「I am happy to send a patch, or to leave the fix to you」）——若数日内无人认领，可直接实现方向 1（NUMA group 存 `struct pid` + `pid_nr_ns()` 打印，同步修 `sched_show_numa()`），抢先发补丁并在 CC 中带上原作者协作。
- `review`：对方向 1 vs 方向 2 给出语义论证（proc.rst 的 0 语义约束），帮助维护者快速定方向。

## 参考链接

- lore（报告）: https://lore.kernel.org/all/20261002194833.1069966-1-maoyixie.tju@gmail.com/

---
id: sched-20261003-003
date: '2026-10-03'
subject: 'sched/numa: Ngid is reported as a global pid inside a pid namespace'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: '<20261002194833.1069966-1-maoyixie.tju@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261002194833.1069966-1-maoyixie.tju@gmail.com/'
authors:
  - 'Maoyi Xie'
maintainers_involved: []
current_version: v0
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '修法方向未定（struct pid 存储 vs 非初始 ns 打 0）'
    - '无维护者表态'
  next_action: '维护者定方向后发补丁；作者公开邀请认领'
contribution_opportunities:
  - kind: new_patch
    description: '实现方向 1（NUMA group 存 struct pid + pid_nr_ns() 打印，同步修 sched_show_numa()）'
  - kind: review
    description: '论证方向 1 vs 2 的语义取舍（proc.rst 的 0 语义约束）'
generated_at: '2026-10-04T01:00:00'
source_email_count: 1
related_articles: []
tags:
  - numa
  - procfs
  - namespaces
---
