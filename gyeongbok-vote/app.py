import os, io, json, re, time, hashlib, secrets, hmac
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string, Response, g
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=40*1024*1024)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
DATABASE_URL=os.environ.get("DATABASE_URL","")
ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD","")
IS_PG=bool(DATABASE_URL)

# API clients must always receive JSON, even when PostgreSQL is temporarily
# unavailable. Flask's default 500 page is HTML and causes JSON parse errors.
import psycopg2

@app.errorhandler(psycopg2.OperationalError)
def database_connection_unavailable(err):
    app.logger.warning("POSTGRES_CONNECTION_UNAVAILABLE: %s",type(err).__name__)
    return jsonify(ok=False,code="DATABASE_UNAVAILABLE",
        error="데이터베이스 연결이 일시적으로 불안정합니다. 기존 사진·영상과 투표 기록은 초기화되지 않았습니다. 잠시 후 새로고침해 다시 시도해주세요."),503

@app.errorhandler(500)
def api_internal_error(err):
    if request.path.startswith('/api/'):
        return jsonify(ok=False,code="SERVER_ERROR",
            error="일시적인 서버 오류입니다. 제출·투표가 저장됐는지 확인하려면 새로고침해 주세요."),500
    return err

@app.errorhandler(404)
def api_route_not_found(err):
    if request.path.startswith('/api/'):
        return jsonify(ok=False,code="API_NOT_FOUND",
            error="요청한 기능의 주소를 찾지 못했습니다. 페이지를 새로고침해 주세요."),404
    return err

def connect():
    if not IS_PG:
        raise RuntimeError('DATABASE_URL is required for persistent event voting')
    if IS_PG:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        c=psycopg2.connect(DATABASE_URL,connect_timeout=7,sslmode='require')
        c.autocommit=False
        return c
    import sqlite3
    c=sqlite3.connect('/tmp/gyeongbok_vote_event.db',timeout=10)
    c.row_factory=sqlite3.Row
    return c

def sql(q):
    return q.replace('?','%s') if IS_PG else q

def query(conn,q,args=(),all=False):
    cur=conn.cursor()
    cur.execute(sql(q),args)
    if cur.description:
        rows=cur.fetchall()
        headers=[x[0] for x in cur.description]
        data=[dict(zip(headers,r)) for r in rows]
        return data if all else (data[0] if data else None)
    return None

