# sched_ext: Pass the initial cmask to cid-form ops.enable()

## TL;DR
Tejun Heo 在一天之内把 sched_ext cid-form API 的一个明显漏洞从 v1 迭代到 v3 并合入 `sched_ext/for-7.3-fixes`：此前 cid-form 调度器的任务 cmask 只能通过 `ops.set_cmask()` 看到，而它在 fork/子调度使能/re-home 等进入路径上不触发，导致调度器只能用 `ops.init_task()` 里从 `p->cpus_ptr` 播种、再被陈旧化。v3 把初始 cmask 通过新参数结构 `scx_enable_args` 传入 `ops.enable()`。Andrea Righi 全程 review（v1 提两点 → v3 给 1/2 Reviewed-by、2/2 几个 nit），Tejun 当日即应用。

## 背景与问题
cid-form API（sched_ext 为 7.3 引入、当时标记为 unpublished）有一个"明显的洞"：任务的 cid mask 只在 `ops.set_cmask()` 回调里可见，而该回调只在亲和性变更和 class 切换时触发，任务通过 fork、sub-sched enable、re-home 进入调度器时并不触发；且没有 `p->cpus_ptr` 等价物可回退。现有调度器的 workaround 是在 `ops.init_task()` 里按 `p->cpus_ptr` 逐 cid 播种掩码，这在 sub-sched enable / re-home 场景下是微妙的错误：`init_task()` 与 `enable()` 之间发生的亲和性变更会投递给任务仍属的旧 sched，新 sched 的副本得不到纠正。

## 技术方案
- 1/2（`sched_ext: Pass the initial cmask to cid-form ops.enable()`）：新增 `struct scx_enable_args`，作为 cid-form `ops.enable()` 的第三参数携带任务的 cmask；在任务进入调度器时于 rq 锁下、per-cpu scratch（arena 内存）里构建该掩码，`enable()` 之后再以同一掩码调用一次 `set_cmask()`。调度器于是可以只在 `set_cmask()` 里维护亲和性，`scx_qmap` 也删掉了 `init_task()` 播种。`set_cmask()` 不再在 cid-form 任务 enable 之前触发；`switching_to_scx()` 里的 class-switch 重发布只保留给 cpu form。
- 2/2（`selftests/sched_ext: Check the cmask cid-form ops.enable() receives`）：新增 cid-form selftest `enable_cmask`，校验 `enable()` 收到的掩码与随后的 `set_cmask()` 一致、与 `p->cpus_ptr` 一致，且初始 `set_cmask()` 落在 `set_weight()` 之前与任务首次 runnable 之前，`set_cmask()` 从不先于 `enable()`，覆盖 class-switch/fork-路径使能与实时亲和性变更。

关键取舍（V2 起）：cmask 以 `u64` arena 地址 `cmask_arena_addr` 传递，而非内核类型指针，因为 BTF 尚不能类型化 arena 结构成员（Sashiko bot 的 review 意见）；用 args 结构而非裸 cmask 参数，为后续更多初始状态留出空间、避免再次改签名。

## 版本演进与当前进展
- v1（`<c8343c2e457508a6cd3fcab66b0823b6@kernel.org>`）：新增 `scx_enable_args`，cmask 以内核指针传递。
- v2（`<2f0eb5c762d55edba5365f1006dbb395@kernel.org>`）：按 Sashiko review 把 cmask 改为 `u64` arena 地址，并文档化类型化限制与计划中的类型别名。
- v3（`<20260919002838.1960071-1-tj@kernel.org>`，PATCHSET，2 patch）：按 Andrea 意见把初始 `set_cmask()` 提前到 `set_weight()` 之前；新增 selftest。分支 `git://git.kernel.org/.../tj/sched_ext.git cid-enable-args-v3`。

## Maintainer 意见与讨论焦点
- **Andrea Righi**（v1）：① 能否把初始 `ops.set_cmask()` 提前到 `ops.set_weight()` 之前，否则 `set_weight()` 可能观察到空/陈旧掩码；②（新原型是否破坏既有 cid-form 调度器？）经 Tejun 实测：不读 `@args` 的两参数 `enable()` 在新旧内核都能加载、读了第三个 ctx slot 的会被旧内核拒绝（"func 'enable' doesn't have 3-th argument"）、旧的一参数 `enable()` 在新内核也正常；③ 建议加 selftest 比对 `enable()` 与紧随的 `set_cmask()` 掩码。
- **Andrea Righi**（v3）：1/2 "Looks good now"，给 Reviewed-by；2/2 三个 nit——全局变量会被 `enable()`/`set_cmask()` 并发写而误导失败报告（应改为 caller-local 栈结构）、mask header 检查应顺带校验 `alloc_words`、循环应直接以 `nr_cids` 为界。
- **Tejun Heo**：采纳全部意见；最终把 1-2 应用到 `sched_ext/for-7.3-fixes`，1/2 加 Andrea 的 Reviewed-by，2/2 用回复中贴出的 v2（已按 nit 修正）。作者还自测：新 selftest 在 4-CPU VM 上独立跑三次+全套 suite 通过；`scx_qmap` 在 fork churn 下约 55k 次 enable 比对无失配。

## 合入评估
likelihood=merged。Tejun 已应用 1-2 至 `sched_ext/for-7.3-fixes`（cid-form API 属 7.3 未发布接口，改签名无兼容负担）。blocking_issues：无。next_action：随 7.3 周期经 tip 进主线。

## 效果评估
纯 API 修复，无性能数据。自测集中在正确性：55k 次 enable 的掩码比对无失配、selftest 全套通过。cid-form 属未发布接口，对存量用户无影响。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入 tip 分支，随 7.3 进主线），可持续观察后续 cid-form 调度器是否还需要补类似初始状态。

## 参考链接
- lore（v3 cover）: https://lore.kernel.org/all/20260919002838.1960071-1-tj@kernel.org/
- lore（v1）: https://lore.kernel.org/all/c8343c2e457508a6cd3fcab66b0823b6@kernel.org/
- lore（v2）: https://lore.kernel.org/all/2f0eb5c762d55edba5365f1006dbb395@kernel.org/

---
id: sched-20260919-002
date: '2026-09-19'
subject: 'sched_ext: Pass the initial cmask to cid-form ops.enable()'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: '<20260919002838.1960071-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20260919002838.1960071-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v3
patch_series:
  - version: v1
    msgid: '<c8343c2e457508a6cd3fcab66b0823b6@kernel.org>'
    date: '2026-09-19'
    summary: '新增 scx_enable_args，cmask 以内核指针传入 enable()'
    review_outcome: 'Andrea 建议 set_cmask 提前到 set_weight 前、问兼容性、要 selftest'
  - version: v2
    msgid: '<2f0eb5c762d55edba5365f1006dbb395@kernel.org>'
    date: '2026-09-19'
    summary: 'cmask 改为 u64 arena 地址（Sashiko review）'
    review_outcome: '无新异议'
  - version: v3
    msgid: '<20260919002838.1960071-1-tj@kernel.org>'
    date: '2026-09-19'
    summary: 'set_cmask 提前至 set_weight 前，新增 enable_cmask selftest，拆为 2 patch'
    review_outcome: 'Andrea 给 1/2 Reviewed-by，2/2 三个 nit；Tejun 修正后应用至 for-7.3-fixes'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '已合入 sched_ext/for-7.3-fixes，随 7.3 周期进主线'
contribution_opportunities: []
generated_at: '2026-09-20T09:00:00'
source_email_count: 11
related_articles: []
tags:
  - sched_ext
---