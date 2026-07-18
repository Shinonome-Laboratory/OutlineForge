<h1 align="center">🌳 OutlineForge <code>outline</code></h1>

<p align="center">Classroom content structure analysis — topic segmentation, knowledge trees, course knowledge graphs, and teacher content-organization style profiling, powered by a local LLM.</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI"></a>
  <a href="https://echarts.apache.org/"><img src="https://img.shields.io/badge/ECharts-5.5-AA344D?logo=apacheecharts&logoColor=white" alt="ECharts"></a>
  <a href="https://ollama.com/"><img src="https://img.shields.io/badge/LLM-Ollama%20%C2%B7%20qwen2.5:14b-000000?logo=ollama&logoColor=white" alt="Ollama"></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-shared%20corpus.db-003B57?logo=sqlite&logoColor=white" alt="SQLite"></a>
  <a href="test/"><img src="https://img.shields.io/badge/tests-322%20collected-brightgreen" alt="Tests"></a>
  <img src="https://img.shields.io/badge/Vibe%20Coding-100%25-blueviolet" alt="Vibe Coding">
</p>

<p align="center">Sibling project: <a href="https://github.com/Shinonome-Laboratory/CorpusForge">📝 CorpusForge <code>corpus</code></a> — the upstream corpus pipeline that feeds this project.</p>

---

<details>
<summary>🇨🇳 中文</summary>

