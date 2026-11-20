# sched_ext: reject oversized dispatch_max_batch

## TL;DR

Sechang Lim 发单补丁：`bpf_scx_init_member()` 接受大到 INT_MAX 的 `dispatch_max_batch`，其决定 per-CPU dispatch buffer 大小，但 `__alloc_percpu()` 拒绝超过 `PCPU_MIN_UNIT_SIZE` 的分配——带 `BPF_F_LINK` 时超大值过 struct_ops 校验、link 创建时触发非法尺寸告警后才 `-ENOMEM`。补丁在 map update 阶段即按有效 batch 算出 buffer 尺寸并拒绝超限（`-E2BIG`）。v1→v2 仅按 Andrea Righi 意见加 braces。小修复、带 Fixes tag。

## 背景与问题

`bpf_scx_init_member()` 对 `dispatch_max_batch` 只检查 `> INT_MAX` 就放行，但该值实际决定 per-CPU dispatch buffer（`struct scx_sched_pcpu` 内 `dsp_ctx.buf`）的大小。`__alloc_percpu()` 能分配的上限是 `PCPU_MIN_UNIT_SIZE`，于是超大值在 struct_ops map update 时通过校验、到 link 创建时才报「非法尺寸」告警并 `-ENOMEM`，报错点远离真正的取值入口，且注册（无 link）路径也不覆盖。

## 技术方案

v2（`kernel/sched/ext/ext.c`，+9/-3）：用「有效 batch 数」（`dispatch_max_batch` 为 0 时取默认 `SCX_DSP_DFL_MAX_BATCH`）算出 buffer 尺寸，`struct_size_t(struct scx_sched_pcpu, dsp_ctx.buf, nr) > PCPU_MIN_UNIT_SIZE` 时在 map update 阶段直接 `-E2BIG`，比进 allocator 更早更清晰；同时覆盖无 link 的注册路径。v1→v2：按 Andrea Righi 意见给 case 加 braces。

## 版本演进与当前进展

*current_version: v2（2026-11-20，`<20261120065559.3979434-1-rhkrqnwk98@gmail.com>`，单补丁）*。v1（`<20261120054913.3795562-1-rhkrqnwk98@gmail.com>`）→ v2（加 braces）。作者系首次提交（Sechang Lim），经 Andrea Righi 评审。

## Maintainer 意见与讨论焦点

- **Andrea Righi（sched_ext 共同维护者）**：v1 仅要求加 braces；v2 回应后无进一步异议。
- 无 NAK；小修复、`Fixes: f0e1a0643a59`、`Signed-off-by` 齐全，方向无争议。

## 合入评估

*likelihood=high*。单补丁边界校验修复、维护者已实质 review（仅格式意见）、带 Fixes tag，符合收尾路径。*blocking_issues*：无实质阻塞，等维护者收取。*next_action*：Tejun/Andrea 收取进 sched_ext 分支。

## 效果评估

无性能数据。效果是错误处理前移：超大 `dispatch_max_batch` 在 map update 阶段即被 `-E2BIG` 拒绝，而非 link 创建时才报非法尺寸告警/`-ENOMEM`（作者主观描述，无测试数据）。

## 我可以参与的点

- **review**：核对 `struct_size_t(...) > PCPU_MIN_UNIT_SIZE` 的比较语义（是否应含可能的对齐/头部开销），确认 `SCX_DSP_DFL_MAX_BATCH` 默认值的覆盖路径无误。
- **testing**：构造一个 `dispatch_max_batch` 接近/超过 `PCPU_MIN_UNIT_SIZE` 的 BPF 调度器，验证两种路径（link 与无 link 注册）的报错时机与错误码。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261120065559.3979434-1-rhkrqnwk98@gmail.com/
- v1: https://lore.kernel.org/sched-ext/20261120054913.3795562-1-rhkrqnwk98@gmail.com/T/#u

---
id: sched-20261120-007
date: '2026-11-20'
subject: "sched_ext: reject oversized dispatch_max_batch"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261120065559.3979434-1-rhkrqnwk98@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261120065559.3979434-1-rhkrqnwk98@gmail.com/"
authors: [Sechang Lim]
maintainers_involved: [Andrea Righi]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261120054913.3795562-1-rhkrqnwk98@gmail.com>"
    date: '2026-11-20'
    summary: "map update 阶段按有效 batch 拒绝超 PCPU_MIN_UNIT_SIZE 的 dispatch_max_batch"
    review_outcome: "Andrea Righi 要求加 braces"
  - version: v2
    msgid: "<20261120065559.3979434-1-rhkrqnwk98@gmail.com>"
    date: '2026-11-20'
    summary: "加 braces，无其它改动"
    review_outcome: "待收取"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Tejun/Andrea 收取进 sched_ext 分支"
contribution_opportunities:
  - kind: review
    description: "核对 struct_size_t > PCPU_MIN_UNIT_SIZE 的比较语义与覆盖路径"
  - kind: testing
    description: "构造超限 dispatch_max_batch 验证 link/无 link 两路径报错时机与错误码"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: []
tags: [sched_ext]
---