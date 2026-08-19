# sched/numa: Prevent race on sysctl_numa_balancing static key

# sched/numa: 修复 sysctl_numa_balancing 静态键切换竞态


## TL;DR
`sched/numa` 修复 `sysctl_numa_balancing` 静态键切换时的抢占竞态（UAF / use-after-uninit），附 syzkaller C repro 与 Fixes 标签。问题真实且有复现，合入可能性高。

## 背景与问题
NUMA_BALANCING 通过 `jump_label`(static_key) 在 sysctl 写时切换。切换静态键本身需要特定的上下文约束，但相关代码在修改期间**未禁止抢占**。若抢占点在 static key 释放/重分配后、后续 `if` 读取该键对应内存之前发生，会读到已释放或未初始化的内存，构成 use-after-free / use-after-uninitialized。这是一条可被 syzkaller 稳定复现的竞态。

## 技术方案
在 static key 切换处加抢占保护，并保证 static key 写入与后续读取之间的顺序，使「是否启用 NUMA balancing」的判断总是在一致的内存视图下进行。作者以「least surprise」原则认为这是比「仅移动写位置」更合理的改法。邮件标注 `Fixes: 6604b3a6b7ba`（引入该 sysctl 静态键切换的原始提交）。

## 版本演进与当前进展
v1（2026-08-03），作者 Chen Jinghuang（华为）。附完整的 syzkaller C repro 与 KASAN/KCSAN 风格报告。`Fixes` 标签指向 2013 年前后的原始提交，说明这是一个长期存在的低频竞态。

## Maintainer 意见与讨论焦点
邮件中尚未出现 maintainer 回复（v1 刚发）。从内容看改法保守，且有 Fixes 标签与 repro，预期无方向性反对。需注意点与 Mel Gorman（NUMA 维护者）的反馈。

## 合入评估
合入可能性 high。有可复现 race + Fixes 标签 + 保守改法，是典型「应该被快速接收」的 bug 修复。

## 效果评估
邮件提供 syzkaller 复现与 KASAN/KCSAN 报告作为效果证据，属「有实证」的 bug 修复。无性能基准（也不应有，是稳定性修复）。

## 我可以参与的点
- 用作者提供的 syzkaller C repro 在内核开启 KASAN/KCSAN 下复现，打补丁后验证竞态消失，回帖「tested-by」式验证数据（恰是作者邮件未附 runs 的缺口）。

## 参考链接
- lore thread: 未获取到

---
subject: "sched/numa: Prevent race on sysctl_numa_balancing static key"
id: sched-20260803-006
date: 2026-08-03
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Chen Jinghuang]
maintainers_involved: [Peter Zijlstra, Mel Gorman, Andrew Morton]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "sysctl 通过 jump_label 切换 NUMA_BALANCING 静态键，但 static_key 修改期间未禁止抢占，存在 use-after-free/use-after-uninit 风险（后续 if 读取已被释放/未初始化内存）。提供 syzkaller C repro，标注 Fixes: 6604b3a6b7ba。"
    review_outcome: "作者自审(principle of least surprise)认为抢占保护与 static-key 写入顺序更合理；邮件附 Fixes 标签指向原始引入提交。"
upstream_commit: null
fixes_commit: "6604b3a6b7ba"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 maintainer 对『抢占保护 + static key 写入顺序』改法的认可；有 syzkaller repro 与 Fixes 标签，合入阻力很小。"
contribution_opportunities:
  - kind: testing
    description: "可基于提供的 syzkaller C repro 在使能 KASAN/KCSAN 的内核上复现 race，并验证补丁后不再触发，回帖验证结果。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: []
tags: [numa, sched_debug]
---
