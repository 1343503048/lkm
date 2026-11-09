---
id: sched-20261109-013
date: '2026-11-09'
subject: 'sched_ext selftest enable_cmask fails to load on 7.4-rc2: verifier rejects
  arena pointer cast from scx_enable_args.cmask_arena_addr'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <6af1e5f2.a438010f.130489.ab94@mx.google.com>
lore_url: https://lore.kernel.org/all/6af1e5f2.a438010f.130489.ab94@mx.google.com/
authors:
- Zhijian Han
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无人响应；需 BPF/verifier 与 sched_ext 共同定性
  next_action: 等 Tejun / BPF verifier 维护者定位
contribution_opportunities:
- kind: review
  description: 核对 verifier 对 addr_space_cast 在 7.4 merge window 的变化
- kind: new_patch
  description: 补 selftest 侧修复：显式 addr_space_cast 或改用 struct_ops 直接 __arena 参数
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext selftest enable_cmask fails to load on 7.4-rc2: verifier rejects
  arena pointer cast from scx_enable_args.cmask_arena_addr'
layout: article
---

## TL;DR

Zhijian Han 报告 sched_ext 的 enable_cmask selftest（merge window 经 `d781d1b78acf` 加入）在 v7.4-rc2 与 linux-next-20261105 上加载失败：BPF verifier 拒绝 `struct scx_cmask __arena *m = (struct scx_cmask __arena *)args->cmask_arena_addr;` 这处「u64 承载的 arena 地址」转型——C cast 不产生 `addr_space_cast` insn，成员加载产出 `R7=scalar()` 并一路保持 scalar，首次解引用 `m->base` 被拒（`R8 invalid mem access 'scalar'`）。7.4 merge window 中 verifier 侧 arena 处理变化疑似不再接受此模式。当日无人回帖。

## 背景与问题

`struct scx_enable_args.cmask_arena_addr` 以 `u64` 承载 arena 指针（文档要求 cast 成 `struct scx_cmask __arena *` 再用）。selftest `enable_cmask.bpf.c:101` 照文档写该 cast，但生成字节码中 C cast 不发射 `addr_space_cast` insn，成员 load 得到 scalar 而非 arena 指针，首次解引用即被 verifier 拒绝。同样的 selftest 此前由 Tejun 在 for-7.3-fixes 分支验证通过（16-CPU VM），说明 7.4 merge window 里 verifier 的 arena 处理发生了变化。struct_ops 直接 `__arena` 参数路径（`ops.set_cmask`）仍正常，仅「u64 承载地址」形式受影响。

## 技术方案

当日为报告，无补丁。报告者给出确定性 reproducer（defconfig + SCHED_CLASS_EXT、DEBUG_INFO_BTF、FUNCTI...），两次连续运行结果一致，并定位到 insn 级根因（insn 1 的 `r7 = *(u64 *)(r2 + 0)` 产出 `R7=scalar()`，跨 cast 与内联 `check_mask()` 前导后仍为 scalar，insn 94 首次解引用被拒）。可能的修法方向（报告者未给出补丁）：让该转型显式发射 `addr_space_cast`、或调整 selftest 的指针携带方式以匹配 verifier 新行为。

## 版本演进与当前进展

*current_version: null（报告，无补丁）*。2026-11-09 发出，当日无人回帖。

## Maintainer 意见与讨论焦点

当日无维护者回帖。报告者引用 Tejun 此前在 for-7.3-fixes 的验证记录作为「曾被确认可用」的证据。无 NAK、无分歧。

## 合入评估

*likelihood=unknown*。刚报告、无人响应；是 selftest 侧回归还是 verifier 行为回归待定性（涉及 BPF arena verifier 与 sched_ext 的交叉）。*blocking_issues*：① 无人响应；② 需 BPF/verifier 侧与 sched_ext（Tejun）共同判断是修 selftest 还是修 verifier。*next_action*：等 Tejun / BPF verifier 维护者定位。

## 效果评估

复现确定性（两次运行一致）：`libbpf: prog 'enable_cmask_enable': BPF program load failed: -EACCES`，`R8 invalid mem access 'scalar'`。属 selftest 加载失败，非内核运行时崩溃；影响 sched_ext 测试覆盖。

## 我可以参与的点

- **review**：核对 verifier 对 `addr_space_cast` 的处理在 7.4 merge window 的变化（`kernel/bpf/verifier.c` 与 arena 相关），判断是 selftest 该改还是 verifier 回归。
- **new_patch**：若结论是 selftest 侧，补一个「u64 承载 arena 地址的显式 `addr_space_cast`」或改用 struct_ops 直接 `__arena` 参数的修复。

## 参考链接

- lore thread: https://lore.kernel.org/all/6af1e5f2.a438010f.130489.ab94@mx.google.com/
