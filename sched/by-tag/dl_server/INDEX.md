# tag: dl_server

共 4 篇

- [sched-20260827-017](../../2026/08/sched-20260827-017-sched-deadline-fix-dl-server-initialization-for-initially-of.md) `fix/medium/under_review` — 同作者的姊妹 ping：针对"初始离线 CPU 上 DL server 初始化"的修复（8 月 11 日发出）同样**已有 Juri Lelli 的 Acked-by**，08-27 作者催办，等 Peter/Ingo 收取。与 sched-20260827-016 一起构成 deadline server 在 CPU 热插拔/离线生命周期下的两个正确性补丁。补丁正文细节不在本日缓存，未获取到。
- [sched-20260827-016](../../2026/08/sched-20260827-016-sched-deadline-fix-dl-server-divide-by-zero-for-inactive-cpu.md) `fix/high/under_review` — Hui Su 对 8 月 12 日发出的 DL server 除零修复发出 gentle ping：该补丁**已获 Juri Lelli 的 Acked-by**，正等 Peter/Ingo 收取。当日线程无新增技术内容，信息价值集中在合入状态——deadline server 激活路径在 CPU 非活跃时除零的问题已被维护者背书。补丁本体与复现细节不在本日缓存（原文 08-12 发出），此处不重
- [sched-20260802-004](../../2026/08/sched-20260802-004-sched-deadline-use-revised-wakeup-rule-only-for-running-dl-server.md) `fix/medium/merged_tip` — Ingo Molnar 于 2026-08-02 向 Linus 发出 `sched-urgent-2026-08-02` pull request，仅含一个补丁：Gabriele Monaco 修正 deferred DL server 的唤醒逻辑，让它真正做到"延迟唤醒"。改动 1 文件 2 增 1 删，**已合入 tip/sched/urgent，无需跟进**。
- [sched-20260729-002](../../2026/07/sched-20260729-002-sched-deadline-use-revised-wakeup-rule-only-for-running-dl-s.md) `fix/medium/under_review` — Gabriele Monaco（Red Hat）5 月发的 dl_server wakeup rule 修复被搁置两个多月，7-29 ping 之后 Peter Zijlstra（度假归来）直接回复 "sched/urgent this?"，作者确认——该修复大概率很快进入 tip/sched/urgent。跟踪合入即可，无参与空间。
