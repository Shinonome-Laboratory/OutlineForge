# 01 — 抽概念端到端跑通（含三栏骨架）

Status: done

## What to build

CKG 抽取管线的第一刀，端到端最薄一刀：从单个视频的台本（复用既有段落转录）抽取**去重的概念节点**，并把知识图谱页改造为三栏布局以承载触发与展示。

- 建立 `course_ckg` 存储（每视频一行）。
- 在 `config` 表 seed 概念抽取提示词 `ck_prompt_concepts`（英文，Step1：全文一次喂 → 概念）。
- 新增触发 API：后台线程跑 Step1（全文一次喂 LLM），SSE 推进度（复用既有日志基建）。
- 前端：知识图谱页改为三栏 —— 视频列表 | 参数设置+开始分析面板 | 视图区。中间面板放「开始分析」按钮；抽完在右侧展示去重概念清单，每个概念含 `name` / `definition` / 引入位置 `first_para`（首次实质讲到的段落序号）。

术语见 CONTEXT.md「CK 维度」（概念节点、引入位置）；方法依据 ADR 0002。粒度方针：大纲级（~15–30/课），靠提示词 INCLUDE/EXCLUDE + ✓「梯度下降」/✗「偏导数」校准。

## Acceptance criteria

- [x] `course_ckg` 表幂等创建（至少 `video_id` 主键、`graph_json`、`model`、`created_at`）
- [x] `config` seed `ck_prompt_concepts`（英文 Step1 提示词），幂等
- [x] 触发 API 启后台线程跑 Step1：全文一次喂 LLM，解析出概念数组，每个含 `name`、`definition`、`first_para`
- [x] 概念去重（同一概念不重复出现）
- [x] SSE 实时推送进度；解析失败推 `error` 事件附原始输出前 500 字，不落盘、不崩溃
- [x] 知识图谱页落地三栏布局；中间面板含「开始分析」按钮；右侧展示概念清单（name + definition + first_para）
- [ ] 对吴恩达某视频实际跑通，产出合理的大纲级概念（数量在 ~15–30 量级）—— 人工验收（需真实 Ollama + 数据，测试用 mock 覆盖逻辑）

## Blocked by

None - can start immediately

## Comments

- **2026-06-25 16:08** — 自动开发完成。实现要点：新增 `course_ckg` 表 + `ck_prompt_concepts` config seed（均幂等接入 `init_db`），新增 `parse_concepts_response`（健壮 JSON 解析 + 按 name 归一化去重）、后台 worker `_run_ckg_extraction`（全文一次喂 LLM、SSE 推进度、解析失败推 error 不落盘不崩溃）、`POST/GET /api/outline/ckg/{video_id}` 两个端点；前端 `#page-ckg` 改三栏（视频列表 | 抽取面板含「开始分析」按钮 | 概念清单视图），i18n 三语补齐。新增 19 个测试全绿，未触动现有用例（22 个预存失败均为本机 corpus.db 缺 video 25 等种子数据所致，与本 issue 无关）。人工验收待办：在真实 Ollama + 吴恩达视频上跑通概念抽取。
