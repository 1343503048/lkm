---
id: sched-20260911-007
subject: 'selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260910233303.1063501-1-ziyang.meme@gmail.com>
lore_url: https://lore.kernel.org/all/20260910233303.1063501-5-ziyang.meme@gmail.com/
authors:
- Ziyang Men
maintainers_involved: []
current_version: v5
patch_series:
- version: v5
  msgid: <20260910233303.1063501-1-ziyang.meme@gmail.com>
  date: 2026-09-11
  summary: 4/4：以共享 lib.bpf.mk 替换 sched_ext 自维护 BPF 构建机制（Makefile 26+/123-），成为第三个 in-tree
    消费者。
  review_outcome: bpf CI AI review 两条非 bug 建议（裁掉 BPF_GEN_SUBSKEL、保留原注释动机）；人类维护者当日无表态。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - bot 两条建议（subskel 裁剪、注释措辞）待作者取舍
  - 系列其余补丁评审状态未入缓存，未获取到
  next_action: 等作者回应 bot 建议与后续版本；关注 sched_ext 树收取情况
contribution_opportunities:
- kind: review
  description: 核对转换后 skeleton API 与生成路径不变；评估裁掉 BPF_GEN_SUBSKEL 的可行性
- kind: new_patch
  description: 如确认无 subskel 消费者，提交移除 BPF_GEN_SUBSKEL 的后续补丁
generated_at: '2026-09-14T11:35:00'
source_email_count: 2
related_articles:
- sched-20260909-011
tags:
- sched_ext
title: 'selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk'
layout: article
---

## TL;DR
Ziyang Men 的 v5 系列第 4 补丁当日入缓存：用共享的 tools/testing/selftests/lib.bpf.mk 替换 sched_ext 自维护的约 130 行 libbpf/bpftool/skeleton 构建机制，并收到 bpf CI 的 AI review 两条非 bug 建议（subskel 生成可否裁掉、保留原注释的动机说明）。本文为增量更新，该系列在 09-09 已有覆盖（sched-20260909-011）。

## 背景与问题
sched_ext selftests 的 Makefile 自带一整套 BPF 构建机制：libbpf 静态库编译、bpftool 构建、vmlinux.h 生成、BPF 对象编译、skeleton/subskeleton 生成，约 130 行。该机制与 selftests/cgroup、selftests/hid 已迁到的共享片段 lib.bpf.mk 重复，三处维护成本高、行为易漂移。

## 技术方案
- 引入 `include ../lib.bpf.mk`，声明 `BPF_SRCS`/`BPF_SKEL_EXT`/`BPF_GEN_SUBSKEL` 与输出目录变量（BPF_OBJ_DIR、BPF_SKEL_DIR），保留原 build/ 目录布局；
- 所有生成的 skeleton/subskeleton 保持相同公共 API，runner 的构建与链接方式不变；
- Makefile 净减 97 行（26+/123-）。

## 版本演进与当前进展
*current_version: v5（v5 cover msgid `<20260910233303.1063501-1-ziyang.meme@gmail.com>`，由 4/4 补丁的 In-Reply-To 落实；4/4 于 09-11 07:33 入缓存）*。本日缓存仅含 4/4 与 bot 回评，系列其余补丁未入缓存。v5 之前的演进承 sched-20260909-011（早期版本曾按 review 迭代，本次缓存窗口内未获取到 1-3/4 的差异说明）。

## Maintainer 意见与讨论焦点
- **bot+bpf-ci（AI review，非人类维护者）**：两条「不是 bug 但值得考虑」：(1) 生成的 `*.bpf.subskel.h` 在目录里没有任何 .c/.h 消费（pre-patch 规则也生成它们，行为等价保留），问是否可作为后续补丁去掉 `BPF_GEN_SUBSKEL` 以省每个调度器一次 bpftool 运行；(2) 替换后丢掉了原注释里「为什么每个 testcase 依赖全部 BPF prog」的动机说明，建议保留原措辞。CI run 摘要：kernel-patches/bpf actions run 34573210499。
- 人类维护者（Eduard Zingerman/Mykola Lysenko 为 Suggested-by）当日缓存内无新表态；sched_ext 树维护者（Tejun）未入场。分歧未获取到。

## 合入评估
*likelihood=unknown*：方向有 Suggested-by 背书、且 cgroup/hid 两个先例在先，但 4/4 之后的版本演进与维护者表态在缓存中不可见。*blocking_issues*：bot 两条建议待作者取舍（尤其 subskel 裁剪会改变生成物集合）；系列其余补丁的评审状态未获取到。*next_action*：等作者对两条 bot 建议的回应与后续版本；关注 sched_ext 树是否收整套系列。

## 效果评估
可量化的是构建面变化：Makefile -97 行、sched_ext 成为 lib.bpf.mk 第三个 in-tree 消费者。运行时行为（skeleton API、runner 链接）声明保持不变，无 benchmark 类数据；AI review 确认「This isn't a bug」。

## 我可以参与的点
- kind=review：独立核对转换后 skeleton/subskeleton 的公共 API 与生成路径确实不变，并评估 bot 提出的「去掉 BPF_GEN_SUBSKEL」是否值得做（若无消费者，裁掉可省每调度器一次 bpftool 调用）。
- kind=new_patch：如采纳裁剪建议，可提交移除 BPF_GEN_SUBSKEL 的后续小补丁。

## 参考链接
- v5 4/4 补丁：https://lore.kernel.org/all/20260910233303.1063501-5-ziyang.meme@gmail.com/
- bpf CI AI review 回帖：https://lore.kernel.org/all/c51a056670cea30c7fb85ed0ef80a6be9b7e538196a5ae53cbad3b374db70c2c@mail.kernel.org/
- CI run 摘要：https://github.com/kernel-patches/bpf/actions/runs/34573210499
- v5 cover：未获取到（未入当日缓存，msgid 取自 In-Reply-To）
