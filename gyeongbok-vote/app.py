import os, io, json, re, time, hashlib, secrets, hmac
from functools import wraps
from flask import Flask, request, jsonify, session, render_template_string, Response
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=55*1024*1024)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
DATABASE_URL=os.environ.get("DATABASE_URL","")
ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD","")
IS_PG=bool(DATABASE_URL)

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
            query(c,"INSERT INTO settings(id) VALUES(1) ON CONFLICT DO NOTHING")
            for t in range(1,6):query(c,"INSERT INTO teams(team) VALUES(?) ON CONFLICT DO NOTHING",(t,))
        else:
            query(c,"CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, vote_open INTEGER DEFAULT 0, reveal INTEGER DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS teams (team INTEGER PRIMARY KEY, photo_title TEXT DEFAULT '', video_title TEXT DEFAULT '', photo_data BLOB, photo_type TEXT, video_data BLOB, video_type TEXT, mission_score REAL DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS codes (code_hash TEXT PRIMARY KEY, team INTEGER NOT NULL, used INTEGER DEFAULT 0)")
            query(c,"CREATE TABLE IF NOT EXISTS votes (code_hash TEXT PRIMARY KEY, voter_team INTEGER NOT NULL, photo_team INTEGER NOT NULL, video_team INTEGER NOT NULL)")
            query(c,"INSERT OR IGNORE INTO settings(id) VALUES(1)")
            for t in range(1,6):query(c,"INSERT OR IGNORE INTO teams(team) VALUES(?)",(t,))
        c.commit()
    finally:c.close()

def h(s):return hashlib.sha256(s.encode()).hexdigest()
def admin_only(fn):
    @wraps(fn)
    def inner(*args,**kwargs):
        if not session.get('admin'):return jsonify(error='관리자 인증이 필요합니다.'),401
        return fn(*args,**kwargs)
    return inner

@app.after_request
def headers(r):
    r.headers['X-Content-Type-Options']='nosniff'
    r.headers['Referrer-Policy']='same-origin'
    r.headers['Cache-Control']='no-store'
    return r

@app.route('/api/state')
def state():
    c=connect()
    try:
        s=query(c,"SELECT vote_open,reveal FROM settings WHERE id=1")
        ts=query(c,"SELECT team,photo_title,video_title,mission_score,photo_data IS NOT NULL AS photo,video_data IS NOT NULL AS video FROM teams ORDER BY team",all=True)
        result={"status":"ok","admin":bool(session.get('admin')),"vote_open":bool(s['vote_open']),"reveal":bool(s['reveal']),"teams":ts,"database":'PostgreSQL' if IS_PG else '임시 저장소'}
        if session.get('admin') or s['reveal']:
            ballots=query(c,"SELECT photo_team,video_team FROM votes",all=True)
            counts=query(c,"SELECT team, COUNT(*) AS count FROM codes GROUP BY team",all=True)
            used=query(c,"SELECT team, COUNT(*) AS count FROM codes WHERE used=TRUE GROUP BY team",all=True)
            result['counts']={str(t):{'photo':sum(v['photo_team']==t for v in ballots),'video':sum(v['video_team']==t for v in ballots),'issued':next((x['count'] for x in counts if x['team']==t),0),'used':next((x['count'] for x in used if x['team']==t),0)} for t in range(1,6)}
        return jsonify(result)
    finally:c.close()

@app.route('/api/media/<int:team>/<kind>')
def media(team,kind):
    if team not in range(1,6) or kind not in ('photo','video'):return 'Not found',404
    c=connect()
    try:
        row=query(c,f"SELECT {kind}_data AS data,{kind}_type AS type FROM teams WHERE team=?",(team,))
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
    try:photo,video=int(d.get('photo')),int(d.get('video'))
    except:return jsonify(error='사진과 영상을 선택하세요.'),400
    code=re.sub(r'[^A-Z0-9]','',str(d.get('code','')).upper())
    if len(code)!=12 or not 1<=photo<=5 or not 1<=video<=5:return jsonify(error='선택과 투표코드를 확인해주세요.'),400
    c=connect()
    try:
        s=query(c,"SELECT vote_open FROM settings WHERE id=1")
        if not s['vote_open']:return jsonify(error='아직 투표가 시작되지 않았습니다.'),403
        if IS_PG:row=query(c,"SELECT team,used FROM codes WHERE code_hash=? FOR UPDATE",(h(code),))
        else:row=query(c,"SELECT team,used FROM codes WHERE code_hash=?",(h(code),))
        if not row:return jsonify(error='등록되지 않은 투표코드입니다.'),403
        if row['used']:return jsonify(error='이미 사용한 투표코드입니다.'),409
        if row['team'] in (photo,video):return jsonify(error='자기 조에는 투표할 수 없습니다.'),400
        entries=query(c,"SELECT team,photo_data IS NOT NULL AS photo, video_data IS NOT NULL AS video FROM teams WHERE team IN (?,?)",(photo,video),all=True)
        if not any(x['team']==photo and x['photo'] for x in entries) or not any(x['team']==video and x['video'] for x in entries):
            return jsonify(error='작품 등록이 완료된 조에만 투표할 수 있습니다.'),400
        query(c,"INSERT INTO votes(code_hash,voter_team,photo_team,video_team) VALUES(?,?,?,?)",(h(code),row['team'],photo,video))
        query(c,"UPDATE codes SET used=TRUE WHERE code_hash=?",(h(code),))
        c.commit()
        return jsonify(ok=True)
    except Exception:
        c.rollback();return jsonify(error='중복 투표 또는 일시적인 처리 오류입니다.'),409
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
    try:t=int(d.get('team',0));score=float(d.get('score',0))
    except:return jsonify(error='입력값 오류'),400
    if t not in range(1,6) or not 0<=score<=70:return jsonify(error='조 또는 점수를 확인하세요.'),400
    p=str(d.get('photo_title',''))[:80];v=str(d.get('video_title',''))[:80]
    c=connect()
    try:
        query(c,"UPDATE teams SET photo_title=?,video_title=?,mission_score=? WHERE team=?",(p,v,score,t));c.commit()
        return jsonify(ok=True)
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

