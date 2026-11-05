import os
import re
import secrets
import json
import io
import zipfile
from datetime import datetime, timezone
from urllib.parse import quote
from flask import Blueprint, request, jsonify, session, Response, render_template_string, redirect, url_for
from functools import wraps

mission_bp = Blueprint("palace_missions", __name__)

# Faithfully transcribed from the event's 13-mission approved handout.
MISSIONS = [
 {"code":"E02","title":"우리 조 품계석 찾기","location":"근정전 앞마당","description":"근정전 앞마당에서 우리 조에 배정된 품계석(글자가 새겨진 돌)을 찾으세요. 글자가 잘 보이게 찍으면 성공!","proof":"지정 품계석 사진 1장","points":10},
 {"code":"E08","title":"경회루 인증샷","location":"경회루 연못","description":"경회루가 잘 보이는 위치를 찾아 사진 한 장을 찍으세요. 사람이 나오지 않아도 괜찮습니다.","proof":"경회루 사진 1장","points":10},
 {"code":"E10","title":"사진 속 건물 찾기","location":"사진 단서 참고","description":"제시된 사진과 같은 건물을 찾아가세요. 건물이 비슷한 각도로 나오게 찍으면 성공!","proof":"찾아낸 건물 사진 1장","points":10},
 {"code":"M01","title":"궁궐 보물 3종 찾기","location":"궁궐 공개 관람구역","description":"조원들이 나누어 찾아보세요. ①기와지붕 ②알록달록한 단청 ③돌 장식. 세 가지를 각각 찍으면 성공!","proof":"기와·단청·돌 장식 사진 각 1장","points":15},
 {"code":"M06","title":"좌우 대칭사진 도전","location":"넓은 마당","description":"조원 2명이 좌우에서 같은 자세를 취하고 다른 조원이 찍으세요. 사람·건물이 좌우로 균형 잡히면 성공!","proof":"좌우 대칭 포즈 사진 1장","points":15},
 {"code":"M11","title":"3곳 릴레이 인증샷","location":"근정전 → 사정전 → 경회루","description":"세 장소를 방문해 각각 사진을 찍으세요. 사진마다 서로 다른 조원 1명씩 등장하게 하면 성공!","proof":"세 장소 사진 3장","points":15},
 {"code":"M12","title":"우리 조 전원 한 컷","location":"마음에 드는 곳","description":"셀카 또는 타이머로 조원 전원이 한 장에 나오게 찍으세요. 얼굴 대신 뒷모습이어도 괜찮습니다.","proof":"조원 전원이 나온 사진 1장","points":15},
 {"code":"H01","title":"손바닥 위 동료 착시샷","location":"넓은 마당","description":"한 명은 카메라 가까이 손바닥을 들고, 다른 한 명은 멀리 서세요. 촬영자가 각도를 맞춰 손 위에 서 있는 것처럼 찍으세요.","proof":"원근 착시 사진 1장","points":20},
 {"code":"H04","title":"우리 조 영화 포스터","location":"경복궁 공개 관람구역","description":"조원 3명 이상이 경복궁을 배경으로 사극·첩보·코미디 등 영화 포스터처럼 한 장면을 만들어 찍으세요. 이 사진이 우리 조의 투표 대표작입니다.","proof":"필수 · 투표용 영화 포스터 사진 1장","points":20,"mandatory":"photo"},
 {"code":"H05","title":"반전이 있는 3컷 사진","location":"같은 장소에서 촬영","description":"사진 3장으로 ①평범한 시작 → ②뜻밖의 상황 → ③재미있는 결말을 보여주세요. 대사나 글 설명은 필요 없습니다.","proof":"순서대로 사진 3장","points":20},
 {"code":"V01","title":"조선시대 출근길","location":"근정전 주변","description":"왕이 출근하고 신하가 맞이하는 장면을 15~30초로 찍으세요. 걷고 고개만 숙여도 됩니다. 큰 소리나 대사는 없어도 돼요.","proof":"필수 선택 · 15~30초 투표용 가로 영상 1개","points":30,"mandatory":"video"},
 {"code":"V02","title":"경회루 30초 여행 광고","location":"경회루 주변","description":"경회루 풍경을 촬영하며 동료가 추천 멘트를 해보세요. 예: '이 풍경을 놓치지 마세요!' 얼굴 없이 목소리만 나와도 됩니다.","proof":"필수 선택 · 15~30초 투표용 가로 영상 1개","points":30,"mandatory":"video"},
 {"code":"V03","title":"오늘의 궁궐 뉴스","location":"근정전 주변","description":"앵커·현장 동료·촬영 역할을 나눠 '오늘 경복궁에서 발견한 것'을 짧은 뉴스처럼 찍어보세요.","proof":"필수 선택 · 15~30초 투표용 가로 영상 1개","points":30,"mandatory":"video"},
]
BY_CODE = {m["code"]:m for m in MISSIONS}
OFFICIAL_MAP = "https://royal.khs.go.kr/ROYAL/contents/R701000000.do"
OSM_MAP = "https://www.openstreetmap.org/export/embed.html?bbox=126.9732%2C37.5730%2C126.9820%2C37.5840&layer=mapnik"
KAKAO_MAP = "https://map.kakao.com/?q=%EA%B2%BD%EB%B3%B5%EA%B6%81"
PHOTO_MIMES = {"image/jpeg", "image/png", "image/webp"}
VIDEO_MIMES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_PHOTO = 6 * 1024 * 1024
MAX_VIDEO = 35 * 1024 * 1024
MAX_VIDEO_INPUT = 35 * 1024 * 1024  # Direct upload, no synchronous transcoding
MAX_PER_TEAM = 75 * 1024 * 1024
MAX_FILES_PER_TEAM = 30

