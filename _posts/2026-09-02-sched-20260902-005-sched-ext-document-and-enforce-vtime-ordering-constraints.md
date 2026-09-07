---
id: sched-20260902-005
date: '2026-09-02'
subject: 'sched_ext: document and enforce vtime ordering constraints'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- Tejun Heo
- Tao Cui
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3 未见维护者结论性意见（缓存正文缺失），是否还需下一轮不明
  - 1/2 仅文档化，无运行时强制手段，是否满足 enforce 的目标存疑
  - 无回绕场景的测试或线上案例支撑
  next_action: 补一个 cvtime 回绕的可复现测试，并在 v3 线程追问 Tejun Heo 的结论
contribution_opportunities:
- 编写 scx_flatcg cvtime 回绕的 kselftest/压测，验证 cgv_node_less() 修复
- 建议把 dsq_vtime 的 2^63 约束从注释升级为 debug 期检查
- 在 v3 封面线程推动维护者给出明确结论
source_email_count: 2
related_articles: []
tags:
- sched_ext
- documentation
title: 'sched_ext: document and enforce vtime ordering constraints'
layout: article
---

## TL;DR

Tao Cui 把 sched_ext vtime 排序的两条隐含前提显式化：同一 DSQ 内的 vtime 差必须小于 2^63，
`scx_flatcg` 的 `cgv_node_less()` 必须回绕安全。9/2 出 v3，Tejun Heo 逐补丁回过 v2 也回了 v3 封面，
但缓存里看不到 v3 的结论性意见。

## 背景与问题

sched_ext 的 dsq（调度队列）按虚拟时间（vtime）排序，其中 `dsq_vtime` 依赖
rolling-cursor 的取序要求；`scx_flatcg` 的 `cgv_node_less()` 在 vtime 回绕（wraparound）
时也存在比较错误风险。本期 v3 把这两点文档化并加强制/修复。

## 技术方案

系列 `sched_ext: document and enforce vtime ordering constraints`（v3，UID 72766 0/2
封面）：
- 1/2 `sched_ext: document the rolling-cursor requirement for dsq_vtime`（72767）
- 2/2 `sched_ext/scx_flatcg: make cgv_node_less() wraparound-safe`（72781）
- 演进：v2（UID 72288 1/2、72291 2/2）→ v3；Re: 72648（v3 2/2）、73048（v3 0/2）。

## 版本演进与当前进展

- 当前状态：**under_review**（v3）。
- 合入可能性 medium/high；文档 + 回绕安全的明确修复。
- 与 004（NMI 拒绝）、006（NULL deref）同为当日 sched_ext 集群。

## Maintainer 意见与讨论焦点

- 唯一的 reviewer 就是维护者本人：Tejun Heo 对 v2 的两个补丁分别回帖（72287 针对 1/2、72288 针对 2/2），
  Tao Cui 9/2 09:21 针对 2/2 作答（72646），当天 10:48 出 v3，Tejun 又回了 v3 封面（73043）。三轮往返都
  只有这两人参与，没有第三方（sched_ext 其它 maintainer、BPF 侧）介入。
- Tejun 抓的点在数值边界表述上：1/2 新增注释里 "should stay within half the u64 range (2^63) of each other
  so that time_before64() ordering remains well-defined." 被直接引用回问；2/2 里 "long-running host. At the
  wrap instant the plain comparison puts the wrapped node behind everything else permanently." 同样是引文。
- 缓存中这些回帖仅存 200 字节引文头，看不到 ack/reviewed-by，也看不到反对意见——既无认可证据也无 NAK 证据。

## 合入评估

**中**。文档 + 一个比较器修复，体量小、方向无争议，理论上不该慢；卡点是 v3 之后还需不需要第四轮
（v2→v3 已经是第二轮修改），以及 1/2 只加注释、没有配套运行时断言，Tejun 是否接受「靠文档约束 BPF 作者」
这一点在缓存中看不到答案。

## 效果评估

暂无效果数据。作者给的是机理推演而非测量（72767）："cgv_node_less() compares cvtimes with a plain <,
which misorders once cvtime wraps: the wrapped node lands at the front of the tree while the unwrapped
ones get stuck…"——回绕后被包裹节点永久排在最前。属作者判断，未见测试数据，也没人报告过线上真实回绕案例。

## 我可以参与的点

- 写一个把 cvtime 推到 u64 边界附近的 scx_flatcg 测试：这是全线程最缺的东西，双方都只在推演。
- 就 1/2 提出：仅文档化不够，是否应在 `scx_bpf_dsq_insert_vtime()` 加一次 2^63 距离检查（或 debug 下 WARN）。
- v3 的实质结论仍空缺，可以直接在 73043 之后追问 Tejun 是否接受，推动收口。

## 参考链接

- 004 sched_ext：拒绝 NMI 调用会拿锁 kfuncs
- 006 sched_ext：修复 select_cpu_and 空指针解引用
