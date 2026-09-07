# sched: dynamic: Simplify PREEMPT_DYNAMIC

## TL;DR

Mark Rutland 的 `sched: dynamic` 精简系列 v2（0/6，08-04 投递）在 09-02 已被 Peter Zijlstra 全部合入 tip:sched/core，本日（09-03）线程里只剩 Jinjie Ruan 把自己的 08-07 提问顶起来催问「Hi Mark, What do you think?」。真正有信息量的是这个 ping 之前发生的事：Jinjie 在 review 中发现本系列删掉了 `preempt_dynamic_none` / `preempt_dynamic_voluntary` 两个枚举值却没有同步 `preempt_modes[]`，导致 `preempt_model_str()` 与 `sched_dynamic_show()` 索引错位——backtrace 里的抢占模型串是错的，`/sys/kernel/debug/sched/preempt` 输出为空。Mark 09-02 承认「Ugh, yes」，Peter 当天照常合入 6 个补丁，Mark 随即单独发修复并以 `Reported-by: Jinjie Ruan` 在同日进 tip（`ef9293b3b797`，`Fixes: 9650ce11f2e3`）。

## 背景与问题

`PREEMPT_DYNAMIC` 的实现历史上背了两套架构侧开关（`HAVE_PREEMPT_DYNAMIC_CALLBACK` 与 `HAVE_PREEMPT_DYNAMIC_KEY`），`{cond,might}_resched()`、`preempt_schedule{_notrace}`、`irqentry_exit_cond_resched` 各自带着条件编译与静态分支包装，抢占模型还维护了一份与枚举值手工对齐的字符串表 `preempt_modes[]`。本系列的目标是把这些遗留分支收敛掉：让 `PREEMPT_DYNAMIC` 直接依赖 `CONFIG_ARCH_HAS_PREEMPT_LAZY`，移除 `HAVE_PREEMPT_DYNAMIC_{CALLBACK,KEY}`，简化各调用点与抢占模型访问器。

收敛过程中暴露的具体缺陷是：随着 `preempt_dynamic_none`、`preempt_dynamic_voluntary` 两个枚举值被删，`preempt_modes[]` 仍是 `"none", "voluntary", "full", "lazy", NULL`，而 `sched_dynamic_show()` 靠 `IS_ENABLED(CONFIG_PREEMPT_RT) || IS_ENABLED(CONFIG_ARCH_HAS_PREEMPT_LAZY)` 乘 2 的方式跳过前两项，字符串表长度还要再按 `!IS_ENABLED(CONFIG_ARCH_HAS_PREEMPT_LAZY)` 修正。枚举值与字符串表各管一处，索引一旦错位就是 `preempt_model_str()` 给错模型串、`/sys/kernel/debug/sched/preempt` 空输出。这是 Jinjie Ruan 在 review 中报出来的，Mark 的答复是「This is all a bit messy, given the enum value isn't used to define the string array」。

## 技术方案

已进 tip:sched/core 的 6 个补丁（全部由 Peter Zijlstra 于 09-02 提交）：

- `d3d16750693b` sched: dynamic: Make PREEMPT_DYNAMIC depend on ARCH_HAS_PREEMPT_LAZY
- `88e0b3bb9930` sched: dynamic: Simplify {cond,might}_resched()
- `b9d267b9d632` sched: dynamic: Simplify preempt_schedule{,_notrace}
- `aa4178f63847` sched: dynamic: Simplify irqentry_exit_cond_resched
- `5b9a28eeed37` sched: dynamic: Remove HAVE_PREEMPT_DYNAMIC_{CALLBACK,KEY}
- `9650ce11f2e3` sched: dynamic: Simplify preempt model accessors

外加针对 review 发现问题的独立修复 `ef9293b3b797` sched: dynamic: Fix preemption model strings（`kernel/sched/core.c` 1 处 + `kernel/sched/debug.c` 10 行简化，共 3 增 9 删）：

