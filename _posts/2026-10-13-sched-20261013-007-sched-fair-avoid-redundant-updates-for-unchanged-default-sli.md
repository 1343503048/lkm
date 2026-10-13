---
id: sched-20261013-007
subject: 'sched/fair: avoid redundant updates for unchanged default slices'
date: 2026-10-13
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CANGjgdnmcm101FneQse==f-YQhKyoARzt20AMyWz21HLQLEFew@mail.gmail.com/
authors:
- Chengfeng Lin
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com>
  date: 2026-10-09
  summary: RFC：默认 slice 未变时走 no-change 捷径
  review_outcome: Peter 批评可读性/正确性，给出 mode-first 简化条件
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 仍为 RFC，作者尚未发正式补丁
  next_action: 作者发正式 patch，Peter 复审后排队
contribution_opportunities:
- kind: testing
  description: 复现 sched_setparam() 微基准，或在真实负载下验证 no-change 捷径收益/回归
- kind: review
  description: 确认 RT-PI 结束后隐含 uclamp 复位等边界语义是否完整
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261009-008
- sched-20261010-002
- sched-20261012-023
tags:
- cfs
title: 'sched/fair: avoid redundant updates for unchanged default slices'
layout: article
---

> **subject**：sched/fair: avoid redundant updates for unchanged default slices

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-008-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261009-008</a> / 20261010-002：Chengfeng Lin 发 RFC——`sched_setparam()` 在参数未变时仍走参数更新路径，SCHED_OTHER 任务用默认 slice 且 slice 未变时直接走 no-change 捷径；原型把每次调用从 618.18ns 降到 163.23ns（省 455ns，约 73.6%）。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-023-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261012-023</a>：Peter Zijlstra 吐槽「太多文字才能找到问题点」、质疑条件正确性（custom_slice/uclamp），给出更简的「mode-first」条件，并追问 PI cost。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-007-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261013-007</a>（今天）：Chengfeng 按 Peter 的 mode-first 比较重写（默认 slice 每次调用 615.98→162.39ns、省 73.66%），重新声明测试并非 PI 测试、并修掉 custom-slice 切换与 RT-PI 后隐含 uclamp 重置两个边界；Peter 回「Yes, this looks reasonable」，作者问是否转正式 patch。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-008-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261009-008</a> / 20261012-023）优化 `sched_setparam()` 在参数未变时的冗余路径开销：`SCHED_OTHER` 任务用默认 slice 时，遗留包装 `_sched_setscheduler()` 把 `attr.sched_runtime` 留 0，而 `p->se.slice` 存实际时长，二者比较即使任务已用当前默认值也继续走更新路径。今天作者澄清两点易被误解处：性能测试不是 PI 测试（是普通 SCHED_OTHER 任务反复调 `sched_setparam(0, priority=0)`）；并明确两个边界问题——(1) 请求自定义 slice 应把任务切到 custom mode（即使时长恰等于当前默认值），(2) RT-PI 结束后 `sched_setparam()` 要把隐含的 `uclamp_min` 从 1024 复位到 0。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-023-sched-fair-avoid-redundant-updates-for-unchanged-default-sli.html">sched-20261012-023</a>）Peter 给出的 mode-first 简化条件：先 `if (!!attr->sched_runtime != !!se->custom_slice) return true;`，再 `if (attr->sched_runtime && attr->sched_runtime != se->slice) return true;`——用「是否设置了 runtime」与「custom_slice 是否一致」判定变化。今天的修订版（`default-slice-peter-v4.patch`）采纳该比较，并保持：默认时长变化、隐含 clamp 需重置、任务当前不在 fair 类时仍走更新；显式 uclamp 请求仍走既有更新路径。作者补充说明修订版已修掉 custom-slice 切换与 RT-PI uclamp 复位两个此前漏掉的场景。

## 版本演进与当前进展
仍为 RFC 修订阶段（无正式 v2 版本号）。今日 Chengfeng 发修订 patch（内部命名 default-slice-peter-v4.patch），Peter 认可「Yes, this looks reasonable」，作者随后问是否发正式 patch。下一步等作者发正式补丁。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：对修订版表态「Yes, this looks reasonable」——相较 10-12 的批评（unreadable、条件正确性、PI cost 疑点）已转向认可。此前对可读性与条件的关切，作者已按 mode-first 比较重写并补充边界说明。
- 焦点已从「是否值得/是否正确」收敛到「正式化」，暂无新争议。

## 合入评估
*likelihood=medium*。Peter 已认可修订方向，但仍是 RFC、作者尚未发正式 patch。*blocking_issues*：需作者发正式补丁并走正常 review 收取。*next_action*：作者发正式 patch，Peter 复审后排队。

## 效果评估
作者今日给出新的三组基准（同 GCC 15.2、同 bare-metal 机器 CPU2、full preemption、performance mode、turbo off、15 样本 × 50 万次调用，probe 与计时分开）：

```
                        Original A    Revision    Original B
Unchanged default slice    615.98      162.39        617.03
Unchanged custom slice     162.69      163.22        162.45
```

默认 slice 场景省约 454ns（73.66%）；custom slice 快路径相对两次 original 中点多约 0.65ns（0.40%）。控制漂移 <0.18%、CV <0.30%。作者仍注明属合成 syscall 微基准。

## 我可以参与的点
- review/testing：可复现作者的 `sched_setparam()` 微基准，或在真实负载下验证 no-change 捷径是否引入可观测收益/回归（作者此前承认「不是应用加速」，真实应用收益仍是社区关注点）。
- discussion：确认边界语义（尤其 RT-PI 结束后的隐含 uclamp 复位路径）是否完整。

## 参考链接
- RFC 线程（20261009 首发）：https://lore.kernel.org/all/CANGjgdnO3HXAxA33cT_rv=on6Qwyf95jgicj6cZKA86Q6tv0Sg@mail.gmail.com/
- 今日修订版回帖：https://lore.kernel.org/all/CANGjgdnmcm101FneQse==f-YQhKyoARzt20AMyWz21HLQLEFew@mail.gmail.com/
