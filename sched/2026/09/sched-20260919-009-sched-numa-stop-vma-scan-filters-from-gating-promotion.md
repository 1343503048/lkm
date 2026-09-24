# sched/numa: stop VMA scan filters from gating promotion

## TL;DR
增量更新：Gregory Price 的 NUMA tiering 修复系列（v2 4-patch，整体目标是移除 VMA 扫描过滤器对 promotion 的门控）本日在 cover 信层面收到 Zi Yan 的测试范围质询——询问是否用了 numactl 等 NUMA 控制；Gregory 澄清这些修复源于 Joshua 的 tiered memcg limits 补丁测试时发现的"numa balancing 彻底失效"，纯内部一致性问题、不涉及 mempolicy/cpuset。

## 背景与问题
背景见 sched-20260918-013 / sched-20260918-014：NUMA balancing 在 tiering 场景下被 VMA 扫描过滤器错误地阻断 promotion（4/4）与只读文件映射扫描（3/4）两个问题。本日讨论聚焦系列整体的测试范围与问题边界。

## 技术方案
系列方案见 sched-20260918-013/014。本日无方案变更，仅澄清测试覆盖与问题性质。

## 版本演进与当前进展
- v2（2026-09-11，`<20260911001826.2109390-1-gourry@gourry.net>`）：4-patch 系列（见 sched-20260918-013/014）。
- 本日 Zi Yan（`<DLIQQNUL2RTD.IGN8MYHYMW1E@nvidia.com>`）质询测试范围；Gregory Price（`<aq2s9R9I-Y9D3tx_@gourry-fedora-PF4VCD3F>`）回复澄清。

## Maintainer 意见与讨论焦点
- **Zi Yan**：询问工作负载是否只是裸跑、有无 numactl/NUMA policy 配置——想弄清问题 scope 与修复的测试覆盖，建议给出"预期行为列表"供人/AI 对照检查。
- **Gregory Price（作者）**：这些问题是与 Joshua 的 tiered memcg limits 补丁一起测公平性控制时发现的——不同 tier 之间带宽严重偏斜；去掉所有 memcg 扩展单独测这些补丁后，发现 numa balancing 完全失效（始于 Johannes 的 shmem 修复之后）。工作负载没有使用任何其他 NUMA 控制（无 numactl、无 mbind/set_mempolicy、无 cpuset.mems）；修复影响的是 fault 注入侧（PROT_NONE 喷洒）而非 fault 处理侧，故 mempolicy/cpuset 不涉及，属 numa balancing 自身的内部一致性问题。

## 合入评估
*likelihood=medium*。系列方向与测试边界已澄清，但具体 patch（3/4 的 VMA 判定、4/4 的 promo_only 计算）仍各有 review 意见待解决。*blocking_issues*：3/4、4/4 的具体实现意见（见 sched-20260919-008 与 sched-20260918-013）。*next_action*：按 Zi Yan 建议补充"预期行为列表"，推进 3/4、4/4 的重写。

## 效果评估
本日无新增 benchmark。Gregory 描述的现象（tier 间带宽极度偏斜、numa balancing 完全失效）为定性观察，未附具体数字。

## 我可以参与的点
- kind=testing：按 Zi Yan 建议的"预期行为列表"在 NUMA tiering 环境核对各 patch 行为，补充可对照的验证数据。
- kind=review：评估 4-patch 系列对 promotion 门控移除后，是否存在过度 promotion 的回归风险。

## 参考链接
- lore（v2 cover）: https://lore.kernel.org/all/20260911001826.2109390-1-gourry@gourry.net/
- lore（Zi Yan 质询）: https://lore.kernel.org/all/DLIQQNUL2RTD.IGN8MYHYMW1E@nvidia.com/

---
id: sched-20260919-009
date: '2026-09-19'
subject: 'sched/numa: stop VMA scan filters from gating promotion'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260911001826.2109390-1-gourry@gourry.net>'
lore_url: 'https://lore.kernel.org/all/20260911001826.2109390-1-gourry@gourry.net/'
authors:
  - 'Gregory Price'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260911001826.2109390-1-gourry@gourry.net>'
    date: '2026-09-11'
    summary: '4-patch：移除 VMA 扫描过滤器对 promotion 的门控 + tiering 扫描只读文件映射'
    review_outcome: 'Zi Yan 质询测试范围，作者澄清问题性质与覆盖'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '3/4、4/4 的具体实现意见待解决（见相关文章）'
  next_action: '按 Zi Yan 建议补充预期行为列表，推进 3/4、4/4 重写'
contribution_opportunities:
  - kind: testing
    description: '按预期行为列表在 NUMA tiering 环境核对并补充验证数据'
  - kind: review
    description: '评估移除 promotion 门控后是否存在过度 promotion 回归风险'
generated_at: '2026-09-20T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260918-013
  - sched-20260918-014
tags:
  - numa_balancing
---