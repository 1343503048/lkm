---
id: sched-20260728-008
date: 2026-07-28
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: null
authors: [Guopeng Zhang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: 2026-07-17
    summary: "修复 PSI trigger 在 32 位架构上的两处溢出：时间转换 u32 乘法和长窗口增长插值乘法"
    review_outcome: "Tao Cui 回复确认问题存在，讨论修复方案细节"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["尚未获得 maintainer Ack"]
  next_action: "等待 PSI maintainer (Johannes Weiner) review"
contribution_opportunities:
  - kind: testing
    description: "在 32 位 ARM 平台上验证 PSI trigger 配置大窗口（>4s）时的行为是否正确"
  - kind: review
    description: "检查 mul_u64_u64_div_u64() 在极端参数下的精度损失"
generated_at: "2026-07-30T10:00:00"
source_email_count: 2
related_articles: []
tags: [psi]
---

## TL;DR

PSI（Pressure Stall Information）trigger 机制在 32 位架构上存在两处整数溢出 bug，导致用户配置的大阈值/窗口（如 4s/6s）被截断为错误值，trigger 监控行为与预期不符。目前 v1 已发出并有社区成员确认问题，等待 maintainer review。

## 背景与问题

PSI trigger 允许用户通过 `/proc/pressure/*` 配置阈值（threshold_us）和窗口（window_us），内核据此判断是否触发压力事件。这两个参数为 u32 类型（微秒），内部转换为纳秒存储。

**问题一（Patch 2/2）**：`threshold_us * NSEC_PER_USEC` 在 32 位架构上使用 32 位无符号算术计算。当 threshold=4,000,000us、window=6,000,000us 时，window 的纳秒值 6,000,000,000 超出 u32 范围，截断为 1,705,032,704ns（约 1.7s），导致存储的窗口比阈值还短，trigger 逻辑完全失效。

**问题二（Patch 1/2）**：`window_update()` 中剩余时间 `remaining` 存为 u32，10 秒窗口经过 2 秒后剩余 8,000,000,000ns 被截断。即使改为 u64，`prev_growth * remaining` 的乘积仍可能超出 U64_MAX（两者均可接近 10^10）。

影响范围：所有 32 位架构（ARM32、x86 等）上配置较大 PSI trigger 窗口的场景。64 位架构不受影响。

## 技术方案

**Patch 2/2（时间转换溢出）**：在乘法前将 threshold_us 和 window_us 显式 cast 为 u64，确保 `NSEC_PER_USEC` 乘法在 64 位宽度下完成。

**Patch 1/2（长窗口插值溢出）**：
- 将 `remaining` 字段从 u32 改为 u64
- 使用 `mul_u64_u64_div_u64()` 替代直接乘除，避免中间乘积溢出

设计取舍：`mul_u64_u64_div_u64()` 内部使用 128 位中间运算（在支持 __int128 的架构上）或分解为多步运算，有少量性能开销，但 window_update 调用频率极低（每个 trigger 周期一次），不构成问题。

## 版本演进与当前进展

- **v1**（2026-07-17 发出）：首次提交 2-patch 系列，修复上述两处溢出。
- 2026-07-28：Tao Cui 回复两封邮件，确认问题存在并讨论修复细节。

当前处于 v1 under_review 阶段。

## Maintainer 意见与讨论焦点

- Tao Cui（社区成员）回复确认了问题的真实性，对修复方向无异议。
- 尚未看到 PSI maintainer Johannes Weiner 或 Peter Zijlstra 的回复。
- 暂无明确争议点，修复方案较为直接。

## 合入评估

修复方案清晰、影响范围明确（仅 32 位），属于典型的 correctness fix。合入可能性中等偏高，主要取决于：
- Johannes Weiner 是否认可 `mul_u64_u64_div_u64()` 的使用（vs 其他避免溢出的方式）
- 是否需要补充 Fixes: tag 指向引入问题的原始 commit

当前卡在等待 maintainer review。

## 效果评估

邮件中给出了具体的溢出数值示例（4s threshold → 正确存储 4,000,000,000ns；6s window → 错误截断为 1,705,032,704ns），但未提供修复前后的运行时测试数据。属于逻辑正确性修复，效果可通过配置大窗口 trigger 并观察 `/proc/pressure/*/triggers` 的存储值来验证。

## 我可以参与的点

- 在 32 位 ARM 平台（如 Raspberry Pi）上配置 PSI trigger（threshold=4s, window=6s），验证修复前后 trigger 行为差异，将测试结果回帖到邮件列表
- 检查 `mul_u64_u64_div_u64()` 在不支持 __int128 的 32 位架构上的实现路径是否有额外边界问题
- 如果熟悉 PSI 代码，可以帮忙补充 Fixes: tag 并确认是否有 stable backport 需求

## 参考链接

- lore thread: 未获取到
- 原始 patch 发送日期: 2026-07-17
