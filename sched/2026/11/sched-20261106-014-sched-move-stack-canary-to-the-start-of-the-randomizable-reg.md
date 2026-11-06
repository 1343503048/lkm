# sched: move stack_canary to the start of the randomizable region

## TL;DR

RISC-V 的 task_struct 增长导致 per-task stack canary 偏移超界、构建失败的修复（把 `stack_canary` 挪到「可随机化区域」的起始处），今天被 Valentin Schneider 再次推动：他替社区「ping」Peter 与 Ingo，请他们收取该补丁，并评估了唯一替代方案（加一条 LUI 指令拉伸 RISC-V 立即数），认为「有点浪费但当下可接受，等更聪明的人给出 RISC-V 专属改进」。补丁历经 Ruidong Tian（5 月 v1）与 Charles Mirabile（8 月 v2）两版，一直未入主线。

## 背景与问题

`task_struct` 随时间不断增大。在那些「从 asm-offsets.h 计算 per-task stack canary 偏移、经 `-mstack-protector-guard-offset=` 传给编译器」的架构上，这个增长最终会把 `stack_canary` 推出目标 ISA 能编码的范围。RISC-V 上 canary load 被发射为 `ld t0, TSK_STACK_CANARY(tp)`，`TSK_STACK_CANARY` 必须落在 12 位有符号立即数 [-2048, 2047] 内；一旦 `stack_canary` 越过 byte 2047，构建直接失败（`cc1: error: '<N>' is not a valid offset in '-mstack-protector-guard-offset='`）。Charles Mirabile 在 CKI 构建里撞上了这一失败。

## 技术方案

把 `stack_canary` 从 `task_struct` 尾部挪到「可随机化区域」的起始处，使其偏移重新落回 RISC-V 可编码范围。Valentin 评估的替代方案是在 RISC-V 上加一条 LUI 指令拉伸立即数、把偏移超出 2k 的部分接上，但认为「有点浪费」，不如先采用本补丁，等架构层面出现 scaled immediate offsets 或更聪明的 RISC-V 专属方案。

## 版本演进与当前进展

*current_version: v2（2026-08-21 发出，Charles Mirabile）*。v1 为 Ruidong Tian 2026-05-09 发出。今日 Valentin Schneider 回帖推动合入（Peter/Ingo），无新代码版本。

## Maintainer 意见与讨论焦点

Valentin Schneider（redhat）明确支持：「Peter, Ingo, do you think you could take this?」，并认为补丁「现在这样就可以了」。Peter/Ingo 当日未回复。无 NAK。

## 合入评估

*likelihood=high*。修复目标明确（RISC-V 构建失败）、有 CKI 实际构建验证、Valentin 支持，仅差 Peter/Ingo 收取。*blocking_issues*：① 无 sched 维护者最终响应；② 需确认挪动 stack_canary 不影响其它架构的偏移假设。*next_action*：Peter/Ingo 收取或明确表态。

## 效果评估

效果为「RISC-V 构建恢复」，Charles 在 CKI 构建（build 1639782）实际撞上并确认该修复方向。无量化性能数据（纯布局调整）。

## 我可以参与的点

- **review**：核对 stack_canary 挪动对其它用 `-mstack-protector-guard-offset=` 的架构（arm64、x86 等）偏移是否有连带影响。
- **testing**：在 RISC-V 工具链上确认修复后 task_struct 增长到任何位置都能编译通过。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20260821171127.1061494-1-cmirabil@redhat.com/
- Valentin 今日回帖: https://lore.kernel.org/all/xhsmh1p8you64.mognet@vschneid-thinkpadt14sgen2i.remote.csb/

---
id: sched-20261106-014
date: 2026-11-06
subject: "sched: move stack_canary to the start of the randomizable region"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260821171127.1061494-1-cmirabil@redhat.com>"
lore_url: "https://lore.kernel.org/all/20260821171127.1061494-1-cmirabil@redhat.com/"
authors: [Ruidong Tian, Charles Mirabile]
maintainers_involved: [Valentin Schneider]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260509035014.2220372-1-tianruidong@linux.alibaba.com>"
    date: 2026-05-09
    summary: "把 stack_canary 挪到可随机化区域起始，修复 RISC-V 偏移超界构建失败。"
    review_outcome: "未获取到 v1 评审记录。"
  - version: v2
    msgid: "<20260821171127.1061494-1-cmirabil@redhat.com>"
    date: 2026-08-21
    summary: "v2（Charles Mirabile），CKI 构建实际撞上该失败。"
    review_outcome: "Valentin 今日支持并 ping Peter/Ingo 收取。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "无 sched 维护者最终响应"
    - "需确认不影响其它架构的偏移假设"
  next_action: "Peter/Ingo 收取或明确表态"
contribution_opportunities:
  - kind: review
    description: "核对 stack_canary 挪动对其它 -mstack-protector-guard-offset 架构的偏移影响"
  - kind: testing
    description: "RISC-V 工具链上验证 task_struct 增长到任意位置都能编译"
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [riscv]
---