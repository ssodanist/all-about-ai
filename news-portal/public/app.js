const LABEL = { economy: '경제', business: '경영·기업', society: '사회' };
const TOPIC_LABEL = { politics: '정치', entertainment: '연예', sports: '스포츠', custom: '내 제외어' };
const STORAGE_KEY = 'issue-only:exclude';

const $ = (sel) => document.querySelector(sel);
const state = { category: 'all', q: '', exclude: loadExclude() };

function loadExclude() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? []; } catch { return []; }
}
function saveExclude() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state.exclude)); } catch { /* 저장 불가 환경은 무시 */ }
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function highlight(text, q) {
  const safe = escapeHtml(text);
  const words = q.split(/\s+/).filter(Boolean).map((w) => escapeHtml(w).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  return words.length ? safe.replace(new RegExp(`(${words.join('|')})`, 'gi'), '<mark>$1</mark>') : safe;
}
function timeAgo(iso) {
  if (!iso) return '';
  const min = Math.round((Date.now() - new Date(iso)) / 60000);
  if (min < 1) return '방금';
  if (min < 60) return `${min}분 전`;
  if (min < 60 * 24) return `${Math.floor(min / 60)}시간 전`;
  return new Date(iso).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
}
function safeLink(url) {
  return /^https?:\/\//i.test(url) ? url : '#';
}

function syncUrl() {
  const p = new URLSearchParams();
  if (state.q) p.set('q', state.q);
  if (state.category !== 'all') p.set('category', state.category);
  history.replaceState(null, '', p.toString() ? `?${p}` : location.pathname);
}

let requestId = 0;
async function load() {
  const id = ++requestId;
  syncUrl();
  $('#status').textContent = state.q ? `“${state.q}” 검색 중…` : '불러오는 중…';
  const p = new URLSearchParams({ category: state.category });
  if (state.q) p.set('q', state.q);
  if (state.exclude.length) p.set('exclude', state.exclude.join(','));

  let data;
  try {
    const res = await fetch(`/api/news?${p}`);
    if (!res.ok) throw new Error(res.status);
    data = await res.json();
  } catch {
    if (id === requestId) $('#status').textContent = '뉴스를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.';
    return;
  }
  if (id !== requestId) return; // 더 최근 요청이 있으면 무시
  render(data);
}

function render(data) {
  const notice = $('#notice');
  notice.hidden = !data.offline;
  notice.textContent = data.offline
    ? '지금은 언론사 피드에 연결할 수 없어 샘플 기사로 보여드리고 있습니다. 인터넷이 되는 환경에서 실행하면 실제 뉴스가 나옵니다.'
    : '';

  for (const [cat, n] of Object.entries(data.counts)) {
    const el = document.querySelector(`[data-count="${cat}"]`);
    if (el) el.textContent = n;
  }

  const n = data.articles.length;
  $('#status').textContent = state.q
    ? `“${state.q}” 검색 결과 ${n}건`
    : `${state.category === 'all' ? '전체' : LABEL[state.category]} 최신 기사 ${n}건`;

  $('#list').innerHTML = data.articles.map((a) => `
    <li class="item">
      <div class="meta">
        <span class="tag ${a.category}">${LABEL[a.category]}</span>
        <span>${escapeHtml(a.source)}</span>
        <span>·</span>
        <time datetime="${escapeHtml(a.publishedAt ?? '')}">${timeAgo(a.publishedAt)}</time>
      </div>
      <h3><a href="${escapeHtml(safeLink(a.link))}" target="_blank" rel="noopener noreferrer">${highlight(a.title, state.q)}</a></h3>
      ${a.summary ? `<p>${highlight(a.summary, state.q)}</p>` : ''}
    </li>`).join('') || '<li class="item">조건에 맞는 기사가 없습니다.</li>';

  $('#blocked-counts').innerHTML = Object.entries(data.blockedCounts)
    .map(([topic, c]) => `<li>${TOPIC_LABEL[topic] ?? topic} <b>${c}</b></li>`).join('') || '<li>없음</li>';
  $('#blocked-list').innerHTML = data.blocked
    .map((b) => `<li><span>${TOPIC_LABEL[b.reason.topic] ?? b.reason.topic}</span>${escapeHtml(b.title)}</li>`).join('');
}

function renderExclude() {
  $('#exclude-list').innerHTML = state.exclude
    .map((t, i) => `<li>${escapeHtml(t)}<button data-i="${i}" aria-label="${escapeHtml(t)} 삭제">×</button></li>`).join('');
}

// 이벤트
$('#search').addEventListener('submit', (e) => {
  e.preventDefault();
  state.q = $('#q').value.trim();
  load();
});
document.querySelectorAll('.tabs button').forEach((btn) => btn.addEventListener('click', () => {
  document.querySelectorAll('.tabs button').forEach((b) => b.classList.toggle('active', b === btn));
  state.category = btn.dataset.cat;
  load();
}));
$('#exclude-form').addEventListener('submit', (e) => {
  e.preventDefault();
  const term = $('#exclude-input').value.trim();
  if (term && !state.exclude.includes(term)) {
    state.exclude.push(term);
    saveExclude();
    renderExclude();
    load();
  }
  $('#exclude-input').value = '';
});
$('#exclude-list').addEventListener('click', (e) => {
  const i = e.target.dataset?.i;
  if (i === undefined) return;
  state.exclude.splice(Number(i), 1);
  saveExclude();
  renderExclude();
  load();
});

// 시작: URL 파라미터 복원
const params = new URLSearchParams(location.search);
state.q = params.get('q') ?? '';
state.category = ['economy', 'business', 'society'].includes(params.get('category')) ? params.get('category') : 'all';
$('#q').value = state.q;
document.querySelectorAll('.tabs button').forEach((b) => b.classList.toggle('active', b.dataset.cat === state.category));
renderExclude();
load();
setInterval(load, 10 * 60 * 1000); // 10분마다 새로고침
