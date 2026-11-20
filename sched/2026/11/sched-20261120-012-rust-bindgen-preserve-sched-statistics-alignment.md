# rust: bindgen: Preserve sched_statistics alignment

## TL;DR

Peder Bergan 发单补丁修 Rust bindgen 布局 bug：`CONFIG_SCHEDSTATS=n` 时空结构体 `struct sched_statistics` 被 bindgen 丢掉对齐，导致其上 `task_struct.mm` 等字段错位（arm64 上报错位到 1168 vs C 的 1208），Rust Binder 经 `CurrentTask::mm()` 读错指针、`mmap()` 返 `-EINVAL`。补丁把 `sched_statistics` 设为 opaque 使 bindgen 采用 C 的尺寸/对齐。Miguel Ojeda review 并建议改 Cc stable 写法与注释措辞。

## 背景与问题

`CONFIG_SCHEDSTATS` 关闭时 `sched_statistics` 是空结构体但仍 cache-line 对齐；bindgen 0.73.2 生成空定义时丢弃该对齐，且不在 over-aligned 字段前补显式 padding，于是后续字段整体前移。Jules Mercier 在 arm64 上报：`task_struct.mm` 偏移 1168（C）vs 1208（正确），Rust Binder 由此 `CurrentTask::mm()` 读错指针、`mmap()` 返 -EINVAL。Rust 无任何代码直接访问该类型字段，故设 opaque 无副作用。

## 技术方案

单补丁 `rust/bindgen_parameters`（+4 行）：加 `--opaque-type sched_statistics`，使 bindgen 用 C 的 size/alignment（不展开空结构体）。作者给数据：改后 layout 与 C 一致（1168→1208）、`CONFIG_SCHEDSTATS=y` 也一致，Rust kernel crate 与 Binder 两种 config 下 Clippy 均通过。`Fixes: 313c4281bc9d`、`Closes: Rust-for-Linux/linux#1269`。

## 版本演进与当前进展

*current_version: v1（2026-11-19 发出、11-20 收件，`<20261119-fix-schedstats-bindgen-layout-v1-1-0599dd230ffd@gmail.com>`，单补丁）*。首版，Miguel Ojeda 当日给出两轮 review。

## Maintainer 意见与讨论焦点

- **Miguel Ojeda（Rust-for-Linux 维护者）**：确认这是 bindgen 0.73.2 独有的 bug（请作者确认）；建议 `Cc: stable@vger.kernel.org # 6.12.x (Rust is pinned in older LTSs)` 而非普通 Cc stable；注释建议写清「bindgen 丢弃空结构体对齐、0.73.2 不补显式 padding」及要 debug Kconfig 开关启用 layout 测试（独立补丁）。
- **Jules Mercier**：Reported-by（arm64 布局不匹配报告者）。
- 无 NAK；作为临时 workaround「可接受」，方向认可。

## 合入评估

*likelihood=high*。Rust 侧维护者认可为合理 workaround、仅要求改 Cc stable 写法与注释；改动局限于 bindgen 参数文件。*blocking_issues*：按 Miguel 意见调整 Cc stable 行与注释措辞。*next_action*：作者按意见改注释/Cc 后重发，由 Miguel/Tricca 收取。

## 效果评估

作者给出 arm64 布局数据（offset 1168→1208 对齐、两种 config 均一致），并说明 Rust Binder `mmap()` 的 -EINVAL 因读错 `mm` 指针。无性能数据。

## 我可以参与的点

- **review**：确认 `--opaque-type sched_statistics` 不破坏其它 Rust 绑定对 `sched_statistics` 内字段的（潜在）未来访问需求；核对 6.12.x 的 Rust bindgen 版本是否同样受影响。

## 参考链接

- lore thread（patch）: https://lore.kernel.org/all/20261119-fix-schedstats-bindgen-layout-v1-1-0599dd230ffd@gmail.com/

---
id: sched-20261120-012
date: '2026-11-20'
subject: "rust: bindgen: Preserve sched_statistics alignment"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261119-fix-schedstats-bindgen-layout-v1-1-0599dd230ffd@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261119-fix-schedstats-bindgen-layout-v1-1-0599dd230ffd@gmail.com/"
authors: [Peder Bergan]
maintainers_involved: [Miguel Ojeda]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261119-fix-schedstats-bindgen-layout-v1-1-0599dd230ffd@gmail.com>"
    date: '2026-11-19'
    summary: "--opaque-type sched_statistics 保对齐"
    review_outcome: "Miguel 认可 workaround，要求改 Cc stable 写法与注释"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["调整 Cc stable 行与注释措辞"]
  next_action: "作者改注释/Cc 后重发，由 Miguel 收取"
contribution_opportunities:
  - kind: review
    description: "确认 opaque 不破坏未来字段访问需求，核对 6.12.x 的 bindgen 版本影响"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: []
tags: [sched_debug]
---