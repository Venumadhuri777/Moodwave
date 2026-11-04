/* ═══════════════════════════════════════════════════════════
   Moodwave Presentation Frontend — app.js
   ═══════════════════════════════════════════════════════════ */

const API = ''; // same origin — served by FastAPI
const USER_ID = 'demo-user-' + Math.random().toString(36).slice(2, 10);
let currentMode = 'familiar';
let savedTracks = new Set();
let lastResponse = null;

// ── Utilities ──────────────────────────────────────────────

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }
function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

// ── Server health check ───────────────────────────────────

async function checkHealth() {
  const el = $('#serverStatus');
  try {
    const r = await fetch(API + '/health');
    const d = await r.json();
    el.innerHTML = `<span class="dot"></span> Server OK · ${d.catalog_size} tracks · LLM: ${d.llm_configured ? 'ON' : 'OFF'}`;
    el.className = 'nav-status online';
    $('#catalogSizeArch').textContent = `${d.catalog_size} tracks loaded`;
    return d;
  } catch {
    el.innerHTML = '<span class="dot"></span> Server offline';
    el.className = 'nav-status offline';
    return null;
  }
}

// ── Wave canvas (hero background) ─────────────────────────

function initWave() {
  const c = $('#waveCanvas');
  const ctx = c.getContext('2d');
  let w, h;
  function resize() { w = c.width = window.innerWidth; h = c.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);

  let t = 0;
  function draw() {
    ctx.clearRect(0, 0, w, h);
    for (let i = 0; i < 4; i++) {
      ctx.beginPath();
      const a = 0.03 + i * 0.008;
      const amp = 40 + i * 20;
      const yOff = h * 0.55 + i * 30;
      ctx.moveTo(0, yOff);
      for (let x = 0; x <= w; x += 4) {
        const y = yOff + Math.sin(x * 0.003 + t * a + i) * amp + Math.sin(x * 0.007 + t * a * 1.5) * amp * 0.4;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(w, h);
      ctx.lineTo(0, h);
      ctx.closePath();
      const colors = ['rgba(45,212,191,0.06)', 'rgba(14,165,233,0.05)', 'rgba(245,158,11,0.04)', 'rgba(45,212,191,0.03)'];
      ctx.fillStyle = colors[i];
      ctx.fill();
    }
    t++;
    requestAnimationFrame(draw);
  }
  draw();
}

// ── Reveal-on-scroll ──────────────────────────────────────

function initReveal() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); } });
  }, { threshold: 0.15 });
  $$('.reveal').forEach(el => obs.observe(el));
}

// ── Mode toggle ───────────────────────────────────────────

function initModeToggle() {
  $$('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.mode-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentMode = btn.dataset.mode;
    });
  });
}

// ── Mood chips ────────────────────────────────────────────

function initChips() {
  $$('.mood-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      $('#searchInput').value = chip.dataset.query;
      $('#searchInput').focus();
    });
  });
}

// ── Pipeline animation ────────────────────────────────────

function animatePipeline() {
  show($('#pipelineViz'));
  const steps = ['pipeStep1', 'pipeStep2', 'pipeStep3', 'pipeStep4'];
  steps.forEach(id => {
    const el = document.getElementById(id);
    el.classList.remove('active', 'done');
  });

  let i = 0;
  return new Promise(resolve => {
    function next() {
      if (i > 0) document.getElementById(steps[i - 1]).classList.replace('active', 'done');
      if (i >= steps.length) { resolve(); return; }
      document.getElementById(steps[i]).classList.add('active');
      i++;
      setTimeout(next, 500);
    }
    next();
  });
}

// ── Search ────────────────────────────────────────────────

