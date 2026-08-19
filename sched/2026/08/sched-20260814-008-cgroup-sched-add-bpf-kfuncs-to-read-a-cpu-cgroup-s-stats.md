# cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats

## TL;DR
Ziyang Men 提交 v1（2 patches）「cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats」。为 cgroup CPU 控制器提供高效 BPF 读取统计（CFS 带宽计数直接读字段，新增 kfunc 计算 throttled time）。含 selftest。under_review。

## 背景与问题
收集 cgroup 统计目前需打开并解析 cgroup 文件，开销大。memcg 已有 BPF 高效替代；本系列把该思路扩展到 CPU 控制器，让 BPF 程序直接读取 cgroup CPU 统计，避免文件解析。

## 技术方案
- 设计：CFS 带宽计数（`tg->cfs_bandwidth` 的普通字段）直接交给 BPF 程序读，无需内核代码；仅 throttled time 需跨所有 CPU 求和，新增一个 kfunc 计算（用户态无法自算）。
- scheduler 侧改动仅为去掉 `throttled_time_self()` 的 static 以便外部使用（`kernel/sched/core.c` 1 行）。
- 新增 `kernel/cgroup/bpf_cpu.c`（80 行），含 rstat 遍历；附 `test_progs` selftest（cgroup_iter_cpu）。
- 已在 v7.2-rc5 VM 测试。

## 版本演进与当前进展
当前 v1（2 patches）。bpf-ci bot 已回复（38950）。8/14 发出。

## Maintainer 意见与讨论焦点
焦点：新 kfunc 的暴露范围与接口稳定性，需 cgroup/BPF 维护者确认。

## 合入评估
合入可能性 medium。方向合理（延续 memcg 的 BPF 统计思路），但跨 cgroup+BPF 子系统需多维护者评审。

## 效果评估
提供高效 cgroup CPU 统计读取，降低监控开销；无性能回归数据。

## 我可以参与的点
- 评审 kfunc 签名与暴露范围；
- 在 cgroup v2 CPU 控制器下验证 BPF 读取正确性。

## 参考链接
- lore: 未获取到

---
subject: "cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats"
id: sched-20260814-008
date: 2026-08-14
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260814025844.cgroup_bpf_cpu@ziyang>"
lore_url: "未获取到"
authors: [Ziyang Men]
maintainers_involved: [Tejun Heo, Peter Zijlstra, Alexei Starovoitov, Andrii Nakryiko]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260814025844.cgroup_bpf_cpu@ziyang>"
    date: 2026-08-14
    summary: "为 cgroup CPU 控制器新增 BPF kfuncs 读取统计：CFS 带宽计数直接读 tg->cfs_bandwidth 字段（无需内核代码），新增一个 kfunc 计算 throttled time（需跨所有 CPU 求和，用户态无法自算）。仅改动 scheduler 部分是去掉 static 的 throttled_time_self() 以便外部使用。含 test_progs selftest。"
    review_outcome: "v1 发出，bpf-ci bot 回复。已在 v7.2-rc5 VM 测试。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需 cgroup 与 BPF 维护者（Tejun/Alexei/Andrii）评审 kfunc 接口稳定性"]
  next_action: "等待 bpf-ci 后与 cgroup/BPF 维护者讨论 kfunc 暴露范围。"
contribution_opportunities:
  - kind: review
    description: "评审新 kfunc 的签名与 cgroup CPU 统计暴露范围是否恰当。"
  - kind: testing
    description: "在 cgroup v2 CPU 控制器下用 BPF 程序验证统计读取正确。"
generated_at: "2026-08-15T00:15:00"
source_email_count: 3
related_articles: []
tags: [sched/core, cgroup, bpf]
---
