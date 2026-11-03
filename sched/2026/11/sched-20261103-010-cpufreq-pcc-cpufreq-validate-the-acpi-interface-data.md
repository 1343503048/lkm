# cpufreq: pcc-cpufreq: validate the ACPI interface data

## TL;DR

Kang Chen 为 PCC cpufreq 驱动补 ACPI 接口数据校验：`pcc_get_offset()` 不检查 PCCP 包元素个数就读 `elements[0]/[1]`，且把 64 位值截断成 u32 当字节偏移未校验映射大小；PCCH 与 `_OSC` 应答也有类似越界读。修复加元素个数/buffer 长度/映射大小校验。单补丁，当日无人回帖。

## 背景与问题

`drivers/cpufreq/pcc-cpufreq.c` 中：`pcc_get_offset()` 读 PCCP 包的 `elements[0]`、`elements[1]` 而不检查包是否有两个元素（零元素包越界解引用 `elements[0]`，单元素包越界读 `elements[1]`），并把返回的 64 位值截成 u32 当字节偏移、未校验 ioremap 映射大小——恶意/畸形固件 PCCP 方法可让驱动清写映射区外地址。`pcc_cpufreq_evaluate()` 读 PCCH 包 `elements[0..3]`、`pcc_cpufreq_do_osc()` 读 `_OSC` buffer 的两个 u32，均未检查包计数/buffer 长度。`Fixes: 0f1d683fb35d`。

## 技术方案

要求 PCCP 为两元素包；偏移以 u64 保留并对映射大小校验后才存 u32；同时校验 PCCH 包计数、两个资源 buffer 长度、最小 PCCH 映射大小、`_OSC` buffer 长度（+37/−8）。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103114109.74400-1-k.chen@smail.nju.edu.cn）*。当日无回帖。

## Maintainer 意见与讨论焦点

无表态。

## 合入评估

*likelihood=unknown*。属固件输入健壮性/安全修复，方向正确，但刚发出、无 review，且属 drivers/cpufreq 而非核心调度。

## 效果评估

无测试数据；作者描述的是越界读/写风险（恶意固件触发），未见复现报告。

## 我可以参与的点

- review：核对 u64→u32 截断点与所有 `pcc_get_offset()`/`pcc_cpufreq_evaluate()` 调用路径是否都被校验覆盖。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103114109.74400-1-k.chen@smail.nju.edu.cn/

---
id: sched-20261103-010
date: 2026-11-03
subject: "cpufreq: pcc-cpufreq: validate the ACPI interface data"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261103114109.74400-1-k.chen@smail.nju.edu.cn>"
lore_url: "https://lore.kernel.org/all/20261103114109.74400-1-k.chen@smail.nju.edu.cn/"
authors: [Kang Chen]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103114109.74400-1-k.chen@smail.nju.edu.cn>"
    date: 2026-11-03
    summary: "PCCP/PCCH/_OSC 应答加元素个数、buffer 长度、映射大小校验。"
    review_outcome: "刚发出，暂无 review。"
upstream_commit: null
fixes_commit: "0f1d683fb35d"
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: "等 cpufreq 维护者（Rafael/Viresh）review。"
contribution_opportunities:
  - kind: review
    description: "核对 u64→u32 截断点与所有越界读路径是否被覆盖。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [cpufreq]
---