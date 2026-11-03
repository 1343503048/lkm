---
id: sched-20261103-012
date: 2026-11-03
subject: 'cpufreq: pxa: Release the core clock reference on failure and exit'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261103062843.1020546-1-vulab@iscas.ac.cn>
lore_url: https://lore.kernel.org/all/20261103062843.1020546-1-vulab@iscas.ac.cn/
authors:
- Wentao Liang
maintainers_involved:
- Krzysztof Kozlowski
current_version: v1
patch_series:
- version: v1
  msgid: <20261103062843.1020546-1-vulab@iscas.ac.cn>
  date: 2026-11-03
  summary: pxa_cpu_init 失败/exit 时 clk_put 释放 core clock。
  review_outcome: Krzysztof 强烈否定：AI 批量、未测试、流程不合规。
upstream_commit: null
fixes_commit: d9278077385f
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 维护者认定 AI 批量/未测试/组织混乱
  next_action: 按内核文档修复提交流程后重投。
contribution_opportunities: []
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- cpufreq
title: 'cpufreq: pxa: Release the core clock reference on failure and exit'
layout: article
---

## TL;DR

Wentao Liang 修 pxa2xx cpufreq 驱动的时钟引用泄漏：`pxa_cpu_init()` 在 CPU 不支持或 `cpufreq_register_driver()` 失败时不释放 `clk_get_sys()` 取得的 core clock，exit 路径也持有不放。补丁在失败与 exit 时 `clk_put()`。Krzysztof Kozlowski 强烈否定（与同作者的 mediatek 补丁收到同一封批评）。

## 背景与问题

`pxa_cpu_init()` 用 `clk_get_sys()` 取得 core clock 引用，但不支持的 CPU 及 `cpufreq_register_driver()` 失败都不释放；模块 exit 在注销驱动后仍保持引用。`Fixes: d9278077385f`，Cc stable。作者标注 `Assisted-by: DeepSeek-V4.1-Flash and OpenAI Codex`。

## 技术方案

`drivers/cpufreq/pxa2xx-cpufreq.c` 中：`ret = cpufreq_register_driver()` 后若 `ret` 则 `clk_put(pxa_cpufreq_data.clk_core)`；`pxa_cpu_exit()` 末尾 `clk_put(pxa_cpufreq_data.clk_core)`（+3 行）。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103062843.1020546-1-vulab@iscas.ac.cn）*。当日 Krzysztof Kozlowski 回帖否定。

## Maintainer 意见与讨论焦点

Krzysztof Kozlowski 同日发出与 mediatek 补丁完全相同的批评：多次无视先前反馈、多身份、未跑 checkpatch、未复现未测试、多个独立补丁撒向多个子系统（AI 生成、大概率未测试）、不按 patchset 组织，属「hostile patch bombing」，要求先读 kernel 文档。

## 合入评估

*likelihood=low*。补丁方向正确但被维护者认定为 AI 批量/未测试/流程不合规，需先整改流程。

## 效果评估

无测试数据（作者未测试，维护者点名指出）。

## 我可以参与的点

- 当前阶段暂无明显参与空间；作者需先按内核文档修复提交流程。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103062843.1020546-1-vulab@iscas.ac.cn/
