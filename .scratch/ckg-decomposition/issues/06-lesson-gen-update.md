# 06 — 教案生成跟改

Status: done

## What to build

教案生成的"要教什么"抽取从"概念 + 先修边"改为"概念拆解 + 讲述关联",风格指令对齐新参数。

- 第②步(得到风格中性的知识结构):material/topic 两种模式下,把"抽先修边"替换为
  **抽拆解结构 + 讲述关联**(复用 01/02 的提示链思路);退役先修边。
- 第③步(风格参数 → 指令):指令改用新核心参数口径 —— 目标 **拆解深度 / 拆解宽度 /
  关联密度**;`bottomup` 走向作辅助 sequencing 提示(保留映射:偏低→先分后总等)。
- 第④步(风格化生成):喂给 LLM 的"目标形状"用新参数;输出仍为层级大纲 + 概念图,
  概念图按新结构(拆解 + 讲述关联)呈现。
- 实时流水线步骤文案同步(原"判定先修关系"→"抽拆解+讲述关联")。
- `format=json` + 容错降级保持。

依据 ADR 0003;与 01/02 抽取口径保持一致。

## Acceptance criteria

- [ ] lesson-gen 第②步产出拆解结构 + 讲述关联(不再产先修边)
- [ ] 风格指令(第③步)改用 拆解深度/宽度/关联密度;bottomup 作辅助 sequencing
- [ ] 第④步生成消费新参数;输出概念图按新结构呈现
- [ ] 流水线 stepper 文案同步到新口径
- [ ] material 与 topic 两模式都跑通;容错降级不报错
- [ ] 既有 lesson-gen 测试更新、不回归

## Blocked by

- 02-grounded-relations

## Comments

- **2026-06-26 自动开发完成**。实现要点(TDD):
  - **提示词**:`_LESSON_GEN_TOPIC_PROMPT` 改为输出"拆解(concepts 带 parent)+ 讲述关联(relations 带自由 type)",退役先修枚举;`_LESSON_GEN_OUTLINE_PROMPT` 的 PREREQUISITES 段换为 DECOMPOSITION(parent→child)+ GROUNDED RELATIONS 两段,新增 `{relation_lines}` 占位。
  - **worker `_run_lesson_gen`**:material 第②步从"判先修边"改为 `_CK_PROMPT_RELATIONS` 抽讲述关联;两种模式都 `derive_decomposition_edges`(从 parent)+ `validate_relations`;退役 `break_cycles/validate_edges`;sequencing/`_build_profile_descriptor` 的走向文案去"先修"措辞改"拆解/上位-下位";result 返回 `decomposition_edges`+`relations`+`edges` 别名;步骤进度文案同步。调用次数不变(material 3、topic 2)。
  - **前端**:`renderLessonGenGraph(concepts, edges, sequence, relations)` 把关联画为第二类边(琥珀虚线+type 标签),调用处传 `res.result.decomposition_edges`/`relations`;stepper 文案 `lessongen.step.edges` 与 `lessongen.dag_title` 三语改"拆解"口径。
  - **测试**:`_LG_CONCEPTS` 加 parent、`_LG_EDGES`→`_LG_RELATIONS`;改写 material/topic 两个 e2e 断言为 decomposition_edges+relations(+edges 别名);新增 topic/outline 提示词内容断言(含 decomposition/relations、无 PREREQUISITE)与前端关联渲染断言。lesson-gen 27 项全绿;全量 **252 passed / 22 failed**(22 均预存环境失败,无新增回归)。
  - 人工验收待办:真实环境跑 material/topic 两模式,核对生成大纲是否按拆解+关联组织。
