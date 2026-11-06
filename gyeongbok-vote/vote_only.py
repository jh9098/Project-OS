"""Emergency, vote-only mode for the 2026-11-06 Gyeongbokgung event.

This module deliberately does NOT call the unavailable Render PostgreSQL for
ordinary voting. It freezes already-published mission scores, accepts ballots
in local SQLite and supports full admin JSON backups and restoration.

Important: Render Free web-service files are ephemeral. Admins should leave
the results page open (it keeps a browser-local backup), download JSON often,
and restore it if a service restart clears the local database.
"""
import hashlib
import hmac
import io
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Response, current_app, g, jsonify, redirect, render_template,
    request, session
)

SCORES = {1: 67.08, 2: 61.25, 3: 58.33, 4: 58.33, 5: 64.17}
# SHA256 fingerprints extracted from the five already-issued team QR images.
# No raw team tokens are stored in source control.
QR_HASHES = {
    1: "260064f8caadc8ccec2d68ceb4c92266455c0290ba0e2af66d081ac84e1f2ede",
    2: "475ba16b58a559d2bc0afdc21426f33ba79d1c1de4980b347f9f328c1da2a62e",
    3: "16024ecbd0e8f1923a10b8128192863f21b2aa2a3735c77b6d4313178d232ab7",
    4: "8cc68aaf1388ec21c5d3c668caeb930b0b4ba33354abdd6a955c11fbccf9a401",
    5: "6223dea83cc0e54ab30181af974c396c7fc32372481abf6c12b896eab5e56ed7",
}
ROOT = Path(os.environ.get("VOTE_ONLY_DB_PATH", "/tmp/gyeongbok_vote_only_20261106.sqlite3"))
DB_LOCK = threading.RLock()
INIT_DONE = False
HEX64 = re.compile(r"^[0-9a-f]{64}$")
TEAM_URL = re.compile(r"^/vote/team/([1-5])/([A-Za-z0-9_-]{24,60})$")
MISSION_URL = re.compile(r"^/mission/([1-5])/([A-Za-z0-9_-]{24,60})$")


def valid_team_qr(team, token):
    if team not in QR_HASHES or not re.fullmatch(r"[A-Za-z0-9_-]{24,60}", token or ""):
        return False
    return hmac.compare_digest(
        hashlib.sha256(token.encode("utf-8")).hexdigest(), QR_HASHES[team])


