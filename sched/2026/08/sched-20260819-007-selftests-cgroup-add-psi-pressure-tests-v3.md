
## TL;DR
Tao Cui 为 cgroup selftests 增加 `test_psi.c`，覆盖 PSI 压力触发与 `cgroup.pressure` 显隐切换，v3 按 review 拆分成 per-resource case 并提升健壮性。纯测试覆盖增强，合入概率高。

## 背景与问题
cgroup selftests 此前没有 PSI 覆盖。PSI（Pressure Stall Information）是判断系统资源压力下的重要接口，缺乏测试易回归。

## 技术方案
新增 `tools/testing/selftests/cgroup/test_psi.c`（+296 行）：
- per-resource（io/memory/cpu/irq）trigger 烟测，每 fd 一个 trigger，irq 仅 full-only；`/proc/pressure/irq` 缺失时跳过。
- `cgroup.pressure` 显隐切换测试。
- CPU 压力触发测试用超配（over-subscription）制造压力；用 `cg_run_nowait()` 起 CPU hog，2s 窗口挂触发以便非特权用户设置。
- PSI 禁用或资源缺失时整体跳过。
配套改 `.gitignore`、`Makefile`、`config`。

## 版本演进与当前进展
- v1：触发测试用 memory 制造压力，runner 在 cgroup 内。
- v2（Michal/Suren/sashiko review）：改 CPU 压力、加 PSI/IRQ 跳过守卫。
- v3（8/19）：触发测试拆成 per-resource case 定位具体失败资源；`cg_run_nowait()` 起 hog；`cg_read_strcmp()` 替代 `atoi()`；`strerror()` 报错；修 unused-parameter/sign-compare nit；用 "created" 标志守护 teardown。

## Maintainer 意见与讨论焦点
Suren、Michal、sashiko 已给 review 意见，v3 已基本消化：聚焦测试结构清晰、健壮性、非特权可跑。无明显分歧。

## 合入评估
合入可能性 high：测试增强、已迭代三轮并按 review 收敛，无功能风险。

## 效果评估
无性能数据（测试代码）。验证方式为在开启 PSI 的内核上运行 `test_psi` 全绿。

## 我可以参与的点
- 在开启 PSI 的多种内核配置上跑该 selftest 并回帖结果。

## 参考链接
- lore thread: 未获取到
- v1/v2 链接: https://lore.kernel.org/all/20260724025826.504586-1-cui.tao@linux.dev/ , https://lore.kernel.org/all/20260728083742.2359320-1-cui.tao@linux.dev/

---
id: sched-20260819-007
date: 2026-08-19
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [Tao Cui]
maintainers_involved: [Michal Koutny, Suren Baghdasaryan]
current_version: v3
patch_series:
  - version: v3
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "为 cgroup selftests 新增 test_psi.c：per-resource（io/memory/cpu/irq）PSI 触发烟测（每 fd 一个 trigger、irq 仅 full-only）、cgroup.pressure 显隐切换测试、用超配制造 CPU 压力的触发测试；PSI 禁用或资源缺失时跳过。v3 按 reviewer 意见把触发测试拆成按资源分 case、用 cg_run_nowait() 起 CPU hog、2s 窗口挂触发以便非特权用户设置，并修清理/健壮性 nit。"
    review_outcome: "Suren Baghdasaryan、Michal Koutny、sashiko 已参与 review；v3 回应了拆分触发 case、runner 移出 cgroup、用 cg_read_strcmp 替代 atoi、strerror 报告、修 unused-parameter/sign-compare 等意见。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需 cgroup/selftest 维护者最终 ack"]
  next_action: "等待 Michal/Suren 收下 v3。"
contribution_opportunities:
  - kind: testing
    description: "可在开启 PSI 的内核上跑 test_psi，验证各资源触发与 cgroup.pressure 切换行为。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 1
related_articles: []
tags: [psi, cgroup]
---