async function doSearch() {
  const query = $('#searchInput').value.trim();
  if (!query) { $('#searchError').textContent = 'Please enter a query.'; return; }
  if (query.length > 300) { $('#searchError').textContent = 'Query must be 300 characters or less.'; return; }
  $('#searchError').textContent = '';

  // Hide previous results
  hide($('#resultsList'));
  hide($('#statusBanner'));
  hide($('#intentSummary'));
  hide($('#apiLogSection'));

  // Show skeleton + pipeline
  show($('#skeleton'));
  await animatePipeline();

  const reqBody = { query, mode: currentMode, user_id: USER_ID, limit: 10 };

  // Show request log
  show($('#apiLogSection'));
  $('#apiReqLog').textContent = `POST /v1/recommend\n\n${JSON.stringify(reqBody, null, 2)}`;
  $('#apiResLog').textContent = 'Waiting for response…';

  const startTime = performance.now();

  try {
    const r = await fetch(API + '/v1/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reqBody),
    });

    const elapsed = Math.round(performance.now() - startTime);

    if (!r.ok) {
      const errBody = await r.json().catch(() => ({}));
      hide($('#skeleton'));
      hide($('#pipelineViz'));

      if (r.status === 422) {
        const msg = errBody?.error?.message || 'Validation error';
        $('#searchError').textContent = msg;
        $('#apiResLog').textContent = `HTTP ${r.status} (${elapsed}ms)\n\n${JSON.stringify(errBody, null, 2)}`;
        return;
      }
      if (r.status === 429) {
        const retryAfter = r.headers.get('Retry-After') || '?';
        showBanner('rate-limited', `Rate limited. Retry after ${retryAfter} seconds.`);
        $('#apiResLog').textContent = `HTTP ${r.status} (${elapsed}ms)\nRetry-After: ${retryAfter}\n\n${JSON.stringify(errBody, null, 2)}`;
        return;
      }
      if (r.status === 503) {
        showBanner('error', 'Server is starting up. Please retry in a moment.', true);
        $('#apiResLog').textContent = `HTTP ${r.status} (${elapsed}ms)\n\n${JSON.stringify(errBody, null, 2)}`;
        return;
      }
      showBanner('error', `Error ${r.status}: ${errBody?.error?.message || 'Unknown error'}`, true);
      $('#apiResLog').textContent = `HTTP ${r.status} (${elapsed}ms)\n\n${JSON.stringify(errBody, null, 2)}`;
      return;
    }

    const data = await r.json();
    lastResponse = data;

    hide($('#skeleton'));
    hide($('#pipelineViz'));

    // Response log
    $('#apiResLog').textContent = `HTTP 200 (${elapsed}ms) · source: ${data.source}\n\n${JSON.stringify(data, null, 2)}`;

    // Degraded banner
    if (data.degraded) {
      const reason = data.degraded_reason || 'Smart parsing is off. Using basic matching.';
      showBanner('degraded', `⚠ Degraded: ${reason}`);
    }

    // Intent summary
    if (data.intent) {
      renderIntentSummary(data.intent);
    }

    // Render tracks
    if (!data.items || data.items.length === 0) {
      renderEmpty();
    } else {
      renderTracks(data.items);
    }

  } catch (err) {
    hide($('#skeleton'));
    hide($('#pipelineViz'));
    showBanner('offline', 'Backend unreachable. Check if localhost:8000 is running.', true);
    $('#apiResLog').textContent = `Network error: ${err.message}`;
  }
}

// ── Banner ────────────────────────────────────────────────

function showBanner(type, text, showRetry) {
  const el = $('#statusBanner');
  const icons = { offline: 'wifi_off', degraded: 'warning', 'rate-limited': 'speed', error: 'error' };
  el.className = `status-banner ${type}`;
  el.innerHTML = `<span class="material-icons-round">${icons[type] || 'info'}</span> ${text}`;
  if (showRetry) {
    el.innerHTML += ' <button class="btn-retry" onclick="doSearch()">Retry</button>';
  }
  show(el);
}

// ── Intent summary ────────────────────────────────────────

function renderIntentSummary(intent) {
  const el = $('#intentSummary');
  let parts = [];
  if (intent.moods && intent.moods.length) parts.push(`Moods: ${intent.moods.map(m => `<span class="intent-tag">${m}</span>`).join(' ')}`);
  if (intent.genres && intent.genres.length) parts.push(`Genres: ${intent.genres.map(g => `<span class="intent-tag">${g}</span>`).join(' ')}`);
  if (intent.context) parts.push(`Context: <span class="intent-tag">${intent.context}</span>`);
  parts.push(`Mode: <span class="intent-tag">${currentMode === 'familiar' ? '💚 Familiar' : '🟡 Non-habitual'}</span>`);
  if (intent.confidence != null) parts.push(`Confidence: ${Math.round(intent.confidence * 100)}%`);
  el.innerHTML = parts.join(' · ');
  show(el);
}

// ── Tracks ────────────────────────────────────────────────

