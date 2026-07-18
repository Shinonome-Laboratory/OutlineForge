# 02 — SSE 全透明控制台

Status: done

## What to build

`/api/stream/logs/outline` SSE 端点，前端底部 250px 终端风格监视窗口。Python `logging` 模块拦截日志通过 SSE 推送，异常时带完整 `traceback.format_exc()` 以红字显示。故意用 `1/0` 触发除零错误验证红字 Traceback 回显。

## Acceptance criteria

- [x] `GET /api/stream/logs/outline` 返回 `text/event-stream`
- [x] 前端底部 250px 终端窗口，`bg-gray-950 text-green-400 font-mono text-xs`
- [x] 正常日志（info/debug 级别）以绿色实时追加显示
- [x] 故意触发除零错误 → 红字 Traceback + 原因诊断出现在窗口
- [x] 窗口底部有「从断点继续执行」和「重试当前步骤」按钮（功能先做占位，Slice 6–7 之后真正可用）

## Blocked by

- #01-project-skeleton

## Comments

### Implementation summary (2026-06-14)

**TDD: Red → Green → Refactor** — 14 new tests added to `test/test_outline.py`, full suite 42/42 passing.

**Backend** (`main_outline.py`):
- `LogEvent` dataclass — structured event with category, message, timestamp, optional traceback and progress_pct
- `SSELogHandler` — custom `logging.Handler` that converts `LogRecord` → `LogEvent`, pushes to `asyncio.Queue` via `call_soon_threadsafe` for thread safety
- `_event_to_sse()` — formats a `LogEvent` as `event: <category>\ndata: <json>\n\n`
- `sse_event_generator()` — async generator that reads from the queue indefinitely
- `push_log_event()` — direct queue push for custom categories (success, progress) that bypass the logging module
- `GET /api/stream/logs/outline` — returns `StreamingResponse` with `text/event-stream` media type
- `POST /api/outline/trigger-error` — deliberately triggers `1/0`, logs via outline logger, returns `{"status": "error_triggered"}`
- Lifespan: captures event loop, attaches `SSELogHandler` to `"outline"` logger at DEBUG level, cleans up on shutdown

**Frontend** (`outline.html`):
- 250px fixed-bottom console with `bg-gray-950 text-green-400 font-mono text-xs`
- Status bar with clock (updates every second)
- Dynamic text-based progress bar: `[████████░░░░░░] 50%` (hidden until progress events arrive)
- Log stream area with `overflow-y-auto`, auto-scrolls to bottom
- `EventSource` connects to `/api/stream/logs/outline`, listens for all five categories
- Color coding: error → `text-red-400`, success → `text-green-300`, progress → `text-yellow-400`, debug → `text-gray-500`, info → `text-green-400`
- Traceback renders as indented `whitespace-pre-wrap` block below error lines
- "测试错误显示" button → POSTs to trigger-error, traceback appears in red
- "从断点继续执行" and "重试当前步骤" buttons — placeholder, log a message on click
- Preserves existing config panel (Slice 11) — page uses `flex flex-col` layout

**Verified**: SSE stream produces correct `event: error` with full `ZeroDivisionError` traceback including file path and line number.
