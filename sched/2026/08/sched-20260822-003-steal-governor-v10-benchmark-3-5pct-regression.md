## TL;DR

steal_governor v10 系列收到 Yury 的独立测试：steal ratio 成功收敛，但整体性能比基线差 3-5%。作者需要调查性能回退原因。

## 背景与问题

steal_governor 为虚拟化环境引入 preferred CPUs 和 steal-driven vCPU backoff 机制，允许 vCPU 在检测到 steal time 过高时主动让出 CPU。v10 是第 10 个版本。

## 技术方案

通过 steal ratio 监控动态调整 vCPU 行为，在 overcommit 场景下优化整体吞吐。

## 版本演进与当前进展

v10 讨论中。Yury Norov 在笔记本上运行了独立测试（4 VMs × 8 vCPUs on 8 pCPUs）：

- **Steal governor off**: 总吞吐 49460，steal% ~75%
- **Steal governor on**: 总吞吐 47941（-3.1%），steal% ~6%

Steal ratio 成功收敛到阈值内，但吞吐下降 3-5%。Yury 怀疑自己可能配置有误，请求 Shrikanth Hegde 验证。

## Maintainer 意见与讨论焦点

Yury 的测试结果显示性能回退，这是合入的主要障碍。Yury 建议系列应包含测试脚本。

## 合入评估

- **likelihood**: low
- **blocking_issues**: 3-5% 性能回退需要解释和修复
- **next_action**: 作者需要调查性能回退原因，可能需要调整算法参数

## 效果评估

| 配置 | 总吞吐 | 平均 steal% |
|------|--------|-------------|
| governor off | 49460 | ~76% |
| governor on | 47941 | ~6% |

Steal ratio 收敛成功，但吞吐下降 3-5%。Yury 指出结果与作者之前报告的数据差异较大，可能配置有误。

## 我可以参与的点

- 在不同虚拟化环境（KVM/Xen）下复现测试，确认性能回退是否普遍
- 分析 steal governor 算法中可能导致吞吐下降的路径
- 帮助优化测试脚本，确保测试条件一致

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260812054033.95658-1-sshegde@linux.ibm.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260822-003
date: 2026-08-22
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20260812054033.95658-1-sshegde@linux.ibm.com>"
lore_url: "https://lore.kernel.org/lkml/20260812054033.95658-1-sshegde@linux.ibm.com/"
authors: ["Shrikanth Hegde"]
maintainers_involved: ["Yury Norov"]
current_version: v10
patch_series:
  - version: v10
    msgid: "<20260812054033.95658-1-sshegde@linux.ibm.com>"
    date: 2026-08-12
    summary: "v10 preferred CPUs + steal-driven vCPU backoff"
    review_outcome: "Yury 独立测试显示 3-5% 性能回退"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "3-5% 性能回退需要解释和修复"
  next_action: "作者调查性能回退原因"
contribution_opportunities:
  - kind: testing
    description: "在不同虚拟化环境下复现测试确认性能回退"
  - kind: review
    description: "分析 steal governor 算法中导致吞吐下降的路径"
generated_at: "2026-08-22T10:00:00"
source_email_count: 2
related_articles: []
tags: ["steal_governor", "virtualization", "performance"]
---
