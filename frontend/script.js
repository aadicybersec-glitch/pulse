const API = window.location.origin;
let currentClassCode = null;
let currentFilter = "all";
let countdownInterval = null;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const deadlineInput = $("#deadlineInput");
const btnAdd = $("#btnAdd");
const parseResult = $("#parseResult");
const deadlineList = $("#deadlineList");
const feedTitle = $("#feedTitle");
const classBadge = $("#classBadge");
const classCodeDisp = $("#classCodeDisplay");
const classNameInput = $("#classNameInput");
const joinCodeInput = $("#joinCodeInput");
const btnCreateClass = $("#btnCreateClass");
const btnJoinClass = $("#btnJoinClass");
const classInfo = $("#classInfo");
const stressFill = $("#stressFill");
const stressScore = $("#stressScore");
const stressLevel = $("#stressLevel");
const stressMessage = $("#stressMessage");
const suggestionsList = $("#suggestionsList");
const notifList = $("#notifList");
const notifCount = $("#notifCount");
const overdueInfo = $("#overdueInfo");
const toastContainer = $("#toastContainer");

async function api(endpoint, opts = {}) {
  const url = `${API}${endpoint}`;
  try {
    const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...opts });
    return await res.json();
  } catch (err) { console.error(`API ${endpoint}:`, err); return { error: err.message }; }
}

function toast(msg, type = "info") {
  const el = document.createElement("div");
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  toastContainer.appendChild(el);
  el.addEventListener("click", () => el.remove());
  setTimeout(() => el.remove(), 4000);
}

function esc(str) { const d = document.createElement("div"); d.textContent = str; return d.innerHTML; }

// ── Add Deadline ──
btnAdd.addEventListener("click", addDeadline);
deadlineInput.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); addDeadline(); } });

async function addDeadline() {
  const raw = deadlineInput.value.trim();
  if (!raw) { toast("Type a deadline first!", "warning"); return; }
  btnAdd.disabled = true; btnAdd.textContent = "Parsing…";
  const body = { input: raw };
  if (currentClassCode) body.class_code = currentClassCode;
  const res = await api("/add", { method: "POST", body: JSON.stringify(body) });
  btnAdd.disabled = false; btnAdd.innerHTML = '<span class="btn-pulse"></span>Parse &amp; Add';
  if (res.error) {
    parseResult.style.display = "block"; parseResult.className = "parse-result error"; parseResult.textContent = res.error;
    toast(res.error, "error"); return;
  }
  const d = res.deadline;
  parseResult.style.display = "block"; parseResult.className = "parse-result success";
  parseResult.innerHTML = `✅ <strong>${esc(d.title)}</strong><br>Subject: ${d.subject} · Type: ${d.task_type}<br>Due: ${new Date(d.due_date).toLocaleString()}<br>Danger: ${d.danger}`;
  deadlineInput.value = "";
  toast(`Deadline added: ${d.title}`, "success");
  refreshAll();
}

// ── Render Deadlines ──
async function fetchDeadlines() {
  const qs = currentClassCode ? `?class_code=${currentClassCode}&boosted=true` : "?boosted=true";
  return await api(`/deadlines${qs}`);
}

function filterDeadlines(list) {
  switch (currentFilter) {
    case "active": return list.filter(d => !d.completed && d.danger !== "OVERDUE");
    case "overdue": return list.filter(d => !d.completed && d.danger === "OVERDUE");
    case "completed": return list.filter(d => d.completed);
    default: return list;
  }
}

async function renderDeadlines() {
  const res = await fetchDeadlines();
  if (res.error) return;
  const filtered = filterDeadlines(res.deadlines || []);
  if (filtered.length === 0) {
    deadlineList.innerHTML = '<div class="empty-state"><div class="empty-icon">🎯</div><p>No deadlines.</p><p class="muted">Type naturally to get started.</p></div>';
    return;
  }
  deadlineList.innerHTML = filtered.map((d, i) => {
    const dc = d.danger_color || "#666";
    const cd = d.countdown || {};
    const cs = cd.formatted || "—";
    const b = d.priority_boost ? "boosted" : "";
    const c = d.completed ? "completed" : "";
    const ds = d.due_date ? new Date(d.due_date).toLocaleString() : "No date";
    return `<div class="deadline-card ${c} ${b}" data-id="${d.id}" style="animation-delay:${i*0.06}s">
      <div class="danger-bar" style="background:${dc}"></div>
      <div class="deadline-body">
        <div class="deadline-title">${esc(d.title)}</div>
        <div class="deadline-meta">
          <span class="meta-tag"><span class="tag-dot" style="background:${dc}"></span>${d.subject}</span>
          <span class="meta-tag">📎 ${d.task_type}</span>
          ${d.priority_boost ? '<span class="meta-tag" style="color:#fd79a8;">🔥 Boosted</span>' : ''}
        </div>
        <div class="deadline-due">📅 ${ds}</div>
        ${d.boost_reason ? `<div class="deadline-due" style="color:#fd79a8;margin-top:3px;">${esc(d.boost_reason)}</div>` : ''}
      </div>
      <div class="deadline-right">
        <div class="countdown-display" style="color:${dc}" data-due="${d.due_date||''}">${cs}</div>
        <span class="time-label">${d.time_label||''}</span>
        <span class="danger-badge danger-${d.danger}">${d.danger}</span>
        <div class="deadline-actions">
          ${!d.completed ? `<button class="btn btn-success btn-complete" data-id="${d.id}" title="Done">✓</button><button class="btn btn-danger btn-delete" data-id="${d.id}" title="Delete">✕</button>` : ''}
        </div>
      </div>
    </div>`;
  }).join("");
  deadlineList.querySelectorAll(".btn-complete").forEach(b => b.addEventListener("click", async e => { e.stopPropagation(); await api(`/deadline/${b.dataset.id}/complete`,{method:"POST"}); toast("Marked complete ✓","success"); refreshAll(); }));
  deadlineList.querySelectorAll(".btn-delete").forEach(b => b.addEventListener("click", async e => { e.stopPropagation(); await api(`/deadline/${b.dataset.id}`,{method:"DELETE"}); toast("Removed","info"); refreshAll(); }));
  startCountdowns();
}

