"""Tests for the teacher-profile feature (HANDOFF01-teachers P1–P3).

Covers: video-list attribution fields, the read-only teacher endpoints,
teacher-scoped profile aggregation, and the config-defaults single source
of truth. Runs against the isolated DB copy provided by conftest.py — the
production corpus.db is never touched (writes below go to the temp copy
only; app code itself stays read-only on teachers/courses/videos).
"""

import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def client():
    from main_outline import app
    from fastapi.testclient import TestClient

    with TestClient(app) as tc:
        yield tc


def _db():
    """Connection to the isolated test DB (repointed by conftest)."""
    import main_outline
    conn = sqlite3.connect(str(main_outline.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# P1 — video list carries attribution fields
# ---------------------------------------------------------------------------

def test_videos_include_attribution_fields(client):
    resp = client.get("/api/outline/videos")
    assert resp.status_code == 200
    videos = resp.json()
    assert videos, "seed DB should contain videos"
    for key in ("course_id", "course_name", "teacher_id", "teacher_name"):
        assert key in videos[0], f"missing attribution field {key}"


def test_videos_unassigned_have_null_attribution(client):
    """A video with course_id NULL reports all four attribution fields null."""
    conn = _db()
    row = conn.execute(
        "SELECT id, course_id FROM videos WHERE status='done' LIMIT 1"
    ).fetchone()
    assert row is not None
    vid = row["id"]
    original = row["course_id"]
    try:
        conn.execute("UPDATE videos SET course_id = NULL WHERE id = ?", (vid,))
        conn.commit()
        videos = client.get("/api/outline/videos").json()
        target = next(v for v in videos if v["id"] == vid)
        assert target["course_id"] is None
        assert target["course_name"] is None
        assert target["teacher_id"] is None
        assert target["teacher_name"] is None
    finally:
        conn.execute(
            "UPDATE videos SET course_id = ? WHERE id = ?", (original, vid)
        )
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# P2 — read-only teacher endpoints
# ---------------------------------------------------------------------------

def test_teachers_list_shape(client):
    resp = client.get("/api/outline/teachers")
    assert resp.status_code == 200
    teachers = resp.json()
    assert isinstance(teachers, list)
    if teachers:
        t = teachers[0]
        for key in ("id", "name", "course_count", "video_count",
                    "para_count", "extracted_count", "total_duration"):
            assert key in t, f"missing {key}"


def test_teacher_ck_profile_shape(client):
    teachers = client.get("/api/outline/teachers").json()
    if not teachers:
        pytest.skip("no teachers in seed DB")
    tid = teachers[0]["id"]
    resp = client.get(f"/api/outline/teachers/{tid}/ck-profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["teacher"]["id"] == tid
    assert isinstance(data["courses"], list)
    if data["courses"]:
        c = data["courses"][0]
        for key in ("id", "name", "video_count", "topic_count",
                    "extracted_count", "avg_depth", "avg_branch_factor",
                    "avg_convergence_count", "avg_relation_density",
                    "avg_bottomup_ratio"):
            assert key in c, f"missing course stat {key}"
    assert "ckg_means" in data
    if data["ckg_means"]:
        for key in ("depth", "branch_factor", "convergence_count",
                    "relation_density", "bottomup_ratio", "n_videos"):
            assert key in data["ckg_means"], f"missing mean {key}"


def test_teacher_ck_profile_404(client):
    resp = client.get("/api/outline/teachers/999999/ck-profile")
    assert resp.status_code == 404


def test_teacher_ck_profile_counts_match_db(client):
    """Course-level topic/extracted counts must equal direct DB counts —
    guards against join fan-out double counting."""
    teachers = client.get("/api/outline/teachers").json()
    if not teachers:
        pytest.skip("no teachers in seed DB")
    tid = teachers[0]["id"]
    data = client.get(f"/api/outline/teachers/{tid}/ck-profile").json()
    conn = _db()
    try:
        for c in data["courses"]:
            expected_topics = conn.execute(
                "SELECT COUNT(*) FROM course_topics ct "
                "JOIN videos v ON v.id = ct.video_id WHERE v.course_id = ?",
                (c["id"],),
            ).fetchone()[0]
            assert c["topic_count"] == expected_topics
            expected_ckg = conn.execute(
                "SELECT COUNT(*) FROM course_ckg k "
                "JOIN videos v ON v.id = k.video_id WHERE v.course_id = ?",
                (c["id"],),
            ).fetchone()[0]
            assert c["extracted_count"] == expected_ckg
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# P3 — teacher-scoped profile
# ---------------------------------------------------------------------------

def test_profile_without_teacher_id_unchanged(client):
    """Default (no param) behaviour: whole-corpus aggregate, original shape."""
    resp = client.get("/api/outline/ckg/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert "lecture_count" in data
    assert "params" in data
    assert "teacher_id" not in data  # additive field only when scoped
    assert "means" not in data       # internal aggregate stays stripped


def test_profile_teacher_scope_matches_whole_corpus_when_single_teacher(client):
    """Regression per HANDOFF §8: while every extracted lecture belongs to one
    teacher, the scoped profile must be numerically identical to the whole-
    corpus profile."""
    conn = _db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT c.teacher_id FROM course_ckg k "
            "JOIN videos v ON v.id = k.video_id "
            "LEFT JOIN courses c ON c.id = v.course_id"
        ).fetchall()
    finally:
        conn.close()
    owners = {r["teacher_id"] for r in rows}
    if len(owners) != 1 or None in owners:
        pytest.skip("extracted lectures span multiple/unassigned teachers")
    tid = owners.pop()

    whole = client.get("/api/outline/ckg/profile").json()
    scoped = client.get(f"/api/outline/ckg/profile?teacher_id={tid}").json()
    assert scoped["teacher_id"] == tid
    assert scoped["lecture_count"] == whole["lecture_count"]
    assert scoped["params"] == whole["params"]
    assert scoped.get("style_label") == whole.get("style_label")


def test_profile_course_scope_matches_teacher_scope_when_single_course(client):
    """Course-level scope (teacher → course hierarchy): while a teacher has
    exactly one course, course scope must equal teacher scope numerically."""
    teachers = client.get("/api/outline/teachers").json()
    if not teachers:
        pytest.skip("no teachers in seed DB")
    tid = teachers[0]["id"]
    courses = client.get(f"/api/outline/teachers/{tid}/ck-profile").json()["courses"]
    if len(courses) != 1:
        pytest.skip("teacher has != 1 course")
    cid = courses[0]["id"]

    by_teacher = client.get(f"/api/outline/ckg/profile?teacher_id={tid}").json()
    by_course = client.get(
        f"/api/outline/ckg/profile?teacher_id={tid}&course_id={cid}"
    ).json()
    assert by_course["course_id"] == cid
    assert by_course["lecture_count"] == by_teacher["lecture_count"]
    assert by_course["params"] == by_teacher["params"]


def test_profile_unknown_course_is_empty(client):
    resp = client.get("/api/outline/ckg/profile?course_id=999999")
    assert resp.status_code == 200
    assert resp.json()["lecture_count"] == 0


def test_profile_unknown_teacher_is_empty(client):
    resp = client.get("/api/outline/ckg/profile?teacher_id=999999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["lecture_count"] == 0


def test_corpus_ckg_rows_carry_attribution(client):
    resp = client.get("/api/outline/ckg")
    assert resp.status_code == 200
    rows = resp.json()
    if not rows:
        pytest.skip("no extracted lectures in seed DB")
    assert "teacher_id" in rows[0]
    assert "course_id" in rows[0]


# ---------------------------------------------------------------------------
# db-viewer config defaults — single source of truth
# ---------------------------------------------------------------------------

def test_config_defaults_endpoint(client):
    import main_outline
    resp = client.get("/api/outline/config-defaults")
    assert resp.status_code == 200
    pairs = resp.json()
    keys = [p[0] for p in pairs]
    expected = [k for k, _ in main_outline.OB_CONFIG_DEFAULTS] + \
               [k for k, _ in main_outline.CK_CONFIG_DEFAULTS]
    assert keys == expected
    # The retired key must NOT resurface (the stale db-viewer copy had it).
    assert "ob_max_topics" not in keys
