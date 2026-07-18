# 05 — 视频列表 + 段落浏览（前端）

Status: done

## What to build

`outline.html` 页面基础布局：视频下拉选择器、段落列表展示区。用户选择视频后，调用 Slice 4 的 API 拉取段落数据并渲染为表格（序号、时间戳、文本截断预览）。

## Acceptance criteria

- [x] 页面加载时视频下拉框自动填充已完成视频列表
- [x] 选择视频后，下方展示段落列表（段落序号、起始时间、文本前 100 字）
- [x] 未选视频时展示空状态提示
- [x] 语言切换按钮可用（zh/en/ja），段落列表文本跟随切换
- [x] 页面整体布局为顶部参数区（预留 Slice 11）+ 中部主内容区 + 底部控制台（Slice 2 已实现）

## Blocked by

- #04-video-paragraph-api

---

## Completion Summary (2026-06-14)

### What was delivered

**outline.html** — single-page application updated with:

1. **Video selector dropdown** — populated from `GET /api/outline/videos` on page load. Each option shows video name + paragraph count + duration. Default placeholder text: "请选择视频…"

2. **Paragraph table** — when user selects a video, fetches `GET /api/outline/video/{id}/paragraphs` and renders a table with columns:
   - `#` — row number
   - `段落序号` — paragraph_index
   - `起始时间` — start_time formatted as MM:SS
   - `结束时间` — end_time formatted as MM:SS
   - `文本预览` — text (server-truncated to 100 chars)

3. **Empty state** — centered friendly placeholder shown when no video is selected: "请选择一个视频" with hint text.

4. **Layout** — flex column structure: config panel (collapsible, Slice 11) → main content (video selector + scrollable paragraph table) → SSE console (fixed 250px, Slice 02). Uses `h-screen flex flex-col` on body and `flex-1 flex flex-col min-h-0 overflow-hidden` on the app container for proper nested scrolling.

5. **i18n system** — zh/en/ja translations for all UI labels:
   - `I18N` object with ~48 translation keys across 3 languages
   - `t(key)` lookup function with zh fallback
   - `setLang(lang)` with localStorage persistence
   - `applyI18N()` updates all `data-i18n`, `data-i18n-html`, and `data-i18n-placeholder` elements
   - Language switcher buttons in header (中文 / EN / 日本語)
   - Paragraph count suffix adapts to current language
   - Console status bar text follows language switch

### TDD
- Added **7 edge-case tests** to `test/test_outline.py`:
  - `test_get_paragraphs_time_fields_are_numeric`
  - `test_get_paragraphs_text_is_non_empty`
  - `test_get_paragraphs_negative_video_id_returns_404`
  - `test_get_paragraphs_zero_video_id_returns_404`
  - `test_get_paragraphs_large_video_count`
  - `test_get_paragraphs_first_and_last_indices_match`
  - `test_get_paragraphs_non_string_video_id_returns_422`
- All **49 tests pass** (35 pre-existing + 7 new edge cases + 7 from other slices)

### Preserved functionality
- Slice 02 SSE Console — fully intact, with graceful i18n integration (falls back to hardcoded Chinese if i18n functions unavailable)
- Slice 11 Config Panel — fully intact, labels now data-i18n driven
- Backend `main_outline.py` — **unchanged** (all API endpoints were already in place from Slice 04)