def init():
    c=connect()
    try:
        if IS_PG:
            query(c,"CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, vote_open BOOLEAN DEFAULT FALSE, reveal BOOLEAN DEFAULT FALSE)")
            query(c,"CREATE TABLE IF NOT EXISTS teams (team INTEGER PRIMARY KEY, photo_title TEXT DEFAULT '', video_title TEXT DEFAULT '', photo_data BYTEA, photo_type TEXT, video_data BYTEA, video_type TEXT, mission_score REAL DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS codes (code_hash TEXT PRIMARY KEY, team INTEGER NOT NULL, used BOOLEAN DEFAULT FALSE)")
            query(c,"CREATE TABLE IF NOT EXISTS votes (code_hash TEXT PRIMARY KEY, voter_team INTEGER NOT NULL, photo_team INTEGER NOT NULL, video_team INTEGER NOT NULL)")
            query(c,"CREATE TABLE IF NOT EXISTS public_votes (device_hash TEXT PRIMARY KEY, voter_team INTEGER NOT NULL, photo_team INTEGER NOT NULL, video_team INTEGER NOT NULL, absentee BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            # Repair initial anonymous table if a prior partial deploy created INTEGER absentee.
            dtype=query(c,"SELECT data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='public_votes' AND column_name='absentee'")
            if dtype and dtype["data_type"] in ("integer","smallint","bigint"):
                query(c,"ALTER TABLE public_votes ALTER COLUMN absentee DROP DEFAULT")
                query(c,"ALTER TABLE public_votes ALTER COLUMN absentee TYPE BOOLEAN USING (absentee <> 0)")
                query(c,"ALTER TABLE public_votes ALTER COLUMN absentee SET DEFAULT FALSE")
            query(c,"INSERT INTO settings(id) VALUES(1) ON CONFLICT DO NOTHING")
            for t in range(1,6):
                query(c,"INSERT INTO teams(team) VALUES(?) ON CONFLICT DO NOTHING",(t,))
        else:
            query(c,"CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, vote_open INTEGER DEFAULT 0, reveal INTEGER DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS teams (team INTEGER PRIMARY KEY, photo_title TEXT DEFAULT '', video_title TEXT DEFAULT '', photo_data BLOB, photo_type TEXT, video_data BLOB, video_type TEXT, mission_score REAL DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS codes (code_hash TEXT PRIMARY KEY, team INTEGER NOT NULL, used INTEGER DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS votes (code_hash TEXT PRIMARY KEY, voter_team INTEGER NOT NULL, photo_team INTEGER NOT NULL, video_team INTEGER NOT NULL)")
            query(c,"CREATE TABLE IF NOT EXISTS public_votes (device_hash TEXT PRIMARY KEY, voter_team INTEGER NOT NULL, photo_team INTEGER NOT NULL, video_team INTEGER NOT NULL, absentee INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
            query(c,"INSERT OR IGNORE INTO settings(id) VALUES(1)")
            for t in range(1,6):
                query(c,"INSERT OR IGNORE INTO teams(team) VALUES(?)",(t,))
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def h(s):return hashlib.sha256(s.encode()).hexdigest()
def admin_only(fn):
    @wraps(fn)
    def inner(*args,**kwargs):
        if not session.get('admin'):return jsonify(error='관리자 인증이 필요합니다.'),401
        return fn(*args,**kwargs)
    return inner


# An opaque browser cookie replaces manual voter-code entry.
# A person who clears browser data or switches devices can still vote again;
# true per-person eligibility is impossible without a credential or identity check.
VOTER_COOKIE="gb_event_voter_20261106"
VOTER_DEVICE_PATTERN=re.compile(r"^[A-Za-z0-9_-]{30,90}$")

@app.before_request
def prepare_voter_device():
    if request.path not in ('/', '/vote/absent', '/api/state', '/api/vote') and not request.path.startswith('/vote/team/'):
        return
    raw=request.cookies.get(VOTER_COOKIE,'')
    if VOTER_DEVICE_PATTERN.fullmatch(raw):
        g.voter_device=raw
        g.new_voter_cookie=False
    else:
        g.voter_device=secrets.token_urlsafe(32)
        g.new_voter_cookie=True

@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options']='nosniff'
    r.headers['Referrer-Policy']='same-origin'
    r.headers['Cache-Control']='no-store'
    if getattr(g,'new_voter_cookie',False):
        r.set_cookie(VOTER_COOKIE,g.voter_device,max_age=60*60*24*30,
            secure=True,httponly=True,samesite="Lax",path='/')
    return r

@app.route('/api/state')
def state():
    c=connect()
    try:
        s=query(c,"SELECT vote_open,reveal FROM settings WHERE id=1")
        ts=query(c,"SELECT team,photo_title,video_title,mission_score,photo_data IS NOT NULL AS photo,video_data IS NOT NULL AS video FROM teams ORDER BY team",all=True)
        # Published vote entries are automatically selected from real submissions,
        # even when an organizer never clicks Approve. Keep curated manual
        # photo/video uploads as preferred voting representatives.
        evidence=query(c,"""SELECT team,mission_code,mime FROM mission_submissions
            WHERE is_test=FALSE AND status<>'rejected'
              AND (mission_code='H04' OR mission_code IN ('V01','V02','V03'))""",all=True)
        photos={int(x["team"]) for x in evidence if x["mission_code"]=="H04" and str(x["mime"]).startswith("image/")}
        videos={int(x["team"]) for x in evidence if x["mission_code"] in ("V01","V02","V03") and str(x["mime"]).startswith("video/")}
        for t in ts:
            t["photo"]=bool(t["photo"] or int(t["team"]) in photos)
            t["video"]=bool(t["video"] or int(t["team"]) in videos)
        from scorecard import calculate_mission_scores
        auto_scores=calculate_mission_scores(c,query,ts)
        for t in ts:
            detail=auto_scores[int(t['team'])]
            t['mission_score']=detail['normalized']
            t['mission_raw']=detail['raw']
            t['completed_missions']=detail['completed']
        device_hash=h(g.voter_device)
        already=query(c,"SELECT device_hash FROM public_votes WHERE device_hash=?",(device_hash,))
        result={"status":"ok","admin":bool(session.get('admin')),"vote_open":bool(s['vote_open']),"reveal":bool(s['reveal']),"teams":ts,"database":'PostgreSQL' if IS_PG else '임시 저장소',"has_voted":bool(already),"automatic_mission_scoring":True}
        if session.get('admin') or s['reveal']:
            result['mission_breakdown']={str(t):v for t,v in auto_scores.items()}
            legacy=query(c,"SELECT photo_team,video_team FROM votes",all=True)
            current=query(c,"SELECT photo_team,video_team,voter_team,absentee FROM public_votes",all=True)
            ballots=legacy+current
            counts=query(c,"SELECT team, COUNT(*) AS count FROM codes GROUP BY team",all=True)
            used=query(c,"SELECT team, COUNT(*) AS count FROM codes WHERE used=TRUE GROUP BY team",all=True)
            absentee_count=sum(bool(v["absentee"]) for v in current)
            result['voting_summary']={'total':len(ballots),'absentee':absentee_count,
                'regular':len(ballots)-absentee_count,'new_votes':len(current),'previous_code_votes':len(legacy)}
            result['counts']={str(t):{'photo':sum(v['photo_team']==t for v in ballots),
                'video':sum(v['video_team']==t for v in ballots),
                'issued':next((x['count'] for x in counts if x['team']==t),0),
                'used':next((x['count'] for x in used if x['team']==t),0)} for t in range(1,6)}
        return jsonify(result)
    finally:c.close()

@app.route('/api/media/<int:team>/<kind>')
def media(team,kind):
    if team not in range(1,6) or kind not in ('photo','video'):return 'Not found',404
    c=connect()
    try:
        row=query(c,f"SELECT {kind}_data AS data,{kind}_type AS type FROM teams WHERE team=?",(team,))
        if not row or row['data'] is None:
            # Fall back to newest actual upload, without an approval gate.
            # Pull only the selected media bytes (not all team submissions).
            code_clause="mission_code='H04'" if kind=='photo' else "mission_code IN ('V01','V02','V03')"
            mime_pattern="image/%" if kind=='photo' else "video/%"
            row=query(c,"SELECT data,mime AS type FROM mission_submissions WHERE team=? "
                        "AND is_test=FALSE AND status<>'rejected' AND "+code_clause+
                        " AND mime LIKE ? ORDER BY id DESC LIMIT 1",(team,mime_pattern))
            if not row or row['data'] is None:return 'Not found',404
        from mobile import serve_media_bytes
        return serve_media_bytes(row['data'],row['type'] or ('image/jpeg' if kind=='photo' else 'video/mp4'))
    finally:c.close()

@app.post('/api/login')
def login():
    data=request.get_json(silent=True) or {}
    supplied=str(data.get('password',''))[:256]
    if not ADMIN_PASSWORD:return jsonify(error='운영진 암호 설정이 필요합니다.'),503
    if not hmac.compare_digest(supplied,ADMIN_PASSWORD):
        time.sleep(.35)
        return jsonify(error='암호가 일치하지 않습니다.'),401
    session.clear();session['admin']=True
    return jsonify(ok=True)

@app.post('/api/logout')
def logout():
    session.clear();return jsonify(ok=True)

@app.post('/api/vote')
def vote():
    d=request.get_json(silent=True) or {}
    try:
        photo,video=int(d.get('photo')),int(d.get('video'))
        voter_team=int(d.get('voter_team',0))
    except (ValueError,TypeError):
        return jsonify(error='사진·영상·소속 조를 선택해주세요.'),400
    absent=d.get('absent') is True
    if not (1<=photo<=5 and 1<=video<=5):
        return jsonify(error='사진과 영상에 각각 한 표씩 선택하세요.'),400
    if (absent and voter_team!=0) or (not absent and voter_team not in range(1,6)):
        return jsonify(error='참석자는 소속 조를 선택해주세요. 미참석자는 미참석자용 QR로 접속해주세요.'),400
    c=connect()
    try:
        qr_token=d.get('team_token')
        if qr_token is not None:
            if absent or not isinstance(qr_token,str) or len(qr_token)>100:
                return jsonify(error='조별 QR 투표 정보가 올바르지 않습니다.'),403
            from mobile import token_ok
            if not token_ok(c,query,voter_team,qr_token):
                return jsonify(error='본인 조 QR 접속 정보가 유효하지 않습니다.'),403
        if not absent and voter_team in (photo,video):
            return jsonify(error='자기 조에는 투표할 수 없습니다.'),400
        setting=query(c,"SELECT vote_open FROM settings WHERE id=1")
        if not setting['vote_open']:
            return jsonify(error='아직 투표가 시작되지 않았습니다.'),403
        key=h(g.voter_device)
        previous=query(c,"SELECT device_hash FROM public_votes WHERE device_hash=?",(key,))
        if previous:
            return jsonify(error='이 브라우저에서는 이미 투표했습니다.'),409
        entries=query(c,"SELECT team,photo_data IS NOT NULL AS photo,video_data IS NOT NULL AS video FROM teams WHERE team IN (?,?)",(photo,video),all=True)
        if not any(x['team']==photo and x['photo'] for x in entries) or not any(x['team']==video and x['video'] for x in entries):
            return jsonify(error='사진과 영상 모두 작품 등록이 완료된 조에 투표할 수 있습니다.'),400
        query(c,"INSERT INTO public_votes(device_hash,voter_team,photo_team,video_team,absentee) VALUES(?,?,?,?,?)",
            (key,voter_team,photo,video,absent))
        c.commit()
        return jsonify(ok=True,absentee=absent)
    except psycopg2.OperationalError:
        try:c.rollback()
        except Exception:pass
        return jsonify(ok=False,code="DATABASE_UNAVAILABLE",
          error="데이터베이스 연결 장애로 투표 완료 여부를 확인하지 못했습니다. 잠시 후 새로고침하여 이미 투표했는지 확인하세요."),503
    except Exception:
        c.rollback()
        return jsonify(error='투표가 이미 제출되었거나 일시적으로 처리하지 못했습니다. 새로고침 후 확인해주세요.'),409
    finally:c.close()

@app.post('/api/admin/settings')
@admin_only
def settings():
    d=request.get_json(silent=True) or {}
    if d.get('key') not in ('vote_open','reveal') or type(d.get('value')) is not bool:return jsonify(error='잘못된 설정'),400
    c=connect()
    try:
        query(c,f"UPDATE settings SET {d['key']}=? WHERE id=1",(d['value'],))
        c.commit();return jsonify(ok=True)
    finally:c.close()

@app.post('/api/admin/team')
@admin_only
def team():
    d=request.get_json(silent=True) or {}
    try:
        t=int(d.get('team',0))
    except (ValueError,TypeError):
        return jsonify(error='조 선택 오류'),400
    if t not in range(1,6):return jsonify(error='조 선택 오류'),400
    p=str(d.get('photo_title',''))[:80]
    v=str(d.get('video_title',''))[:80]
    c=connect()
    try:
        # Never change historical manual score: the active mission score is
        # calculated from review approvals whenever /api/state is requested.
        query(c,"UPDATE teams SET photo_title=?,video_title=? WHERE team=?",(p,v,t))
        c.commit()
        return jsonify(ok=True,automatic_mission_scoring=True)
    finally:c.close()

@app.post('/api/admin/upload')
@admin_only
def upload():
    try:t=int(request.form.get('team','0'))
    except:t=0
    kind=request.form.get('kind')
    f=request.files.get('file')
    if t not in range(1,6) or kind not in ('photo','video') or not f:return jsonify(error='업로드 정보 오류'),400
    allowed=('image/jpeg','image/png','image/webp') if kind=='photo' else ('video/mp4','video/webm')
    maxsize=7*1024*1024 if kind=='photo' else 35*1024*1024
    content=f.read(maxsize+1)
    if f.mimetype not in allowed or len(content)>maxsize:return jsonify(error='사진은 7MB, 영상은 35MB 이하의 JPG/PNG/WEBP 또는 MP4/WEBM만 허용됩니다.'),400
    c=connect()
    try:
        query(c,f"UPDATE teams SET {kind}_data=?,{kind}_type=? WHERE team=?",(content,f.mimetype,t));c.commit()
        return jsonify(ok=True)
    finally:c.close()

@app.post('/api/admin/codes')
@admin_only
def codes():
    d=request.get_json(silent=True) or {}
    try:t=int(d.get('team',0));n=int(d.get('count',0))
    except:return jsonify(error='입력 오류'),400
    if t not in range(1,6) or not 1<=n<=50:return jsonify(error='조별 1~50개씩 발급할 수 있습니다.'),400
    new=[secrets.token_hex(6).upper() for _ in range(n)]
    c=connect()
    try:
        for code in new:query(c,"INSERT INTO codes(code_hash,team) VALUES(?,?)",(h(code),t))
        c.commit();return jsonify(ok=True,codes=new)
    finally:c.close()

@app.get('/api/admin/absent-qr.png')
@admin_only
def absent_qr():
    import qrcode
    from urllib.parse import urljoin
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=12,border=4)
    qr.add_data(urljoin(request.host_url,'vote/absent'))
    qr.make(fit=True)
    out=io.BytesIO()
    qr.make_image(fill_color="#173449",back_color="white").save(out,'PNG')
    return Response(out.getvalue(),mimetype='image/png',
        headers={'Content-Disposition':'attachment; filename="absentee-voting-QR.png"'})

@app.get('/healthz')
def health():
    try:
        c=connect();query(c,'SELECT 1');c.close();return jsonify(ok=True,db='postgres' if IS_PG else 'temporary')
    except:return jsonify(ok=False),503

@app.get('/')
def home():
    return render_template_string(PAGE)

@app.get('/vote/absent')
def absent_vote_home():
    return render_template_string(PAGE)

@app.get('/vote/team/<int:team>/<token>')
def team_vote_home(team,token):
    from mobile import token_ok
    c=connect()
    try:
        if not token_ok(c,query,team,token):
            return '유효하지 않은 조별 QR입니다. 배포받은 미션 QR로 다시 접속해 주세요.',403
    finally:
        c.close()
    return render_template_string(PAGE)

PAGE = """
<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>경복궁 힐링데이 투표</title><style>
:root{font-family:"Malgun Gothic","Apple SD Gothic Neo",sans-serif;color:#172e43;background:#eef2f4}*{box-sizing:border-box}body{margin:0}.wrap{max-width:920px;margin:auto;padding:0 19px}header{display:flex;align-items:center;justify-content:space-between;padding:21px 0;border-bottom:1px solid #c9d8df;gap:8px}header strong{font-size:17px}nav{display:flex;gap:5px}nav button{border:0;background:transparent;padding:10px;color:#617889;border-radius:9px}nav button.on{background:#21485d;color:white}h1{font-size:clamp(35px,7vw,60px);letter-spacing:-.06em;line-height:1.18;margin:17px 0}h1 span{color:#42748b}.intro{padding:37px 0}.intro p{color:#768998;line-height:1.7}.tag{font-size:11px;color:#916d45;letter-spacing:.16em;font-weight:bold}.box{background:white;border:1px solid #d6e0e5;border-radius:17px;padding:26px;margin-bottom:35px;box-shadow:0 10px 45px #0e30450a}h2{font-size:21px;letter-spacing:-.04em}small,.muted{color:#8494a0}.divider{border-top:1px solid #e0e8ec;margin:25px 0}.teams{display:flex;gap:9px}.teams button{flex:1;padding:15px 0;border:1px solid #d7e0e5;border-radius:10px;background:#f6f9fa;color:#3a6073;font-weight:800}.teams button.sel{background:#21485d;color:white}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.item{border:2px solid #dce5e9;border-radius:12px;overflow:hidden;background:white}.item.pick{border-color:#32738b}.media{height:167px;background:#e9eff2;display:flex;align-items:center;justify-content:center;color:#94a6b1;font-size:14px}.media img,.media video{height:100%;width:100%;object-fit:contain;background:#102433}.item button{width:100%;padding:13px;border:0;background:white;text-align:left;font:inherit;font-weight:bold;color:#254b62;display:flex;justify-content:space-between;gap:8px}.item button:disabled{opacity:.5}.item small{display:block;font-weight:400;margin-top:5px;font-size:11px}.primary{padding:15px 24px;background:#214c63;color:white;border:0;border-radius:11px;font-size:15px;font-weight:bold;cursor:pointer}.primary:disabled{opacity:.4;cursor:default}.full{width:100%}input,select{border:1px solid #cddbe3;padding:13px;border-radius:9px;font-size:15px;max-width:100%;background:#f9fbfc;color:#234359}input{width:100%}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.note{font-size:12px;color:#748a99;line-height:1.7}.ok{padding:25px;text-align:center;font-size:21px;font-weight:bold;color:#276f60}.msg{background:#fff0dc;border:1px solid #ead5b0;color:#805832;padding:14px;border-radius:11px;margin-bottom:16px}.adminteam{border:1px solid #dbe5e9;padding:18px;border-radius:12px;margin:12px 0}.adminteam label{display:block;font-size:12px;color:#647d8b;margin:10px 0 5px}.adminteam input{margin-bottom:8px}.mini{border:1px solid #bfd0d9;border-radius:9px;background:#eaf2f5;color:#2d5e75;padding:11px;font-size:12px;font-weight:bold;cursor:pointer}.rank{display:flex;align-items:center;padding:16px;border-bottom:1px solid #dde7eb;gap:12px}.rank>strong{min-width:45px;font-size:22px;color:#457489}.rank span{flex:1}.rank b{font-size:22px}.badge{background:#e5f1ed;color:#32816d;border-radius:30px;padding:8px 12px;font-size:12px}.foot{padding:25px 0;color:#8294a0;font-size:11px;border-top:1px solid #d5e1e5}button{cursor:pointer}button:disabled{cursor:default}#result,#admin{display:none}@media(min-width:720px){.media{height:235px}}@media(max-width:430px){.box{padding:19px}.teams button{padding:13px 0}.media{height:130px}nav button{font-size:12px;padding:8px}header strong{font-size:14px}.row>*{min-width:0}} 
</style></head><body><div class="wrap"><header><strong>宮 경복궁 힐링데이</strong><nav><button onclick="tab('vote')" id="nav-vote" class="on">투표</button><button onclick="tab('result')" id="nav-result">결과</button><button onclick="tab('admin')" id="nav-admin">운영진</button></nav></header><div class="intro"><div class="tag">2026 · GYEONGBOKGUNG · TEAM AWARDS</div><h1>우리들의 하루,<br><span>최고의 한 장면</span></h1><p>우리 조를 제외하고 가장 멋진 사진 한 장과<br>가장 재미있는 영상 하나를 뽑아주세요.</p><div id="vote-status" class="badge">투표 대기 중</div></div>
<div id="msg"></div>
<section id="vote" class="box"><div id="thank" style="display:none" class="ok">✓ 투표가 완료되었습니다!<p class="note">소중한 한 표 감사합니다.</p></div><div id="votebody">
<div id="absent-banner" style="display:none;background:#eaf3f7;border:1px solid #b9d3e2;padding:17px;border-radius:12px;margin:0 0 18px"><strong style="color:#24536b">🏠 미참석자 전용 투표</strong><p class="note">행사에 참석하지 않은 직원도 사진 1표와 영상 1표를 투표할 수 있습니다. 소속 조 선택은 필요하지 않습니다.</p></div>
<div id="auto-team-banner" style="display:none;background:#e8f3ed;border:1px solid #afcfc1;padding:17px;border-radius:12px;margin:0 0 18px"><strong style="color:#24614b" id="auto-team-name">조별 QR 자동 인증</strong><p class="note">내 조는 자동으로 선택되었습니다. 내 조의 사진·영상에는 투표할 수 없습니다.</p><a id="return-mission" href="/" style="font-size:12px;font-weight:700;color:#24614b">← 우리 조 미션으로 돌아가기</a></div>
<div id="team-panel"><h2>01. 나의 조 선택</h2><p class="muted">자기 조에는 투표할 수 없습니다. 미참석자는 <a href="/vote/absent">미참석자 투표</a>로 이동하세요.</p><div class="teams" id="myteams"></div><div class="divider"></div></div>
<h2>02. 베스트 포토</h2><p class="muted">사진 한 장을 선택하세요.</p><div class="grid" id="photos"></div><div class="divider"></div>
<h2>03. 베스트 영상</h2><p class="muted">영상을 보고 한 개를 선택하세요.</p><div class="grid" id="videos"></div><div class="divider"></div>
<h2>04. 투표 확정</h2><p class="note">사진과 영상에 각 1표씩 선택하세요. 별도 투표코드는 필요하지 않습니다. 이 브라우저에서는 1회만 투표할 수 있습니다.</p><button class="primary full" id="submit" onclick="vote()" disabled>투표 시작 전입니다</button>
</div></section>
<section id="result" class="box"><h2>종합 순위</h2><p class="muted">미션 70점 + 사진 10점 + 영상 20점</p><div id="result-body">운영진이 공개한 뒤 볼 수 있습니다.</div></section>
<section id="admin" class="box"><div id="login"><h2>운영진 로그인</h2><p class="muted">참가자는 로그인할 필요가 없습니다.</p><input type="password" id="password" placeholder="관리자 비밀번호"><p><button class="primary full" onclick="login()">관리자 로그인</button></p></div>
<div id="admin-body" style="display:none"><a href="/admin/mission" style="display:block;background:#dceee8;color:#234c62;padding:15px;text-align:center;border-radius:10px;font-weight:bold;margin-bottom:18px;text-decoration:none">🏯 조별 미션 · QR 발급 · 사진·영상 검수 관리 ↗</a><h2>행사 운영</h2><div id="dbstate" class="note"></div><p class="row"><button class="mini" onclick="setting('vote_open')">투표 시작 / 종료</button><button class="mini" onclick="setting('reveal')">결과 공개 / 비공개</button><button class="mini" onclick="logout()">로그아웃</button></p><p id="toggles"></p><h2>조별 작품 등록</h2><div id="admteams"></div>
<h2>미참석자 투표</h2><p class="note">미참석 직원에게 전용 QR을 배포하세요. 이 주소를 공유하면 조 선택·투표코드 입력 없이 참여할 수 있습니다.</p><div class="row"><a class="mini" href="/vote/absent" target="_blank" rel="noopener" style="text-decoration:none">미참석자 투표 화면 열기</a><a class="mini" href="/api/admin/absent-qr.png" download style="text-decoration:none">미참석자 QR PNG 저장</a></div>
</div></section>
<footer class="foot">2026 HEALING DAY · PRIVATE EVENT VOTING</footer></div>
<script src="/static/vote.js" defer></script></body></html>
"""

# Secure QR team missions; the existing vote service remains unchanged.
from mobile import mission_bp, init_missions
from exports import export_bp
app.register_blueprint(mission_bp)
app.register_blueprint(export_bp)

if __name__=='__main__':
    init()
    init_missions()
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))
else:
    # The existing production database is already initialized. During brief
    # Render Postgres DNS/availability outages, keep the web process running
    # so it can resume using that SAME database as soon as it returns.
    # Never fall back to transient SQLite or create a replacement database.
    try:
        init()
        init_missions()
        print('EVENT_PERSISTENT_POSTGRES_READY: schema initialized', flush=True)
    except psycopg2.OperationalError:
        print('EVENT_POSTGRES_STARTUP_DEFERRED: existing database temporarily unavailable; '
              'web process remains online and database-backed requests return 503 until recovery',
              flush=True)
