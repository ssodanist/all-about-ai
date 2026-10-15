import { test } from 'node:test';
import assert from 'node:assert/strict';
import { blockReason, classify, matchesQuery } from '../lib/filter.mjs';
import { parseFeed, decodeXml } from '../lib/rss.mjs';

const a = (title, summary = '', link = 'https://news.example.com/article/1') => ({ title, summary, link });

test('정치 기사를 차단한다', () => {
  assert.equal(blockReason(a('여야, 예산안 처리 놓고 정면충돌'))?.topic, 'politics');
  assert.equal(blockReason(a('대통령실 "인사 발표 임박"'))?.topic, 'politics');
  assert.equal(blockReason(a('국회의원 선거 앞두고', '의원들이 선거 운동에 나섰다'))?.topic, 'politics');
});

test('연예 기사를 차단한다', () => {
  assert.equal(blockReason(a('아이돌 그룹 정규 앨범으로 컴백'))?.topic, 'entertainment');
  assert.equal(blockReason(a('주말 드라마 시청률 20% 돌파'))?.topic, 'entertainment');
});

test('스포츠 기사를 차단한다', () => {
  assert.equal(blockReason(a('프로야구 포스트시즌 끝내기 홈런'))?.topic, 'sports');
  assert.equal(blockReason(a('대표팀 감독, 선수 명단 발표', '구단과 리그 일정 조율'))?.topic, 'sports');
});

test('URL 섹션 경로로 차단한다', () => {
  assert.equal(blockReason(a('평범한 제목', '', 'https://x.com/sports/123'))?.topic, 'sports');
  assert.equal(blockReason(a('평범한 제목', '', 'https://x.com/politics/123'))?.topic, 'politics');
  assert.equal(blockReason(a('평범한 제목', '', 'https://x.com/entertainment/1'))?.topic, 'entertainment');
});

test('경제·경영·사회 기사는 통과한다', () => {
  assert.equal(blockReason(a('한은, 기준금리 동결', '물가와 가계부채 흐름을 점검')), null);
  assert.equal(blockReason(a('반도체 3분기 영업이익 급증')), null);
  assert.equal(blockReason(a('지하철 노조 파업 예고', '교통 불편 우려')), null);
});

test('경제 신호가 강하면 약한 차단어가 있어도 통과한다', () => {
  // '소속사', '콘서트'(연예 약신호)가 있어도 실적 기사는 경영으로 남긴다
  assert.equal(blockReason(a('엔터 기업 3분기 실적', '소속사 콘서트 매출 증가로 영업이익 개선')), null);
  // 요약에 '국회'가 지나가듯 나와도 경제 기사는 통과
  assert.equal(blockReason(a('세법 개정으로 배당소득 과세 바뀐다', '국회 통과 후 주주 배당 세금이 줄어든다')), null);
});

test('대통령이 언급돼도 사회 정책 기사는 통과한다', () => {
  assert.equal(blockReason(a('돌봄·근로시간 걱정에… 대통령, 인구 대책 언급')), null);
  assert.equal(blockReason(a('대통령 지지율 하락'))?.topic, 'politics');
});

test('사용자 제외어로 차단한다', () => {
  assert.deepEqual(blockReason(a('비트코인 급등'), { excludeTerms: ['비트코인'] }), { topic: 'custom', term: '비트코인' });
});

test('분류: 경제/경영/사회', () => {
  assert.equal(classify(a('기준금리 동결, 환율 하락'), null), 'economy');
  assert.equal(classify(a('반도체 기업 실적 발표, 매출 증가'), null), 'business');
  assert.equal(classify(a('대학 입시 경쟁률 상승', '교육 현장 혼란'), null), 'society');
  assert.equal(classify(a('알 수 없는 제목'), 'society'), 'society');
});

test('검색어는 모든 단어를 포함해야 일치한다', () => {
  assert.ok(matchesQuery(a('반도체 수출 증가'), '반도체 수출'));
  assert.ok(!matchesQuery(a('반도체 수출 증가'), '반도체 금리'));
  assert.ok(matchesQuery(a('anything'), ''));
});

test('RSS 파싱: CDATA, 엔티티, 날짜', () => {
  const xml = `<?xml version="1.0" encoding="UTF-8"?><rss><channel>
    <item><title><![CDATA[금리 &amp; 환율 동향]]></title><link>https://n.example.com/1</link>
    <description><![CDATA[<p>요약 <b>본문</b></p>]]></description><pubDate>Wed, 15 Oct 2026 01:00:00 +0900</pubDate></item>
    <item><title>제목 없는 링크</title></item>
  </channel></rss>`;
  const items = parseFeed(xml);
  assert.equal(items.length, 1);
  assert.equal(items[0].title, '금리 & 환율 동향');
  assert.equal(items[0].summary, '요약 본문');
  assert.equal(items[0].publishedAt, '2026-10-14T16:00:00.000Z');
});

test('RSS 파싱: Atom', () => {
  const xml = `<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>물가 상승</title>
    <link href="https://n.example.com/2"/><updated>2026-10-15T00:00:00Z</updated><summary>요약</summary></entry></feed>`;
  const [item] = parseFeed(xml);
  assert.equal(item.link, 'https://n.example.com/2');
});

test('EUC-KR 인코딩 피드를 디코딩한다', () => {
  // "경제" in EUC-KR
  const head = new TextEncoder().encode('<?xml version="1.0" encoding="EUC-KR"?><t>');
  const body = new Uint8Array([0xb0, 0xe6, 0xc1, 0xa6]);
  const buf = new Uint8Array([...head, ...body]);
  assert.ok(decodeXml(buf.buffer).endsWith('경제'));
});
