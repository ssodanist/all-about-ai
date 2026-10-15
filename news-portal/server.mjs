// 경제·경영·사회 뉴스 포털 서버 (Node 18+, 외부 의존성 없음)
// 실행: node server.mjs  →  http://localhost:8787

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { getNews } from './lib/aggregator.mjs';

const PORT = Number(process.env.PORT ?? 8787);
const PUBLIC_DIR = fileURLToPath(new URL('./public/', import.meta.url));
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml' };
const CATEGORIES = new Set(['all', 'economy', 'business', 'society']);

function json(res, status, body) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(body));
}

async function serveStatic(res, pathname) {
  const rel = normalize(pathname === '/' ? '/index.html' : pathname).replace(/^(\.\.[/\\])+/, '');
  const file = join(PUBLIC_DIR, rel);
  if (!file.startsWith(PUBLIC_DIR)) return json(res, 403, { error: 'forbidden' });
  try {
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': MIME[extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    json(res, 404, { error: 'not found' });
  }
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host ?? 'localhost'}`);
  if (url.pathname === '/api/news') {
    const category = url.searchParams.get('category') ?? 'all';
    if (!CATEGORIES.has(category)) return json(res, 400, { error: 'category must be all|economy|business|society' });
    const query = (url.searchParams.get('q') ?? '').slice(0, 100);
    const excludeTerms = (url.searchParams.get('exclude') ?? '').split(',').map((s) => s.trim()).filter(Boolean).slice(0, 30);
    try {
      return json(res, 200, await getNews({ category, query, excludeTerms }));
    } catch (err) {
      console.error(err);
      return json(res, 500, { error: '뉴스를 불러오지 못했습니다.' });
    }
  }
  return serveStatic(res, url.pathname);
});

server.listen(PORT, () => console.log(`경제·사회 뉴스 포털: http://localhost:${PORT}`));
