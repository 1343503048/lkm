---
id: sched-20260828-009
date: '2026-08-28'
subject: 'sched: Add support for long task name'
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: <20260827-tonyk-long_name-v5-0-5fa843782a00@igalia.com>
lore_url: https://lore.kernel.org/all/20260827-tonyk-long_name-v5-0-5fa843782a00@igalia.com/
authors:
- André Almeida
maintainers_involved: []
current_version: v5
patch_series:
- version: v5
  msgid: <20260827-tonyk-long_name-v5-0-5fa843782a00@igalia.com>
  date: '2026-08-28'
  summary: comm 由 16 扩到 TASK_COMM_EXT_LEN=64，旧 UAPI 显式截到 TASK_COMM_LEN，新增 PR_{SET,GET}_EXT_NAME
    + copy_task_comm() + KUnit + selftests；v5 相对 v4 把 helper 限定到 task_struct 并补 len
    边界检查
  review_outcome: 截至 9/5 无任何回帖，无 review 标签
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - v5 零 review，sched/core 与 tracing 侧维护者均未表态
  - task_struct 增大 48 字节只有一句 'no significant change'，无可复现数据
  - 1/6、2/6 为 treewide 改动，需 drm/audit/LSM/net/tracing 多个子系统 ack
  - 新增 prctl UAPI 需与 man-pages/glibc pthread_setname_np 协调
  next_action: 等 tracing/perf 侧对开销与 trace event 字段的意见；作者需补 task_struct 尺寸与 tracing
    开销数据
contribution_opportunities:
- kind: testing
  description: 测量 comm 16→64 的 task_struct 尺寸、上下文切换与 ftrace/perf sched 采样开销变化，补上作者缺失的数据
- kind: new_patch
  description: 评估 1/6+2/6 在 OLK-6.6 的冲突面（get_task_comm 的 BUILD_BUG_ON 与调用点数量）
- kind: discussion
  description: 就长名字是否应同时体现在 /proc/PID/comm 给出使用场景与立场
generated_at: '2026-09-07T22:40:00'
source_email_count: 2
related_articles: []
tags:
- sched_debug
title: 'sched: Add support for long task name'
layout: article
---

## TL;DR

André Almeida（Igalia）8/27 深夜发出 **v5**：把 `struct task_struct` 的 `comm` 从 16 字节扩到 **64**（`TASK_COMM_EXT_LEN`），但**所有既有用户态接口保持 16 字节**（`prctl(PR_SET_NAME/PR_GET_NAME)`，以及 `/proc` 侧由 `proc_task_name()` 生成的命令名字段），只有新增的 `PR_{SET,GET}_EXT_NAME` 才读写完整 64 字节。动机与 kthread 侧的 `6b59808bfe48`（workqueue 名显示进 `/proc/PID/{comm,stat,status}`）同源：上千线程的复杂程序里 16 字节线程名根本不够用于调试与 tracing，而 `cmd_line` 不受 `pthread_setname_np()`/`prctl()` 影响。为了在 `comm` 变大后不越界，系列先做两件 prep：treewide 去掉 `get_task_comm()`、treewide 用新的 `copy_task_comm()` 替换 `memcpy(..., current->comm)`，并给 `copy_task_comm()` 配 KUnit。**8/28 当日及缓存末尾（9/5）无人回帖**——跨 42 文件、要动 `task_struct` 布局与 UAPI 的补丁，这个沉默本身就是信息。

## 背景与问题

16 字节的 `comm` 是内核里最少动的 ABI 之一，但它有两个方向的痛点：

1. **可读性**：多线程程序（GPU/图形栈、大型服务）里线程名被截断到 15 字符，`perf`/`ftrace`/`trace-cmd` 输出中无法区分线程；kthread 已经通过 `6b59808bfe48` 拿到了"显示更长的来源名"待遇，用户态线程没有对等能力。
2. **不能直接放大数组**：`comm` 一旦变成 64 字节，所有依赖 `sizeof(p->comm)` / `sizeof(tsk->comm)` 的代码语义立刻改变——`get_task_comm(buf, tsk)` 这类宏甚至用 `BUILD_BUG_ON(sizeof(buf) != TASK_COMM_LEN)` 把"缓冲区必须正好 16 字节"编译期钉死。所以扩大字段的前置条件是把"复制 `comm`"这件事从一个裸 `memcpy`/`strscpy` 收敛成一个带长度语义的 helper。

作者还解释了为什么不能用 `strscpy()` 直接实现该 helper：在 tracing 路径上实测有可观开销（cover 里给出的 [0] 就是 Steven Rostedt 那封 `20260526190625.3f4aca0a@gandalf.local.home` 的性能讨论），所以 `copy_task_comm()` 的做法是"能 `memcpy` 就 `memcpy`，末尾补 NUL"。

