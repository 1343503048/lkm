---
id: sched-20260802-005
date: 2026-08-02
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [Julian Braha]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-14581@qq-imap>"
    date: 2026-08-02
    summary: "删除 NO_HZ_FULL 中对 choice 成员 VIRT_CPU_ACCOUNTING_GEN 的失效 select，改为在 choice 上加 `default VIRT_CPU_ACCOUNTING_GEN if NO_HZ_FULL` 表达同一依赖关系。由静态分析工具 kconfirm 发现。"
    review_outcome: "Bradley Morgan 给出 Reviewed-by；无维护者回帖。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "尚无 timer/nohz 维护者（Frederic Weisbecker、Thomas Gleixner）回帖；唯一 Reviewed-by 来自非维护者。"
    - "改动跨 init/Kconfig 与 kernel/time/Kconfig 两个文件，归属哪棵树（tip/timers 还是 kbuild）未明确，容易在无人认领的情况下沉寂。"
    - "补丁未附任何配置矩阵验证证据，无法确认在 NO_HZ_FULL=y 但 HAVE_VIRT_CPU_ACCOUNTING_GEN=n 等边界组合下语义完全等价。"
  next_action: "需要作者补充 allmodconfig/allnoconfig 及 NO_HZ_FULL 相关组合下 .config 前后对比，并明确 Cc 到 Frederic Weisbecker；否则大概率停滞。"
contribution_opportunities:
  - kind: testing
    description: "构造若干配置组合（NO_HZ_FULL=y/n × HAVE_VIRT_CPU_ACCOUNTING_GEN=y/n × 各 arch defconfig），对比打补丁前后生成的 .config 中 VIRT_CPU_ACCOUNTING_GEN 取值是否完全一致，回帖数据——这是当前补丁最缺的证据。"
    
  - kind: review
    description: "核对 choice 中多个 default 的优先级语义：新加的 `default VIRT_CPU_ACCOUNTING_GEN if NO_HZ_FULL` 置于 `default TICK_CPU_ACCOUNTING` 之前，Kconfig 取首个条件成立的 default，可确认该顺序是否确保了预期行为。"
generated_at: "2026-08-03T00:15:00"
source_email_count: 2
related_articles: []
tags: [nohz, sched_clock]
---

# nohz: 用 choice default 替换失效的 select

## TL;DR

Kconfig 中 `select` 对 `choice` 内的选项无效，`NO_HZ_FULL` 里的 `select VIRT_CPU_ACCOUNTING_GEN` 是一行死代码。补丁删除它并改用 choice 的条件 default 表达同一关系。由静态分析工具 kconfirm 发现，已获一个非维护者的 Reviewed-by，但缺少配置验证数据且无维护者关注，存在沉寂风险。

## 背景与问题

Kconfig 有一条容易被忽略的规则：**`select` 不能作用于 `choice` 内部的配置项**。

`kernel/time/Kconfig` 中 `NO_HZ_FULL` 写了：

```
config NO_HZ_FULL
	depends on HAVE_VIRT_CPU_ACCOUNTING_GEN
	select NO_HZ_COMMON
	select RCU_NOCB_CPU
	select VIRT_CPU_ACCOUNTING_GEN      <-- 这行是死的
	select IRQ_WORK
	select CPU_ISOLATION
```

而 `VIRT_CPU_ACCOUNTING_GEN` 位于 `init/Kconfig` 的 "Cputime accounting" choice 之中，因此这个 `select` 从来没有生效过。

那为什么现有行为看起来是对的？作者给出了解释：`VIRT_CPU_ACCOUNTING_GEN` 之所以在 `NO_HZ_FULL=y` 时被选中，**是因为该 choice 的其他成员都 `depends on NO_HZ_FULL=n`** —— 也就是说，当 `NO_HZ_FULL=y` 时其余选项全被排除，只剩它一个候选，于是"歪打正着"。

这是一种脆弱的隐式依赖：正确行为依赖于其他选项的排除条件，而不是显式声明。一旦有人给 choice 添加新成员而忘记加 `depends on NO_HZ_FULL=n`，行为就会静默出错。

发现途径值得一提：**kconfirm，一个 Kconfig 静态分析工具**。这类工具化发现的问题往往数量多、单个价值低，但正是容易在人工 review 中长期漏掉的类型。

严重度 low：当前行为正确，问题是可维护性与表达正确性，不影响运行。

## 技术方案

两处改动，一删一加：

**`kernel/time/Kconfig`** —— 删掉死 select：

```diff
 	select NO_HZ_COMMON
 	select RCU_NOCB_CPU
-	select VIRT_CPU_ACCOUNTING_GEN
 	select IRQ_WORK
```

**`init/Kconfig`** —— 在 choice 上加条件 default：

```diff
 choice
 	prompt "Cputime accounting"
+	default VIRT_CPU_ACCOUNTING_GEN if NO_HZ_FULL
 	default TICK_CPU_ACCOUNTING
```

设计取舍很清晰：**把隐式依赖显式化**。原来"NO_HZ_FULL 需要 GEN 记账"这个意图靠其他选项的排除条件间接实现，现在直接写成 choice 的条件默认值。Kconfig 中 choice 可以有多个 `default`，按书写顺序取第一个条件成立的 —— 新加的条件 default 置于无条件 default 之前，因此 `NO_HZ_FULL=y` 时选 GEN，否则回落到 `TICK_CPU_ACCOUNTING`。

