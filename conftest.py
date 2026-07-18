"""Pytest session setup: isolate the test DB from the production corpus.db.

The test suite mutates ``course_ckg`` destructively (one test does
``DROP TABLE course_ckg``; many call ``_cleanup_ckg`` which ``DELETE``s rows).
Historically ``DB_PATH`` pointed straight at the real, shared
``00-data/corpus.db`` — so running the tests wiped real analysis results.

This session-scoped, autouse fixture copies the production DB to a temp file
once per run and repoints BOTH the app module (``main_outline.DB_PATH``) and the
test module (``test_outline.DB_PATH``) at the copy. Tests therefore see the real
seed data (videos / paragraphs) but can never mutate the production file.
"""

import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

_REAL_DB = Path(r"d:\Project\All for Style\00-data\corpus.db")

# 测试黄金数据：test_outline.py 的断言写死了旧语料时代的视频（CCNA 课，
# id 25/29/31，29/343/218 段，25 号首段 end_time=12.56）。共享库后来整体
# 换成了吴恩达 113 课（id 132+），这些视频不复存在——在隔离副本里按原断言
# 播种同构 fixture，让测试与生产语料内容解耦。id < 132 不会与真实数据冲突。
_FIXTURE_VIDEOS = [
    # (id, name, paragraph_count)
    (25, "ccna-network lesson (test fixture)", 29),
    (29, "WOLF-LAB CCNA-day2-6-UDP (test fixture)", 343),
    (31, "WOLF-LAB CCNA-day6-18-VLAN (test fixture)", 218),
]


def _checkpoint(db: Path) -> None:
    """Fold any -wal contents into the main file before copying."""
    try:
        c = sqlite3.connect(str(db))
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        c.close()
    except Exception:
        pass


def _seed_fixture_videos(db: Path) -> None:
    conn = sqlite3.connect(str(db))
    try:
        for vid, name, para_count in _FIXTURE_VIDEOS:
            exists = conn.execute(
                "SELECT 1 FROM videos WHERE id = ?", (vid,)
            ).fetchone()
            if exists:
                continue
            conn.execute(
                "INSERT INTO videos (id, name, path, duration, file_size, "
                "status, uploaded_at, course_id) "
                "VALUES (?, ?, ?, ?, 0, 'done', '2026-01-01T00:00:00+00:00', "
                "NULL)",
                (vid, name, f"test-fixtures/{vid}.mp4", para_count * 10.0),
            )
            rows = []
            for i in range(1, para_count + 1):
                # 25 号视频首段时间戳被 test_get_paragraphs_first_item_matches_db
                # 精确断言为 (0.0, 12.56)；其余段任意递增即可。
                if i == 1:
                    start, end = 0.0, 12.56
                else:
                    start = 12.56 + (i - 2) * 10.0
                    end = start + 10.0
                rows.append(
                    (vid, i, start, end,
                     f"Test fixture paragraph {i} for video {vid}.")
                )
            conn.executemany(
                "INSERT INTO corpus_paragraphs "
                "(video_id, paragraph_index, start_time, end_time, text) "
                "VALUES (?, ?, ?, ?, ?)",
                rows,
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def _isolate_test_db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ckg-db") / "corpus_test_copy.db"
    if _REAL_DB.exists():
        _checkpoint(_REAL_DB)
        shutil.copy2(_REAL_DB, tmp)
        _seed_fixture_videos(tmp)

    # Repoint the app module.
    import main_outline
    main_outline.DB_PATH = tmp

    # Repoint the test module's own DB_PATH global (functions read it at call
    # time, so reassigning the module attribute is enough).
    for name, mod in list(sys.modules.items()):
        if name.endswith("test_outline") and hasattr(mod, "DB_PATH"):
            mod.DB_PATH = tmp

    yield
    # Temp file is cleaned up by pytest's tmp_path_factory.
