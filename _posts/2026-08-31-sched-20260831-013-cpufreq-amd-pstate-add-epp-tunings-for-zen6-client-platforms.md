---
id: sched-20260831-013
date: '2026-08-31'
subject: 'cpufreq/amd-pstate: Add EPP tunings for Zen6 client platforms'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260831054630.1745997-1-superm1@kernel.org>
lore_url: https://lore.kernel.org/all/20260831054630.1745997-1-superm1@kernel.org/
authors:
- Mario Limonciello
maintainers_involved:
- Viresh Kumar
current_version: v1
patch_series:
- version: v1
  msgid: <20260831054630.1745997-2-superm1@kernel.org>
  date: 2026-08-31
  summary: 1/2 建立 x86_cpu_id 驱动的 per-SoC/per-core-type EPP 表（缺省回落 legacy），epp_values
    改 u8，并让 sysfs 在具名档不匹配时回显数值 EPP
  review_outcome: 当日无人回复
- version: v1
  msgid: <20260831054630.1745997-3-superm1@kernel.org>
  date: 2026-08-31
  summary: 2/2 为 Zen6 客户端（family 0x1A，model 0x80/0x81/0x84/0x85/0xe0）写入调优值，三核类型仅在
    power 档区分（大核 64、小核/LP 核 115）
  review_outcome: 当日无人回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: possible
  blocking_issues:
  - 无任何 benchmark/功耗数据支撑 64/115 这组具体数值
  - 1/2 混入大量清理并含一处 sysfs 对外行为变更，可能被要求拆分
  - 当日无 maintainer review
  next_action: 等 Viresh Kumar review；作者需补测得数据并考虑把 sysfs 行为变更独立成补丁
contribution_opportunities:
- kind: testing
  description: 在 Zen6 客户端上对比 power 档 64 vs 115 的频率分布/续航/吞吐，补上系列完全缺失的数据
- kind: review
  description: 从调度器频率不变性角度评估按核类型压低 EPP 对 capacity_of()/util↔freq 换算的连带影响
generated_at: '2026-09-07T21:16:22'
source_email_count: 2
related_articles: []
tags:
- cpufreq
- thermal
- x86
title: 'cpufreq/amd-pstate: Add EPP tunings for Zen6 client platforms'
layout: article
---

## TL;DR

Mario Limonciello（AMD）8/31 13:46 发 2 补丁：1/2 给 amd-pstate 建立 **per-SoC / per-core-type 的 EPP 表**（`x86_cpu_id` 匹配，缺 SoC 则回落 legacy 常量），2/2 用它给 Zen6 客户端写入第一组调优值。核心手法是把 `power` 档从"所有核一个 0xFF"改成"大核 64、小核/低功耗核 115"，即在省电档下对弱核更激进地压频率。当天无任何 review 回帖。附带一处**用户可见行为变更**：`show_energy_performance_preference()` 在缓存 EPP 不匹配任何具名档位时改为回显数值，而不是返回 `-EINVAL`。

## 背景与问题

1/2 的动机陈述是："On newer SoCs the behavior of the platform has changed, and using the same EPP values for everything will yield worse results than expected."——新平台（尤其 hybrid：性能核 + 能效核 + 低功耗核）用同一组 EPP 常量会得到低于预期的结果。既有实现是一组全局 `epp_values[]`（`0x00/0x80/0xBF/0xFF` 四档），既不分 SoC 也不分核类型；Zen6 客户端上"不同核类型需要不同调优"被作者明确写进 2/2 的 commit message（"Zen6 client platforms perform better with individual tunings for different core types"）。

## 技术方案

- **匹配表**：新增 `static const struct x86_cpu_id amd_pstate_epp_soc_ids[]`，按 vendor/family/model 关联一个 `struct amd_pstate_epp_soc`；表内注释规定**只列 hybrid SoC**，非 hybrid 系统一律用 legacy 默认值。
- **数据结构**：`struct amd_pstate_epp_soc` 内含 `performance_core` / `efficiency_core` / `low_power_core` 三组，每组四个具名档（`performance`、`balance_performance`、`balance_power`、`power`），并加 `static_assert` 确保 `epp_values` 的行数覆盖所有 CPU 类型。
- **类型收敛**：`epp_values[]` 与 `amd_pstate_cpu_epp_values()` 由 `unsigned int` 改为 `u8`（EPP 本身是 8 bit）。
- **常量重命名**：`AMD_CPPC_EPP_PERFORMANCE/BALANCE_PERFORMANCE/BALANCE_POWERSAVE/POWERSAVE` 改为 `AMD_CPPC_EPP_LEGACY_*` 前缀，为新表让出语义空间。
- **Zen6 客户端的具体数值**（family `0x1A`，model `0x80/0x81/0x84/0x85/0xe0` 五个匹配项）：

  | 核类型 | performance | balance_performance | balance_power | power |
  |---|---|---|---|---|
  | performance_core | 25 | 51 | 64 | 64 |
  | efficiency_core | 25 | 51 | 64 | **115** |
  | low_power_core | 25 | 51 | 64 | **115** |

  读法：三种核在高性能与均衡档上完全一致，差异只出现在 `power` 档——大核仍停在 64，小核/低功耗核推到 115。也就是**只有"省电"这一档才按核类型区分**，把弱核更用力地压下去，而不改变快核行为。
