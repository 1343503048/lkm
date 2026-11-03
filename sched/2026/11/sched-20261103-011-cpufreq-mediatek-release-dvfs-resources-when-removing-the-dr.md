# cpufreq: mediatek: Release DVFS resources when removing the driver

## TL;DR

Wentao Liang 为 mediatek cpufreq 驱动补 `remove` 回调，在解绑/卸载时释放 probe 保留的时钟/regulator/OPP 等 DVFS 资源，避免 list 仍指向被 devm 释放的内存与资源泄漏。Krzysztof Kozlowski 强烈否定：系列疑似 AI 批量生成、未测试，属「hostile patch bombing」。

## 背景与问题

`mtk_cpufreq_probe()` 注册驱动并保留时钟、regulator、OPP 表与 notifier 到 `dvfs_info_list`，但没有 platform remove 回调在设备解绑/模块卸载时撤销；devm 分配的 DVFS 信息被释放后 list 与驱动仍引用，同时泄漏保留资源。`Fixes: 89b56047f6f9`，Cc stable。

## 技术方案

新增 `mtk_cpufreq_remove()`：`cpufreq_unregister_driver()` 后遍历 `dvfs_info_list` 逐个 `mtk_cpu_dvfs_info_release()` 并 `list_del()`，与 probe 失败路径一致（+13 行）。

## 版本演进与当前进展

*current_version: v1（2026-11-03 发出，msgid 20261103063609.1028187-1-vulab@iscas.ac.cn）*。当日 Krzysztof Kozlowski 回帖否定。

## Maintainer 意见与讨论焦点

Krzysztof Kozlowski 严厉批评（同日对 pxa 补丁发了一模一样的回复）：1) 团队多次无视先前反馈；2) 同一邮件用多个身份，怀疑不是真人；3) 机器人连 checkpatch 都不跑；4) 无复现无测试；5) 多个独立补丁撒向多个子系统，明显 AI 生成且大概率未测试；不按 patchset 组织、让评审困难。「到了 hostile patch 的边缘……先读 kernel 文档再说」。

## 合入评估

*likelihood=low*。补丁本身方向合理，但作者被维护者认定为 AI 批量、未测试、未正确组织，需先回应流程质疑并按规范重投。

## 效果评估

无测试数据（作者未测试，维护者点名指出）。

## 我可以参与的点

- 当前阶段暂无明显参与空间；作者需先按内核文档修复提交流程（checkpatch、patchset 组织、Assisted-by 标注、真实测试）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261103063609.1028187-1-vulab@iscas.ac.cn/

---
id: sched-20261103-011
date: 2026-11-03
subject: "cpufreq: mediatek: Release DVFS resources when removing the driver"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261103063609.1028187-1-vulab@iscas.ac.cn>"
lore_url: "https://lore.kernel.org/all/20261103063609.1028187-1-vulab@iscas.ac.cn/"
authors: [Wentao Liang]
maintainers_involved: [Krzysztof Kozlowski]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261103063609.1028187-1-vulab@iscas.ac.cn>"
    date: 2026-11-03
    summary: "新增 mtk_cpufreq_remove() 释放 DVFS 资源。"
    review_outcome: "Krzysztof 强烈否定：AI 批量、未测试、未按 patchset 组织。"
upstream_commit: null
fixes_commit: "89b56047f6f9"
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["维护者认定 AI 批量/未测试/组织混乱"]
  next_action: "按内核文档修复提交流程后重投。"
contribution_opportunities: []
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [cpufreq]
---