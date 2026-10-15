# 이슈만 — 경제·경영·사회 뉴스 포털

정치·연예·스포츠 뉴스 없이 **경제 / 경영·기업 / 사회** 이슈만 모아 보고 검색하는 포털입니다.

## 실행

Node.js 18 이상만 있으면 됩니다 (설치할 패키지 없음).

```bash
cd news-portal
npm start          # http://localhost:8787
npm test           # 필터·파서 테스트
```

인터넷에 연결되지 않으면 `sample-data.json`의 샘플 기사로 동작하고, 화면 위에 안내가 뜹니다.

## 동작 방식

1. **수집** — `feeds.mjs`에 적힌 언론사 RSS(연합뉴스, 한국경제, 매일경제, 한겨레의 경제·산업·사회 섹션과 Google 뉴스 비즈니스)를 10분 간격으로 가져옵니다. 처음부터 정치·연예·스포츠 섹션은 수집하지 않습니다.
2. **검색** — 검색어를 넣으면 모아 둔 기사에서 찾고, Google 뉴스 검색 RSS도 함께 조회합니다(`-정치 -연예 -스포츠` 제외 연산자 포함).
3. **2차 필터** (`lib/filter.mjs`) — 경제 섹션에도 정치 기사가 섞이기 때문에 기사마다 다시 확인합니다.
   - URL에 `/politics/`, `/entertainment/`, `/sports/` 같은 섹션 경로가 있으면 차단
   - 제목에 강한 신호어(정당명, 대통령실, 아이돌, 프로야구 등)가 있으면 차단
   - 약한 신호어(국회, 배우, 선수 등)는 **경제 신호어보다 많을 때만** 차단 → "엔터 기업 3분기 실적"처럼 경제 기사는 남깁니다
   - 사용자가 화면에서 추가한 **나만의 제외어**도 적용
4. **분류** — 남은 기사를 키워드 점수로 경제 / 경영·기업 / 사회로 나눕니다.

걸러낸 기사는 오른쪽 "걸러낸 기사" 패널에서 사유와 함께 확인할 수 있어, 필터가 너무 세거나 약하면 바로 알 수 있습니다.

## 조정하기

| 바꾸고 싶은 것 | 파일 |
|---|---|
| 언론사 / RSS 주소 추가·삭제 | `feeds.mjs` |
| 차단 키워드, 분류 키워드 | `lib/filter.mjs` |
| 캐시 시간, 타임아웃 | `lib/aggregator.mjs` |
| 화면 | `public/` |

## API

`GET /api/news?category=all|economy|business|society&q=검색어&exclude=단어1,단어2`

```json
{ "articles": [{ "title", "link", "summary", "source", "publishedAt", "category" }],
  "counts": { "economy": 0, "business": 0, "society": 0 },
  "blocked": [{ "title", "source", "link", "reason": { "topic", "term" } }],
  "blockedCounts": { "politics": 0, "entertainment": 0, "sports": 0 },
  "offline": false, "failedFeeds": 0, "fetchedAt": "..." }
```

## 참고

- RSS 주소는 언론사 사정으로 바뀔 수 있습니다. 실패한 피드는 건너뛰고(`failedFeeds`), 나머지로 계속 동작합니다.
- 기사 본문은 저장하지 않고 제목·요약·링크만 보여줍니다. 공개 서비스로 운영하려면 각 언론사의 RSS 이용 약관을 확인하세요.