function renderTracks(items) {
  const list = $('#resultsList');
  list.innerHTML = '';
  items.forEach((item, i) => {
    const card = document.createElement('div');
    card.className = 'track-card';
    card.style.animationDelay = `${i * 0.06}s`;
    card.dataset.trackId = item.track_id;

    const moodTags = (item.mood_tags || []).map(t => `<span class="track-mood">${t}</span>`).join('');
    const isSaved = savedTracks.has(item.track_id);

    const titleHtml = item.track_url
      ? `<a href="${item.track_url}" target="_blank" rel="noopener" title="Open on Jamendo">${item.title}</a>`
      : item.title;

    card.innerHTML = `
      <div class="track-header">
        <div>
          <div class="track-title">${titleHtml}</div>
          <div class="track-artist">${item.artist}</div>
        </div>
      </div>
      <div class="track-meta">
        <span class="track-genre">${item.genre}</span>
        ${moodTags}
        <span class="track-sid">${item.semantic_id}</span>
      </div>
      <div class="track-explanation">"${item.explanation}"</div>
      <div class="track-actions">
        <button class="track-btn skip" data-track="${item.track_id}" aria-label="Skip ${item.title}">
          <span class="material-icons-round">skip_next</span> Skip
        </button>
        <button class="track-btn save ${isSaved ? 'saved' : ''}" data-track="${item.track_id}" aria-label="Save ${item.title}">
          <span class="material-icons-round">${isSaved ? 'bookmark' : 'bookmark_border'}</span> ${isSaved ? 'Saved' : 'Save'}
        </button>
        <button class="track-btn replay" data-track="${item.track_id}" aria-label="Replay ${item.title}">
          <span class="material-icons-round">replay</span> Replay
        </button>
      </div>
    `;

    list.appendChild(card);
  });
  show(list);
  bindTrackActions();
}

function renderEmpty() {
  const list = $('#resultsList');
  list.innerHTML = `
    <div style="text-align:center;padding:48px 0;">
      <span class="material-icons-round" style="font-size:3rem;color:var(--text-dim);display:block;margin-bottom:12px;">music_off</span>
      <p style="color:var(--text-dim);margin-bottom:16px;">No tracks matched your query.</p>
      <button class="mood-chip" onclick="document.getElementById('searchInput').value='calm music for a rainy afternoon';document.getElementById('searchInput').focus();">Try: calm music for a rainy afternoon</button>
    </div>
  `;
  show(list);
}

// ── Track actions (skip/save/replay) ──────────────────────

function bindTrackActions() {
  $$('.track-btn.skip').forEach(btn => {
    btn.addEventListener('click', () => {
      const trackId = btn.dataset.track;
      sendFeedback(trackId, 'skip');
      const card = btn.closest('.track-card');
      card.classList.add('removing');
      setTimeout(() => card.remove(), 350);
    });
  });

  $$('.track-btn.save').forEach(btn => {
    btn.addEventListener('click', () => {
      const trackId = btn.dataset.track;
      if (savedTracks.has(trackId)) {
        savedTracks.delete(trackId);
        btn.classList.remove('saved');
        btn.innerHTML = '<span class="material-icons-round">bookmark_border</span> Save';
      } else {
        savedTracks.add(trackId);
        sendFeedback(trackId, 'save');
        btn.classList.add('saved');
        btn.innerHTML = '<span class="material-icons-round">bookmark</span> Saved';
      }
    });
  });

  $$('.track-btn.replay').forEach(btn => {
    btn.addEventListener('click', () => {
      const trackId = btn.dataset.track;
      sendFeedback(trackId, 'replay');
      btn.style.color = 'var(--amber)';
      btn.style.borderColor = 'var(--amber)';
      setTimeout(() => { btn.style.color = ''; btn.style.borderColor = ''; }, 1200);
    });
  });
}

async function sendFeedback(trackId, action) {
  try {
    await fetch(API + '/v1/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: USER_ID, track_id: trackId, action }),
    });
  } catch { /* silently ignore — feedback is best-effort */ }
}

// ── Init ──────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initWave();
  initReveal();
  initModeToggle();
  initChips();

  // Search triggers
  $('#searchBtn').addEventListener('click', doSearch);
  $('#searchInput').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });

  // Health check
  checkHealth();
  setInterval(checkHealth, 15000);
});
