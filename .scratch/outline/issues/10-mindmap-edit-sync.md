# 10 — 思维导图编辑 + 回写

Status: done

## What to build

用户在 jsMind 思维导图上右键操作：重命名节点、新增子节点、删除分支。每次操作后定位到受影响的 `course_topics` 行 → `PUT /api/outline/topics/{id}` 将修改后的 `subtree_json` 单行回写。不涉及跨行拖拽移动（拖拽暂不实现）。

## Acceptance criteria

- [x] 右键"重命名"节点 → 弹出输入框 → 确认后更新该行 `subtree_json` → `PUT` 落盘
- [x] 右键"新增子节点" → 输入节点名 → 追加到对应节点的 `children` → `PUT` 落盘
- [x] 右键"删除分支" → 确认 → 移除对应节点 → `PUT` 落盘
- [x] PUT 请求成功后 UI 即时更新，无需整页刷新
- [x] PUT 失败时 UI 回滚到修改前状态，提示错误
- [x] 修改 `topic_name`（根节点直接子节点）时同步更新 `course_topics.topic_name` 列
- [x] 知识树节点上有 `data-topic-id` 属性标记来源行，确保编辑定位准确

## Blocked by

- #08-mindmap-render

## Completion summary

**Backend** (`main_outline.py`):
- Added `PUT /api/outline/topics/{topic_id}` endpoint
- Accepts JSON body with optional `topic_name` and `subtree_json` fields
- Validates: empty body → 400, non-existent id → 404, unexpected fields → 422
- Uses parameterized SQL UPDATE, returns the updated row as JSON
- 13 unit/integration tests added (all pass)

**Frontend** (`outline.html`):
- Enabled jsMind editing mode: `editable: true`
- `buildFullTree`: sets `data: {"topic-id": row.id}` on each topic node
- `convertToJsMindNodes`: propagates `topicRowId` to all descendant nodes
- `findAffectedRowId(nodeId)`: reads `data["topic-id"]` from jsMind node
- `serializeMindMapToSubtree(topicRowId)`: converts jsMind subtree → LLM-native `{course_name, subtree: {children}}` format
- `syncMindMapEdit(nodeId)`: PUTs updated subtree_json (and topic_name for root-direct children) to backend
- `syncDeleteToBackend(topicRowId)`: POST-delete sync after node removal
- `_overrideJsMindMethods()`: wraps `update_node`, `add_node`, `remove_node` on the jsMind instance
  - `update_node`: calls original, then syncs
  - `add_node`: prompts for name, calls original with topic-id data, then syncs
  - `remove_node`: confirms with user, calls original, then syncs affected row
- `_showEditFeedback(success, message)`: green flash on success (auto-fades), red error on failure
- On PUT failure: reloads mind map from server to revert UI state
- Added i18n keys for edit operations (zh/en/ja): `mindmap.edit_saved`, `mindmap.edit_save_failed`, `mindmap.edit_add_child_prompt`, `mindmap.edit_delete_confirm`

**Tests**: 102 total, all passing (13 new for Slice 10)
