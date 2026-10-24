# sched_ext: Sync tools headers with scx and fix unsigned enum reads

## TL;DR
Tejun Heo 发往 sched_ext/for-7.5 的四补丁系列：修 `__COMPAT_read_enum()` 对无符号 4 字节枚举的符号扩展（导致 `SCX_RESCUE_DISABLE` 被读成 `0xffffffffffffffff`）、把 tools/sched_ext/include 的共享头与 scx 仓库同步、并删掉 kernel 已不存在的枚举查表条目。属 for-7.5 枚举查表收尾的又一步（承接 10-23 已合入的 enum tables 系列），scx 侧 PR 已合并，在 Tejun 自有树迭代，高确信合入。

## 背景与问题
`__COMPAT_read_enum()` 是无符号 4 字节枚举的兼容读取路径，此前对 unsigned enum 做了符号扩展，使 `SCX_RESCUE_DISABLE` 这类枚举被读成 `0xffffffffffffffff`。同时 tools/sched_ext/include 下的共享头（`common.bpf.h`、`compat.h`、`compat.bpf.h` 等）与 scx 仓库（https://github.com/sched-ext/scx）存在漂移，且 autogen 枚举查表里残留了 kernel 已删除的枚举条目。该系列承接 10-23 已发出、10-24 已合入 for-7.5 的「Regenerate the enum tables」系列，进一步统一枚举读取与头文件同步。

## 技术方案
四补丁（7 files，+48/-35，均在 tools/sched_ext/）：

1. **sched_ext: Don't sign-extend unsigned enums in __COMPAT_read_enum()**：修正符号扩展，使无符号枚举读取值正确。
2. **sched_ext: Sync tools autogen enum lookup tables from the scx repo**：同步 `enum_defs.autogen.h` / `enums_abi.autogen.h` 两份生成表。
3. **sched_ext: Sync common and compat headers from the scx repo**：同步 `bpf_arena_common.bpf.h`、`common.bpf.h`、`compat.bpf.h`、`compat.h`、`enums.autogen.bpf.h`、`enums.autogen.h`。
4. **sched_ext: Drop stale entries from the enum lookup tables**：删掉 kernel 已不存在的枚举条目（如 `scx_flatcg.bpf.c` 里 5 行删除）。

scx 侧为已合并的 https://github.com/sched-ext/scx/pull/3930 与 3932。应用后 tools/sched_ext/include 与 scx 仓库的共享头除两份生成表（双方各自从 vmlinux.h 生成）外完全一致。基于 sched_ext/for-7.5（`dd3b1d9be27c`），分支 `git://.../tj/sched_ext.git enums-sync`。

## 版本演进与当前进展
*current_version: v1*（`<20261023232102.1124938-1-tj@kernel.org>`）。当日发出，缓存内暂无 review 回帖。

## Maintainer 意见与讨论焦点
暂无外部 reviewer 上线表态。Tejun 为 sched_ext 维护者，系列在其自有树迭代；此前同类枚举查表系列已获 Andrea Righi Reviewed-by 并合入 for-7.5，本系列方向一致、无争议预期。

## 合入评估
*likelihood=high*。属 Tejun 自有 sched_ext/for-7.5 树的枚举/头文件同步与正确性修复，scx 侧 PR 已合并、无反向意见。*blocking_issues*：当日缓存未见第二 reviewer 确认（预计同前序由 Andrea 或其他 sched_ext reviewer 背书）。*next_action*：Tejun 收取进 for-7.5。

## 效果评估
功能等价性为主：修 unsigned enum 符号扩展（`SCX_RESCUE_DISABLE` 从误读的 `0xffffffffffffffff` 恢复正确值）、头文件与 scx 仓库对齐。无量化性能数据。

## 我可以参与的点
- *kind: review*：核对签名后的 `__COMPAT_read_enum()` 对 unsigned/有符号枚举的语义、以及生成表与 scx 仓库的一致性。
- *kind: extend*：继续清理 Andrea 此前指出的、`enums.autogen.h` 中已不存在的 stale 枚举条目（`SCX_RQ_BAL_PENDING` 等）并同步 scx 仓库。

## 参考链接
- cover: https://lore.kernel.org/all/20261023232102.1124938-1-tj@kernel.org/
- 前文（enum tables 系列）: sched-20261023-007

---
id: sched-20261024-003
date: 2026-10-24
subject: 'sched_ext: Sync tools headers with scx and fix unsigned enum reads'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261023232102.1124938-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20261023232102.1124938-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261023232102.1124938-1-tj@kernel.org>'
    date: 2026-10-24
    summary: '修 __COMPAT_read_enum 符号扩展、同步 scx 头与 autogen 表、删 stale 枚举条目'
    review_outcome: '暂无 review'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '当日缓存未见第二 reviewer 确认'
  next_action: 'Tejun 收取进 sched_ext/for-7.5'
contribution_opportunities:
  - kind: review
    description: '核对 __COMPAT_read_enum 修复与生成表/scx 仓库一致性'
  - kind: extend
    description: '继续清理 enums.autogen.h 中已不存在的 stale 枚举条目'
generated_at: '2026-10-25T01:00:00'
source_email_count: 5
related_articles:
  - sched-20261023-007
tags:
  - sched_ext
---