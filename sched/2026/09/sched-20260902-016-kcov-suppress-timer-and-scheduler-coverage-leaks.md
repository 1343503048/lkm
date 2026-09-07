# kcov: Suppress timer and scheduler coverage leaks

## TL;DR

9/2 该主题只有一封邮件：kcov 维护者 Alexander Potapenko 回作者 9/1 的催评审，态度是
`"I think it makes sense"`，但立刻加两个要求——**减少 `kcov_pause()/kcov_resume()` 插入点**
（"Perhaps we could piggyback on some common scheduler action (e.g. locking) to do that?"）和
**把最终判断权推给调度侧**（"If Peter is fine with these annotations being open-coded in
kernel/sched/core.c, then I'm also fine."）。原稿有三处必须纠正：(1) 标题大小写——邮件原文（v2）是
`kcov: Suppress timer and scheduler coverage leaks`（大写 S），v1 才是小写；(2) 「无效果数据」不成立，
v2 封面给出 **3 组 syzkaller A/B、同执行次数下覆盖率 +14–19%、corpus +42–54%**，v1 封面给出 5 组一小时的
中位数与 `__schedule()` +117 字节等规模代价；(3) Peter Zijlstra 并非「看不到他说了什么」——他 8/8 明确
抱怨 v1 只发了半串（"You've send me a partial series; which is the same as not sending me anything at all."），
并主张过一个替代方案（IRQ-exit preempt count）。**真正的卡点因此是调度侧对「在 `kernel/sched/core.c` 里
open-code 标注」尚未认账**，而这是 Potapenko 自己设的前置条件。

## 背景与问题

kcov 的设计契约是：排除中断与调度器自身的覆盖，让 syscall 覆盖率保持「与输入相关」。漏洞在于
`kernel/sched/` 目录本身不插桩，但它**调用的**函数插桩——`sched_clock()`、arch 的 CPU-capacity helper
（`arch_scale_cpu_capacity()`）、`profile_hits()`、`kthread_is_per_cpu()`、`SCHED_HRTICK` 装填等。
当未插桩的 timer/sched 路径在 `in_task()` 为真时运行，这些被调用者的 PC 就会被记进当前任务，
形成非确定性覆盖污染。作者在 v1 封面列出三个 `CONFIG_KCOV_SELFTEST`（他 7/24 先提的 selftest 补丁）
在 x86-64 暴露的用例：deferred hrtimer rearm、`__schedule()` 的 callee、以及 PREEMPT_RT 下的唤醒。

调度侧最难受的是 PREEMPT_RT：RT 把 timer softirq 放进内核线程跑，于是「中断上下文的唤醒」实际发生在
任务上下文，selftest 自旋期间 `try_to_wake_up()` 就会泄漏；非 RT 也有同类问题（pipe write 唤醒读者）。
fork 路径同理：`wake_up_new_task()` 的 CPU 选择与 enqueue 会把 sched/hrtimer/clockevent 覆盖记进父进程，
而且这些路径依赖 runqueue 与 CPU 状态，"coverage varies between identical forks"。

术语上还有一个小摩擦点：补丁注释写 `sched/ is uninstrumented`，Peter 指出这个说法有歧义（作者 9/1 已接受，
v3 会改成 "built without KCOV instrumentation"）。

## 技术方案

机制：新增可嵌套的 `KCOV_PAUSED` 位与 `kcov_pause()/kcov_resume()` guard，在四个点包住
**deferred hrtimer rearm、`__schedule()`、`try_to_wake_up()` 唤醒主体、`wake_up_new_task()`**，
效果是抑制这些函数的插桩 callee，同时**不把 callee 从真正的任务上下文覆盖里排除掉**。

为什么整函数包而不是逐 callee 标注（作者给的理由）：

- `__schedule()`："Annotating each callee would spread exclusions across architectures."
  arm64 上同一类泄漏出现在 `sched_clock()`，且要先压掉另一个 arm64 中断记账泄漏才看得见。
