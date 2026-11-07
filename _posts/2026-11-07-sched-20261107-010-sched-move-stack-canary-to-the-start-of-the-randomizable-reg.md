---
id: sched-20261107-010
date: '2026-11-07'
subject: 'sched: move stack_canary to the start of the randomizable region'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260821171127.1061494-1-cmirabil@redhat.com>
lore_url: https://lore.kernel.org/all/20261106160730.GJ1779021@noisy.programming.kicks-ass.net/
authors:
- Ruidong Tian
- Charles Mirabile
maintainers_involved:
- Peter Zijlstra
- Valentin Schneider
current_version: v2
patch_series:
- version: v2
  msgid: <20260821171127.1061494-1-cmirabil@redhat.com>
  date: '2026-08-21'
  summary: 把 stack_canary 挪到可随机化区域起始，修复 RISC-V 偏移超界构建失败
  review_outcome: Peter 提出结构化 thread_info + asm-offsets 替代方案，原方向需重做
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需按 Peter 的结构化方案（thread_info + asm-offsets）重写
  - 需补 12 位立即数限制注释并确认其它架构不受影响
  next_action: 作者基于 Peter 的方案实现 v3 并重跑 RISC-V 构建验证
contribution_opportunities:
- kind: extend
  description: 按 Peter 的 thread_info + asm-offsets 方向动手实现 v3
- kind: review
  description: 核对 canary 入 thread_info 对其它用 guard-offset 的架构的影响
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261106-014
tags:
- riscv
title: 'sched: move stack_canary to the start of the randomizable region'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-014-sched-move-stack-canary-to-the-start-of-the-randomizable-reg.html">sched-20261106-014</a>：RISC-V 的 task_struct 增长导致 per-task stack canary 偏移超界、构建失败的修复（把 `stack_canary` 挪到「可随机化区域」起始处），被 Valentin Schneider 再次推动：替社区 ping Peter 与 Ingo 请他们收取，并评估了唯一替代方案。补丁历经 Ruidong Tian（5 月 v1）与 Charles Mirabile（8 月 v2）两版，一直未入主线。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-010-sched-move-stack-canary-to-the-start-of-the-randomizable-reg.html">sched-20261107-010</a>（今天）：**Peter Zijlstra 回帖「这样显得特别随意，且极易随着 task_struct 进一步改动而再次随机断裂」**，给出一个更结构化的替代方案（RISC-V 侧导出 per-arch 的 canary 偏移——`asm-offsets.c` 生成 `TSK_STACK_CANARY`、thread_info 里放 canary、stackprotector.h 直接用该符号），并另补一句「这个应该在某个地方注释一下 12 位立即数的限制」。方向从「挪到可随机化区起始」转为「按 arch 结构化解偏移」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-014-sched-move-stack-canary-to-the-start-of-the-randomizable-reg.html">sched-20261106-014</a>）`task_struct` 增长最终会把 `stack_canary` 推出 RISC-V 的 12 位有符号立即数 [-2048, 2047] 范围，`-mstack-protector-guard-offset=` 编译失败（Charles Mirabile 在 CKI 构建撞上）。

今日 Peter 对现有补丁方案的批评：把字段「随机地」挪到可随机化区域起始是脆弱的——task_struct 每再改一次就可能又推出去，只是把问题推迟；他主张用结构化方式让偏移由 arch 自己控制。

## 技术方案

（承接）原补丁：把 `stack_canary` 从 task_struct 尾部挪到「可随机化区域」起始。

Peter 今日给出的替代 diff（6 文件 +20/-10）：

- `arch/riscv/include/asm/thread_info.h`：把 `stack_canary` 放进 thread_info（per-task、紧邻栈），而不是塞在 task_struct 末尾。
- `arch/riscv/include/asm/stackprotector.h`：`boot_init_stack_canary()` 直接用 thread_info 里的 canary 字段。
- `arch/riscv/kernel/asm-offsets.c`：生成 `TSK_STACK_CANARY` 偏移符号，供 `-mstack-protector-guard-offset=` 使用——这样编译器取 canary 的偏移由 arch 的 asm-offsets 决定，天然落在可控范围内，task_struct 怎么改都不再牵连。
- `include/linux/sched.h` / `kernel/fork.c` / `drivers/misc/lkdtm/bugs.c`：相应调整字段位置与访问。

Peter 另在回帖末尾补一句「This should probably have a comment about 12 bit immediates somewhere」，即需要显式注释 12 位立即数这一架构限制。

## 版本演进与当前进展

*current_version: v2（2026-08-21 发出，Charles Mirabile）*。今日 Peter Zijlstra 给出结构化替代方案，无新版本补丁；原 v2 方向需按新方案重构。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**（sched/core 维护者）：不认可「挪到可随机化区域起始」的随机性，「Why not do something a little more structured; like so?」并给出把 canary 移入 thread_info + asm-offsets 的结构化 diff；补充需注释 12 位立即数限制。
- **Valentin Schneider**（前日）：支持修复方向并 ping Peter/Ingo 收取。

无 NAK；Peter 的反对是「实现方式不够结构化」，而非「不该修」。

## 合入评估

*likelihood=medium*。修复目标（RISC-V 构建失败）无争议、有 CKI 实据，但 Peter 要求按结构化方案（thread_info + asm-offsets）重做，原方向被否。*blocking_issues*：① 需按 Peter 的结构化 diff 重写并验证；② 需补 12 位立即数限制注释；③ 重写后需确认不破坏其它用 `-mstack-protector-guard-offset=` 的架构。*next_action*：作者基于 Peter 的 thread_info + asm-offsets 方案重写补丁并重跑 RISC-V 构建验证。

## 效果评估

效果为「RISC-V 构建恢复」，无量化性能数据（纯布局调整）。Charles 在 CKI 构建（build 1639782）实际撞上并确认方向；Peter 的结构化方案未附构建/性能数据。

## 我可以参与的点

- **extend**：按 Peter 的 thread_info + asm-offsets 方案实现并验证 RISC-V 构建（这本身是 Peter 明确给好的方向，适合直接动手发 v3）。
- **review**：核对把 canary 移入 thread_info 是否影响 arm64/x86 等其它用 `-mstack-protector-guard-offset=` 的架构的偏移假设，以及 12 位立即数注释是否覆盖全部受影响点。

## 参考链接

- lore thread（Peter 结构化方案）: https://lore.kernel.org/all/20261106160730.GJ1779021@noisy.programming.kicks-ass.net/
- lore thread（Peter 补注立即数）: https://lore.kernel.org/all/20261106161428.GC1922751@noisy.programming.kicks-ass.net/
- lore thread（v2）: https://lore.kernel.org/all/20260821171127.1061494-1-cmirabil@redhat.com/
