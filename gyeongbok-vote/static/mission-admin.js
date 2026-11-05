(() => {
  'use strict';
  const $=s=>document.querySelector(s);
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  let data=null,filter='pending',busy=false,refreshTimer=0;
  function show(msg){const n=$('#notice');n.hidden=false;n.textContent=msg;clearTimeout(refreshTimer);refreshTimer=setTimeout(()=>n.hidden=true,6000)}
  async function send(url,payload) {
    const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',body:JSON.stringify(payload)});
    let j;try{j=await r.json()}catch{throw new Error('서버 통신 오류')};
    if(!r.ok||j.error)throw new Error(j.error||'처리 오류');
    return j;
  }
  async function refresh() {
    if(busy)return;
    try {
      const r=await fetch('/api/admin/mission/state',{cache:'no-store'});
      if(r.status===401){$('#admin-login').hidden=false;$('#admin-panel').hidden=true;return;}
      const j=await r.json();
      if(!r.ok)throw new Error(j.error||'서버 오류');
      data=j;$('#admin-login').hidden=true;$('#admin-panel').hidden=false;render();
    }catch(e){show(e.message);}
  }
  function render() {
    if(!data)return;
    $('#upload-state').textContent=data.uploads_open?'접수 진행 중 · 제출 가능':'제출 마감';
    $('#toggle-uploads').textContent=data.uploads_open?'⏹ 제출 마감하기':'▶ 제출 재개하기';
    const qrMarkup=data.links.map(a=>{
      const url='/api/admin/mission/qr.png?team='+a.team;
      return '<div class="qr-card"><strong>'+a.team+'조</strong>'+
        '<img alt="'+a.team+'조 QR" src="'+url+'&inline=1">'+
        '<a href="'+url+'">QR PNG 저장</a>'+
        '<button data-copy="'+escape(a.url)+'">링크 복사</button></div>'
    }).join('');
    $('#qr-grid').innerHTML=qrMarkup;
    $('#test-links').innerHTML=data.links.map(a=>'<a target="_blank" rel="noopener" href="'+escape(a.url)+'?test=1">'+a.team+'조 테스트 제출 ↗</a>').join('');
    const testCount=data.submissions.filter(x=>x.is_test).length;
    const testFilter=$('.admin-filters [data-filter="test"]');
    if(testFilter)testFilter.textContent='테스트만 ('+testCount+')';
    let rows=data.submissions;
    if(filter==='pending')rows=rows.filter(x=>x.status==='pending'&&!x.is_test);
    if(filter==='test')rows=rows.filter(x=>x.is_test);
    $('#submissions').innerHTML=rows.length?rows.map(s=>{
      const url='/api/admin/mission/media/'+s.id;
      const media=s.mime.startsWith('video/')?
        '<span class="video-thumb" aria-hidden="true">🎬<small>영상 재생</small></span>':
        '<img loading="lazy" src="'+url+'" alt="제출 사진">';
      const status=s.is_test?'🧪 테스트':s.status==='approved'?'✓ 승인':s.status==='rejected'?'반려':'검수 대기';
      const buttons=s.is_test?'<button class="danger" data-action="delete" data-id="'+s.id+'">테스트 파일 삭제</button>':
        '<button class="approve" data-action="approved" data-id="'+s.id+'">승인</button>'+
        '<button class="reject" data-action="rejected" data-id="'+s.id+'">반려</button>'+
        '<button class="danger" data-action="delete" data-id="'+s.id+'">삭제</button>';
      const previewButton='<button class="preview-button" data-preview="'+s.id+'">🔍 '+(s.mime.startsWith('video/')?'영상 크게 재생':'사진 크게 보기')+'</button>';
      return '<article class="review-card"><div class="review-preview"><button class="preview-thumb" data-preview="'+s.id+'" aria-label="'+(s.mime.startsWith('video/')?'영상 재생':'사진 확대')+'">'+media+'</button></div>'+
        '<div class="review-info"><h3>'+s.team+'조 · '+escape(s.mission_code)+' <span class="tag">'+status+'</span></h3>'+
        '<p>'+escape(s.filename)+' · '+Math.round(s.size_bytes/1024)+'KB</p>'+
        '<p>'+escape(s.created_at.replace('T',' ').slice(0,19))+'</p>'+
        '<div class="review-buttons">'+previewButton+buttons+'</div></div></article>';
    }).join(''):'<div class="empty">현재 이 조건에 해당하는 제출 파일이 없습니다.</div>';
    document.querySelectorAll('.admin-filters button').forEach(b=>b.classList.toggle('active',b.dataset.filter===filter));
  }
  async function mutation(url,payload,msg){
    if(busy)return;
    busy=true;
    try{await send(url,payload);show(msg);busy=false;await refresh()}
    catch(e){busy=false;show(e.message)}
  }
  $('#login-button').addEventListener('click',async()=>{
    const pw=$('#admin-password').value;
    if(!pw){show('관리자 비밀번호를 입력해주세요.');return}
    try{await send('/api/login',{password:pw});$('#admin-password').value='';show('관리자 로그인 성공');await refresh()}
    catch(e){show(e.message)}
  });
  $('#admin-password').addEventListener('keydown',e=>{if(e.key==='Enter')$('#login-button').click()});
  $('#toggle-uploads').addEventListener('click',()=>{
    if(!data)return;
    if(data.uploads_open&&!confirm('모든 참가자의 사진·영상 제출을 마감할까요?'))return;
    mutation('/api/admin/mission/uploads',{open:!data.uploads_open},'제출 상태를 변경했습니다.');
  });
  $('#clear-tests').addEventListener('click',()=>{
    if(!confirm('모든 업로드 테스트 파일을 삭제하시겠습니까? 실제 제출 파일은 유지됩니다.'))return;
    mutation('/api/admin/mission/clear-tests',{},'테스트 파일을 정리했습니다.');
  });
  $('#qr-grid').addEventListener('click',async e=>{
    const button=e.target.closest('[data-copy]');
    if(!button)return;
    try{await navigator.clipboard.writeText(button.dataset.copy);show('조별 링크를 복사했습니다.')}
    catch{show('브라우저에서 복사가 차단되었습니다. URL을 직접 선택해주세요.')}
  });
  $('.admin-filters').addEventListener('click',e=>{
    const button=e.target.closest('[data-filter]');if(!button)return;
    filter=button.dataset.filter;render();
  });
  const previewDialog=$('#preview-modal');
  function closePreview(){
    if(previewDialog.open)previewDialog.close();
    $('#preview-body').replaceChildren();
  }
  function openPreview(id) {
    const item=data?.submissions.find(x=>Number(x.id)===Number(id));
    if(!item){show('파일을 찾지 못했습니다. 새로고침 후 다시 시도해주세요.');return;}
    const url='/api/admin/mission/media/'+item.id;
    $('#preview-title').textContent=item.team+'조 · '+item.mission_code+' · '+(item.is_test?'테스트 파일':'제출 파일');
    const body=$('#preview-body');
    body.replaceChildren();
    let media;
    if(item.mime.startsWith('video/')){
      media=document.createElement('video');
      media.controls=true;media.playsInline=true;media.preload='metadata';
    }else{
      media=document.createElement('img');
      media.alt=item.filename;
    }
    media.src=url;
    body.appendChild(media);
    $('#preview-download').href=url;
    previewDialog.showModal();
  }
  $('#preview-close').addEventListener('click',closePreview);
  previewDialog.addEventListener('click',e=>{if(e.target===previewDialog)closePreview();});
  previewDialog.addEventListener('close',()=>$('#preview-body').replaceChildren());
  $('#submissions').addEventListener('click',e=>{
    const previewButton=e.target.closest('[data-preview]');
    if(previewButton){openPreview(Number(previewButton.dataset.preview));return;}
    const b=e.target.closest('[data-action]');if(!b)return;
    const id=Number(b.dataset.id),action=b.dataset.action;
    if(action==='delete'){
      if(!confirm('제출 파일을 완전히 삭제하시겠습니까? 승인된 투표 작품일 경우 투표 화면에서도 제거됩니다.'))return;
      return mutation('/api/admin/mission/delete',{id},'파일 삭제 완료');
    }
    if(action==='approved'||action==='rejected'){
      if(!confirm((action==='approved'?'이 파일을 승인':'이 파일을 반려')+'하시겠습니까?'))return;
      return mutation('/api/admin/mission/review',{id,action},action==='approved'?'승인 완료 · 대표작이면 투표 화면에 반영됩니다.':'반려 완료');
    }
  });
  refresh();
  setInterval(()=>{if(!busy&&!Array.from(document.querySelectorAll('video')).some(v=>!v.paused&&!v.ended))refresh()},45000);
})();