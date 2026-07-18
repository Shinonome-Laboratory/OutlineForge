# 04 — 画像卡视图改造(单课 + 小多图 + 参数条)

Status: done

## What to build

风格画像卡从"归一化雷达"改造为以**拆解树**为主体的多视图。本片做两个视图 + 参数条
(原型示意树见 05)。

- **视图切换框架**:画像卡顶部切换 单课 / 小多图(/ 原型树占位,05 接入)。
- **① 单课视图**:选中某视频 → 展示**那节课的真实 CKG**(拆解树 + 讲述关联,按 first_para 排)。
  **复用** 知识图谱页现有的单课渲染器,不重写。
- **② 小多图视图(small-multiples)**:全库已分析课的**拆解树缩略图一排** —— 风格 =
  这排图共有的节奏。缩略图轻量(可只画拆解骨架,弱化交互)。
- **参数条**:三视图下方常驻 `拆解深度 / 拆解宽度 / 关联密度`(+汇聚数)的**均值 ± 跨课 sd**
  (复用/调整 `_aggregate_ckg_profile`),作为"视觉规律确为跨课稳定"的量化证据。
- **弃用雷达**:移除单教师阶段的归一化雷达(代码可保留为"≥2 教师对比"时的延后视图,
  但默认不出现);如实说明"区分风格需第二位教师"。

术语/依据见 ADR 0003(画像卡三视图)。

## Acceptance criteria

- [ ] 画像卡顶部视图切换(单课 / 小多图;原型树位留给 05)
- [ ] 单课视图复用现有单课 CKG 渲染器,展示选中视频的拆解树 + 讲述关联
- [ ] 小多图视图渲染全库已分析课的拆解树缩略图
- [ ] 参数条展示核心参数均值 ± sd(无已分析课程时友好提示"先去分析视频")
- [ ] 归一化雷达不再作为默认视图出现
- [ ] i18n 三语补齐;既有测试不回归

## Blocked by

- 03-style-params

## Comments

- **2026-06-26 自动开发完成**。实现要点(TDD):
  - **复用渲染器**:把单课 CKG 的图构建逻辑抽成 `_buildDecompGraphOption(concepts, edges, relations, opts)`(first_para 横排、拆解骨架 + 讲述关联两类边;`opts.compact` 出缩略图模式);`renderCKGGraph` 改为薄封装调用它,画像卡各视图共用 —— 满足"复用现有单课渲染器"。
  - **画像卡三视图**:顶部切换 小多图 / 单课 / 原型树。① **小多图** `renderProfileMulti`:拉 `/api/outline/ckg` 全库,逐课 `_fetchCKG` 渲染 compact 拆解树缩略图入网格(风格＝这排图共有节奏);② **单课** `renderProfileSingle`:下拉选课 → 全尺寸复用渲染器;③ **原型树** `renderProfileArchetype`:占位 + "待接入"角标(issue 05 填充)。
  - **参数条**常驻:核心 拆解深度/拆解宽度/关联密度/汇聚数 + 概念数 + 引入走向 的 均值±sd + mini 进度条(读 `/api/outline/ckg/profile`)。
  - **弃用雷达**:删除 `profile-radar` 容器与 `_profileRadarChart`/radar 渲染;保留风格判定 + 生成规则块。i18n 三语补 `profile.view.*`/`multi_hint`/`pick_lecture`/`archetype_todo`。
  - **测试**:改写 radar 相关前端测试为视图容器/复用渲染器/resize 断言(并断言 `profile-radar` 已移除);profile i18n 测试加新视图键。profile/ckg/前端相关 106 项全绿;抽取的内联 JS 经 `node --check` 通过;全量 **252 passed / 22 failed**(22 预存环境失败,无新增回归)。
  - 备注:原型树视图为占位,留给 issue 05;雷达代码已删,多教师对比阶段如需可另行恢复。
