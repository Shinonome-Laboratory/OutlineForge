# 05 — 提示词前端编辑（可选）

Status: done

## What to build

在中间面板提供两条 CKG 提示词的编辑能力，支撑提示词迭代与抽取质量的人工调优（grill 决定 c）。

- 中间面板可查看并编辑 `ck_prompt_concepts` / `ck_prompt_edges`。
- 保存写回 `config` 表；下次抽取使用更新后的提示词。
- 模型选择沿用现有 `ob_` config 模式（如已有下拉则复用）。

抽取质量（概念粒度、先修边对错）由人工借此迭代验收 —— 本功能不单列 HITL 实现刀。

## Acceptance criteria

- [ ] 中间面板可查看并编辑两条提示词
- [ ] 保存写回 `config` 表
- [ ] 重新抽取使用更新后的提示词
- [ ] 模型选择沿用现有 config 模式

## Blocked by

- 01-concept-extraction-e2e

## Comments

- **2026-06-25 16:35** — 自动开发完成。实现要点：新增专用 `GET/PUT /api/outline/ckg/prompts` 读写两条 CK 提示词（不污染 ob_ config 端点），中间面板加可折叠提示词编辑器 + 模型下拉（复用 ob_llm_model，worker 抽取时直接读取），i18n 三语补齐，TDD 新增 8 个测试全绿。