- `preempt_modes[]` 改为 `{"full", "lazy", NULL}`，与仅存的两个枚举值对齐。
- `sched_dynamic_show()` 删掉 `int i = (IS_ENABLED(CONFIG_PREEMPT_RT) || IS_ENABLED(CONFIG_ARCH_HAS_PREEMPT_LAZY)) * 2;` 这个偏移起点和「先数数组长度再按 `!IS_ENABLED(CONFIG_ARCH_HAS_PREEMPT_LAZY)` 修正」的循环，改为 `for (int i = 0; preempt_modes[i]; i++)` 走到 NULL 结束。理由写在提交说明里：既然 `CONFIG_PREEMPT_DYNAMIC` 现在依赖 `CONFIG_ARCH_HAS_PREEMPT_LAZY` 且只剩 full/lazy 两个模式，`sched_dynamic_show()` 不再需要跳过任何模型串。

评审中确定保留的一处设计：5/6 不额外 `select JUMP_LABEL`。Mark 的理由是它功能上不必要、`!HAVE_PREEMPT_DYNAMIC_KEY`（例如 x86）此前也没 select、相关 defconfig 本来就 `CONFIG_JUMP_LABEL=y`，而**不 select 才能在测试时把它关掉**，因此倾向维持现状。

## 版本演进与当前进展

- 07-03 v1（`[PATCH 0/5]`）；07-30 Mete Durlu 在 s390 上给出体积对比数据。
- 08-04 v2（`[PATCH v2 0/6]`，即本篇主题）。08-05 ~ 08-07 Jinjie Ruan 对 2/6、3/6、4/6、5/6、6/6 及封面逐条回帖，Mete Durlu 与 Shrikanth Hegde 也在封面线程发言（这几封邮件的正文与 msgid 未被缓存保留，具体意见无法确认）。
- 09-01 23:26 ~ 09-02 00:05（北京时间）Mark Rutland 集中回答 Jinjie：JUMP_LABEL 保持不 select；承认 6/6 里那些注释「Evidently keeping them was confusing, so I'll delete them」；对抢占模型串问题回「Ugh, yes」，并预告 `sched_dynamic_show()` 也要改、真正的一致性需要「a bit more rework」。
- 09-02 09:37（CET）Peter Zijlstra 把 6 个补丁全部提交到 tip:sched/core；同日 Mark 发出抢占模型串修复（AuthorDate 11:16 UK），09-02 12:54 CET 由 Peter 提交为 `ef9293b3b797`，带 `Reported-by: Jinjie Ruan` 与 `Fixes: 9650ce11f2e3`。
- 本日 09-03 09:30 Jinjie Ruan 在封面线程顶起自己 08-07 的一封邮件催问，尚未得到回答（该 08-07 原文正文未保留，无法确定具体待答内容）。
- 本系列已进入 tip，不存在 v3 计划；Mark 提到的「by construction 保证枚举与字符串表一致」是可能出现的后续重构。

## Maintainer 意见与讨论焦点

- **Mark Rutland（作者，Arm）** 本日之前的三点表态：
  - 拒绝在 5/6 里 `select JUMP_LABEL`：「Not selecting JUMP_LABEL allows it to be turned off for testing, so I would prefer to leave it as-is.」——保留可关闭测试的能力优先于配置自洽。
  - 对 6/6 的注释：「I had left those lines to indicate that those modes were deliberately not selectable with preempt_dynamic. Evidently keeping them was confusing, so I'll delete them.」
  - 对抢占模型串：「Ugh, yes. We'll also need to fix up `sched_dynamic_show()`, since it has logic to conditionally skip "none" and "voluntary". This is all a bit messy, given the enum value isn't used to define the string array. I'll see if I can figure a way to make that consistent by construction, but that probably needs a bit more rework...」
