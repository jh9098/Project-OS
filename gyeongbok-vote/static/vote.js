const absentMode=window.location.pathname==='/vote/absent';
const teamQRMatch=window.location.pathname.match(/^\/vote\/team\/([1-5])\/([A-Za-z0-9_-]{24,60})$/);
const qrTeam=teamQRMatch?Number(teamQRMatch[1]):0;
const qrToken=teamQRMatch?teamQRMatch[2]:null;
let state=null,my=absentMode?6:qrTeam,photo=0,video=0,finished=false;
let lastPhotoMarkup=null,lastVideoMarkup=null;
let offlineMode=false,pendingSyncBusy=false;
const PENDING_VOTE_KEY='gyeongbok-20261106-pending-ballot';
const LAST_STATE_KEY='gyeongbok-20261106-last-voting-state';
function safeLocalGet(key){try{return JSON.parse(localStorage.getItem(key)||'null')}catch{return null}}
function safeLocalRemove(key){try{localStorage.removeItem(key)}catch{}}
function pendingVote(){const p=safeLocalGet(PENDING_VOTE_KEY);
  return p&&Date.now()-Number(p.at||0)<86400000?p:null;
}
function queueVote(payload){
  const safe={voter_team:payload.voter_team,absent:payload.absent,
    photo:payload.photo,video:payload.video,needs_qr:!!payload.team_token,at:Date.now()};
  try{
    localStorage.setItem(PENDING_VOTE_KEY,JSON.stringify(safe));
    return true;
  }catch{return false}
}
function savePublicSnapshot(s){
  const snapshot={at:Date.now(),data:{
    teams:s.teams.map(t=>({team:t.team,photo:t.photo,video:t.video,
      photo_title:t.photo_title,video_title:t.video_title,mission_score:t.mission_score})),
    vote_open:!!s.vote_open,reveal:false,admin:false,has_voted:false,
    automatic_mission_scoring:true
  }};
  try{localStorage.setItem(LAST_STATE_KEY,JSON.stringify(snapshot))}catch{}
}
function loadPublicSnapshot(){
  const snap=safeLocalGet(LAST_STATE_KEY);
  if(!snap||Date.now()-Number(snap.at||0)>3600000||!snap.data?.teams?.length)return null;
  return snap.data;
}
function pendingNotice(){return '⚠ 이 기기에만 투표 선택을 임시 저장했습니다. 아직 서버에 접수되지 않았습니다. 연결 회복 시 자동 전송합니다. 브라우저 데이터를 삭제하지 마세요.';}

