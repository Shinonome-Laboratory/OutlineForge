"""Database layer for outline (Function B).

Schema DDL（course_topics / course_ckg / lesson_plans——02 独家写的三张表）、
ob_/ck_ 配置默认值与 prompt 常量、连接与初始化函数。从 main_outline.py 拆出
（债#2），单文件职责收敛；main_outline 通过 re-export 保持既有导入路径可用。

共享库中 teachers / courses / videos / corpus_paragraphs / asr_sentences 归
01-corpus 独家写，此处不建不改（HANDOFF01-teachers §2）。
"""

import sqlite3

# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

_OB_PROMPT_ROUND1 = (
    "You are an expert curriculum designer and text structure analyst. "
    "Segment the numbered lecture transcript below into pedagogical topics.\n"
    "\n"
    "Your segmentation should behave like **condensed milk poured on a "
    "flat surface** — spreading naturally, maintaining consistent "
    "thickness, and staying highly cohesive without breaking apart.\n"
    "\n"
    "WORKFLOW:\n"
    "1. Count the total number of paragraphs in the transcript. This is "
    "your `total_paragraphs`.\n"
    "2. Scan the text. Identify the main pedagogical topics — each a "
    "conceptually complete unit. Write a concise title and a 1-sentence "
    "concept summary for each topic (this helps verify even density).\n"
    "3. For each topic (except the last), determine the paragraph index "
    "where it ENDS. The next topic begins at end+1.\n"
    "\n"
    "PRINCIPLES:\n"
    "• Consistent Density: Cognitive load of each topic must be roughly "
    "equal. Don't cram heavy concepts together; don't isolate trivial "
    "transitions as standalone topics.\n"
    "• Conceptual Completeness: Only cut after a concept is fully "
    "resolved (introduction → explanation → examples → wrap-up).\n"
    "• Natural Boundaries: Cut at semantic shifts or breathing pauses. "
    "If a paragraph bridges two ideas, assign it to the heavier side.\n"
    "\n"
    "CHAIN CALCULATION (Zero overlap, zero gap):\n"
    "• Topic 1 starts at paragraph 1.\n"
    "• Each subsequent topic starts at (previous topic's end + 1).\n"
    "• The final topic MUST end at total_paragraphs.\n"
    "• breaks array: the end paragraph index for each topic except the "
    "last. N topics → exactly N−1 breaks.\n"
    "\n"
    "OUTPUT — strict JSON only. No markdown fences, no extra text:\n"
    "{\n"
    '  "course_name": "Concise lecture title",\n'
    '  "total_paragraphs": <integer>,\n'
    '  "topics": ["Topic 1 Title", "Topic 2 Title", "Topic 3 Title"],\n'
    '  "breaks": [end_para_of_topic1, end_para_of_topic2]\n'
    "}\n"
    "\n"
    "FATAL RED LINES:\n"
    "• breaks[i] < breaks[i+1] (strictly increasing).\n"
    "• breaks[-1] < total_paragraphs (last break must leave room for final topic).\n"
    "• len(breaks) == len(topics) − 1.\n"
    "• All values are integers.\n"
    "\n"
    "Full transcript below:"
)

_OB_PROMPT_ROUND2 = (
    "You are a subject knowledge structure analyst. Below is the teaching "
    'content for the topic "{topic_name}" from a lecture transcript.\n'
    "\n"
    "Analyze the knowledge structure within this text and generate a knowledge "
    "subtree for this topic. Let the depth be determined by the actual content "
    "structure — shallow for simple content, deep for complex content.\n"
    "\n"
    "Output strictly in the following JSON format. Do not output any other text:\n"
    "\n"
    "{\n"
    '  "topic": "{topic_name}",\n'
    '  "subtree": {\n'
    '    "children": [\n'
    '      { "name": "sub-topic name", "children": [...] }\n'
    "    ]\n"
    "  }\n"
    "}\n"
    "\n"
    "If the topic content is too simple to subdivide further, children can be "
    "an empty array.\n"
    "\n"
    "Topic text below:"
)

