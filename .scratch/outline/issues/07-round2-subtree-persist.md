# 07 — 第二轮 LLM 分析（子树生成）+ 落盘

Status: done

## What to build

接 Slice 6 的话题切分结果，逐话题调 Ollama 生成知识子树。每个话题：取对应段落文本拼接 → 用 `ob_prompt_round2`（替换 `{topic_name}`）调 Ollama → 解析子树 JSON → 即时 INSERT 到 `course_topics`。SSE 推送每个话题的完成进度（"话题 2/5 完成"）。单个话题失败不影响已完成的，支持对失败话题重试。

## Acceptance criteria

- [x] 逐话题串行调用 Ollama，话题 N 完成后立即 INSERT 到 `course_topics`
- [x] SSE 推送：`progress`（"话题 2/5 正在生成子树…"）、`success`（单个话题完成）、`error`（单话题失败带 LLM 输出）
- [x] `course_topics` 每行 `subtree_json` 格式正确，含 `course_name` 和 `subtree`
- [x] 所有话题完成后 SSE 推送 `success`（"全部 N 个话题完成"）
- [x] 单个话题 JSON 解析失败时：该话题跳过、SSE 报错、已完成的保留
- [x] 支持中止——已写入的行保留，未开始的跳过
- [x] 时间字段 `start_time`/`end_time` 从首/末段落的时间戳正确派生

## Blocked by

- #06-round1-topic-segmentation

## Completion summary

**Date:** 2026-06-14

**Implementation:**

1. `parse_round2_response(raw, topic_name)` — parses LLM round-2 JSON output into subtree dict. Handles markdown fences, leading/trailing text, and structural validation (must contain `subtree` key). Returns `None` on failure.

2. `_run_round2_analysis(video_id)` — iterates topics from `_topic_segmentation_results[video_id]`:
   - Filters paragraphs by topic range, concatenates, builds prompt with `{topic_name}` replacement
   - Calls Ollama `/api/generate`, parses subtree JSON
   - On parse failure: pushes `error` SSE event with raw output preview, skips topic, continues
   - On success: derives `start_time`/`end_time` from first/last paragraph, INSERTs into `course_topics` immediately, pushes `success` event
   - Supports cancel between topics via `_analysis_cancel_flags`
   - Final summary event: "全部 N 个话题完成" (or "N 成功, M 失败")

3. `_run_full_analysis(video_id)` — wrapper that runs round1 then round2 sequentially in the same thread. Cancels clean up in `finally`.

4. `POST /api/outline/analyze/{video_id}` — updated to spawn `_run_full_analysis` instead of `_run_round1_analysis`.

5. `_run_round1_analysis` — removed `finally` block (cancel-flag cleanup moved to wrapper).

**Files changed:**
- `main_outline.py`: +200 lines (parse_round2_response, _run_round2_analysis, _run_full_analysis, endpoint update)
- `test/test_outline.py`: +400 lines (19 new tests)

**Tests (19 new, 86 total — all pass):**
- 9 `parse_round2_response` unit tests (valid, empty children, deep nesting, invalid JSON, wrong structure, truncated, empty, markdown fences, leading text)
- 7 round2 flow tests (INSERT, subtree_json format, time derivation, error-per-topic, cancel-between-topics, no-round1-result, empty-topics)
- 3 edge cases (no paragraphs for topic range, Ollama call failure per topic, full pipeline end-to-end)
