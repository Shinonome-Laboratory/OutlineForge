# 06 — 第一轮 LLM 分析（话题切分）

Status: done

## What to build

后台线程：将所有 `corpus_paragraphs` 段落文本按 `paragraph_index` 拼接为全文 → 用 `ob_prompt_round1` + 全文调 Ollama → 解析返回 JSON 获取 `course_name` 和 `topics` 数组 → SSE 推送进度和 Ollama token 流 → 结果暂存内存（落盘留给 Slice 7）。支持用户点击中止按钮停止分析。

## Acceptance criteria

- [x] `POST /api/outline/analyze/{video_id}` 启动后台线程，返回 202
- [x] 后台拼接全文、调 Ollama、解析 JSON
- [x] SSE 实时推送：`info`（"正在拼接全文…"、"调用 LLM 进行话题切分…"）、可选 `ollama_stream`（token 逐字）
- [x] 返回的 JSON 解析成功，格式为 `{"course_name": "...", "topics": [{name, start_para, end_para}]}`
- [x] JSON 解析失败时发送 `error` 事件，附 LLM 原始输出前 500 字
- [x] `POST /api/outline/stop/{video_id}` 可中止，SSE 推送 `info`（"分析已中止"）
- [x] 解析失败时不落盘、不崩溃，控制台显示错误并支持重试

## Blocked by

- #05-video-paragraph-ui

## Completion summary

**TDD**: Red-Green-Refactor cycle completed. 18 new tests written, all 67 tests pass.

### Backend (`main_outline.py`)

**New module-level state:**
- `_topic_segmentation_results: Dict[int, dict]` — stores parsed round-1 results keyed by `video_id`. Consumed by Slice 07.
- `_analysis_cancel_flags: Dict[int, bool]` — tracks cancel requests. `True` = cancel requested, `False` = running, absent = no analysis.

**New functions:**
- `parse_round1_response(raw: str) -> dict | None` — robust JSON parser that handles markdown fences, leading/trailing text, and structural validation (requires `course_name` + `topics` with `name`, `start_para`, `end_para` per topic).
- `concat_paragraphs(paragraphs) -> (str, dict)` — joins paragraph texts with `[段落 N]` markers for LLM input.
- `_fetch_paragraphs_full_text(video_id) -> list[dict]` — fetches full paragraph texts from DB (extracted for mockability).
- `_call_ollama_generate(model, prompt, stream=False) -> dict` — calls `POST http://localhost:11434/api/generate` (extracted for mockability).
- `_run_round1_analysis(video_id)` — background worker thread: fetch → concat → load config → call Ollama → parse → store. Checks cancel flag between each step. Cleans up flag in `finally` block.

**New endpoints:**
- `POST /api/outline/analyze/{video_id}` — validates video exists and has paragraphs, checks no analysis is already running (409 if so), sets cancel flag to `False`, spawns daemon thread, returns 202.
- `POST /api/outline/stop/{video_id}` — sets cancel flag to `True`, returns 200. Idempotent.

### Frontend (`outline.html`)

- i18n keys added: `analyze.btn`, `analyze.running`, `analyze.success`, `analyze.error`, `analyze.stopping` (zh/en/ja).
- "生成分析" button + "中止" button added between video selector and paragraph table.
- JavaScript controller (`startAnalysis`, `stopAnalysis`, `setAnalyzeUIState`, `appendConsoleLog`) manages button state and API calls.
- SSE console controller updated to reset analyze button on `success`/`error` events, and detect cancellation messages ("分析已中止").

### Test coverage

18 new tests in `test/test_outline.py`:
- `test_parse_llm_response_*` (8 tests) — valid JSON, single topic, invalid JSON, wrong structure, truncated, empty string, markdown fences, leading text extraction.
- `test_concat_paragraphs_to_full_text` — paragraph concatenation with markers.
- `test_analyze_endpoint_returns_202` — full integration test with mocked Ollama and paragraph fetch, verifies thread stores result.
- `test_analyze_endpoint_nonexistent_video_returns_404`, `test_analyze_endpoint_already_running_returns_409`.
- `test_stop_endpoint_*` (3 tests) — sets cancel flag, idempotent, works for non-existent video.
- `test_cancel_flag_stops_worker_before_ollama` — cancel flag prevents Ollama call.
- `test_parse_failure_pushes_error_event` — invalid LLM output does NOT store result.
- `test_i18n_has_analyze_button_label` — verifies all 5 i18n keys exist in outline.html.
