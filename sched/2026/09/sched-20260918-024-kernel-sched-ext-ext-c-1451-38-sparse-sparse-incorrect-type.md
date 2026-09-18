# kernel/sched/ext/ext.c:1451:38: sparse: sparse: incorrect type in initializer (different address spaces)

## TL;DR
kernel test robot 的 sparse（W=1）报告：`kernel/sched/ext/ext.c:1451:38` 初始化器把 `struct task_struct [noderef] __rcu *` 赋给 `struct task_struct *`，地址空间标注不匹配；同报告还列出 `rt.c` 多处 donor 的 `__rcu` 标注缺失。定位到 commit bba2c3615bd6（sched_ext 源码迁移，3 个月前）。当前无人认领。

## 背景与问题
sparse（v0.6.5-rc1，sparc64-linux-gcc 15.2.0，sparc-randconfig）在 master（head 9b87fdc9af2f）上报告：`ext.c:1451:38` 及 `rt.c`（1498/1826/1517/1518/1579/1605/1627 等）对 `donor`/`sd`/`curr` 的 `__rcu` 标注缺失，属 proxy/执行上下文拆分后 RCU 注解未补齐一类问题。报告建议 Fixes: bba2c3615bd6。

## 技术方案
无补丁——静态分析报告。修复方向：补齐相关 `donor`/`curr`/`sd` 指针的 `__rcu` 标注或使用 `rcu_dereference` 系列访问。

## 版本演进与当前进展
- 首报（09-18，`<202609180902.DfxdJTuY-lkp@intel.com>`）：本日无后续。

## Maintainer 意见与讨论焦点
- 无维护者回应。属 0-day robot 报告。

## 合入评估
likelihood=low。纯 W=1 静态告警、无运行时影响且无认领人。blocking_issues：无认领者。next_action：sched_ext maintainer（Tejun）或相关作者认领，补齐 `__rcu` 标注并加 Fixes/Closes 标签提交修复。

## 效果评估
无性能/运行时影响；sparse W=1 编译期地址空间告警。

## 我可以参与的点
- kind=new_patch：补齐 `ext.c`/`rt.c` 中 `donor`/`curr` 的 `__rcu` 标注（加 Fixes/Reported-by/Closes 标签）。

## 参考链接
- lore（报告）: https://lore.kernel.org/all/202609180902.DfxdJTuY-lkp@intel.com/

---
id: sched-20260918-024
date: '2026-09-18'
subject: 'kernel/sched/ext/ext.c:1451:38: sparse: sparse: incorrect type in initializer (different address spaces)'
subsystem: sched
type: bug
status: stalled
severity: low
thread_root_msgid: '<202609180902.DfxdJTuY-lkp@intel.com>'
lore_url: 'https://lore.kernel.org/all/202609180902.DfxdJTuY-lkp@intel.com/'
authors:
  - 'kernel test robot'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<202609180902.DfxdJTuY-lkp@intel.com>'
    date: '2026-09-18'
    summary: 'sparse 报告 ext.c/rt.c 的 __rcu 标注缺失'
    review_outcome: '无回应'
upstream_commit: null
fixes_commit: 'bba2c3615bd6'
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '无修复者认领'
  next_action: '补齐 donor/curr 的 __rcu 标注并提交修复'
contribution_opportunities:
  - kind: new_patch
    description: '补齐 ext.c/rt.c 的 __rcu 标注（加 Fixes/Closes 标签）'
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - sched_ext
  - sched_debug
---