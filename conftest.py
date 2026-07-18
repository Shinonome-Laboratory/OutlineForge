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


def _checkpoint(db: Path) -> None:
    """Fold any -wal contents into the main file before copying."""
    try:
        c = sqlite3.connect(str(db))
        c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        c.close()
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def _isolate_test_db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("ckg-db") / "corpus_test_copy.db"
    if _REAL_DB.exists():
        _checkpoint(_REAL_DB)
        shutil.copy2(_REAL_DB, tmp)

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
