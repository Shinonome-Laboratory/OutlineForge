# 01 — 拆解树抽取 + 单课渲染

Status: done

## What to build

CKG 重构第一刀:把抽取链的第一步从"抽概念清单"改为"**按「标题→概念」拆解成树**",
并把 `graph_json` 换成能承载拆解结构的新版,单课视图渲染这棵拆解树。

- Step1 提示词(`config.ck_prompt_concepts` 改写或新增 `ck_prompt_decompose`,英文):
  输入全文,输出以**课程标题为根**的概念拆解树 —— 每个概念含 `name`、`definition`、
  `first_para`(首次实质讲到的段落序号)、`parent`(上位概念名,根的 parent 为课程标题/空)。
- `graph_json` 新结构:`concepts[]` + **拆解边**(由 parent 关系导出,父→子)。加
  `schema_version`(或 `edge_kind` 标记)以区分新旧图;旧的先修结构视为 legacy,
  重新分析即覆盖(数据为吴恩达视频,可重跑)。
- 退役 `ck_prompt_edges`(先修判定提示词)与先修边语义(本片只产拆解边,讲述关联见 02)。
- 单课视图:渲染拆解树,节点按 `first_para` 左右排布(复用/调整现有 ECharts graph 渲染器)。
- 全程 `format=json` + 解析失败容错兜底(不落盘、不崩溃、SSE 推 error)。

术语见 CONTEXT.md「拆解关系 / 概念节点 / 引入位置」;依据 ADR 0002、0003。
粒度方针:概念数**跟随实际内容、不设目标数**。

## Acceptance criteria

- [ ] Step1 提示词产出"标题→概念"拆解树,每个概念含 `name`/`definition`/`first_para`/`parent`
- [ ] `graph_json` 新结构落地:concepts + 拆解边 + `schema_version` 标记
- [ ] 概念去重(同名概念不重复)
- [ ] 旧先修结构/`ck_prompt_edges` 退役;旧 graph_json 行可被重新分析覆盖,不导致崩溃
- [ ] 单课视图渲染拆解树,节点按 `first_para` 排布
- [ ] 解析失败推 SSE error(附原始输出前 500 字),不落盘、不崩溃
- [ ] 对吴恩达某视频实际跑通,产出合理拆解树 —— 人工验收(测试用 mock 覆盖逻辑)

## Blocked by

None - can start immediately

## Comments

- **2026-06-26 自动开发完成**。实现要点(TDD):
  - **提示词**:`_CK_PROMPT_CONCEPTS` 改写为"标题→概念拆解树",每个概念输出 `name`/`definition`/`first_para`/`parent`,并输出 `title` 作为树根;保留 `TEACHING CONCEPT`/`first_para` 字样。
  - **解析**:`parse_concepts_response` 新增捕获 `parent`(缺省 `""`)与 `title` 透传;去重逻辑不变。
  - **新函数** `derive_decomposition_edges(concepts)`:由 `parent` 指针导出 父→子 拆解边,parent 解析到另一概念才连边(指向 title/未知=森林根),丢弃自环与重复,经 `break_cycles` 保证无环。
  - **worker**:删除先修(Step2)调用,改为单次 LLM 调用 → 拆解 → 派生拆解边;`graph_json` 换新结构 `{schema_version:2, title, concepts, decomposition_edges, relations:[]}`;拓扑参数暂在拆解边上计算(issue 03 重做);成功消息改"拆解边"。
  - **退役** `ck_prompt_edges`:移出 `CK_CONFIG_DEFAULTS` 与 `_CK_PROMPT_KEYS`,prompts 编辑器 GET/PUT 仅留 `ck_prompt_concepts`(PUT 含该键返回 422);`_CK_PROMPT_EDGES`/`parse_edges_response`/`validate_edges`/`break_cycles` 保留供教案生成(issue 06)。新增迁移:旧 `ck_prompt_concepts`(无 `"parent"`)自动升级。
  - **GET 端点**:返回 `schema_version`/`title`/`concepts`/`decomposition_edges`/`relations` + `edges` 向后兼容别名(=拆解边);旧行回退到 `edges` 键。`_counts` 改读 decomposition_edges+relations(回退 legacy edges)。
  - **前端**:`loadCKGConcepts` 读 `decomposition_edges`(回退 `edges`);单课视图复用 ECharts 渲染器画拆解树(按 first_para 横排);移除已退役的"先修关系"提示词编辑框 + load/save 引用;i18n 三语 先修→拆解(dag_title/dag_empty/edges_count/prompt_concepts_label/scatter_skipped)。
  - **测试**:新增 parent/title 解析、`derive_decomposition_edges`、schema_version-2 持久化、单次调用+自定义拆解提示词、prompts 退役键拒绝 等用例;改写两个旧的两步 worker 测试与 GET 测试;删除 `ck_prompt_edges` seed 测试。CKG 相关 94 项全绿;全量 233 passed / 22 failed(22 均为本机缺种子数据的预存环境失败,无 CKG 相关、无新增回归)。
  - 人工验收待办:在真实 Ollama + 吴恩达视频上跑通拆解抽取,核对拆解树质量。
