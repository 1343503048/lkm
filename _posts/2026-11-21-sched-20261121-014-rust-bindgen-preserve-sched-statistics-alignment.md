---
id: sched-20261121-014
date: '2026-11-21'
subject: 'rust: bindgen: Preserve sched_statistics alignment'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261120-fix-schedstats-bindgen-layout-v2-1-1c42e4a996ae@gmail.com>
lore_url: https://lore.kernel.org/all/20261120-fix-schedstats-bindgen-layout-v2-1-1c42e4a996ae@gmail.com/
authors:
- Peder Bergan
maintainers_involved:
- Miguel Ojeda
current_version: v2
patch_series:
- version: v1
  msgid: <20261119-fix-schedstats-bindgen-layout-v1-1-0599dd230ffd@gmail.com>
  date: '2026-11-19'
  summary: --opaque-type sched_statistics 保对齐
  review_outcome: Miguel 认可 workaround，要求改 Cc stable 写法与注释
- version: v2
  msgid: <20261120-fix-schedstats-bindgen-layout-v2-1-1c42e4a996ae@gmail.com>
  date: '2026-11-20'
  summary: 补 padding 变更说明、bindgen bug 链接、stable 6.12.x、credit 报告/测试者、扩 Binder Cc
  review_outcome: Miguel 要求注释改通用措辞
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 注释改为通用措辞
  next_action: 作者微调注释后由 Miguel/Tricca 收取
contribution_opportunities:
- kind: review
  description: 确认 opaque 不破坏未来字段访问需求，核对 6.12.x 的 bindgen 版本影响
generated_at: '2026-11-22T01:00:00+08:00'
source_email_count: 91
related_articles:
- sched-20261120-012
tags:
- sched_debug
title: 'rust: bindgen: Preserve sched_statistics alignment'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-012-rust-bindgen-preserve-sched-statistics-alignment.html">sched-20261120-012</a>：Peder Bergan 发 v1 修 Rust bindgen 布局 bug——`CONFIG_SCHEDSTATS=n` 时空结构体 `struct sched_statistics` 被 bindgen 丢掉对齐，导致 `task_struct.mm` 等字段错位（arm64 上报错位到 1168 vs C 的 1208），Rust Binder 经 `CurrentTask::mm()` 读错指针、`mmap()` 返 -EINVAL；Miguel Ojeda review 并建议改 Cc stable 写法与注释措辞。
- <a class="article-ref" href="/lkm/2026/11/21/sched-20261121-014-rust-bindgen-preserve-sched-statistics-alignment.html">sched-20261121-014</a>（今天）：**v2 发出**——补充 bindgen 0.73.2 padding 变更如何暴露该问题、链接 bindgen bug、请求 stable 6.12.x 回退、credit Jules Mercier 报告与 OnePlus 6T 测试、扩大 Binder Cc 名单；另自查发现 bindgen 0.73.1 下 `task_struct.se` 也有 offset 错位。Miguel 再回复：其建议的注释应写成通用措辞（不点名 sched_statistics）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/20/sched-20261120-012-rust-bindgen-preserve-sched-statistics-alignment.html">sched-20261120-012</a>）`CONFIG_SCHEDSTATS` 关闭时 `sched_statistics` 是空结构体但仍 cache-line 对齐；bindgen 0.73.2 生成空定义时丢弃对齐、且不在 over-aligned 字段前补显式 padding，后续字段整体前移。Rust Binder 由此读错 `task_struct.mm`。Rust 无代码直接访问该类型字段，故设 opaque 无副作用。

## 技术方案

单补丁 `rust/bindgen_parameters`：加 `--opaque-type sched_statistics`，使 bindgen 用 C 的 size/alignment（不展开空结构体）。v2 保持 opaque 规则无条件（按前次讨论），并补充：bindgen 0.73.1 下 `task_struct.se` 也有 offset 错位；arm64 6.12.y + bindgen 0.73.2 + schedstats 关时，`task_struct.pid` offset 从 1208 移到 1216 与 C 一致。

## 版本演进与当前进展

*current_version: v2（2026-11-20 发出，`<20261120-fix-schedstats-bindgen-layout-v2-1-1c42e4a996ae@gmail.com>`，单补丁）*。v1 → v2：补 padding 变更说明、bindgen bug 链接、stable 6.12.x 请求、credit 报告/测试者、扩 Binder Cc 名单。当日收到 Miguel 对 v2 的回复。

## Maintainer 意见与讨论焦点

- **Miguel Ojeda（Rust-for-Linux 维护者）**：澄清其前次建议的注释应写成通用措辞（未来可能往列表加更多 case），而非点名 `sched_statistics`；并寄望 bindgen 的 bug 尽快修复。
- **Jules Mercier**：Reported-by + Tested-by（arm64 布局不匹配报告者，OnePlus 6T 测试）。
- 无 NAK；方向认可，剩余只是注释措辞微调。

## 合入评估

*likelihood=high*。Rust 侧维护者认可为合理 workaround，仅剩注释措辞微调；改动局限于 bindgen 参数文件。*blocking_issues*：按 Miguel 意见把注释改通用措辞。*next_action*：作者微调注释后由 Miguel/Tricca 收取。

## 效果评估

作者给出 arm64 布局数据（offset 1168→1208、pid 1208→1216 与 C 对齐、两种 config 一致），并说明 Rust Binder `mmap()` 的 -EINVAL 因读错 `mm` 指针。无性能数据。

## 我可以参与的点

- **review**：确认 `--opaque-type sched_statistics` 不破坏未来对 `sched_statistics` 内字段的（潜在）访问；核对 6.12.x 的 Rust bindgen 版本是否同样受影响。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261120-fix-schedstats-bindgen-layout-v2-1-1c42e4a996ae@gmail.com/
- Miguel 对 v2 的回复: https://lore.kernel.org/all/CANiq72k3e5ko2vA26Dy2GmVW+8Ja2xmzPydX8w@mail.gmail.com/
