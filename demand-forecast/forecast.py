#!/usr/bin/env python3
"""프랜차이즈 물류 수요예측 & 발주추천 엔진 (경량, pandas/numpy/openpyxl만 사용)

물류 실무에서 쓰는 방법들을 가볍게 묶었습니다.
  1. 결품일 판매량은 '수요'가 아니라 '잘린 값' → 결측 처리 (과소예측 악순환 방지)
  2. 요일 지수: 점포×품목 패턴을 품목 전체 패턴으로 수축(shrinkage)해 소량 품목도 안정적으로
  3. 공휴일/연휴 전날 효과는 점포별, 프로모션 효과는 품목별로 과거 데이터에서 학습
  4. 수요패턴 분류(ADI/CV², Syntetos-Boylan) + 여러 모델을 백테스트해 시계열마다 최적 모델 선택
  5. 안전재고는 '수요 편차'가 아니라 '보호기간(리드타임+발주주기) 누적 예측오차'로 계산
  6. ABC 등급별 서비스수준, 유통기한 상한(폐기 방지), 박스입수/MOQ 반올림까지 반영한 발주량

사용법:
    python forecast.py --data sample_data --out output
"""
from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

WEEKDAY_KR = "월화수목금토일"

# 한국 공휴일(대체공휴일·선거일 포함). 임시공휴일 등은 holidays.csv 로 추가하세요.
KR_HOLIDAYS = """
2024-01-01 2024-02-09 2024-02-10 2024-02-11 2024-02-12 2024-03-01 2024-04-10 2024-05-05
2024-05-06 2024-05-15 2024-06-06 2024-08-15 2024-09-16 2024-09-17 2024-09-18 2024-10-01
2024-10-03 2024-10-09 2024-12-25
2025-01-01 2025-01-27 2025-01-28 2025-01-29 2025-01-30 2025-03-01 2025-03-03 2025-05-05
2025-05-06 2025-06-03 2025-06-06 2025-08-15 2025-10-03 2025-10-05 2025-10-06 2025-10-07
2025-10-08 2025-10-09 2025-12-25
2026-01-01 2026-02-16 2026-02-17 2026-02-18 2026-03-01 2026-03-02 2026-05-05 2026-05-24
2026-05-25 2026-06-03 2026-06-06 2026-08-15 2026-08-17 2026-09-24 2026-09-25 2026-09-26
2026-10-03 2026-10-05 2026-10-09 2026-12-25
2027-01-01 2027-02-06 2027-02-07 2027-02-08 2027-02-09 2027-03-01 2027-05-05 2027-05-13
2027-06-06 2027-08-15 2027-08-16 2027-09-14 2027-09-15 2027-09-16 2027-10-03 2027-10-04
2027-10-09 2027-10-11 2027-12-25 2027-12-27
""".split()

MODELS = ["SES_느림", "SES_빠름", "홀트_감쇠", "이동평균28", "크로스턴SBA", "앙상블"]
MODEL_DESC = {
    "SES_느림": "단순지수평활(α=0.1) – 안정적 품목",
    "SES_빠름": "단순지수평활(α=0.3) – 수준 변화가 잦은 품목",
    "홀트_감쇠": "감쇠추세 홀트 – 성장/감소 추세 품목",
    "이동평균28": "최근 28일 이동평균",
    "크로스턴SBA": "Croston-SBA – 간헐 수요(가끔 팔리는) 품목",
    "앙상블": "SES·홀트·이동평균 평균 – 예측 결합",
}


@dataclass
class Config:
    horizon: int = 21          # 예측 일수
    backtest_days: int = 56    # 백테스트 기간(일) – 이 기간의 매일을 예측시점으로 가정해 검증
    profile_weeks: int = 12    # 요일지수 학습 기간(주)
    lead_time: int = 2         # sku_master 미기재 시 기본값
    review_period: int = 1     # 발주주기(일). 매일 발주=1
    shelf_life: int = 365
    case_pack: int = 1
    moq: int = 0
    service_level: dict = field(default_factory=lambda: {"A": 0.98, "B": 0.95, "C": 0.90})


# ----------------------------------------------------------------------------
# 데이터 로딩
# ----------------------------------------------------------------------------
def _read_optional(path: Path, **kw):
    return pd.read_csv(path, **kw) if path.exists() else None