OB_CONFIG_DEFAULTS = [
    ("ob_llm_model", "qwen2.5:14b-instruct"),
    ("ob_llm_temperature", "0.0"),
    # Ollama context-window size (tokens). Ollama defaults to ~2048 and SILENTLY
    # truncates longer prompts; this is user-tunable from the settings panel.
    ("ob_llm_num_ctx", "8192"),
    ("ob_prompt_round1", _OB_PROMPT_ROUND1),
    ("ob_prompt_round2", _OB_PROMPT_ROUND2),
]

# ---------------------------------------------------------------------------
# CKG concept extraction prompt (Step 1) — see ADR 0002 / CONTEXT.md「CK 维度」
# Stored in config under key ``ck_prompt_concepts`` (front-end editable).
# ---------------------------------------------------------------------------

_CK_PROMPT_CONCEPTS = (
    "You are a curriculum analyst reconstructing how an instructor DECOMPOSES a lecture's title into teaching concepts.\n"
    "\n"
    "Read the transcript and break the lecture's TITLE down into the teaching concepts the instructor actually carves out, as a DECOMPOSITION TREE: each concept is a piece the instructor splits a higher concept (or the lecture title) into. This captures HOW THIS INSTRUCTOR organizes the content — grounded entirely in THIS transcript, not the subject's objective structure.\n"
    "\n"
    "A TEACHING CONCEPT is a nameable, definable knowledge point the instructor actually teaches — something that could be a bullet on the syllabus, or that the instructor effectively says \"now let's learn X\" about.\n"
    "\n"
    "INCLUDE: named methods, models, principles, terms the instructor explains or builds on (e.g. \"Gradient Descent\", \"Learning Rate\", \"Cost Function\").\n"
    "EXCLUDE:\n"
    "- Tools/sub-steps used only to explain something else, not taught as their own topic (e.g. \"partial derivative\" mentioned only to derive gradient descent).\n"
    "- Generic words, examples, anecdotes, course logistics, greetings.\n"
    "- Anything NOT covered in this transcript. Do NOT add knowledge from outside the transcript — extract only what is actually taught here.\n"
    "\n"
    "GRANULARITY: syllabus-level — each concept is a nameable, definable knowledge point as described above. Extract AS MANY as the lecture genuinely teaches at this granularity; let the COUNT follow the actual content (a rich lecture yields many, a light one few). Do NOT pad, drop, split, or merge concepts just to hit any target number. Keep the granularity (what counts as a concept) consistent — never the count.\n"
    "\n"
    "For each concept output:\n"
    "- NAME: a short name.\n"
    "- DEFINITION: a ONE-SENTENCE definition grounded in how the transcript uses it.\n"
    "- FIRST_PARA: the integer index of the [段落 N] marker where the concept is first substantively taught.\n"
    "- PARENT: the NAME of the higher concept this one is carved out of (the concept the instructor was decomposing when this came up). If it is a top-level piece carved directly from the lecture title, set PARENT to the lecture TITLE string. PARENT must be EXACTLY another concept's NAME or the TITLE — never invent a new label here.\n"
    "\n"
    "Also output TITLE: the lecture's title / overall topic, used as the root of the decomposition tree.\n"
    "\n"
    "OUTPUT — strict JSON only. No markdown fences, no extra text:\n"
    "{\n"
    '  "title": "...",\n'
    '  "concepts": [ {"name": "...", "definition": "...", "first_para": <int>, "parent": "..."} ]\n'
    "}\n"
    "\n"
    "Full transcript below:"
)

# ---------------------------------------------------------------------------
# CKG prerequisite-edge extraction prompt (Step 2) — see ADR 0002 / CONTEXT.md
# Stored in config under key ``ck_prompt_edges`` (front-end editable).
# ---------------------------------------------------------------------------

