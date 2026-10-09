# sched/cache: Honor asym packing over cache aware scheduling on hybrid systems

> **subject**：`sched/cache: Honor asym packing over cache aware scheduling on hybrid systems`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-003：Tim Chen 针对「cache-aware 调度在 AMD big/little 混合平台性能回退」的修复补丁——让 asym packing 在「要把任务迁到更高优先级空核」时优先于 cache-aware（迁到更高性能空核比 cache 共置更划算），带 `Fixes: 23b2b5ccc45c`、双 `Tested-by`、`Cc: stable # 7.2.x`；Kayra 指出注释与实现的语义不一致（未检查 idle 就放行）。
- sched-20260930-013：Kayra 与 Tim 就「应给 `sched_asym()` 的 cache-aware 放行加 `env->idle` 前置」往返讨论，Tim 认可并给出具体补丁片段。
- sched-20261006-002（今天）：**v2 发出**——`can_migrate_llc_task()` 的放行条件落成 `env->idle && sched_asym(env->sd, dst_cpu, src_cpu)`（正是 09-30 讨论的结论），另在 `llc_balance()` 加 `SD_ASYM_PACKING + group_asym_packing` 检查、把 `need_active_balance()` 的 asym 判断提到 `alb_break_llc()` 之前；Ricardo Neri 与 Klaus Kusche 线下完成测试。**当日两份重量级背书**：Kayra `Reviewed-by`（顺带指出 `llc_balance()` 里显式 `SD_ASYM_PACKING` 检查冗余——`sched_asym()`→`sched_use_asym_prio()` 内部已含该检查）；Chen Yu 用「QOS 限 L3 ways + pstate 限频」在 AMD Ryzen 9 8945HX 上仿真出 hybrid 配置实测——补丁前 cache-aware ON 吞吐 -56.6%（8 线程中 6 个困在 LLC1）、补丁后与 cache-aware OFF 持平（+1.5%，噪声内），附 `Tested-by`。

## 背景与问题

（承接 sched-20260929-003 → sched-20260930-013）AMD Ryzen AI HX 370 上 cache 密集的 Clang full-LTO 链接受阻：小核频率低（3.3 vs 5.1 GHz）、L3 减半（8 vs 16 MB），cache-aware 调度把任务钉到小核 LLC 双重受损。冲突根源是 asym packing（要最高优先级 CPU）与 cache-aware（要共置到同一 LLC、不论优先级）表达相反的放置策略。v1 的语义漏洞（`sched_asym()` 放行未检查目标核是否空闲）经 09-30 讨论确认修法为加 `env->idle` 前置。

## 技术方案

v2（`<77ceef1e51b895760dc5f6c9cde985a1679545b5.1791224900.git.tim.c.chen@linux.intel.com>`，kernel/sched/fair.c +18/−3）三处：

1. `can_migrate_llc_task()`：进入「too many threads / exceed LLC capacity」检查前，先判 `env->idle && sched_asym(env->sd, dst_cpu, src_cpu)`——**v2 相对 v1 的实质改动**（v2 说明：Ensure asym packing condition of idle CPU is fulfilled... (Kayra Cizmeci)）。
2. `llc_balance()`：`(env->sd->flags & SD_ASYM_PACKING) && sgs->group_asym_packing` 时 `return false` 优先 asym packing。Kayra 今日指出该显式 flag 检查**冗余**——`group_asym_packing` 由 `sched_group_asym()` 设置、其调 `sched_asym()`、再调 `sched_use_asym_prio()`，后者内部已有 `SD_ASYM_PACKING` 检查。
3. `need_active_balance()`：`asym_active_balance()` 提到 `alb_break_llc()` 之前——asym 迁移不应被 LLC 打破逻辑拦截。

Chen Yu 的仿真测试方法（对称 AMD Ryzen 9 8945HX 上造 hybrid）：改 AMD pstate driver + QOS 限 L3 ways——LLC0「大/快」：CPU 0-7,16-23、5.46 GHz、16 ways（32 MB）、ITMT 236；LLC1「小/慢」：CPU 8-15,24-31、3.29 GHz、8 ways（16 MB）、ITMT 100。负载：8 线程 pointer-chase ring（24 MB 工作集）。

## 版本演进与当前进展

