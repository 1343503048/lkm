---
id: sched-20260910-020
date: 2026-09-10
subject: 'sched_ext: Merge adjacent ifdefs in ext.h'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: <20260909172740.36375-1-yphbchou0911@gmail.com>
lore_url: https://lore.kernel.org/all/178897635522.2.2211845744379646092@kernel.org/
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
current_version: v1
generated_at: '2026-09-11T02:05:00'
authors:
- yphbchou0911@gmail.com
maintainers_involved:
- Tejun Heo
patch_series:
- version: v1
  msgid: <20260909172740.36375-1-yphbchou0911@gmail.com>
  date: '2026-09-09'
  summary: '合并 kernel/sched/ext/ext.h 中同条件（CONFIG_SCHED_CLASS_EXT）的相邻 ifdef 块，即 7.2-rc6
    中第 59 行 #endif 与第 61 行 #ifdef 之间的那一对；该邮件未投递到本邮箱，正文与 changelog 未获取到。'
  review_outcome: '09-10 01:52 Tejun Heo: Applied to sched_ext/for-7.4，无附加意见，线程内无其他往返。'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 等 sched_ext/for-7.4 合入主线；注意 ext.h 行位置变化会让其他新增 scx_* 接口的在飞补丁需要 rebase
contribution_opportunities:
- kind: review
  description: 合入后用 CONFIG_SCHED_CLASS_EXT=n 构建一次，确认 stub 搬家未漏符号——这是机械重排类补丁唯一可能出错处，线程内无人验证
- kind: extend
  description: 用同样方法扫描 kernel/sched/sched.h、features.h 等调度器内部头文件是否存在同条件相邻 ifdef；若有可定向投
    topic 分支，但需先确认核心维护者对纯格式清理的接受度
source_email_count: 1
related_articles:
- sched-20260910-019
- sched-20260910-018
tags:
- sched_ext
title: 'sched_ext: Merge adjacent ifdefs in ext.h'
layout: article
---

## TL;DR
Tejun Heo 于 09-10 01:52 回复 "Applied to sched_ext/for-7.4."，收取了 `yphbchou0911@gmail.com` 直接投给 topic 分支的 v1 清理补丁。原始补丁未投递到本邮箱，正文与作者姓名均未获取到；本文的技术部分来自我对 Linux 7.2-rc6 中该头文件的逐行核对——`kernel/sched/ext/ext.h` 里确实存在**唯一一处**同条件相邻 ifdef 块（第 59 行 `#endif` 与第 61 行 `#ifdef CONFIG_SCHED_CLASS_EXT`），补丁标题描述的对象真实存在且范围恰好覆盖该文件里的全部实例。纯预处理结构整理，零功能影响。

## 背景与问题
`ext.h` 是 sched_ext 对调度器核心暴露接口的内部头文件，用 `CONFIG_SCHED_CLASS_EXT` 的 `#ifdef`/`#else` 成对提供「开启时的真实声明」与「关闭时的空实现 stub」。当同一个条件的块被拆成相邻的两段时，会出现两类实际成本：

1. 同一个配置状态下的声明分散在两处，读代码时容易只看到其中一段——尤其是 `#else` 分支里的 stub，两段各有一份，新增接口时很容易只补其中一处，导致 `CONFIG_SCHED_CLASS_EXT=n` 的构建在很久之后才暴露缺符号。
2. 预处理分支数量翻倍，后续补丁的 diff 上下文更难对齐。

Linux 7.2-rc6 的 `kernel/sched/ext/ext.h` 中该结构如下（行号为该版本实际行号，已确认本地树与 7.2-rc6 逐字节一致）：

```c
  9: #ifdef CONFIG_SCHED_CLASS_EXT
        ... 真实声明与 inline ...
 38: #ifdef CONFIG_SCHED_CORE
 41: #endif
 43: #else	/* CONFIG_SCHED_CLASS_EXT */
        ... 一整段 static inline 空 stub（task_on_scx()、scx_allow_ttwu_queue()、init_sched_ext_class() 等）...
 59: #endif	/* CONFIG_SCHED_CLASS_EXT */
 60:
 61: #ifdef CONFIG_SCHED_CLASS_EXT
 62: void __scx_update_idle(struct rq *rq, bool idle, bool do_notify);
 63:
 64: static inline void scx_update_idle(struct rq *rq, bool idle, bool do_notify)
 65: {
 66: 	if (scx_enabled())
 67: 		__scx_update_idle(rq, idle, do_notify);
 68: }
 69: #else
 70: static inline void scx_update_idle(struct rq *rq, bool idle, bool do_notify) {}
 71: #endif
```

第 59 行的 `#endif` 与第 61 行的 `#ifdef` 之间只隔一个空行，条件完全相同——这就是标题里 "adjacent ifdefs" 指的对象。

## 技术方案
补丁正文未获取到（原始邮件不在邮箱缓存内），以下是按标题与上述文件结构可确定的改动形态，**属我基于 7.2-rc6 代码的推演，不是邮件内容**：

- 把第二段（61-71）的开启分支内容——`__scx_update_idle()` 声明与带 `scx_enabled()` 判断的 `scx_update_idle()` inline——移入第一段（9-42）的开启分支；
- 把第二段的 `#else` stub（`scx_update_idle()` 空实现）移入第一段的 `#else` 分支（43-58），与其他 stub 并列；
- 删除 59/61 这一对冗余的 `#endif` + `#ifdef`。

