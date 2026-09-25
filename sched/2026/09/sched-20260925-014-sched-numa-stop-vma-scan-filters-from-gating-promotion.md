# sched/numa: stop VMA scan filters from gating promotion

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 sched-20260923-008（v3 封面）。David Hildenbrand 今天逐枚 review 了 v3 的 3/7、4/7、5/7 三枚，核心意见是 `placement_scan` 的 `&=` 布尔组合难读、建议改成显式 `if/else if` 赋值并尽量少用 `&=`；4/7、5/7 除同类可读性意见外「LGTM」。作者 Gregory Price 表示会在重命名函数时一并处理，系列朝 v4 收敛。

## 背景与问题

（承接 sched-20260923-008）NUMA 内存 tiering 模式下，VMA 扫描过滤器（`placement_scan` 等）此前会「挡住」本应发生的页提升（promotion）。v3 系列（7 补丁）逐步把「VMA 放置」与「扫描是否继续」解耦，并放开对只读文件映射、PID 不活跃 VMA 的扫描，让 tiering 模式下的提升不再被这些过滤器误门控。

## 技术方案

（承接 sched-20260923-008）3/7 在 tiering 模式下扫描只读文件映射；4/7 把「VMA 放置」从「扫描继续」里分离；5/7 扫描 PID 不活跃的 VMA 用于提升。今天的 review 聚焦在这些补丁里 `placement_scan` 的组合逻辑：David 建议把 `placement_scan &= numab_mode & NUMA_BALANCING_NORMAL;` 这类连续 `&=` 改成显式的

```c
if (scan_started && !vma->numab_state->placement_scan)
    placement_scan = false;
else if (tiering && !placement_due)
    placement_scan = false;
```

并问「是否真的需要更新 placement_scan 本身」，给出用 `const bool balancing = numab_mode & NUMA_BALANCING_NORMAL;` + `if (!placement_scan || !balancing) cp_flags |= MM_CP_PROT_NUMA_PROMO_ONLY;` 的替代。Gregory 回帖说明 `&=` 在后续 commit 里如何组合，并表示会在改函数名时一并处理。

## 版本演进与当前进展

- v2（2026-09-11，`<20260911001826.2109390-1-gourry@gourry.net>`）。
- v3（2026-09-22，封面 `<20260922182928.2199090-1-gourry@gourry.net>`，7 补丁）。
- 09-25：David 逐枚 review 3/7、4/7、5/7（见下），无 NAK；4/7「LGTM」、5/7「Same comment, apart from that LGTM」；作者准备 v4。

## Maintainer 意见与讨论焦点

- **David Hildenbrand 的意见全部集中在可读性**：连续 `&=` 布尔组合难读、建议显式 `if/else if` 赋值；并明确承认「It's all very complicated, so I won't pretend I fully digested the logic」——这是诚实的保守态度，也意味着逻辑本身未被质疑、但也没有被完全背书。
- 无 NAK；4/7、5/7 已「LGTM」；3/7 的 placement_scan 改写方式在 David/Gregory 之间往返了一次（`balancing` 变量 vs 显式 if 分支），最终 David 认可后者。
- 该系列主要 reviewer 就是 David（Arm），Gregory 是作者；未见其他维护者表态。

## 合入评估

*likelihood=medium*。David 已对 4/7、5/7 LGTM，3/7 是可读性收尾；但系列尚无合入信号，且 David 自陈未完全消化逻辑，正式合入前可能还需一两位熟悉 NUMA 平衡的 reviewer。*blocking_issues*：3/7 的 placement_scan 可读性改写待作者落 v4；缺第二 reviewer。*next_action*：Gregory 发 v4 收掉可读性意见，争取 Peter/其他 NUMA 平衡维护者 review。

## 效果评估

今日无 benchmark 数据；系列属行为正确性（tiering 提升被过滤器误门控）修复，效果通常以 tiering 场景的页提升成功率或迁移指标衡量，本次讨论未涉及量化。暂无效果数据。

## 我可以参与的点

- `review`：David 自陈「未完全消化逻辑」，且缺第二 reviewer；对 NUMA 平衡/tiering 熟悉的人可逐枚审读 placement_scan 的布尔组合与 4/7 的分离逻辑，给出第二意见。
- `testing`：在内存 tiering（如 CXL/PMEM + DRAM）场景下验证 3/7~5/7 是否真正放开被门控的提升，并测量提升成功率/迁移量。

## 参考链接

- v3 封面: https://lore.kernel.org/all/20260922182928.2199090-1-gourry@gourry.net/
- David 对 3/7: https://lore.kernel.org/all/c73021d4-60c8-4446-9c08-f9d7807a3a0f@kernel.org/
- David 对 3/7（续）: https://lore.kernel.org/all/75358469-e4b1-4c11-89a2-61773c89132c@kernel.org/
- David 对 4/7: https://lore.kernel.org/all/0aa5b55f-54a4-4d39-885b-817c0191cdeb@kernel.org/
- David 对 5/7: https://lore.kernel.org/all/ad99014e-3714-45a5-ad23-aa7fe72745cb@kernel.org/
- Gregory 对 3/7 回应: https://lore.kernel.org/all/arXBari1QNJ-aIW8@gourry-fedora-PF4VCD3F/

---
id: sched-20260925-014
date: 2026-09-25
subject: "sched/numa: stop VMA scan filters from gating promotion"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260922182928.2199090-1-gourry@gourry.net>"
lore_url: "https://lore.kernel.org/all/20260922182928.2199090-1-gourry@gourry.net/"
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: "2026-09-26T01:15:00"
authors:
  - "Gregory Price"
maintainers_involved:
  - "David Hildenbrand"
patch_series:
  - version: v2
    msgid: "<20260911001826.2109390-1-gourry@gourry.net>"
    date: 2026-09-11
    summary: "v2"
    review_outcome: "无"
  - version: v3
    msgid: "<20260922182928.2199090-1-gourry@gourry.net>"
    date: 2026-09-22
    summary: "7 补丁：放开 tiering 模式只读文件映射/PID 不活跃 VMA 扫描，解耦 VMA 放置与扫描继续"
    review_outcome: "09-25 David 逐枚 review 3/7~5/7，提 placement_scan 可读性意见，4/7、5/7 LGTM"
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "3/7 的 placement_scan 可读性改写待作者落 v4"
    - "缺第二 reviewer，David 自陈未完全消化逻辑"
  next_action: "Gregory 发 v4 收掉可读性意见，争取 Peter 或其他 NUMA 平衡维护者 review"
contribution_opportunities:
  - kind: review
    description: "对 NUMA 平衡/tiering 熟悉者可逐枚审读 placement_scan 布尔组合与 4/7 分离逻辑，给出第二意见"
  - kind: testing
    description: "在内存 tiering（CXL/PMEM + DRAM）场景验证 3/7~5/7 放开被门控的提升并测量成功率/迁移量"
source_email_count: 5
related_articles:
  - "sched-20260923-008"
  - "sched-20260919-008"
  - "sched-20260918-014"
tags:
  - numa_balancing
---