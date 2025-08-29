/* globals Chart */
const $ = (id) => document.getElementById(id);

const state = {
  timer: null,
  intervalSec: 5,
  chart: null,
  labels: [],
  cpu: [],
  mem: [],
};

function cssVar(name){ return getComputedStyle(document.body).getPropertyValue(name).trim(); }

function applyChartTheme(){
  if(!state.chart) return;
  const legendColor = cssVar('--legend') || '#111827';
  const gridColor   = cssVar('--grid')   || '#d1d5db';
  state.chart.options.plugins.legend.labels.color = legendColor;
  state.chart.options.scales.x.ticks.color = legendColor;
  state.chart.options.scales.y.ticks.color = legendColor;
  state.chart.options.scales.x.grid.color = gridColor;
  state.chart.options.scales.y.grid.color = gridColor;
  state.chart.update('none');
}

function fmtSecs(s) {
  if (s == null) return "–";
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
  if (h) return `${h}h ${m}m ${sec}s`;
  if (m) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function setBars(cpu, mem){
  const c = cpu ?? 0, m = mem ?? 0;
  $("cpuBar").style.width = Math.min(c,100) + "%";
  $("memBar").style.width = Math.min(m,100) + "%";
  $("cpuPct").textContent = c==null ? "–" : `${c.toFixed(0)}%`;
  $("memPct").textContent = m==null ? "–" : `${m.toFixed(0)}%`;
}

function setServer(ok, uptime, served){
  const badge = $("serverBadge");
  badge.classList.toggle("ok", !!ok);
  badge.classList.toggle("fail", !ok);
  badge.textContent = ok ? "ONLINE" : "OFFLINE";
  $("serverNote").textContent = ok ? "— OK" : "— Unreachable";
  $("uptime").textContent = fmtSecs(uptime);
  $("served").textContent = served ?? "–";
}

function dotColor(el, status){
  el.classList.remove("green","yellow","red");
  if (!status) { el.classList.add("yellow"); return; }
  const s = status.toLowerCase();
  if (s.startsWith("succ")) el.classList.add("green");
  else if (s.startsWith("fail")) el.classList.add("red");
  else el.classList.add("yellow");
}

function setMeta(meta){
  $("gitBranch").textContent = meta.git.branch || "—";
  $("gitCommit").textContent = (meta.git.commit || "—").slice(0,7);
  $("gitAuthor").textContent = meta.git.author || "—";
  $("gitDate").textContent = meta.git.date || "—";
  $("cid").textContent = meta.container.id || "—";
  $("cuptime").textContent = fmtSecs(meta.container.uptime_s);
  $("ports").textContent = meta.container.port_mappings || "—";
  $("sysHost").textContent = meta.system.host || "—";
  $("sysPy").textContent = meta.system.python || "—";
  $("sysUtc").textContent = meta.system.utc_time || "—";

  $("stageBuild").textContent  = meta.stages.build;
  $("stageTest").textContent   = meta.stages.test;
  $("stageDeploy").textContent = meta.stages.deploy;

  dotColor($("dotBuild"),  meta.stages.build);
  dotColor($("dotTest"),   meta.stages.test);
  dotColor($("dotDeploy"), meta.stages.deploy);

  const badge = $("envBadge");
  if (window.APP_ENV) badge.textContent = window.APP_ENV;
}

async function fetchMeta(){
  const r = await fetch("/api/meta");
  if(!r.ok) throw new Error("meta failed");
  setMeta(await r.json());
}

async function fetchHealth(){
  const r = await fetch("/api/health");
  if(!r.ok) throw new Error("health failed");
  const j = await r.json();
  setServer(j.ok, j.uptime_s, j.requests_served);
  setBars(j.cpu, j.memory);
}

async function fetchStats(){
  const r = await fetch("/api/stats");
  if(!r.ok) throw new Error("stats failed");
  const j = await r.json();
  const now = new Date();
  state.labels.push(now.toLocaleTimeString([], {minute:'2-digit', second:'2-digit'}));
  state.cpu.push(j.cpu ?? 0);
  state.mem.push(j.memory ?? 0);
  if(state.labels.length>60){ state.labels.shift(); state.cpu.shift(); state.mem.shift(); }
  state.chart.data.labels = state.labels;
  state.chart.data.datasets[0].data = state.cpu;
  state.chart.data.datasets[1].data = state.mem;
  state.chart.update();
}

async function fetchLogs(){
  try{
    const r = await fetch("/api/logs");
    if(!r.ok) throw new Error();
    const j = await r.json();
    $("logs").textContent = j.map(x => `${x.ts}  ${x.path}  ${x.status}`).join("\n") || "—";
  }catch{
    const card = document.getElementById("logsCard");
    if (card) card.style.display = "none";
  }
}

function setupChart(){
  const ctx = document.getElementById("usageChart");
  // dataset colors follow the current CSS var --fill / --accent look
  const cpuColor = cssVar('--fill') || '#3b82f6';
  const memColor = '#8b5cf6'; // a second line; stays readable in both themes
  state.chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        { label: "CPU", data: [], tension: .3, borderWidth: 2, pointRadius: 0, borderColor: cpuColor },
        { label: "Memory", data: [], tension: .3, borderWidth: 2, pointRadius: 0, borderColor: memColor },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "top", labels: { color: '#111827' } } },
      scales: {
        x: { ticks: { color: '#111827' }, grid: { color: '#d1d5db' } },
        y: { beginAtZero: true, max: 100, ticks: { callback: v => v + "%", color: '#111827' }, grid: { color: '#d1d5db' } }
      }
    }
  });
  applyChartTheme(); // <-- apply current theme colors
}

function setIntervalButtons(){
  const chips = document.querySelectorAll(".chip");
  chips.forEach(btn=>{
    if(btn.dataset.interval === String(state.intervalSec)) btn.classList.add("active");
    btn.addEventListener("click", ()=>{
      chips.forEach(b=>b.classList.remove("active"));
      btn.classList.add("active");
      state.intervalSec = parseInt(btn.dataset.interval,10);
      startPolling();
    });
  });
}

function startPolling(){
  if(state.timer) clearInterval(state.timer);
  const tick = async ()=>{
    try{
      await Promise.all([fetchMeta(), fetchHealth(), fetchStats(), fetchLogs()]);
    }catch{
      setServer(false, null, null);
    }
  };
  tick();
  state.timer = setInterval(tick, state.intervalSec*1000);
}

function setupDarkToggle(){
  const t = document.getElementById("darkToggle");
  // keep chips readable by not changing their classes on toggle
  t.addEventListener("change", ()=>{
    document.body.classList.toggle("dark", t.checked);
    applyChartTheme(); // <-- retint chart labels/grid to the new theme
  });
  t.checked = false; // default light (matches your screenshot)
}

window.addEventListener("DOMContentLoaded", ()=>{
  setupChart();
  setIntervalButtons();
  setupDarkToggle();
  startPolling();
});