- 1/2 同时做了一批周边清理：`show_energy_performance_preference()` 循环改为带 preference 跟踪的 for 循环并排除未初始化的 `EPP_INDEX_CUSTOM`/`EPP_INDEX_DYNAMIC` 槽位；移除 `amd_pstate_get_epp_from_platform_profile()` 并内联其逻辑；修 `amd_pstate_set_dynamic_epp()` 的清理路径；在 `amd_pstate_init_epp_values()` 加 debug 打印。作者声明该 commit **不新增任何平台**。
- **行为变更（作者显式标注）**：`show_energy_performance_preference()` 现在在缓存 EPP 不匹配任何具名 preference 时通过 sysfs 返回数值 EPP，而不再返回 `-EINVAL`——理由是"给硬件或 BIOS 设置的自定义 EPP 值提供可见性"。

## 版本演进与当前进展

- 当前 v1（cover `<20260831054630.1745997-1-superm1@kernel.org>`，1/2 = `-2-`、2/2 = `-3-`），8/31 13:46 发出。
- 当日**无人回帖**，无 `Reviewed-by`/`Acked-by`，也没有 v2。

## Maintainer 意见与讨论焦点

本日没有 maintainer 意见。需要留意的潜在争议点（由补丁内容而非讨论得出）：

- 数值全部是裸常量，1/2 与 2/2 都没有给出任何测量说明"为什么 64/115 而不是别的"，而作者的说法是"platform behavior changed / performs better"——按模板口径这属于**作者主观判断，未见测试数据**。
- 架构层面的争议空间在于"per-SoC 表放驱动里"还是走 ACPI/CPPC 上报：本方案选择 x86 CPU id 表 + 缺省回落，等于承认这些信息固件给不出来。
- 1/2 混入了较多清理与一处 sysfs 可见行为变更，cpufreq 维护者通常偏好把"重构"和"加平台数据"拆得更干净。

## 合入评估

**possible**。作者本人是 amd-pstate 的活跃维护贡献者，方向（分核类型 EPP）与该驱动此前引入 `struct amd_pstate_epp_soc` 的路子一致，且做了保守回落（非 hybrid / 缺 SoC 一律 legacy 值），风险面小。卡点：没有任何 benchmark 支撑、1/2 改动面偏大（`160 insertions(+), 37 deletions(-)`，含一处对外可见的 sysfs 语义变化）、当天完全无人 review。`next_action`：需要 Viresh Kumar 的 review，以及作者补充"为什么是这组数值"的数据；sysfs 行为变更可能需要单独的文档/通知。

## 效果评估

暂无效果数据。两封邮件里只有"perform better with individual tunings"、"will yield worse results than expected"这类定性表述，**没有任何功耗、频率、性能或续航数字**，也没有测试机型号与测试方法。

## 我可以参与的点

- **数据侧补强**：如果你有 Zen6 客户端（或同 family/model 的机器），跑一组 `power`/`balance_power` 档下 64 vs 115 的对比（频率分布、续航、多线程吞吐），是对该系列最直接的输入——目前全线程没有一份数据。
- **调度器视角的评审**：EPP 与调度是耦合的——非对称容量系统里"小核被 EPP 压到 64/115"会直接改变 `capacity_of()`/频率不变性（util→freq）换算，进而影响 EEVDF 与负载判定。若你正在跟踪 `sched/fair` 的频率不变性方向（`sched-20260825-010` 那条线），这是一个能提出实质意见的交叉点。
- **拆分建议**：把 1/2 里的 sysfs 行为变更与纯重构分离，是 review 阶段容易提也更容易被接受的意见。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20260831054630.1745997-1-superm1@kernel.org/
- 1/2 per SoC/per core type 框架: https://lore.kernel.org/all/20260831054630.1745997-2-superm1@kernel.org/
- 2/2 Zen6 客户端数值: https://lore.kernel.org/all/20260831054630.1745997-3-superm1@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到
