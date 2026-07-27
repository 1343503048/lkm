# 文章固定模板

每个 patch 系列生成一篇文章时，严格套用下面这个结构。frontmatter 用 YAML，供程序/agent 解析索引；
正文给人读，围绕"这个系列在解决什么问题、方案是什么、现在进展到哪一步、社区怎么看、值不值得我跟进/参与"来写，
不要大段照抄邮件原文。

```markdown
---
id: sched-YYYYMMDD-NNN            # NNN为当日三位序号，如001
date: YYYY-MM-DD
subsystem: sched
type: bug | feature | fix | discussion        # 单选，四选一
status: rfc | under_review | merged_tip | merged_stable | superseded | stalled
severity: critical | high | medium | low | none   # type=bug/fix时必填，其余填none
thread_root_msgid: "<xxxxx@xxxxx>"             # 若邮件工具未暴露该字段，可填 unknown
lore_url: "https://lore.kernel.org/lkml/xxxxx" # 若无法获取，填 unknown，不要编造链接
authors: [name1, name2]
maintainers_involved: [name1, name2]           # 参与review/acked/nak的关键维护者
current_version: v3                            # 当前观察到的最新版本号
patch_series:
  - version: v1
    msgid: "<xxx>"
    date: YYYY-MM-DD
    summary: "该版本方案要点/较上版关键改动"
    review_outcome: "主要review意见摘要，一两句话"
  - version: v2
    msgid: "<yyy>"
    date: YYYY-MM-DD
    summary: "该版本方案要点/较上版关键改动"
    review_outcome: "主要review意见摘要，一两句话"
upstream_commit: "abcdef1234567" | null
fixes_commit: null                              # bug/fix类：被修复的引入commit，未知填null
merged_branch: "tip/sched/urgent" | null
merge_assessment:
  likelihood: merged | high | medium | low | rejected | unknown
  blocking_issues: []                           # 目前卡住合入的具体问题，没有就留空数组
  next_action: "需要作者/社区做什么才能推进，比如'等待v4补充benchmark数据'"
contribution_opportunities:                     # 我能参与的点，没有就填 []，不要硬凑
  - kind: testing | review | extend | new_patch | discussion
    description: "具体能做什么，比如'在xx场景下跑基准测试并回帖数据'"
generated_at: "2026-07-27T10:00:00"             # 文章生成时间戳（ISO 8601），区别于邮件日期
source_email_count: 5                           # 该系列分析了多少封邮件，用于评估信息完整度
related_articles: []                            # 关联的前几天关于同一系列的文章 ID 列表
                                                # 如 ["sched-20260725-001", "sched-20260726-003"]
                                                # 跨天系列衔接用，没有就填 []
tags: []                                        # 必须从 tag_vocabulary.md 选取，可多选
---

## TL;DR
一到两句话：这个系列要解决什么问题，现在进展到哪一步，值不值得我关注/参与。

## 背景与问题
说清楚"为什么会有这个系列"——遇到了什么实际问题/场景痛点，还是纯粹的代码质量改进。
bug/fix类：复现条件、症状、影响范围。
feature类：动机、要解决的具体问题、现有实现的不足在哪。

## 技术方案
方案本身在做什么，关键设计取舍是什么（比如为什么选这种算法/数据结构而不是另一种）。
如果邮件里提到了备选方案被放弃，也记一下，这对判断合入可能性有用。

## 版本演进与当前进展
当前处于第几版（对应 frontmatter 的 current_version），按版本列出每版做了什么改动、
是回应了谁的哪条意见。如果只有v1还没人回复，写"v1刚发出，暂无review意见"。

## Maintainer 意见与讨论焦点
维护者/资深社区成员的具体意见，哪些是认可的方向、哪些是争议点/未解决的分歧、
是否有人明确表示反对（NAK）或需要补充材料才愿意继续看。这一节是判断"合入可能性"的主要依据，
如实反映分歧，不要为了让文章显得"进展顺利"而淡化争议。

## 合入评估
结合 merge_assessment 字段展开：这个系列合入主线的可能性如何、当前卡在哪、
还需要满足什么条件（比如补充benchmark、拆分patch、等其他子系统的人确认）。
如果已经合入tip或某个stable分支，这里直接说明合入情况即可。

## 效果评估
邮件里提到的效果数据（性能提升/回退幅度、复现测试结果等），如果作者/reviewer给出了具体数字就引用数字本身，
没有数据支撑的说法（比如"应该会更快"）要标注为"作者主观判断，未见测试数据"，不要当成既定结论转述。
如果完全没有讨论效果，写"暂无效果数据"。

## 我可以参与的点
结合 contribution_opportunities 展开，具体到"做什么、怎么参与"，比如：
- 帮忙在特定硬件/场景下测试并把结果回帖到邮件列表
- 该方案有明显可以扩展的方向，可以基于此发后续patch
- 讨论中有个问题目前没人回应，可以帮忙分析或提供数据
如果这个系列本身已经很成熟、没有明显参与空间，如实写"当前阶段暂无明显参与空间，可持续观察后续版本"，不要硬找参与点。

## 参考链接
- lore thread: ...
- tip-bot commit: ...
- stable backport: ...
（任何拿不到的链接，写"未获取到"，不要编造URL）
```

## 生成时的注意事项

- 所有"未知/拿不到"的字段，如实标注为 `unknown` / `null` / "未获取到"，绝不编造 commit hash、链接或人名。
- **"合入评估"和"我可以参与的点"是这份模板里最容易被写空的两节，也是用户最关心的**：宁可如实写"暂无明显参与空间/证据不足以判断合入可能性"，也不要为了填满结构而编造过度乐观或过度具体的建议。
- "Maintainer 意见与讨论焦点"要覆盖分歧和未解决问题，不能只挑正面评价写，判断合入可能性依赖的正是这些争议点。
- 正文各节都要写，即使内容很短也不要跳过，用一句话说明"暂无相关内容"。
- id 里的序号 NNN 在同一天内递增，同一天生成多篇文章时注意不要重复。
