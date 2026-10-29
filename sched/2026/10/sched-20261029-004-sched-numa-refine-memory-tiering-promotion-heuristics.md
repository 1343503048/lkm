# sched/numa: refine memory tiering promotion heuristics

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261014-002（v1 0/6）：Li Zhe（字节跳动）发系列修复 NUMA balancing 的 scan-period 调整、memory-tiering promotion 反馈污染、陈旧 task-placement 状态三类问题（含 memory hotplug 下可复现除零）；Gregory Price 逐补丁要求补「用户可见性能影响」数据。
- sched-20261015-026：Li Zhe 逐条回应，坦承 3/6、5/6、6/6 无说服力性能数据，计划把「严重修复」与「启发式改动」拆开，将其余收敛到 memory-tiering 专属。
- sched-20261029-004（今天）：作者把系列收束为 **v2 0/3**（1/3 free-space bypass 可配置、2/3 不把 tiering promotion 喂进 task-placement 统计、3/3 修 tiering-only 的 scan-period 调整）。Bharata Rao（AMD，pghot 作者）当日密集回帖：质疑 1/3 对「自然溢出」场景的收益、指出 2/3 在缺 3/3 替代路径前不能独立成 fix、建议 3/3 不要把 scan-period 反馈塞进 `should_numa_migrate_memory()`。Li Zhe 决定**把 2/3 拆成独立 fix（补 Fixes 标签 + rc1 后 Cc stable），1/3 与 3/3 并入更大的 pghot/tiering 启发式讨论**。

## 背景与问题
（承接 20261014-002 的 0/6）三类缺陷收敛为 v2 的三条主线：

1. **free-space bypass 不可控**（1/3）：现有 free-space bypass 会在 fast tier 有足够空闲时，无视 hotness/rate-limit 把短时冷访问/突发热页回填到 DRAM。对有意识地把内存铺在 DRAM+CXL 的部署（如编排层希望某 cgroup 固定 DRAM/CXL 配比、保留 DRAM 容量给后续决策），这种回填是被动的。
2. **tiering promotion 污染 task-placement 统计**（2/3）：tiering-only 模式的 promotion fault 漏过 `task_numa_fault()` 的排除逻辑，把 promotion 结果喂进正常 task-placement 统计与 preferred-node 状态。
3. **tiering-only 的 scan-period 调整**（3/3）：现有 scan-period 更新依赖 private/shared fault，对 tiering-only 模式语义不符，需要独立反馈路径。

## 技术方案
（承接 v1，v2 收束）三片各对应一条主线：

- **1/3** 给 free-space bypass 加开关：默认维持现状；关闭后跳过 free-space 捷径，让这些 fault 回落到已有的 hotness/rate-limit 检查（作者强调「不是新增 hotness 策略，只是让已有策略在 fast tier 有空闲时也生效」）。
- **2/3** 停止把 tiering promotion 结果喂进 task-placement 统计。
- **3/3** 从 `should_numa_migrate_memory()` 驱动 tiering-only 的 scan-period 更新（与常规模式分离）。

今日讨论出的**方向性调整**：Bharata 认为 scan-period 属于 hint fault scanner（他正在 pghot 里把 promotion 启发式从 `should_numa_migrate_memory()` 抽出、由 shared engine 做分类与迁移），3/3 的反馈应留在 hint fault 路径；Li Zhe 认同分层合理，但想在本系列内「贴近现有 numabalance 实现」、把分离留给更大的 promotion-engine 重构。

## 版本演进与当前进展
*current_version: v2*（2026-10-28，cover `<20261028041253.74839-1-lizhe.67@bytedance.com>`；当日无 digest，本日由讨论邮件续）。

- **v1（0/6，20261014）**：三类缺陷一起发，Gregory Price 要求性能数据。
- **v2（0/3，20261028）**：收束为 tiering promotion 启发式三片。
- **今天（20261029）**：Bharata Rao 多封 review + Li Zhe 逐条回应，达成「2/3 拆独立 fix」共识，1/3、3/3 并入 pghot 讨论。

## Maintainer 意见与讨论焦点
- **Bharata Rao（AMD，pghot 作者，非 maintainer）**：① 对 1/3，认为「自然溢出」才是正确评估方法，非 overcommitted 场景的 free-space bypass 优化未必惠及真实运行；② 对 2/3，指出当前只有成功 promotion 喂统计、此改动会让 tiering 模式无人更新 scan-period，需 3/3 的替代路径否则不能独立成 fix，并请 **Ying Huang（NUMA maintainer）** 澄清为何 tiering 模式只有成功 promotion 驱动 fault 统计；③ 对 3/3，认可 tiering 与常规模式分离，但反对从 `should_numa_migrate_memory()` 驱动（属于 hint fault scanner），与 pghot 的 source-specific 分层冲突。
- **Li Zhe**：接受 2/3 拆独立 fix（补 Fixes 标签、rc1 后 Cc stable）；对 1/3 坚持其「刻意 DRAM/CXL 配比」使用场景真实存在；对 3/3 认可分层但希望把分离与更大重构一起做。
- 未解决的焦点：3/3 的 scan-period 反馈该放哪一层，本质上取决于 pghot 的 promotion-engine 重构节奏。

