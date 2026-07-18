# 05 — 原型示意树视图

Status: done

## What to build

画像卡第三视图:用**均值参数合成**一棵"这位老师典型长这样"的原型示意树,一图概括风格。

- 接入 04 的视图切换框架,作为第三个视图。
- 合成规则(读 `_aggregate_ckg_profile` 的均值):
  - 均值 `decompose_depth` → 树高(层数,四舍五入)
  - 均值 `decompose_breadth` → 每个非叶节点挂几个子(四舍五入)
  - 均值 `relation_density` → 按比例撒几条跨支讲述关联边(示意)
  - 节点名用**占位**(如 概念A / A.1 / A.2),因为它表达的是"形状"而非"内容"
- **诚实角标**:视图固定标注「示意结构 · 由均值参数生成 · 非任何真实课程」。
- 引入走向(辅助信号)体现在左右排布上,不单列指标。

依据 ADR 0003。注意:这是**示意图**,不得让用户误以为是某节真实课程。

## Acceptance criteria

- [ ] 原型示意树接入画像卡视图切换,可与单课/小多图互切
- [ ] 树形由均值 depth/breadth 生成;按均值 relation_density 撒示意跨支边
- [ ] 节点用占位名,不冒充真实概念
- [ ] 固定显示"示意/由均值参数生成/非真实课程"角标
- [ ] 无已分析课程时友好降级(不崩溃)
- [ ] i18n 三语补齐

## Blocked by

- 04-profile-card-views

## Comments

- **2026-06-26 自动开发完成**。实现要点(TDD):
  - `renderProfileArchetype` 由占位变实现:读 `_profileMeans`(04 已存)的 均值 depth→树高、branch_factor→每节点子数、relation_density→按比例撒跨支边;BFS 生成占位概念名(根=「主题」,子=`父名.序号`),`first_para` 递增供横排;`MAX_NODES=40` 防爆;经 `_buildDecompGraphOption` 复用渲染。
  - **诚实角标**:固定显示「示意结构 · 由均值参数生成 · 非任何真实课程」(i18n `profile.archetype_badge`,三语);新增 `archetype_root`/`archetype_rel` 占位标签键。
  - 无已分析课程时 `renderProfile` 走空态、不进该视图,降级安全。
  - **测试**:新增原型合成断言(读三个均值、复用渲染器、三语角标含"非真实课程"字样);更新 profile i18n 键(`archetype_todo`→`archetype_badge`)。profile/archetype 18 项全绿;内联 JS `node --check` 通过;全量 **253 passed / 22 failed**(22 预存环境失败,无新增回归)。
