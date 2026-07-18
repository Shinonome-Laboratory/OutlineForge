# 11 — 参数配置面板

Status: done

## What to build

页面顶部可折叠参数配置面板。包含：模型下拉菜单（动态获取 Ollama 模型列表）、温度滑动条（0.0–1.0，步长 0.1）、最大话题数输入框（支持数字或 `auto`）、两轮 Prompt 文本框。读 `GET /api/outline/config` 获取当前值，修改后 `PUT /api/outline/config` 保存。参数修改后立即对下一次分析生效。

## Acceptance criteria

- [x] 面板可折叠/展开，默认折叠
- [x] 模型下拉菜单通过 `GET /api/outline/ollama/models` 动态获取本地模型列表
- [x] 温度滑动条范围 0.0–1.0，步长 0.1，当前值显示在滑块旁
- [x] 最大话题数输入框，输入 `auto` 或正整数，非数字值时红色提示
- [x] 两轮 Prompt 各一个文本框，默认预填英文 Prompt
- [x] 修改任意参数后点击保存 → `PUT /api/outline/config` → 成功后绿色提示
- [x] 刷新页面后参数保持修改后的值

## Blocked by

- #01-project-skeleton

## Completion summary

**Backend** (main_outline.py):
- `GET /api/outline/config` — returns all `ob_` prefix keys as `{key: value}` JSON
- `PUT /api/outline/config` — UPSERT config keys (rejects non-`ob_` prefix), returns updated values
- `GET /api/outline/ollama/models` — proxies Ollama `/api/tags`, returns flat list of model name strings; 503 if Ollama unreachable
- Helper function `_fetch_ollama_tags()` extracted for testability (avoids mocking `httpx.Client.get` which conflicts with TestClient)

**Frontend** (outline.html):
- Collapsible config panel toggled via button, collapse state persisted in localStorage
- Model `<select>` dropdown populated from API on page load
- Temperature `<input type="range">` 0.0–1.0 step 0.1 with live value display
- Max topics `<input type="text">` with validation (accepts `auto` or positive integer, red border on invalid)
- Two prompt `<textarea>` fields pre-filled from config
- Save button with green flash animation on success

**Tests** (test/test_outline.py — 8 new tests, all passing):
- `test_get_config_returns_all_ob_keys`
- `test_put_config_updates_existing_key`
- `test_put_config_upserts_multiple_keys`
- `test_put_config_rejects_non_ob_prefix_key`
- `test_put_config_rejects_mixed_keys`
- `test_put_config_empty_body_returns_400`
- `test_get_ollama_models_returns_list`
- `test_get_ollama_models_handles_ollama_unavailable`
- `test_get_ollama_models_extracts_name_only`

**Files changed:**
- `main_outline.py` — added 3 routes + 1 helper function (lines 383–459)
- `outline.html` — full config panel UI with vanilla JS (complete rewrite)
- `test/test_outline.py` — 9 new test functions (lines 234–379)

**TDD flow:** Red (wrote tests → 404) → Green (implemented routes) → Refactor (extracted `_fetch_ollama_tags()`, fixed mock interference with TestClient, added DB restore in tear-down)