## 合入评估
*likelihood=medium*。2/3 是货真价实的 fix、方向获 Bharata 认可，将拆成独立补丁（带 Fixes + stable），合入概率较高；1/3 与 3/3 属启发式/策略，需与 pghot 协同、短期内难合。*blocking_issues*：2/3 需确认引入该路径的确切 commit 以补 Fixes 标签，并等 rc1 后 Cc stable；3/3 的反馈层归属与 pghot 方向绑定；1/3 的「自然溢出」方法论分歧未消。*next_action*：作者发 2/3 独立 fix 版本，1/3、3/3 随 pghot 讨论推进。

## 效果评估
作者无说服力性能数据（v1 阶段已坦承 3/6、5/6、6/6 纯语义正确性）；1/3 的收益描述（保留 DRAM 容量、避免冷访问回填）为作者主观判断，未见 bench。Bharata 提到 pghot 用「非 overcommitted」与「overcommitted」两类场景出数据，但未在本线程给出具体数字。

## 我可以参与的点
- **review**：Bharata 明确点名请 **Ying Huang** 解释「为何 tiering 模式只有成功 promotion 驱动 fault 统计」——这是 2/3 成立与否的关键，可帮查 `kernel/sched/fair.c` 的 `task_numa_fault()`/tiering 路径给出分析。
- **discussion**：就「scan-period 反馈该放在 hint fault 路径还是 should_numa_migrate_memory()」结合 pghot 方向给出分层建议。
- **new_patch**：2/3 独立 fix 需要先确认引入路径的 commit 与 Fixes 标签，可协助定位。

## 参考链接
- lore thread（v2 0/3 cover）: https://lore.kernel.org/all/20261028041253.74839-1-lizhe.67@bytedance.com/
- Bharata Rao 对 2/3 的 review: https://lore.kernel.org/all/8d6f589c-4427-465d-be5a-17eb99f41a91@amd.com/
- Bharata Rao 对 3/3 的 review: https://lore.kernel.org/all/de52b5f1-97eb-4404-b7f1-53f0aab17fae@amd.com/

---
id: sched-20261029-004
date: 2026-10-29
subject: "sched/numa: refine memory tiering promotion heuristics"
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20261028041253.74839-1-lizhe.67@bytedance.com>"
lore_url: "https://lore.kernel.org/all/20261028041253.74839-1-lizhe.67@bytedance.com/"
authors: [Li Zhe]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: 2026-10-14
    summary: "0/6：修复 NUMA balancing scan-period / tiering promotion 反馈污染 / 陈旧 task-placement 状态三类问题"
    review_outcome: "Gregory Price 逐补丁要求补性能数据"
  - version: v2
    msgid: "<20261028041253.74839-1-lizhe.67@bytedance.com>"
    date: 2026-10-28
    summary: "0/3：收束为 tiering promotion 启发式三片（free-space bypass 可配置 / 不喂 placement 统计 / scan-period 调整）"
    review_outcome: "Bharata Rao 密集 review，2/3 拆独立 fix、1/3 与 3/3 并入 pghot 讨论"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "2/3 独立 fix 需确认引入路径的确切 commit 以补 Fixes 标签，并等 rc1 后 Cc stable"
    - "3/3 的 scan-period 反馈层归属与 pghot promotion-engine 重构节奏绑定"
    - "1/3 的「自然溢出 vs 刻意配比」方法论分歧未消"
  next_action: "作者发 2/3 独立 fix 版本；1/3、3/3 随 pghot 讨论推进"
contribution_opportunities:
  - kind: review
    description: "帮查 task_numa_fault()/tiering 路径，回答 Ying Huang 被点名的「为何只有成功 promotion 驱动 fault 统计」"
  - kind: discussion
    description: "就 scan-period 反馈层归属结合 pghot 方向给出分层建议"
  - kind: new_patch
    description: "协助定位 2/3 引入路径的 commit 并补 Fixes 标签"
generated_at: "2026-10-30T09:30:00"
source_email_count: 13
related_articles: [sched-20261014-002, sched-20261015-026]
tags: [numa_balancing]
---