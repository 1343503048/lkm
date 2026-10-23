# sched_ext: Regenerate the enum tables and drop scx_qmap's last compat lookup

## TL;DR
Tejun Heo 发往 sched_ext/for-7.5 的两补丁小系列（承接 scx_qmap compat 移除 [1]）：`788b494fab1c`（"sched_ext: scx_qmap: Drop the compat code"）遗留了一处 `__COMPAT_ENUM_OR_ZERO("scx_consts","SCX_RESCUE_DISABLE")` 兼容查表——用户态只能从 BTF 读这个 kernel 内部枚举、枚举查表里没有它。patch 1 从当前 `vmlinux.h` 重新生成两份 autogen 枚举头（补上上次生成后新增枚举的 presence marker 与 ABI 值），patch 2 把 `SCX_RESCUE_DISABLE` 加进查表并删掉那处 compat 查询。当日 Andrea Righi 对两补丁均给 `Reviewed-by`，并提醒另可在 scx 仓库补 `SCX_RESCUE_DISABLE`、且 autogen 头里还有几个已不存在的枚举（`SCX_RQ_BAL_PENDING` 等）可作后续清理。

## 背景与问题
这是对 10-19 发出、已合入 for-7.5 的「scx_qmap: Drop the compat code and fix a lowpri starvation」系列的跟进（Tejun 当日曾预告「I'll follow up with the changes needed to drop the remaining `__COMPAT_ENUM_OR_ZERO()` for `SCX_RESCUE_DISABLE`, including regenerating the enum tables」）。问题：`scx_qmap` 的 `-B 0` 分支此前用 `__COMPAT_ENUM_OR_ZERO` 读取 `SCX_RESCUE_DISABLE`，而该枚举位于 kernel 内部 `enum scx_consts`、用户态只能从 BTF 读——但枚举查表（`enums.autogen.*`）没列出它，导致无法像其他枚举那样在调度器 open 时从 BTF 统一读取。

## 技术方案
两补丁（5 files，+32/-6）：

1. **patch 1**（sched_ext: Regenerate tools autogen enum headers）：从当前 `vmlinux.h` 重新生成 `enum_defs.autogen.h` 与 `enums_abi.autogen.h`，补进上次生成后新增枚举的 `HAVE_*` presence marker 与 ABI 值（如 `SCX_CID_SCHED_NONE/SELF`、`SCX_RQ_PROXY_PENDING/BLOCKING`、`SCX_SCHED_PCPU_ECAPS_*`、`SCX_REENQ_MARKED` 等，`SCX_OPI_*` 尾值也从 0x23 推进到 0x25）。
2. **patch 2**（sched_ext: scx_qmap: Read SCX_RESCUE_DISABLE through the enum lookup tables）：把 `SCX_RESCUE_DISABLE` 加进 `enums.autogen.bpf.h`/`enums.autogen.h` 查表，`scx_qmap.c` 的 `-B 0` 分支改用 `skel->rodata->__SCX_RESCUE_DISABLE` 读取，删掉 compat 查询；无行为变化。

作者验证：`-B 0` 仍能禁用 rescue、默认值保持不变。基于 sched_ext/for-7.5（`bbd3a3288035`），分支 `git://.../tj/sched_ext.git qmap-enums`。

## 版本演进与当前进展
*current_version: v1*（`<20261023000348.2726436-1-tj@kernel.org>`）。当日发出，Andrea Righi 即回帖 review。

## Maintainer 意见与讨论焦点
Andrea Righi 对 patch 1、patch 2 均给 *Reviewed-by*，另提两点非阻塞建议：(1) 提醒把 `SCX_RESCUE_DISABLE` 也补到 scx 仓库；(2) 指出 `enums.autogen.h`（及 `.bpf.h`）里仍有 `SCX_RQ_BAL_PENDING`、`SCX_RQ_BAL_KEEP`、`SCX_RQ_BYPASSING`、`SCX_RQ_IN_BALANCE`、`SCX_TASK_NR_STATES` 等 kernel 已不存在的条目，无害但可作后续清理。无分歧。

## 合入评估
*likelihood=high*。属 Tejun 自有 sched_ext/for-7.5 树的清理/补齐，两补丁已得 Andrea Reviewed-by，无反向意见。*blocking_issues*：无实质卡点。*next_action*：Tejun 收取进 for-7.5；后续可顺手清理 Andrea 提到的 stale 枚举条目。

## 效果评估
功能等价性验证：`-B 0` 仍禁用 rescue、默认保持不变（无量化数据，纯查表机制替换）。

## 我可以参与的点
- *kind: extend*：按 Andrea 建议提交后续补丁，清理 `enums.autogen.h` 中已不存在的 stale 枚举（`SCX_RQ_BAL_PENDING` 等 5 个）并同步 scx 仓库的 `SCX_RESCUE_DISABLE`。

## 参考链接
- cover: https://lore.kernel.org/all/20261023000348.2726436-1-tj@kernel.org/
- patch 1: https://lore.kernel.org/all/20261023000348.2726436-2-tj@kernel.org/
- patch 2: https://lore.kernel.org/all/20261023000348.2726436-3-tj@kernel.org/
- Andrea 回帖 1: https://lore.kernel.org/all/atr0I5EF7hmM_m7Y@gpd4/
- Andrea 回帖 2: https://lore.kernel.org/all/atr0lZ5dHdoZRz68@gpd4/
- Tejun 前序「已合入并预告本跟进」回帖: https://lore.kernel.org/all/d1370714620d401548f4458f8e4cd24e@kernel.org/

---
id: sched-20261023-007
date: 2026-10-23
subject: "sched_ext: Regenerate the enum tables and drop scx_qmap's last compat lookup"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261023000348.2726436-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261023000348.2726436-1-tj@kernel.org/"
authors: ["Tejun Heo"]
maintainers_involved: ["Andrea Righi"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261023000348.2726436-1-tj@kernel.org>"
    date: 2026-10-23
    summary: "重新生成 autogen 枚举头 + 加 SCX_RESCUE_DISABLE 查表并删 compat 查询"
    review_outcome: "Andrea Righi 双补丁 Reviewed-by，附 stale 枚举清理建议"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Tejun 收取进 sched_ext/for-7.5"
contribution_opportunities:
  - kind: extend
    description: "清理 enums.autogen.h 中已不存在的 stale 枚举并同步 scx 仓库 SCX_RESCUE_DISABLE"
generated_at: "2026-10-24T09:06:00"
source_email_count: 6
related_articles: []
tags: [sched_ext]
---