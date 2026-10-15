#!/usr/bin/env python3
"""데모용 가상 데이터 생성: 카페·베이커리 프랜차이즈 8개 점포 × 20개 품목, 약 18개월 일별 출고.
요일 패턴(오피스/주거 상권 다름), 공휴일 효과, 계절성, 추세, 프로모션, 결품, 간헐 수요를 포함합니다.

    python make_sample.py --out sample_data --end 2026-10-14
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from forecast import KR_HOLIDAYS

STORES = {  # 점포: (상권, 규모, 연간성장률)
    "S01_강남역": ("오피스", 1.6, 0.05), "S02_여의도": ("오피스", 1.3, 0.00),
    "S03_판교": ("오피스", 1.1, 0.12), "S04_분당정자": ("주거", 1.0, 0.03),
    "S05_일산": ("주거", 0.8, -0.05), "S06_송도": ("주거", 0.9, 0.15),
    "S07_스타필드": ("몰", 1.4, 0.04), "S08_부산서면": ("몰", 1.2, 0.02),
}
WEEKDAY = {"오피스": [1.15, 1.15, 1.15, 1.15, 1.2, 0.5, 0.35],
           "주거": [0.9, 0.9, 0.9, 0.95, 1.05, 1.3, 1.2],
           "몰": [0.75, 0.75, 0.75, 0.8, 1.0, 1.6, 1.5]}
HOLIDAY = {"오피스": 0.35, "주거": 1.25, "몰": 1.5}
PRE_HOLIDAY = {"오피스": 0.85, "주거": 1.1, "몰": 1.15}
#        sku, 품목명, 일평균, 계절(+여름/-겨울), 간헐여부, 리드타임, 박스입수, MOQ, 유통기한, 단가
SKUS = [
    ("C001", "원두 1kg", 3.0, 0.0, False, 3, 1, 0, 180, 28000),
    ("C002", "디카페인 원두 500g", 0.6, 0.0, False, 3, 1, 0, 180, 19000),
    ("M001", "우유 1L", 28.0, -0.05, False, 1, 12, 0, 7, 1900),
    ("M002", "오트밀크 1L", 6.0, 0.0, False, 2, 6, 0, 30, 3800),
    ("M003", "휘핑크림 1L", 3.5, 0.1, False, 1, 6, 0, 10, 6500),
    ("B001", "크루아상 생지(10입)", 5.0, -0.05, False, 2, 4, 0, 60, 9000),
    ("B002", "베이글(10입)", 3.0, 0.0, False, 1, 2, 0, 3, 8000),
    ("B003", "샌드위치", 14.0, 0.0, False, 1, 6, 0, 2, 3200),
    ("B004", "조각케이크", 9.0, 0.0, False, 1, 4, 0, 3, 3500),
    ("I001", "얼음 3kg", 9.0, 0.5, False, 1, 4, 0, 365, 2500),
    ("I002", "아이스컵 16oz(50입)", 7.0, 0.45, False, 3, 10, 0, 365, 4500),
    ("I003", "핫컵 12oz(50입)", 5.0, -0.4, False, 3, 10, 0, 365, 4200),
    ("I004", "컵홀더(100입)", 2.0, 0.0, False, 3, 5, 0, 365, 3000),
    ("S001", "바닐라시럽", 1.2, 0.1, False, 3, 1, 0, 365, 11000),
    ("S002", "시즌 시럽(한정)", 0.25, 0.0, True, 5, 1, 0, 365, 14000),
    ("S003", "기프트박스", 0.15, 0.0, True, 5, 1, 0, 365, 5000),
    ("P001", "딸기청(시즌)", 2.0, -0.2, False, 2, 2, 0, 14, 12000),
    ("P002", "자몽청", 1.5, 0.3, False, 2, 2, 0, 21, 11000),
    ("T001", "냅킨(1000입)", 1.0, 0.0, False, 3, 4, 0, 365, 6000),
    ("T002", "세척제", 0.3, 0.0, True, 5, 1, 0, 365, 9000),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="sample_data")
    ap.add_argument("--end", default="2026-10-14")
    ap.add_argument("--days", type=int, default=560)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    dates = pd.date_range(end=a.end, periods=a.days, freq="D")
    hol = dates.isin(pd.to_datetime(KR_HOLIDAYS))
    pre = (dates + pd.Timedelta(days=1)).isin(pd.to_datetime(KR_HOLIDAYS)) & ~hol
    doy = dates.dayofyear.to_numpy()
    summer = np.sin(2 * np.pi * (doy - 105) / 365)       # 7월 말 최고, 1월 말 최저
    t_years = np.arange(len(dates)) / 365

    # 품목별 프로모션 기간 (전 점포 공통, 3~5일, 연 4~6회)
    promo = {}
    for sku, *_ in SKUS:
        flag = np.zeros(len(dates), bool)
        if rng.random() < 0.5:
            for start in rng.choice(len(dates) - 7, size=rng.integers(6, 9), replace=False):
                flag[start:start + rng.integers(3, 6)] = True
        promo[sku] = flag

    rows = []
    for st, (kind, scale, growth) in STORES.items():
        wd = np.array(WEEKDAY[kind])[dates.dayofweek]
        ev = np.where(hol, HOLIDAY[kind], np.where(pre, PRE_HOLIDAY[kind], 1.0))
        for sku, name, base, season, inter, *_ in SKUS:
            mu = base * scale * (1 + growth) ** t_years * (1 + season * summer) * wd * ev
            mu = mu * np.where(promo[sku], 1.7, 1.0) * rng.uniform(0.9, 1.1)
            if inter:
                qty = (rng.random(len(dates)) < np.clip(mu, 0, 0.9)) * rng.integers(1, 4, len(dates))
            else:
                r = 8.0                                  # 음이항 분산 (포아송보다 변동 큼)
                qty = rng.negative_binomial(r, r / (r + np.maximum(mu, 1e-6)))
            spike = rng.random(len(dates)) < 0.004       # 단체주문 등 이상치
            qty = qty + spike * rng.integers(3, 8) * np.ceil(base * scale)
            stockout = (rng.random(len(dates)) < 0.02) & (qty > 2)
            qty = np.where(stockout, np.floor(qty * rng.uniform(0.3, 0.8, len(dates))), qty)
            for d, q, so, pr in zip(dates, qty, stockout, promo[sku]):
                if q > 0 or so:
                    rows.append((d.date(), st, sku, int(q), int(so), int(pr)))

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    sales = pd.DataFrame(rows, columns=["date", "store", "sku", "qty", "stockout", "promo"])
    sales.to_csv(out / "sales.csv", index=False)
    pd.DataFrame([(s, n, lt, 1, cp, moq, sl, c) for s, n, _, _, _, lt, cp, moq, sl, c in SKUS],
                 columns=["sku", "name", "lead_time", "review_period", "case_pack", "moq", "shelf_life",
                          "unit_cost"]).to_csv(out / "sku_master.csv", index=False)

    recent = sales[pd.to_datetime(sales["date"]) > dates[-28]].groupby(["store", "sku"])["qty"].sum() / 28
    inv = recent.reset_index(name="avg")
    inv["on_hand"] = np.floor(inv["avg"] * rng.uniform(0.5, 4, len(inv))).astype(int)
    inv["on_order"] = np.where(rng.random(len(inv)) < 0.3, np.ceil(inv["avg"] * 2), 0).astype(int)
    inv[["store", "sku", "on_hand", "on_order"]].to_csv(out / "inventory.csv", index=False)

    nxt = dates[-1] + pd.Timedelta(days=9)
    pd.DataFrame({"date": pd.date_range(nxt, periods=4), "store": "*", "sku": "B004"}).to_csv(
        out / "promo_plan.csv", index=False)
    pd.DataFrame({"date": [], "name": []}).to_csv(out / "holidays.csv", index=False)
    print(f"{out.resolve()} 에 {len(sales):,}행 생성 ({dates[0]:%Y-%m-%d}~{dates[-1]:%Y-%m-%d})")


if __name__ == "__main__":
    main()