const $=id=>document.getElementById(id),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function notify(s){$('msg').innerHTML=s?'<div class="msg">'+esc(s)+'</div>':'';}
async function readJsonResponse(r){
  const contentType=(r.headers.get('Content-Type')||'').toLowerCase();
  if(!contentType.includes('application/json')){
    const e=Error(r.status>=500?
      '서버 또는 데이터베이스가 일시적으로 응답하지 않습니다. 기존 기록은 삭제되지 않았습니다. 새로고침 후 확인해주세요.':
      '서버 응답이 올바르지 않습니다. 새로고침해 주세요. (HTTP '+r.status+')');
    e.retryable=r.status>=500;
    throw e;
  }
  let j;
  try{j=await r.json()}catch{throw Error('서버 데이터가 불완전합니다. 새로고침해 주세요.');}
  if(!r.ok||j.error){
    const e=Error(j.error||'처리 오류 (HTTP '+r.status+')');
    e.retryable=r.status>=500;
    throw e;
  }
  return j;
}
async function api(path,data,files=false){
  const r=await fetch(path,{method:'POST',
    headers:files?{}:{'Content-Type':'application/json'},
    body:files?data:JSON.stringify(data),credentials:'same-origin'});
  return readJsonResponse(r);
}
function tab(t){['vote','result','admin'].forEach(x=>{$(x).style.display=x===t?'block':'none';$('nav-'+x).classList.toggle('on',x===t)});refresh();}
async function flushPendingVote(){
  const q=pendingVote();
  if(!q||pendingSyncBusy||!state?.vote_open||state?.has_voted)return;
  if(q.needs_qr&&(!qrToken||qrTeam!==q.voter_team))return;
  pendingSyncBusy=true;
  const payload={voter_team:q.voter_team,absent:q.absent,
    photo:q.photo,video:q.video,team_token:q.needs_qr?qrToken:null};
  try{
    await api('/api/vote',payload);
    safeLocalRemove(PENDING_VOTE_KEY);
    finished=true;offlineMode=false;
    notify('✅ 임시 저장된 투표가 서버에 정상 접수됐습니다.');
    render();
  }catch(e){
    if(e.message.includes('이미 투표')){
      safeLocalRemove(PENDING_VOTE_KEY);
      finished=true;
      notify('기존 투표 접수가 확인됐습니다.');
      render();
    }else if(!e.retryable){
      // Do not replay an invalid, closed, or self-team ballot forever.
      notify('임시 투표 재전송 불가: '+e.message+' 운영진에게 확인해주세요.');
    }else notify(pendingNotice());
  }finally{pendingSyncBusy=false}
}
async function refresh(){
  try{
    const r=await fetch('/api/state',{cache:'no-store'});
    const nextState=await readJsonResponse(r);
    state=nextState;
    offlineMode=false;
    savePublicSnapshot(state);
    if(state.has_voted){
      safeLocalRemove(PENDING_VOTE_KEY);
      finished=true;
    }
    render();
    if(pendingVote()){
      notify('임시 보관된 투표가 있습니다. 서버 접수 여부를 확인하고 있습니다.');
      await flushPendingVote();
    }else notify('');
  }catch(e){
    offlineMode=true;
    if(!state)state=loadPublicSnapshot();
    if(state){render();notify(pendingVote()?pendingNotice():
      '데이터베이스 연결이 일시적으로 불안정합니다. 이전에 확인된 후보 목록만 표시됩니다. 서버 접수 여부는 아직 확인할 수 없습니다.');}
    else notify('연결 오류: '+e.message+' 기존 데이터는 삭제되지 않았습니다.');
    const status=$('vote-status');
    if(status)status.textContent='● DB 연결 불안정 · 서버 접수 확인 불가';
  }
}
function render(){if(!state)return;
 $('vote-status').textContent=offlineMode?'● DB 연결 불안정 · 기기 임시저장 가능':
    (state.vote_open?'● 투표 진행 중':'● 투표 대기 또는 종료');
 if(state.has_voted)finished=true;
 $('team-panel').style.display=absentMode||qrTeam?'none':'block';
 $('absent-banner').style.display=absentMode?'block':'none';
 $('auto-team-banner').style.display=qrTeam?'block':'none';
 if(qrTeam){
   $('auto-team-name').textContent='✓ '+qrTeam+'조 자동 선택 완료';
   $('return-mission').href='/mission/'+qrTeam+'/'+encodeURIComponent(qrToken);
 }
 $('myteams').innerHTML=[1,2,3,4,5].map(t=>'<button class="'+(my===t?'sel':'')+'" onclick="setmy('+t+')">'+t+'조</button>').join('');
 const list=type=>state.teams.filter(t=>t.team!==my).map(t=>'<div class="item '+((type==='photo'?photo:video)===t.team?'pick':'')+'"><div class="media">'+(t[type]?type==='photo'?'<img alt="'+t.team+'조 사진" src="/api/media/'+t.team+'/photo?v='+t.photo_title.length+'">':'<video controls playsinline preload="none" src="/api/media/'+t.team+'/video"></video>':'작품 준비 중')+'</div><button '+(!my||!t[type]?'disabled':'')+' onclick="pick(\''+type+'\','+t.team+')"><span>'+t.team+'조 <small>'+esc(t[type+'_title']||'경복궁 작품')+'</small></span><b>'+((type==='photo'?photo:video)===t.team?'✓':'○')+'</b></button></div>').join('');
 const photoMarkup=list('photo'),videoMarkup=list('video');
 if(photoMarkup!==lastPhotoMarkup){$('photos').innerHTML=photoMarkup;lastPhotoMarkup=photoMarkup;}
 if(videoMarkup!==lastVideoMarkup){$('videos').innerHTML=videoMarkup;lastVideoMarkup=videoMarkup;}
 $('submit').disabled=!state.vote_open||!my||!photo||!video||finished||!!pendingVote();
 $('submit').textContent=state.vote_open?(offlineMode?'연결 복구 후 접수 · 기기에 임시저장':'사진·영상 투표 제출'):'투표 시작 전입니다';
 $('thank').style.display=finished?'block':'none';$('votebody').style.display=finished?'none':'block';
 $('login').style.display=state.admin?'none':'block';$('admin-body').style.display=state.admin?'block':'none';
 if(state.admin){$('dbstate').textContent='저장 방식: '+state.database;$('toggles').textContent='투표: '+(state.vote_open?'진행 중':'대기')+' / 결과: '+(state.reveal?'공개':'비공개');$('admteams').innerHTML=state.teams.map(t=>'<div class="adminteam"><b>'+t.team+'조</b><small> 사진 '+(t.photo?'등록':'미등록')+' · 영상 '+(t.video?'등록':'미등록')+'</small><label>사진 제목</label><input id="pt'+t.team+'" value="'+esc(t.photo_title)+'"><label>영상 제목</label><input id="vt'+t.team+'" value="'+esc(t.video_title)+'"><label>미션 점수 자동 집계 (0~70점)</label><input id="sc'+t.team+'" type="text" readonly value="'+Number(t.mission_score).toFixed(2)+'"><small>승인된 미션 점수 자동 반영</small><div class="row"><button class="mini" onclick="saveTeam('+t.team+')">설정 저장</button><label class="mini">사진 업로드<input type="file" style="display:none" accept="image/jpeg,image/png,image/webp" onchange="upload('+t.team+',\'photo\',this.files[0])"></label><label class="mini">영상 업로드<input type="file" style="display:none" accept="video/mp4,video/webm" onchange="upload('+t.team+',\'video\',this.files[0])"></label></div></div>').join('');}
 if(state.counts){const ranked=state.teams.map(t=>{const x=state.counts[t.team];return {team:t.team,mission:Number(t.mission_score),p:x.photo,v:x.video,issued:x.issued,used:x.used}});const getRank=(key,t)=>1+ranked.filter(y=>y[key]>t[key]).length;for(const t of ranked){t.pScore=t.p?Math.max(2,12-getRank('p',t)*2):0;t.vScore=t.v?Math.max(4,24-getRank('v',t)*4):0;t.total=Math.round((t.mission+t.pScore+t.vScore)*100)/100;}ranked.sort((a,b)=>b.total-a.total||b.v-a.v||a.team-b.team);$('result-body').innerHTML=ranked.map((t,i)=>'<div class="rank"><strong>'+(i+1)+'위</strong><span>'+t.team+'조<br><small>미션 '+t.mission.toFixed(2)+' · 사진 '+t.pScore+'('+t.p+'표) · 영상 '+t.vScore+'('+t.v+'표)</small></span><b>'+t.total.toFixed(2)+'점</b></div>').join('')+(state.admin?'<p class="note">전체 투표 '+(state.voting_summary?.total||0)+'명 · 미참석자 '+(state.voting_summary?.absentee||0)+'명 · 참석자 '+(state.voting_summary?.regular||0)+'명</p>':'');}else $('result-body').innerHTML='<p class="muted">집계 결과는 아직 비공개입니다.</p>';
}
function setmy(t){if(qrTeam||absentMode)return;my=t;photo=0;video=0;render()}function pick(type,t){if(type==='photo')photo=t;else video=t;render();}
async function vote(){
  if(!my||!photo||!video||finished||pendingVote())return;
  const payload={voter_team:absentMode?0:my,absent:absentMode,
    team_token:qrToken,photo,video};
  // The local draft survives tab closes; it is NOT a confirmed server vote.
  const queued=queueVote(payload);
  if(!queued){notify('이 브라우저에서 투표 임시 저장을 할 수 없습니다. 브라우저 저장 공간 설정을 확인해주세요.');return;}
  $('submit').disabled=true;
  try{
    await api('/api/vote',payload);
    safeLocalRemove(PENDING_VOTE_KEY);
    finished=true;offlineMode=false;
    notify('✅ 서버에 투표가 정상 접수됐습니다.');
    render();
  }catch(e){
    if(e.message.includes('이미 투표')){
      safeLocalRemove(PENDING_VOTE_KEY);
      finished=true;
      notify('이미 완료된 투표가 확인됐습니다.');
      refresh();
    }else if(e.retryable||e instanceof TypeError){
      offlineMode=true;
      notify(pendingNotice());
      render();
    }else{
      safeLocalRemove(PENDING_VOTE_KEY);
      notify('투표 미접수: '+e.message);
      render();
    }
  }
}
async function login(){try{await api('/api/login',{password:$('password').value});$('password').value='';notify('');refresh()}catch(e){notify(e.message)}}
async function logout(){await api('/api/logout',{});refresh()}
async function setting(key){try{await api('/api/admin/settings',{key,value:!state[key]});refresh()}catch(e){notify(e.message)}}
async function saveTeam(t){try{await api('/api/admin/team',{team:t,photo_title:$('pt'+t).value,video_title:$('vt'+t).value});notify(t+'조 설정 저장 완료');refresh()}catch(e){notify(e.message)}}
async function upload(t,kind,file){if(!file)return;try{const f=new FormData();f.append('team',t);f.append('kind',kind);f.append('file',file);notify('업로드 중입니다. 이 화면을 닫지 마세요.');await api('/api/admin/upload',f,true);notify(t+'조 업로드 완료');refresh()}catch(e){notify(e.message)}}
refresh();setInterval(()=>{const typing=document.activeElement&&['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName);const playing=Array.from(document.querySelectorAll('video')).some(v=>!v.paused&&!v.ended);if(!typing&&!playing)refresh()},25000);