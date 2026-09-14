---
id: sched-20260911-008
subject: 'sched/numa: stop VMA scan filters from gating promotion'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911001826.2109390-1-gourry@gourry.net>
lore_url: https://lore.kernel.org/all/20260911001826.2109390-4-gourry@gourry.net/
authors:
- Gregory Price
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20260904182006.1562449-1-gourry@gourry.net>
  date: 2026-09-05
  summary: 分层模式下允许扫描只读文件映射与 PID 不活跃 VMA（promotion-only）；sashiko 指出重扫与并发疑问，作者 09-07
    自认捆绑过多并承诺 v2。
  review_outcome: 作者自我修正：并发扫描与 mode=3 需更复杂改动，既有测试仍成立。
- version: v2
  msgid: <20260911001826.2109390-1-gourry@gourry.net>
  date: 2026-09-11
  summary: 3/4 抽 vma_is_ro_file() helper 并收敛分层判断；4/4 新增 prev_placement_scan_seq 解决并发扫描与饥饿兜底；均带
    Fixes + Cc stable。
  review_outcome: 作者判定 v1 遗留 review 意见多为误报；无人类维护者表态。
upstream_commit: null
fixes_commit: c574bbe91703
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 系列自 v1 起无人类维护者回帖，需 mm 与调度两侧认可
  - 回合 stable 存在冲突（作者自述），需子系统树先行
  - promo-only 扫描对放置语义的长期影响只有推理
  next_action: 等 mm/sched 维护者首次表态；核对 v2 1/2/4 补丁与测试声明
contribution_opportunities:
- kind: testing
  description: CXL 机型上用 trace_sched_skip_vma_numa 统计被跳过 VMA 与慢层驻留，给第二份数据
- kind: review
  description: 核对 patch 4/4 删除旧补偿逻辑后多线程扫描完成性
- kind: new_patch
  description: 补分层模式下只读映射 promo fault 是否计入 numa_faults[] 的语义矩阵
generated_at: '2026-09-14T11:35:00'
source_email_count: 3
related_articles:
- sched-20260905-006
- sched-20260907-009
tags:
- numa_balancing
title: 'sched/numa: stop VMA scan filters from gating promotion'
layout: article
---

## TL;DR
Gregory Price（Meta）v2 系列的第 3、4 补丁当日入缓存并给出重磅实测数据：CXL 分层机上 20GB 热 hash 表在修复前完全滞留慢层、修复后 DRAM/CXL 均分；作者同时回应 v1 review 认为遗留疑问多为误报。本文为增量更新（v1 背景与 3/4 的 v1 分析见 sched-20260905-006、sched-20260907-009）：v2 把两个 VMA 过滤器在分层模式下改为「仅提升（promotion-only）」扫描。

## 背景与问题
NUMA balancing 有两个 VMA 级过滤会阻止 hinting fault，进而在分层内存（NUMA_BALANCING_MEMORY_TIERING）下把热内存困在慢层：

- 只读文件映射（commit 4591ce4f2d22，防共享库页放置弹跳）：主程序/共享库这类映射永不被扫描，慢层上的热 folio 无法被提升；
- VMA PID 活跃过滤（commit fc137c0ddab2）：只有 NUMA hint fault 记录 PID 活动，过滤器会抑制本该发生的那次 fault，形成死锁式跳过。

## 技术方案
- patch 3/4（vma_is_ro_file()）：新增 helper 判定只读 file-backed VMA；task_numa_work() 对其的跳过改为仅在未开分层时生效；分层模式下允许扫描，但在 folio 保护遍历时置 `promo_only = ... || vma_is_ro_file(vma)`——普通放置语义保留原限制；
- patch 4/4（prev_placement_scan_seq）：vma_numab_state 新增 placement 扫描序号；vma_is_accessed() 的饥饿判定改用 prev_placement_scan_seq——promotion-only 扫描仍更新 prev_scan_seq 但不再推迟放置扫描的饥饿兜底；删除「扫描已过半则无视 PID 活跃继续」的旧补偿逻辑（由新序号机制覆盖）；
- 作者对 v1 review 的收尾（cover 回帖）：sashiko 遗留意见多为误报——patch 2 注释「bounce horizontally between slow tiers」系笔误级问题；patch 3/4 是既有检查抽 helper，「要更新可以另开补丁」；并指出本工作存在回合 stable 的冲突（backport conflicts），理由是「分层 NUMA balancing 自 2022/2023 年起已被这些过滤机制反复弄坏」。

