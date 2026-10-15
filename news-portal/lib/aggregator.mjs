import { readFile } from 'node:fs/promises';
import { FEEDS, searchFeedUrl } from '../feeds.mjs';
import { parseFeed, decodeXml } from './rss.mjs';
import { blockReason, classify, matchesQuery, SEARCH_EXCLUDE_OPERATORS } from './filter.mjs';

const CACHE_TTL_MS = 10 * 60 * 1000;
const FETCH_TIMEOUT_MS = 8000;
const cache = new Map(); // url -> { at, items }

async function fetchFeed(url) {
  const hit = cache.get(url);
  if (hit && Date.now() - hit.at < CACHE_TTL_MS) return hit.items;
  const res = await fetch(url, {
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
    headers: { 'user-agent': 'Mozilla/5.0 (compatible; EconNewsPortal/1.0)' },
  });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  const items = parseFeed(decodeXml(await res.arrayBuffer(), res.headers.get('content-type') ?? ''));
  cache.set(url, { at: Date.now(), items });
  return items;
}

// Google 뉴스 제목은 "제목 - 언론사" 형식이라 언론사를 분리한다.
function splitGoogleTitle(item) {
  const m = item.title.match(/^(.*) - ([^-]{1,30})$/);
  return m ? { ...item, title: m[1].trim(), source: item.source ?? m[2].trim() } : item;
}

async function loadSample() {
  const raw = await readFile(new URL('../sample-data.json', import.meta.url), 'utf8');
  return JSON.parse(raw);
}

async function collect(query) {
  const jobs = [...FEEDS];
  if (query) jobs.push({ source: null, category: null, url: searchFeedUrl(`${query} ${SEARCH_EXCLUDE_OPERATORS}`) });

  const results = await Promise.allSettled(jobs.map((f) => fetchFeed(f.url)));
  const raw = [];
  let failed = 0;
  results.forEach((r, i) => {
    if (r.status !== 'fulfilled') return void failed++;
    const feed = jobs[i];
    for (const item of r.value) {
      const it = feed.url.includes('news.google.com') ? splitGoogleTitle(item) : item;
      raw.push({ ...it, source: it.source ?? feed.source ?? '알 수 없음', hint: feed.category, fromSearch: !feed.category });
    }
  });

  // 모든 피드가 실패하면 (오프라인 등) 샘플 데이터로 동작한다.
  if (raw.length === 0) return { raw: await loadSample(), offline: true, failed };
  return { raw, offline: false, failed };
}

function dedupe(articles) {
  const seen = new Set();
  return articles.filter((a) => {
    const key = a.title.replace(/[\s\p{P}]/gu, '').slice(0, 40);
    if (seen.has(key) || seen.has(a.link)) return false;
    seen.add(key);
    seen.add(a.link);
    return true;
  });
}

export async function getNews({ category = 'all', query = '', excludeTerms = [], limit = 60 } = {}) {
  const q = query.trim();
  const { raw, offline, failed } = await collect(q);

  const articles = [];
  const blocked = [];
  for (const item of dedupe(raw)) {
    const reason = blockReason(item, { excludeTerms });
    if (reason) {
      blocked.push({ title: item.title, source: item.source, link: item.link, reason });
      continue;
    }
    articles.push({ ...item, category: classify(item, item.hint) });
  }

  const filtered = articles
    .filter((a) => category === 'all' || a.category === category)
    .filter((a) => (a.fromSearch ? true : matchesQuery(a, q)))
    .sort((a, b) => (b.publishedAt ?? '').localeCompare(a.publishedAt ?? ''))
    .slice(0, limit)
    .map(({ hint, fromSearch, ...a }) => a);

  const counts = { economy: 0, business: 0, society: 0 };
  for (const a of articles) counts[a.category]++;

  const blockedCounts = {};
  for (const b of blocked) blockedCounts[b.reason.topic] = (blockedCounts[b.reason.topic] ?? 0) + 1;

  return {
    articles: filtered,
    counts,
    blocked: blocked.slice(0, 50),
    blockedCounts,
    offline,
    failedFeeds: failed,
    fetchedAt: new Date().toISOString(),
  };
}
