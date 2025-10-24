const $ = (id)=>document.getElementById(id);

function toast(msg){ const t=$('toast'); if(!t) return; const m=$('toastMsg'); if(m) m.textContent=msg; t.style.display='block'; setTimeout(()=>t.style.display='none',2200); }

async function api(path, opts={}){
  const res = await fetch(path, opts);
  let data;
  try{ data = await res.json(); }catch(e){ data = await res.text(); }
  if(!res.ok) toast('Request failed');
  return {ok: res.ok, data};
}

function renderCapsule(container, cap){
  container.innerHTML='';
  if(!cap.items || cap.items.length===0){ container.innerHTML = '<div class="muted">No items found. Run pipeline or add sample news.</div>'; return; }
  (cap.items||[]).forEach(it=>{
    const div = document.createElement('div');
    div.className = 'card';
    const chips = (it.topics||[]).slice(0,6).map(t=>`<span class="chip" title="score: ${Math.round((t.score||0)*100)/100}">${t.paper}: ${t.topic}</span>`).join('');
    const pyqs = (it.pyqs||[]).slice(0,4).map(p=>`<div class="muted">(${p.year} ${p.paper}) ${p.question}</div>`).join('');
    div.innerHTML = `
      <div><a href="${it.url}" target="_blank"><strong>${it.title}</strong></a> <span class="muted">${it.source||''}</span></div>
      <div class="muted">${(it.summary||'').slice(0,300)}</div>
      <div>${chips}</div>
      <div>${pyqs}</div>
    `;
    container.appendChild(div);
  });
}

function setActiveTab(tabId){
  document.querySelectorAll('section').forEach(s=>s.hidden=true);
  document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
  const sec = document.getElementById(tabId); if(sec) sec.hidden=false;
  const btn = document.querySelector(`.tab[data-tab="${tabId}"]`); if(btn) btn.classList.add('active');
}

async function loadSubsTable(){
  const t = $('subsTable'); if(!t) return; t.innerHTML='';
  const daily = await api('/subscription/subscribers');
  const weekly = await api('/subscription/weekly-subscribers');
  const push = (items,type)=>{
    (items.data?.subscribers||[]).forEach(s=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${s.email}</td><td>${s.name||''}</td><td>${type}</td>`;
      t.appendChild(tr);
    });
  };
  if(daily.ok) push(daily,'daily');
  if(weekly.ok) push(weekly,'weekly');
}

window.addEventListener('DOMContentLoaded', ()=>{
  // Tabs
  document.querySelectorAll('.tab').forEach(b=> b.onclick=()=> setActiveTab(b.dataset.tab));
  // Theme
  const root=document.documentElement, key='cb_theme'; const saved=localStorage.getItem(key); if(saved){ root.setAttribute('data-theme', saved); }
  const tt=$('themeToggle'); if(tt){ tt.onclick=()=>{ const v = root.getAttribute('data-theme')==='dark'?'light':'dark'; root.setAttribute('data-theme', v); localStorage.setItem(key, v); }; }
  const cap = $('capsule');
  // Auth state
  const token = localStorage.getItem('token');
  const headersAuth = token ? {'Authorization': 'Bearer '+token} : {};
  const loginBtn = $('loginBtn'), signupBtn=$('signupBtn'), logoutBtn=$('logoutBtn');
  if(token){
    // Validate token and get role
    fetch('/users/me',{headers: headersAuth}).then(r=>r.json()).then(me=>{
      if(me && me.role){
        // Show admin controls if admin
        if(me.role === 'admin' || me.role === 'manager'){
          const bp = $('btnPipeline'); if(bp) bp.hidden=false;
          const bws = $('btnWeeklySend'); if(bws) bws.hidden=false;
        }
        if(loginBtn) loginBtn.hidden=true; if(signupBtn) signupBtn.hidden=true; if(logoutBtn){ logoutBtn.hidden=false; logoutBtn.onclick=()=>{ localStorage.removeItem('token'); location.reload(); } }
      }
    }).catch(()=>{});
  }
  $('btnCapsule').onclick = async ()=>{
    const {ok,data} = await api('/capsule/daily');
    if(ok){ renderCapsule(cap, data); toast('Loaded capsule'); }
  };
  $('btnPipeline').onclick = async ()=>{
    const {ok,data} = await api('/pipeline/run',{method:'POST', headers: {'Content-Type':'application/json', ...headersAuth}});
    $('utilOut').textContent = JSON.stringify(data,null,2);
    if(ok){ const capRes = await api('/capsule/daily'); if(capRes.ok){ renderCapsule(cap, capRes.data); toast('Pipeline completed'); } }
  };
  $('btnSubDaily').onclick = async ()=>{
    const email = $('email').value.trim();
    const {data} = await api(`/subscription/subscribe/${encodeURIComponent(email)}`,{method:'POST'});
    $('subsOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnUnsubDaily').onclick = async ()=>{
    const email = $('email').value.trim();
    const {data} = await api(`/subscription/unsubscribe/${encodeURIComponent(email)}`,{method:'POST'});
    $('subsOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnSubWeekly').onclick = async ()=>{
    const email = $('email').value.trim();
    const {data} = await api(`/subscription/subscribe-weekly/${encodeURIComponent(email)}`,{method:'POST'});
    $('subsOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnUnsubWeekly').onclick = async ()=>{
    const email = $('email').value.trim();
    const {data} = await api(`/subscription/unsubscribe-weekly/${encodeURIComponent(email)}`,{method:'POST'});
    $('subsOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnWeeklyPreview').onclick = async ()=>{
    const {data} = await api('/reports/weekly');
    $('subsOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnWeeklySend').onclick = async ()=>{
    const {data} = await api('/reports/weekly/send',{method:'POST', headers: {'Content-Type':'application/json', ...headersAuth}});
    $('subsOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnAsk').onclick = async ()=>{
    const q = $('question').value.trim();
    if(!q){ toast('Type a question'); return; }
    // Stable chat session id
    const sidKey='cb_chat_sid';
    let sid = localStorage.getItem(sidKey);
    if(!sid){ sid = (crypto.randomUUID? crypto.randomUUID() : (Date.now().toString(36)+Math.random().toString(36).slice(2))); localStorage.setItem(sidKey, sid); }
    const out = $('chatOut');
    out.textContent += (out.textContent? "\n" : "") + `You: ${q}\nAssistant: `;
    const {data} = await api('/chat/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q, session_id: sid})});
    if(typeof data === 'object'){
      out.textContent += (data.response || JSON.stringify(data));
    } else {
      out.textContent += data;
    }
    $('question').value = '';
  };
  $('btnSample').onclick = async ()=>{
    const sample = [{source:'admin',title:'RBI policy update on inflation',url:'https://example.com/rbi-'+Date.now(),published_at:new Date().toISOString(),content:'RBI keeps repo rate; measures to manage inflation and growth.'}];
    const {data} = await api('/ingest/news',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(sample)});
    $('utilOut').textContent = JSON.stringify(data,null,2);
  };
  $('btnPlan').onclick = async ()=>{
    const {data} = await api('/schedule/generate',{method:'POST'});
    $('utilOut').textContent = JSON.stringify(data,null,2);
  };
  // Initial
  setActiveTab('capsuleTab');
  $('btnCapsule').click();
  loadSubsTable();
});