_CK_PROMPT_EDGES = (
    "You are a learning-dependency analyst. Below is a list of teaching concepts (with definitions) from a single lecture.\n"
    "\n"
    "Identify PREREQUISITE relations. An edge A -> B means \"a learner must understand A before they can understand B.\" This is learning dependency / ordering — NOT containment or categorization.\n"
    "\n"
    "CRITICAL — what is and isn't a prerequisite edge:\n"
    "  ✓  \"Derivative\" -> \"Gradient Descent\"   (must grasp derivatives first)\n"
    "  ✗  \"Classification\" / \"Regression\" are both kinds of \"Supervised Learning\" → category relation, NOT prerequisite. No edge.\n"
    "  ✗  \"Classification\" vs \"Regression\" → siblings, either can be learned first. No edge.\n"
    "\n"
    "RULES:\n"
    "- Use ONLY the concepts in the list; use their exact names; invent nothing.\n"
    "- Edge only when the dependency is genuinely real. A few high-confidence edges beat many speculative ones — not every concept needs an edge.\n"
    "- Direction: prerequisite (earlier) -> dependent (later).\n"
    "- No cycles: if A -> B (directly or transitively), do not also add B -> A.\n"
    "\n"
    "OUTPUT — strict JSON only. No markdown fences, no extra text:\n"
    "{\n"
    '  "edges": [ {"from": "...", "to": "..."} ]\n'
    "}\n"
    "\n"
    "Concept list:"
)

# ---------------------------------------------------------------------------
# CKG grounded cross-relation prompt (Step 2, 讲述关联) — see ADR 0003.
# Stored in config under key ``ck_prompt_relations`` (front-end editable). The
# relation TYPE is FREE-LABELLED by the LLM (emergent, not a fixed taxonomy);
# builds-on / explains-via / motivates are only example anchors.
# ---------------------------------------------------------------------------

_CK_PROMPT_RELATIONS = (
    "You are analyzing how an instructor CONNECTS concepts ACROSS different branches of a lecture, beyond the parent→child decomposition.\n"
    "\n"
    "Below is the list of teaching concepts (with definitions) the instructor decomposed the lecture into, followed by the full transcript.\n"
    "\n"
    "Identify GROUNDED CROSS-RELATIONS: directed relations the instructor EXPLICITLY establishes between two concepts while teaching — connections the instructor actually states or demonstrates in THIS transcript, that are NOT already captured by the decomposition (parent→child) structure.\n"
    "\n"
    "For each relation output:\n"
    "- FROM / TO: the exact NAMES of two concepts from the list (the relation goes FROM → TO).\n"
    "- TYPE: a short label for HOW the instructor connects them — describe the relation in YOUR OWN WORDS (e.g. \"builds-on\", \"explains-via\", \"motivates\", \"contrasts-with\"). Use whatever label best fits; you are NOT limited to these examples.\n"
    "- EVIDENCE: a brief quote or the [段落 N] index grounding this relation in the transcript.\n"
    "\n"
    "RULES:\n"
    "- Use ONLY concept names from the list; use their exact names; invent no new concepts.\n"
    "- Only relations the instructor genuinely establishes in the transcript — a few well-grounded relations beat many speculative ones; not every concept needs one.\n"
    "- These are CROSS-branch narrative links, NOT the decomposition hierarchy (do not just restate parent→child).\n"
    "\n"
    "OUTPUT — strict JSON only. No markdown fences, no extra text:\n"
    "{\n"
    '  "relations": [ {"from": "...", "to": "...", "type": "...", "evidence": "..."} ]\n'
    "}\n"
    "\n"
    "Concept list:"
)

# ck_prompt_edges (prerequisite-edge prompt) is RETIRED for CKG extraction —
# the graph backbone is now the title→concept DECOMPOSITION tree (ADR 0003).
# _CK_PROMPT_EDGES / parse_edges_response are kept only for lesson generation.
CK_CONFIG_DEFAULTS = [
    ("ck_prompt_concepts", _CK_PROMPT_CONCEPTS),
    ("ck_prompt_relations", _CK_PROMPT_RELATIONS),
]

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

COURSE_TOPICS_DDL = """
CREATE TABLE IF NOT EXISTS course_topics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id          INTEGER NOT NULL,
    start_para_index  INTEGER NOT NULL,
    end_para_index    INTEGER NOT NULL,
    start_time        REAL    NOT NULL,
    end_time          REAL    NOT NULL,
    topic_name        TEXT    NOT NULL,
    subtree_json      TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);
"""

