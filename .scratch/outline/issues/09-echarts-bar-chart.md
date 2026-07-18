# 09 — ECharts 分段条形图

Status: done

## What to build

左栏 ECharts 水平条形图，展示各话题的时间占比。每条对应一个话题，条长度 = 该话题 `duration`（`end_time - start_time`），标签显示 `topic_name`。点击某条可联动 jsMind 定位到对应节点（预留 Slice 10）。

## Acceptance criteria

- [x] 左栏渲染 ECharts 条形图，每个话题一条
- [x] 条长度与各话题时长成比例
- [x] 标签显示 `topic_name`，hover 显示详细时间范围
- [x] 无数据时不报错，展示空状态
- [x] 与 Slice 8 的 jsMind 位于同一页面，左右栏布局

## Blocked by

- #07-round2-subtree-persist