- **Peter Zijlstra（committer）**：用行动表态——09-02 一次性合入 6 个补丁，并在同一天接受并提交修复，没有要求重投 v3，也没有把修复压回原补丁。这实际确立了本线程的讨论焦点：**问题已被记录，剩余工作是把「枚举 ↔ 字符串表」的一致性做成 by construction**，而不是撤回已合入的简化。
- **Jinjie Ruan（华为，报告者）**：`Reported-by` 落在他身上；本日的 ping 是全线程当天唯一的新内容，说明他仍在跟未回答的问题。
- **Mete Durlu / Shrikanth Hegde（IBM）**：在 v1/v2 封面提供过 s390 侧验证（正文未保留，仅有 07-30 那封的体积数据可引）。

## 合入评估

likelihood: **likely**（已合入）。

依据：6 个补丁与后续修复都已在 09-02 进入 `tip:sched/core`，committer 是 Peter Zijlstra，commit-id 由 tip-bot2 通告，无回退迹象；review 阶段的三条意见（JUMP_LABEL、注释、模型串）都已有明确处置，其中两条落到代码、一条被作者说明后保留；`Reported-by`/`Fixes` 链完整。

卡点（仅剩余工作层面）：一是 Mark 自认当前的修法是「a bit messy」，「make that consistent by construction ... probably needs a bit more rework」，即枚举与字符串表的对齐仍靠人工维护，后续可能再来一版重构；二是本日的 ping 尚未回答；三是 `Fixes: 9650ce11f2e3` 指向本系列自身，因此该 bug 只存在于「已合入简化、未合入 fix」这个窗口，是否需要向 stable 传播取决于各树是否回合过本系列，邮件中没有 stable 相关讨论。

## 效果评估

唯一可引的数据是 Mete Durlu 在 v1（0/5）上做的 s390 体积测量（07-30）：`git clean -xfd` 后全编译，vmlinux 从 409306880 降到 407987680（约 1.3 MB），`bloat-o-meter` 为 `add/remove: 67/50 grow/shrink: 731/2058 up/down: 54992/-161849 (-106857)`，bzImage 从 12914688 降到 12881920（约 32 KB）；他还做了若干「sniff tests」，未观察到行为变化。

需要标注的局限：这是 v1（5 补丁）在 s390 上的结果，v2 增加了 1 个补丁且未重测；只有体积、没有延迟或吞吐数据，也没有 x86/arm64 对照；对 PREEMPT_DYNAMIC 的实际热点（`cond_resched()`、`preempt_schedule_notrace()`）收益没有量化。本系列属清理性质，效果以体积与维护成本为主是合理的，但社区同样没有给出静态分支数量或 code size 之外的证据。

## 我可以参与的点

1. 把 Mark 明确留为 open 的事做掉：让 `preempt_modes[]` 与 `preempt_dynamic_*` 枚举由同一处定义（例如用枚举值作下标的指定初始化器），使「删枚举忘改字符串表」这类错位不可能发生。这是一条维护者已经自认需要、且尚未有人提交的改动，性价比很高。
2. 检查自研内核是否踩在错位窗口里：只要合过 `9650ce11f2e3` 而没合 `ef9293b3b797`，`preempt_model_str()` 会给出错误模型串、`/sys/kernel/debug/sched/preempt` 输出为空——这会让「当前实际抢占模型」这个诊断信息直接失真。可以把「读 `/sys/kernel/debug/sched/preempt` 是否为空、`preempt_model_str()` 输出是否与实际配置一致」做成一条自检项进回归清单。
3. 复测 v2 的体积收益：本系列只被 v1/s390 测过，在 x86_64 与 arm64 defconfig 上对 v2 六个补丁跑 `bloat-o-meter` 是补齐数据链条的小活儿，且这类数据在讨论「是否值得向更早 stable 回合」时会被引用。
4. 回合判断：OLK-6.6 上 `d3d16750693b` 把 `PREEMPT_DYNAMIC` 依赖到 `CONFIG_ARCH_HAS_PREEMPT_LAZY`，而 6.6 没有 lazy 抢占模型，因此整链不可直接 cherry-pick；可评估的是 `88e0b3bb9930`（`{cond,might}_resched()` 简化）与 `5b9a28eeed37`（移除 `HAVE_PREEMPT_DYNAMIC_{CALLBACK,KEY}`）这一子集，并顺带确认 `preempt_modes[]` 在自研树上的定义方式是否有同样的错位风险。