def load_inputs(data_dir: str | Path, cfg: Config):
    d = Path(data_dir)
    sales = pd.read_csv(d / "sales.csv", parse_dates=["date"], dtype={"store": str, "sku": str})
    for c in ("stockout", "promo"):
        if c not in sales:
            sales[c] = 0
    sales = sales.groupby(["store", "sku", "date"], as_index=False).agg(
        qty=("qty", "sum"), stockout=("stockout", "max"), promo=("promo", "max"))

    skus = sorted(sales["sku"].unique())
    master = _read_optional(d / "sku_master.csv", dtype={"sku": str})
    defaults = {"name": "", "lead_time": cfg.lead_time, "review_period": cfg.review_period,
                "case_pack": cfg.case_pack, "moq": cfg.moq, "shelf_life": cfg.shelf_life, "unit_cost": 0.0}
    master = (master if master is not None else pd.DataFrame({"sku": skus})).set_index("sku").reindex(skus)
    for c, v in defaults.items():
        master[c] = master[c].fillna(v) if c in master else v
    master["name"] = master["name"].replace("", np.nan).fillna(pd.Series(master.index, index=master.index))

    inventory = _read_optional(d / "inventory.csv", dtype={"store": str, "sku": str})
    if inventory is not None:
        for c in ("on_hand", "on_order"):
            if c not in inventory:
                inventory[c] = 0
    promo_plan = _read_optional(d / "promo_plan.csv", parse_dates=["date"], dtype={"store": str, "sku": str})
    extra = _read_optional(d / "holidays.csv", parse_dates=["date"])
    holidays = pd.to_datetime(KR_HOLIDAYS)
    if extra is not None:
        holidays = holidays.union(pd.DatetimeIndex(extra["date"]))
    return sales, master, inventory, promo_plan, holidays


def build_panel(sales: pd.DataFrame):
    dates = pd.date_range(sales["date"].min(), sales["date"].max(), freq="D")
    keys = sales[["store", "sku"]].drop_duplicates().sort_values(["store", "sku"]).reset_index(drop=True)
    idx = pd.MultiIndex.from_frame(keys)

    def piv(col):
        return (sales.pivot_table(index=["store", "sku"], columns="date", values=col, aggfunc="sum")
                .reindex(index=idx, columns=dates).fillna(0).to_numpy(float).copy())

    Y = piv("qty")                     # 판매 기록이 없는 날 = 0개 판매
    stockout = piv("stockout") > 0
    promo = piv("promo") > 0
    first = sales.groupby(["store", "sku"])["date"].min().reindex(idx).to_numpy()
    Y[dates.values[None, :] < first[:, None]] = np.nan   # 취급 시작 전은 결측
    Y[stockout] = np.nan               # 결품일 판매량은 실제 수요보다 작다 → 결측 처리
    return keys, dates, Y, promo


