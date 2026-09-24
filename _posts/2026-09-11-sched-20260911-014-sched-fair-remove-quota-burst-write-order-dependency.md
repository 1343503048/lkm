---
id: sched-20260911-014
subject: 'sched/fair: remove quota/burst write-order dependency'
date: '2026-09-11'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260911092258.660771-1-liuzhe1@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260911092258.660771-1-liuzhe1@kylinos.cn/
authors:
- Zhe Liu
maintainers_involved: []
current_version: v3
patch_series:
- version: v1
  msgid: <20260820033218.214259-1-liuzhe1@kylinos.cn>
  date: 2026-08-20
  summary: 首次移除 quota/burst 写序依赖。
  review_outcome: 承 sched-20260904-004（无量化验证数据为主要保留）。
- version: v2
  msgid: <20260904062013.504236-1-liuzhe1@kylinos.cn>
  date: 2026-09-04
  summary: 配置 burst 独立于 quota 更新；限制移到 refill 路径；新增自测与文档。
  review_outcome: 当日缓存内未获取到 v2 阶段 review 细节。
- version: v3
  msgid: <20260911092258.660771-1-liuzhe1@kylinos.cn>
  date: 2026-09-11
  summary: burst 上限改为独立 max_bw_runtime_us/2；patch 1 去 Cc stable；文档更新。
  review_outcome: 当日无回帖，零 review。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v3 零 review，cgroup 带宽路径评审未开始
  - v3 核心语义刚改为独立上限，兼容性论证待接受
  next_action: 等 sched/fair 与 cgroup 两侧维护者首轮意见
contribution_opportunities:
- kind: testing
  description: 跑新自测用例并补 max_bw_runtime_us/2 上限的边界用例
- kind: review
  description: 核对独立上限与历史隐式限制在全部 quota 取值下等价
generated_at: '2026-09-14T11:35:00'
source_email_count: 2
related_articles:
- sched-20260904-004
tags:
- cfs
- cgroup
title: 'sched/fair: remove quota/burst write-order dependency'
layout: article
---

## TL;DR
Zhe Liu（kylinos）修复 cgroup CPU 带宽 quota/burst 写入顺序依赖的系列发到 v3：v2 时曾考虑直接丢弃用户配置的 burst，v3 改为「保留配置值、refill 时把可用 burst 截到 min(burst, quota)」，并补自测与 cgroup v1/v2 文档。当日与 v2 版本同时入缓存、尚无回帖。本文为增量更新，v1/v2 进展见 <a class="article-ref" href="/lkm/2026/09/04/sched-20260904-004-sched-fair-remove-quota-burst-write-order-dependency.html">sched-20260904-004</a>。

## 背景与问题
cpu.max 与 cpu.max.burst 的写入顺序会影响结果：quota 无限时配置的 burst 会阻止之后安装有限 quota；先升 quota 前更新 burst 可能得到 -EINVAL。根因是 burst 校验隐式依赖「当前 quota」——有限 quota 下最大可配置 burst 被隐式限在 max_bw_runtime_us / 2。

## 技术方案
- 解耦 burst 校验与当前 quota：把原先「相对 quota 的检查」改为独立上限 max_bw_runtime_us / 2（v3 新设计），保住有限 quota 场景既有允许的最大 burst；
- 配置的 burst 在 quota 更新时保持不变（v2 起的立场）；运行时 refill 把实际可用 burst 截为 min(burst, quota)——quota/burst 任意顺序更新都不改变有限 quota 下允许的最大 burst；
- patch 2：selftests/cgroup/test_cpu.c 增加两种写序的覆盖（+40 行）；patch 3：更新 cgroup-v2 与 sched-bwc 文档描述配置值与运行时截断的关系。

## 版本演进与当前进展
*current_version: v3（cover msgid `<20260911092258.660771-1-liuzhe1@kylinos.cn>`，09-11 17:22 入缓存；含 0/3 与 1/3，2/3、3/3 未入缓存）*。

- v1（08-20，承 <a class="article-ref" href="/lkm/2026/09/04/sched-20260904-004-sched-fair-remove-quota-burst-write-order-dependency.html">sched-20260904-004</a>）；
- v2（09-04）：配置 burst 独立于 quota 更新；quota 相对限制移到 refill 路径；新增自测与文档；
- v3（09-11）：burst 上限改为独立的 max_bw_runtime_us / 2；patch 1 去掉 Cc: stable；文档改为描述「配置值独立于当前 quota + refill 时按 quota 截断」。

## Maintainer 意见与讨论焦点
当日缓存内 v3 无任何回帖，未获取到维护者意见（v2 阶段的 review 内容在当日缓存亦不可见，承 <a class="article-ref" href="/lkm/2026/09/04/sched-20260904-004-sched-fair-remove-quota-burst-write-order-dependency.html">sched-20260904-004</a> 的记录：无量化验证数据是当时的主要保留）。

## 合入评估
*likelihood=medium*：问题真实（写序导致 -EINVAL/配置被拦）、修复语义自洽、带自测与文档；但 v3 仍无任何维护者意见，cgroup 带宽控制路径（core.c/fair.c）的评审尚未开始。*blocking_issues*：零 review；v3 刚改了核心语义（独立上限替代 quota 相对限制），需要确认该上限与历史行为的兼容论证被接受；效果无量化数据。*next_action*：等待 sched/fair 与 cgroup 两侧维护者的首轮意见；关注 v1 时被去掉的 Cc: stable 是否影响回合预期。

## 效果评估
无量化数据：系列目标是消除写序敏感性（任意顺序可配置），效果为行为语义改进；邮件窗口内无 benchmark 或复现耗时数字，selftests 的断言结果未入缓存。

## 我可以参与的点
- kind=testing：用 selftests/cgroup/test_cpu.c 的新增用例在 cgroup v1/v2 环境验证两种写序，并可补充 max_bw_runtime_us/2 上限的边界用例（如 quota 接近运行时上限时的 burst 行为）。
- kind=review：核对 v3 的独立上限（max_bw_runtime_us / 2）与 v1/v2 时代隐式限制在所有 quota 取值下等价，尤其是 quota 从无限切换到有限时的过渡行为。

## 参考链接
- v3 cover：https://lore.kernel.org/all/20260911092258.660771-1-liuzhe1@kylinos.cn/
- v3 1/3：https://lore.kernel.org/all/20260911092258.660771-2-liuzhe1@kylinos.cn/
- v2：https://lore.kernel.org/all/20260904062013.504236-1-liuzhe1@kylinos.cn/
- v1：https://lore.kernel.org/all/20260820033218.214259-1-liuzhe1@kylinos.cn/