**OutlineForge** 是 "All for Style" 课堂分析系统的 **Function B——课堂内容结构分析**。它读取上游 [CorpusForge](https://github.com/Shinonome-Laboratory/CorpusForge)（Function A）产出的课堂转写语料，用本地 LLM 把一节课的"台本"拆成层级化的知识结构，进而刻画**教师如何组织内容**的风格特征。

在"舞台剧模型"中，课堂被解构为双轨时序流：**台本**（教学内容演进）+ **演技**（微观教学动作）。本项目负责台本维度。

## ✨ 核心功能

- 🔪 **两轮 LLM 话题切分** — 第一轮把完整台本按语义边界切成话题段（断点式分界，天然不重叠）；第二轮对每个话题独立生成知识子树，拼装成整节课的知识树
- 🕸️ **课程知识图谱（CKG）抽取** — 以「课程标题 → 教学概念」的拆解为骨架，叠加教师课中实际明说的跨支讲述关联，并标注每个概念的引入位置——刻画"这位老师怎么讲"，而非学科客观结构
- 🃏 **CK 风格画像卡** — 从 CKG 计算内容组织风格参数，支持视频 / 课程 / 教师三级作用域聚合（层级选择：教师 → 课程）
- 📝 **教案生成** — 基于风格画像反向生成教案：上传新材料，按目标教师的组织风格产出教学单元
- 🖥️ **交互式工作台** — ECharts 树形思维导图（roam 缩放/平移/折叠）、话题分布时间轴甘特图、视频播放器联动、深色 SSE 实时日志控制台
- 🗄️ **内置 DB Viewer** — 浏览共享 corpus.db、执行 SQL、下载数据库快照
- 🌏 **三语界面** — 中文 / English / 日本語，偏好存 localStorage

## 💭 开发哲学

这个项目没有一行代码是手工逐字敲出来的——它是 **100% Vibe Coding** 的产物，由 Claude Code 在人类的需求描述、验收反馈和方向纠偏下迭代而成。开发流程本身也是结构化的：需求先落成 PRD，再拆成可独立领取的 issue（见 [`.scratch/`](.scratch/)），按 TDD 红绿循环实现。322 个测试就是这么攒出来的。

诚实地说：`main_outline.py` 有 16 万字符，如果让我逐行读完它，我大概会先去写第三个项目。但每一个行为都有测试钉住——这是 Vibe Coding 能走远的前提。

## 🏗️ 架构总览

```
CorpusForge (Function A)                OutlineForge (Function B)
┌─────────────────────┐    corpus.db    ┌──────────────────────────────────┐
│ 视频 → ASR → 段落化  │ ──────────────▶ │  corpus_paragraphs (只读消费)      │
└─────────────────────┘   (共享 SQLite)  └──────────────┬───────────────────┘
                                                       │
                     ┌─────────────────────────────────┼─────────────────┐
                     ▼                                 ▼                 ▼
        ┌─ 两轮 LLM 分析 ──────────┐      ┌─ CKG 抽取 ──────────┐   ┌─ 教案生成 ──────┐
        │ R1: 全文 → 话题切分       │      │ 拆解骨架 (标题→概念)  │   │ 画像参数 + 新材料 │
        │ R2: 每话题 → 知识子树     │      │ + 讲述关联 (跨支边)   │   │  → 风格化教学单元 │
        └──────────┬──────────────┘      │ + 引入位置 (段落序号)  │   └────────────────┘
                   ▼                     └──────────┬──────────┘
        知识树 (course_topics)                       ▼
                   │                        CK 风格画像卡
                   ▼                       (视频/课程/教师 作用域)
        前端: 时间轴甘特 + ECharts 思维导图 + SSE 控制台
```

## 🚀 快速开始

| 前置条件 | 说明 |
|---|---|
| Python 3.10+ | 依赖见 `requirements.txt` |
| [Ollama](https://ollama.com/) | 本地运行，默认模型 `qwen2.5:14b-instruct` |
| `corpus.db` | 由 CorpusForge 产出，置于 `../00-data/corpus.db` |

```bash
pip install -r requirements.txt
python setup.py    # 环境自检 + 自动修复
python start.py    # 停旧进程 → 启动 (port 8001) → 自动开浏览器
python stop.py     # 停止服务
```

典型工作流：选择已转写视频 → **生成分析**（SSE 控制台实时看进度）→ 时间轴 + 思维导图审阅 → 需要时编辑话题/子树 → 抽取 CKG → 查看画像卡。

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3 · FastAPI · uvicorn (port 8001) · threading + SSE |
| 前端 | 单页 HTML · Tailwind CSS（自定义主题）· ECharts 5.5 · 原生 JS |
| LLM | Ollama `/api/generate` · 默认 `qwen2.5:14b-instruct` · Prompt 在线可编辑 |
| 存储 | SQLite（与 Function A 共享 `corpus.db`）|
| 测试 | pytest · 322 个测试 |

## 📡 API 端点

| 分组 | 端点 | 说明 |
|---|---|---|
| 页面 | `GET /` · `GET /db-viewer` | 工作台 / 数据库查看器 |
| 视频 | `GET /api/outline/videos` · `…/video/{id}/paragraphs` · `…/video/{id}/file` | 视频列表、段落、文件流 |
| 分析 | `POST /api/outline/analyze/{video_id}` · `…/regenerate/{video_id}` · `…/stop/{video_id}` | 启动 / 重跑 / 中止两轮分析 |
| 话题 | `GET /api/outline/topics/{video_id}` · `PUT …/topics/{topic_id}` | 读取 / 编辑话题与子树 |
| CKG | `POST·GET·PUT·DELETE /api/outline/ckg/{video_id}` · `GET …/ckg` · `GET·PUT …/ckg/prompts` | 抽取、增删改查、Prompt 配置 |
| 画像 | `GET …/ckg/profile` · `…/video/{id}/ck-profile` · `…/teachers/{id}/ck-profile` | 全库 / 视频 / 教师作用域画像 |
| 教案 | `POST …/lesson-gen(/analyze·/generate-units·/extract-file)` · `…/lesson-plans` CRUD | 风格化教案生成与管理 |
| 配置 | `GET·PUT /api/outline/config` · `GET …/config-defaults` · `…/ollama/models` | 模型、温度、Prompt 等 |
| 其他 | `GET /api/stream/logs/outline` · `GET …/db` · `POST …/db-table/_sql` | SSE 日志流、下载 DB、执行 SQL |

## 📁 项目结构

```
02-outline/
├── main_outline.py           # FastAPI 应用：路由 + 两轮分析 + CKG + 画像 + 教案生成
├── database_outline.py       # SQLite schema / 迁移 / 配置表 / 内置 Prompt
├── outline.html              # 单页前端工作台
├── db-viewer-02outline.html  # 数据库查看器
├── setup.py / start.py / stop.py   # 环境自检 / 一键启停
├── conftest.py               # pytest fixtures
├── test/                     # 322 个测试
└── .scratch/                 # issue 追踪（开发过程实录）
```

## ⚙️ 配置项

存于共享库 `config` 表，可在应用内设置面板在线编辑：

| 键 | 默认值 | 说明 |
|---|---|---|
| `ob_llm_model` | `qwen2.5:14b-instruct` | Ollama 模型名 |
| `ob_llm_temperature` | `0.0` | 采样温度 |
| `ob_llm_num_ctx` | `8192` | 上下文窗口（Ollama 默认 ~2048 且**静默截断**，故显式调大） |
| `ob_prompt_round1` | 内置 | 第一轮话题切分 Prompt（"课程设计师"人设） |
| `ob_prompt_round2` | 内置 | 第二轮知识子树 Prompt |
| `ck_prompt_concepts` | 内置 | CKG 概念抽取 Prompt |
| `ck_prompt_relations` | 内置 | CKG 讲述关联 Prompt |

## 🧪 测试

```bash
python -m pytest test/ -q
```

322 个测试覆盖两轮分析管线、CKG 抽取、画像聚合、教案生成与教师归属层（`test/test_outline.py` 端到端主线 + `test/test_20_teachers.py` 归属层）。测试直接读取共享 `corpus.db` 的真实种子数据。

## 📚 关联文档

- [📝 CorpusForge](https://github.com/Shinonome-Laboratory/CorpusForge) — Function A：视频 → ASR → 段落化语料的上游流水线
- [`.scratch/`](.scratch/) — 各功能的 issue 拆解与开发实录

## 🙏 致谢

由 [Claude Code](https://claude.com/claude-code) 驱动开发；感谢 [Ollama](https://ollama.com/)、[Apache ECharts](https://echarts.apache.org/) 与 [FastAPI](https://fastapi.tiangolo.com/) 让本地优先的课堂分析成为可能。

</details>

<details open><summary>🇬🇧 English</summary>

**OutlineForge** is **Function B — classroom content structure analysis** — of the "All for Style" classroom analysis system. It consumes the lecture transcripts produced by [CorpusForge](https://github.com/Shinonome-Laboratory/CorpusForge) (Function A) and uses a local LLM to decompose each lesson's "script" into a hierarchical knowledge structure, ultimately characterizing **how a teacher organizes content**.

In the *Theater Model*, a classroom is decomposed into two parallel temporal streams: the **Script** (progression of teaching content) and the **Performance** (micro-level teaching actions). This project owns the Script dimension.

## ✨ Features

- 🔪 **Two-round LLM analysis** — Round 1 segments the full transcript into topics at semantic boundaries (breakpoint-style `last_para` output, overlap-free by construction); Round 2 generates a knowledge subtree per topic, assembled into the lesson's knowledge tree
- 🕸️ **Course Knowledge Graph (CKG) extraction** — a decomposition skeleton (course title → concepts) overlaid with cross-branch *grounded relations* the teacher actually stated in class, plus each concept's *introduction position*. It captures *how this teacher teaches*, not the discipline's objective structure
- 🃏 **CK style profile cards** — content-organization style parameters computed from CKGs, aggregated at video / course / teacher scope (hierarchical selection: teacher → course)
- 📝 **Lesson generation** — invert the profile: upload new material and generate teaching units in a target teacher's organizational style
- 🖥️ **Interactive workbench** — ECharts tree mind-map (roam zoom/pan/collapse), topic-distribution Gantt timeline, synced video player, dark SSE live-log console
- 🗄️ **Built-in DB viewer** — browse the shared corpus.db, run SQL, download snapshots
- 🌏 **Trilingual UI** — 中文 / English / 日本語, preference persisted in localStorage

## 💭 Development Philosophy

Not a single line of this codebase was typed out by hand — it is a **100% Vibe Coding** product, iterated by Claude Code under human requirement-setting, acceptance feedback, and course correction. The process itself is structured: requirements become PRDs, PRDs are split into independently grabbable issues (see [`.scratch/`](.scratch/)), and each issue is implemented through a TDD red–green loop. That's where the 322 tests came from.

Honestly: `main_outline.py` is 160k characters. If someone asked me to read it line by line, I'd rather start a third project. But every behavior is pinned by a test — which is the only reason Vibe Coding scales this far.

## 🏗️ Architecture

```
CorpusForge (Function A)                OutlineForge (Function B)
┌─────────────────────┐    corpus.db    ┌──────────────────────────────────┐
│ video → ASR → paras │ ──────────────▶ │  corpus_paragraphs (read-only)    │
└─────────────────────┘  (shared SQLite)└──────────────┬───────────────────┘
                                                       │
                     ┌─────────────────────────────────┼─────────────────┐
                     ▼                                 ▼                 ▼
        ┌─ Two-round LLM ─────────┐      ┌─ CKG extraction ────┐   ┌─ Lesson gen ────┐
        │ R1: transcript → topics │      │ decomposition edges │   │ profile params  │
        │ R2: topic → subtree     │      │ + grounded relations│   │ + new material  │
        └──────────┬──────────────┘      │ + intro positions   │   │ → styled units  │
                   ▼                     └──────────┬──────────┘   └─────────────────┘
        knowledge tree (course_topics)              ▼
                   │                       CK style profile cards
                   ▼                      (video / course / teacher)
        frontend: Gantt timeline + ECharts mind-map + SSE console
```

## 🚀 Quick Start

| Prerequisite | Notes |
|---|---|
| Python 3.10+ | dependencies in `requirements.txt` |
| [Ollama](https://ollama.com/) | running locally, default model `qwen2.5:14b-instruct` |
| `corpus.db` | produced by CorpusForge, expected at `../00-data/corpus.db` |

```bash
pip install -r requirements.txt
python setup.py    # environment check + auto-fix
python start.py    # stop stale process → launch (port 8001) → open browser
python stop.py     # stop the service
```

Typical workflow: pick a transcribed video → **Analyze** (watch progress in the SSE console) → review timeline + mind-map → edit topics/subtrees if needed → extract the CKG → inspect profile cards.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3 · FastAPI · uvicorn (port 8001) · threading + SSE |
| Frontend | single-page HTML · Tailwind CSS (custom theme) · ECharts 5.5 · vanilla JS |
| LLM | Ollama `/api/generate` · default `qwen2.5:14b-instruct` · prompts editable in-app |
| Storage | SQLite (shares `corpus.db` with Function A) |
| Testing | pytest · 322 tests |

## 📡 API Endpoints

| Group | Endpoints | Purpose |
|---|---|---|
| Pages | `GET /` · `GET /db-viewer` | workbench / database viewer |
| Videos | `GET /api/outline/videos` · `…/video/{id}/paragraphs` · `…/video/{id}/file` | listing, paragraphs, file streaming |
| Analysis | `POST /api/outline/analyze/{video_id}` · `…/regenerate/{video_id}` · `…/stop/{video_id}` | run / redo / abort the two-round pipeline |
| Topics | `GET /api/outline/topics/{video_id}` · `PUT …/topics/{topic_id}` | read / edit topics and subtrees |
| CKG | `POST·GET·PUT·DELETE /api/outline/ckg/{video_id}` · `GET …/ckg` · `GET·PUT …/ckg/prompts` | extraction, CRUD, prompt config |
| Profiles | `GET …/ckg/profile` · `…/video/{id}/ck-profile` · `…/teachers/{id}/ck-profile` | corpus / video / teacher scope |
| Lesson gen | `POST …/lesson-gen(/analyze·/generate-units·/extract-file)` · `…/lesson-plans` CRUD | styled lesson generation & management |
| Config | `GET·PUT /api/outline/config` · `GET …/config-defaults` · `…/ollama/models` | model, temperature, prompts |
| Misc | `GET /api/stream/logs/outline` · `GET …/db` · `POST …/db-table/_sql` | SSE log stream, DB download, raw SQL |

## 📁 Project Structure

```
02-outline/
├── main_outline.py           # FastAPI app: routes + two-round pipeline + CKG + profiles + lesson gen
├── database_outline.py       # SQLite schema / migrations / config table / built-in prompts
├── outline.html              # single-page frontend workbench
├── db-viewer-02outline.html  # database viewer
├── setup.py / start.py / stop.py   # env check / one-command start & stop
├── conftest.py               # pytest fixtures
├── test/                     # 322 tests
└── .scratch/                 # issue tracker (development history, as-is)
```

## ⚙️ Configuration

Stored in the shared database's `config` table, editable live from the in-app settings panel:

| Key | Default | Description |
|---|---|---|
| `ob_llm_model` | `qwen2.5:14b-instruct` | Ollama model name |
| `ob_llm_temperature` | `0.0` | sampling temperature |
| `ob_llm_num_ctx` | `8192` | context window (Ollama defaults to ~2048 and **silently truncates**, hence explicit) |
| `ob_prompt_round1` | built-in | Round 1 topic-segmentation prompt ("curriculum designer" persona) |
| `ob_prompt_round2` | built-in | Round 2 knowledge-subtree prompt |
| `ck_prompt_concepts` | built-in | CKG concept-extraction prompt |
| `ck_prompt_relations` | built-in | CKG grounded-relations prompt |

## 🧪 Testing

```bash
python -m pytest test/ -q
```

322 tests covering the two-round pipeline, CKG extraction, profile aggregation, lesson generation, and the teacher attribution layer (`test/test_outline.py` end-to-end mainline + `test/test_20_teachers.py` attribution). Tests read real seed data from the shared `corpus.db`.

## 📚 Related Docs

- [📝 CorpusForge](https://github.com/Shinonome-Laboratory/CorpusForge) — Function A: the upstream video → ASR → paragraph pipeline
- [`.scratch/`](.scratch/) — per-feature issue breakdowns and development history

## 🙏 Acknowledgments

Developed with [Claude Code](https://claude.com/claude-code); thanks to [Ollama](https://ollama.com/), [Apache ECharts](https://echarts.apache.org/), and [FastAPI](https://fastapi.tiangolo.com/) for making local-first classroom analysis possible.

</details>

<details><summary>🇯🇵 日本語</summary>

**OutlineForge** は「All for Style」授業分析システムの **Function B——授業内容の構造分析**です。上流の [CorpusForge](https://github.com/Shinonome-Laboratory/CorpusForge)（Function A）が生成した授業の文字起こしコーパスを読み込み、ローカル LLM で一回の授業の「台本」を階層的な知識構造へ分解し、**教師がどのように内容を組み立てるか**というスタイル特徴を捉えます。

「舞台劇モデル」では、授業は二本の時系列——**台本**（教育内容の展開）と**演技**（ミクロな教育行動）——に分解されます。本プロジェクトは台本の次元を担当します。

## ✨ 主な機能

- 🔪 **2 ラウンド LLM 分析** — 第 1 ラウンドで全文を意味的境界でトピックに分割（`last_para` 方式で重複ゼロ）、第 2 ラウンドでトピックごとに知識サブツリーを生成し、授業全体の知識ツリーへ組み立て
- 🕸️ **授業知識グラフ（CKG）抽出** — 「タイトル → 概念」の分解骨格に、教師が授業中に実際に明言した横断的関連と各概念の導入位置を重ねる——学問の客観構造ではなく「この先生の教え方」を写し取る
- 🃏 **CK スタイル・プロファイルカード** — CKG から内容組織スタイルのパラメータを算出、動画 / コース / 教師の 3 スコープで集約
- 📝 **教案生成** — プロファイルを逆向きに使い、新しい教材を対象教師の組織スタイルで教学ユニットへ変換
- 🖥️ **インタラクティブなワークベンチ** — ECharts ツリー型マインドマップ、トピック分布ガントタイムライン、動画プレイヤー連動、ダーク SSE ログコンソール
- 🗄️ **内蔵 DB ビューア** — 共有 corpus.db の閲覧・SQL 実行・スナップショットのダウンロード
- 🌏 **三言語 UI** — 中文 / English / 日本語

## 💭 開発哲学

このプロジェクトのコードは一行たりとも手で打たれていません——**100% Vibe Coding** の産物であり、人間の要件定義・受け入れフィードバック・軌道修正のもとで Claude Code が反復開発しました。プロセス自体も構造化されています：要件は PRD に落とし、独立して着手できる issue に分割し（[`.scratch/`](.scratch/) 参照）、TDD の赤緑ループで実装する。322 個のテストはその積み重ねです。

正直なところ、16 万文字の `main_outline.py` を一行ずつ読めと言われたら、**目が潰れる**自信があります。しかし全ての挙動はテストで釘付けにされている——それが Vibe Coding をここまで運べた唯一の理由です。

## 🏗️ アーキテクチャ

```
CorpusForge (Function A)                OutlineForge (Function B)
┌─────────────────────┐    corpus.db    ┌──────────────────────────────────┐
│ 動画 → ASR → 段落化  │ ──────────────▶ │  corpus_paragraphs (読み取り専用)   │
└─────────────────────┘   (共有 SQLite)  └──────────────┬───────────────────┘
                                                       │
                     ┌─────────────────────────────────┼─────────────────┐
                     ▼                                 ▼                 ▼
        ┌─ 2 ラウンド LLM ─────────┐     ┌─ CKG 抽出 ──────────┐   ┌─ 教案生成 ──────┐
        │ R1: 全文 → トピック分割   │     │ 分解骨格 (タイトル→概念)│   │ プロファイル参数 │
        │ R2: トピック → サブツリー │     │ + 横断的関連          │   │ + 新しい教材     │
        └──────────┬──────────────┘     │ + 導入位置            │   │ → 様式化ユニット │
                   ▼                    └──────────┬───────────┘   └────────────────┘
        知識ツリー (course_topics)                  ▼
                   │                     CK スタイル・プロファイル
                   ▼                     (動画 / コース / 教師)
        フロント: ガントタイムライン + ECharts マインドマップ + SSE コンソール
```

## 🚀 クイックスタート

| 前提条件 | 備考 |
|---|---|
| Python 3.10+ | 依存関係は `requirements.txt` |
| [Ollama](https://ollama.com/) | ローカル起動、既定モデル `qwen2.5:14b-instruct` |
| `corpus.db` | CorpusForge が生成、`../00-data/corpus.db` に配置 |

```bash
pip install -r requirements.txt
python setup.py    # 環境チェック + 自動修復
python start.py    # 旧プロセス停止 → 起動 (port 8001) → ブラウザ自動オープン
python stop.py     # サービス停止
```

典型的なワークフロー：文字起こし済み動画を選択 → **分析実行**（SSE コンソールで進捗確認）→ タイムライン + マインドマップでレビュー → 必要ならトピック/サブツリーを編集 → CKG 抽出 → プロファイルカードを確認。

## 🛠️ 技術スタック

| レイヤ | 技術 |
|---|---|
| バックエンド | Python 3 · FastAPI · uvicorn (port 8001) · threading + SSE |
| フロントエンド | シングルページ HTML · Tailwind CSS · ECharts 5.5 · vanilla JS |
| LLM | Ollama `/api/generate` · 既定 `qwen2.5:14b-instruct` · プロンプトはアプリ内編集可 |
| ストレージ | SQLite（Function A と `corpus.db` を共有） |
| テスト | pytest · 322 テスト |

## 📡 API エンドポイント

| グループ | エンドポイント | 用途 |
|---|---|---|
| ページ | `GET /` · `GET /db-viewer` | ワークベンチ / DB ビューア |
| 動画 | `GET /api/outline/videos` · `…/video/{id}/paragraphs` · `…/video/{id}/file` | 一覧、段落、ファイル配信 |
| 分析 | `POST /api/outline/analyze/{video_id}` · `…/regenerate/{video_id}` · `…/stop/{video_id}` | 実行 / 再実行 / 中止 |
| トピック | `GET /api/outline/topics/{video_id}` · `PUT …/topics/{topic_id}` | 読み取り / 編集 |
| CKG | `POST·GET·PUT·DELETE /api/outline/ckg/{video_id}` · `GET …/ckg` · `GET·PUT …/ckg/prompts` | 抽出、CRUD、プロンプト設定 |
| プロファイル | `GET …/ckg/profile` · `…/video/{id}/ck-profile` · `…/teachers/{id}/ck-profile` | 全体 / 動画 / 教師スコープ |
| 教案 | `POST …/lesson-gen(/analyze·/generate-units·/extract-file)` · `…/lesson-plans` CRUD | 様式化教案の生成と管理 |
| 設定 | `GET·PUT /api/outline/config` · `GET …/config-defaults` · `…/ollama/models` | モデル、温度、プロンプト |
| その他 | `GET /api/stream/logs/outline` · `GET …/db` · `POST …/db-table/_sql` | SSE ログ、DB ダウンロード、SQL 実行 |

## 📁 プロジェクト構造

```
02-outline/
├── main_outline.py           # FastAPI アプリ：ルート + 2ラウンド分析 + CKG + プロファイル + 教案生成
├── database_outline.py       # SQLite スキーマ / マイグレーション / 設定テーブル / 内蔵プロンプト
├── outline.html              # シングルページのフロントエンド
├── db-viewer-02outline.html  # DB ビューア
├── setup.py / start.py / stop.py   # 環境チェック / ワンコマンド起動・停止
├── conftest.py               # pytest フィクスチャ
├── test/                     # 322 テスト
└── .scratch/                 # issue トラッカー（開発の記録そのまま）
```

## ⚙️ 設定項目

共有データベースの `config` テーブルに保存され、アプリ内設定パネルから編集できます：

| キー | 既定値 | 説明 |
|---|---|---|
| `ob_llm_model` | `qwen2.5:14b-instruct` | Ollama モデル名 |
| `ob_llm_temperature` | `0.0` | サンプリング温度 |
| `ob_llm_num_ctx` | `8192` | コンテキスト窓（Ollama の既定 ~2048 は**黙って切り詰める**ため明示） |
| `ob_prompt_round1` | 内蔵 | 第 1 ラウンド トピック分割プロンプト |
| `ob_prompt_round2` | 内蔵 | 第 2 ラウンド 知識サブツリープロンプト |
| `ck_prompt_concepts` | 内蔵 | CKG 概念抽出プロンプト |
| `ck_prompt_relations` | 内蔵 | CKG 関連抽出プロンプト |

## 🧪 テスト

```bash
python -m pytest test/ -q
```

322 テストが 2 ラウンド分析パイプライン、CKG 抽出、プロファイル集約、教案生成、教師帰属レイヤをカバーします（`test/test_outline.py` エンドツーエンド + `test/test_20_teachers.py` 帰属レイヤ）。

## 📚 関連ドキュメント

- [📝 CorpusForge](https://github.com/Shinonome-Laboratory/CorpusForge) — Function A：動画 → ASR → 段落化の上流パイプライン
- [`.scratch/`](.scratch/) — 機能ごとの issue 分解と開発記録

## 🙏 謝辞

[Claude Code](https://claude.com/claude-code) による開発。[Ollama](https://ollama.com/)、[Apache ECharts](https://echarts.apache.org/)、[FastAPI](https://fastapi.tiangolo.com/) に感謝します。

</details>