## 参考链接

- 本系列与关键邮件：
  - v2 封面（0/6）：https://lore.kernel.org/all/20260803191731.3244294-1-mark.rutland@arm.com/
  - v1 封面（0/5）与 Mete Durlu 的 s390 体积数据：https://lore.kernel.org/all/10c3cc66-080b-4a70-979d-90594b06d71d@linux.ibm.com/
  - Mark Rutland 关于 JUMP_LABEL 的答复：https://lore.kernel.org/all/apbutocBHjiBTmCd@J2N7QTR9R3.cambridge.arm.com/
  - Mark Rutland 关于 6/6 注释的答复：https://lore.kernel.org/all/apb3XyPKQVTVJqQx@J2N7QTR9R3.cambridge.arm.com/
  - Mark Rutland 的「Ugh, yes」+ sched_dynamic_show() 表态：https://lore.kernel.org/all/apb3naadvUkEJxGM@J2N7QTR9R3.cambridge.arm.com/
  - 修复补丁（Reported-by: Jinjie Ruan，进 tip 为 ef9293b3b797）：https://lore.kernel.org/all/20260902101637.232129-1-mark.rutland@arm.com/
  - 本日 Jinjie Ruan 的催问：https://lore.kernel.org/all/6f4a009f-4261-4cce-88b6-1dec5ecc3a53@huawei.com/
- 相关文章：[[sched-20260902-002]]（PREEMPT_DYNAMIC 简化与 static key 迁移）、[[sched-20260903-007]]（本日同族的 deprecated static key 收尾）。

---
id: sched-20260903-013
date: '2026-09-03'
subject: 'sched: dynamic: Simplify PREEMPT_DYNAMIC'
subsystem: sched
type: discussion
status: merged_tip
severity: medium
thread_root_msgid: '<20260803191731.3244294-1-mark.rutland@arm.com>'
lore_url: https://lore.kernel.org/all/20260803191731.3244294-1-mark.rutland@arm.com/
upstream_commit: ef9293b3b797
fixes_commit: 9650ce11f2e3
merged_branch: tip:sched/core
current_version: v2
generated_at: '2026-09-07'
authors:
- Mark Rutland
maintainers_involved:
- Peter Zijlstra
- Jinjie Ruan
- Mete Durlu
patch_series:
- "sched: dynamic: Make PREEMPT_DYNAMIC depend on ARCH_HAS_PREEMPT_LAZY"
- "sched: dynamic: Simplify {cond,might}_resched()"
- "sched: dynamic: Simplify preempt_schedule{,_notrace}"
- "sched: dynamic: Simplify irqentry_exit_cond_resched"
- "sched: dynamic: Remove HAVE_PREEMPT_DYNAMIC_{CALLBACK,KEY}"
- "sched: dynamic: Simplify preempt model accessors"
- "sched: dynamic: Fix preemption model strings"
merge_assessment:
  likelihood: likely
  blocking_issues:
  - "枚举与 preempt_modes[] 字符串表的一致性仍是手工维护，Mark 认为需要 by construction 的后续重构"
  - "Jinjie Ruan 本日催问的 08-07 问题尚无回答（原文正文未保留）"
  next_action: "跟进 by-construction 一致性重构，并复测 v2 在 x86/arm64 上的体积收益"
contribution_opportunities:
- "用指定初始化器把 preempt_modes[] 与 preempt_dynamic 枚举做成编译期一致"
- "自检是否落在 9650ce11f2e3 与 ef9293b3b797 之间的错位窗口（debug/sched/preempt 空输出）"
- "在 x86_64/arm64 defconfig 上对 v2 六补丁补跑 bloat-o-meter"
- "评估 OLK-6.6 只回合 {cond,might}_resched 与 Remove HAVE_PREEMPT_DYNAMIC_* 两笔的可行性"
source_email_count: 1
related_articles:
- sched-20260902-002
tags:
- preempt
- sched/core
---
