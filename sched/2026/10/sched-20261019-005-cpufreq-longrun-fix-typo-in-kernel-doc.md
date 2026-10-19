# cpufreq: longrun: fix typo in kernel-doc

## TL;DR

Manuel Ebner 的 cpufreq longrun 驱动 kernel-doc 拼写修复（`longrun_verify_poliy` → `longrun_verify_policy`），今日获 cpufreq 维护者 Viresh Kumar「Applied. Thanks.」直接收取；Qualcomm 的 Zhongqiu Han 复核后提示 checkpatch 有一个可接受的换行警告、并建议把 `/**` 误用为 `/*` 的注释问题另起补丁。

## 背景与问题

`drivers/cpufreq/longrun.c:126` 的 kernel-doc 原型声明把函数名拼错（`longrun_verify_poliy`），导致 kernel-doc 工具报「expecting prototype for longrun_verify_poliy(). Prototype was for longrun_verify_policy()」警告。原补丁 2026-10-17 发出，今日进入收尾。

## 技术方案

单补丁（kernel-doc 注释拼写修正）。Zhongqiu Han 复核：checkpatch 报一个 75 字符换行警告（属工具输出，可接受）；另发现 `longrun.c:21` 一处 `/**` 开头的注释其实不是 kernel-doc，建议改用 `/*` 并单独成补丁（不在本次范围）。

## 版本演进与当前进展

*current_version: v1*。原补丁 10-17 发出，今日 Viresh 应用、Zhongqiu 复核、作者回复「Will do」并询问「pre-git 历史的 init commit 是否能在 future patches 中引用」——属收尾阶段。

## Maintainer 意见与讨论焦点

Viresh Kumar（cpufreq 维护者）已应用。Zhongqiu Han 的补充意见（注释风格另起补丁）为改进建议，不影响本补丁。作者对 pre-git 历史引用方式有疑问，但该疑问针对后续补丁。

## 合入评估

*likelihood=high*。已由维护者应用（进入 cpufreq/pm 树），属打字级修复、零风险。*blocking_issues*：无。*next_action*：等待随 pm 树进入 mainline；可选的 `/**`→`/*` 注释清理由作者另起补丁。

## 效果评估

无性能数据，属文档/注释正确性修复（消除 kernel-doc 警告）。

## 我可以参与的点

- `new_patch`：作者尚未动手的 `/**`→`/*` 注释清理（`longrun.c:21`）可单独成补丁。

## 参考链接

- 原补丁：https://lore.kernel.org/all/20261017071434.1250140-2-manuelebnerli@mailbox.org/
- Viresh「Applied」回帖：https://lore.kernel.org/all/atW6JlE-pkObg9MX@vireshk-B250M-D3H/

---
id: sched-20261019-005
subject: "cpufreq: longrun: fix typo in kernel-doc"
date: 2026-10-19
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261017071434.1250140-2-manuelebnerli@mailbox.org>"
lore_url: "https://lore.kernel.org/all/20261017071434.1250140-2-manuelebnerli@mailbox.org/"
authors: ["Manuel Ebner"]
maintainers_involved: ["Viresh Kumar"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261017071434.1250140-2-manuelebnerli@mailbox.org>"
    date: 2026-10-17
    summary: "修正 longrun.c kernel-doc 原型函数名拼写错误"
    review_outcome: "Viresh 应用；Zhongqiu 建议注释风格另起补丁"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待随 cpufreq/pm 树进入 mainline"
contribution_opportunities:
  - kind: new_patch
    description: "longrun.c:21 的 /**→/* 注释清理可单独成补丁"
generated_at: "2026-10-20T01:30:00"
source_email_count: 3
related_articles: []
tags: [cpufreq]
---