def dbtools():
    from app import connect, query
    return connect, query

def init_missions():
    connect, q = dbtools()
    db = connect()
    try:
        q(db, "CREATE TABLE IF NOT EXISTS mission_access(team INTEGER PRIMARY KEY, token TEXT NOT NULL)")
        q(db, """CREATE TABLE IF NOT EXISTS mission_submissions(
          id BIGSERIAL PRIMARY KEY, team INTEGER NOT NULL, mission_code VARCHAR(3) NOT NULL,
          mime VARCHAR(60) NOT NULL, filename VARCHAR(180) NOT NULL,
          data BYTEA NOT NULL, size_bytes INTEGER NOT NULL,
          status VARCHAR(20) NOT NULL DEFAULT 'pending', is_test BOOLEAN NOT NULL DEFAULT FALSE,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), reviewed_at TIMESTAMPTZ)""")
        q(db, "CREATE INDEX IF NOT EXISTS idx_mission_submission_team ON mission_submissions(team,created_at DESC)")
        q(db, "ALTER TABLE teams ADD COLUMN IF NOT EXISTS vote_photo_submission_id BIGINT")
        q(db, "ALTER TABLE teams ADD COLUMN IF NOT EXISTS vote_video_submission_id BIGINT")
        q(db, """CREATE TABLE IF NOT EXISTS mission_settings(
          id INTEGER PRIMARY KEY, uploads_open BOOLEAN NOT NULL DEFAULT TRUE)""")
        q(db,"ALTER TABLE mission_settings ADD COLUMN IF NOT EXISTS test_mode BOOLEAN NOT NULL DEFAULT TRUE")
        q(db,"INSERT INTO mission_settings(id,test_mode) VALUES(1,TRUE) ON CONFLICT DO NOTHING")
        for team in range(1,6):
            q(db,"INSERT INTO mission_access(team,token) VALUES(?,?) ON CONFLICT (team) DO NOTHING",
              (team,secrets.token_urlsafe(24)))
        db.commit()
        print("PALACE_MISSIONS_DB_READY", flush=True)
    except:
        db.rollback()
        raise
    finally:
        db.close()

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):return jsonify(error="관리자 로그인이 필요합니다."),401
        return fn(*args,**kwargs)
    return wrapper

def token_ok(db, q, team, token):
    if team not in range(1,6) or not re.fullmatch(r"[A-Za-z0-9_-]{24,60}",token or ""):return False
    row=q(db,"SELECT token FROM mission_access WHERE team=?",(team,))
    return bool(row) and secrets.compare_digest(row["token"],token)

def get_team_link(team,token):
    return f"https://gyeongbok-vote-20261106.onrender.com/mission/{team}/{token}"

def mission_content(team):
    out=[]
    for item in MISSIONS:
        m=dict(item)
        if m["code"]=="E02":m["description"] += f" · {team}조는 정{team}품"
        out.append(m)
    return out

def public_submission(row):
    return {"id":row["id"],"team":row["team"],"mission_code":row["mission_code"],
      "filename":row["filename"],"mime":row["mime"],"size_bytes":row["size_bytes"],
      "status":row["status"],"is_test":bool(row["is_test"]),
      "created_at":(row["created_at"].isoformat() if hasattr(row.get("created_at"),"isoformat") else str(row.get("created_at") or ""))}

