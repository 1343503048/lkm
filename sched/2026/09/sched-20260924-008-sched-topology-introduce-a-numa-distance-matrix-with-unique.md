# sched/topology: Introduce a NUMA distance matrix with unique distance values

## TL;DR
- sched-20260901-004：Jianyong Wu（海光）的 23 补丁 RFC v2（NUMA/LLC 两级亲和性打分负载均衡）进入 Peter Zijlstra 逐片精读。已定型：per-node `numa_counts[]` 记账改为按需累加；未定：距离矩阵去重算法上界与 commit message 质量。
- sched-20260923-006：继续 02/23 讨论——Tim Chen 提出用 `llc_next` 数组替代「人造 LLC 距离矩阵」（更省存储），Jianyong 澄清系列目标是系统级 LLC 亲和排序、去重只作用于节点层。路线未收敛。
- sched-20260924-008（今天，增量更新）：Tim Chen 进一步收敛论点——「排序 + 打分」两个目的可由 raw distance 共同满足（排序用 `(distance, node_id)` 平局决胜，打分用 raw distance），去重矩阵只是把二者耦合、反而给等距节点对制造了虚假的 Di 收益（patch 12 里 `Di = dist(src,i) - dist(dst,i)` 读的是距离**幅度**而非顺序）。Jianyong 回应：去重是为了**强制对称性**（`(distance,node_id)` 缺对称），并给出「把任务聚合到最小区域」的意图说明；承认唯一 open 点是「对称性是否必需」——若不需要，可按 Tim 方案大幅简化。分歧收敛到「对称 vs 简化」这一取舍上。

## 背景与问题
- sched-20260901-004：上游 cache-aware 负载均衡只在 LLC 粒度决策，跨 NUMA 节点放置交给独立的 NUMA balancing，二者互不知情。该系列给拓扑加一张去重后的 NUMA 距离矩阵，让每个节点的距离值互不相同，供 load balance 按「任务数 × 距离差」算 affinity 得分。海光这类非全对称互连平台节点间距离非单值，需要区分度。
- sched-20260923-006：背景无新增。
- sched-20260924-008（今天）：背景无新增，讨论聚焦在 02/23 的去重矩阵本身是否必要。

## 技术方案
- sched-20260901-004：两级矩阵（NUMA 节点距离矩阵 + 节点内 LLC 距离小矩阵）；贪心边着色去重保证每行无重复（Peter 指上界不够紧）；rq/sd 上维护 `llc_counts[]`/`numa_counts[]`；per-sd scratch 数组。热路径记账 vs 慢路径按需累加，Peter 主张后者、作者接受。
- sched-20260923-006：Tim Chen 提 `llc_next` 数组（节点内 cache 排序）；Jianyong 澄清去重只作用于节点矩阵、`llc_next` 描述不了「访问哪个等距节点」。
- sched-20260924-008（今天）：
  - Tim Chen 进一步主张：patch 12 的 score `Di = dist(src,i) - dist(dst,i)`（仅当 Di>0 保留）读的是距离**幅度**，去重矩阵制造的 refined 值正好在等距节点对上注入虚假收益——他举了两个反例（Scenario A：N0/N1 对 N2 物理等距、raw Di=0，refined 却制造 40 的「好处」；Scenario B：两个物理等价源被 refined 排名成 8 vs 4，还因 clamp 下限 4 抬高了伪造值）。结论：排序只需确定性全序（raw distance + node_id 决胜），打分需要真实幅度（raw distance），二者都可以用未修改的 distance 完成，无需人造矩阵。
  - Tim Chen（另一帖）也回应对称性：可用 `(distance, abs(node_id_i - node_id_j))` 解决排序对称；node distance 不改就是对称的；「以真实距离为 affinity 度量 + 单独、可控地施加 node 属性偏置」比「调一个 hacked 距离来改变偏置」更好控制（偏置幅度难控且逐节点不一致）。
  - Jianyong Wu 回应：`(distance, node_id)` 类似 memory zonelist fallback 序列，但缺对称（`node_affinity_distance(A,B) != node_affinity_distance(B,A)`），去重算法正能强制这一对称；意图是「区分等距节点、给出确定性的任务移动方向」——例如 N2 是 Preferred 且饱和时，希望任务聚合到 N1 而非 N0，这需要给 N0 的任务权重；refined distance 同时服务「affinity-score 计算」与「迁移控制」两个目标，二者需一致矩阵。唯一 open 点是「对称是否严格需要」——若不需要，他可按 Tim 的 `(node_distance, node_id)` 方案实现，显著简化；他承认「这是系列最棘手的一处」。

