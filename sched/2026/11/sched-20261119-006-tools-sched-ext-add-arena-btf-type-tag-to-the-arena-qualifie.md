# tools/sched_ext: Add "arena" BTF type tag to the __arena qualifier

## TL;DR

Shaojie Sun 发 1 行修复：给 `tools/sched_ext` 里的 `__arena` 限定符补上 `btf_type_tag("arena")`，与 `tools/testing/selftests/bpf/libarena`（commit a0fa68d8ce75）对齐，使「某类型是否属于 arena」单凭 BTF 即可判断。Tao Cui 已实测（sched_ext for-next 上全部工具/sched_ext 调度器可 build、scx_sdt 带 tag 正常加载运行）并给 Tested-by，但指出两点：补丁对当前树（0a5e9cf2525f 改了上下文行）不直接 apply、需 rebase（`git am -3` 暂时可用）；且该头文件也存在于 sched-ext/scx 仓库、两处靠手工 reconcile，scx 仓库侧缺同样改动，否则下次 reconciliation 会覆盖这处改动。

## 背景与问题

`libarena` 用 `btf_type_tag("arena")` 给 `__arena` 类型打标，从而仅凭 BTF 元数据就能识别 arena 类型（`a0fa68d8ce75` 引入）。`tools/sched_ext` 里的 `__arena` 定义与之作用相同，却缺少该 BTF tag，导致两处在「如何描述 arena 类型」上不一致。补齐 tag 即可让两者行为统一。

## 技术方案

修改 `tools/sched_ext/include/scx/bpf_arena_common.bpf.h` 中的 `__arena` 宏，在 `__attribute__((address_space(1)))` 之外追加 `btf_type_tag("arena")`（1 处插入/1 处删除）。checkpatch 对此类「复杂值宏」报「Macros with complex values should be enclosed in parentheses」的误报——该宏值是声明属性序列而非表达式，既不能加括号也无法包 do-while，且 libarena 的 selftests 副本同样定义、同样触发该告警，作者已在 changelog 说明。

## 版本演进与当前进展

*current_version: v1（2026-11-19，`<20261119102613.811845-1-sunshaojie@kylinos.cn>`）*。首版即获 Tao Cui Tested-by，但需 rebase 与 scx 仓库同步后方可落地，尚未出新版。

## Maintainer 意见与讨论焦点

- **Tao Cui（评审）**：功能验证通过并给 `Tested-by: Tao Cui <cuitao@kylinos.cn>`；两点落地障碍：① 与 `0a5e9cf2525f`（"sched_ext: Sync common and compat headers from the scx repo"）冲突，需 rebase；② scx 仓库侧 `sched-ext/scx` 的同名头需要同样的改动，否则下一次双向 reconciliation 会反向覆盖内核侧。
- 无 NAK；无争议，纯工程落地细节。

## 合入评估

*likelihood=high*。1 行工具头改动、行为验证充分、评审仅要求 rebase + scx 仓库同步，不涉及调度核心逻辑。*blocking_issues*：rebase 到当前树、scx 仓库侧同步改动。*next_action*：作者 rebase 后重发，并在 sched-ext/scx 仓库提同类改动，由 Tejun 收取。

## 效果评估

Tao Cui 实测：sched_ext for-next 上全部 `tools/sched_ext` 调度器 build 通过、`scx_sdt` 加载后 BTF 中带 tag 正常运行。无性能数据。

## 我可以参与的点

- **review**：确认 `btf_type_tag("arena")` 的 C 标准属性序在 Clang/GCC 两种前端下的可移植性（尤其 address_space + btf_type_tag 顺序）。
- **extend**：在 sched-ext/scx 仓库给同名头提交相同改动，避免 reconciliation 覆盖。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261119102613.811845-1-sunshaojie@kylinos.cn/
- Tao Cui 评审: https://lore.kernel.org/all/8bb22131-7f3b-4b70-a7a6-92f465027350@linux.dev/

---
id: sched-20261119-006
date: '2026-11-19'
subject: 'tools/sched_ext: Add "arena" BTF type tag to the __arena qualifier'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261119102613.811845-1-sunshaojie@kylinos.cn>"
lore_url: "https://lore.kernel.org/all/20261119102613.811845-1-sunshaojie@kylinos.cn/"
authors: [Shaojie Sun]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261119102613.811845-1-sunshaojie@kylinos.cn>"
    date: '2026-11-19'
    summary: "给 __arena 限定符补 btf_type_tag(\"arena\")，与 libarena 对齐"
    review_outcome: "Tao Cui Tested-by；需 rebase 与 scx 仓库同步"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["rebase 到当前树", "scx 仓库侧同步改动"]
  next_action: "作者 rebase 重发并在 sched-ext/scx 仓库提交同改动"
contribution_opportunities:
  - kind: review
    description: "确认 btf_type_tag 与 address_space 顺序在 Clang/GCC 下的可移植性"
  - kind: extend
    description: "在 sched-ext/scx 仓库同名头提交相同改动避免被覆盖"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [sched_ext]
---