---
id: sched-20261019-006
subject: '[tip:sched/core 35/37] ld.lld: error: relocation refers to a symbol in a
  discarded section: __UNIQUE_ID_addressable_overflowuid_553'
date: 2026-10-19
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <629C00D8-BEF2-4B35-A056-2D8699F355FD@gmail.com>
lore_url: https://lore.kernel.org/all/629C00D8-BEF2-4B35-A056-2D8699F355FD@gmail.com/
authors:
- Jemmy Wong
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等 LLVM/LLD 侧确认 ELF32 符号索引回绕处理，或 tip 侧规避 i386+lld 构建
contribution_opportunities:
- kind: discussion
  description: 跟进 LLVM/LLD 的 ELF32 重定位符号索引回绕修复
generated_at: '2026-10-20T01:30:00'
source_email_count: 1
related_articles: []
tags:
- x86
title: '[tip:sched/core 35/37] ld.lld: error: relocation refers to a symbol in a discarded
  section: __UNIQUE_ID_addressable_overflowuid_553'
layout: article
---

## TL;DR

kernel test robot 此前对 `tip:sched/core` 分支 35/37（`sched/cache: Avoid publishing partial LLC utilization` 一带）报 lld 链接错误「relocation refers to a symbol in a discarded section」。今日 Jemmy Wong 复现并定位为 **ELF32 符号索引 24 位溢出** 的 toolchain 问题——在不含该 sched 补丁的祖先 commit 上同样失败，与调度补丁无关。

## 背景与问题

ktest robot 在 `tip:sched/core` 分支构建（i386 + lld）时报 `ld.lld: error: relocation refers to a symbol in a discarded section: __UNIQUE_ID_addressable_overflowuid_553`。需判断是 tip 分支某 sched 提交引入，还是 toolchain 固有缺陷。

## 技术方案

Jemmy 用 Clang/LLD 23.1.3 在三个 commit 上复现：fcceb7da9465（`sched/cache: Avoid publishing partial LLC utilization`）、其父 96a494c9cfd8、更早祖先 840e23085b03（`Merge branch 'tip/sched/urgent'`），均同样失败。三个 vmlinux.o 的符号数分别为 21,371,209 / 21,370,053 / 21,370,091，超过 ELF32 重定位的 24 位符号索引上限。抽查 840e23085b03 里 `basic_stm_init` initcall 的重定位：编码符号索引 1,427,711 指向无关 `.L0` label，加 2^24 后才是 `basic_stm_init`——证明是符号索引回绕。结论：需在 ELF32 重定位处理侧修复，与 sched 补丁无关（不含补丁的本地构建同样失败）。

## 版本演进与当前进展

非补丁系列，为 ktest 构建报告的排查跟进。今日为第三方（Jemmy）的复现与归因回复，暂无维护者回应。

## Maintainer 意见与讨论焦点

无维护者表态。Jemmy 的结论为调度补丁免责，问题归到 LLVM/LLD 的 ELF32 重定位处理。

## 合入评估

*likelihood=unknown*。属构建工具链问题而非补丁合入决策；对 `tip:sched/core` 分支的 i386+lld 构建有影响，但根因在 toolchain。*blocking_issues*：无（对 sched 补丁本身不构成阻塞）。*next_action*：等 lld/LLVM 侧确认 ELF32 符号索引回绕处理，或 tip 侧对 i386 构建配置做规避。

## 效果评估

Jemmy 给出三个 commit 的符号数（均 ~2137 万，超 2^24=16,777,216）与 `basic_stm_init` 重定位索引回绕证据（1,427,711 vs 18,204,927）。无性能数据。

## 我可以参与的点

- `discussion`：在 LLVM/LLD 侧跟进 ELF32 重定位符号索引回绕的修复，或确认 tip 分支 i386 构建是否需要规避。

## 参考链接

- Jemmy 回帖：https://lore.kernel.org/all/629C00D8-BEF2-4B35-A056-2D8699F355FD@gmail.com/
- 原始 ktest 报告：https://lore.kernel.org/all/202610170544.6hPndDUW-lkp@intel.com/
