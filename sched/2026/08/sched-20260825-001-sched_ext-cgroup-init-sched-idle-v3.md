---
title: "sched_ext：在 scx_cgroup_init_args 中传递初始 sched_idle 状态（v3）"
date: 2026-08-25
tags: [sched_ext, cgroup]
series: "sched_ext cgroup init sched_idle"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

sched_ext 的 `scx_cgroup_init_args` 会把 cgroup 的初始 weight、带宽控制参数带给
`ops.cgroup_init()`，却漏掉了 `cpu.idle` 状态。于是「在调度器加载之前（或在其下
被 online 之前）就已配置为 idle 的 cgroup」会被呈现为非 idle，BPF 调度器只有在该
cgroup 后续再次写入 `cpu.idle` 时才会知晓。

v3（UID 56332 cover、56333 1/2、56331 2/2 改名）相对 v2 的主要变化（据 cover 正文）：
- 按 Tejun 意见把新字段从裸 `idle` 改名为 `sched_idle`（裸 idle 在 sched_ext 里易被
  读成 CPU idle 状态）。
- 按 Andrea 建议补上 `Fixes:` 标签：`Fixes: 347ed2d566da ("sched/ext: Implement cgroup_set_idle() callback")`。
- 在 `tg->scx.idle` 改名的部分挪到 2/2。
- 已 rebase 到当前 linux-next，解决了 v2 报告的 CI 冲突。

## 改动内容 / 核心补丁

- 在 `struct scx_cgroup_init_args` 中新增 `sched_idle` 字段，并在构建 args 的全部
  四处填入：
  - `scx_tg_online()`：调度器下 online 的 cgroup；
  - `scx_cgroup_init()`：调度器加载时已存在的 cgroup；
  - `scx_cgroup_claim_subtree()` / `scx_cgroup_return_subtree()`：子调度器交接路径。
- 2/2 把 `tg->scx.idle` 改名为 `tg->scx.sched_idle`。

作者验证（VM 内用 probe 调度器打印 init args）：加载前配置 `cpu.idle=1` 的 cgroup
在 `ops.cgroup_init()` 中显示 `sched_idle=1`，默认值显示 0，后续 `cpu.idle` 写入仍
走 `ops.cgroup_set_idle()`；子调度器路径仅编译测试。

## 状态与讨论

- 当前状态：**under_review**；已获 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。
- 与 003（sched_ext Serialize cgroup knob updates，for-7.3-fixes）、005（cgroup
  更新锁上提到 core）配套，共同完善 sched_ext 的 cgroup 能力面。

## 关联

- 003 sched_ext：Serialize cgroup knob updates（for-7.3-fixes）
- 005 sched：cgroup 更新锁上提到 core
- 002 / 004 sched_ext 其它 cgroup 相关补丁