净改动 1 增 1 删，跨两个文件。邮件中**未提及任何被放弃的备选方案** —— 例如另一种思路是保留隐式关系但加注释说明，或者把 `VIRT_CPU_ACCOUNTING_GEN` 移出 choice。作者直接给出了单一方案。

## 版本演进与当前进展

v1，2026-08-02 00:01（北京时间）发出。同日 05:26 收到回帖：

**Bradley Morgan** (`include@grrlz.net`)：

> Thanks for the patch Julian.
>
> Please add:
>
> Reviewed-by: Bradley Morgan <include@grrlz.net>

除此之外无其他讨论。截至当日结束，无维护者参与。

## Maintainer 意见与讨论焦点

**没有维护者回帖** —— 这是本系列当前最主要的状态特征，需要如实指出。

唯一的 `Reviewed-by` 来自 Bradley Morgan，从邮件域名（`grrlz.net`）与回帖内容看，是社区参与者而非 `kernel/time/` 或 `init/Kconfig` 的维护者。这个 tag 有价值，但**不足以推动合入** —— nohz 相关改动通常需要 Frederic Weisbecker（NO_HZ_FULL 维护者）或 Thomas Gleixner 点头。

**未被讨论的实质问题**（均为空白，非分歧）：

1. **无配置验证证据**。补丁声称新旧写法语义等价，但没有提供任何 `.config` 生成结果的前后对比。对 Kconfig 改动而言，这是最直接、也最应该提供的证据类型。边界情况尤其值得验证：`HAVE_VIRT_CPU_ACCOUNTING_GEN=n` 时（此时 `NO_HZ_FULL` 因 depends 无法开启）、以及各架构 defconfig 下的表现。
2. **归属树不明**。改动同时触及 `init/Kconfig`（通常走 kbuild 或 Andrew Morton 树）与 `kernel/time/Kconfig`（走 tip/timers）。跨树小改动常见的失败模式就是双方都认为该由对方接手，最终无人 pick。邮件中未见作者对此有安排。
3. **choice 多 default 优先级未经复核**。新写法依赖"Kconfig 取首个条件成立的 default"这一行为。这是正确的，但没有 reviewer 独立确认过 —— 而这正是整个补丁正确性的支点。

## 合入评估

合入可能性 **medium**，低于本日其他系列。理由：

**有利因素**：

- 问题客观存在，死 select 是事实，不存在"要不要改"的争议；
- 改动极小（1 增 1 删），风险接近于零；
- 已有一个 Reviewed-by；
- 静态分析工具发现的问题，通常内核社区对这类清理持欢迎态度。

**不利因素**（决定了评级不是 high）：

- **无人认领**是核心风险。Kconfig 清理类补丁没有紧迫性，容易在维护者的收件箱中排到最后；
- 缺少验证数据，维护者若要 pick 需自己验证，增加了 pick 的成本；
- 跨两个文件、两棵树，归属模糊。

这类补丁的典型结局是两极的：要么某个维护者顺手 pick 掉，要么石沉大海需要作者数周后 ping 重发。**当前更接近后者的轨迹** —— 发出近一天只有一个社区 Reviewed-by。

`next_action` 很明确：补验证数据 + 明确 Cc 到 Frederic Weisbecker。

## 效果评估

**暂无效果数据**，且本补丁也不产生可测量效果。

这是一次纯 Kconfig 表达层面的清理：

- **运行时行为**：作者主张改动前后完全一致 —— 但这是**作者的主观判断，未见任何 .config 对比数据支撑**，需明确标注。
- **性能影响**：零。不涉及任何运行时代码路径。
- **收益**：可维护性。消除一行误导性的死代码，把隐式依赖变为显式声明，降低未来向该 choice 添加成员时引入静默错误的概率。

值得注意的是，"语义等价"这个断言恰恰是唯一需要验证的东西，而它目前没有证据。这与 001（作者给出 4 条 splat → 0 条的明确对比）形成鲜明差别。

## 我可以参与的点

这个系列的参与门槛在当日所有系列中**最低**，且补的正好是它最缺的东西：

- **配置矩阵验证**（最直接有用）：构造组合 —— `NO_HZ_FULL=y/n` × `HAVE_VIRT_CPU_ACCOUNTING_GEN=y/n` × 几个主流 arch defconfig，用 `make olddefconfig` 分别在打补丁前后生成 `.config`，diff 出 `VIRT_CPU_ACCOUNTING_*` 相关取值。如果完全一致，回帖这份数据 —— 这会把补丁从"看起来对"变成"验证过对"，是能实质推动合入的贡献。不需要任何特殊硬件，一台机器几分钟即可完成。
- **复核 choice default 优先级**：确认 Kconfig 在多个 `default` 中取首个条件成立者的行为，验证新加的条件 default 置于无条件 default 之前是必要且充分的。回帖 Reviewed-by 时附上这条分析。
- **帮助推进归属**：如果验证通过，可以在回帖中建议明确走哪棵树并 Cc 相应维护者。对停滞风险高的小补丁，这类"流程助推"往往比技术意见更有效。

对想开始参与内核社区的人来说，这是一个理想的切入点：问题清晰、验证成本低、当前确实缺人、且贡献是可见的。

## 参考链接

- lore thread: 未获取到（IMAP 邮件头未暴露原始 Message-ID）
- 静态分析工具: kconfirm（补丁中提及，未附链接）
- tip-bot commit: 未获取到
- stable backport: 不适用