- `try_to_wake_up()`："Wrapping only select_task_rq() would miss SCHED_HRTICK arming during enqueue."
- 跨上下文语义：`KCOV_PAUSED` 在任务被切出后仍保持置位，由被 resume 的那个 `__schedule()` 帧恢复先前状态
  ——这是嵌套 + 任务切换正确性的关键，也是本系列最值得盯的一处。

代价（v1 封面自测）：`CONFIG_KCOV=n` 时 pause 调用编译掉；x86-64 开启 KCOV 时 `__schedule()` 跨 patch 2+3
增长 117 字节、`try_to_wake_up()` 106 字节、`wake_up_new_task()` 88 字节。v1 体量 4 文件 +55/-5，
base-commit `8ba098e6b6ff0db8edf28528d1552be261af30d4`；三个 sched 补丁都挂
`Fixes: 5c9a8750a640 ("kernel: add kcov code coverage")`。

v2 相对 v1 的两处实质变化可确认：patch 1 变为 `kcov: Add a kcov_pause guard`（Potapenko 回帖点名要求
"converging the flag functions"），以及 `kcov_mode` 存取要一致用 `READ_ONCE/WRITE_ONCE`（回应 Sashiko 关于
重排/删除 `kcov_mode` store 的警告，作者认为对这些调用点不成立）。**v2 的 6 个补丁标题只有这一个能确认，
其余未获取到**；v2 封面正文不在缓存中。

## 版本演进与当前进展

- 7/24：作者先投 `CONFIG_KCOV_SELFTEST`（v1 封面引用其 lore 链接
  `20260724192122.73080-1-kmehltretter@gmail.com`，该 msgid 未出现在缓存的 msgid/In-Reply-To 字段中，故不给链接）。
- 8/8（作者本地时间 8/7 21:50–22:50）：**v1 0/5**。当天 Bradley Morgan 在 3/5、4/5、5/5 给
  `Reviewed-by`；Sashiko 机器人在 4/5 提 [Low] 意见（`goto` 手工清理与 `guard()` 混用）；
  Peter Zijlstra 当天 16:44 回封面，只抱怨「发了半个系列」，**未评价机制本身**。
- 8/11：**v2 0/6**（`<20260811154111.64669-1-kmehltretter@gmail.com>`，封面正文未缓存）。
- 9/1：作者回封面点名 Andrey/Alexander/Dmitry 从 KCOV 侧评审，给出 v2 的 syzkaller 数据、
  `CONFIG_KCOV_SELFTEST` 已被修好、以及 v3 计划（把 ttwu 里的 pause guard 提到 preempt guard 之前、
  改措辞、把 Peter 的 IRQ-exit preempt-count 提案拆成面向通用插桩（尤其 KCSAN）的独立补丁）。
- 9/2：Potapenko 回帖——方向认可 + 三个具体要求（见下节）。
- 9/3–9/7：缓存内该主题零新邮件，**没有 v3，也没有 Peter 的表态**。
- 标签面：3 个 Reviewed-by（均来自 Bradley Morgan，非维护者）、`Fixes: 5c9a8750a640` ×3、
  `Assisted-by: Claude:claude-opus-4-8` 与 `Assisted-by: Claude:claude-fable-5`；无 `Acked-by`、无 `Cc: stable`。

## Maintainer 意见与讨论焦点

- **Alexander Potapenko（kcov 维护者，9/2）** 给出四笔：
  1. 方向：`"I think it makes sense, although it would be nice to try to minimize the number of points where
     we insert kcov_pause()/kcov_resume(). Perhaps we could piggyback on some common scheduler action
     (e.g. locking) to do that?"`
  2. 前置条件：`"If Peter is fine with these annotations being open-coded in kernel/sched/core.c,
     then I'm also fine."`
  3. 实现：`"I think consistently using READ_ONCE/WRITE_ONCE here is better. See my suggestion of converging
     the flag functions in 'kcov: Add a kcov_pause guard'."`
  4. 逐条同意作者 v3 计划：ttwu 里 guard 顺序 `"Agreed."`；措辞修改 `"Ack, this is indeed clearer."`；
     IRQ-exit 独立补丁 `"Fixing the IRQ exit should also help with some KMSAN false positives, so I am all
     for it."`
