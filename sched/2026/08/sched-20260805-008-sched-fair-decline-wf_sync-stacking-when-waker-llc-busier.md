---
id: sched-20260805-008
date: "2026-08-05"
title: "sched/fair: 当唤醒者 LLC 更忙时拒绝 WF_SYNC 堆叠（RFC + Hillf 审查）"
series: "Decline WF_SYNC stacking when waker LLC is busier share"
type: feature
status: under_review
severity: none
merge_likelihood: low
tags: [cfs, load_balance, topology, wake_affine]
authors: ["Vinicius Peixoto <viniciuspeixoto@github.com>", "Hillf Danton <hdanton@sina.com>"]
reviewers: ["Hillf Danton <hdanton@sina.com>"]
related_articles: ["sched-20260804-006"]
emails: ["uid-21117@qq-imap", "uid-21331@qq-imap"]
---

# sched/fair: 当唤醒者 LLC 更忙时拒绝 WF_SYNC 堆叠（RFC + Hillf 审查）

## 摘要

Vinicius Peixoto 提出一个 RFC：当发生 sync wakeup 时，若**唤醒者所在 LLC 域的负载比被唤醒者当前所在 LLC 更忙**，则**不要**因为 `WF_SYNC` 而把 wakee 堆叠到 waker 的 LLC，而是保持 wakee 在原地（或按其既有亲和选空闲 CPU）。这是 sync wakeup 主题下的又一个子方向，与 006/007 形成互补的「反向约束」。

动机：现有 sync 偏好会无条件把 wakee 拉向 waker，但当 waker 的 LLC 已经很忙时，这种堆叠只会制造更多 SMT/LLC 争用，反而拖慢二者。RFC 主张用「LLC 忙闲对比」作为是否应用 sync 偏好的开关。

本日要点：
- **Vinicius 的 RFC（21117）**：给出 `llc_busier_than()` 之类的判定，在 `select_idle_sibling()` 的 sync 分支前先比较 waker LLC 与 wakee LLC 的 avg_load / nr_running，若 waker 侧更忙则跳过 sync 偏好。
- **Hillf 的审查（21331）**：提出两点
  1. `nr_running` 作为忙闲代理过于粗糙，未考虑任务权重与 CPU capacity，可能在异构（不同 capacity CPU）平台上误判；
  2. RFC 在 `select_idle_sibling` 早期 return 可能绕过后续的 `prev_cpu` 亲和保留，导致 wakee 被错误迁到远处。

## 技术细节

RFC 逻辑（示意）：
```
if (wake_flags & WF_SYNC) {
    if (llc_busy_ratio(waker_llc) > llc_busy_ratio(wakee_llc))
        /* 不堆叠：交给常规 idle 选择 / 保持 prev_cpu */
        goto no_sync_pref;
    target = idle sibling of waker;
}
```

Hillf 的反对点：
- `nr_running` 不考虑 `task_h_load` / `cpu_capacity`，在 ARM DynamIQ 或 intel 混合架构上，「忙」的定义失真。
- 提前 `goto` 可能跳过 `if (cpu == prev_cpu && idle)` 这段「优先留在 prev_cpu」的保护，破坏 wake-affine 的稳态。

## 影响与风险

- 影响面：sync wakeup 在「waker 侧过载」时的行为，潜在避免不必要的 LLC 内堆叠。
- 风险：中—高（RFC 阶段）。忙闲判定指标选择直接决定正确性；过早 return 可能引入 wakee 误迁移回退。
- 数据状态：**RFC，无实测**，且 Hillf 已指出需要更稳健的负载度量。

## 评价

与 006/007 一起把 sync wakeup 主题拆成了「往 waker 靠 / 同 SMT 才靠 / waker 忙就别靠」三个互补视角，讨论健康。但本 RFC 的负载度量过于粗糙，需要换成考虑 capacity/weight 的指标并补数据，才有机会脱离 RFC。当前合入可能性低，属于方向性探索。
