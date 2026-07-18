# 01 — 项目骨架 + 配置初始化

Status: done

## What to build

搭建功能 B `outline` 的最小可运行骨架：FastAPI 服务监听 `:8001`，在 `00-data/corpus.db` 中建 `course_topics` 表，初始化 5 个 `ob_` 配置项，serve 空白占位页。

## Acceptance criteria

- [x] `main_outline.py` 启动 FastAPI，访问 `http://localhost:8001` 返回 200
- [x] `course_topics` 表在 `00-data/corpus.db` 中创建成功（字段见 PRD §3.1），可重复执行不报错
- [x] 5 个 `ob_` 默认配置写入 `config` 表：`ob_llm_model`=`qwen2.5:14b-instruct`、`ob_llm_temperature`=`0.0`、`ob_max_topics`=`auto`、`ob_prompt_round1`（英文默认 prompt）、`ob_prompt_round2`（英文默认 prompt）
- [x] `GET /` 返回空白 `outline.html` 占位页

## Blocked by

None — 可立即开始

## Comments

### Completion summary (2026-06-14)

TDD Red-Green-Refactor cycle completed:

**Files created:**
- `main_outline.py` — FastAPI app on port 8001 with lifespan-init, `init_db()`, and `GET /` serving `outline.html`
- `outline.html` — Minimal HTML5 placeholder with Tailwind CDN
- `test/__init__.py` — Package marker
- `test/test_outline.py` — 7 tests covering all acceptance criteria

**Test results:** 7 passed, 0 failed
- `test_app_starts` — GET / returns 200
- `test_root_returns_html_content_type` — text/html Content-Type
- `test_root_body_contains_html_doctype` — valid HTML doctype
- `test_course_topics_table_exists` — table exists in shared corpus.db
- `test_course_topics_columns_correct` — 8 columns match PRD §3.1
- `test_ob_config_keys_exist` — 5 ob_ keys with correct values
- `test_init_db_idempotent` — double init_db does not error, count stays at 5

**Database changes (in shared `00-data/corpus.db`):**
- Added `course_topics` table (IF NOT EXISTS)
- Inserted 5 `ob_` config rows (INSERT OR IGNORE, idempotent)
