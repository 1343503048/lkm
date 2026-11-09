# sched: move stack_canary to the start of the randomizable region

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-014：RISC-V 的 task_struct 增长导致 per-task stack canary 偏移超界、构建失败的修复（把 `stack_canary` 挪到「可随机化区域」起始处），被 Valentin Schneider 再次推动（替社区 ping Peter 与 Ingo）。补丁历经 Ruidong Tian（5 月 v1）与 Charles Mirabile（8 月 v2）两版未入主线。
- sched-20261107-010：Peter Zijlstra 回帖「这样显得特别随意，且极易随 task_struct 进一步改动再次随机断裂」，给出结构化替代方案（RISC-V 侧 per-arch canary 偏移：`asm-offsets.c` 生成 `TSK_STACK_CANARY`、thread_info 放 canary）。
- sched-20261109-014（今天）：**Valentin Schneider 落地 Peter 的结构化方案**，发新补丁 `riscv, sched: move stack_canary to thread_info`——把 RISC-V 的 `stack_canary` 移到 thread_info 并引入访问宏，彻底规避 task_struct 增长带来的 12 位立即数越界。

## 背景与问题

（承接 sched-20261106-014 / 20261107-010）RISC-V 上 per-task stack canary 用 asm-offsets.h 计算出偏移并传给编译器 `-mstack-protector-guard-offset=`，其 `TSK_STACK_CANARY` 必须fit 进 12 位有符号立即数（[-2048,2047]）。task_struct 持续增长，一旦 `stack_canary` 越过 byte 2047，构建即失败（`cc1: error: '<N>' is not a valid offset`）。此前「挪到可随机化区域起始」被 Peter 否掉（太随意、易随 task_struct 再断裂）。

## 技术方案

Valentin 的新补丁采用 Peter 建议的结构化方案：把 RISC-V 的 `stack_canary` 移到 `thread_info`（RISC-V 上 `CONFIG_STACKPROTECTOR_PER_TASK` 依赖 `!RANDSTRUCT`，故 stack_canary 不因在 task_struct 随机化区而获益），引入一个访问宏指向正确的 stack_canary 位置，其他架构不受影响。涉及 `arch/riscv/include/asm/{stackprotector.h,thread_info.h}`、`arch/riscv/kernel/asm-offsets.c` 等。作者署名链：Ruidong Tian 与 Peter Zijlstra 标记 "Not-signed-off-by"（未正式签名）、Valentin Schneider 为 Signed-off-by。

## 版本演进与当前进展

*current_version: v1（新方案，2026-11-09，`<xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb>`）*。方向从「挪到可随机化区起始」正式切换为「移到 thread_info + 访问宏」（Peter 的结构化建议），补丁当日发出，署名链保留 Ruidong Tian 与 Peter 的贡献。

## Maintainer 意见与讨论焦点

无当日新回帖。此前 Peter Zijlstra 明确否定「挪到可随机化区起始」并给出结构化替代方案（本补丁即按此实现），属方向已被维护者预先背书。潜在待跟进：Peter 曾提「12 位立即数限制应在某处注释」；署名里 Ruidong/Peter 为 Not-signed-off-by，需作者补齐确认。

## 合入评估

*likelihood=medium*。新方案沿 Peter 给的结构化路径，方向正确且规避了 task_struct 增长的脆弱性；但涉及 RISC-V 架构代码，需 RISC-V 侧（Palmer Dabbelt 等）审阅。*blocking_issues*：① 无当日评审；② 署名链（Not-signed-off-by）待理顺；③ 需 RISC-V 侧确认。*next_action*：Peteter/Ingo 与 RISC-V 侧审阅后收取。

## 效果评估

无量化数据；修复价值为使 RISC-V per-task stack canary 不再随 task_struct 增长而构建失败（结构性问题，非运行时 perf）。

## 我可以参与的点

- **review**：核对 `thread_info` 方案在 RISC-V 的 `THREAD_INFO_IN_TASK` 各配置下的正确性（访问宏的偏移计算）。
- **testing**：在 RISC-V 交叉编译 + `CONFIG_STACKPROTECTOR_PER_TASK=y` 下确认 `TSK_STACK_CANARY` 不再越界、构建通过。

## 参考链接

- Valentin 的新补丁: https://lore.kernel.org/all/xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb/

---
id: sched-20261109-014
date: '2026-11-09'
subject: "sched: move stack_canary to the start of the randomizable region"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb>"
lore_url: "https://lore.kernel.org/all/xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb/"
authors: [Valentin Schneider, Ruidong Tian]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb>"
    date: '2026-11-09'
    summary: "把 RISC-V stack_canary 移到 thread_info 并引入访问宏（Peter 的结构化方案）"
    review_outcome: "沿用 Peter 预先背书的方案，无当日回帖"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "无当日评审；署名链待理顺；需 RISC-V 侧确认"
  next_action: "Peter/Ingo 与 RISC-V 侧审阅后收取"
contribution_opportunities:
  - kind: review
    description: "核对 thread_info 方案在 THREAD_INFO_IN_TASK 各配置下的偏移计算正确性"
  - kind: testing
    description: "RISC-V 交叉编译 + CONFIG_STACKPROTECTOR_PER_TASK=y 确认构建通过"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261106-014, sched-20261107-010]
tags: [riscv, preempt]
---