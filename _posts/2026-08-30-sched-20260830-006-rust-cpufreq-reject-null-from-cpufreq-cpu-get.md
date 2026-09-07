---
id: sched-20260830-006
date: '2026-08-30'
subject: 'rust: cpufreq: reject NULL from cpufreq_cpu_get()'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260829161013.102967-1-mehmet.mkoseoglu@gmail.com>
lore_url: https://lore.kernel.org/all/20260829161013.102967-1-mehmet.mkoseoglu@gmail.com/
authors:
- Mehmet Koseoglu
- Onur Özkan
maintainers_involved: []
current_version: v3
patch_series:
- version: v1
  msgid: <20260828154235.17315-1-mehmet.mkoseoglu@gmail.com>
  date: 2026-08-28
  summary: 功能版本：用 NonNull 拒 cpufreq_cpu_get() 的 NULL 返回并回 ENODEV，避免 from_err_ptr()
    放过 NULL 导致 kobject_put() oops；含 KUnit 负控复现与 Validated on a VM as well 一句
  review_outcome: 尚无意见可查（本日报数据源仅捕获到 v2 之后的回复）
- version: v2
  msgid: <20260828161834.29539-1-mehmet.mkoseoglu@gmail.com>
  date: 2026-08-29
  summary: 仅把改动的 import 调整为内核竖排风格，功能代码不变；删掉了 VM 验证那句
  review_outcome: 'Onur Özkan：应加 Cc: stable，其余 LGTM'
- version: v3
  msgid: <20260829161013.102967-1-mehmet.mkoseoglu@gmail.com>
  date: 2026-08-30
  summary: '在 v2 基础上加 Cc: stable@vger.kernel.org，代码与 v1/v2 完全一致'
  review_outcome: '拿到 Reviewed-by: Onur Özkan；cpufreq 与 rust-for-linux 两侧维护者当日均未表态'
upstream_commit: null
fixes_commit: 6ebdd7c93177
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - cpufreq 侧与 rust-for-linux 侧维护者均未表态，归属不清可能拖延收取
  - KUnit 复现器未公开，第三方无法独立复核
  - Fixes 指向的 stable 回合边界（NULL 路径何时引入）无人评估
  next_action: 由任一相关维护者给出 Acked-by 后经 cpufreq -fixes 或 rust-for-linux 收取，并把负控测试一并提交
contribution_opportunities:
- kind: new_patch
  description: 把未公开的 KUnit 负控测试作为 selftest 补丁随修复一起发出，使缺陷可被第三方复核
- kind: review
  description: 扫描 rust/kernel 中其它把可能为 NULL 的 C 返回值喂给 from_err_ptr() 的调用点，列出同型缺陷清单
generated_at: '2026-09-07T22:06:23'
source_email_count: 2
related_articles: []
tags:
- cpufreq
- crash
title: 'rust: cpufreq: reject NULL from cpufreq_cpu_get()'
layout: article
---

## TL;DR

Mehmet Koseoglu 的 Rust cpufreq 绑定修复走到 **v3**：`PolicyCpu::from_cpu()` 把 `cpufreq_cpu_get()` 的返回值交给 `from_err_ptr()`，而后者只拒 `ERR_PTR`、**接受 NULL**，于是查表失败时会用 NULL 构造出一个可变引用，`PolicyCpu` 析构时再把非法指针传给 `cpufreq_cpu_put()` → `kobject_put()` 处 oops。改法是用 `NonNull::new(...).ok_or(ENODEV)?` 显式拒 NULL。v2 上 Onur Özkan 要求 `Cc: stable`，v3 加上并拿到他的 `Reviewed-by`。三天三个版本、证据齐（KUnit 负控复现），属"改了就能收"的状态；但**复现器至今未公开**。

## 背景与问题

- **缺陷位置**：`rust/kernel/cpufreq.rs` 里 `PolicyCpu::from_cpu()`——Rust cpufreq vtable 抽象获取 per-CPU policy 的入口。
- **成因链条**（作者描述）：`cpufreq_cpu_get()` 的契约是"返回一个带引用的 policy，或者 NULL"；原实现 `from_err_ptr(unsafe { bindings::cpufreq_cpu_get(...) })?` 只对 `ERR_PTR` 报错，NULL 被当作有效指针继续走 `Policy::from_raw_mut(ptr)`，即从 NULL 构造 `&mut Policy`；随后 `PolicyCpu` 被 drop 时把该非法指针交给 `cpufreq_cpu_put()`，在 `kobject_put()` 里 oops。
- **触发条件**：policy 查表失败（例如 CPU 尚未/已不再拥有 policy、驱动未注册），属于 Rust 绑生的错误路径而非稳态路径。
- **已有验证**：作者称用 KUnit 负控（negative-control）跑出了原转换下的 oops，同一测试在改动后通过；v1 里还多写了一句 "Validated on a VM as well."（v2/v3 的 commit message 里这句被删掉）。复现器"available on request"，**至今未公开**。

## 技术方案

`rust/kernel/cpufreq.rs`，+14/−4：

```rust
     fn from_cpu(cpu: CpuId) -> Result<Self> {
         // SAFETY: It is safe to call `cpufreq_cpu_get` for any valid CPU.
-        let ptr = from_err_ptr(unsafe { bindings::cpufreq_cpu_get(u32::from(cpu)) })?;
+        let ptr =
+            NonNull::new(unsafe { bindings::cpufreq_cpu_get(u32::from(cpu)) }).ok_or(ENODEV)?;
 
         Ok(Self(
-            unsafe { Policy::from_raw_mut(ptr) },
+            unsafe { Policy::from_raw_mut(ptr.as_ptr()) },
         ))
     }
```

