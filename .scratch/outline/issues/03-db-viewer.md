# 03 — DB Viewer 适配

Status: done

## What to build

基于已有的 `db-viewer-02outline.html`，适配为功能 B 的数据库查看器。展示 `00-data/corpus.db` 中四张表（`videos`、`corpus_paragraphs`、`course_topics`、`config`），侧栏底部展示 `ob_` 前缀的默认配置项。支持本地文件加载和服务器模式两种方式。

## Acceptance criteria

- [x] 打开 db-viewer，左侧显示四张表名及行数
- [x] 点击 `course_topics` 能看到表结构和数据
- [x] 侧栏底部展示 `ob_` 前缀配置项及当前值
- [x] 支持本地文件模式和服务器加载模式（通过 `fetch` 从后端读 db）
- [x] 服务器模式下支持单元格双击编辑和行删除（读写模式）
- [x] SQL 执行框可用

## Blocked by

- #01-project-skeleton

## Completion summary (2026-06-14)

### Backend changes (`main_outline.py`)
- Added `GET /db-viewer` route to serve `db-viewer-02outline.html`
- Added `GET /api/outline/db-path` — returns absolute filesystem path of the SQLite DB
- Added `GET /api/outline/db` — serves the raw SQLite file for sql.js loading
- Added `POST /api/outline/db-table/_sql` — executes arbitrary SQL (SELECT returns rows; INSERT/UPDATE/DELETE commits and returns affected rowcount; DDL commits and returns success; errors return 400 with detail)
- All 8 API tests pass (TestClient): root HTML, db-viewer HTML, db-path, db-file serving, SQL SELECT, SQL UPDATE, empty SQL rejection, bad SQL rejection

### Frontend changes (`db-viewer-02outline.html`)
- **SCHEMA**: Replaced `asr_sentences` with `course_topics` (8 columns: id, video_id, start_para_index, end_para_index, start_time, end_time, topic_name, subtree_json; FK to videos(id))
- **CONFIG_DEFAULTS**: Replaced corpus-specific keys with 5 `ob_` prefix items: `ob_llm_model`, `ob_llm_temperature`, `ob_max_topics`, `ob_prompt_round1`, `ob_prompt_round2`
- **API paths**: All 4 occurrences of `/api/corpus/` changed to `/api/outline/` (inline edit save, delete cascade loop, SQL runner, and db-path fetch)
- **Cascade delete**: Updated for outline schema — deleting a video cascades to `asr_sentences` + `corpus_paragraphs` + `course_topics`; deleting corpus_paragraphs cascades to `asr_sentences`
- **loadDefault()**: Simplified to fetch from `/api/outline/db` (single reliable endpoint) instead of trying multiple relative paths
- **Title/i18n**: Updated page title, h1, and all 3 locale `title` keys to "📊 corpus.db · Outline"
- **Verification**: 0 remaining `/api/corpus/` references; `asr_sentences` only appears in cascade delete logic (correct); `course_topics` confirmed in schema + cascade
