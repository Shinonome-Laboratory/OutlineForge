# 08 — 知识树前端拼接 + jsMind 渲染

Status: done

## What to build

前端拉取 `GET /api/outline/topics/{video_id}` 获取所有话题行 → JS 将各行 `subtree_json` 拼成完整知识树 → 转 jsMind 格式 → jsMind.js 渲染可交互思维导图（支持展开/折叠节点、缩放、拖拽画布）。

## Acceptance criteria

- [x] `GET /api/outline/topics/{video_id}` 返回该视频所有 topic 行
- [x] 前端 JS `buildFullTree(rows)` 将各行拼接为完整树（根节点 = `course_name`，子节点 = 各 `topic_name` 挂 `subtree`）
- [x] `convertToJsMindNodes()` 将 LLM 原生格式递归转为 jsMind 格式（生成唯一 `id`，包装 `topic`/`children` 结构）
- [x] jsMind 渲染的思维导图节点层级正确，可展开/折叠
- [x] 无话题数据时展示空状态提示："请先生成分析"

## Blocked by

- #07-round2-subtree-persist
