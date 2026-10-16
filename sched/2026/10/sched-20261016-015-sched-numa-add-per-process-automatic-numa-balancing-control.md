# sched/numa: Add per-process automatic NUMA balancing control

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20260908-007：Li Zhe（ByteDance）发 4 补丁，给自动 NUMA 平衡加 **prctl 级别 per-process 开关**（`PR_SET/GET_NUMA_BALANCING`），让个别进程能整体退出 NUMA 扫描与 locality 统计，同时保留 `kernel.numa_balancing` 作管理员硬总闸。当日零 review。
- sched-20261016-015（今天）：讨论正式展开——Tim Chen 质疑 per-cgroup cache 分组的继承与跨 cgroup 聚合；Yafang Shao 主张走 cgroup::numab_mode + BPF、反对 prctl；Chen Yu 用 threaded cgroup 场景论证两者互补，并深入问 cgroup BPF 在跨 cgroup 共享 mm 时的实现细节。

## 背景与问题
（承接 20260908-007）「launcher 拉起大多数进程用默认策略、选中的进程自己管 NUMA 放置或吃不起采样开销」是核心用例。今天的讨论聚焦接口形态之争：**prctl（per-task，精确但部署成本高）vs cgroup + BPF（per-cgroup，可中心化管理、对用户透明）**。

## 技术方案
（承接 20260908-007）原系列为 prctl 两态开关。今天的讨论在挑战这一形态：
- Yafang Shao 主张 cgroup 方案，提出引入 `cgroup::numab_mode` 字段（暂不暴露 cgroupfs 文件，由 BPF 程序写入），并明确「不支持 threaded cgroup、后续有需求再加 kfunc」。
- Chen Yu 则指出 prctl 与 cgroup/BPF 并不互斥——他举例 Google schedqos 与 DeepSeek RL 基建都用 prctl 部署 core-scheduling，证明 per-task 接口有真实需求；同时对 cgroup BPF 提出「跨 cgroup 共享 mm 的线程时，关一个 cgroup 是否要内核遍历其他 cgroup 同步 enabled」的实现难题。

## 版本演进与当前进展
v1（2026-09-08）→ 今天进入设计讨论，尚无 v2。方向从「纯 prctl」向「prctl 与 cgroup/BPF 并存或转向 cgroup」的辩论推进。

## Maintainer 意见与讨论焦点
- Tim Chen（Intel）：per-cgroup cache 分组的继承规则与跨 cgroup 聚合成本存疑。
- Yafang Shao（ByteDance）：明确「not a big fan of prctl」，认为部署 prctl 政策需要跨团队协调、调整成本高，BPF 可全由内核团队掌控、对用户透明。
- Chen Yu（Intel，sched/numa 维护者）：认可 prctl 有精细控制价值、可与 cgroup/BPF 互补，但指出 cgroup BPF 在 threaded domain 与跨 cgroup 共享 mm 下的语义与实现尚未论证。

## 合入评估
*likelihood=medium*。接口形态之争是核心未解决问题，需在 prctl 与 cgroup/BPF 间收敛或并存；尚无 Peter/Ingo 等顶层表态。*blocking_issues*：接口形态（prctl vs cgroup/BPF）未定；numa_group 跨线程组聚合的语义未论证。*next_action*：作者回应 Chen Yu 对 cgroup BPF 的语义追问，并决定是否保留 prctl 形态。

## 效果评估
无量化数据；讨论仍停留在接口设计与用例辩论。

## 我可以参与的点
- *discussion*：参与 prctl vs cgroup/BPF 的接口形态之争——尤其是「跨 cgroup 共享 mm 时 per-cgroup 开关的传播语义」这一 Chen Yu 抛出的开放问题。
- *testing*：为「关闭 NUMA 平衡省下多少采样开销」提供真实数据，这是判断是否值得新增 uAPI 的关键缺口。

## 参考链接
- 系列 cover：https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/
- Tim Chen：https://lore.kernel.org/all/807eb0e80c76c3ccb85024b360bd47ace201931b.camel@linux.intel.com/
- Yafang Shao（cgroup/BPF 主张）：https://lore.kernel.org/all/CALOAHbCt+iGGWMxzjrcRamdSqD48_v+V685-qi7_Qy7UL8bxxQ@mail.gmail.com/
- Chen Yu（互补论证 + 语义追问）：https://lore.kernel.org/all/bcabbe25-5b2c-464a-a22d-5375a342f938@intel.com/

---
id: sched-20261016-015
date: 2026-10-16
subject: "sched/numa: Add per-process automatic NUMA balancing control"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260908122446.56708-1-lizhe.67@bytedance.com>"
lore_url: "https://lore.kernel.org/all/20260908122446.56708-1-lizhe.67@bytedance.com/"
authors: ["Li Zhe"]
maintainers_involved: ["Chen Yu"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260908122446.56708-1-lizhe.67@bytedance.com>"
    date: 2026-09-08
    summary: "prctl 级别 per-process NUMA 平衡开关（PR_SET/GET_NUMA_BALANCING 82/83）"
    review_outcome: "Tim Chen/Yafang Shao/Chen Yu 就 prctl vs cgroup+BPF 形态展开辩论"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["接口形态 prctl vs cgroup/BPF 未定；numa_group 跨线程组语义未论证"]
  next_action: "作者回应 Chen Yu 的语义追问并决定是否保留 prctl 形态"
contribution_opportunities:
  - kind: discussion
    description: "参与 prctl vs cgroup/BPF 形态之争，尤其跨 cgroup 共享 mm 时 per-cgroup 开关传播语义"
  - kind: testing
    description: "提供关闭 NUMA 平衡的采样开销节省数据，补判断 uAPI 价值的缺口"
generated_at: "2026-10-17T01:30:00"
source_email_count: 5
related_articles: ["sched-20260908-007"]
tags: [numa_balancing, cfs]
---