结果是：一个条件、一对分支、一处集中管理。预处理结果与编译产物**完全不变**（两段之间没有任何代码，合并纯粹是文本重排），因此不需要任何测试数据支撑。

我另外扫描了 sched_ext 的全部内部头文件（`kernel/sched/ext/*.h`、`include/linux/sched/ext.h`），查找「`#endif` 后 2 行内出现同条件 `#if*`」的模式，**只命中 ext.h 的 59/61 这一处**。也就是说该补丁的范围恰好覆盖了这一类问题的全部现存实例，合并后不留尾巴——这一点是判断它「已彻底完成」而非「只改了一半」的依据。

## 版本演进与当前进展
- v1：`<20260909172740.36375-1-yphbchou0911@gmail.com>`（09-09 17:27 发出）。标题前缀为 `[PATCH sched_ext/for-7.4]`——作者按 Tejun 对 sched_ext 补丁的惯例把目标 topic 分支直接写进前缀，说明是定向投递而非泛发 LKML。该邮件**未投递到本邮箱**，正文未获取到。
- **09-10 01:52:35（本日）**：Tejun Heo 回复 "Hello, Applied to sched_ext/for-7.4."（`<178897635522.2.2211845744379646092@kernel.org>`），称呼处未写名字。从发出到收取约 8.5 小时，中间无任何往返。
- 同一批：同作者的 `selftests/sched_ext: Drop -rdynamic and stop clobbering LDFLAGS`（见 sched-20260910-019）在同一秒级批次内被收取（两封通知的 msgid 分别为 `178897635521.2.18013318571965009488@kernel.org` 与 `178897635522.2.2211845744379646092@kernel.org`，仅序号递增，属同一次批量 apply）；Tianyi Chen 的 `Validate select_cpu_and mask constraints` 也在 5 分钟后被收取（见 sched-20260910-018）。
- 已进 `sched_ext/for-7.4`；缓存内无 tip-bot 回帖，主线尚未合入。无 v2。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：唯一发言者，只有收取通知一句，未提任何修改要求。这类零风险的预处理整理正是维护者会直接收的类型。
- 无 NAK、无争议、无未决问题。
- 一个可记录的观察（非邮件内容）：本枚与 sched-20260910-019 出自同一新作者、同一晚被同一批次收取，且都带 `sched_ext/for-7.4` 前缀——说明 Tejun 正在为该 topic 分支集中收集构建/代码卫生类小补丁。对想参与 sched_ext 的人，这是一条低门槛的入口路径：定向投 `for-7.4` 前缀的小型清理，收取速度以小时计。

## 合入评估
likelihood: merged。

已进 `sched_ext/for-7.4` topic 分支，剩下的只是随该分支进入主线的时间问题。改动限于 `kernel/sched/ext/ext.h` 的预处理结构，编译产物不变，风险为零。

blocking_issues：无。

next_action：等 `sched_ext/for-7.4` 合入主线。需要注意的唯一现实风险是**与其他在飞 sched_ext 补丁的上下文冲突**——`ext.h` 是接口声明的集中地，任何新增 scx_* 接口的补丁都会碰到这两段；本补丁合并后会改变它们的行位置，后进的补丁需要 rebase。

## 效果评估
暂无效果数据，且这类补丁不需要数据：合并相邻同条件 ifdef 不改变预处理输出，编译产物逐字节相同。

可核实的部分是我对该文件结构的核对结论（代码审阅，非测试）：Linux 7.2-rc6 的 `kernel/sched/ext/ext.h` 存在且仅存在一处同条件相邻块（59/61），sched_ext 其余头文件无同类问题。补丁正文未获取到，因此无法确认它是否还顺带调整了 `#endif` 后的注释（7.2-rc6 中第一段的 `#endif` 带 `/* CONFIG_SCHED_CLASS_EXT */` 注释，第二段的不带）。

## 我可以参与的点
当前阶段暂无明显参与空间：补丁已被收取、范围经我核对已覆盖全部同类实例、且无任何可测行为。

若要顺着这条线找活，有两个低成本方向：
- **检查合并后 stub 的完整性（review）**：等 `sched_ext/for-7.4` 合入后，用 `CONFIG_SCHED_CLASS_EXT=n` 构建一次（`allmodconfig` 关掉该选项或直接用 `make defconfig`），确认没有因为 stub 搬家而漏掉符号——这是这类「机械重排」补丁唯一可能出错的地方，且没人在线程里验证过。
- **同类清理的下一处（extend）**：本次扫描只覆盖 sched_ext 自己的头文件。`kernel/sched/sched.h`、`kernel/sched/features.h` 等调度器内部头文件是否存在同条件相邻 ifdef，可用同样方法扫一遍；若有，按同一惯例定向投 `sched_ext/for-7.4` 或 tip。但要注意调度器核心维护者对纯格式清理的接受度低于 sched_ext，投之前先看线程风向。

## 参考链接
- Tejun Heo 的收取通知（本日邮件）: https://lore.kernel.org/all/178897635522.2.2211845744379646092@kernel.org/
- 被收取的 v1 补丁（线程根，未投递到本邮箱、正文未获取到）: https://lore.kernel.org/all/20260909172740.36375-1-yphbchou0911@gmail.com/
- 同作者同批被收取的另一枚: https://lore.kernel.org/all/20260909151741.24742-1-yphbchou0911@gmail.com/
- upstream commit / tip-bot: 未获取到（已进 topic 分支，缓存内无 tip-bot 回帖）
- stable backport: 不适用（纯预处理结构整理）
