# selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk

## TL;DR
Ziyang Men 提交 v3（4/4）「selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk」。把 sched_ext 自带的约 130 行 libbpf/bpftool/vmlinux.h/BPF object/skeleton 构建逻辑替换为共享的 `tools/testing/selftests/lib.bpf.mk`，使 sched_ext 成为第三个使用该片段的树内消费者（继 cgroup、hid）。under_review。

## 背景与问题
sched_ext 的 selftests Makefile 自带约 130 行重复的 libbpf + bpftool + vmlinux.h + BPF object + skeleton 构建机械。这与其它 selftests（cgroup、hid）重复，维护成本高。

## 技术方案
- 删除本地构建机械，改为 `include ../lib.bpf.mk`，沿用现代 `*.bpf.c` 布局、`.bpf.skel.h` 后缀与 subskeleton。
- 保持 28 个 skeleton 与 28 个 sub-skeleton 的公开 API 前后一致，runner 构建/链接方式不变。
- 覆盖 `BPF_CFLAGS`（去掉跨 clang 版本的 `-Werror`，改为保留该目录原 flag 集）与 `EXTRA_CLEAN`。
- 净减约 116 行 Makefile。Suggested-by Eduard Zingerman 与 Mykola Lysenko。

## 版本演进与当前进展
当前 v3（系列 4/4）。8/14 发出。

## Maintainer 意见与讨论焦点
焦点：`BPF_CFLAGS` 覆盖（去掉 `-Werror`）是否会降低构建严格性；API 一致性已确认。

## 合入评估
合入可能性 high。纯构建系统重构，风险低，有维护者建议。

## 效果评估
减少 116 行重复构建逻辑，统一树内 selftests 构建方式；无功能影响。

## 我可以参与的点
- 验证 sched_ext selftests 在 clang 多版本下仍正常构建；
- 评审 `-Werror` 去除的取舍。

## 参考链接
- lore: 未获取到

---
subject: "selftests/sched_ext: build BPF schedulers via the shared lib.bpf.mk"
id: sched-20260814-010
date: 2026-08-14
subsystem: sched
type: cleanup
status: under_review
severity: low
thread_root_msgid: "<20260814155054.scx_selftests_make@ziyang>"
lore_url: "未获取到"
authors: [Ziyang Men]
maintainers_involved: [Tejun Heo, David Vernet, Eduard Zingerman, Mykola Lysenko]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20260814155054.scx_selftests_make@ziyang>"
    date: 2026-08-14
    summary: "v3（4/4）：sched_ext 自带约 130 行 libbpf+bpftool+vmlinux.h+BPF object+skeleton 构建逻辑，替换为包含共享的 tools/testing/selftests/lib.bpf.mk，使 sched_ext 成为继 cgroup、hid 之后第三个使用该片段的树内消费者。28 个 skeleton/sub-skeleton 公开 API 前后一致。"
    review_outcome: "v3 发出，Suggested-by Eduard Zingerman 与 Mykola Lysenko。Makefile 减 116 行。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 scx/selftests 维护者接受构建系统重构。"
contribution_opportunities:
  - kind: review
    description: "评审 BPF_CFLAGS 覆盖（去掉 -Werror 跨 clang 版本）是否影响构建严格性。"
  - kind: testing
    description: "在 sched_ext selftests 下验证 28 个 skeleton 构建/链接与运行一致。"
generated_at: "2026-08-15T00:15:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, selftests]
---