def _connect():
    global INIT_DONE
    ROOT.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(ROOT), timeout=10, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout=10000")
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=FULL")
    if not INIT_DONE:
        with DB_LOCK:
            connection.execute("""CREATE TABLE IF NOT EXISTS ballots(
                device_hash TEXT PRIMARY KEY,
                voter_team INTEGER NOT NULL,
                photo_team INTEGER NOT NULL,
                video_team INTEGER NOT NULL,
                absentee INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'vote_only',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            connection.execute("""CREATE TABLE IF NOT EXISTS vote_settings(
                id INTEGER PRIMARY KEY, vote_open INTEGER NOT NULL DEFAULT 1,
                reveal INTEGER NOT NULL DEFAULT 0
            )""")
            connection.execute("INSERT OR IGNORE INTO vote_settings(id,vote_open,reveal) VALUES(1,1,0)")
            INIT_DONE = True
    return connection


def _device_hash():
    raw = getattr(g, "voter_device", None)
    if not raw:
        raise ValueError("투표 기기 식별이 필요합니다. 페이지를 새로고침해 주세요.")
    return hashlib.sha256(raw.encode()).hexdigest()


def _summary(c):
    ballots = [dict(x) for x in c.execute(
        "SELECT device_hash,voter_team,photo_team,video_team,absentee,source,created_at FROM ballots ORDER BY created_at,device_hash")]
    counts = {str(t): {
        "photo": sum(x["photo_team"] == t for x in ballots),
        "video": sum(x["video_team"] == t for x in ballots),
        "issued": 0, "used": 0,
    } for t in range(1, 6)}
    return ballots, counts


def get_state():
    key = _device_hash()
    c = _connect()
    try:
        setting = dict(c.execute("SELECT vote_open,reveal FROM vote_settings WHERE id=1").fetchone())
        already = c.execute("SELECT 1 FROM ballots WHERE device_hash=?", (key,)).fetchone() is not None
        result = {
            "status": "ok", "vote_only": True, "automatic_mission_scoring": False,
            "storage": "temporary_sqlite_with_admin_backup",
            "storage_warning": "무료 Render 서버 재시작 시 임시 투표 DB가 초기화될 수 있습니다. 운영진 JSON 백업 필수",
            "database": "독립 투표 임시저장소",
            "admin": bool(session.get("admin")),
            "vote_open": bool(setting["vote_open"]), "reveal": bool(setting["reveal"]),
            "has_voted": already,
            "teams": [{
                "team": t, "photo": True, "video": True,
                "photo_title": f"{t}조 사진 작품", "video_title": f"{t}조 영상 작품",
                "mission_score": SCORES[t],
            } for t in range(1, 6)],
        }
        if result["admin"] or result["reveal"]:
            ballots, counts = _summary(c)
            absentees = sum(bool(x["absentee"]) for x in ballots)
            result["counts"] = counts
            result["voting_summary"] = {
                "total": len(ballots), "absentee": absentees,
                "regular": len(ballots)-absentees, "previous_code_votes": 0,
                "new_votes": len(ballots),
            }
        return jsonify(result)
    finally:
        c.close()


def cast_vote():
    if not request.is_json:
        return jsonify(error="투표 요청 형식이 올바르지 않습니다."), 400
    d = request.get_json(silent=True) or {}
    try:
        photo, video = int(d["photo"]), int(d["video"])
        voter_team = int(d.get("voter_team", 0))
        absentee = d.get("absent") is True
    except (ValueError, TypeError, KeyError):
        return jsonify(error="사진·영상에 각각 1표를 선택해주세요."), 400
    if photo not in SCORES or video not in SCORES:
        return jsonify(error="투표 대상 조를 다시 선택해주세요."), 400
    if absentee:
        if voter_team != 0 or d.get("team_token"):
            return jsonify(error="미참석자 정보가 올바르지 않습니다."), 400
    elif voter_team not in SCORES:
        return jsonify(error="본인 조를 선택해주세요."), 400
    else:
        token = d.get("team_token")
        if token and not valid_team_qr(voter_team, token):
            return jsonify(error="조별 QR 정보가 올바르지 않습니다."), 403
        if voter_team in (photo, video):
            return jsonify(error="자기 조의 작품에는 투표할 수 없습니다."), 400

    key = _device_hash()
    c = _connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        settings = c.execute("SELECT vote_open FROM vote_settings WHERE id=1").fetchone()
        if not settings or not settings["vote_open"]:
            c.rollback()
            return jsonify(error="투표가 마감됐습니다."), 403
        try:
            c.execute("""INSERT INTO ballots
                (device_hash,voter_team,photo_team,video_team,absentee,source)
                VALUES (?,?,?,?,?,?)""", (key,voter_team,photo,video,int(absentee),"vote_only"))
        except sqlite3.IntegrityError:
            c.rollback()
            return jsonify(error="이 브라우저에서는 이미 투표했습니다."), 409
        c.commit()
        return jsonify(ok=True,stored=True,storage="temporary_sqlite",
                       message="투표 접수 완료. 운영진이 백업할 때까지 임시 서버에 저장됩니다.")
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def set_setting():
    if not session.get("admin"):
        return jsonify(error="운영진 로그인이 필요합니다."), 401
    d = request.get_json(silent=True) or {}
    key = d.get("key")
    value = d.get("value")
    if key not in ("vote_open", "reveal") or type(value) is not bool:
        return jsonify(error="설정이 올바르지 않습니다."), 400
    c = _connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        c.execute(f"UPDATE vote_settings SET {key}=? WHERE id=1", (int(value),))
        c.commit()
        return jsonify(ok=True)
    finally:
        c.close()


def backup_json():
    if not session.get("admin"):
        return jsonify(error="운영진 로그인이 필요합니다."), 401
    c = _connect()
    try:
        ballots, _ = _summary(c)
        settings = dict(c.execute("SELECT vote_open,reveal FROM vote_settings WHERE id=1").fetchone())
        payload = {
            "format": "gyeongbok_vote_only_v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mission_scores": SCORES, "settings": settings, "ballots": ballots,
        }
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8-sig")
        response = Response(body, mimetype="application/json")
        response.headers["Cache-Control"] = "no-store"
        if request.args.get("download") == "1":
            response.headers["Content-Disposition"] = 'attachment; filename="gyeongbok-votes-backup.json"'
        return response
    finally:
        c.close()


def restore_backup():
    if not session.get("admin"):
        return jsonify(error="운영진 로그인이 필요합니다."), 401
    d = request.get_json(silent=True)
    if not isinstance(d, dict) or d.get("format") != "gyeongbok_vote_only_v1":
        return jsonify(error="올바른 투표 백업 JSON을 선택해주세요."), 400
    ballots = d.get("ballots")
    if not isinstance(ballots, list) or len(ballots) > 3000:
        return jsonify(error="백업 투표 목록 형식이 잘못됐습니다."), 400
    validated = []
    for b in ballots:
        try:
            dev = str(b["device_hash"]).lower()
            t, p, v = int(b["voter_team"]), int(b["photo_team"]), int(b["video_team"])
            a = int(b.get("absentee", 0))
            src = str(b.get("source") or "restored")[:36]
            at = str(b.get("created_at") or datetime.now(timezone.utc).isoformat())[:40]
        except (KeyError, TypeError, ValueError):
            return jsonify(error="투표 백업 항목이 잘못됐습니다."), 400
        if not HEX64.fullmatch(dev) or p not in SCORES or v not in SCORES or t not in (0,1,2,3,4,5) or a not in (0,1):
            return jsonify(error="투표 백업에 유효하지 않은 항목이 있습니다."), 400
        if (a and t!=0) or (not a and (t==0 or t in (p,v))):
            return jsonify(error="투표 백업에 자기 조 투표 또는 소속 조 오류가 있습니다."), 400
        validated.append((dev,t,p,v,a,src,at))

    c = _connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        for row in validated:
            c.execute("""INSERT OR IGNORE INTO ballots
                (device_hash,voter_team,photo_team,video_team,absentee,source,created_at)
                VALUES(?,?,?,?,?,?,?)""", row)
        imported = c.execute("SELECT changes()").fetchone()[0] if validated else 0
        current = c.execute("SELECT COUNT(*) FROM ballots").fetchone()[0]
        c.commit()
        return jsonify(ok=True,total=current,source_count=len(validated),
                       message="기존 투표를 유지하며 중복 없이 백업을 복원했습니다.")
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def merge_prior_postgres():
    """Manual optional import of already recorded legacy votes from original DB."""
    if not session.get("admin"):
        return jsonify(error="운영진 로그인이 필요합니다."), 401
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return jsonify(error="기존 PostgreSQL 주소가 없습니다."), 503
    try:
        import psycopg2
        pg = psycopg2.connect(url, connect_timeout=2, sslmode="require")
        try:
            with pg.cursor() as cur:
                cur.execute("""SELECT device_hash,voter_team,photo_team,video_team,absentee
                    FROM public_votes""")
                modern = cur.fetchall()
                cur.execute("SELECT code_hash,voter_team,photo_team,video_team FROM votes")
                prior = cur.fetchall()
        finally:
            pg.close()
    except Exception:
        return jsonify(error="기존 DB가 현재 연결되지 않습니다. 투표 전용 화면은 그대로 사용할 수 있습니다."), 503
    rows = [(str(r[0]),int(r[1]),int(r[2]),int(r[3]),int(bool(r[4])),"prior_pg") for r in modern]
    rows += [(str(r[0]),int(r[1]),int(r[2]),int(r[3]),0,"prior_code") for r in prior]
    c = _connect()
    try:
        c.execute("BEGIN IMMEDIATE")
        before = c.execute("SELECT COUNT(*) FROM ballots").fetchone()[0]
        for dev,t,p,v,a,src in rows:
            if HEX64.fullmatch(dev) and t in SCORES and p in SCORES and v in SCORES:
                c.execute("""INSERT OR IGNORE INTO ballots
                    (device_hash,voter_team,photo_team,video_team,absentee,source)
                    VALUES(?,?,?,?,?,?)""", (dev,t,p,v,a,src))
        after = c.execute("SELECT COUNT(*) FROM ballots").fetchone()[0]
        c.commit()
        return jsonify(ok=True,added=after-before,total=after,
                       message="기존 DB의 투표를 중복 없이 가져왔습니다.")
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def page(team=0, token="", absent=False):
    return render_template("vote_only.html", team=team, token=token,
                           absent=absent, mission_scores=SCORES)


def dispatch():
    """Called by app.before_request; return None for existing authentication routes."""
    if os.environ.get("VOTE_ONLY_MODE","1") != "1":
        return None
    path = request.path
    method = request.method
    if method=="GET" and path=="/":
        return page()
    if method=="GET" and path=="/vote/absent":
        return page(absent=True)
    if method=="GET" and path=="/admin/mission":
        return redirect("/?tab=admin")
    qr = TEAM_URL.fullmatch(path) or MISSION_URL.fullmatch(path)
    if method=="GET" and qr:
        team,token=int(qr.group(1)),qr.group(2)
        if not valid_team_qr(team,token):
            return "발급된 조별 QR이 아닙니다. 기존 QR을 다시 확인해주세요.",403
        if path.startswith("/mission/"):
            return redirect(f"/vote/team/{team}/{token}",code=302)
        return page(team=team,token=token)
    if method=="GET" and path=="/api/state":
        return get_state()
    if method=="POST" and path=="/api/vote":
        return cast_vote()
    if method=="POST" and path=="/api/admin/settings":
        return set_setting()
    if method=="GET" and path=="/api/vote-only/backup":
        return backup_json()
    if method=="POST" and path=="/api/vote-only/restore":
        return restore_backup()
    if method=="POST" and path=="/api/vote-only/merge-pg":
        return merge_prior_postgres()
    if method=="GET" and path=="/healthz":
        return jsonify(ok=True,mode="vote_only",storage="temporary_sqlite",
                       warning="Temporary storage; admin backup required")
    if path.startswith("/api/mission/") or path.startswith("/api/admin/mission/"):
        return jsonify(error="행사 사진·영상 제출은 종료됐습니다. 현재는 투표 전용 모드입니다."),410
    return None