## 版本演进与当前进展
- v2（08-27，23 枚）以来持续逐片评审。本日为 02/23 去重矩阵「必要性与对称性」路线分歧的深入，无新版。

## Maintainer 意见与讨论焦点
- **Tim Chen（Intel）**：核心反对「人造去重距离」——它只在等距对（本无局部性差异）上制造偏置，且把「排序」与「打分」两个本可独立的工作耦合进一张矩阵。主张 raw distance + 平局决胜（node_id 或 load），偏置单独、可控地施加。
- **Jianyong Wu（作者）**：坚持 dedup 的价值是**强制对称性**与**确定性移动方向**；承认「对称是否必需」是当前唯一 open 点，若不需要可显著简化。
- 无 Peter Zijlstra 本日新表态。分歧从「数据结构」收敛为「对称性 vs 简化」的一个具体取舍。

## 合入评估
*likelihood=unknown*。23 枚架构性 RFC 仍处早期评审，02/23 的去重矩阵必要性尚未与 Tim 的方案对齐（现聚焦「对称是否必需」）；此前 Peter 的 `__build_all_zonelists()` 联动、着色上界等 open 项依旧未决。*blocking_issues*：去重矩阵 vs raw distance+平局决胜 未定；系列整体仍缺跨平台收益数据与 v3。*next_action*：作者就「对称是否必需」给出结论，据此决定 02/23 用去重矩阵还是简化方案，再出 v3。

## 效果评估
本日无性能数据。Tim 给出的是静态反例论证（refined 矩阵在等距对上制造虚假 Di），Jianyong 给出意图层面的论证（聚合目标 + 对称性）；均属设计论证，无实测。

## 我可以参与的点
- kind=discussion：「对称性是否必需」是当前唯一卡点——可从负载均衡对「移动方向确定性」的实际需求出发，判断 `(distance, node_id)`+单独偏置能否替代去重矩阵，帮双方收敛。
- kind=testing：若手上有 Hygon 多节点机型，给出开启/关闭该系列的 NUMA 亲和收益对比——整个系列最缺的仍是跨平台收益背书。

## 参考链接
- lore (02/23 补丁): https://lore.kernel.org/all/20260827122816.756234-3-wujianyong@hygon.cn/
- Tim 去重反例: https://lore.kernel.org/all/ce95ec57af9dfaf4d9ed604ad7337441a543f538.camel@linux.intel.com/
- Tim 对称性建议: https://lore.kernel.org/all/112e526b4013e23c70adf5b8883db8e75358b473.camel@linux.intel.com/
- Jianyong 回应: https://lore.kernel.org/all/f6ebab3d0e44412dad17ac64a3b93339@hygon.cn/

---
id: sched-20260924-008
date: '2026-09-24'
subject: 'sched/topology: Introduce a NUMA distance matrix with unique distance values'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20260827122816.756234-1-wujianyong@hygon.cn>'
lore_url: 'https://lore.kernel.org/all/20260827122816.756234-3-wujianyong@hygon.cn/'
authors:
  - 'Jianyong Wu'
maintainers_involved:
  - 'Tim Chen'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260827122816.756234-1-wujianyong@hygon.cn>'
    date: '2026-08-27'
    summary: '23 枚：NUMA 距离矩阵 + LLC 距离小矩阵 + affinity 打分'
    review_outcome: '02/23 去重矩阵必要性与对称性仍在与 Tim Chen 对齐'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '去重矩阵 vs raw distance + 平局决胜 未定（焦点：对称是否必需）'
    - '系列整体仍缺跨平台收益数据与 v3'
  next_action: '作者就对称必要性给出结论并出 v3'
contribution_opportunities:
  - kind: discussion
    description: '从负载均衡角度判断 (distance,node_id)+单独偏置能否替代去重矩阵'
  - kind: testing
    description: 'Hygon 多节点机型上给出该系列 NUMA 亲和收益对比数据'
generated_at: '2026-09-25T09:00:00'
source_email_count: 4
related_articles:
  - sched-20260923-006
tags:
  - topology
  - numa_balancing
  - load_balance
---