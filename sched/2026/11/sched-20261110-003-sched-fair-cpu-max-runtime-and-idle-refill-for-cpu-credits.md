# sched/fair: cpu.max.runtime and idle refill for CPU credits

## TL;DR

Fernand Sieber（Amazon）发 v2 四补丁系列，为 CFS 带宽控制器补上「CPU credits」场景所需的三个能力：新增 `cpu.max.runtime` 读/写 cgroup v2 文件以直接读写 runtime（信用额度）、解除 `cpu.max.burst` 不能超过一个 quota 的限制、并让空闲组在 idle 期间持续挣取最多 quota+burst 的额度。目标是把 CFS bandwidth 控制器直接当作 burstable VM 的「信用桶」：quota=基线（挣额度速率）、quota+burst=上限、runtime=当前额度。补丁 3 把写入透传给 BPF 调度器、补丁 4 让它们把任务也计入同一 runtime。

## 背景与问题

作者运行以 CPU credits 计费的 VM：每个实例有 baseline（其 vCPU 始终可用的份额）、运行时低于 baseline 挣额度、高于 baseline 花额度、额度有上限，花完则被压回 baseline。起始额度、baseline 与上限属于实例类型的保证，host 无论做什么都不能让实例丢额度或白拿额度。CFS bandwidth 控制器几乎就是那个信用桶：quota/period=挣额度速率（baseline），quota+burst=上限，runtime=额度；控制器在调度器内做逐 CPU 计费与 throttle，粒度是用户态记账无法匹敌的。缺三件事：① 上限无法超过一个 quota（burst 被限制在 quota 内，patch 1 解除）；② 额度无法读/写（patch 1）；③ 空闲组不挣额度（period 定时器在组未运行的一个 period 后停掉，睡过的 period 完全不补）——例如 100ms period 的实例 idle 一分钟，只能挣到一个 quota 而不是最多 600 个。

作者列出必须能读/写额度的场景：启动时按实例类型授予起始额度；kexec/reboot 跨内核活升级时先读后写回；活迁移把额度随实例搬到新 host；控制面调升/调降额度。并回应 Ben 的「cpu.max/cpu.max.burst 写已加一个 quota + cpuacct 给用量」的替代方案：它只能加、且每次只能加一个 quota，降额度或精确设定都要用临时 quota 反复写、每次都走 `tg_set_cfs_bandwidth()` 遍历每 CPU 的 cfs_rq。

## 技术方案

四补丁：① `sched/fair: expose cpu.max.runtime to set bandwidth runtime directly`（新增 `cpu.max.runtime`，读写 runtime，并解除 burst≤quota 限制）；② `sched/fair: refill bandwidth for the periods the timer slept through`（空闲组醒来后按睡过的 period 补 refill，行为上让「带 burst 且 idle 后变 runnable 的组」拥有最多 quota+burst，等于它一直以低于 quota 运行）；③ `sched_ext: add cgroup_set_runtime ops callback`；④ `sched_ext: charge BPF scheduler tasks to cpu.max bandwidth`（把 SCX 侧任务计入同一 runtime）。cover 明示 patch 2 会改变现有 `cpu.max.burst` 用户的行为。

## 版本演进与当前进展

*current_version: v2（2026-11-10，`<cover.1794303670.git.sieberf@amazon.com>`）*。v2 相对 v1 的改动未见 cover 逐条罗列（changelog 未给出 v1 msgid），正文为完整方案说明。当日无评审回复。

## Maintainer 意见与讨论焦点

当日缓存无维护者回复。cover 里作者回应了 Ben（CFS bandwidth 作者）此前的替代方案质疑（cpu.max/cpu.max.burst 写 + cpuacct 为何不够），并强调 patch 2 对既有 `cpu.max.burst` 用户是一次行为变更、需要评审者正视。无 NAK。

## 合入评估

*likelihood=medium*。方案完整、用例清晰，但涉及 cgroup v2 接口扩展（`cpu.max.runtime`）与 `cpu.max.burst` 行为变更，需 CFS bandwidth 维护者与 sched_ext 维护者（patch 3/4）双方评审。*blocking_issues*：① `cpu.max.runtime` 新接口需 cgroup 维护者认可；② patch 2 的行为变更需确认无破坏既有用户。*next_action*：等待 CFS bandwidth（Ben）与 sched_ext（Tejun）评审 v2。

## 效果评估

当日无性能数据。作者从「credits 计量正确性」角度立论（不丢额度、不多挣额度），cover 未给 benchmark。

## 我可以参与的点

- **review**：评估 patch 2「空闲组补 refill」在 quota 很小、burst 很大时的边界（是否会让长期 idle 的组醒来后一次性获得远超预期的 runtime）。
- **testing**：在真实 VM 计费场景验证 kexec/活迁移前后 runtime 读/写往返一致，尤其 `cpu.max.burst` 既有用户是否被 patch 2 改变行为。

## 参考链接

- lore thread: https://lore.kernel.org/all/cover.1794303670.git.sieberf@amazon.com/

---
id: sched-20261110-003
date: '2026-11-10'
subject: "sched/fair: cpu.max.runtime and idle refill for CPU credits"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<cover.1794303670.git.sieberf@amazon.com>"
lore_url: "https://lore.kernel.org/all/cover.1794303670.git.sieberf@amazon.com/"
authors: [Fernand Sieber]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<cover.1794303670.git.sieberf@amazon.com>"
    date: '2026-11-10'
    summary: "新增 cpu.max.runtime 读/写、解除 burst≤quota、空闲补 refill、SCX hook"
    review_outcome: "当日无评审回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "cpu.max.runtime 新接口需 cgroup 维护者认可"
    - "patch 2 对 cpu.max.burst 既有用户的行为变更需确认"
  next_action: "等待 CFS bandwidth（Ben）与 sched_ext（Tejun）评审 v2"
contribution_opportunities:
  - kind: review
    description: "评估 patch 2 空闲补 refill 在 quota 很小、burst 很大时的边界"
  - kind: testing
    description: "验证 kexec/活迁移前后 runtime 读/写往返一致，以及 cpu.max.burst 既有用户是否被改变"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 5
related_articles: []
tags: [cgroup, cfs, sched_ext]
---