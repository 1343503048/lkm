---
id: sched-20260825-002
date: 2026-08-25
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <cover.1756108800.git.fangqiurong@kylinos.cn>
lore_url: https://lore.kernel.org/r/cover.1756108800.git.fangqiurong@kylinos.cn
authors:
- fangqiurong
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1756108800.git.fangqiurong@kylinos.cn>
  date: 2026-08-25
  summary: 'RFC: 用 per-CPU 变量替代 rq->nr_pinned 的 generated offset 访问方式，删除 rq-offsets.c'
  review_outcome: 暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 sched maintainer 对 per-CPU 方案的反馈
contribution_opportunities:
- kind: review
  description: 用 objdump 验证修改前后的 codegen 确实一致并回帖确认
generated_at: '2026-08-27T10:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_debug
title: 'sched: Replace nr_pinned offset hack with a dedicated per-CPU counter'
layout: article
---

## TL;DR

Qiurong Fang 发出 RFC，用简单的 per-CPU 变量替代 `rq->nr_pinned` 的 generated offset 访问方式，消除 `rq-offsets.c`、Kbuild 规则和全局生成头文件。这是纯代码清理，不修复 bug，删除 53 行、新增 6 行。

## 背景与问题

commit 378b7708194f 将 `migrate_{en,dis}able()` 内联到 `include/linux/sched.h`，但此时 `struct rq` 不完整，无法直接访问 `rq->nr_pinned`。当时的解决方案是通过生成的 offset 常量 + `arch_raw_cpu_ptr()` 间接访问，引入了：
- `kernel/sched/rq-offsets.c`（专用偏移量计算）
- Kbuild 规则生成 `include/generated/rq-offsets.h`
- `sched.h` 中的全局 `#include <generated/rq-offsets.h>`

这套机制被原始作者评为"four options weighed in the 2025-07 bpf-next discussion"中"least ugly"的选择，但本质上仍是一个 hack。

## 技术方案

RFC 提出的替代方案：
- `nr_pinned` 变为普通 per-CPU 变量 `rq_nr_pinned`
- 写入用 `__this_cpu_inc()`/`__this_cpu_dec()`（调用点已 preempt-disabled，codegen 不变）
- 读取用 `per_cpu_ptr()` + `READ_ONCE()`（唯一的 hotplug reader）
- 删除 `rq-offsets.c`、Kbuild 规则、`generated/rq-offsets.h` include

关键设计点：code generation 和运行时行为不变，模块导出的 wrapper 函数保留。

## 版本演进与当前进展

v1（RFC），刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无。RFC 阶段，等待社区反馈。

## 合入评估

- **likelihood: medium** — 纯清理，逻辑等价，但涉及 `include/linux/sched.h` 和 Kbuild 的改动需要 maintainer 认可
- **blocking_issues**: 无
- **next_action**: 等待 sched maintainer 对 per-CPU 方案的反馈；如果 Peter 认为 offset 方式仍有必要（例如为未来的 BPF 场景），可能被拒

## 效果评估

作者明确表示 codegen 不变（"same plain RMW codegen as the open-coded access"），无性能影响。暂无效果数据。

## 我可以参与的点

- **review codegen**：可以用 `objdump` 验证修改前后的 codegen 确实一致，回帖确认
- 当前阶段暂无明显参与空间，可持续观察后续版本

## 参考链接

- lore thread: https://lore.kernel.org/r/cover.1756108800.git.fangqiurong@kylinos.cn
- 原始讨论: https://lore.kernel.org/bpf/CAADnVQ+5sEDKHdsJY5ZsfGDO_1SEhhQWHrt2SMBG5SYyQ+jt7w@mail.gmail.com/
- tip-bot commit: 未获取到
