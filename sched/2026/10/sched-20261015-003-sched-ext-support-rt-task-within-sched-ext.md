# sched_ext: Support RT task within sched_ext

## TL;DR
Tengfei Fan（高通）重发（上一版含 HTML 被列表拒收）一份 RFC，探讨如何让 RT 任务（SCHED_FIFO/SCHED_RR）与 sched_ext 在 CPU 放置、CPU 平衡、以及向 schedutil 上报负载三方面协同——延续 LPC 上的讨论。核心诉求是允许 sched_ext 调度「显式选定」的部分 RT 任务，以避免 RT 任务抢占重要 SCX 任务造成帧率抖动与缓存局部性损失。无代码，属设计讨论；Andrea Righi 建议不改核心调度器、走 BPF ops 把 RT 任务纳入 sched-ext 控制。合入评估为 unknown，等待社区设计收敛。

## 背景与问题
Android 游戏/视频/直播场景里，非 RT 线程与 RT 线程协作构帧，按时完成帧（无 jank）是关键性能 KPI，跨 CPU 均衡负载、减少不必要的频率上跳是关键功耗 KPI。以游戏为例，UnityMain/UnityGfxDeviceW 这类高负载普通线程跑在 gold/prime 簇，RT 线程（display HAL、SurfaceFlinger、GPU 相关任务）负载与普通线程相当。

测试中 sched_ext 以 switch-all 模式运行（未设 `SCX_OPS_SWITCH_PARTIAL`），调度非 RT 任务（即「SCX 任务」），RT 任务仍在原生 RT 类。观察到的三个问题：
- **CPU 放置**：RT 任务可落在重要 SCX 任务所用的 CPU 上，导致 SCX 任务被抢占、等待变长或丢缓存局部性；
- **CPU 平衡**：缺少 sched_ext 参与 RT 任务放置时的均衡；
- **负载上报**：RT 任务的负载未如实上报给 schedutil。

作者明确：RT 任务优先级高，抢占本身是预期的；问题在于「更好的 CPU 放置」能减少这类干扰。SCHED_DEADLINE 不在本提案范围。

## 技术方案
作者想探索的方向之一：允许 sched_ext 调度部分「显式选定」的 SCHED_FIFO/SCHED_RR 任务。已有反馈：
- Changwoo（LAVD sched-ext）认可问题的真实性，其方案是把 RT 任务 affine 到有限 CPU 集作为 workaround，但作者认为不够灵活。
- Andrea Righi 认可场景与问题，但**建议不改当前核心调度器**，而是用 BPF ops 把 RT 任务纳入 sched-ext 控制——作者正在这条路径上继续探索。

## 版本演进与当前进展
RFC 首版（纯文本重发，<6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com>），无版本演进。附 LPC 议题与 slides 链接。

## Maintainer 意见与讨论焦点
本日无维护者在线回帖；关键立场来自离线沟通并被作者转述——Andrea Righi 明确反对改核心调度器，倾向 BPF ops 路线。尚未解决的焦点：用 BPF ops 具体如何表达「哪些 RT 任务交给 sched_ext 调度」、如何避免破坏 RT 语义（优先级、PI、push/pull）仍是开放问题。

## 合入评估
*likelihood=unknown*。无代码、无维护者在线表态，属早期设计讨论。*blocking_issues*：方案未定；RT 语义安全性未论证。*next_action*：继续沿 BPF ops 路线细化设计并回帖，吸引 sched_ext 与 RT 维护者（Tejun、Steven）对可行性的评估。

## 效果评估
暂无效果数据。作者描述的是定性问题（抢占/等待/缓存干扰），未见任何量化测量。

## 我可以参与的点
- *discussion*：参与「BPF ops 如何安全地把部分 RT 任务纳入 sched-ext 调度」的设计讨论——尤其 RT 任务的 PI、migration_disabled、push/pull 语义如何在 SCX 下保持。
- *testing*：若后续给出原型，可在 Android 游戏/视频场景下测帧率与功耗 KPI 的变化。

## 参考链接
- RFC 正文：https://lore.kernel.org/all/6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com/
- LPC 议题：https://lpc.events/event/20/contributions/2561/

---
id: sched-20261015-003
date: 2026-10-15
subject: "sched_ext: Support RT task within sched_ext"
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: "<6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com>"
lore_url: "https://lore.kernel.org/all/6b295276-4f42-4f46-b5a2-50c3ac83b412@oss.qualcomm.com/"
authors: ["Tengfei Fan"]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["无代码，方案未定；RT 语义安全性未论证"]
  next_action: "沿 BPF ops 路线细化设计并回帖，争取 sched_ext/RT 维护者评估"
contribution_opportunities:
  - kind: discussion
    description: "参与 BPF ops 如何安全地把部分 RT 任务纳入 sched-ext 的设计讨论（PI/migration_disabled/push-pull 语义）"
  - kind: testing
    description: "若有原型，在 Android 游戏/视频场景测帧率与功耗 KPI"
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: []
tags: [sched_ext, rt]
---