(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const originalTeam=Number(document.body.dataset.team)||0;
  const absentee=document.body.dataset.absent==="1";
  const token=document.body.dataset.token||"";
  const AUTO_BACKUP_KEY="gyeongbok_20261106_admin_browser_backup";
  const DRAFT_KEY="gyeongbok_20261106_vote_only_draft";
  let mine=originalTeam,photo=0,video=0,state=null,tab="vote",busy=false;
  let lastBackupTime=0;

  function safeGet(k) { try{return JSON.parse(localStorage.getItem(k)||"null");}catch{return null;} }
  function safeSet(k,v) { try{localStorage.setItem(k,JSON.stringify(v));return true;}catch{return false;} }
  function safeRemove(k){try{localStorage.removeItem(k);}catch{}}
  function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}

  function notice(message,type="error"){
    const n=$("notice");n.hidden=!message;n.textContent=message||"";
    n.className="status "+type;
  }
  async function api(url,options={}){
    let r;
    try{r=await fetch(url,{credentials:"same-origin",cache:"no-store",...options});}
    catch{throw Error("네트워크 연결 오류입니다. 저장 여부를 확인해주세요.");}
    const type=r.headers.get("Content-Type")||"";
    if(!type.includes("application/json"))throw Error("서버 연결 상태가 불안정합니다. 잠시 후 다시 시도해주세요.");
    let j;
    try{j=await r.json();}catch{throw Error("서버 응답을 읽지 못했습니다.");}
    if(!r.ok||j.error)throw Error(j.error||"요청이 실패했습니다.");
    return j;
  }
  function jsonPost(url,data){
    return api(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)});
  }
  function switchTab(next){
    tab=next;
    for(const t of ["vote","results","admin"]){
      $("page-"+t).classList.toggle("hidden",t!==next);
      document.querySelector('[data-page="'+t+'"]').classList.toggle("active",t===next);
    }
    if(next==="results"||next==="admin")render();
  }
  function teamChoices(){
    if(absentee){
      $("team-fixed").classList.add("hidden");
      $("team-select").classList.add("hidden");
      $("absent-note").classList.remove("hidden");
    } else if(originalTeam){
      $("team-fixed").classList.remove("hidden");
      $("team-fixed").textContent="✓ "+originalTeam+"조 자동 선택 · 우리 조 투표 제외";
      $("team-select").classList.add("hidden");
      $("absent-note").classList.add("hidden");
    } else {
      $("team-fixed").classList.add("hidden");
      $("team-select").classList.remove("hidden");
      $("absent-note").classList.add("hidden");
      $("team-picks").innerHTML=[1,2,3,4,5].map(t=>
        '<button type="button" data-my="'+t+'" class="'+(mine===t?"active":"")+'">'+t+'조</button>'
      ).join("");
    }
  }
  function choices(kind,selected){
    const canVote=absentee||mine>=1&&mine<=5;
    return [1,2,3,4,5].filter(t=>absentee||t!==mine).map(t=>{
      const active=selected===t;
      return '<button type="button" data-kind="'+kind+'" data-team="'+t+
        '" class="choice '+(active?"selected":"")+(canVote?"":" disabled")+
        '" '+(!canVote||busy||state?.has_voted?"disabled":"")+'>'+
        '<span><strong>'+t+'조</strong><small>'+escapeHtml(kind==="photo"?"사진 작품":"영상 작품")+'</small></span>'+
        '<span class="mark">'+(active?"●":"○")+'</span></button>';
    }).join("");
  }
  function renderVoting(){
    teamChoices();
    $("vote-success").classList.toggle("hidden",!state?.has_voted);
    $("vote-form").classList.toggle("hidden",!!state?.has_voted);
    if(state?.has_voted)return;
    $("photo-options").innerHTML=choices("photo",photo);
    $("video-options").innerHTML=choices("video",video);
    const valid=(absentee||mine>0)&&photo>0&&video>0&&state?.vote_open&&!busy;
    const submit=$("submit-vote");submit.disabled=!valid;
    submit.textContent=!state?.vote_open?"운영진이 투표를 종료했습니다":
      !valid?"사진·영상 각각 1표를 선택하세요":"🗳 사진 1표 + 영상 1표 투표 제출";
  }
  function computeResults(){
    const teams=state?.teams||[];
    const counts=state?.counts||{};
    const entries=teams.map(t=>{
      const c=counts[t.team]||{photo:0,video:0};
      return {team:t.team,mission:Number(t.mission_score)||0,
        photoVotes:Number(c.photo)||0,videoVotes:Number(c.video)||0};
    });
    for(const e of entries){
      const photoRank=1+entries.filter(x=>x.photoVotes>e.photoVotes).length;
      const videoRank=1+entries.filter(x=>x.videoVotes>e.videoVotes).length;
      e.photoScore=e.photoVotes?Math.max(2,12-photoRank*2):0;
      e.videoScore=e.videoVotes?Math.max(4,24-videoRank*4):0;
      e.total=Math.round((e.mission+e.photoScore+e.videoScore)*100)/100;
    }
    return entries.sort((a,b)=>b.total-a.total||b.videoVotes-a.videoVotes||a.team-b.team);
  }
  function renderResults(){
    const el=$("results-area");
    if(!state){el.innerHTML='<p class="hint">조회 중입니다.</p>';return;}
    if(!state.admin&&!state.reveal){
      el.innerHTML='<div class="status">🔒 결과는 아직 비공개입니다. 운영진이 공개하면 확인할 수 있습니다.</div>';
      return;
    }
    const summary=state.voting_summary||{};
    const ranked=computeResults();
    el.innerHTML='<div class="kpi"><div class="tile"><b>'+Number(summary.total||0)+'</b><span>투표 참여 인원</span></div>'+
      '<div class="tile"><b>'+Number(summary.absentee||0)+'</b><span>미참석자 투표</span></div></div>'+
      ranked.map((s,i)=>{
        const width=Math.min(100,Math.max(0,s.total));
        return '<div class="card"><div class="card-top"><strong>'+(i+1)+'위 · '+s.team+'조</strong>'+
          '<b>'+s.total.toFixed(2)+'점</b></div>'+
          '<div class="track"><span style="width:'+width+'%"></span></div>'+
          '<div class="detail">미션 확정 <strong>'+s.mission.toFixed(2)+'</strong> / 70점 · 사진 <strong>'+
          s.photoScore+'</strong>점 ('+s.photoVotes+'표) · 영상 <strong>'+
          s.videoScore+'</strong>점 ('+s.videoVotes+'표)</div></div>';
      }).join("");
  }
  function renderAdmin(){
    $("admin-login").classList.toggle("hidden",!!state?.admin);
    $("admin-panel").classList.toggle("hidden",!state?.admin);
    if(!state?.admin)return;
    const s=state.voting_summary||{};
    $("admin-kpis").innerHTML='<div class="tile"><b>'+Number(s.total||0)+'</b><span>총 투표</span></div>'+
      '<div class="tile"><b>'+Number(s.regular||0)+'</b><span>참석자</span></div>'+
      '<div class="tile"><b>'+Number(s.absentee||0)+'</b><span>미참석자</span></div>';
    $("toggle-vote").textContent=state.vote_open?"⏹ 투표 종료":"▶ 투표 재개";
    $("toggle-reveal").textContent=state.reveal?"🔒 결과 비공개":"👀 결과 공개";
    $("admin-scores").innerHTML=state.teams.map(t=>
      '<div class="flex" style="padding:12px 3px;border-bottom:1px solid #e6ecef">'+
      '<strong>'+t.team+'조</strong><strong>'+Number(t.mission_score).toFixed(2)+' / 70점</strong></div>'
    ).join("");
    const cached=safeGet(AUTO_BACKUP_KEY);
    const localCount=Array.isArray(cached?.ballots)?cached.ballots.length:0;
    $("backup-meta").textContent="현재 서버 "+Number(s.total||0)+"표 · 이 운영진 브라우저에 저장된 마지막 백업 "+
      localCount+"표. 서버가 재시작했다면 이 기기의 백업으로 복원하세요.";
  }
  function render(){
    renderVoting();renderResults();renderAdmin();
  }
  async function autoBrowserBackup(){
    if(!state?.admin||busy)return;
    if(Date.now()-lastBackupTime<6000)return;
    try{
      const backup=await api("/api/vote-only/backup");
      const current=safeGet(AUTO_BACKUP_KEY);
      if(!current||!Array.isArray(current.ballots)||
        backup.ballots.length>=current.ballots.length){
        safeSet(AUTO_BACKUP_KEY,backup);
      }
      lastBackupTime=Date.now();
    }catch(e){console.warn("Admin browser backup unavailable",e);}
  }
  async function refresh(){
    try{
      const next=await api("/api/state");
      state=next;
      const savedDraft=safeGet(DRAFT_KEY);
      if(state.has_voted){
        safeRemove(DRAFT_KEY);
      }else if(savedDraft&&savedDraft.team===(absentee?0:mine)){
        photo=savedDraft.photo||photo;
        video=savedDraft.video||video;
      }
      notice("");
      render();
      await autoBrowserBackup();
      if(tab==="admin")renderAdmin();
    }catch(e){notice("연결 오류: "+e.message);if(state)render();}
  }
  async function submit(){
    if(busy||!state?.vote_open||!photo||!video)return;
    if(!absentee&&!mine)return;
    busy=true;renderVoting();
    const payload={voter_team:absentee?0:mine,absent:absentee,
      team_token:token||null,photo,video};
    safeSet(DRAFT_KEY,{team:payload.voter_team,photo,video,at:Date.now()});
    try{
      await jsonPost("/api/vote",payload);
      safeRemove(DRAFT_KEY);
      state.has_voted=true;
      notice("투표가 서버에 접수됐습니다.","success");
      render();
      if(state.admin)autoBrowserBackup();
    }catch(e){
      notice("투표 접수를 확인하지 못했습니다: "+e.message+
        " 잠시 후 새로고침하여 접수 여부를 확인하고, 미접수면 다시 제출해 주세요.");
      await refresh();
    }finally{busy=false;renderVoting();}
  }
  async function login(){
    try{
      await jsonPost("/api/login",{password:$("admin-password").value});
      $("admin-password").value="";notice("운영진 로그인 완료","success");
      await refresh();switchTab("admin");
    }catch(e){notice(e.message);}
  }
  async function setting(key){
    if(!state?.admin)return;
    try{
      await jsonPost("/api/admin/settings",{key,value:!state[key]});
      await refresh();
      notice("변경 사항을 저장했습니다.","success");
    }catch(e){notice(e.message);}
  }
  async function restore(payload){
    if(!state?.admin)return;
    if(!payload||!Array.isArray(payload.ballots)){notice("복원할 백업을 찾지 못했습니다.");return;}
    if(!confirm("백업 "+payload.ballots.length+"표를 서버에 복원하시겠습니까? 중복 투표는 추가되지 않습니다."))return;
    busy=true;
    try{
      const result=await jsonPost("/api/vote-only/restore",payload);
      notice("복원 완료 · 서버 현재 "+result.total+"표","success");
      await refresh();
    }catch(e){notice("백업 복원 실패: "+e.message);}
    finally{busy=false;}
  }

  document.querySelectorAll("[data-page]").forEach(b=>b.addEventListener("click",()=>switchTab(b.dataset.page)));
  $("team-picks").addEventListener("click",e=>{
    const b=e.target.closest("[data-my]");if(!b||originalTeam||absentee)return;
    mine=Number(b.dataset.my);photo=0;video=0;renderVoting();
  });
  for(const [container,kind] of [["photo-options","photo"],["video-options","video"]]){
    $(container).addEventListener("click",e=>{
      const b=e.target.closest("[data-kind]");if(!b||busy||!state?.vote_open)return;
      const team=Number(b.dataset.team);
      if(!absentee&&mine===team)return;
      if(kind==="photo")photo=team;else video=team;
      renderVoting();
    });
  }
  $("submit-vote").addEventListener("click",submit);
  $("admin-login-btn").addEventListener("click",login);
  $("admin-password").addEventListener("keydown",e=>{if(e.key==="Enter")login();});
  $("admin-logout").addEventListener("click",async()=>{
    try{await jsonPost("/api/logout",{});state.admin=false;renderAdmin();notice("로그아웃했습니다.","success");}
    catch(e){notice(e.message);}
  });
  $("toggle-vote").addEventListener("click",()=>setting("vote_open"));
  $("toggle-reveal").addEventListener("click",()=>setting("reveal"));
  $("restore-browser").addEventListener("click",()=>restore(safeGet(AUTO_BACKUP_KEY)));
  $("restore-file").addEventListener("change",async e=>{
    const file=e.target.files?.[0];e.target.value="";if(!file)return;
    if(file.size>1500000){notice("백업 파일이 너무 큽니다.");return;}
    try{await restore(JSON.parse(await file.text()));}
    catch{notice("JSON 백업 파일을 확인해주세요.");}
  });
  $("merge-old").addEventListener("click",async()=>{
    if(!confirm("기존 PostgreSQL에 기록된 투표가 남아 있으면 중복 없이 가져옵니다. 진행하시겠습니까?"))return;
    try{const j=await jsonPost("/api/vote-only/merge-pg",{});notice("기존 DB에서 "+j.added+"표를 추가했습니다.","success");await refresh();}
    catch(e){notice(e.message);}
  });
  teamChoices();
  if(new URLSearchParams(window.location.search).get("tab")==="admin")switchTab("admin");
  refresh();
  setInterval(()=>{
    const focused=document.activeElement;
    if(document.hidden||busy||(focused&&focused.id==="admin-password"))return;
    refresh();
  },15000);
})();