- **Peter Zijlstra（调度维护者）** 是这条线唯一没被满足的门槛。他 8/8 的原话：
  `"You've send me a partial series; which is the same as not sending me anything at all. If you want me to
  look at it, send the complete thing, so I can evaluate the whole thing."` 即 v1 在他那里从未进入评审状态。
  另外他提出的 IRQ-exit preempt-count 被作者明确界定为不可替代（"it only covers work run directly from
  IRQ exit"），所以它是并行动作，不是分歧。缓存内他对本系列**没有任何技术评价**。
- **Bradley Morgan**（3 个 Reviewed-by，8/8）：对 4/5 的说法是 "I don't mind" 并替作者挡了 Sashiko 的意见
  （"this isn't a bug, but a scoped guard"，但承认若考虑将来有人加 early return 则该决策属于 patch 1）；
  对 5/5 提出注释改写建议 `/* Instrumented callees would leak into current here... */`；
  同时公开表达了对双模型 `Assisted-by` 的困惑（"no idea how one patch could be assisted by two AI models...
  tbh idc because this patch is good anyway"）。
- **Sashiko AI 机器人**：4/5 的 [Low] 意见——`try_to_wake_up()` 里 `guard(preempt)()` 与手工
  `kcov_resume()` 清理混用，建议改为 scope-based cleanup helper。这条与 Potapenko 的
  "converging the flag functions" 指向同一处修改。

## 合入评估

**possible**。方向已获 kcov 维护者认可、有 3 个 Reviewed-by、体量小（v1 +55/-5）、`CONFIG_KCOV=n` 时零成本，
且修的是可复现的 selftest 失败，这些都利于合入；但阻塞项同样明确：

1. **调度侧未认账**：Potapenko 把结论挂在 Peter 身上，而 Peter 在缓存内对该系列零技术意见；
   被改的是 `__schedule()`/`try_to_wake_up()`/`wake_up_new_task()` 三个最热路径。
2. **维护者要求减少插入点**：`piggyback on locking` 与「四个 open-code 点」是两种实现，未收敛就会要 v3/v4。
3. **v3 尚未发出**：9/1 作者列的两处改动 + 9/2 Potapenko 的 READ_ONCE/WRITE_ONCE 与 flag 函数收敛都还没落到
   邮件里，v2 当前形态是「被认可但待改」。
4. **数据全是作者自测**，无第三方复测；v2 的 14–19%/42–54% 只能从回帖引用取得，封面正文缺失。
5. 部分 arch 仍需架构特定的插桩排除（作者自述 "Some architectures still need further architecture-specific
   KCOV instrumentation exclusions"），合入后 `CONFIG_KCOV_SELFTEST` 在非 x86 上未必全绿。

## 效果评估

有数据（原稿「无数据」的判断有误），全部出自作者自测：

- v1 封面：syzkaller 在 4 台 2-vCPU PREEMPT_RT VM 上做 **5 组一小时 A/B**，约 110k 执行次数时，
  5 次中位数 corpus **4,142 vs 3,216（+28.8%）**、coverage **54,872 vs 50,940（+7.7%）**，
  且 "No unsuppressed reports"。
- v2 封面（作者 9/1 引用）：3 组 A/B，同执行次数下覆盖率 **+14–19%**、corpus **+42–54%**。
- 定性证据：USB 跑批中来自 deferred rearm / hrtick / scheduler wakeup callee 的 baseline PC 消失；
  fork 跑批中 `__smp_call_single_queue()`、`generic_exec_single()`、`smp_call_function_single_async()`
  的 baseline PC 消失。