# Course Knowledge Graph (CKG) — one row per video.
# graph_json (schema_version 2) holds {"schema_version", "title", "concepts"
# (each with parent/first_para), "decomposition_edges", "relations"}. The
# decomposition backbone is the title→concept tree (issue 01); grounded
# cross-relations (讲述关联) fill "relations" in issue 02.
COURSE_CKG_DDL = """
CREATE TABLE IF NOT EXISTS course_ckg (
    video_id    INTEGER PRIMARY KEY,
    graph_json  TEXT,
    model       TEXT,
    created_at  TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(id)
);
"""

# Saved lesson plans (教案). payload_json holds the full generated result
# ({title, units:[plan,...]}) so it can be reloaded into the outline + graphs.
LESSON_PLANS_DDL = """
CREATE TABLE IF NOT EXISTS lesson_plans (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    created_at   TEXT,
    payload_json TEXT
);
"""

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_db(db_path: str) -> sqlite3.Connection:
    """Return a read-write connection with FK and WAL pragmas set."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(db_path: str) -> None:
    """Create course_topics table (if not exists) and seed ob_ config defaults."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(COURSE_TOPICS_DDL)
    conn.executescript(COURSE_CKG_DDL)
    conn.executescript(LESSON_PLANS_DDL)

    # Idempotent migration: CREATE TABLE IF NOT EXISTS never adds columns to an
    # already-existing course_ckg, so add the topology / delivery-direction
    # columns one by one only when missing (issue 03).
    _CKG_TOPO_COLUMNS = [
        ("depth", "INTEGER"),            # = 拆解深度 (decomposition-tree height)
        ("branch_factor", "REAL"),       # = 拆解宽度 (mean children of non-leaf)
        ("convergence_count", "INTEGER"),  # in-degree>1 over decomposition+relations
        ("relation_density", "REAL"),    # = 讲述关联边数 / 概念数 (issue 03)
        ("density", "REAL"),             # RETIRED (issue 03): no longer populated
        ("avg_path_length", "REAL"),     # RETIRED (issue 03): no longer populated
        ("clustering", "REAL"),          # RETIRED (issue 03): no longer populated
        ("bottomup_ratio", "REAL"),      # 辅助信号 (delivery direction)
    ]
    existing_cols = {
        row[1] for row in conn.execute("PRAGMA table_info(course_ckg)")
    }
    for col_name, col_type in _CKG_TOPO_COLUMNS:
        if col_name not in existing_cols:
            conn.execute(
                f"ALTER TABLE course_ckg ADD COLUMN {col_name} {col_type}"
            )

    conn.executemany(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        OB_CONFIG_DEFAULTS,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
        CK_CONFIG_DEFAULTS,
    )

    # Migrate old round-1 prompts to the latest version
    _OLD_MARKERS = [
        '"start_para"',                           # v1: range-based prompt
        'classroom instruction content analyst',  # v2: breakpoint prompt
        '"last_para"',                            # v3: curriculum designer prompt
    ]
    row = conn.execute(
        "SELECT value FROM config WHERE key = 'ob_prompt_round1'"
    ).fetchone()
    if row and any(m in (row[0] or "") for m in _OLD_MARKERS):
        conn.execute(
            "UPDATE config SET value = ? WHERE key = 'ob_prompt_round1'",
            (_OB_PROMPT_ROUND1,),
        )
        conn.execute("COMMIT")

    # Migrate any pre-decomposition ck_prompt_concepts (concept-list only, no
    # PARENT field) to the latest DECOMPOSITION-tree prompt (ADR 0003). The new
    # prompt is detected by the presence of the "parent" output field.
    ck_row = conn.execute(
        "SELECT value FROM config WHERE key = 'ck_prompt_concepts'"
    ).fetchone()
    if ck_row and '"parent"' not in (ck_row[0] or ""):
        conn.execute(
            "UPDATE config SET value = ? WHERE key = 'ck_prompt_concepts'",
            (_CK_PROMPT_CONCEPTS,),
        )
        conn.execute("COMMIT")

    conn.commit()
    conn.close()


