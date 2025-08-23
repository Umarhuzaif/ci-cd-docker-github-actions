async function fetchJSON(url) {
  const r = await fetch(url, { cache: 'no-store' });
  return await r.json();
}
function secondsToHMS(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}h ${m}m ${s}s`;
}
async function refresh() {
  try {
    const health = await fetchJSON('/api/health');
    const stats  = await fetchJSON('/api/stats');

    const badge = document.getElementById('statusBadge');
    if (health.status === 'ok') {
      badge.textContent = 'ONLINE — OK';
      badge.className = 'badge badge-ok px-3 py-2';
    } else {
      badge.textContent = 'OFFLINE — ERROR';
      badge.className = 'badge badge-bad px-3 py-2';
    }

    document.getElementById('uptime').textContent   = secondsToHMS(stats.uptime_seconds || 0);
    document.getElementById('requests').textContent = stats.requests ?? '--';
    document.getElementById('commit').textContent   = stats.commit_sha || 'unknown';
    document.getElementById('image').textContent    = stats.image_tag || 'unknown';

    document.getElementById('host').textContent = stats.hostname || 'unknown';
    document.getElementById('py').textContent   = stats.python_version || 'unknown';
    document.getElementById('ts').textContent   = stats.timestamp || '';

    const cpu = document.getElementById('cpu');
    const mem = document.getElementById('mem');
    const cpuVal = document.getElementById('cpu-val');
    const memVal = document.getElementById('mem-val');

    if (typeof stats.cpu === 'number') {
      cpu.style.width = `${stats.cpu}%`;
      cpuVal.textContent = stats.cpu.toFixed(0);
    } else {
      cpu.style.width = '0%';
      cpuVal.textContent = '--';
    }
    if (typeof stats.memory === 'number') {
      mem.style.width = `${stats.memory}%`;
      memVal.textContent = stats.memory.toFixed(0);
    } else {
      mem.style.width = '0%';
      memVal.textContent = '--';
    }
  } catch (e) {
    const badge = document.getElementById('statusBadge');
    badge.textContent = 'OFFLINE — ERROR';
    badge.className = 'badge badge-bad px-3 py-2';
  }
}
document.addEventListener('DOMContentLoaded', () => {
  refresh();
  setInterval(refresh, 5000);
});