## 技术方案

6 个补丁（v5 diffstat：42 files changed, 173 insertions(+), 76 deletions(-)）：

| # | 补丁 | 作用 |
|---|---|---|
| 1 | treewide: Get rid of get_task_comm() | 去掉把缓冲区大小写死为 16 的宏 |
| 2 | treewide: Replace memcpy(..., current->comm) with copy_task_comm() | 统一复制入口，保证目标缓冲区更小时仍 NUL 结尾 |
| 3 | lib/string_kunit: Add test for copy_task_comm() | `lib/tests/string_kunit.c` +38 行 |
| 4 | sched: Extend task command name with TASK_COMM_EXT_LEN | **本系列核心** |
| 5 | prctl: Add support for long user thread names | 新增 `PR_{SET,GET}_EXT_NAME`（`include/uapi/linux/prctl.h` +3） |
| 6 | selftests: prctl: Add test for long thread names | 扩展现有 `set-process-name.c` +37 行 |

4/6 的三处改动最能说明"兼容性怎么保"：

```
 enum {
 	TASK_COMM_LEN = 16,
+	TASK_COMM_EXT_LEN = 64,
 };
-	char				comm[TASK_COMM_LEN];
+	char				comm[TASK_COMM_EXT_LEN];
```

- `include/linux/sched.h`：`copy_task_comm()` 内部上限由 `min(len, TASK_COMM_LEN)` 抬到 `min(len, TASK_COMM_EXT_LEN)`——**内核内**读者（如 trace event）可以拿到 64 字节。
- `kernel/sys.c` 的 `prctl()`：`PR_SET_NAME`/`PR_GET_NAME` 全部从 `sizeof(me->comm)` 改为显式 `TASK_COMM_LEN`（含 `comm[TASK_COMM_LEN - 1] = 0;` 与 `strncpy_from_user(..., TASK_COMM_LEN - 1)`）——**旧 UAPI 一寸不变**。
- `fs/proc/array.c` 的 `proc_task_name()`：`strscpy_pad(tcomm, p->comm)` → `strscpy_pad(tcomm, p->comm, TASK_COMM_LEN)`，同样是把隐含的 16 字节写成显式。

也就是说：**64 字节的长名字只有新 prctl 拿得到，既有 `/proc` 命令名与 `ps`/`top` 的行为不变**；扩展收益主要落在 tracing/内核内消费者与显式使用新接口的程序上。v5 相对 v4 的两处变化也都是这个取向：`copy_task_comm()` 不再用于 `task_struct` 以外的结构，并新增 `len > TASK_COMM_LEN` / `len < 0` 的检查。

## 版本演进与当前进展

| 版本 | 时间 | 关键变化（作者自述） |
|---|---|---|
| v1 | 2026-05-17 | 初版；引入新的 `strtostr()` |
| v2 | 2026-05-24 | 放弃 `strtostr()`，改用自定义 `copy_task_comm()`（memcpy 优先、回落 strscpy、保证 NUL 结尾）+ 加 KUnit |
| v3 | 2026-06-12 | 去掉 `get_task_comm()` 相关 commit 的简化；`copy_task_comm()` 简化为 memcpy + 末尾 NUL |
| v4 | 2026-07-17 | — |
| v5 | 2026-08-27 | 把 `copy_task_comm()` 限定到 `task_struct`；补 `len` 边界检查 |

验证情况（作者自述，无数字）：`selftests/prctl/set-process-name.c` 在新接口下通过并已扩展；KUnit 已适配 `copy_task_comm()`；跑了与 [0] 相同的 benchmark，"no significant change was found"。**base-commit `73e3f0710014fe6d4ed98cfc02292f6121db7558`**。8/28 缓存里只有 0/6 与 4/6 两封，其余 4 封未收到。

## Maintainer 意见与讨论焦点

未获取到——v5 无任何回帖，v4 及更早版本的评审意见也未进入本次数据源。可预期的争议点（线程里至今没人提，但决定成败）：

- **`task_struct` 膨胀 48 字节**：`comm` 位于 `task_struct` 前部热区，扩到 64 字节会把该字段推过 cache line 边界；作者用 benchmark 说明"无显著变化"，但没有给出被追问过的具体数据。
- **UAPI 面积**：新增两个 `prctl` option 需要与 `man-pages` 侧对齐；glibc 的 `pthread_setname_np()` 是否/何时跟进 64 字节，没人问也没人答。
- **treewide 归属**：1/6 与 2/6 横跨 drm、audit、security/LSM、net、trace events（`include/trace/events/sched.h` 等），这类补丁通常要拆给各子系统维护者 ack，是本系列落地节奏的最大不确定项。

