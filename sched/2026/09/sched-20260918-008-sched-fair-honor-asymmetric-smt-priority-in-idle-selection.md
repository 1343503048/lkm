# sched/fair: Honor asymmetric SMT priority in idle selection

## TL;DR
增量更新：Andrea Righi 的非对称 SMT 首选 idle 选择系列（原 v4 起重构为 2 枚补丁：1/2 `sched/fair` idle 选择尊享 SMT 优先级、2/2 `sched/topology` 新增内核参数覆盖）本日集中收到 review——Vincent Guittot 与 Kayra Cizmeci 对 1/2 给出 Reviewed-by（Kayra 另附 Tested-by）；Shrikanth Hegde 对 2/2 的 kernel 参数设计提出三点疑问（changelog 缺失、为何不由 arch 提供、对不收益于 asym packing 的架构的困惑）。

## 背景与问题
背景见 sched-20260912-008：在大小核/非对称 SMT 平台上，idle 选择希望优先选择高优先级 SMT sibling。系列此前为单补丁（v4 及以前），09-17 起重构为 2 枚补丁，把"是否启用 SMT 打包 override"拆成独立的内核参数（2/2）。

## 技术方案
- 1/2（`sched/fair: Honor asymmetric SMT priority in idle selection`）：在 `select_idle_smt_cpu()` 中按不对称 SMT 优先级选择 idle sibling，而非等权挑选。
- 2/2（`sched/topology: Add asymmetric SMT packing override`）：新增一个内核参数/选项，允许显式开启 SMT 层的 asymmetric packing 覆盖。

## 版本演进与当前进展
- v4（09-09，`<20260909062649.469633-1-arighi@nvidia.com>`）：单补丁形式。
- 09-17 新迭代（`<20260917140707.3807229-1-arighi@nvidia.com>`）：重构为 1/2 + 2/2 两枚补丁，2/2 拆分出 topology 打包 override。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**：对 1/2 给出 Reviewed-by。
- **Kayra Cizmeci**：对 1/2 给出 Tested-by 与 Reviewed-by（其平台为普通 SMT2，补丁未改变行为属预期）；早前曾就 `select_idle_smt_cpu()` 上 `sched_smt_active()` 检查是否冗余提问。
- **Shrikanth Hegde**（2/2）：三点问题——① "sorted out? 或中途有变化？"要求把变更写入 changelog/注释；② "这个 option/parameter 不是应该来自 arch 私有文件吗"；③ 对不在 SMT 受益、却可被该内核参数勾上的架构是否会困惑。
- 分歧/未决：2/2 的 kernel 参数设计（arch 归属、命名与适用范围）尚未回应，1/2 已获认可。

## 合入评估
likelihood=medium。1/2 获两位维护者/资深 reviewer 认可，方向明确；2/2 的 override 参数设计仍有 Shrikanth 三点质疑待作者回应。blocking_issues：2/2 内核参数设计（arch 归属、changelog 补充、对非相关架构的影响）未解决。next_action：作者回应 Shrikanth 关于 2/2 的质疑，补充 changelog 或改为 arch 提供方式后重发。

## 效果评估
本日无新增 benchmark；Kayra 在 SMT2 平台验证补丁未引入行为变化（符合预期）。

## 我可以参与的点
- kind=review：就 2/2 内核参数 vs arch 私有配置的取舍给出跨架构视角（如 arm64/riscv/powerpc 对 asym packing 的实际需求差异）。
- kind=testing：在有非对称 SMT 的硬件（如 Intel P/E 核混合或多等级 SMT）上复测 1/2 的 idle 选择。

## 参考链接
- lore（09-17 系列 cover）: https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/

---
id: sched-20260918-008
date: '2026-09-18'
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260917140707.3807229-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260917140707.3807229-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Vincent Guittot'
  - 'Shrikanth Hegde'
current_version: v4
patch_series:
  - version: v4
    msgid: '<20260909062649.469633-1-arighi@nvidia.com>'
    date: '2026-09-09'
    summary: '单补丁：idle 选择尊享不对称 SMT 优先级'
    review_outcome: '见 sched-20260912-008'
  - version: '09-17 迭代'
    msgid: '<20260917140707.3807229-1-arighi@nvidia.com>'
    date: '2026-09-17'
    summary: '重构为 1/2（fair idle 选择）+ 2/2（topology SMT packing override）'
    review_outcome: '1/2 获 Vincent/Kayra Reviewed-by；2/2 遇 Shrikanth 参数设计三问'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '2/2 内核参数设计（arch 归属、changelog、非相关架构影响）待回应'
  next_action: '作者回应 Shrikanth 关于 2/2 的质疑后重发'
contribution_opportunities:
  - kind: review
    description: '就 2/2 内核参数 vs arch 私有配置给出跨架构视角'
  - kind: testing
    description: '在非对称 SMT 硬件上复测 1/2 的 idle 选择'
generated_at: '2026-09-19T09:00:00'
source_email_count: 4
related_articles:
  - sched-20260912-008
tags:
  - cfs
  - topology
  - idle
  - hyperthreading
---