- 覆盖面验证：GCC 跨 x86-64/arm32/arm64/MIPS32/PPC32-64/s390/RISC-V32-64/LoongArch/Xtensa/UML，
  x86-64 Clang 与关闭 KCOV 的构建，KCOV selftest 在 x86-64（含/不含 PREEMPT_RT）10/10 启动通过，
  RISC-V 32/64、LoongArch、s390 各 3/3（在先隔离无关的 arch entry leak 之后），
  40 轮 dummy_hcd/g_zero remote-KCOV（x86-64 与 arm64）、400 次重复 fork（x86-64 PREEMPT_RT）。
- 规模代价：`__schedule()` +117B、`try_to_wake_up()` +106B、`wake_up_new_task()` +88B（KCOV 开启、x86-64）。
- **缺口**：没有第三方复测；没有量化「抑制调度/定时器覆盖后 syzkaller 少看到多少 sched 代码」这一反向代价；
  收益集中在覆盖率工具的 fuzzing 效率，对生产内核的 runtime 影响无人测过。

## 我可以参与的点

- **这条线最缺的就是调度侧意见，而且问题已经被 Potapenko 具体化**：在 `kernel/sched/core.c` 的
  `__schedule()`/`try_to_wake_up()`/`wake_up_new_task()` 里 open-code `kcov_pause()`，对比「挂到 rq 加锁/解锁
  的公共动作上」。谁能给出可维护性论证 + 可编译的替代实现，谁就能决定这个系列走 v3 还是直接进 sched/core。
- **验证跨任务切换的 pause 语义**（真实可测的正确性问题）：`kcov_pause()/kcov_resume()` 都以 `current` 为参数，
  而 `__schedule()` 期间 `current` 会变，作者的说法是 `KCOV_PAUSED` 在切出后仍保持、由被 resume 的帧恢复先前
  状态。用 `CONFIG_KCOV_SELFTEST` + PREEMPT_RT 构造「A  preempt 出去、B 在 A 的 pause 窗口内跑起来」的序列，
  检查 B 的任务上下文合法覆盖是否被连带吞掉。
- **量化反向代价**：从 fuzzing 有效性角度给出「被抑制区间内原本能被 syscall 触发的 sched 代码占比」，
  这是缓存内完全缺失的那个数字，也是调度开发者最该出的意见。
- **热路径规模/性能复核**：+117/+106/+88 字节只报了 objdiff，没报性能。在 KCOV=n 与 KCOV=y 两种配置下
  测 `sched` 相关微基准，顺带确认 v3 若改用 scope-based cleanup（Sashiko 与 Potapenko 都指向这个方向）
  不会引入额外开销。
- **AI 辅助标注规范**：三个补丁都带 `Assisted-by: Claude:*`，其中一个同时挂两个模型，评审人公开表示读不懂。
  若你在推内部 AI 辅助提交流程，这是一个可以直接补位的具体问题（`Assisted-by` 的粒度与可审计性）。

## 参考链接

- v2 0/6 封面（正文未缓存；仅作为 9/1 回帖的 In-Reply-To 出现在缓存字段中）：https://lore.kernel.org/all/20260811154111.64669-1-kmehltretter@gmail.com/
- Karl Mehltretter 9/1 催 KCOV 侧评审 + v2 syzkaller 数据 + v3 计划：https://lore.kernel.org/all/apZlkC1lCUFFMKsl@gmail.com/
- Alexander Potapenko 9/2 回复（当日该主题唯一邮件，UID 73513）：https://lore.kernel.org/all/CAG_fn=VR_mfRpbtzgXU=pO2hV9dzgqdrfSPEG_no+vZmC066QA@mail.gmail.com/
- Sashiko 仪表盘对该 patchset 的报告（正文中的真实链接，非 lore）：https://sashiko.dev/#/patchset/20260811154111.64669-1-kmehltretter@gmail.com
- v1（`[PATCH 0/5]` + 3 个 Reviewed-by + Peter 的 partial-series 抱怨 + Sashiko 的 4/5 意见，共 9 封，UID 27674/27675/27678/27679/27698/27998/28000/28001/28191）：
  这些邮件在缓存中的 msgid 均为 IMAP 占位（形如 `<uid-27674@qq-imap>`），**未获取到可链接的真实 msgid**；
  v1 patchset 的 msgid 只能从 Sashiko 脚注读作 `20260807205027.31972-1-kmehltretter@gmail.com`，
  它未出现在缓存的 msgid/In-Reply-To 字段中，故不给出 lore 链接。
