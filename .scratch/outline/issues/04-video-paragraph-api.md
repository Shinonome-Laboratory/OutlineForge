# 04 — 视频列表 + 段落浏览（后端 API）

Status: done

## What to build

两个只读 API 端点：`GET /api/outline/videos` 返回已完成处理的视频列表（从 `videos` 表 `WHERE status='done'`），`GET /api/outline/video/{video_id}/paragraphs` 返回该视频的全部段落（从 `corpus_paragraphs` 按 `paragraph_index` 排序）。

## Acceptance criteria

- [x] `GET /api/outline/videos` 返回 JSON 数组，字段包含 `id`、`name`、`duration`、段落数
- [x] `GET /api/outline/video/{id}/paragraphs` 返回 JSON 数组，每项含 `paragraph_index`、`start_time`、`end_time`、`text`（截断前 100 字）
- [x] 视频不存在时返回 404
- [x] 数据库路径指向 `00-data/corpus.db`

## Blocked by

- #01-project-skeleton

## Completion summary

**Date:** 2026-06-14

**TDD cycle:** Red → Green → Refactor completed.

### Red phase
Added 12 test cases in `test/test_outline.py` (Slice 04 section):
- `test_get_videos_returns_json_array` — response is a JSON list with 200
- `test_get_videos_each_item_has_required_keys` — each item has id, name, duration, paragraph_count
- `test_get_videos_all_have_status_done` — all videos have paragraph_count > 0 (done status)
- `test_get_videos_returns_known_videos` — verifies the 3 known videos and their exact paragraph counts (25→29, 29→343, 31→218)
- `test_get_paragraphs_returns_json_array` — response is a JSON list with 200
- `test_get_paragraphs_each_item_has_required_keys` — each item has paragraph_index, start_time, end_time, text
- `test_get_paragraphs_text_truncated_to_100_chars` — text length ≤ 100 for all paragraphs
- `test_get_paragraphs_ordered_by_index` — paragraphs sorted ascending by paragraph_index
- `test_get_paragraphs_returns_correct_count` — video 25 returns exactly 29 paragraphs
- `test_get_paragraphs_first_item_matches_db` — first paragraph has paragraph_index=1, start_time=0.0, end_time=12.56
- `test_get_paragraphs_nonexistent_video_returns_404` — video 99999 returns 404
- `test_get_paragraphs_nonexistent_video_has_detail` — 404 response includes detail key
All 12 tests initially failed (routes did not exist).

### Green phase
Implemented two routes in `main_outline.py`:
1. `GET /api/outline/videos` — LEFT JOINs `videos` with a `corpus_paragraphs` COUNT subquery, filters `WHERE status='done'`, returns `[dict(row)]` array with COALESCE for paragraph_count.
2. `GET /api/outline/video/{video_id}/paragraphs` — validates video existence (404 if not found), queries corpus_paragraphs ordered by paragraph_index, uses `SUBSTR(text, 1, 100)` for truncation, returns 404 if no paragraphs found.
All 12 tests pass, no regressions in existing tests.

### Refactor
Code follows existing patterns (get_db helper, sqlite3.Row, dict(row) conversion). No refactoring needed.

### Files changed
- `d:\Project\All for Style\02-outline\main_outline.py` — added 2 routes (~40 lines)
- `d:\Project\All for Style\02-outline\test\test_outline.py` — added 12 tests (~120 lines)