function startCountdowns() {
  if (countdownInterval) clearInterval(countdownInterval);
  countdownInterval = setInterval(() => {
    document.querySelectorAll(".countdown-display[data-due]").forEach(el => {
      const due = el.dataset.due; if (!due) return;
      const diff = new Date(due) - new Date();
      if (diff <= 0) { el.textContent = "OVERDUE"; el.style.color = "#9e9e9e"; return; }
      const dd = Math.floor(diff/86400000), h = Math.floor((diff%86400000)/3600000), m = Math.floor((diff%3600000)/60000), s = Math.floor((diff%60000)/1000);
      el.textContent = dd > 0 ? `${dd}d ${String(h).padStart(2,"0")}h ${String(m).padStart(2,"0")}m ${String(s).padStart(2,"0")}s` : `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`;
    });
  }, 1000);
}

// ── Filters ──
$$(".btn-chip[data-filter]").forEach(btn => btn.addEventListener("click", () => {
  $$(".btn-chip[data-filter]").forEach(b => b.classList.remove("active"));
  btn.classList.add("active"); currentFilter = btn.dataset.filter; renderDeadlines();
}));

// ── Classes ──
btnCreateClass.addEventListener("click", async () => {
  const name = classNameInput.value.trim(); if (!name) { toast("Enter a class name","warning"); return; }
  const res = await api("/class/create",{method:"POST",body:JSON.stringify({name})});
  if (res.ok) { setClass(res.class.code,res.class.name); classNameInput.value=""; toast(`Class created: ${res.class.code}`,"success");
    classInfo.style.display="block"; classInfo.innerHTML=`<strong>Code:</strong> <span style="font-family:var(--font-mono);letter-spacing:2px;">${res.class.code}</span><br><strong>Name:</strong> ${esc(res.class.name)}<br><span class="muted">Share the code!</span>`; }
});

btnJoinClass.addEventListener("click", async () => {
  const code = joinCodeInput.value.trim().toUpperCase(); if (!code) { toast("Enter a code","warning"); return; }
  const res = await api("/join",{method:"POST",body:JSON.stringify({code})});
  if (res.error) { toast(res.error,"error"); return; }
  setClass(res.class.code,res.class.name); joinCodeInput.value=""; toast(`Joined: ${res.class.name}`,"success");
  classInfo.style.display="block"; classInfo.innerHTML=`<strong>Joined:</strong> ${esc(res.class.name)}<br><strong>Code:</strong> ${res.class.code}<br><strong>Members:</strong> ${res.class.members.length}`;
  refreshAll();
});

function setClass(code, name) { currentClassCode=code; classBadge.style.display="flex"; classCodeDisp.textContent=code; feedTitle.textContent=`📋 ${name}`; }

// ── Analytics ──
async function refreshStress() {
  const qs = currentClassCode ? `?class_code=${currentClassCode}` : "";
  const res = await api(`/analytics/stress${qs}`); if (res.error) return;
  stressScore.textContent=res.score; stressLevel.textContent=res.level; stressMessage.textContent=res.message;
  stressFill.style.width=`${res.score}%`; stressFill.className="stress-fill";
  if (res.level==="MEDIUM") stressFill.classList.add("medium");
  if (res.level==="HIGH") stressFill.classList.add("high");
  if (res.level==="EXTREME") stressFill.classList.add("extreme");
}

async function refreshSuggestions() {
  const qs = currentClassCode ? `?class_code=${currentClassCode}` : "";
  const res = await api(`/analytics/suggestions${qs}`); if (res.error) return;
  suggestionsList.innerHTML = (res.suggestions||[]).map(t => `<li class="suggestion-item">${esc(t)}</li>`).join("");
}

async function refreshOverdue() {
  const qs = currentClassCode ? `?class_code=${currentClassCode}` : "";
  const res = await api(`/analytics/overdue${qs}`); if (res.error) return;
  if (res.count===0) { overdueInfo.innerHTML='<p class="muted">✅ All clear!</p>'; }
  else { overdueInfo.innerHTML=`<div class="overdue-count">${res.count}</div><p>overdue deadline${res.count>1?"s":""}</p><p class="overdue-subjects">Subjects: ${res.subjects_affected.join(", ")}</p>`; }
}

async function refreshNotifications() {
  const res = await api("/notifications?limit=20"); if (res.error) return;
  const n = res.notifications||[];
  if (n.length===0) { notifList.innerHTML='<p class="muted">No notifications yet.</p>'; notifCount.style.display="none"; return; }
  notifCount.style.display="inline"; notifCount.textContent=n.length;
  notifList.innerHTML = n.map(x => `<div class="notif-item">${esc(x.message)}<span class="notif-time">${new Date(x.timestamp).toLocaleTimeString()}</span></div>`).join("");
}

async function refreshAll() { await Promise.all([renderDeadlines(),refreshStress(),refreshSuggestions(),refreshOverdue(),refreshNotifications()]); }

document.addEventListener("DOMContentLoaded", () => {
  refreshAll();
  setInterval(refreshNotifications, 15000);
  setInterval(() => { refreshStress(); refreshSuggestions(); refreshOverdue(); }, 30000);
});