- v1（09-29）：首发；Kayra 指语义不一致（sched-20260929-003）。
- 09-30：确认 `env->idle` 前置修法（sched-20260930-013）。
- v2（10-06 02:29 北京）：`env->idle` 落地 + `llc_balance` 检查 + `need_active_balance` 重排；Ricardo/Klaus 线下测试（v2 说明注明）。当日 Kayra `Reviewed-by`（附冗余检查备注）、Chen Yu 仿真实测 + `Tested-by`。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci**（reviewer）：`Reviewed-by`；同时指出 `llc_balance()` 显式 `SD_ASYM_PACKING` 检查冗余（调用链内部已查）——v3 待删。
- **Chen Yu**（Intel，sched/fair 维护者之一）：AI 辅助的 hybrid 仿真实测，数据说服力强（-56.6% 回归被修复），给 `Tested-by`。
- **Tim Chen**（作者）：v2 精确落实 09-30 讨论结论。
- 焦点：唯一遗留技术点是 Kayra 的冗余检查备注（将进 v3）；Peter Zijlstra 尚未收取进 sched/urgent。

## 合入评估

*likelihood=high*。`Fixes:` + 三位 `Tested-by`（Klaus Kusche、Ricardo Neri、Chen Yu，含维护者级）+ `Reviewed-by`（Kayra）+ `Cc: stable # 7.2.x`，v2 已吸收全部已知 review 意见；唯一未决是冗余检查删除（非阻塞）。*blocking_issues*：Kayra 的冗余检查待 v3 清理；Peter 的收取动作未发生。*next_action*：v3 删冗余检查后进 sched/urgent（后续实际进展见 sched-20261008-011）。

## 效果评估

Chen Yu 仿真 hybrid 实测（8 线程 pointer-chase ring、24 MB）：

| 配置 | cache-aware ON | cache-aware OFF |
|---|---|---|
| 补丁前 | ~230 M/s（6/8 线程困 LLC1） | ~530 M/s（-56.6% 差距） |
| 补丁后 | 520.7 ± 18.3 M/s（8 线程全在 LLC0） | 512.9 ± 16.6 M/s（+1.5%，噪声） |

回归被完全消除且 cache-aware 开关间无差。另有 Klaus/Ricardo 线下测试（v2 说明记录，无独立数字）。

## 我可以参与的点

- `review`：核对 Kayra 的冗余论证——沿 `sched_group_asym() → sched_asym() → sched_use_asym_prio()` 调用链确认 `SD_ASYM_PACKING` 检查确实覆盖 `llc_balance()` 新增分支的全部路径，为 v3 删除提供第二确认。
- `testing`：在真 hybrid 硬件（如 Ryzen AI 370 原机）上复核 Chen Yu 的仿真结论，补一份非仿真数据。

## 参考链接

- v2 补丁: https://lore.kernel.org/all/77ceef1e51b895760dc5f6c9cde985a1679545b5.1791224900.git.tim.c.chen@linux.intel.com/
- Kayra Reviewed-by（冗余检查备注）: https://lore.kernel.org/all/20261006135959.5709-1-kayracizmeci@gmail.com/
- Chen Yu 仿真实测 + Tested-by: https://lore.kernel.org/all/asUT-eR9yteRmB_v@three-body/
- v1（09-29）: https://lore.kernel.org/all/221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com/
- 回归报告（Klaus Kusche）: https://lore.kernel.org/lkml/2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info/

---
id: sched-20261006-002
date: '2026-10-06'
subject: 'sched/cache: Honor asym packing over cache aware scheduling on hybrid systems'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>'
lore_url: 'https://lore.kernel.org/all/77ceef1e51b895760dc5f6c9cde985a1679545b5.1791224900.git.tim.c.chen@linux.intel.com/'
authors:
  - 'Tim Chen'
maintainers_involved:
  - 'Chen Yu'
  - 'Kayra Cizmeci'
current_version: v2
patch_series:
  - version: v1
    msgid: '<221f8b0345328c4b26b65daff4d3eec56a32b06d.1790617047.git.tim.c.chen@linux.intel.com>'
    date: '2026-09-29'
    summary: 'asym packing 在迁往更高优先级空核时优先于 cache-aware'
    review_outcome: 'Kayra 指出语义不一致；09-30 确认 env->idle 前置修法'
  - version: v2
    msgid: '<77ceef1e51b895760dc5f6c9cde985a1679545b5.1791224900.git.tim.c.chen@linux.intel.com>'
    date: '2026-10-06'
    summary: 'env->idle 前置落地；llc_balance 加 asym 检查；need_active_balance 重排'
    review_outcome: 'Kayra Reviewed-by（冗余检查备注）；Chen Yu 仿真实测 + Tested-by'
related_articles:
  - sched-20260929-003
  - sched-20260930-013
upstream_commit: null
fixes_commit: '23b2b5ccc45c'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: '冗余检查待 v3 清理；Peter 收取动作未发生'
  next_action: 'v3 删冗余检查后进 sched/urgent'
generated_at: '2026-10-07T01:00:00'
tags:
  - load_balance
  - topology
  - regression
---