## 版本演进与当前进展
current_version: v2（v2 cover msgid `<20260911001826.2109390-1-gourry@gourry.net>`，msgid 时间戳 09-11 00:18；当日入缓存 3/4、4/4 与 cover 回帖，1/2/4 补丁未入缓存）。

- v1（2026-09-04/05，root `<20260904182006.1562449-1-gourry@gourry.net>`）：sashiko 提出无谓重扫与并发扫描疑问，作者逐条反驳后于 09-07 自认 v1 捆绑过多、承诺测后发 v2（详见 sched-20260907-009）；
- v2（09-11）：3/4 抽出 vma_is_ro_file() helper 并收敛分层判断；4/4 新增 prev_placement_scan_seq 处理并发扫描与饥饿兜底——正是 v1 自认缺失的两点；两补丁均带 Fixes 与 Cc stable，署名 Assisted-by: LLM。

## Maintainer 意见与讨论焦点
- **Gregory Price（作者）**：宣布剩余 review 意见为误报；明确该组修复有回合冲突但坚持 Cc stable（分层平衡长期损坏）。
- 无人类维护者（mm/sched 两侧）当日表态；v1 时 sashiko（机器人）意见已被作者判定误报。与 v1 相比，「作者自认捆绑过多」的阻力在 v2 已消除，但维护者真空依旧。

## 合入评估
likelihood=medium：v2 直接回应了 v1 自认的两个结构性问题（并发扫描、mode=3），数据完整、Fixes+stable 齐备；但整个系列自 v1 起无任何人类维护者回帖。blocking_issues：维护者真空（需 mm 与调度两侧同时认可）；回合 stable 的冲突需要子系统树先行；「promo_only」扫描对放置语义的长期影响只有推理。next_action：等 mm/sched 维护者首次表态；作者侧核对 v2 1/2/4 的发出与测试声明。

## 效果评估
patch 3/4：768GB DRAM + 256GB CXL 主机、约 430GB 数据库服务——修复前 185MB 主程序二进制中 169MB 积压在 CXL，修复后层级驻留随运行负载分布。
patch 4/4：同机型跑两个约 430GB 数据库负载——一个大 shmem VMA 长期占住扫描，其余 2,537 个 VMA（84GB）被当作不活跃跳过；修复前 20GB 热 hash 表完全滞留 CXL，修复后 DRAM/CXL 均分。
以上数字均出自补丁 commit message，为作者单一平台数据，无第三方复现。

## 我可以参与的点
- kind=testing：在 CXL/慢层机型上开分层模式，用 trace_sched_skip_vma_numa 统计被跳过 VMA 字节与慢层驻留比例，提供作者之外的第二份数据（承 sched-20260907-009 的参与点，v2 后依然成立）。
- kind=review：核对 patch 4/4 删除「扫描过半继续」补偿逻辑后，多线程应用跨 VMA 的扫描完成性是否仍成立（原逻辑正是为此而设）。
- kind=new_patch：评估「分层模式下只读映射的 promo fault 是否应计入 numa_faults[] 参与放置」的语义矩阵——作者在 v1 遗留、v2 仍未覆盖的设计输入。

## 参考链接
- v2 cover：https://lore.kernel.org/all/20260911001826.2109390-1-gourry@gourry.net/
- v2 3/4：https://lore.kernel.org/all/20260911001826.2109390-4-gourry@gourry.net/
- v2 4/4：https://lore.kernel.org/all/20260911001826.2109390-5-gourry@gourry.net/
- 作者对 v1 review 的收尾：https://lore.kernel.org/all/aqOR7TY5YtIadMAK@gourry-fedora-PF4VCD3F/
- v1 root：https://lore.kernel.org/all/20260904182006.1562449-1-gourry@gourry.net/
