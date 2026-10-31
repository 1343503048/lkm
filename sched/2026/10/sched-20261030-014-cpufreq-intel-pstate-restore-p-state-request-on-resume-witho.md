# cpufreq: intel_pstate: Restore P-state request on resume without HWP

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261027-015：Zak Brighton Knight 报告并修 intel_pstate 被动模式 resume 缺陷——无 HWP 的 Ivy Bridge（ThinkPad T520/i7-3840QM，coreboot）每次 suspend-to-RAM 后 turbo 永久丢失（停在 2.8GHz 基频直到改 policy 或重启），根因是 resume 时固件把 `MSR_IA32_PERF_CTL` 设回基频、内核因缓存/`policy->cur` 跳过重写。
- sched-20261029-015：Doug Smythies 给 **Tested-by**，实测 Zak 的 V2 与 Rafael 的补丁都正常，但未 review 代码。
- sched-20261030-014（今天）：Rafael 复盘——该补丁被 AI 查出问题，且不能照原设想改（至少 userspace governor 依赖跨 suspend-resume 保留 `policy->cur`），但存在「在 `__cpufreq_driver_target()` 里强制驱动回调、即便 `policy->cur` 等于新目标频率」的可行路径（resume 时可用）；Rafael 决定**拆开补丁、等 AI 满意后另发一套正式系列**。Zak 表示随时可测新补丁。

## 背景与问题
（承接 20261027-015 → 20261029-015）无 HWP 时 intel_pstate 缓存最后一次写入的 P-state、跳过不变写入；被动模式下 cpufreq core 因 `policy->cur` 认为频率已设而跳过请求，resume 后固件把 P-state 请求寄存器设回基频 ratio（28）、内核不再写回 turbo ratio（38）。今日新增约束：userspace governor 依赖 `policy->cur` 跨 suspend-resume 保留，使「直接复写 P-state」的原始做法不可行。

## 技术方案
（承接 v1/v2，今日方向调整）Rafael 提出的可行路径：在 `__cpufreq_driver_target()` 里于 resume 阶段**强制触发驱动回调**，即便 `policy->cur` 已等于新目标频率——绕开「跳过不变写入」的缓存判断。具体实现细节 Rafael 未在正文展开，他明确会「split the patch and submit a proper series when the AI is happy with it」，即以放大/拆分的形式重新提交，而非沿用 Zak 的单补丁。

## 版本演进与当前进展
*current_version: v2（Zak 的补丁形态，今日被 Rafael 决定重构另发）*。Zak 的 V2 + Rafael 的补丁均获 Doug 实测通过，但 Rafael 认定原始实现有缺陷，转由自己拆分重新成串提交。

## Maintainer 意见与讨论焦点
- **Rafael Wysocki（cpufreq maintainer）**：确认 AI 发现问题、userspace governor 的 `policy->cur` 依赖是硬约束，给出「resume 时强制驱动回调」的新方向，并将亲自拆分重发。
- **Zak Brighton Knight（作者）**：接受现状，表示可测试未来补丁。
- **未解决**：新系列的拆分形态与「强制回调」的具体实现尚未落地。

## 合入评估
*likelihood=medium*。维护者亲自接手、方向明确，合入概率不低；但仍需 Rafael 另发正式系列并过 AI/review 一关，原 Zak 单补丁已不会被按原样合入。*blocking_issues*：等 Rafael 拆分的正式系列提交并通过 review。*next_action*：Rafael 发新系列，Zak 测试反馈。

## 效果评估
Doug Smythies 此前实测 Zak V2 与 Rafael 补丁均「工作正常」，turbo 可在 resume 后恢复；无量化性能数字。

## 我可以参与的点
- **testing**：Rafael 发新系列后，在无 HWP 的 Intel 平台上验证 suspend-resume 后 turbo 是否恢复（Zak 已表态可测，可协同）。
- **review**：核对「resume 时强制驱动回调」是否影响 userspace governor 的 `policy->cur` 语义。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261027143725.3763827-1-zakbrightonknight@gmail.com/

---
id: sched-20261030-014
date: 2026-10-30
subject: "cpufreq: intel_pstate: Restore P-state request on resume without HWP"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261027143725.3763827-1-zakbrightonknight@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261027143725.3763827-1-zakbrightonknight@gmail.com/"
authors: [Zak Brighton Knight]
maintainers_involved: [Rafael Wysocki]
current_version: v2
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "等 Rafael 拆分的正式系列提交并通过 review"
  next_action: "Rafael 发新系列，Zak 测试反馈"
contribution_opportunities:
  - kind: testing
    description: "在无 HWP 的 Intel 平台上验证 suspend-resume 后 turbo 恢复"
  - kind: review
    description: "核对 resume 时强制驱动回调是否影响 userspace governor 的 policy->cur 语义"
generated_at: "2026-10-31T09:00:00"
source_email_count: 2
related_articles: [sched-20261027-015, sched-20261029-015]
tags: [cpufreq, x86]
---