@app.get('/healthz')
def health():
    try:
        c=connect();query(c,'SELECT 1');c.close();return jsonify(ok=True,db='postgres' if IS_PG else 'temporary')
    except:return jsonify(ok=False),503

@app.get('/')
def home():
    return render_template_string(PAGE)

PAGE = """
<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>경복궁 힐링데이 투표</title><style>
:root{font-family:"Malgun Gothic","Apple SD Gothic Neo",sans-serif;color:#172e43;background:#eef2f4}*{box-sizing:border-box}body{margin:0}.wrap{max-width:920px;margin:auto;padding:0 19px}header{display:flex;align-items:center;justify-content:space-between;padding:21px 0;border-bottom:1px solid #c9d8df;gap:8px}header strong{font-size:17px}nav{display:flex;gap:5px}nav button{border:0;background:transparent;padding:10px;color:#617889;border-radius:9px}nav button.on{background:#21485d;color:white}h1{font-size:clamp(35px,7vw,60px);letter-spacing:-.06em;line-height:1.18;margin:17px 0}h1 span{color:#42748b}.intro{padding:37px 0}.intro p{color:#768998;line-height:1.7}.tag{font-size:11px;color:#916d45;letter-spacing:.16em;font-weight:bold}.box{background:white;border:1px solid #d6e0e5;border-radius:17px;padding:26px;margin-bottom:35px;box-shadow:0 10px 45px #0e30450a}h2{font-size:21px;letter-spacing:-.04em}small,.muted{color:#8494a0}.divider{border-top:1px solid #e0e8ec;margin:25px 0}.teams{display:flex;gap:9px}.teams button{flex:1;padding:15px 0;border:1px solid #d7e0e5;border-radius:10px;background:#f6f9fa;color:#3a6073;font-weight:800}.teams button.sel{background:#21485d;color:white}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.item{border:2px solid #dce5e9;border-radius:12px;overflow:hidden;background:white}.item.pick{border-color:#32738b}.media{height:167px;background:#e9eff2;display:flex;align-items:center;justify-content:center;color:#94a6b1;font-size:14px}.media img,.media video{height:100%;width:100%;object-fit:contain;background:#102433}.item button{width:100%;padding:13px;border:0;background:white;text-align:left;font:inherit;font-weight:bold;color:#254b62;display:flex;justify-content:space-between;gap:8px}.item button:disabled{opacity:.5}.item small{display:block;font-weight:400;margin-top:5px;font-size:11px}.primary{padding:15px 24px;background:#214c63;color:white;border:0;border-radius:11px;font-size:15px;font-weight:bold;cursor:pointer}.primary:disabled{opacity:.4;cursor:default}.full{width:100%}input,select{border:1px solid #cddbe3;padding:13px;border-radius:9px;font-size:15px;max-width:100%;background:#f9fbfc;color:#234359}input{width:100%}.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.note{font-size:12px;color:#748a99;line-height:1.7}.ok{padding:25px;text-align:center;font-size:21px;font-weight:bold;color:#276f60}.msg{background:#fff0dc;border:1px solid #ead5b0;color:#805832;padding:14px;border-radius:11px;margin-bottom:16px}.adminteam{border:1px solid #dbe5e9;padding:18px;border-radius:12px;margin:12px 0}.adminteam label{display:block;font-size:12px;color:#647d8b;margin:10px 0 5px}.adminteam input{margin-bottom:8px}.mini{border:1px solid #bfd0d9;border-radius:9px;background:#eaf2f5;color:#2d5e75;padding:11px;font-size:12px;font-weight:bold;cursor:pointer}.rank{display:flex;align-items:center;padding:16px;border-bottom:1px solid #dde7eb;gap:12px}.rank>strong{min-width:45px;font-size:22px;color:#457489}.rank span{flex:1}.rank b{font-size:22px}.badge{background:#e5f1ed;color:#32816d;border-radius:30px;padding:8px 12px;font-size:12px}.foot{padding:25px 0;color:#8294a0;font-size:11px;border-top:1px solid #d5e1e5}button{cursor:pointer}button:disabled{cursor:default}#result,#admin{display:none}@media(min-width:720px){.media{height:235px}}@media(max-width:430px){.box{padding:19px}.teams button{padding:13px 0}.media{height:130px}nav button{font-size:12px;padding:8px}header strong{font-size:14px}.row>*{min-width:0}} 
</style></head><body><div class="wrap"><header><strong>宮 경복궁 힐링데이</strong><nav><button onclick="tab('vote')" id="nav-vote" class="on">투표</button><button onclick="tab('result')" id="nav-result">결과</button><button onclick="tab('admin')" id="nav-admin">운영진</button></nav></header><div class="intro"><div class="tag">2026 · GYEONGBOKGUNG · TEAM AWARDS</div><h1>우리들의 하루,<br><span>최고의 한 장면</span></h1><p>우리 조를 제외하고 가장 멋진 사진 한 장과<br>가장 재미있는 영상 하나를 뽑아주세요.</p><div id="vote-status" class="badge">투표 대기 중</div></div>
<div id="msg"></div>
<section id="vote" class="box"><div id="thank" style="display:none" class="ok">✓ 투표가 완료되었습니다!<p class="note">소중한 한 표 감사합니다.</p></div><div id="votebody">
<h2>01. 나의 조 선택</h2><p class="muted">자기 조에는 투표할 수 없습니다.</p><div class="teams" id="myteams"></div><div class="divider"></div>
<h2>02. 베스트 포토</h2><p class="muted">사진 한 장을 선택하세요.</p><div class="grid" id="photos"></div><div class="divider"></div>
<h2>03. 베스트 영상</h2><p class="muted">영상을 보고 한 개를 선택하세요.</p><div class="grid" id="videos"></div><div class="divider"></div>
<h2>04. 투표코드 입력</h2><p class="muted">운영진이 배부한 1회용 코드를 입력하세요.</p><input placeholder="투표코드 12자리" id="code" maxlength="20" autocomplete="off"><p class="note">사진과 영상 각각 한 표씩 선택하고 완료 버튼을 눌러주세요.</p><button class="primary full" id="submit" onclick="vote()" disabled>투표 시작 전입니다</button>
</div></section>
<section id="result" class="box"><h2>종합 순위</h2><p class="muted">미션 70점 + 사진 10점 + 영상 20점</p><div id="result-body">운영진이 공개한 뒤 볼 수 있습니다.</div></section>
<section id="admin" class="box"><div id="login"><h2>운영진 로그인</h2><p class="muted">참가자는 로그인할 필요가 없습니다.</p><input type="password" id="password" placeholder="관리자 비밀번호"><p><button class="primary full" onclick="login()">관리자 로그인</button></p></div>
<div id="admin-body" style="display:none"><a href="/admin/mission" style="display:block;background:#dceee8;color:#234c62;padding:15px;text-align:center;border-radius:10px;font-weight:bold;margin-bottom:18px;text-decoration:none">🏯 조별 미션 · QR 발급 · 사진·영상 검수 관리 ↗</a><h2>행사 운영</h2><div id="dbstate" class="note"></div><p class="row"><button class="mini" onclick="setting('vote_open')">투표 시작 / 종료</button><button class="mini" onclick="setting('reveal')">결과 공개 / 비공개</button><button class="mini" onclick="logout()">로그아웃</button></p><p id="toggles"></p><h2>조별 작품 등록</h2><div id="admteams"></div>
<h2>일회용 투표코드</h2><p class="note">참가자 1인당 1개씩 발급합니다. 코드는 최초 발급 화면에서만 확인할 수 있으니 저장하세요.</p><div class="row"><select id="codeteam"><option value="1">1조</option><option value="2">2조</option><option value="3">3조</option><option value="4">4조</option><option value="5">5조</option></select><input type="number" id="codecount" value="6" min="1" max="50" style="width:85px"><button class="mini" onclick="codes()">코드 발급</button></div><div id="codes"></div>
</div></section>
<footer class="foot">2026 HEALING DAY · PRIVATE EVENT VOTING</footer></div>
<script src="/static/vote.js" defer></script></body></html>
"""

# Secure QR team missions; the existing vote service remains unchanged.
from mobile import mission_bp, init_missions
app.register_blueprint(mission_bp)

if __name__=='__main__':
    init()
    init_missions()
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','10000')))
else:
    # Gunicorn: fail startup when persistent PostgreSQL is not ready.
    init()
    init_missions()
    print('EVENT_PERSISTENT_POSTGRES_READY: schema initialized', flush=True)
