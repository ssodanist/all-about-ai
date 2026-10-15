// 기사 분류/차단 규칙.
// 정치·연예·스포츠 기사는 걸러내고, 남은 기사를 경제/경영/사회로 분류한다.

// URL 경로에 이런 섹션명이 있으면 해당 언론사가 이미 그 분야로 분류한 기사다.
const BLOCKED_URL_PATTERNS = {
  politics: [/\/politics?\//i, /\/polit\//i, /sid1=100\b/, /\/nk\//i, /\/north-?korea\//i],
  entertainment: [/\/entertain(ment)?\//i, /\/enter\//i, /\/star\//i, /\/celeb/i, /\/culture\/broadcast/i],
  sports: [/\/sports?\//i, /\/baseball\//i, /\/soccer\//i, /\/football\//i, /\/golf\//i, /sid1=107\b/],
};

// 하나만 있어도 차단하는 강한 신호.
const STRONG_TERMS = {
  politics: [
    '국민의힘', '더불어민주당', '민주당', '조국혁신당', '개혁신당', '진보당', '정의당',
    '여당', '야당', '여야', '원내대표', '당대표', '최고위원', '전당대회', '공천',
    '총선', '대선', '지방선거', '보궐선거', '탄핵', '대통령실', '국무회의', '청와대',
    '인사청문회', '국정감사', '국감', '대북', '북한', '김정은', '외교부 장관',
  ],
  entertainment: [
    '연예', '아이돌', '걸그룹', '보이그룹', '열애', '결혼 발표', '컴백', '팬미팅',
    '뮤직비디오', '예능', '드라마', '시청률', '박스오피스', '레드카펫', '오디션 프로그램',
    '방송인', '유튜버', '인플루언서', '셀럽', '스캔들', '음원 차트',
  ],
  sports: [
    '프로야구', 'KBO', 'MLB', '메이저리그', 'K리그', '프리미어리그', 'EPL', '챔피언스리그',
    'NBA', 'KBL', 'V리그', 'LPGA', 'PGA', '올림픽', '월드컵', '아시안게임', '국가대표팀',
    '홈런', '골키퍼', '득점왕', '감독 경질', '선발 투수', '결승골', '세트스코어', '손흥민', '이강인', '김하성', '이정후',
  ],
};

// 단독으로는 애매해서, 경제 신호보다 많을 때만 차단하는 약한 신호.
const WEAK_TERMS = {
  politics: ['국회', '의원', '대통령', '정부 여당', '정당', '선거', '장관 후보', '총리', '정치권', '의정', '개헌'],
  entertainment: ['배우', '가수', '방송', '영화', '앨범', '콘서트', '데뷔', '소속사', '출연'],
  sports: ['경기', '선수', '감독', '구단', '우승', '리그', '시즌', '이적', '경기장', '득점'],
};

// 경제/경영 맥락을 보여주는 신호. 약한 차단어를 상쇄한다.
// 예: "하이브 3분기 영업이익" → '소속사'가 있어도 경영 기사로 남긴다.
const ECONOMY_SIGNALS = [
  '경제', '금리', '물가', '환율', '성장률', '수출', '수입', '무역', '경기침체', '인플레이션',
  '기준금리', '한국은행', '한은', '기획재정부', '기재부', '세수', '재정', '예산안', 'GDP',
  '코스피', '코스닥', '증시', '주가', '채권', '부동산', '아파트값', '집값', '전세', '대출',
  '가계부채', '고용', '실업률', '취업자', '소비자', '유가', '원자재', '관세',
];
const BUSINESS_SIGNALS = [
  '기업', '실적', '매출', '영업이익', '순이익', '적자', '흑자', '주주', '배당', '인수', '합병',
  'M&A', '투자', '상장', 'IPO', '스타트업', '경영', 'CEO', '대표이사', '이사회', '지배구조',
  '구조조정', '반도체', '배터리', '자동차', '조선', '철강', '석유화학', '바이오', '플랫폼',
  '공급망', '신사업', '공장', '삼성', 'SK', 'LG', '현대차', '네이버', '카카오',
];
const SOCIETY_SIGNALS = [
  '사회', '사건', '사고', '경찰', '검찰', '법원', '재판', '판결', '교육', '학교', '대학',
  '입시', '의료', '병원', '복지', '저출생', '저출산', '고령화', '노동', '노조', '파업',
  '환경', '기후', '재난', '날씨', '폭염', '한파', '교통', '안전', '인구', '주거', '청년',
  '돌봄', '이민', '외국인 근로자', '산재',
];

function countHits(text, terms) {
  let hits = 0;
  for (const term of terms) if (text.includes(term)) hits++;
  return hits;
}

// 제목 + 요약 + URL을 보고 차단 사유를 돌려준다. 통과하면 null.
export function blockReason(article, { excludeTerms = [] } = {}) {
  const text = `${article.title ?? ''} ${article.summary ?? ''}`;
  const link = article.link ?? '';

  for (const term of excludeTerms) {
    if (term && text.includes(term)) return { topic: 'custom', term };
  }

  for (const [topic, patterns] of Object.entries(BLOCKED_URL_PATTERNS)) {
    if (patterns.some((p) => p.test(link))) return { topic, term: 'url' };
  }

  // 제목에 강한 신호가 있으면 즉시 차단. 요약에만 있으면 약한 신호로 취급한다
  // (경제 기사 요약에 "국회 통과" 같은 말이 지나가듯 나오는 경우가 많다).
  const title = article.title ?? '';
  for (const [topic, terms] of Object.entries(STRONG_TERMS)) {
    const term = terms.find((t) => title.includes(t));
    if (term) return { topic, term };
  }

  const econ = countHits(text, ECONOMY_SIGNALS) + countHits(text, BUSINESS_SIGNALS);
  // 정책 기사("대통령, 저출생 대책 발표")는 사회 신호도 정치 약신호를 상쇄한다.
  const society = countHits(text, SOCIETY_SIGNALS);
  for (const [topic, terms] of Object.entries(WEAK_TERMS)) {
    const weak = countHits(text, terms) + countHits(article.summary ?? '', STRONG_TERMS[topic]) * 2;
    const offset = econ + (topic === 'politics' ? society : 0);
    if (weak > 0 && weak > offset) return { topic, term: terms.find((t) => text.includes(t)) ?? 'summary' };
  }
  return null;
}

// 경제 / 경영 / 사회 중 하나로 분류. 피드에 지정된 기본 분류를 우선 가중한다.
export function classify(article, hint) {
  const text = `${article.title ?? ''} ${article.summary ?? ''}`;
  const scores = {
    economy: countHits(text, ECONOMY_SIGNALS) + (hint === 'economy' ? 1.5 : 0),
    business: countHits(text, BUSINESS_SIGNALS) + (hint === 'business' ? 1.5 : 0),
    society: countHits(text, SOCIETY_SIGNALS) + (hint === 'society' ? 1.5 : 0),
  };
  let best = hint ?? 'economy';
  for (const [cat, score] of Object.entries(scores)) if (score > (scores[best] ?? -1)) best = cat;
  return best;
}

export function matchesQuery(article, query) {
  if (!query) return true;
  const text = `${article.title ?? ''} ${article.summary ?? ''} ${article.source ?? ''}`.toLowerCase();
  // 공백으로 나눈 모든 단어가 들어 있어야 일치 (AND 검색)
  return query.toLowerCase().split(/\s+/).filter(Boolean).every((w) => text.includes(w));
}

// Google 뉴스 검색어에 붙일 제외 연산자 (-정치 -연예 ...).
export const SEARCH_EXCLUDE_OPERATORS = ['정치', '연예', '스포츠', '국회', '아이돌', '프로야구'].map((t) => `-${t}`).join(' ');
