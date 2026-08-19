# tag: dl_server

共 2 篇

- [sched-20260802-004](../../2026/08/sched-20260802-004-sched-deadline-use-revised-wakeup-rule-only-for-running-dl-server.md) `fix/medium/merged_tip` — Ingo Molnar 于 2026-08-02 向 Linus 发出 `sched-urgent-2026-08-02` pull request，仅含一个补丁：Gabriele Monaco 修正 deferred DL server 的唤醒逻辑，让它真正做到"延迟唤醒"。改动 1 文件 2 增 1 删，**已合入 tip/sched/urgent，无需跟进**。
- [sched-20260729-002](../../2026/07/sched-20260729-002-sched-deadline-use-revised-wakeup-rule-only-for-running-dl-s.md) `fix/medium/under_review` — Gabriele Monaco（Red Hat）5 月发的 dl_server wakeup rule 修复被搁置两个多月，7-29 ping 之后 Peter Zijlstra（度假归来）直接回复 "sched/urgent this?"，作者确认——该修复大概率很快进入 tip/sched/urgent。跟踪合入即可，无参与空间。
