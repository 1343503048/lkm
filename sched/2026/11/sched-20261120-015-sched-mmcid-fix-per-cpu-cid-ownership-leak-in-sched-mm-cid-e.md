# sched/mmcid: fix per-CPU CID ownership leak in sched_mm_cid_exit()

## TL;DR

Dominik Maier（Google）回复 Thomas Gleixner 对其「修复 `sched_mm_cid_exit()` per-CPU CID ownership leak」补丁的评审：感谢 tglx 指向其更宏观的 MM CID 重做方案，并表示将改用「execve() 时显式重初始化 MM CID 状态」而非依赖 last-user 退出路径；同时为原提交的两处流程失误致歉。原补丁正文不在当日缓存，属修复方向被维护者重做的收敛讨论。

## 背景与问题

MM CID（memory-mapped Context ID）按进程/CPU 分配，进程退出时 `sched_mm_cid_exit()` 负责回收。原补丁修一处 per-CPU CID 所有权泄漏。Thomas Gleixner 于 11/8 评审后指向其更宏观的 MM CID 重做（`https://lore.kernel.org/all/87mrs8bhp4.ffs@fw13`），主张「在 execve() 时显式重初始化 MM CID 状态」而非依赖 last-user 退出路径。

## 技术方案

当日为讨论、无新补丁：作者接受 tglx 的方向——execve() 显式重初始化比依赖 `sched_mm_cid_exit()` 的 last-user 退出路径更干净；承诺在 QEMU/KVM 复跑原有 reproducer 验证 tglx 的 exec 重初始化方案后，回帖报告结果。作者同时纠正流程：此前漏 Cc `linux-kernel@vger.kernel.org`、误含 `Assisted-by:` tag（改为 changelog 用自然语言描述工具与验证）。

## 版本演进与当前进展

*current_version: v1（原补丁，未在当日缓存，msgid 未获取到）*。今日为作者对维护者评审的回应，方向从「退出路径修泄漏」转为「采纳 tglx 的 exec 重初始化重做」。

## Maintainer 意见与讨论焦点

- **Thomas Gleixner（维护者）**：指向其 MM CID 重做方案，主张 execve() 显式重初始化（前情，11/8）。
- **Dominik Maier（作者）**：接受方向、承诺实测后回帖；为提交流程失误致歉。
- 无 NAK；修复路径被维护者的更宏观方案吸收，属收敛。

## 合入评估

*likelihood=unknown*。原补丁方向被 tglx 的方案取代，最终形态（并入 tglx 的 MM CID 重做 vs 独立修复）未定；作者承诺的验证结果尚未回帖。*blocking_issues*：验证结果未回帖；最终并入方式未定。*next_action*：作者在 QEMU/KVM 验证 tglx 的 exec 重初始化方案后回帖报告。

## 效果评估

无数据（补丁正文与测试结果均未在当日获取到）。

## 我可以参与的点

- **testing**：按作者口径在 QEMU/KVM 复跑原 reproducer，验证 tglx 的 execve() 重初始化方案确实消除 per-CPU CID 泄漏。
- **review**：核对 execve() 显式重初始化对 fork/clone/exec 边界的覆盖是否完整。

## 参考链接

- lore thread（作者回复）: https://lore.kernel.org/all/20261119192306.reply-tglx-sched-mmcid@google.com/
- tglx 的 MM CID 重做: https://lore.kernel.org/all/87mrs8bhp4.ffs@fw13

---
id: sched-20261120-015
date: '2026-11-20'
subject: "sched/mmcid: fix per-CPU CID ownership leak in sched_mm_cid_exit()"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<87cxsfwkm7.ffs@fw13>"
lore_url: "https://lore.kernel.org/all/20261119192306.reply-tglx-sched-mmcid@google.com/"
authors: [Dominik Maier]
maintainers_involved: [Thomas Gleixner]
current_version: v1
patch_series:
  - version: v1
    msgid: null
    date: '2026-11-20'
    summary: "原补丁修 sched_mm_cid_exit() 的 per-CPU CID 泄漏；作者采纳 tglx 的 exec 重初始化重做方向"
    review_outcome: "作者承诺实测后回帖"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["验证结果未回帖", "最终并入 tglx 重做的方式未定"]
  next_action: "作者在 QEMU/KVM 验证 tglx 方案后回帖报告"
contribution_opportunities:
  - kind: testing
    description: "QEMU/KVM 复跑原 reproducer 验证 execve() 重初始化消除泄漏"
  - kind: review
    description: "核对 execve() 重初始化对 fork/clone/exec 边界的覆盖"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: []
tags: [affinity]
---