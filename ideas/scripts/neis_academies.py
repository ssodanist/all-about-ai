"""NEIS 학원교습소정보(acaInsTiInfo)로 바톤 시작 지역 학원 목록과 매도 후보를 뽑는다.

사용법:
    NEIS_API_KEY=발급받은키 python3 neis_academies.py [출력폴더]

인증키는 open.neis.go.kr 에서 무료 발급. 키가 없으면 샘플 요청만 되어 행 수가 제한된다.
"""
import csv
import json
import os
import re
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date

API = "https://open.neis.go.kr/hub/acaInsTiInfo"
PAGE = 1000

# 학원가: (교육청 코드, 행정구역명, 주소에 들어갈 동 이름)
REGIONS = {
    "목동": ("B10", "양천구", ["목동", "신정동"]),
    "상계·중계": ("B10", "노원구", ["상계동", "중계동"]),
    "대치": ("B10", "강남구", ["대치동"]),
    "분당 정자": ("J10", "성남시 분당구", ["정자동"]),
    "분당 수내": ("J10", "성남시 분당구", ["수내동"]),
    "분당 서현": ("J10", "성남시 분당구", ["서현동"]),
}

TODAY = date.today()


def fetch(office, zone, key):
    rows, page = [], 1
    while True:
        q = {"Type": "json", "pIndex": page, "pSize": PAGE,
             "ATPT_OFCDC_SC_CODE": office, "ADMST_ZONE_NM": zone}
        if key:
            q["KEY"] = key
        with urllib.request.urlopen(f"{API}?{urllib.parse.urlencode(q)}", timeout=30) as r:
            body = json.load(r)
        if "acaInsTiInfo" not in body:
            msg = body.get("RESULT", {}).get("MESSAGE", "")
            if page == 1:
                print(f"  {zone}: 결과 없음 ({msg})")
            break
        head, data = body["acaInsTiInfo"]
        total = head["head"][0]["list_total_count"]
        rows += data["row"]
        if len(rows) >= total or not key:
            break
        page += 1
        time.sleep(0.2)
    return rows


def years_open(r):
    d = r.get("ESTBL_YMD") or ""
    if len(d) != 8:
        return None
    y, m, dd = int(d[:4]), int(d[4:6]), int(d[6:])
    return (TODAY - date(y, m, dd)).days / 365.25


def fee_won(r):
    """인당수강료내용에서 첫 금액(원)을 뽑는다. 형식이 제각각이라 근사치."""
    m = re.search(r"(\d[\d,]{3,})", r.get("PSNBY_THCC_CNTNT") or "")
    return int(m.group(1).replace(",", "")) if m else None


def capacity(r):
    try:
        return int(float(r.get("TOFOR_SMTOT") or 0))
    except ValueError:
        return 0


def in_dong(r, dongs):
    addr = f"{r.get('FA_RDNMA', '')} {r.get('FA_RDNDA', '')}"
    return any(d in addr for d in dongs)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "neis_out"
    os.makedirs(out, exist_ok=True)
    key = os.environ.get("NEIS_API_KEY", "")
    cache = {}
    report = ["# 바톤 시작 지역 학원 현황", f"기준일 {TODAY.isoformat()} · 출처 NEIS 학원교습소정보", ""]
    report.append("| 지역 | 전체 | 학원 | 교습소 | 개원 | 휴원 | 5년↑ 소형 개원 (매도 후보) | 수강료 중앙값 |")
    report.append("|---|---|---|---|---|---|---|---|")
    candidates = []
    for name, (office, zone, dongs) in REGIONS.items():
        if (office, zone) not in cache:
            print(f"{zone} 수집 중…")
            cache[(office, zone)] = fetch(office, zone, key)
        rows = [r for r in cache[(office, zone)] if in_dong(r, dongs)]
        status = Counter(r.get("REG_STTUS_NM", "") for r in rows)
        kind = Counter(r.get("ACA_INSTI_SC_NM", "") for r in rows)
        active = [r for r in rows if r.get("REG_STTUS_NM") == "개원"]
        # 매도 후보: 개원 5년 이상, 정원 60명 이하 소형, 운영 중
        cand = [r for r in active if (years_open(r) or 0) >= 5 and 0 < capacity(r) <= 60]
        fees = [f for f in (fee_won(r) for r in active) if f and 10000 <= f <= 3000000]
        med = f"{statistics.median(fees):,.0f}원" if fees else "-"
        report.append(f"| {name} | {len(rows)} | {kind.get('학원', 0)} | {kind.get('교습소', 0)} | "
                      f"{status.get('개원', 0)} | {status.get('휴원', 0)} | {len(cand)} | {med} |")
        for r in cand:
            candidates.append({"지역": name, "구분": r.get("ACA_INSTI_SC_NM"), "학원명": r.get("ACA_NM"),
                               "분야": r.get("REALM_SC_NM"), "교습과정": r.get("LE_CRSE_NM"),
                               "개설일": r.get("ESTBL_YMD"), "운영연수": round(years_open(r), 1),
                               "정원": capacity(r), "인당수강료": r.get("PSNBY_THCC_CNTNT"),
                               "주소": r.get("FA_RDNMA"), "전화": r.get("FA_TELNO")})
    if candidates:
        with open(os.path.join(out, "seller_candidates.csv"), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(candidates[0].keys()))
            w.writeheader()
            w.writerows(candidates)
    with open(os.path.join(out, "region_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))
    print(f"\n매도 후보 {len(candidates)}곳 → {out}/seller_candidates.csv")


if __name__ == "__main__":
    main()