- 相关：[[sched-20260902-002]]（同期 `sched: dynamic: Simplify PREEMPT_DYNAMIC`，同属抢占/调度核心的低风险清理线）

---
id: sched-20260902-016
date: '2026-09-02'
subject: 'kcov: Suppress timer and scheduler coverage leaks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260811154111.64669-1-kmehltretter@gmail.com>
lore_url: https://lore.kernel.org/all/20260811154111.64669-1-kmehltretter@gmail.com/
upstream_commit: null
fixes_commit: 5c9a8750a640
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Karl Mehltretter
maintainers_involved:
- Alexander Potapenko
- Peter Zijlstra
patch_series:
- '[PATCH 0/5] kcov: suppress timer and scheduler coverage leaks'
- '[PATCH 1/5] kcov: add kcov_pause()/kcov_resume() helpers'
- '[PATCH 2/5] hrtimer: pause KCOV during deferred rearm'
- '[PATCH 3/5] sched: pause KCOV in __schedule()'
- '[PATCH 4/5] sched: pause KCOV in try_to_wake_up()'
- '[PATCH 5/5] sched: pause KCOV in wake_up_new_task()'
- '[PATCH v2 0/6] kcov: Suppress timer and scheduler coverage leaks'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 'Potapenko 把合入条件写在 Peter 身上（open-code 标注需调度侧认账），而 Peter 在缓存内对该系列零技术意见，v1 只留下一句 “发了半个系列”'
  - '维护者要求压缩插入点（piggyback on locking）与现有四个 open-code 点未收敛，v3 到 9/7 仍未发出'
  - 'kcov_mode 存取需一致使用 READ_ONCE/WRITE_ONCE，且 v2 的 flag 函数需按 Potapenko 的建议收敛'
  - '覆盖率收益全部为作者自测，v2 封面正文未在缓存中（14–19%/42–54% 只能从回帖引用取得），且缺少“抑制后少测到多少 sched 代码”的反向量化'
  - '部分架构仍需 arch specific 的 KCOV 插桩排除，合入后 CONFIG_KCOV_SELFTEST 在非 x86 不保证全绿'
  next_action: '等 v3；在 v2 上从调度侧表态：接受 __schedule()/try_to_wake_up()/wake_up_new_task() 三处 open-code pause，还是给出挂在 rq 锁上的替代实现；同时验证跨任务切换的 pause 恢复语义是否吞掉下一个任务的合法覆盖'
contribution_opportunities:
- '就 “在 kernel/sched/core.c 里 open-code kcov_pause()” vs “挂到 rq 加锁/解锁的公共动作” 给出可维护性论证与可编译替代实现'
- '用 CONFIG_KCOV_SELFTEST + PREEMPT_RT 构造抢占切换序列，验证 __schedule() 中 KCOV_PAUSED 跨 current 变更的恢复是否误吞下一个任务的覆盖'
- '量化抑制调度器/定时器路径后 syzkaller 损失了多少 sched 代码可见性，补上目前完全缺失的反向代价数据'
- '在 KCOV=n/KCOV=y 两种配置下复测热路径规模与性能，并检查 v3 改用 scope-based cleanup 后的开销'
- '为同时挂两个 Assisted-by 模型的做法提出可审计的标注约定（评审人已公开表示读不懂）'
source_email_count: 12
related_articles: []
tags:
- sched/core
- documentation
---
