---
id: sched-20261009-001
date: '2026-10-09'
subject: 'cpuidle: Add the shallow governors'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261008-b4-cpuidle-shallow-v1-1-c19e71127b14@amazon.de>
lore_url: https://lore.kernel.org/all/20261008-b4-cpuidle-shallow-v1-1-c19e71127b14@amazon.de/
authors:
- Roman Kagan
maintainers_involved:
- Christian Loehle
current_version: v1
patch_series:
- version: v1
  msgid: <20261008-b4-cpuidle-shallow-v1-1-c19e71127b14@amazon.de>
  date: '2026-10-09'
  summary: 新增 shallow / shallow_nopoll 两个 governor，运行时与命令行可切换
  review_outcome: Christian Loehle 建议改用 cmdline 参数表达，作者反驳，路线未定
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 实现路线未定：新 governor vs cmdline 参数
  - 无 cpuidle 维护者 review
  next_action: 作者回应 cmdline 方案权衡或收敛出 v2
contribution_opportunities:
- kind: discussion
  description: 就 governor vs cmdline 参数路线给出意见
- kind: review
  description: 审 shallow_nopoll 回退 polling 状态的边界语义
generated_at: '2026-10-10T01:30:00'
source_email_count: 5
related_articles: []
tags:
- idle
title: 'cpuidle: Add the shallow governors'
layout: article
---

## TL;DR
Roman Kagan（Amazon）发补丁新增两个窄用途 cpuidle governor（`shallow` 与 `shallow_nopoll`），让 CPU 停驻最浅 idle 状态并保持 scheduler tick 运行，可在运行时与命令行（`cpuidle.governor=`）双向切换，用于时延敏感负载与 kexec 在线升级场景。当日 Christian Loehle（ARM）质疑「两个 governor 是重复代码」，建议改用 cmdline 参数（如 `cpuidle.max_exit_latency_us=<N>`）表达策略，作者反问 governor 正是策略的载体。方向未定，属早期评审。

## 背景与问题
平台提供的 idle 状态在「唤醒时延」与「节能」之间取舍，但有些场景不值得做这个取舍：时延敏感负载运行期间，或 kexec 在线升级期间（旧内核停负载到新内核恢复之间全是 downtime，深 idle 状态会拉长它）。现有机制都是单向的：`cpuidle.off=1`、`idle=poll`、`idle=halt` 只能在命令行一次性指定、无法撤销；PM QoS 接口（`/dev/cpu_dma_latency` 与 per-CPU `pm_qos_resume_latency_us`）要等用户态起来才能用，覆盖不到新内核的启动阶段。

## 技术方案
新增两个 governor，让 CPU 停驻最浅 idle 状态并保持 scheduler tick 运行：

- `shallow`：总是选择最浅的启用状态（含 polling 状态）。
- `shallow_nopoll`：跳过 polling 状态（polling 虽然唤醒时延最低，但几乎不省电、与 SMT 兄弟竞争核心、在 Intel 上还会阻止 package 进入需要某些 CPU idle 的 P-state），除非它要选的状态超过 PM QoS 时延上限、或所有非 polling 状态都被禁用。

作为 governor，两者都可在 sysfs `current_governor` 写名运行时切换，也可经 `cpuidle.governor=` 命令行指定；在线升级时把 outgoing 内核切过去、传入新内核使其启动即生效、升级完成后再切回节能 governor。两个 governor rating 均为 1（低于其它 governor），不会被默认选中；命令行命名的 governor 不会被后续注册的更高 rating governor 顶替，`cpuidle.governor=` 对整次启动生效。在无 polling 状态（如 arm64）的平台，两者选同样的状态。改动 `drivers/cpuidle/governors/{Makefile,shallow.c}`、`Documentation/admin-guide/pm/cpuidle.rst`、`drivers/cpuidle/Kconfig`，+169/-9 行。

## 版本演进与当前进展
v1 首发（`<20261008-b4-cpuidle-shallow-v1-1-c19e71127b14@amazon.de>`）。当日即有两轮实质讨论，尚无新版本。

## Maintainer 意见与讨论焦点
- **Christian Loehle（ARM）**：① 指出 sysfs 已可按 CPU 按状态禁用 idle state（`echo 1 > .../stateX/disable`），质疑是否真需要新 governor；② 更倾向用命令行参数表达（构想 `cpuidle.max_exit_latency_us=<N>`，对适用状态写 disable 属性），理由是「两个 governor 是重复的维护与文档负担」。
- **Roman Kagan（作者）**：反驳逐 CPU 逐状态的命令行配置不现实，认为「单一选项表达全局策略」正是 governor 的职责，反问「两个简单、窄用途的 governor 到底哪里不对」。

分歧核心：新增 governor 表达策略 vs 用 cmdline 参数 + 既有 disable 机制表达。目前双方各执一词，未见第三方表态。

## 合入评估
*likelihood=unknown*。v1 刚发出，无维护者（Rafael Wysocki / cpuidle 维护者）表态，且「新 governor vs cmdline 参数」的实现路线尚在争论。*blocking_issues*：① 实现路线未定（重复代码负担是 Christian 的核心关切）；② 无 cpuidle 维护者 review。*next_action*：作者回应 Christian 的 cmdline 方案权衡，或收敛出 v2。

## 效果评估
暂无效果数据。作者仅定性论证 polling 状态的副作用与在线升级场景的 downtime 拉长风险，未附 benchmark。是否采用取决于「运行时切换 + 覆盖新内核启动阶段」这一诉求是否足以正当化两个新 governor 的维护成本，属设计权衡、无量化支撑。

## 我可以参与的点
- `discussion`：就「governor vs cmdline 参数」两条路线给出意见——尤其是否已有真实生产场景需要「从旧内核经 kexec 传到新内核」这一 cmdline 无法覆盖的运行时切换诉求。
- `review`：审 `shallow_nopoll` 在「所选状态超 PM QoS 时延上限」时回退到 polling 状态的边界语义是否正确。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261008-b4-cpuidle-shallow-v1-1-c19e71127b14@amazon.de/
- Christian Loehle 回复: https://lore.kernel.org/all/e18bd763-0d6d-4bfd-b59e-78f952c94aa2@arm.com/
- Roman Kagan 回应: https://lore.kernel.org/all/asjaR_aPwevvBw_O@ub9ea591b72db54.ant.amazon.com/