@mission_bp.get("/mission/<int:team>/<token>")
def team_mission_page(team,token):
    connect,q=dbtools()
    db=connect()
    try:
        if not token_ok(db,q,team,token):return "<h2>유효하지 않은 조별 QR코드입니다.</h2>",403
    finally:db.close()
    return render_template_string(MISSION_HTML, team=team, token=token, official_map=OFFICIAL_MAP, osm_map=OSM_MAP, kakao_map=KAKAO_MAP)

@mission_bp.get("/api/mission/<int:team>/<token>/state")
def mission_state(team, token):
    connect, q = dbtools()
    db = connect()
    try:
        if not token_ok(db, q, team, token):
            return jsonify(error="조별 QR코드를 확인해주세요."), 403
        config = q(db, "SELECT uploads_open,test_mode FROM mission_settings WHERE id=1")
        global_test = bool(config["test_mode"])
        wants_admin_tests = request.args.get("test") == "1"
        if wants_admin_tests and not session.get("admin") and not global_test:
            return jsonify(error="운영진 테스트 내역은 관리자만 볼 수 있습니다."), 401
        include_tests = global_test or (wants_admin_tests and bool(session.get("admin")))
        constraint = "" if include_tests else " AND is_test=FALSE"
        rows = q(db, """SELECT id,team,mission_code,filename,mime,size_bytes,status,is_test,created_at
            FROM mission_submissions WHERE team=?""" + constraint + " ORDER BY created_at DESC",
            (team,), all=True)
        uploaded_by_admin = q(db,"SELECT video_data IS NOT NULL AS video_ready FROM teams WHERE team=?",(team,))
        return jsonify(ok=True,team=team,uploads_open=bool(config["uploads_open"]),
            organizer_video_uploaded=bool(uploaded_by_admin["video_ready"]),
            test_mode=global_test,admin_test_preview=bool(wants_admin_tests and session.get("admin")),
            max_video_input_mb=35, max_video_saved_mb=35,missions=mission_content(team),
            submissions=[public_submission(x) for x in rows])
    finally:
        db.close()


def valid_magic(data,mime):
    if mime=="image/jpeg":return data[:3]==b"\xff\xd8\xff"
    if mime=="image/png":return data[:8]==b"\x89PNG\r\n\x1a\n"
    if mime=="image/webp":return data[:4]==b"RIFF" and data[8:12]==b"WEBP"
    if mime=="video/mp4":return data[4:8]==b"ftyp"
    if mime=="video/webm":return data[:4]==b"\x1a\x45\xdf\xa3"
    if mime=="video/quicktime":return data[4:8]==b"ftyp"
    return False

