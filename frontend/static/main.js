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

function renderQuiz(container, quiz){
  container.innerHTML = '';
  if(!quiz || !Array.isArray(quiz.questions) || quiz.questions.length === 0){
    container.innerHTML = '<div class="muted">No quiz available for today. Generate capsule or check later.</div>';
    return;
  }
  const meta = document.getElementById('quizMeta');
  if(meta){ meta.textContent = `${quiz.name || 'Daily Quiz'} — ${quiz.questions.length} questions`; }
  // Keep name for submit
  container.dataset.quizName = quiz.name || 'Daily Quiz';
  quiz.questions.forEach((q, idx)=>{
    const card = document.createElement('div');
    card.className = 'card';
    const options = (q.options||[]).map((opt, oi)=>{
      const id = `q${idx}_opt${oi}`;
      return `
        <div class="row-sm">
          <input type="radio" id="${id}" name="q${idx}" value="${oi}" />
          <label for="${id}">${String.fromCharCode(65+oi)}. ${opt}</label>
        </div>
      `;
    }).join('');
    card.innerHTML = `
      <div><strong>Q${idx+1}.</strong> ${q.q}</div>
      ${q.context ? `<div class="muted-sm">Context: ${q.context.slice(0,200)}</div>` : ''}
      <div style="margin-top:6px;">${options}</div>
    `;
    container.appendChild(card);
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
  // Quiz wiring
  const quizContainer = $('quizContainer');
  const btnQuizLoad = $('btnQuizLoad');
  const btnQuizSubmit = $('btnQuizSubmit');
  const btnQuizProgress = $('btnQuizProgress');
  if(btnQuizLoad){
    btnQuizLoad.onclick = async ()=>{
      try{
        // Force regenerate to ensure latest logic and LLM output
        await api('/tests/generate/daily?force=1',{method:'POST'});
        const {ok, data} = await api('/tests/today');
        if(ok){ renderQuiz(quizContainer, data); toast('Quiz loaded'); }
        else { $('quizOut').textContent = JSON.stringify(data,null,2); toast('Unable to load quiz'); }
      }catch(e){
        $('quizOut').textContent = String(e);
        toast('Quiz load error');
      }
    };
  }
  if(btnQuizSubmit){
    btnQuizSubmit.onclick = async ()=>{
      const token = localStorage.getItem('token');
      if(!token){ toast('Login required to submit'); return; }
      const answers = [];
      const cards = quizContainer.querySelectorAll('.card');
      cards.forEach((card, i)=>{
        const sel = card.querySelector(`input[name="q${i}"]:checked`);
        answers.push(sel ? parseInt(sel.value, 10) : -1);
      });
      const name = quizContainer.dataset.quizName || 'Daily Quiz';
      const res = await fetch('/tests/submit',{
        method:'POST',
        headers:{'Content-Type':'application/json','Authorization':'Bearer '+token},
        body: JSON.stringify({name, answers})
      });
      const data = await res.json().catch(()=>({}));
      $('quizOut').textContent = JSON.stringify(data,null,2);
      if(res.ok){ toast(`Score: ${data.score}`); }
      else { toast('Submit failed'); }
    };
  }
  if(btnQuizProgress){
    btnQuizProgress.onclick = async ()=>{
      const token = localStorage.getItem('token');
      if(!token){ toast('Login required'); return; }
      const [resP, resH] = await Promise.all([
        fetch('/tests/progress',{headers:{'Authorization':'Bearer '+token}}),
        fetch('/tests/history',{headers:{'Authorization':'Bearer '+token}})
      ]);
      const dataP = await resP.json().catch(()=>({}));
      const dataH = await resH.json().catch(()=>([]));
      $('quizOut').textContent = JSON.stringify({summary: dataP, history: dataH},null,2);
      // draw chart
      const canvas = document.getElementById('quizChart');
      if(canvas && canvas.getContext){ drawQuizChart(canvas, dataH); }
    };
  }

  function drawQuizChart(canvas, history){
    const ctx = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    ctx.clearRect(0,0,W,H);
    // axes
    ctx.strokeStyle = '#888';
    ctx.beginPath(); ctx.moveTo(30,10); ctx.lineTo(30,H-30); ctx.lineTo(W-10,H-30); ctx.stroke();
    // labels
    ctx.fillStyle = '#666'; ctx.font = '12px Arial';
    ctx.fillText('Score', 4, 12);
    ctx.fillText('Tests', W-60, H-10);
    // bars
    const n = Math.max(1, history.length);
    const barW = Math.max(6, Math.floor((W-50)/n) - 4);
    history.forEach((it, i)=>{
      const score = Math.max(0, Math.min(100, it.score||0));
      const x = 32 + i*(barW+4);
      const y = (H-30) - Math.round((score/100)*(H-50));
      ctx.fillStyle = '#3b82f6';
      ctx.fillRect(x, y, barW, (H-30)-y);
    });
    // y ticks 0,50,100
    ctx.fillStyle = '#444';
    [0,50,100].forEach(v=>{
      const y = (H-30) - Math.round((v/100)*(H-50));
      ctx.fillText(String(v), 4, y+4);
      ctx.strokeStyle = '#eee';
      ctx.beginPath(); ctx.moveTo(30,y); ctx.lineTo(W-10,y); ctx.stroke();
    });
  }
  // Initial
  setActiveTab('capsuleTab');
  $('btnCapsule').click();
  loadSubsTable();

  // Plan tab wiring
  async function loadPlan(){
    const headers = token? {'Authorization':'Bearer '+token} : {};
    const res = await fetch('/plan/me', {headers});
    const data = await res.json().catch(()=>({}));
    const sum = $('planSummary'); const weeks = $('planWeeks');
    weeks.innerHTML = '';
    if(!data.plan){ sum.textContent = 'No plan yet. Click Recompute to generate.'; return; }
    const fb = data.plan.feedback_summary || {};
    sum.textContent = `Tests: ${fb.tests_considered||0} | Avg Score: ${fb.average_score||0} | Weak: ${(fb.weak_topics||[]).join(', ')}`;
    (data.plan.weeks||[]).forEach(w=>{
      const card = document.createElement('div'); card.className='card';
      const tasks = (w.tasks||[]).map(t=>`<li>${t}</li>`).join('');
      card.innerHTML = `<div><strong>Week ${w.week}</strong> — Hours: ${w.hours}</div><ul>${tasks}</ul>`;
      weeks.appendChild(card);
    });
  }
  const blp = $('btnLoadPlan'); if(blp){ blp.onclick = loadPlan; }
  const brp = $('btnRecomputePlan'); if(brp){ brp.onclick = async ()=>{
    const headers = {'Content-Type':'application/json', ...(token? {'Authorization':'Bearer '+token}: {})};
    const res = await fetch('/plan/recompute',{method:'POST', headers});
    await res.json().catch(()=>({}));
    await loadPlan(); toast('Plan recomputed');
  }; }
});
