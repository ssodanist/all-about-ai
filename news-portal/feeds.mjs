// 수집할 RSS 피드 목록. 정치·연예·스포츠 섹션은 처음부터 넣지 않는다.
// category: 이 피드 기사의 기본 분류 (economy | business | society)
// 언론사가 RSS 주소를 바꾸면 여기만 고치면 된다.

export const FEEDS = [
  // 연합뉴스
  { source: '연합뉴스', category: 'economy', url: 'https://www.yna.co.kr/rss/economy.xml' },
  { source: '연합뉴스', category: 'business', url: 'https://www.yna.co.kr/rss/industry.xml' },
  { source: '연합뉴스', category: 'society', url: 'https://www.yna.co.kr/rss/society.xml' },

  // 한국경제
  { source: '한국경제', category: 'economy', url: 'https://www.hankyung.com/feed/economy' },
  { source: '한국경제', category: 'economy', url: 'https://www.hankyung.com/feed/finance' },
  { source: '한국경제', category: 'economy', url: 'https://www.hankyung.com/feed/realestate' },
  { source: '한국경제', category: 'business', url: 'https://www.hankyung.com/feed/it' },
  { source: '한국경제', category: 'society', url: 'https://www.hankyung.com/feed/society' },

  // 매일경제
  { source: '매일경제', category: 'economy', url: 'https://www.mk.co.kr/rss/30100041/' },
  { source: '매일경제', category: 'business', url: 'https://www.mk.co.kr/rss/50100032/' },
  { source: '매일경제', category: 'economy', url: 'https://www.mk.co.kr/rss/50200011/' },
  { source: '매일경제', category: 'society', url: 'https://www.mk.co.kr/rss/50400012/' },

  // 한겨레
  { source: '한겨레', category: 'economy', url: 'https://www.hani.co.kr/rss/economy/' },
  { source: '한겨레', category: 'society', url: 'https://www.hani.co.kr/rss/society/' },

  // Google 뉴스 '비즈니스' 토픽 (여러 언론사 종합)
  { source: null, category: 'business', url: 'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko' },
];

// 검색어가 있을 때 추가로 조회하는 Google 뉴스 검색 RSS.
export const searchFeedUrl = (query) =>
  `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=ko&gl=KR&ceid=KR:ko`;
