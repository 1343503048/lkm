---
id: sched-20260912-003
subject: 'sched/cache: Refresh LLC capacity across CPU hotplug'
date: '2026-09-12'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260911220229.1368887-1-davichazbh@gmail.com>
lore_url: https://lore.kernel.org/all/20260911220229.1368887-1-davichazbh@gmail.com/
authors:
- Davi Chaves Azevedo
maintainers_involved:
- Tim Chen
- Chen Yu
current_version: v2
patch_series:
- version: v1
  msgid: <20260911134825.420748-1-davichazbh@gmail.com>
  date: 2026-09-11
  summary: cacheinfo 传共享掩码给 sched_update_llc_bytes()，逐幸存 CPU 刷新 llc_bytes；Fixes 7030513a0877。
  review_outcome: Chen Yu 复现（Ryzen 8945HX 2 LLC + Xeon 4 LLC/节点）并给 R-b；建议保留启动期注释。
- version: v2
  msgid: <20260911220229.1368887-1-davichazbh@gmail.com>
  date: 2026-09-12
  summary: 恢复启动期注释并补多 LLC 验证记录，无功能变化；加 R-b。
  review_outcome: Tim Chen：The patch looks good to me。
upstream_commit: null
fixes_commit: 7030513a0877
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存内未见应用动作
  - cacheinfo 接口改动的驱动侧 ack 必要性未在邮件中讨论
  next_action: 跟踪 Tim Chen 侧收取；内部分支回合验证
contribution_opportunities:
- kind: new_patch
  description: 内部 CONFIG_SCHED_CACHE 分支回合该修复并按 v1 测试矩阵验证
- kind: review
  description: 确认 cacheinfo 侧签名变化无需 drivers/base 额外 ack
generated_at: '2026-09-14T12:40:00'
source_email_count: 4
related_articles:
- sched-20260911-016
tags:
- cfs
- topology
title: 'sched/cache: Refresh LLC capacity across CPU hotplug'
layout: article
---

## TL;DR
Davi Chaves Azevedo 的 llc_bytes 热插拔修复一日内走完 v1 review → v2 → 维护者认可：Chen Yu 在 Ryzen 8945HX（2 LLC）与 Xeon（每节点 4 LLC）上复现并给 Reviewed-by，Tim Chen 对 v2 表态「looks good to me」。v2 无功能变化（恢复启动期注释 + 补多 LLC 测试记录）。本文为增量更新，v1 分析见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-016-sched-cache-refresh-llc-capacity-across-cpu-hotplug.html">sched-20260911-016</a>。

## 背景与问题
CPU 下线时 sched_cpu_deactivate() 先重建调度域、cacheinfo_cpu_pre_down() 才更新 shared_cpu_map，随后 sched_update_llc_bytes() 查到已 detach 的 sd_llc 直接返回，幸存 CPU 的 llc_bytes 停留旧值（Ryzen 5 7535U 上 16MiB 只算出 15,379,114 字节），可致 exceed_llc_capacity() 错误拒绝聚合。修复把 cacheinfo 已保留的共享掩码直接传给调度器并逐幸存 CPU 刷新。

## 技术方案
（承 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-016-sched-cache-refresh-llc-capacity-across-cpu-hotplug.html">sched-20260911-016</a>：cacheinfo 传 cpu_map 给 sched_update_llc_bytes()，online/pre_down 两路径对掩码内每个幸存 CPU 用各自 LLC 域刷新；Fixes: 7030513a0877。）v2 相对 v1：恢复 build_sched_domains()/cacheinfo_cpu_online() 启动期共享掩码的原有注释（Chen Yu 建议，与离线/cpuset 分区说明并存）、加入 Reviewed-by 与多平台验证记录；无功能变化。

## 版本演进与当前进展
*current_version: v2（msgid `<20260911220229.1368887-1-davichazbh@gmail.com>`，09-12 06:02 入缓存）*。

- v1（09-11）：Chen Yu 当日 review：指出 v1 注释只覆盖启动时序、遗漏运行时热插拔场景，建议保留原启动期注释并补离线/分区说明；同时在 **AMD Ryzen 8945HX（2 LLC、每 LLC 8 核）** 与 **Xeon（每节点 4 LLC）** 上复现问题、确认 v1 恢复正常 sd->llc_bytes，给 Reviewed-by；
- v2（09-12）：按上述意见补注释与验证记录，无功能变化；
- Tim Chen 对 v2：「Thanks. The patch looks good to me.」——sched/cache 核心维护者认可。

## Maintainer 意见与讨论焦点
- **Chen Yu**：注释覆盖面意见（已落实）+ 两平台复现 + R-b；
- **Tim Chen**：明确认可 v2；
- 无分歧记录。维护者两侧（评审 + 认可）齐备，v1 时「缺多 LLC 数据」的缺口已由 Chen Yu 的 8945HX/Xeon 复现补上。

## 合入评估
*likelihood=high*：修复需求经两平台复现、实现经 Chen Yu 评审与 Tim Chen 认可、v2 已收敛；仅差合入动作。*blocking_issues*：当日缓存内未见应用动作；cacheinfo（驱动侧）的接口改动是否需要 drivers/base 侧 ack 未在邮件中出现。*next_action*：跟踪 Tim Chen 侧的收取（预计随 sched/cache 相关树走）；v2 与 v1 无功能差异，回合验证可沿用 v1 的测试矩阵。

## 效果评估
承 v1 的一手数据（Ryzen 5 7535U 修复前后 15,379,114 → 16,777,216 字节、20 轮热插拔、8 场景夹具 5/8→8/8、多架构构建）；新增 Chen Yu 的独立复现平台（Ryzen 8945HX、Xeon 每节点 4 LLC）——「缺多 LLC 硬件结果」的边界已在 v2 中补齐。

## 我可以参与的点
- kind=new_patch：内部分支若开启 CONFIG_SCHED_CACHE，回合该修复并按 v1 测试矩阵（热插拔循环 + llc_bytes 校验）验证。
- kind=review：确认 cacheinfo 侧函数签名变化（sched_update_llc_bytes 入参改为掩码）在 drivers/base 维护者视角无需额外 ack。

## 参考链接
- v2 补丁：https://lore.kernel.org/all/20260911220229.1368887-1-davichazbh@gmail.com/
- Chen Yu 的复现与 R-b：https://lore.kernel.org/all/a3433e6a-0d1f-44a8-99bd-bc63d1a15913@intel.com/
- Tim Chen 的认可：https://lore.kernel.org/all/8da2c1b91baf26b89b37e9cb6ea38af8c4f807cf.camel@linux.intel.com/
- v1 补丁：https://lore.kernel.org/all/20260911134825.420748-1-davichazbh@gmail.com/
