# cpufreq: CPPC: Enable boost by default when supported

## TL;DR
Pengjie Zhang（华为）的 v2 补丁让 CPPC 驱动在「Highest Performance 超过 Nominal Performance」（即平台支持 boost）时**默认启用 boost**，省去用户空间逐 policy 手动开启的步骤——此前驱动默认禁用 boost，governor 无法用到平台宣传的完整性能区间；仍可用 boost knob 退回 nominal 以内。今日 Christian Loehle（Arm）继续评论：声明「并非拦补丁」，但抛出更深一层的问题——「highest − nominal 当作 boost」这个解释本身**是否还值得保留**？若干脆删掉，BIOS 的 nominal==highest 设置就没意义了，用户空间可自行 query nominal 并限制（甚至可加进 cpupower）；并质疑「为什么逐个 CPU scan boost 能力，而不是直接 `boost_enabled = true`」。方向未定，等作者回应。

## 背景与问题
CPPC 驱动在 Highest > Nominal 时仍默认不启用 boost，用户空间必须在 governor 用满平台性能前显式开启 boost。补丁要改默认值：至少有一个 possible CPU 报告支持就默认开 boost；想留在 sustained nominal 以内的用户仍可经 boost knob 关闭（无需逐 policy 设 `scaling_max_freq`）。作者 v2 相对 v1 删了「even」并澄清 commit message（回应 Christian）。

## 技术方案
在注册驱动前检查性能能力（`drivers/cpufreq/cppc_cpufreq.c`，+20 行）：至少一个 possible CPU 报告支持（Highest > Nominal）时，默认使能 boost，让 cpufreq core 对每个支持该能力的 policy 开启 boost。今日的讨论焦点在方案形态：Christian 提出①干脆移除「highest − nominal 即 boost」的解释，让用户空间 query nominal 自己限制；②即便保留，也没必要逐个 CPU scan，直接 `boost_enabled = true`（无 boost 平台也会露出 toggle，但大体与其它驱动一致）。

## 版本演进与当前进展
*current_version: v2*（2026-10-22，`<20261022075901.3436021-1-zhangpengjie2@huawei.com>`）。v1 为 2026-10-15。今日无新补丁，是 Christian 的继续评论（设计取舍 + 实现形态质疑）与作者未来返工的起点。

## Maintainer 意见与讨论焦点
- **Christian Loehle（Arm，reviewer，非 maintainer）**：明确不拦（「not blocking this per se」），但连发四问：①「highest − nominal 当 boost」的解释是否还值得保留？②若删掉，BIOS nominal==highest 设置即废弃，用户空间可 query nominal 并限制（可加进 cpupower 设所有 policy max=nominal）；③CPCv4 在即，删掉可省去追踪 `ospm_nominal_perf` 被写时的 boost 状态；④「nominal < highest 且运行时显式 toggle boost」的组合实际多常出现？⑤为何 scan 而不是直接设 `boost_enabled = true`。
- **cpufreq 维护者（Rafael / Viresh）**：本线程未见表态。
- 未解决焦点：补丁的「默认开 boost」目标无人反对，但「boost 语义该不该绑定 highest − nominal」被上升到设计层，作者需在这点上做选择。

## 合入评估
*likelihood=medium*。补丁目标（省去手动开启 boost）合理、Christian 不阻挡，但他提出的语义问题不做澄清会影响最终形态（是保留 scan 还是直接 `boost_enabled=true`、是否动「highest − nominal 即 boost」的解释）。*blocking_issues*：boost 语义与实现形态（scan vs 直接置位）待作者回应；最终需 Rafael/Viresh 之一拍板。*next_action*：作者回应 Christian 的四问并给出 v3（或改为直接设 boost_enabled）。

## 效果评估
无性能数据——这是默认配置/enablement 的行为改动，收益是「用户不用手动开启即可用满平台性能」，属功能便捷性而非性能提升，未见 bench。

## 我可以参与的点
- **discussion**：就「highest − nominal 是否该继续解释为 boost」结合 CPCv4/ospm_nominal_perf 的走向给出建议，帮作者与 Christian 收敛语义。
- **review**：核对「直接 boost_enabled=true vs 逐个 CPU scan」两种实现对「平台是否支持 boost」的判定差异与边界（如只有部分 CPU 支持时的行为）。

## 参考链接
- lore thread（v2 补丁）: https://lore.kernel.org/all/20261022075901.3436021-1-zhangpengjie2@huawei.com/
- Christian Loehle 今日的评论: https://lore.kernel.org/all/d9fa8052-f562-4867-9e9f-1fd2a66fa794@arm.com/
- v1: https://lore.kernel.org/all/20261015015812.867988-1-zhangpengjie2@huawei.com/

---
id: sched-20261029-017
date: 2026-10-29
subject: "cpufreq: CPPC: Enable boost by default when supported"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261022075901.3436021-1-zhangpengjie2@huawei.com>"
lore_url: "https://lore.kernel.org/all/20261022075901.3436021-1-zhangpengjie2@huawei.com/"
authors: [Pengjie Zhang]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: 2026-10-15
    summary: "CPPC 驱动在 Highest > Nominal 时默认启用 boost"
    review_outcome: null
  - version: v2
    msgid: "<20261022075901.3436021-1-zhangpengjie2@huawei.com>"
    date: 2026-10-22
    summary: "删 even、澄清 commit message；注册前检查性能能力，至少一个 possible CPU 支持即默认开 boost"
    review_outcome: "Christian 继续质疑 boost 语义（highest − nominal）与实现形态（scan vs 直接置位）"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "boost 语义（highest − nominal 是否继续作 boost）与实现形态待作者回应"
    - "最终需 Rafael / Viresh 之一拍板"
  next_action: "作者回应 Christian 的四问并给出 v3（或改直接设 boost_enabled）"
contribution_opportunities:
  - kind: discussion
    description: "就 highest − nominal 是否继续解释为 boost 结合 CPCv4 走向给出建议"
  - kind: review
    description: "核对直接 boost_enabled=true vs 逐个 scan 两种实现的边界差异"
generated_at: "2026-10-30T09:30:00"
source_email_count: 1
related_articles: []
tags: [cpufreq]
---