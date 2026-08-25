# posix-cpu-timers: use-after-free in exec failure path

# posix-cpu-timers: exec 失败路径 use-after-free


## TL;DR
修复 exec 失败路径中 posix-cpu-timers 引用已释放 mm/sighand 的 use-after-free。附 Fixes 标签与 KASAN 报告，合入可能性高。

## 背景与问题
进程 exec 一个二进制时若中途失败（如解释器缺失、权限问题），内核会回滚到原 mm 与 sighand。但 `posix-cpu-timers` 的定时引用可能仍指向**切换后的旧 mm 与旧 sighand**，而这两者（尤其在新 mm 已 commit 的那一刻）可能已被释放。任何后续 timer 触发对该 mm/sighand 的访问即构成 use-after-free，可被 KASAN 捕获。

## 技术方案
在 exec 失败的回滚路径，显式清理或重新绑定 posix-cpu-timers 到当前仍然有效的 mm 与 sighand，确保在 mm/sighand 切换完成前 timers 不会悬空引用。邮件附 `Fixes` 标签指向引入该 exec 回滚时序的提交，以及 KASAN 报告作为实证。

## 版本演进与当前进展
v1（2026-08-03）。邮件附 KASAN 堆栈与 Fixes 标签。尚未见 maintainer 回复。

## Maintainer 意见与讨论焦点
暂未见 maintainer 回复。预期 Thomas Gleixner（posix timers 维护者）会关注 exec 回滚语义的正确性，方向应为认可（UAF 修复属共识）。

## 合入评估
合入可能性 high。有 KASAN 实证 + Fixes 标签，是典型应被快速接收的稳定性修复。

## 效果评估
邮件提供 KASAN 报告作为效果证据，属「有实证」的 UAF 修复。无性能基准，本不应有。

## 我可以参与的点
- 构造 exec 失败用例（解释器缺失的脚本、无执行位的二进制）在 KASAN 内核复现，打补丁后验证 UAF 消失，回帖 tested-by。

## 参考链接
- lore thread: 未获取到

---
subject: "posix cpu timers use after free in exec failure path"
id: sched-20260803-011
date: 2026-08-03
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [unknown]
maintainers_involved: [Thomas Gleixner, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "exec 失败且 task 已切换 mm 后，posix-cpu-timers 仍引用旧 mm + 旧 sighand，二者可能已被释放，构成 use-after-free。补丁在 exec 失败回滚路径显式清理/重新绑定 timers 到当前有效 mm 与 sighand。"
    review_outcome: "邮件附 Fixes 标签与 KASAN 报告；尚未见 maintainer 回复。"
upstream_commit: null
fixes_commit: "unknown"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 Thomas Gleixner 对 exec 回滚语义的认可；有 Fixes + KASAN 证据，属应被快速接收的 UAF 修复。"
contribution_opportunities:
  - kind: testing
    description: "可在开启 KASAN 的内核上构造 exec 失败场景（如 exec 一个无执行权限/解释器缺失的二进制）复现 UAF，打补丁后验证不再触发，回帖 tested-by。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: []
tags: [posix_cpu_timer, uaf, mm]
---
