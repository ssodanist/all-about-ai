// 의존성 없는 가벼운 RSS/Atom 파서.

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', middot: '·', hellip: '…', lsquo: '‘', rsquo: '’', ldquo: '“', rdquo: '”' };

export function decodeEntities(s) {
  return s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) => {
    if (e[0] === '#') {
      const code = e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      return Number.isFinite(code) ? String.fromCodePoint(code) : m;
    }
    return ENTITIES[e.toLowerCase()] ?? m;
  });
}

function clean(raw) {
  if (!raw) return '';
  let s = raw.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1');
  s = decodeEntities(s); // 이중 인코딩된 HTML 처리
  s = s.replace(/<[^>]+>/g, ' ');
  return decodeEntities(s).replace(/\s+/g, ' ').trim();
}

function tag(block, name) {
  const m = block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, 'i'));
  return m ? m[1] : '';
}

function atomLink(block) {
  const m = block.match(/<link[^>]*?href=["']([^"']+)["'][^>]*>/i);
  return m ? m[1] : '';
}

export function parseFeed(xml) {
  const items = [];
  const isAtom = /<feed[\s>]/i.test(xml) && !/<rss[\s>]/i.test(xml);
  const re = isAtom ? /<entry[\s>][\s\S]*?<\/entry>/gi : /<item[\s>][\s\S]*?<\/item>/gi;
  for (const block of xml.match(re) ?? []) {
    const title = clean(tag(block, 'title'));
    const link = clean(tag(block, 'link')) || atomLink(block);
    if (!title || !link) continue;
    const date = clean(tag(block, 'pubDate') || tag(block, 'published') || tag(block, 'updated') || tag(block, 'dc:date'));
    const summary = clean(tag(block, 'description') || tag(block, 'summary') || tag(block, 'content'));
    const source = clean(tag(block, 'source'));
    const parsed = Date.parse(date);
    items.push({
      title,
      link,
      summary: summary.length > 220 ? `${summary.slice(0, 220)}…` : summary,
      publishedAt: Number.isNaN(parsed) ? null : new Date(parsed).toISOString(),
      source: source || null,
    });
  }
  return items;
}

// 응답 바이트를 XML 선언의 인코딩(EUC-KR 등)에 맞춰 디코딩한다.
export function decodeXml(buffer, contentType = '') {
  const bytes = new Uint8Array(buffer);
  const head = new TextDecoder('latin1').decode(bytes.slice(0, 200));
  const declared = head.match(/encoding=["']([\w-]+)["']/i)?.[1] ?? contentType.match(/charset=([\w-]+)/i)?.[1] ?? 'utf-8';
  try {
    return new TextDecoder(declared.toLowerCase()).decode(bytes);
  } catch {
    return new TextDecoder('utf-8').decode(bytes);
  }
}
