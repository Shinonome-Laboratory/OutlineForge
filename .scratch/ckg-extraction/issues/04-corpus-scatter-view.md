# 04 — 全库散点视图

Status: done

## What to build

跨课对比视图：把全库每节课的 CKG 参数打到一张散点图上。

- 新增读取 API：返回所有已抽 CKG 的视频的参数（至少 `depth`、`bottomup_ratio`、视频名）。
- 前端散点视图：**每节课一个点**，默认轴 `x = depth`（拓扑轴）、`y = bottomup_ratio`（走向轴），与单课 DAG 视图用切换开关并存。
- 用途：单教师阶段"看吴恩达各课拓扑聚不聚"的 sanity check；将来加入第二位教师后，同一界面升级为 within/between 距离对比。

## Acceptance criteria

- [ ] 读取 API 返回全库已抽视频的 CKG 参数（含 depth、bottomup_ratio、视频名）
- [ ] 散点视图每课一点，默认轴 depth × bottomup_ratio
- [ ] 单课 DAG 视图 / 全库散点视图可切换并存
- [ ] 对吴恩达全库（已抽部分）实际打点显示

## Blocked by

- 03-topology-params-delivery-direction

## Comments

- **2026-06-25 16:42** — 自动开发完成。实现要点：新增 `GET /api/outline/ckg`（全库，join videos 取名，返回每节课 depth/bottomup_ratio 等参数），右侧视图区加「全库散点」第三态切换，ECharts scatter 默认轴 x=depth / y=bottomup_ratio，bottomup_ratio 为 null 的课跳过不打点并以小字注明跳过数量（避免伪装成 y=0 误导聚集判断），i18n 三语补齐 ckg.view_scatter 等 key；代码注释标注将来加第二位教师升级为 within/between 对比。人工验收待办：吴恩达全库抽取后看散点聚集情况。