# ----------------------------------------------------------------------------
# 요일지수 · 이벤트 승수 (계절성/특수일 보정)
# ----------------------------------------------------------------------------
def weekday_profile(Y, promo, dow, event_day, sku_codes, upto, weeks):
    lo = max(0, upto - weeks * 7)
    W = Y[:, lo:upto].copy()
    W[:, event_day[lo:upto]] = np.nan
    W[promo[:, lo:upto]] = np.nan
    d = dow[lo:upto]
    sums = np.stack([np.nansum(W[:, d == k], 1) for k in range(7)], 1)
    cnts = np.stack([np.sum(~np.isnan(W[:, d == k]), 1) for k in range(7)], 1)
    means = np.where(cnts > 0, sums / np.maximum(cnts, 1), np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = means / np.nanmean(means, 1, keepdims=True)
        g = pd.DataFrame(np.nan_to_num(means)).groupby(sku_codes).sum()
        pooled = (g.div(g.mean(1), axis=0)).reindex(sku_codes).to_numpy()
    pooled = np.where(np.isfinite(pooled), pooled, 1.0)
    units = np.nansum(W, 1, keepdims=True)
    w = units / (units + 100.0)        # 판매량이 적을수록 품목 공통 패턴을 더 신뢰
    idx = np.where(np.isfinite(raw), w * raw + (1 - w) * pooled, pooled)
    idx = np.clip(idx / idx.mean(1, keepdims=True), 0.2, 5.0)
    return idx / idx.mean(1, keepdims=True)


def event_multipliers(Y, promo, WDm, hol, pre, store_codes, sku_codes, upto):
    """공휴일/연휴 전날 승수(점포별), 프로모션 승수(품목별)를 과거 실적/기준선 비율로 추정."""
    T = Y.shape[1]
    special = (hol | pre)[:T]
    Z0 = Y / WDm[:, :T]
    clean = np.where(~special[None, :] & ~promo, Z0, np.nan)
    base = pd.DataFrame(clean.T).rolling(28, min_periods=7).median().shift(1).to_numpy().T
    expected = base * WDm[:, :T]
    valid = ~np.isnan(Y) & ~np.isnan(expected) & (expected > 0)
    valid[:, upto:] = False

    def ratio(mask, groups, prior_n):
        act = pd.Series(np.where(mask, Y, 0).sum(1)).groupby(groups).sum()
        exp = pd.Series(np.where(mask, expected, 0).sum(1)).groupby(groups).sum()
        n = pd.DataFrame(mask).groupby(groups).any().sum(1)          # 그룹별 해당 이벤트 '일수'
        r = (act / exp.replace(0, np.nan)).fillna(1.0)
        m = 1 + (r - 1) * n / (n + prior_n)                          # 관측일이 적으면 1(무효과)로 수축
        return m.clip(0.2, 3.0).reindex(groups).to_numpy()

    m_hol = ratio(valid & hol[None, :T] & ~promo, store_codes, 3)
    m_pre = ratio(valid & pre[None, :T] & ~promo, store_codes, 3)
    m_promo = ratio(valid & promo & ~special[None, :], sku_codes, 5)
    return m_hol, m_pre, m_promo


def multiplier_matrix(WD, dow_all, hol, pre, promo_all, m_hol, m_pre, m_promo):
    M = WD[:, dow_all].copy()
    M[:, hol] *= m_hol[:, None]
    M[:, pre] *= m_pre[:, None]
    return np.where(promo_all, M * m_promo[:, None], M)


# ----------------------------------------------------------------------------
# 모델 시뮬레이션 (시계열 전체를 벡터화해 하루씩 진행 → 수만 개 시계열도 가볍게)
# ----------------------------------------------------------------------------
def simulate(Z, Y, M, origins, H, P, final_h=0):
    """Z: 보정수요(요일/이벤트 제거), Y: 실제판매(결측=NaN), M: 승수 행렬(S×(T+미래)).
    origins 시점마다 H일 앞을 예측해 오차를 누적하고, 마지막 시점에서 final_h일 예측을 반환."""
    S, T = Z.shape
    a1, a2, ah, bh, phi, ac = 0.1, 0.3, 0.2, 0.05, 0.9, 0.1
    l1 = np.full(S, np.nan); l2 = l1.copy(); lh = l1.copy(); bt = np.zeros(S)
    q = l1.copy(); p = l1.copy(); k = np.ones(S)
    Zf = np.nan_to_num(Z); Zc = np.concatenate([np.zeros((S, 1)), np.cumsum(Zf, 1)], 1)
    Nc = np.concatenate([np.zeros((S, 1)), np.cumsum(~np.isnan(Z), 1)], 1)
    hcurve = {h: np.cumsum(phi ** np.arange(1, h + 1)) for h in (H, final_h) if h}
    origin_set = set(origins)
    acc = {m: {k_: np.zeros(S) for k_ in ("abs", "err", "act", "sqP", "nP")} for m in MODELS + ["단순요일반복"]}
    hmask = np.arange(H)[None, :] < P[:, None]
    final = None

    def forecast_base(t, h):
        lo = max(0, t + 1 - 28)
        ma = (Zc[:, t + 1] - Zc[:, lo]) / np.maximum(Nc[:, t + 1] - Nc[:, lo], 1)
        out = {
            "SES_느림": np.repeat(l1[:, None], h, 1),
            "SES_빠름": np.repeat(l2[:, None], h, 1),
            "홀트_감쇠": lh[:, None] + bt[:, None] * hcurve[h][None, :],
            "이동평균28": np.repeat(ma[:, None], h, 1),
            "크로스턴SBA": np.repeat(np.nan_to_num((1 - ac / 2) * q / p)[:, None], h, 1),
        }
        out["앙상블"] = (np.nan_to_num(out["SES_느림"]) + np.nan_to_num(out["홀트_감쇠"]) + out["이동평균28"]) / 3
        return {m: np.clip(np.nan_to_num(v), 0, None) for m, v in out.items()}

    for t in range(T):
        z = Z[:, t]; ok = ~np.isnan(z)
        for lv, a in ((l1, a1), (l2, a2)):
            lv[ok & np.isnan(lv)] = z[ok & np.isnan(lv)]
            lv[ok] = a * z[ok] + (1 - a) * lv[ok]
        new = ok & np.isnan(lh); lh[new] = z[new]
        prev = lh.copy()
        lh[:] = np.where(ok, ah * z + (1 - ah) * (prev + phi * bt), prev + phi * bt)
        bt[:] = np.where(ok & ~new, bh * (lh - prev) + (1 - bh) * phi * bt, phi * bt)
        pos = ok & (z > 0)
        init = pos & np.isnan(q)
        q[init] = z[init]; p[init] = k[init]
        upd = pos & ~init
        q[upd] += ac * (z[upd] - q[upd]); p[upd] += ac * (k[upd] - p[upd])
        k[pos] = 1; k[ok & ~pos] += 1

        if t in origin_set:
            A = Y[:, t + 1:t + 1 + H]
            fc = {m: b * M[:, t + 1:t + 1 + H] for m, b in forecast_base(t, H).items()}
            same_dow = t + 1 + np.arange(H) - 7 * np.ceil((np.arange(H) + 1) / 7).astype(int)
            fc["단순요일반복"] = np.nan_to_num(Y[:, same_dow])  # 비교용 벤치마크: 지난주 같은 요일
            have = ~np.isnan(A)
            for m, F in fc.items():
                e = np.where(have, F - np.nan_to_num(A), 0)
                a_ = acc[m]
                a_["abs"] += np.abs(e).sum(1); a_["err"] += e.sum(1)
                a_["act"] += np.where(have, A, 0).sum(1)
                cum_err = np.where(hmask, F - np.where(have, A, F), 0).sum(1)  # 보호기간 누적오차
                a_["sqP"] += cum_err ** 2; a_["nP"] += 1
        if t == T - 1 and final_h:
            final = {m: b * M[:, T:T + final_h] for m, b in forecast_base(t, final_h).items()}
    return acc, final


# ----------------------------------------------------------------------------
# 분류 · 등급
# ----------------------------------------------------------------------------
def demand_pattern(Y, days=91):
    W = Y[:, -days:]
    out = []
    for row in W:
        v = row[~np.isnan(row)]
        nz = v[v > 0]
        if len(nz) < 2:
            out.append("간헐(희소)"); continue
        adi = len(v) / len(nz)
        cv2 = (nz.std() / nz.mean()) ** 2
        out.append({(False, False): "안정형", (False, True): "변동형",
                    (True, False): "간헐형", (True, True): "불규칙형"}[(adi >= 1.32, cv2 >= 0.49)])
    return out


def abc_class(keys, Y, master, days=91):
    qty = pd.Series(np.nansum(Y[:, -days:], 1)).groupby(keys["sku"].values).sum()
    cost = master["unit_cost"].reindex(qty.index).fillna(0)
    value = qty * cost if cost.sum() > 0 else qty
    share = value.sort_values(ascending=False).cumsum() / max(value.sum(), 1e-9)
    cls = pd.Series(np.where(share <= 0.8, "A", np.where(share <= 0.95, "B", "C")), index=share.index)
    return keys["sku"].map(cls).fillna("C").to_numpy()


# ----------------------------------------------------------------------------
# 메인 파이프라인
# ----------------------------------------------------------------------------
def run(data_dir, out_dir, cfg: Config):
    sales, master, inventory, promo_plan, holidays = load_inputs(data_dir, cfg)
    keys, dates, Y, promo = build_panel(sales)
    S, T = Y.shape
    sku_codes = keys["sku"].to_numpy(); store_codes = keys["store"].to_numpy()
    m = master.reindex(sku_codes)
    LT = m["lead_time"].to_numpy(int); R = m["review_period"].to_numpy(int)
    P = LT + R
    H = max(cfg.horizon, int(P.max()))
    if H > cfg.horizon:
        print(f"[알림] 최대 보호기간({P.max()}일)에 맞춰 예측일수를 {H}일로 늘렸습니다.")

    future = pd.date_range(dates[-1] + pd.Timedelta(days=1), periods=H, freq="D")
    all_dates = dates.append(future)
    dow_all = all_dates.dayofweek.to_numpy()
    hol = all_dates.isin(holidays)
    pre = (all_dates + pd.Timedelta(days=1)).isin(holidays) & ~hol
    promo_all = np.concatenate([promo, np.zeros((S, H), bool)], 1)
    if promo_plan is not None:
        for r in promo_plan.itertuples():
            j = all_dates.get_indexer([r.date])[0]
            if j >= T:
                hit = (sku_codes == r.sku) & ((str(r.store) in ("*", "nan", "")) | (store_codes == r.store))
                promo_all[hit, j] = True

    def fit(upto):
        WD = weekday_profile(Y, promo, dow_all[:T], hol | pre, sku_codes, upto, cfg.profile_weeks)
        mh, mp, mpr = event_multipliers(Y, promo, WD[:, dow_all], hol, pre, store_codes, sku_codes, upto)
        M = multiplier_matrix(WD, dow_all, hol, pre, promo_all, mh, mp, mpr)
        Z = Y / M[:, :T]
        hist = Z[:, :upto]
        med = np.nanmedian(hist, 1, keepdims=True)
        mad = np.nanmedian(np.abs(hist - med), 1, keepdims=True)
        cap = np.where(mad > 0, med + 6 * 1.4826 * mad, np.nanpercentile(hist, 99, axis=1, keepdims=True))
        return np.minimum(Z, np.nan_to_num(cap, nan=np.inf)), M, (mh, mp, mpr)

    # 1) 백테스트 (정보 누설 방지를 위해 검증구간 이전 데이터로만 지수/승수 학습)
    bt = min(cfg.backtest_days, T - H - 60)
    origins = list(range(T - 1 - H - bt + 1, T - H)) if bt > 0 else []
    if origins:
        Zb, Mb, _ = fit(origins[0] + 1)
        acc, _ = simulate(Zb, Y, Mb, origins, H, P)
    else:
        print("[경고] 이력이 짧아 백테스트를 생략합니다(최소 약 90일 권장).")
        acc = {mm: {k_: np.zeros(S) for k_ in ("abs", "err", "act", "sqP", "nP")} for mm in MODELS + ["단순요일반복"]}

    # 2) 모델 선택: MAE + |편향| (간헐수요에서 '0 예측'이 뽑히는 함정 방지)
    scores = np.stack([(acc[mm]["abs"] + np.abs(acc[mm]["err"])) / np.maximum(acc[mm]["act"], 1) for mm in MODELS], 1)
    pattern = demand_pattern(Y)
    intermittent = np.isin(pattern, ["간헐형", "불규칙형", "간헐(희소)"])
    scores[~intermittent, MODELS.index("크로스턴SBA")] = np.inf   # Croston은 간헐 수요에만 사용
    has_bt = acc["앙상블"]["nP"] > 0
    choice = np.where(has_bt, scores.argmin(1), MODELS.index("앙상블"))

    # 3) 전체 데이터로 재학습 후 미래 예측
    Zf, Mf, (mh, mp, mpr) = fit(T)
    _, final = simulate(Zf, Y, Mf, [], H, P, final_h=H)
    F = np.stack([final[mm] for mm in MODELS], 0)[choice, np.arange(S)].round(1)  # 엑셀과 동일한 값으로 계산

    pick = lambda key: np.stack([acc[mm][key] for mm in MODELS], 0)[choice, np.arange(S)]
    abs_e, err, act, sqP, nP = (pick(k_) for k_ in ("abs", "err", "act", "sqP", "nP"))
    hmask = np.arange(H)[None, :] < P[:, None]
    daily_mean = (F * hmask).sum(1) / P
    sigma_day = np.where(nP > 0, np.sqrt(sqP / np.maximum(nP, 1)) / np.sqrt(P), np.sqrt(daily_mean))
    sigma_day = np.maximum(sigma_day, 0.5 * np.sqrt(daily_mean))   # 포아송 하한의 절반
    sigma_day = sigma_day.round(3)

    abc = abc_class(keys, Y, master)
    sl = np.array([cfg.service_level[c] for c in abc])
    z = np.array([NormalDist().inv_cdf(s) for s in sl])
    D_P = (F * hmask).sum(1)
    ss = z * sigma_day * np.sqrt(P)
    shelf = m["shelf_life"].to_numpy(int)
    cap_days = LT + shelf
    cap = np.where(cap_days <= H, (F * (np.arange(H)[None, :] < cap_days[:, None])).sum(1), np.inf)
    target = np.minimum(D_P + ss, cap)

    inv = keys.copy(); inv["on_hand"] = 0.0; inv["on_order"] = 0.0
    if inventory is not None:
        inventory = inventory.groupby(["store", "sku"], as_index=False)[["on_hand", "on_order"]].sum()
        inv = keys.merge(inventory, on=["store", "sku"], how="left").fillna({"on_hand": 0, "on_order": 0})
    need = np.maximum(0, target - inv["on_hand"].to_numpy() - inv["on_order"].to_numpy())
    pack = m["case_pack"].to_numpy(float).clip(1); moq = m["moq"].to_numpy(float)
    order = np.where(need <= 0, 0, np.maximum(moq, np.ceil(need / pack) * pack))

    plan = keys.assign(
        name=m["name"].to_numpy(), abc=abc, pattern=pattern, model=[MODELS[c] for c in choice],
        lead_time=LT, review_period=R, protect_days=P, forecast_protect=D_P.round(1),
        sigma_day=sigma_day.round(3), service_level=sl, safety_stock=ss.round(1),
        shelf_life=shelf, target_stock=target.round(1), on_hand=inv["on_hand"].to_numpy(),
        on_order=inv["on_order"].to_numpy(), case_pack=pack.astype(int), moq=moq.astype(int),
        order_qty=order.astype(int), unit_cost=m["unit_cost"].to_numpy(float))
    plan["order_amount"] = plan["order_qty"] * plan["unit_cost"]

    daily = pd.DataFrame(F.round(1), columns=future)
    daily.insert(0, "sku", sku_codes); daily.insert(0, "store", store_codes)
    daily.insert(2, "name", m["name"].to_numpy())

    bench = acc["단순요일반복"]
    accuracy = keys.assign(
        name=m["name"].to_numpy(), pattern=pattern, model=[MODELS[c] for c in choice],
        actual=act.round(1), abs_err=abs_e.round(1), bias=err.round(1),
        bench_abs_err=bench["abs"].round(1))
    effects = dict(holiday=pd.Series(mh, index=store_codes).groupby(level=0).first(),
                   pre_holiday=pd.Series(mp, index=store_codes).groupby(level=0).first(),
                   promo=pd.Series(mpr, index=sku_codes).groupby(level=0).first())

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    plan.to_csv(out / "order_plan.csv", index=False, encoding="utf-8-sig")
    daily.rename(columns={d: d.strftime("%Y-%m-%d") for d in future}).to_csv(
        out / "forecast_daily.csv", index=False, encoding="utf-8-sig")
    accuracy.to_csv(out / "accuracy.csv", index=False, encoding="utf-8-sig")

    from report import write_excel
    write_excel(out / "수요예측_발주추천.xlsx", plan, daily, future, accuracy, effects, holidays, dates, cfg, H, MODEL_DESC)

    tot_act = accuracy["actual"].sum()
    if tot_act > 0:
        wape = accuracy["abs_err"].sum() / tot_act
        wape_b = accuracy["bench_abs_err"].sum() / tot_act
        print(f"백테스트 WAPE(오차율): 엔진 {wape:.1%}  vs  지난주 같은요일 방식 {wape_b:.1%}  "
              f"→ 오차 {1 - wape / wape_b:.0%} 감소")
        print(f"예측 편향: {accuracy['bias'].sum() / tot_act:+.1%} (양수=과대예측)")
    print(f"시계열 {S}개, 이력 {T}일({dates[0]:%Y-%m-%d}~{dates[-1]:%Y-%m-%d}), 예측 {H}일")
    print(f"발주 품목 {int((plan['order_qty'] > 0).sum())}건, 총 발주금액 {plan['order_amount'].sum():,.0f}원")
    print(f"결과: {out.resolve()}")
    return plan, daily, accuracy


def main():
    ap = argparse.ArgumentParser(description="프랜차이즈 물류 수요예측 & 발주추천")
    ap.add_argument("--data", default="sample_data", help="입력 CSV 폴더")
    ap.add_argument("--out", default="output", help="결과 폴더")
    ap.add_argument("--horizon", type=int, default=21)
    ap.add_argument("--backtest-days", type=int, default=56)
    ap.add_argument("--sl-a", type=float, default=0.98, help="A등급 서비스수준(결품 안 날 확률)")
    ap.add_argument("--sl-b", type=float, default=0.95)
    ap.add_argument("--sl-c", type=float, default=0.90)
    a = ap.parse_args()
    cfg = Config(horizon=a.horizon, backtest_days=a.backtest_days,
                 service_level={"A": a.sl_a, "B": a.sl_b, "C": a.sl_c})
    run(a.data, a.out, cfg)


if __name__ == "__main__":
    main()