## 合入评估

**likelihood: unclear**。

- 有利：设计取向稳健（旧 ABI 不动、新接口才扩长）；有 KUnit + selftest；从 v1 到 v5 迭代方向一致（持续缩小改动面、减少 helper 适用范围），说明维护者意见在被吸收；痛点真实且有 kthread 先例（`6b59808bfe48`）可援引。
- 卡点：缓存内**零 review**，尤其没有 sched/core 与 tracing 侧维护者表态；treewide 补丁需要多个子系统 ack；`task_struct` 尺寸属于"必须拿数据说话"的类别，而作者只给了一句"no significant change"。
- `next_action`：等 tracing/perf 侧（Steven Rostedt、Namhyung Kim 一类）对开销与 trace event 字段变化的意见；若无人 review，v6 大概仍以重发为主。

## 效果评估

作者提供的唯一量化信息是"沿用 [0] 的 benchmark，未发现显著变化"，未给出任何数字、机器配置或事件计数，因此无法独立评估。可确定的成本是 `comm` 由 16 → 64 使 `task_struct` 增大 48 字节（约每任务一个 cache line 量级），收益是内部消费者与新 prctl 可拿到 64 字节线程名。缓存内无 perf/ftrace 前后对比数据。

## 我可以参与的点

- **补上最缺的那份数据**：`comm` 扩容的真实代价（`task_struct` 尺寸、`sizeof(struct task_struct)` 前后对比、上下文切换 + `perf sched`/ftrace `sched:sched_switch` 采样开销、高线程数进程的 RSS 变化）目前是空白的。给出可复现数字本身就是有效 review，也是决定内部是否跟进的前提。
- **回合成本已经可以量化**：OLK-6.6 侧 `TASK_COMM_LEN = 16`（`include/linux/sched.h:300`）、`char comm[TASK_COMM_LEN]`（同文件 1148），`copy_task_comm()` 完全不存在，且 `get_task_comm()` 宏里就是那句 `BUILD_BUG_ON(sizeof(buf) != TASK_COMM_LEN)`（`include/linux/sched.h:2160`），`PR_SET_NAME/PR_GET_NAME` 仍是 15/16（`include/uapi/linux/prctl.h:56-57`）。也就是说 1/6 的"去掉 `get_task_comm()`"在 6.6 上要覆盖更多调用点，还叠加本地 QoS 补丁对 `task_struct` 的既有改动。**若内部确实需要长线程名，先评估 1/6+2/6 的冲突量，再决定是否只取 `TASK_COMM_EXT_LEN` 的内部版**。
- **检查自家可观测性栈对 16 字节的隐式假设**：任何按 `sizeof(comm)`/固定 16 字节解析 `/proc/*/comm`、tracepoint `comm` 字段或 BPF `bpf_get_current_comm()` 缓冲的工具，在扩长后语义会变（`bpf_get_current_comm()` 仍按传入 buf 大小截断）。这类假设清单可以在上游合入前就准备好。
- **UAPI 立场值得表态**：把长名字只放在新 `prctl` 而不是扩 `/proc/PID/comm`，是兼容性与实用性的折中；如果内部工具链更希望 `/proc` 直接变长，这正是要在上游提出来的时刻。

## 参考链接

- v5 cover: https://lore.kernel.org/all/20260827-tonyk-long_name-v5-0-5fa843782a00@igalia.com/
- v5 4/6: https://lore.kernel.org/all/20260827-tonyk-long_name-v5-4-5fa843782a00@igalia.com/
- v4 cover（作者 cover 中给出）: https://patch.msgid.link/20260717-tonyk-long_name-v4-0-1fedfc870d21@igalia.com
- v3 cover（作者 cover 中给出）: https://patch.msgid.link/20260612-tonyk-long_name-v3-0-7989b66e8a99@igalia.com
- v2 cover（作者 cover 中给出）: https://patch.msgid.link/20260524-tonyk-long_name-v2-0-332f6bd041c4@igalia.com
- v1 cover（作者 cover 中给出）: https://patch.msgid.link/20260517-tonyk-long_name-v1-0-3c282eaa91e2@igalia.com
- strscpy 开销讨论 [0]（作者 cover 中给出）: https://lore.kernel.org/lkml/20260526190625.3f4aca0a@gandalf.local.home/
- 1/6、2/6、3/6、5/6、6/6 邮件正文: 未获取到（本次数据源只含 0/6 与 4/6）
