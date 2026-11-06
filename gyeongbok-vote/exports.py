"""Download all Gyeongbokgung mission submissions and voting media as ZIP.

ZIPs are assembled on temporary disk, not in memory. Individual BYTEA values
are fetched one at a time to avoid allocating the whole archive in RAM.
"""
import csv
import io
import os
import re
import tempfile
import zipfile
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, session, jsonify, send_file

export_bp = Blueprint("gyeongbok_exports", __name__)

def _db():
    from app import connect, query
    return connect, query

def _only_admin(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if not session.get("admin"):
            return jsonify(error="운영진 로그인이 필요합니다."), 401
        return fn(*args, **kwargs)
    return inner

def _safe_filename(value, default):
    name = str(value or "").replace("\\", "/").split("/")[-1]
    name = re.sub(r'[\x00-\x1f\x7f<>:"/\\|?*]+', "_", name).strip(" .")
    name = name[:110].strip(" .")
    if not name:
        return default
    return name

def _kind(mime):
    return "video" if (mime or "").startswith("video/") else "photo"

def _extension(mime):
    return {
        "image/jpeg":".jpg", "image/png":".png", "image/webp":".webp",
        "video/mp4":".mp4", "video/webm":".webm", "video/quicktime":".mov",
    }.get(mime or "", ".bin")

def _make_zip(team_filter, kind, scope, include_vote):
    """Return seekable temporary file and the number of included media items.

    Leave the returned file open until Flask finishes sending the response.
    The operating system automatically deletes the anonymous TemporaryFile
    when its handle is closed.
    """
    connect, q = _db()
    db = connect()
    fp = tempfile.TemporaryFile(mode="w+b")
    written = 0
    manifest = io.StringIO()
    writer = csv.writer(manifest)
    writer.writerow(["구분", "조", "미션", "검수", "시험자료", "원본파일명", "ZIP경로", "저장바이트"])
    try:
        with zipfile.ZipFile(fp, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as z:
            clauses = ["is_test=?"]
            params = [scope == "test"]
            if team_filter:
                clauses.append("team=?")
                params.append(team_filter)
            if kind == "photo":
                clauses.append("mime LIKE 'image/%'")
            elif kind == "video":
                clauses.append("mime LIKE 'video/%'")
            where = " AND ".join(clauses)
            # Metadata query has no LIMIT; all saved submissions are exported.
            records = q(db, """SELECT id,team,mission_code,filename,mime,status,is_test,size_bytes
                 FROM mission_submissions WHERE """ + where + " ORDER BY team,mission_code,id",
                 tuple(params), all=True)
            for rec in records:
                file_row = q(db, "SELECT data FROM mission_submissions WHERE id=?", (rec["id"],))
                if not file_row or file_row["data"] is None:
                    continue
                media = bytes(file_row["data"])
                filename = _safe_filename(rec["filename"], f"file-{rec['id']}{_extension(rec['mime'])}")
                cat = "영상" if _kind(rec["mime"]) == "video" else "사진"
                team = rec["team"]
                subdir = "테스트_제출자료" if scope == "test" else "미션_제출자료"
                zip_name = f"{team}조/{subdir}/{cat}/{rec['mission_code']}/{rec['id']:06d}_{filename}"
                z.writestr(zip_name, media)
                writer.writerow(["미션제출", team, rec["mission_code"], rec["status"],
                                 "예" if rec["is_test"] else "아니오", rec["filename"], zip_name, len(media)])
                written += 1
                del media, file_row
            # Voting data may be uploaded directly by the organizer after KakaoTalk.
            # Include it alongside all mission evidence, even if it duplicates an approved file.
            if include_vote and scope == "real":
                teams = q(db, """SELECT team,photo_title,video_title,photo_type,video_type,
                      photo_data IS NOT NULL AS has_photo,video_data IS NOT NULL AS has_video
                      FROM teams ORDER BY team""", all=True)
                for t in teams:
                    team = t["team"]
                    if team_filter and team != team_filter:
                        continue
                    for k in ("photo", "video"):
                        if kind != "all" and kind != k:
                            continue
                        if not t["has_" + k]:
                            continue
                        row = q(db, f"SELECT {k}_data AS data FROM teams WHERE team=?", (team,))
                        if not row or row["data"] is None:
                            continue
                        mime = t[k + "_type"] or ("image/jpeg" if k == "photo" else "video/mp4")
                        title = _safe_filename(t[k + "_title"], "대표작")[:36]
                        extension = _extension(mime)
                        type_name = "사진" if k == "photo" else "영상"
                        name = f"{team}조/투표_대표작/{type_name}_{team}조_{title}{extension}"
                        data = bytes(row["data"])
                        z.writestr(name, data)
                        writer.writerow(["투표대표작", team, "", "등록", "아니오", title + extension, name, len(data)])
                        written += 1
                        del data, row

            details = [
                "2026 경복궁 힐링데이 · 제출 사진·영상 백업",
                "",
                f"다운로드 범위: {'전체 5개 조' if not team_filter else str(team_filter) + '조'}",
                f"자료 분류: {'테스트 자료' if scope == 'test' else '실제 제출 자료 + 투표 대표작'}",
                f"파일 종류: {'사진·영상 전체' if kind == 'all' else '사진' if kind == 'photo' else '영상'}",
                f"포함 미디어 파일 수: {written}개",
                "",
                "미션 제출 자료에는 승인·검수대기·반려 파일이 모두 포함됩니다.",
                "투표 대표작 폴더는 운영진이 등록한 사진/영상이며 일부 미션 파일과 중복될 수 있습니다.",
                "이 ZIP에는 투표자 개인정보·투표코드·QR 비밀 주소를 포함하지 않습니다.",
                "index.csv에서 파일명과 각 조·미션·검수 상태를 확인하세요.",
            ]
            z.writestr("읽어주세요.txt", "\n".join(details).encode("utf-8-sig"))
            z.writestr("index.csv", manifest.getvalue().encode("utf-8-sig"))
        fp.seek(0)
        return fp, written
    except Exception:
        fp.close()
        raise
    finally:
        db.close()

def _deliver_zip(team, kind, scope, include_vote):
    fp, written = _make_zip(team, kind, scope, include_vote)
    today = "20261106"
    target = f"team{team}" if team else "all5teams"
    filename = f"gyeongbok-{today}-{target}-{scope}-{kind}.zip"
    try:
        response = send_file(fp, as_attachment=True, download_name=filename,
                             mimetype="application/zip", conditional=False, max_age=0)
        response.cache_control.no_store = True
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Archive-Media-Count"] = str(written)
        return response
    except Exception:
        fp.close()
        raise

@export_bp.get("/api/admin/mission/archive.zip")
@_only_admin
def admin_download_all():
    try:
        team = int(request.args.get("team", "0"))
    except (TypeError, ValueError):
        return jsonify(error="조 선택이 올바르지 않습니다."), 400
    kind = request.args.get("kind", "all")
    scope = request.args.get("scope", "real")
    if team not in range(0, 6) or kind not in ("all", "photo", "video") or scope not in ("real", "test"):
        return jsonify(error="ZIP 다운로드 옵션이 올바르지 않습니다."), 400
    return _deliver_zip(team, kind, scope, include_vote=(scope == "real"))

@export_bp.get("/api/mission/<int:team>/<token>/archive.zip")
def download_team_archive(team, token):
    # A team link grants access ONLY to that team's existing submissions.
    # The test archive can be downloaded publicly while the rehearsal mode
    # is active; otherwise it requires an authenticated organizer.
    from mobile import token_ok
    connect, q = _db()
    db = connect()
    try:
        if not token_ok(db, q, team, token):
            return jsonify(error="조별 QR이 올바르지 않습니다."), 403
        cfg = q(db, "SELECT test_mode FROM mission_settings WHERE id=1")
        test_mode = bool(cfg["test_mode"])
        scope = "test" if test_mode else "real"
    finally:
        db.close()
    return _deliver_zip(team, "all", scope, include_vote=False)
