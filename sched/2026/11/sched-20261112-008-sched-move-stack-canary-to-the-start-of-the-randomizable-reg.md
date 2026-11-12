# sched: move stack_canary to the start of the randomizable region

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-014：RISC-V 的 task_struct 增长导致 per-task stack canary 偏移超界、构建失败（把 `stack_canary` 挪到「可随机化区域」起始处），被 Valentin Schneider 再次推动；补丁历经 Ruidong Tian（5 月 v1）与 Charles Mirabile（8 月 v2）未入主线。
- sched-20261107-010：Peter Zijlstra 否掉「挪到可随机化区起始」，给出结构化替代方案（RISC-V 侧 per-arch canary 偏移：`asm-offsets.c` 生成 `TSK_STACK_CANARY`、thread_info 放 canary）。
- sched-20261109-014：Valentin Schneider 落地 Peter 的方案，发新补丁 `riscv, sched: move stack_canary to thread_info`。
- sched-20261112-008（今天）：**Ron Economos 给出 Tested-by**（RISC-V + gcc 16 + `CONFIG_SCHED_CLASS_EXT=y` 的构建失败被修复、真机可启动）；**Peter Zijlstra 补上自己的 Signed-off-by**，并指出这补丁「是不是走丢了、要不要重发」，倾向于让它走 RISC-V 的 tree（因为问题实际出现在 RISC-V 上）。

## 背景与问题

（承接 sched-20261106-014 / 20261107-010 / 20261109-014）RISC-V 上 per-task stack canary 用 asm-offsets.h 计算偏移并传给编译器 `-mstack-protector-guard-offset=`，其 `TSK_STACK_CANARY` 必须 fit 进 12 位有符号立即数（[-2048,2047]）。task_struct 持续增长，一旦 `stack_canary` 越过 byte 2047 构建即失败。今日 Ron Economos 报告其实际命中：gcc 16 + `CONFIG_SCHED_CLASS_EXT=y` 下构建失败（gcc 14 不失败），且 Valentin 的 thread_info 补丁在 gcc 16 下能构建并真机启动。

## 技术方案

（承接）Valentin 的结构化方案：把 RISC-V 的 `stack_canary` 移到 `thread_info` 并引入访问宏，规避 task_struct 增长带来的 12 位立即数越界。今日无代码变化，为测试与维护者背书进展。

## 版本演进与当前进展

*current_version: v1（新方案，2026-11-09，`<xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb>`）*。今日无新版本；补丁获得 RISC-V 实机 Tested-by，Peter 补上 Signed-off-by（此前署名链里 Peter 为 Not-signed-off-by），并讨论补丁的收取路径。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：补上 Signed-off-by，并问「它们是不是走丢了？需要重发吗？我在想这也许应该走它们的 tree，因为确实是它们那边在碰到这个问题」——即倾向由 RISC-V 维护者（Palmer 等）经 RISC-V tree 收取，而非 sched tree。
- **Ron Economos（测试者）**：Tested-by，并把 RISC-V folks 重新加进 Cc。
- 无 NAK。方向已被 Peter 预先背书（本补丁即按他的建议实现），分歧仅在「走哪条 tree 收取」。

## 合入评估

*likelihood=medium*。方案已获 Peter Signed-off-by 与 RISC-V 实机 Tested-by，方向正确；但需 RISC-V 侧维护者确认并决定收取路径（Peter 倾向走 RISC-V tree）。*blocking_issues*：补丁可能需重发至 RISC-V 维护者；RISC-V 侧尚未正式表态收取。*next_action*：Valentin 将补丁重发/直接递给 RISC-V 维护者，由其经 RISC-V tree 收取。

## 效果评估

Ron 报告：RISC-V + gcc 16 + `CONFIG_SCHED_CLASS_EXT=y` 构建失败（gcc 14 不失败），Valentin 的补丁在 gcc 16 下能构建并真机启动正常。属结构性构建修复，无运行时 perf 数据。

## 我可以参与的点

- **testing**：在 RISC-V 交叉编译（不同 gcc 版本 14/15/16）+ `CONFIG_STACKPROTECTOR_PER_TASK=y` 下确认 `TSK_STACK_CANARY` 不再越界、构建通过。
- **review**：核对 `thread_info` 方案在 `THREAD_INFO_IN_TASK` 各配置下访问宏的偏移计算正确性。

## 参考链接

- lore thread: https://lore.kernel.org/all/xhsmhy0b2ntmh.mognet@vschneid-thinkpadt14sgen2i.remote.csb/
- Ron 的 Tested-by: https://lore.kernel.org/all/34f2ff11-8156-4c32-91dc-e4576807cf3b@w6rz.net/
- Peter 的 Signed-off 与收取路径讨论: https://lore.kernel.org/all/20261112153427.GV1779021@noisy.programming.kicks-ass.net/

---
id: sched-20261112-008
date: '2026-11-12'
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
    review_outcome: "Ron Tested-by；Peter 补 Signed-off-by 并倾向走 RISC-V tree"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["补丁可能需重发至 RISC-V 维护者", "RISC-V 侧尚未正式表态收取"]
  next_action: "Valentin 重发/递交给 RISC-V 维护者经 RISC-V tree 收取"
contribution_opportunities:
  - kind: testing
    description: "RISC-V 多 gcc 版本交叉编译确认构建通过"
  - kind: review
    description: "核对 thread_info 访问宏在 THREAD_INFO_IN_TASK 各配置下的偏移计算"
generated_at: "2026-11-13T09:00:00+08:00"
source_email_count: 2
related_articles: [sched-20261106-014, sched-20261107-010, sched-20261109-014]
tags: [riscv, preempt]
---