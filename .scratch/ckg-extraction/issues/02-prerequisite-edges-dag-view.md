# 02 — 先修边 + 单课 DAG 视图

Status: done

## What to build

在概念基础上抽取**先修关系**并组装为 DAG，渲染单课视图。

- 在 `config` seed 边提示词 `ck_prompt_edges`（英文，Step2：把概念表喂回 LLM → 先修边，含先修≠包含的 ✓/✗ 示例）。
- Step2 产出先修边 `[{from, to}]`，仅使用既有概念名。
- 代码**查环断环**，保证最终图为有向无环图（DAG）—— 无环保证来自代码，不依赖 LLM。
- 把完整 DAG（节点含 `first_para`、边含方向）存入 `course_ckg.graph_json`。
- 前端单课 DAG 视图：ECharts 有向图，**x 轴按 `first_para` 横向布局**（讲述时间从左到右），先修边画箭头 —— 使「讲授走向」一眼可见（箭头多向右 = 自底向上 / 先讲前置；多向左 = 自顶向下 / 回补前置）。

先修关系语义见 CONTEXT.md「CK 维度」；DAG 决策见 ADR 0002。

## Acceptance criteria

- [ ] `config` seed `ck_prompt_edges`（英文，含先修 vs 包含的 ✓/✗ 示例），幂等
- [ ] Step2 产出先修边，仅引用 issue 01 抽出的既有概念名，不新造概念
- [ ] 代码检测并打破环，最终图保证为 DAG
- [ ] `graph_json` 持久化完整图：节点带 `first_para`，边带方向
- [ ] 单课视图用 ECharts 有向图渲染，节点按 `first_para` 横向定位，边为箭头
- [ ] 对吴恩达某视频跑通，能从图上肉眼看出先修方向倾向

## Blocked by

- 01-concept-extraction-e2e

## Comments

- **2026-06-25 16:16** — 自动开发完成。实现要点：新增 `ck_prompt_edges` config seed（幂等接入 `init_db`）+ `parse_edges_response`/`validate_edges`/`break_cycles`（贪心增量建图，加边前查 to→from 可达性，成环则丢弃，代码保证 DAG），worker 串入 Step2 抽先修边（校验+断环后存 `graph_json` 的 concepts+edges，边步失败不丢概念），GET 端点返回 edges，前端右侧新增 ECharts `graph` 单课 DAG 视图（`layout:'none'`、x 按 first_para 线性映射、先修边画箭头、hover 显示 definition）+ DAG/清单视图切换，i18n 三语补齐。新增 23 个测试全绿，全量 122 passed / 22 failed（基线 99/22，22 个失败均为预存环境问题：corpus.db 缺 video 25、陈旧 config/mock，未引入新失败）。人工验收待办：真实 Ollama 上跑通先修边并核对 DAG 走向。