- **为什么选 `NonNull` 而不是在 `from_err_ptr` 里补判空**：这是 Rust 侧表达"这个指针不得为 NULL"的最 idiomatic 方式——`NonNull<T>` 在构造点就把不变式建立起来，`unsafe { Policy::from_raw_mut(...) }` 的前置条件（"guaranteed to be valid"）才真正成立；改 `from_err_ptr()` 会影响所有调用点，语义也超出该 helper "转 ERR_PTR" 的职责。
- **错误码选 `ENODEV`**：与"该 CPU 上没有 policy"这一实际情形一致。
- 其余改动是把 `use` 列表改成内核的竖排 import 风格（v2 的唯一变化）。
- `Fixes: 6ebdd7c93177`（"rust: cpufreq: Extend abstractions for policy and driver ops"），`Cc: stable@vger.kernel.org`，`Assisted-by: LLM`。

## 版本演进与当前进展

- 8/28 v1（`<20260828154235.17315-1-mehmet.mkoseoglu@gmail.com>`）：功能改动即已定型，message 里还写了 "Validated on a VM as well."。
- 8/29 v2（`<20260828161834.29539-1-mehmet.mkoseoglu@gmail.com>`）：按 review 把 import 改成内核竖排风格，功能代码不变；同日 03:11 Onur Özkan 回复"This should be tagged for stable: `Cc: stable@vger.kernel.org`；LGTM otherwise."
- 8/30 v3：加上 `Cc: stable`；同日 03:52 Onur Özkan 给出 `Reviewed-by: Onur Özkan <work@onurozkan.dev>`。
- 三个版本**功能代码完全一致**，变化只在元数据与格式；截至本日没有 cpufreq/Rust 侧维护者（Viresh Kumar 或 rust-for-linux）表态，未进 tip 或 stable（未获取到）。

## Maintainer 意见与讨论焦点

- **Onur Özkan（社区贡献者，非维护者）**：全程唯一 reviewer，两轮意见都是流程性的（stable 标签、import 风格），**没有对根因分析或方案本身提异议**。
- **无争议，但也无维护者背书**：本条真正的未决问题是"谁来收"——它同时落在 cpufreq 与 rust-for-linux 两个交叉口，`rust/kernel/cpufreq.rs` 的改动通常需要两边都点过头；本日内两边都没出现。
- 另一处未被讨论的点：`Fixes:` 指向 `6ebdd7c93177`（"Extend abstractions for policy and driver ops"）。若 NULL 返回路径是更早引入的（`cpufreq_cpu_get()` 的契约本身一直如此），stable 该回合到哪个分支、是否只回到该抽象被引入的版本，需要维护者判断——目前无人提出。

## 合入评估

**likely**。理由：缺陷链条清晰可核（`from_err_ptr()` 接受 NULL 是事实）、改动 14 行且idiomatic、带 `Fixes:`、带 `Cc: stable`、并已有一枚 `Reviewed-by`，没有任何待处理的 review 意见。风险仅在维护归属（cpufreq 侧与 Rust 侧谁走这笔），这决定它进的是 cpufreq 的 -fixes 还是 rust-for-linux 的树，而不是它会不会被收。

## 效果评估

有测试但无量化数据，且证据不可独立复核：

- 作者给出的验证方式是"KUnit 负控运行在原转换下复现了 oops，同一测试在本改动后通过"，另有 v1 提到"也在 VM 上验证过"（v2/v3 删掉了这句）。这足以说明缺陷真实存在。
- **复现器与测试代码未公开**（"available on request"），因此第三方无法复核；也未给出该错误路径在真实负载下的可达性/频率。属于"个案复现级别"，不是系统性验证。

## 我可以参与的点

- **推动公开复现器/测试**：本线程目前唯一实质缺口就是这个——把 KUnit 负控测试作为补丁的一部分发出来（selftest + 修复成对提交）在社区里通常会被明确欢迎，也能让"是否可被 syzbot/负控覆盖"这个问题有答案。
- **帮它找对归属**：如果关心这条，可以直接在帖里 `Acked-by`/`Tested-by` 或提醒 cpufreq 与 rust-for-linux 两边的 maintainer，避免这类小修复因归属不清而停滞。
- **同类审计**：Rust 抽象里凡是把 C 侧"可能返回 NULL"的接口喂给 `from_err_ptr()` 的地方都有同一形状的问题。可以在 `rust/kernel/` 下扫一遍 `from_err_ptr(` 的调用点，把可疑处列出来——这类清单对 rust-for-linux 侧很有价值，目前没人做过。
- **回合判断**：与调度器无直接关系，只在依赖 Rust cpufreq 绑定的分支上才需要跟进；OLK-6.6 若不带 Rust cpufreq 抽象可忽略。

## 参考链接

- lore（v3 + Reviewed-by）: https://lore.kernel.org/all/20260829161013.102967-1-mehmet.mkoseoglu@gmail.com/
- lore（Onur Özkan 的 Reviewed-by）: https://lore.kernel.org/all/20260829195250.24625-1-work@onurozkan.dev/
- lore（v2）: https://lore.kernel.org/all/20260828161834.29539-1-mehmet.mkoseoglu@gmail.com/
- lore（Onur Özkan 要求 Cc stable）: https://lore.kernel.org/all/20260828191213.45530-1-work@onurozkan.dev/
- 本补丁 `Fixes:` 目标: `6ebdd7c93177` ("rust: cpufreq: Extend abstractions for policy and driver ops")
- tip-bot commit: 未获取到
- stable backport: 未获取到（v3 已 `Cc: stable@vger.kernel.org`）
