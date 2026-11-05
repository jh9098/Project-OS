(() => {
  'use strict';
  const team = Number(document.body.dataset.team);
  const token = document.body.dataset.token;
  const base = '/api/mission/' + team + '/' + encodeURIComponent(token);
  const testMode = new URLSearchParams(location.search).get('test') === '1';
  const $ = (s) => document.querySelector(s);
  const escape = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  const thresholds = {M01:3,M11:3,H05:3};
  let data = null;
  let openCode = 'H04';
  let selectedTab = 'missions';
  let busy = false;
  let noticeTimer = null;

  function notify(message) {
    const box = $('#notice');
    box.textContent = message;
    box.hidden = false;
    clearTimeout(noticeTimer);
    noticeTimer = setTimeout(() => box.hidden = true, 6500);
  }
  function setBusy(v) {
    busy = v;
    let overlay = document.querySelector('.busy');
    if(v && !overlay) {
      overlay = document.createElement('div');
      overlay.className = 'busy';
      overlay.innerHTML = '<div class="spinner"></div><span>사진·영상 업로드 중입니다.<br>페이지를 닫지 마세요.</span>';
      document.body.appendChild(overlay);
    }
    if(!v && overlay) overlay.remove();
  }
  function tab(id) {
    selectedTab = id;
    document.querySelectorAll('.tab-panel').forEach(el => el.hidden = el.id !== id);
    document.querySelectorAll('.tabs button').forEach(el => el.classList.toggle('active', el.dataset.tab === id));
  }
  function statusFor(code) {
    const items = (data.submissions || []).filter(x => x.mission_code === code);
    const ok = items.filter(x => x.status === 'approved').length;
    const pending = items.filter(x => x.status === 'pending').length;
    const need = thresholds[code] || 1;
    return {ok,pending,need,done:ok>=need,items};
  }
  function progressCount() {
    const submitted = c => {const x=statusFor(c);return x.ok+x.pending>=x.need};
    const mandatoryPhoto=submitted('H04') ? 1 : 0;
    const videoDone=['V01','V02','V03'].some(submitted) ? 1 : 0;
    const extra=data.missions.filter(m=>m.code!=='H04'&&!m.code.startsWith('V') && submitted(m.code)).length;
    return Math.min(6,mandatoryPhoto+videoDone+Math.min(4,extra));
  }
  function iconFor(m) { return m.code.startsWith('V')?'🎬':m.code.startsWith('H')?'📸':m.code.startsWith('M')?'🤝':'🏛️' }
  function evidenceMarkup(row) {
    const url=base+'/media/'+row.id;
    const media=row.mime.startsWith('video/')?
      '<video controls playsinline preload="metadata" src="'+url+'"></video>':
      '<img loading="lazy" src="'+url+'" alt="제출된 증빙">';
    const status=row.status==='approved'?'승인':row.status==='rejected'?'반려':'검수 대기';
    return '<div class="evidence'+(row.mime.startsWith('video/')?' video':'')+'">'+media+
      '<small>'+escape(status)+' · '+escape(row.filename)+'</small></div>';
  }
  function cardMarkup(m) {
    const stat=statusFor(m.code);
    const isVideo=m.code.startsWith('V');
    const mandatory=m.code==='H04'||isVideo;
    const badge=m.code==='H04'?'필수 사진':isVideo?'필수 영상 택1':'자유 선택';
    const label=stat.done?'<span class="tag green">검수 완료</span>':
       stat.pending?'<span class="tag">검수 대기 '+stat.pending+'</span>':
       stat.items.length?'<span class="tag red">확인 필요</span>':'<span class="tag grey">미제출</span>';
    const mediaType=isVideo?'video/mp4,video/webm,video/quicktime,.mov':
      'image/jpeg,image/png,image/webp,image/heic,image/heif';
    const clue = m.code==='E10'?
      '<div id="e10-clue"><img class="clue-photo" loading="lazy" src="/static/e10-clue.jpg" alt="E10 사진 단서" onerror="this.parentElement.innerHTML=\'<p class=&quot;caption&quot;>사진 단서는 현장 운영진 안내를 확인해 주세요.</p>\'"></div>':'';
    const statusHelp=isVideo?'동영상 1개씩, 파일당 35MB 이하 · 15~30초 가로 MP4 권장':
      '사진 1~3장 선택 가능 · 파일당 6MB 이하 (자동 크기 최적화)';
    return '<article class="mission-card'+(mandatory?' mandatory':'')+'" data-mission="'+escape(m.code)+'">'+
      '<div class="mission-summary"><div class="mission-icon">'+iconFor(m)+'</div><div class="mission-title">'+
      '<div class="mission-tags"><span class="tag">'+escape(m.code)+' · '+m.points+'점</span>'+
      (mandatory?'<span class="tag gold">'+badge+'</span>':'')+label+'</div>'+
      '<h3>'+escape(m.title)+'</h3></div><button class="details-toggle" type="button" data-open="'+escape(m.code)+'">'+(openCode===m.code?'접기 −':'상세 보기 +')+'</button></div>'+
      '<div class="mission-detail" '+(openCode===m.code?'':'hidden')+'>'+
      '<div class="info-line">📍 <strong>장소</strong> '+escape(m.location)+'</div>'+
      '<p>'+escape(m.description)+'</p>'+clue+
      '<div class="info-line">📎 <strong>제출</strong> '+escape(m.proof)+' '+(stat.need>1?'('+stat.ok+'/'+stat.need+'건 승인)':'')+'</div>'+
      '<div class="action-row"><label class="upload-label'+(!data.uploads_open?' disabled':'')+'">📤 '+(isVideo?'영상 올리기':'사진 올리기')+
      '<input type="file" data-upload="'+escape(m.code)+'" accept="'+mediaType+'" '+(isVideo?'':'multiple')+' '+(!data.uploads_open?'disabled':'')+'></label>'+
      '<button type="button" data-tab-jump="map">📍 지도 보기</button></div>'+
      '<p class="caption">'+statusHelp+' · 제출 후 운영진이 검수합니다.</p>'+
      (stat.items.length?'<div class="evidences">'+stat.items.map(evidenceMarkup).join('')+'</div>':'')+
      '</div></article>';
  }
  function render() {
    if(!data)return;
    $('#progress').textContent=progressCount()+' / 6';
    $('#bar').style.width=(progressCount()/6*100)+'%';
    const missions=data.missions.filter(m=>m.code==='H04'||m.code.startsWith('V'));
    const others=data.missions.filter(m=>m.code!=='H04'&&!m.code.startsWith('V'));
    $('#mission-list').innerHTML=
      '<div class="info-line" style="background:#fff1d5"><strong>★ 필수 미션</strong> H04 영화 포스터 + V01~V03 중 영상 하나를 제출하세요.</div>'+
      missions.map(cardMarkup).join('')+
      '<div class="lead"><h2>자유 미션 9개 중 4개</h2><p>쉽고 재미있는 미션을 골라 조원들과 함께 수행하세요.</p></div>'+
      others.map(cardMarkup).join('');
    $('#uploads-list').innerHTML=data.submissions.length?
      data.submissions.map(e=>'<div class="upload-history">'+
        (e.mime.startsWith('video/')?'<video controls playsinline preload="metadata" src="'+base+'/media/'+e.id+'"></video>':
          '<img loading="lazy" alt="제출 사진" src="'+base+'/media/'+e.id+'">')+
        '<div><b>'+escape(e.mission_code)+' · '+escape(data.missions.find(m=>m.code===e.mission_code)?.title||'미션')+'</b>'+
        '<p>'+escape(e.filename)+'</p><small>'+(e.status==='approved'?'✓ 검수 완료':e.status==='rejected'?'반려 · 재제출 가능':'⏳ 검수 대기')+'</small></div></div>').join(''):
      '<div class="empty">아직 제출된 작품이 없습니다.<br>미션 카드를 열고 사진·영상을 올려주세요.</div>';
    if(testMode){
      if(!document.querySelector('#test-banner')){
        const p=document.createElement('div');p.id='test-banner';p.className='info-line';
        p.style.background='#fff0d9';p.innerHTML='<strong>운영진 업로드 테스트 모드</strong> · 여기서 올리는 파일은 투표와 실제 점수에 반영되지 않습니다.';
        $('#missions').prepend(p);
      }
    }
  }
  async function refresh() {
    if(busy)return;
    try {
      const res=await fetch(base+'/state',{cache:'no-store'});
      const j=await res.json();
      if(!res.ok)throw new Error(j.error||'미션 데이터를 불러올 수 없습니다.');
      data=j;render();
    }catch(err){notify(err.message||'네트워크 연결을 확인해주세요.')}
  }
  async function optimizePhoto(file) {
    if(!file.type.startsWith('image/'))return file;
    let bitmap=null;
    try {
      bitmap=await createImageBitmap(file,{imageOrientation:'from-image'});
      const max=1600;
      const scale=Math.min(1,max/Math.max(bitmap.width,bitmap.height));
      const canvas=document.createElement('canvas');
      canvas.width=Math.round(bitmap.width*scale);canvas.height=Math.round(bitmap.height*scale);
      const ctx=canvas.getContext('2d',{alpha:false});ctx.drawImage(bitmap,0,0,canvas.width,canvas.height);
      bitmap.close();
      const out=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',0.83));
      if(out && out.size>100 && out.size<=6*1024*1024){
        return new File([out],file.name.replace(/\.[^.]+$/, '')+'.jpg',{type:'image/jpeg'});
      }
    }catch(err){if(bitmap)bitmap.close();console.warn('Photo optimize fallback',err)}
    return file;
  }
  async function uploadFiles(code,input) {
    if(busy)return;
    const files=Array.from(input.files||[]);
    input.value='';
    if(!files.length)return;
    if(!data.uploads_open && !testMode){notify('운영진이 업로드를 마감했습니다.');return}
    const isVideo=code.startsWith('V');
    if(isVideo && files.length>1){notify('영상은 한 번에 한 개씩 제출해주세요.');return}
    setBusy(true);
    let succeeded=0;
    try {
      for(const original of files) {
        const file=isVideo?original:await optimizePhoto(original);
        const limit=isVideo?35*1024*1024:6*1024*1024;
        if(file.size>limit){notify(original.name+' 파일이 너무 큽니다. '+(isVideo?'영상 35MB':'사진 6MB')+' 이하로 준비해주세요.');continue}
        const form=new FormData();
        form.append('mission_code',code);form.append('file',file,file.name);
        if(testMode)form.append('test','1');
        const resp=await fetch(base+'/upload',{method:'POST',body:form,credentials:'same-origin'});
        let result;try{result=await resp.json()}catch{throw new Error('파일 업로드 연결 오류입니다.')}
        if(!resp.ok||result.error)throw new Error(result.error||'파일 업로드 실패');
        succeeded++;
      }
      notify(succeeded+'개 파일 제출 완료 · '+(testMode?'테스트 자료로 저장됨':'운영진 검수 대기'));
    }catch(err){notify('제출 '+succeeded+'개 성공 · '+(err.message||'오류'))}
    finally {setBusy(false);await refresh();}
  }
  document.querySelector('.tabs').addEventListener('click',e=>{
    const el=e.target.closest('[data-tab]');
    if(!el)return;
    tab(el.dataset.tab);
  });
  $('#mission-list').addEventListener('click',e=>{
    const open=e.target.closest('[data-open]');
    if(open){openCode=openCode===open.dataset.open?'':open.dataset.open;render();return}
    const map=e.target.closest('[data-tab-jump]');
    if(map){tab('map');window.scrollTo({top:0,behavior:'smooth'});}
  });
  $('#mission-list').addEventListener('change',e=>{
    const input=e.target.closest('[data-upload]');
    if(input)uploadFiles(input.dataset.upload,input);
  });
  refresh();
  setInterval(()=>{
    if(busy||Array.from(document.querySelectorAll('video')).some(v=>!v.paused&&!v.ended))return;
    refresh();
  },40000);
})();