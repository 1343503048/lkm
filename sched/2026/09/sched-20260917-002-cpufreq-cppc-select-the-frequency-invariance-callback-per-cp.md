# cpufreq: CPPC: Select the frequency-invariance callback per CPU

## TL;DR
Christian Loehle 的 CPPC v7 系列尾部两枚补丁（19/20、20/20）修 FIE（frequency invariance）回调的空指针缺陷：共享 policy 下非 PCC CPU 会被装上 PCC tick 回调、或离线成员/热加 policy 引用不存在的 FIE worker，最终调用 NULL 函数指针。两补丁均 Fixes: 997c021abc6e、Cc: stable，属明确的 bug 修复。

## 背景与问题
`cppc_cpufreq_cpu_fie_init()` 只为使用 PCC 计数器传输的 CPU 初始化延迟工作，但只要共享 policy 里任一 CPU 用 PCC，就为整个 policy 安装 PCC tick 回调。FIE 开启后，非 PCC CPU 会排入未初始化的 irq_work，运行时调用 NULL 函数指针。另一路径：policy 可初始化一个离线的 PCC 成员，该 CPU 上线时回调通过缺失的 `kworker_fie` 排队并解引用 NULL；热加 PCC policy 也会遇到同样的缺失 worker。两处都会导致内核崩溃。

## 技术方案
- 19/20（Select the frequency-invariance callback per CPU）：按每 CPU 记录的 work 初始化状态分别选择回调；处理器移除可能先于回调注册取消发布 CPC 描述符，因此不能再靠重新查询计数器传输方式来选择直读/PCC；改为在所有计数器初始化完成后再注册回调，避免部分注册的 policy 状态。
- 20/20（Create the FIE worker before enabling PCC callbacks）：在 policy 初始化遇到 PCC 计数器时就创建 worker（在初始化其 work、发布回调之前），串行化创建并复用到驱动 teardown；worker 分配失败则该 policy 不注册 FIE，但全局 FIE 设置保持不变，让直读 policy 独立、既有 policy 仍能排空。

## 版本演进与当前进展
这两枚是 CPPC v7（20 枚系列，cover `<20260916162805.1039247-1-christian.loehle@arm.com>`）的尾部补丁，本次窗口只收到 19/20 与 20/20。早期版本不在本次分析窗口内。

## Maintainer 意见与讨论焦点
当日无维护者针对这两枚补丁回帖。两枚均带 Fixes: 997c021abc6e（"cpufreq: CPPC: Update FIE arch_freq_scale in ticks for non-PCC regs"）与 Cc: stable，属回归修复。

## 合入评估
likelihood=high。明确的空指针解引用修复，带 Fixes 与 stable 标签，改动集中在 drivers/cpufreq/cppc_cpufreq.c；无争议点，等待 cpufreq 维护者（Viresh/Rafael）收取。blocking_issues：无实质阻塞，缺维护者 Ack。next_action：等待 cpufreq 维护者评审收取。

## 效果评估
无性能数据；属正确性修复。作者以 NULL 解引用崩溃路径为修复对象，未给出 benchmark。

## 我可以参与的点
- kind=testing：在带 PCC（platform 通信）CPPC 的 arm64 平台上做 CPU 热插拔 + 离线成员上线，验证 FIE 回调与 worker 生命周期不再崩溃。
- kind=review：核对"处理器移除先于回调注册取消发布 CPC 描述符"这一时序是否在 x86 共享内存 CPPC 上同样成立。

## 参考链接
- lore（v7 cover）: https://lore.kernel.org/all/20260916162805.1039247-1-christian.loehle@arm.com/

---
id: sched-20260917-002
date: '2026-09-17'
subject: 'cpufreq: CPPC: Select the frequency-invariance callback per CPU'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260916162805.1039247-1-christian.loehle@arm.com>'
lore_url: 'https://lore.kernel.org/all/20260916162805.1039247-1-christian.loehle@arm.com/'
authors:
  - 'Christian Loehle'
maintainers_involved: []
current_version: v7
patch_series:
  - version: v7
    msgid: '<20260916162805.1039247-1-christian.loehle@arm.com>'
    date: '2026-09-17'
    summary: 'CPPC v7 系列尾部两枚：19/20 每 CPU 选择 FIE 回调、20/20 提前创建 FIE worker，修 NULL 指针解引用'
    review_outcome: '暂无评审'
upstream_commit: null
fixes_commit: '997c021abc6e'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待 cpufreq 维护者评审收取'
contribution_opportunities:
  - kind: testing
    description: '在 PCC CPPC arm64 平台做 CPU 热插拔验证 FIE 生命周期'
  - kind: review
    description: '核对取消发布 CPC 描述符时序在 x86 共享内存 CPPC 上是否一致'
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles: []
tags:
  - cpufreq
---