@mission_bp.post("/api/mission/<int:team>/<token>/upload")
def mission_upload(team, token):
    code = (request.form.get("mission_code") or "").upper().strip()
    if code not in BY_CODE:
        return jsonify(error="유효하지 않은 미션입니다."), 400
    f = request.files.get("file")
    if not f:
        return jsonify(error="파일을 선택해주세요."), 400
    is_video = code.startswith("V")
    allowed = VIDEO_MIMES if is_video else PHOTO_MIMES
    incoming_limit = MAX_VIDEO_INPUT if is_video else MAX_PHOTO
    mime = (f.mimetype or "").lower().split(";")[0].strip()
    if mime not in allowed:
        return jsonify(error="사진 JPG/PNG/WEBP, 영상 MP4/WEBM/MOV만 지원합니다."), 400

    # Avoid reading or processing media for an invalid team or closed intake.
    connect, q = dbtools()
    db = connect()
    try:
        if not token_ok(db, q, team, token):
            return jsonify(error="조별 QR코드가 유효하지 않습니다."), 403
        setting = q(db,"SELECT uploads_open,test_mode FROM mission_settings WHERE id=1")
        global_test = bool(setting["test_mode"])
        explicit_test = request.form.get("test") == "1"
        if explicit_test and not global_test and not session.get("admin"):
            return jsonify(error="관리자 테스트 모드로 올리려면 관리자로 로그인해주세요."), 401
        is_test = global_test or explicit_test
        if not setting["uploads_open"] and not (is_test and session.get("admin")):
            return jsonify(error="제출 시간이 종료됐습니다. 운영진에게 문의해주세요."), 403
    finally:
        db.close()

    raw = f.read(incoming_limit + 1)
    if not 100 <= len(raw) <= incoming_limit or not valid_magic(raw,mime):
        limit_text = "영상 원본 35MB" if is_video else "사진 6MB"
        return jsonify(error=f"파일 형식과 크기를 확인해주세요. {limit_text} 이하로 올릴 수 있습니다."), 413

    original_bytes = len(raw)
    safe_name = os.path.basename(f.filename or ("video" if is_video else "photo"))[:180]
    compressed = False
    # Save uploaded video directly, as before the compression regression.
    # No FFmpeg lock or long-running work: concurrent teams can submit.
    # Large videos are intentionally handled via the event's KakaoTalk fallback.
    db = connect()
    try:
        if not token_ok(db,q,team,token):
            return jsonify(error="조별 QR코드가 유효하지 않습니다."), 403
        # Per-team lock prevents concurrent uploads from bypassing storage quotas.
        q(db,"SELECT team FROM teams WHERE team=? FOR UPDATE",(team,))
        latest = q(db,"SELECT uploads_open,test_mode FROM mission_settings WHERE id=1")
        is_test = is_test or bool(latest["test_mode"])
        if not latest["uploads_open"] and not (is_test and session.get("admin")):
            return jsonify(error="제출 시간이 종료됐습니다."), 403
        usage = q(db,"""SELECT COALESCE(SUM(size_bytes),0) AS total,COUNT(*) AS cnt
            FROM mission_submissions WHERE team=? AND is_test=?""",(team,is_test))
        if usage["total"] + len(raw) > MAX_PER_TEAM or usage["cnt"] >= MAX_FILES_PER_TEAM:
            return jsonify(error="조별 업로드 용량(75MB) 또는 파일 개수(30개) 한도를 초과했습니다. 운영진에게 문의해주세요."), 413
        q(db, """INSERT INTO mission_submissions(team,mission_code,mime,filename,data,size_bytes,is_test)
            VALUES(?,?,?,?,?,?,?)""",(team,code,mime,safe_name,raw,len(raw),is_test))
        db.commit()
        return jsonify(ok=True,test=is_test,compressed=compressed,
            original_bytes=original_bytes,stored_bytes=len(raw),
            message="🧪 사전 테스트 제출 완료 · 실제 점수와 투표에는 반영되지 않습니다."
            if is_test else "제출 완료 · 운영진 검수 대기")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def serve_media_bytes(data,mime):
    data=bytes(data)
    total=len(data)
    rng=request.headers.get("Range","")
    headers={"Accept-Ranges":"bytes","Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}
    if rng:
        m=re.fullmatch(r"bytes=(\d*)-(\d*)",rng.strip())
        if not m:return Response(status=416,headers={"Content-Range":f"bytes */{total}"})
        lo,hi=m.groups()
        if lo:
            start=int(lo);end=int(hi) if hi else total-1
        else:
            suffix=int(hi or 0);start=max(0,total-suffix);end=total-1
        if start>=total or end<start:return Response(status=416,headers={"Content-Range":f"bytes */{total}"})
        end=min(end,total-1)
        chunk=data[start:end+1]
        headers["Content-Range"]=f"bytes {start}-{end}/{total}"
        headers["Content-Length"]=str(len(chunk))
        return Response(chunk,206,mimetype=mime,headers=headers)
    headers["Content-Length"]=str(total)
    return Response(data,mimetype=mime,headers=headers)

@mission_bp.get("/api/mission/<int:team>/<token>/media/<int:file_id>")
def participant_media(team,token,file_id):
    connect,q=dbtools()
    db=connect()
    try:
        if not token_ok(db,q,team,token):
            return "Forbidden",403
        cfg=q(db,"SELECT test_mode FROM mission_settings WHERE id=1")
        include_tests=bool(cfg["test_mode"]) or (request.args.get("test")=="1" and bool(session.get("admin")))
        if request.args.get("test")=="1" and not include_tests:
            return "Unauthorized",401
        condition="" if include_tests else " AND is_test=FALSE"
        row=q(db,"SELECT data,mime FROM mission_submissions WHERE id=? AND team=?"+condition,(file_id,team))
        if not row:return "Not Found",404
        return serve_media_bytes(row["data"],row["mime"])
    finally:db.close()




def downloadable_media(data, mime, filename, file_id):
    """Return stored media bytes as an actual download, never as inline HTML."""
    from flask import send_file
    safe = re.sub(r"[\\/\x00-\x1f\x7f]", "_", str(filename or "").split("\\")[-1]).strip(" .")
    if not safe:
        safe = f"submission-{file_id}.mp4" if str(mime).startswith("video/") else f"submission-{file_id}.jpg"
    response = send_file(io.BytesIO(bytes(data)), mimetype=mime,
                         as_attachment=True, download_name=safe,
                         conditional=False, max_age=0)
    response.cache_control.no_store = True
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@mission_bp.get("/api/mission/<int:team>/<token>/download/<int:file_id>")
def participant_download(team, token, file_id):
    connect, q = dbtools()
    db = connect()
    try:
        if not token_ok(db, q, team, token):
            return "Forbidden", 403
        cfg = q(db, "SELECT test_mode FROM mission_settings WHERE id=1")
        include_tests = bool(cfg["test_mode"]) or (
            request.args.get("test") == "1" and bool(session.get("admin")))
        if request.args.get("test") == "1" and not include_tests:
            return "Unauthorized", 401
        condition = "" if include_tests else " AND is_test=FALSE"
        row = q(db, "SELECT data,mime,filename FROM mission_submissions WHERE id=? AND team=?"
                + condition, (file_id, team))
        if not row:
            return "Not Found", 404
        return downloadable_media(row["data"], row["mime"], row["filename"], file_id)
    finally:
        db.close()


@mission_bp.get("/api/admin/mission/download/<int:fid>")
@admin_required
def administrator_download(fid):
    connect, q = dbtools()
    db = connect()
    try:
        row = q(db, "SELECT data,mime,filename FROM mission_submissions WHERE id=?", (fid,))
        if not row:
            return "Not Found", 404
        return downloadable_media(row["data"], row["mime"], row["filename"], fid)
    finally:
        db.close()


@mission_bp.get("/admin/mission")
def admin_mission_page():
    return Response(ADMIN_HTML,mimetype="text/html")

@mission_bp.get("/api/admin/mission/state")
@admin_required
def admin_mission_state():
    connect,q=dbtools()
    db=connect()
    try:
        links=q(db,"SELECT team,token FROM mission_access ORDER BY team",all=True)
        docs=q(db,"""SELECT id,team,mission_code,filename,mime,size_bytes,status,is_test,created_at
          FROM mission_submissions ORDER BY created_at DESC LIMIT 250""",all=True)
        rec=q(db,"SELECT uploads_open,test_mode FROM mission_settings WHERE id=1")
        ts=q(db,"SELECT team,photo_data IS NOT NULL AS photo_ready,video_data IS NOT NULL AS video_ready,mission_score FROM teams ORDER BY team",all=True)
        return jsonify(ok=True,links=[{"team":r["team"],"url":get_team_link(r["team"],r["token"])} for r in links],
          submissions=[public_submission(r) for r in docs],uploads_open=bool(rec["uploads_open"]),
          test_mode=bool(rec["test_mode"]),test_count=sum(1 for r in docs if r["is_test"]),teams=ts)
    finally:db.close()

@mission_bp.post("/api/admin/mission/test-mode")
@admin_required
def toggle_pretest_mode():
    data=request.get_json(silent=True) or {}
    if type(data.get("enabled")) is not bool:
        return jsonify(error="올바른 테스트 설정을 선택해주세요."),400
    connect,q=dbtools()
    db=connect()
    try:
        q(db,"UPDATE mission_settings SET test_mode=? WHERE id=1",(data["enabled"],))
        db.commit()
        return jsonify(ok=True,test_mode=data["enabled"],
            message="사전 테스트 모드 실행 중" if data["enabled"] else "실제 행사 제출 모드로 전환됨")
    finally:db.close()


@mission_bp.post("/api/admin/mission/uploads")
@admin_required
def set_uploads_open():
    data=request.get_json(silent=True) or {}
    if type(data.get("open")) is not bool:return jsonify(error="설정값 오류"),400
    connect,q=dbtools();db=connect()
    try:
        q(db,"UPDATE mission_settings SET uploads_open=? WHERE id=1",(data["open"],))
        db.commit();return jsonify(ok=True)
    finally:db.close()

@mission_bp.post("/api/admin/mission/review")
@admin_required
def review_upload():
    b=request.get_json(silent=True) or {}
    try:fid=int(b.get("id",0))
    except:return jsonify(error="파일 번호 오류"),400
    action=b.get("action")
    if action not in ("approved","rejected"):return jsonify(error="승인/반려를 선택하세요."),400
    connect,q=dbtools();db=connect()
    try:
        row=q(db,"SELECT id,team,mission_code,mime,data,is_test FROM mission_submissions WHERE id=? FOR UPDATE",(fid,))
        if not row:return jsonify(error="파일이 없습니다."),404
        if row["is_test"]:return jsonify(error="테스트 파일은 승인되지 않습니다. 테스트 삭제 버튼을 이용하세요."),400
        code=row["mission_code"];team=row["team"]
        if action=="approved" and code=="H04":
            q(db,"UPDATE mission_submissions SET status='pending' WHERE team=? AND mission_code='H04' AND status='approved' AND id<>?",(team,fid))
            q(db,"UPDATE teams SET photo_data=?,photo_type=?,vote_photo_submission_id=? WHERE team=?",
              (row["data"],row["mime"],fid,team))
        if action=="approved" and code.startswith("V"):
            q(db,"UPDATE mission_submissions SET status='pending' WHERE team=? AND mission_code LIKE 'V%' AND status='approved' AND id<>?",(team,fid))
            q(db,"UPDATE teams SET video_data=?,video_type=?,vote_video_submission_id=? WHERE team=?",
              (row["data"],row["mime"],fid,team))
        if action=="rejected":
            if code=="H04":
                q(db,"UPDATE teams SET photo_data=NULL,photo_type=NULL,vote_photo_submission_id=NULL WHERE team=? AND vote_photo_submission_id=?",(team,fid))
            elif code.startswith("V"):
                q(db,"UPDATE teams SET video_data=NULL,video_type=NULL,vote_video_submission_id=NULL WHERE team=? AND vote_video_submission_id=?",(team,fid))
        q(db,"UPDATE mission_submissions SET status=?,reviewed_at=NOW() WHERE id=?",(action,fid))
        db.commit();return jsonify(ok=True)
    except:
        db.rollback();raise
    finally:db.close()

@mission_bp.post("/api/admin/mission/delete")
@admin_required
def remove_upload():
    b=request.get_json(silent=True) or {}
    try:fid=int(b.get("id",0))
    except:return jsonify(error="파일 번호 오류"),400
    connect,q=dbtools();db=connect()
    try:
        q(db,"UPDATE teams SET photo_data=NULL,photo_type=NULL,vote_photo_submission_id=NULL WHERE vote_photo_submission_id=?",(fid,))
        q(db,"UPDATE teams SET video_data=NULL,video_type=NULL,vote_video_submission_id=NULL WHERE vote_video_submission_id=?",(fid,))
        q(db,"DELETE FROM mission_submissions WHERE id=?",(fid,))
        db.commit();return jsonify(ok=True)
    except:
        db.rollback();raise
    finally:db.close()

@mission_bp.post("/api/admin/mission/clear-tests")
@admin_required
def clear_tests():
    connect,q=dbtools();db=connect()
    try:
        q(db,"DELETE FROM mission_submissions WHERE is_test=TRUE")
        db.commit();return jsonify(ok=True)
    finally:db.close()

@mission_bp.get("/api/admin/mission/media/<int:fid>")
@admin_required
def admin_media(fid):
    connect,q=dbtools();db=connect()
    try:
        row=q(db,"SELECT mime,data FROM mission_submissions WHERE id=?",(fid,))
        if not row:return "Not Found",404
        return serve_media_bytes(row["data"],row["mime"])
    finally:db.close()

@mission_bp.get("/api/admin/mission/qr.png")
@admin_required
def single_qr():
    try:team=int(request.args.get("team","0"))
    except:team=0
    if team not in range(1,6):return "Invalid team",400
    import qrcode
    connect,q=dbtools();db=connect()
    try:
        t=q(db,"SELECT token FROM mission_access WHERE team=?",(team,))
        qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=10,border=4)
        qr.add_data(get_team_link(team,t["token"]))
        qr.make(fit=True)
        out=io.BytesIO();qr.make_image(fill_color="#172F45",back_color="white").save(out,"PNG")
        return Response(out.getvalue(),mimetype="image/png",
          headers={"Content-Disposition":("inline" if request.args.get("inline")=="1" else "attachment") + f'; filename="gyeongbok-team-{team}.png"'})
    finally:db.close()

