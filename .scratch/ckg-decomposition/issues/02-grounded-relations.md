# 02 — 讲述关联跨支边

Status: done

## What to build

在拆解树骨架之上,抽取教师课中**实际明说的跨支讲述关联**,作为第二类边叠加渲染。

- Step2 提示词(新增 `ck_prompt_relations`,英文):输入 Step1 的概念表 + 全文,
  输出教师**在课中实际建立**的跨分支有向关系 —— 每条边含 `from`、`to`、`type`(关系类型)、
  可选 `evidence`(接地的原文片段/段落序号)。
- **类型不预设**:LLM **自由标注** `type` 字符串,原样存储;提示词只给 builds-on /
  explains-via / motivates 作**示例锚点**,明确不限制输出。(涌现类型的聚类归一化属
  下游研究分析,不在本片范围。)
- `graph_json` 增加第二类边集合(讲述关联),与拆解边分开存(`edge_kind` 区分)。
- 单课视图:讲述关联边叠加到拆解树上渲染,带箭头 + 类型标签(与拆解边视觉可区分)。
- `format=json` + 容错兜底;校验边端点必须是已存在概念,丢弃悬空边。

术语见 CONTEXT.md「讲述关联」;依据 ADR 0003。共现边**不做**(暂缓)。

## Acceptance criteria

- [ ] Step2 提示词产出跨支讲述关联边,每条含 `from`/`to`/`type`(+可选 evidence)
- [ ] `type` 为 LLM 自由标注字符串,原样存储,不被映射/限制到固定枚举
- [ ] `graph_json` 分开存拆解边与讲述关联边(可区分)
- [ ] 校验:边端点为已存在概念,悬空边丢弃
- [ ] 单课视图叠加渲染讲述关联边(带箭头 + 类型标签,与拆解边视觉区分)
- [ ] 解析失败容错(不落盘、不崩溃、SSE error)
- [ ] 对吴恩达某视频跑通,图上出现合理的跨支关联边 —— 人工验收

## Blocked by

- 01-decomposition-tree-extract

## Comments

- **2026-06-26 自动开发完成**。实现要点(TDD):
  - **提示词**:新增 `_CK_PROMPT_RELATIONS`(英文,key `ck_prompt_relations`),输入概念表 + 全文,抽"跨支讲述关联";`type` 由 LLM **自由标注**(builds-on/explains-via/motivates 仅作示例,明确 "NOT limited"),输出 `from/to/type/evidence`。seed 进 `CK_CONFIG_DEFAULTS`、加入 `_CK_PROMPT_KEYS`(可编辑)。
  - **解析/校验**:新增 `parse_relations_response`(健壮解析 + 容错 salvage,`type`/`evidence` 缺省 `""`,原样保留自由 type)与 `validate_relations`(端点归一化到规范概念名、丢弃悬空/自环、保留 type/evidence;**不**断环——叙事关联可成环)。
  - **worker**:拆解树后新增 Step6b 第二次 LLM 调用抽关联 → `validate_relations` → 写入 `graph_json.relations`;解析/调用失败降级为 `relations=[]`(不丢概念与骨架);成功消息含"X 条讲述关联"。
  - **前端**:`loadCKGConcepts` 读 `data.relations`;`renderCKGGraph(concepts, edges, relations)` 把关联画为**第二类边**(琥珀色虚线、曲度更大、带 `type` 标签、tooltip 显 evidence),与拆解边视觉区分;edge 计数行加"X 条讲述关联";新增关联提示词编辑框 + load/save 接线;i18n 三语补 `relations_count`/`prompt_relations_label`。
  - **测试**:新增 `ck_prompt_relations` seed/幂等、`parse_relations_*`(含自由 type 保留、缺省、容错、空表有效)、`validate_relations`(丢未知/自环、保留 type)、worker 持久化关联、坏关联降级仍存骨架、前端渲染关联 + i18n 等;并把 issue 01 的"单次调用"测试改为"两次调用(拆解+关联)"。CKG/关联相关 98 项全绿;全量 **246 passed / 22 failed**(22 均为预存环境失败,无新增回归)。
  - 人工验收待办:真实 Ollama + 吴恩达视频跑通,核对关联是否接地、type 标签是否合理。