@mission_bp.get("/api/admin/mission/qr.zip")
@admin_required
def qrs_zip():
    import qrcode
    connect,q=dbtools();db=connect()
    try:
        rows=q(db,"SELECT team,token FROM mission_access ORDER BY team",all=True)
        data=io.BytesIO()
        with zipfile.ZipFile(data,"w",compression=zipfile.ZIP_DEFLATED) as archive:
            notes=["2026-11-06 Gyeongbokgung team mission QR links"]
            for row in rows:
                team=row["team"];url=get_team_link(team,row["token"])
                qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=10,border=4)
                qr.add_data(url);qr.make(fit=True)
                buf=io.BytesIO()
                qr.make_image(fill_color="#172F45",back_color="white").save(buf,"PNG")
                archive.writestr(f"team-{team}-QR.png",buf.getvalue())
                notes.append(f"{team}조: {url}")
            archive.writestr("team-links.txt","\n".join(notes))
        return Response(data.getvalue(),mimetype="application/zip",
          headers={"Content-Disposition":'attachment; filename="gyeongbok-team-QR-5.zip"'})
    finally:db.close()

# HTML shell strings contain no embedded JavaScript: scripts are standalone static files.
MISSION_HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#152e43"><title>{{team}}조 · 경복궁 힐링데이 미션</title>
<link rel="stylesheet" href="/static/mission.css"></head><body data-team="{{team}}" data-token="{{token}}">
<header class="top"><div class="logo">宮 <span>2026 HEALING DAY</span></div><b>{{team}}조 전용 미션</b></header>
<div id="notice" role="alert" hidden></div><main class="shell">
<section class="hero"><small>GYEONGBOKGUNG CHALLENGE</small><h1>경복궁에서 만드는<br><em>우리 조의 한 장면</em></h1><p>11월 6일 (금) · 14:40–16:00 미션</p><div class="count"><b id="progress">0 / 6</b><span>제출 진행률 (승인·채점 별도)</span></div><div class="progress-track"><div id="bar"></div></div></section>
<nav class="tabs" aria-label="미션 탐색"><button class="active" data-tab="missions">미션 13개</button><button data-tab="map">실제 지도</button><button data-tab="uploads">제출 현황</button><button data-tab="info">일정·안내</button></nav>
<section id="missions" class="tab-panel"><div class="lead"><h2>필수 2개 + 자유 4개</h2><p>영화 포스터 1장, 영상 3종 중 1개는 필수! 나머지 4개는 자유 선택하세요. 사진은 이 페이지에서 직접 제출하세요. 영상은 조별 대표자가 카카오톡으로 운영진에게 보내는 방식을 추천하며, 35MB 이하 영상은 사이트에 직접 올릴 수도 있습니다.</p></div><div id="mission-list" class="mission-list"></div></section>
<section id="map" class="tab-panel" hidden><div class="lead"><h2>지도로 장소 찾기</h2><p>실제 지도를 확대해 확인하세요. 궁 안에서는 GPS 오차가 있을 수 있습니다.</p></div><div class="map-buttons"><a href="{{official_map}}" target="_blank" rel="noopener">🏯 공식 궁궐 관람지도</a><a href="{{kakao_map}}" target="_blank" rel="noopener">📍 카카오맵 열기</a></div><iframe title="경복궁 실시간 지도" loading="lazy" src="{{osm_map}}"></iframe><p class="caption">지도 데이터 © OpenStreetMap 기여자 · 미션 장소는 실제 관람 가능 구역을 기준으로 확인해 주세요.</p><div class="map-places"><b>주요 위치 바로 찾기</b><a href="https://map.kakao.com/?q=%EA%B2%BD%EB%B3%B5%EA%B6%81%20%EA%B7%BC%EC%A0%95%EC%A0%84" target="_blank" rel="noopener">근정전</a><a href="https://map.kakao.com/?q=%EA%B2%BD%EB%B3%B5%EA%B6%81%20%EC%82%AC%EC%A0%95%EC%A0%84" target="_blank" rel="noopener">사정전</a><a href="https://map.kakao.com/?q=%EA%B2%BD%EB%B3%B5%EA%B6%81%20%EA%B2%BD%ED%9A%8C%EB%A3%A8" target="_blank" rel="noopener">경회루</a></div></section>
<section id="uploads" class="tab-panel" hidden><div class="lead"><h2>제출된 사진·영상</h2><p>이 조에서 제출한 파일과 운영진 검수 현황입니다. 제출 후에도 이곳에서 확인할 수 있습니다.</p></div><div id="uploads-list"></div></section>
<section id="info" class="tab-panel" hidden><div class="lead"><h2>운영 안내</h2></div><div class="info-card"><b>14:40 — 미션 시작</b><p>13개 중 필수 2개 + 자유 4개를 수행합니다.</p></div><div class="info-card"><b>16:00 — 미션 종료</b><p>사진·영상 파일을 정리해 등록하세요.</p></div><div class="info-card"><b>16:25 — 제출 마감</b><p>경복궁에서 별도 재집결 없이 세화미술관 방향으로 이동합니다.</p></div><div class="info-card"><b>16:30 — 세화미술관</b><p>예약된 관람 일정에 맞춰 도착합니다.</p></div><div class="info-card"><b>시상식 — 작품 모바일 투표</b><p>각 조의 영화 포스터 사진 1장과 카카오톡으로 받은 영상 1개를 운영진이 투표 사이트에 등록해 투표합니다.</p><a href="/" class="soft-link">투표 사이트 열기 ↗</a></div><div class="info-card"><b>종합 점수</b><p>미션 원점수 최대 120점을 70점으로 환산 + 사진 투표 10점 + 영상 투표 20점 = 100점</p><p>미션 완료 체크는 자동 점수가 아닙니다. 운영진의 증빙 검수와 최종 채점이 적용됩니다.</p></div></section>
</main><footer>宮 2026 경복궁 힐링데이 · 조별 전용 페이지</footer>
<script src="/static/mission.js" defer></script></body></html>"""

ADMIN_HTML = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#152e43"><title>경복궁 미션 운영 관리</title><link rel="stylesheet" href="/static/mission.css"></head>
<body class="admin-body"><header class="top"><div class="logo">宮 <span>HEALING DAY · CONTROL</span></div><a href="/">투표 관리로 이동 ↗</a></header><main class="shell"><section class="hero"><small>ORGANIZER DASHBOARD</small><h1>미션 제출·QR 관리</h1><p>5개 조의 사진을 검수하고, 카카오톡으로 수신한 영상은 투표 관리에서 등록합니다.</p></section><div id="notice" role="alert" hidden></div>
<section id="admin-login" class="admin-login"><h2>관리자 로그인</h2><p>기존 투표 사이트 관리자 비밀번호를 사용하세요.</p><input id="admin-password" type="password" placeholder="관리자 비밀번호"><button id="login-button">로그인</button></section>
<section id="admin-panel" hidden><div class="test-mode-controls" id="test-mode-controls"><div class="test-mode-copy"><div class="test-mode-heading"><strong>🧪 사전 테스트 모드</strong><span id="test-mode-badge">확인 중</span></div><p id="test-mode-description">조별 QR로 업로드한 파일을 테스트로 분리합니다. 테스트 파일은 점수·투표에 반영되지 않습니다.</p></div><button id="toggle-test-mode">설정 불러오는 중</button></div><div class="admin-strip"><div><strong>참가자 업로드</strong><small id="upload-state"></small></div><button id="toggle-uploads">마감 / 재개</button><button id="clear-tests">테스트 파일만 일괄 삭제</button></div>
<div class="panel-box"><h2>① 조별 QR코드 5개</h2><p>회사 쪽지에 조별 QR 이미지를 보내세요. 아래 파일은 회사 쪽지에 첨부할 수 있습니다.</p><a class="action-link" href="/api/admin/mission/qr.zip">⬇ 5개 조 QR 이미지 ZIP 다운로드</a><div id="qr-grid" class="qr-grid"></div><p class="caption">QR에 포함된 조별 링크는 길고 무작위로 생성된 주소입니다. 외부에 공유되지 않도록 주의하세요.</p></div>
<div class="panel-box"><h2>② 실제 제출 확인 및 승인</h2><p>QR로 제출된 사진·영상은 여기서 검수합니다. 카카오톡으로 받은 영상은 상단 '투표 관리로 이동'에서 해당 조의 영상 업로드로 등록할 수 있습니다. QR로 받은 작품 중 승인한 H04 영화 포스터·영상 미션도 투표 화면에 반영됩니다.</p><div class="admin-filters"><button data-filter="pending" class="active">검수 대기</button><button data-filter="all">전체</button><button data-filter="test">테스트만</button></div><div id="submissions"></div></div>
<div class="panel-box"><h2>③ 관리자 업로드 테스트</h2><p>사전 테스트 모드에서는 누구든 기존 조별 QR로 시험 제출합니다. 이 관리자 전용 링크는 실제 행사 모드에서도 별도 테스트에 사용할 수 있습니다.</p><div id="test-links"></div><p class="caption">테스트 전용 링크로 접속하면 파일이 '테스트'로 구분됩니다. 테스트 후 위의 삭제 기능으로 일괄 정리할 수 있습니다.</p></div>
</section></main><dialog id="preview-modal" class="preview-modal" aria-label="제출 파일 확대 미리보기"><div class="preview-head"><strong id="preview-title">제출 파일 미리보기</strong><button id="preview-close" type="button">닫기 ✕</button></div><div id="preview-body" class="preview-body"></div><a id="preview-download" class="preview-download" target="_blank" rel="noopener">원본 파일 새 창에서 보기 ↗</a></dialog><footer>궁궐 미션 · 운영진 전용</footer><script src="/static/mission-admin.js" defer></script></body></html>"""
