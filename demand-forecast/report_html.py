"""웹 페이지(dashboard.html) 작성. 서버 없이 브라우저로 열면 되고, 현재고를 입력하면 발주량이 즉시 다시 계산됩니다."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

HIST_DAYS = 56
WEEKDAY_KR = "월화수목금토일"


def _num(v, nd=1):
    return None if v is None or (isinstance(v, float) and not math.isfinite(v)) else round(float(v), nd)


def build_payload(plan, F, observed, stockout, dates, future, holidays, accuracy, effects, cfg, H, model_desc, sample=False):
    hol = set(pd.DatetimeIndex(holidays).normalize())
    hist_dates = dates[-HIST_DAYS:]
    obs = observed[:, -HIST_DAYS:]
    so = stockout[:, -HIST_DAYS:]
    acc = accuracy.reset_index(drop=True)
    rows = []
    for i, p in enumerate(plan.itertuples(index=False)):
        rows.append({
            "st": p.store, "sku": p.sku, "nm": p.name, "abc": p.abc, "pat": p.pattern, "mdl": p.model,
            "lt": int(p.lead_time), "r": int(p.review_period), "sig": float(p.sigma_day),
            "shelf": int(p.shelf_life), "pack": int(p.case_pack), "moq": int(p.moq), "cost": float(p.unit_cost),
            "oh": float(p.on_hand), "oo": float(p.on_order),
            "f": [float(x) for x in F[i]],
            "h": [None if np.isnan(x) else float(x) for x in obs[i]],
            "so": [int(j) for j in np.nonzero(so[i])[0]],
            "act": float(acc.at[i, "actual"]), "ae": float(acc.at[i, "abs_err"]),
            "be": float(acc.at[i, "bench_abs_err"]), "bias": float(acc.at[i, "bias"]),
        })

    def day(d):
        return {"d": d.strftime("%Y-%m-%d"), "l": f"{d.month}/{d.day}", "w": WEEKDAY_KR[d.dayofweek],
                "hol": d.normalize() in hol}

    return {
        "asOf": dates[-1].strftime("%Y-%m-%d"),
        "from": dates[0].strftime("%Y-%m-%d"),
        "orderDay": day(future[0]),
        "H": int(H),
        "backtestDays": int(cfg.backtest_days),
        "sl": cfg.service_level,
        "hist": [day(d) for d in hist_dates],
        "fut": [day(d) for d in future],
        "effects": {
            "holiday": {k: _num(v, 2) for k, v in effects["holiday"].items()},
            "pre": {k: _num(v, 2) for k, v in effects["pre_holiday"].items()},
            "promo": {k: _num(v, 2) for k, v in effects["promo"].items()},
        },
        "models": model_desc,
        "sample": bool(sample),
        "rows": rows,
    }


def render(payload, fragment=False):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    body = TEMPLATE.replace("__DATA__", data)
    if fragment:
        return body
    return f'<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n' \
           f'<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n' \
           f'</head>\n<body>\n{body}\n</body>\n</html>\n'


def write_html(path, payload, fragment=False):
    Path(path).write_text(render(payload, fragment), encoding="utf-8")


TEMPLATE = r"""<title>발주 콘솔</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap">
<style>
/* 레이아웃: 상단 요약 → 탭 → (발주표 | 품목 상세) 2단, 좁은 화면에서는 1단 */
:root{
  --bg:#f3f5f7; --surface:#ffffff; --surface-2:#f8fafb; --ink:#14202b; --ink-2:#465462; --muted:#768391;
  --line:#dbe1e7; --line-2:#eaeef2; --accent:#1d6aae; --accent-soft:#e2edf7;
  --fc:#2a78d6; --band:rgba(42,120,214,.15); --bench:#9aa5b1; --hol:#fbeadf; --hol-ink:#a4511c;
  --crit:#b72a2a; --crit-bg:#fbe6e5; --warn:#9a5a00; --warn-bg:#fcefd6; --ok:#1a7447; --ok-bg:#e0f2e8;
  --up:#c4572a; --down:#2f6db0;
  --sans:"IBM Plex Sans KR","Apple SD Gothic Neo","Malgun Gothic",system-ui,sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0e141a; --surface:#151d25; --surface-2:#19222b; --ink:#e6ecf1; --ink-2:#b2bec9; --muted:#7f8c98;
  --line:#28333e; --line-2:#202a34; --accent:#62a6e8; --accent-soft:#1a2e42;
  --fc:#3987e5; --band:rgba(57,135,229,.22); --bench:#66727e; --hol:#33261c; --hol-ink:#f0a874;
  --crit:#ff8078; --crit-bg:#3a1c1b; --warn:#f2b860; --warn-bg:#382a14; --ok:#63d49c; --ok-bg:#16301f;
  --up:#e9875e; --down:#6aa4e6; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0e141a; --surface:#151d25; --surface-2:#19222b; --ink:#e6ecf1; --ink-2:#b2bec9; --muted:#7f8c98;
  --line:#28333e; --line-2:#202a34; --accent:#62a6e8; --accent-soft:#1a2e42;
  --fc:#3987e5; --band:rgba(57,135,229,.22); --bench:#66727e; --hol:#33261c; --hol-ink:#f0a874;
  --crit:#ff8078; --crit-bg:#3a1c1b; --warn:#f2b860; --warn-bg:#382a14; --ok:#63d49c; --ok-bg:#16301f;
  --up:#e9875e; --down:#6aa4e6; color-scheme:dark}
*{box-sizing:border-box}
[hidden]{display:none!important}
body{background:var(--bg);color:var(--ink);font:14px/1.5 var(--sans);margin:0}
.wrap{max-width:1360px;margin:0 auto;padding-block:20px 48px;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));
  display:grid;gap:18px}
.num,td.n,.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
header{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px}
.eyebrow{font-size:12px;letter-spacing:.06em;color:var(--muted);font-weight:500}
h1{font-size:26px;line-height:1.2;margin:2px 0 0;font-weight:700;text-wrap:balance}
.sub{color:var(--ink-2);font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:10px;overflow:hidden}
.kpi{background:var(--surface);padding:14px 16px;display:grid;gap:4px;min-width:0}
.kpi .k{font-size:12px;color:var(--muted);letter-spacing:.02em}
.kpi .v{font-family:var(--mono);font-size:24px;font-weight:500;line-height:1.15}
.kpi .d{font-size:12px;color:var(--ink-2)}
.kpi .v.crit{color:var(--crit)}
@media (max-width:760px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);overflow-x:auto}
.tab{appearance:none;border:0;background:none;color:var(--ink-2);font:600 14px var(--sans);padding:10px 14px;
  border-bottom:2px solid transparent;cursor:pointer;white-space:nowrap}
.tab[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--accent)}
.tab:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.controls{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:flex-end}
.field{display:grid;gap:3px;font-size:12px;color:var(--muted)}
select,input[type=search],input[type=number]{font:14px var(--sans);color:var(--ink);background:var(--surface);
  border:1px solid var(--line);border-radius:6px;padding:6px 8px;min-width:0}
input[type=number]{font-family:var(--mono);width:68px;text-align:right;padding:3px 6px}
.sl{display:flex;gap:6px;align-items:center}
.sl input{width:72px;padding:6px 8px}
.btn{appearance:none;border:1px solid var(--line);background:var(--surface);color:var(--ink);font:600 13px var(--sans);
  padding:7px 12px;border-radius:6px;cursor:pointer}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--surface)}
.btn:hover{border-color:var(--accent)}
.spacer{flex:1}
.toast{font-size:12px;color:var(--ok);min-height:1em}
.main{display:grid;grid-template-columns:minmax(0,1fr) 420px;gap:18px;align-items:start}
@media (max-width:1100px){.main{grid-template-columns:minmax(0,1fr)}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;min-width:0}
.tablebox{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
th{font-size:11px;color:var(--muted);font-weight:600;text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);
  white-space:nowrap;background:var(--surface-2);position:sticky;top:0;letter-spacing:.02em}
th.n,td.n{text-align:right}
td{padding:6px 8px;border-bottom:1px solid var(--line-2);white-space:nowrap}
tbody tr{cursor:pointer}
tbody tr:hover{background:var(--surface-2)}
tbody tr.sel{background:var(--accent-soft)}
td.item{white-space:normal;min-width:130px}
td.item small{display:block;color:var(--muted);font-size:11px}
td.q{font-weight:600}
td.q.zero{color:var(--muted);font-weight:400}
.chip{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:600;padding:2px 7px;border-radius:999px;white-space:nowrap}
.chip::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}
.chip.crit{color:var(--crit);background:var(--crit-bg)}
.chip.warn{color:var(--warn);background:var(--warn-bg)}
.chip.ok{color:var(--ok);background:var(--ok-bg)}
.chip.idle{color:var(--muted);background:var(--surface-2)}
.grade{font-family:var(--mono);font-weight:500;font-size:12px;padding:1px 6px;border:1px solid var(--line);border-radius:4px}
.more{padding:10px;text-align:center}
.detail{position:sticky;top:env(safe-area-inset-top,0px);padding:16px;display:grid;gap:14px}
.detail h2{font-size:18px;margin:0;line-height:1.3;text-wrap:balance}
.detail .meta{display:flex;flex-wrap:wrap;gap:6px;font-size:12px;color:var(--ink-2)}
.tag{border:1px solid var(--line);border-radius:4px;padding:1px 6px}
.legend{display:flex;flex-wrap:wrap;gap:12px;font-size:12px;color:var(--ink-2)}
.legend i{display:inline-block;width:14px;height:2px;vertical-align:middle;margin-right:5px}
.legend i.band{height:10px;background:var(--band)}
.legend i.hol{height:10px;background:var(--hol)}
.chart{position:relative}
.chart svg{display:block;width:100%;height:auto}
.chart svg text{fill:var(--muted);font:10px var(--mono)}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--line);border-radius:6px;
  padding:6px 8px;font-size:12px;box-shadow:0 4px 14px rgba(0,0,0,.12);white-space:nowrap}
.tip b{font-family:var(--mono);font-weight:500}
.calc{display:grid;grid-template-columns:1fr auto;gap:4px 12px;font-size:13px;border-top:1px solid var(--line-2);padding-top:12px}
.calc .n{font-family:var(--mono);text-align:right}
.calc .tot{font-weight:700;border-top:1px solid var(--line);padding-top:4px}
.calc .note{grid-column:1/-1;font-size:12px;color:var(--muted)}
.facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
.facts div{background:var(--surface-2);border-radius:6px;padding:8px}
.facts span{display:block;font-size:11px;color:var(--muted)}
.facts b{font-family:var(--mono);font-weight:500}
.panel{padding:16px;display:grid;gap:14px}
.panel h3{margin:0;font-size:16px}
.panel p{margin:0;color:var(--ink-2);max-width:72ch}
.bars td{vertical-align:middle}
.bar{position:relative;height:8px;background:var(--line-2);border-radius:4px;min-width:120px}
.bar span{position:absolute;left:0;top:0;bottom:0;border-radius:4px}
.bar2{display:grid;gap:3px}
.div{position:relative;height:12px;min-width:160px}
.div::before{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;border-left:1px solid var(--muted)}
.div span{position:absolute;top:2px;height:8px;border-radius:2px}
.method{display:grid;gap:12px;max-width:80ch}
.method ol{margin:0;padding-left:20px;display:grid;gap:8px;color:var(--ink-2)}
.method b{color:var(--ink)}
.empty{padding:24px;color:var(--muted)}
@media (prefers-reduced-motion:no-preference){tbody tr{transition:background .12s}}
</style>

<div class="wrap">
  <header>
    <div>
      <div class="eyebrow" id="eyebrow"></div>
      <h1>발주 콘솔</h1>
      <div class="sub" id="sub"></div>
    </div>
    <span class="chip warn" id="sample" hidden>예시 데이터</span>
  </header>

  <section class="kpis" aria-label="요약">
    <div class="kpi"><span class="k">총 발주금액</span><span class="v" id="kAmt"></span><span class="d" id="kAmtD"></span></div>
    <div class="kpi"><span class="k">발주 필요</span><span class="v" id="kCnt"></span><span class="d" id="kCntD"></span></div>
    <div class="kpi"><span class="k">입고 전 결품위험</span><span class="v crit" id="kRisk"></span><span class="d">이번 발주로는 못 막음 · 긴급배송 검토</span></div>
    <div class="kpi"><span class="k">예측 오차율 (최근 백테스트)</span><span class="v" id="kErr"></span><span class="d" id="kErrD"></span></div>
  </section>

  <nav class="tabs" role="tablist">
    <button class="tab" role="tab" id="t-order" aria-selected="true" data-p="order">발주</button>
    <button class="tab" role="tab" id="t-acc" aria-selected="false" data-p="acc">예측 정확도</button>
    <button class="tab" role="tab" id="t-eff" aria-selected="false" data-p="eff">특수일 효과</button>
    <button class="tab" role="tab" id="t-how" aria-selected="false" data-p="how">계산 방식</button>
  </nav>

  <section id="p-order" style="display:grid;gap:14px">
    <div class="controls">
      <label class="field">점포<select id="fStore"></select></label>
      <label class="field">상태<select id="fStatus">
        <option value="">전체</option><option value="crit">결품위험</option><option value="order">발주 필요</option>
        <option value="warn">폐기위험</option><option value="none">발주 없음</option></select></label>
      <label class="field">등급<select id="fAbc"><option value="">전체</option><option>A</option><option>B</option><option>C</option></select></label>
      <label class="field">품목 검색<input type="search" id="fQ" placeholder="품목명·SKU"></label>
      <label class="field">정렬<select id="fSort"><option value="risk">긴급순</option><option value="amt">발주금액순</option><option value="store">점포·품목순</option></select></label>
      <div class="field">서비스수준 (결품 안 날 확률)
        <div class="sl"><span>A</span><input type="number" id="slA" step="0.5" min="50" max="99.9"><span>B</span><input type="number" id="slB" step="0.5" min="50" max="99.9"><span>C</span><input type="number" id="slC" step="0.5" min="50" max="99.9"></div>
      </div>
      <span class="spacer"></span>
      <div style="display:grid;gap:3px;justify-items:end">
        <div style="display:flex;gap:8px"><button class="btn" id="bReset">입력 초기화</button><button class="btn primary" id="bCopy">발주서 복사</button></div>
        <span class="toast" id="toast" role="status"></span>
      </div>
    </div>
    <div class="main">
      <div class="card tablebox">
        <table>
          <thead><tr><th>점포</th><th>품목</th><th>등급</th><th>상태</th><th class="n">보호기간 수요</th><th class="n">안전재고</th>
          <th class="n">목표재고</th><th class="n">현재고</th><th class="n">입고예정</th><th class="n">발주수량</th><th class="n">금액(원)</th></tr></thead>
          <tbody id="tb"></tbody>
        </table>
        <div class="more" id="more"></div>
      </div>
      <aside class="card detail" id="detail" aria-live="polite"></aside>
    </div>
  </section>

  <section id="p-acc" class="card panel" hidden>
    <h3>품목별 예측 오차율</h3>
    <p id="accNote"></p>
    <div class="legend"><span><i style="background:var(--fc);height:8px"></i>이 엔진</span><span><i style="background:var(--bench);height:8px"></i>지난주 같은 요일 그대로</span></div>
    <div class="tablebox"><table class="bars"><thead><tr><th>품목</th><th>수요패턴</th><th class="n">이 엔진</th><th class="n">기존 방식</th><th>비교</th><th class="n">오차 감소</th><th class="n">편향</th></tr></thead><tbody id="accTb"></tbody></table></div>
  </section>

  <section id="p-eff" class="card panel" hidden>
    <h3>학습된 특수일 효과</h3>
    <p>평소 같은 요일 대비 판매 배율입니다. 1.00이면 평소와 같고, 1.30이면 30% 더 팔립니다. 관측일이 적은 효과는 1.00 쪽으로 보수적으로 줄여 반영합니다.</p>
    <div class="legend"><span><i style="background:var(--down);height:8px"></i>감소</span><span><i style="background:var(--up);height:8px"></i>증가</span></div>
    <div class="tablebox"><table class="bars"><thead><tr><th>점포</th><th class="n">공휴일</th><th>0.3 ← 1.0 → 1.7+</th><th class="n">연휴 전날</th><th>0.3 ← 1.0 → 1.7+</th></tr></thead><tbody id="effSt"></tbody></table></div>
    <h3>프로모션 효과 (행사 이력이 있는 품목)</h3>
    <div class="tablebox"><table class="bars"><thead><tr><th>품목</th><th class="n">행사 배율</th><th>0.3 ← 1.0 → 1.7+</th></tr></thead><tbody id="effPr"></tbody></table></div>
  </section>

  <section id="p-how" class="card panel" hidden>
    <div class="method">
      <h3>발주량은 이렇게 계산됩니다</h3>
      <ol>
        <li><b>보호기간 수요</b>: 오늘 발주한 물건이 들어온 뒤 다음 입고 때까지 버텨야 하는 기간(리드타임 + 발주주기)의 예측 수요 합계.</li>
        <li><b>안전재고</b>: 정규분포 z(서비스수준) × 일 환산 예측오차 × √보호기간. 예측오차는 최근 8주 동안 매일 실제로 예측해 보고 틀린 정도를 잰 값입니다. 잘 맞는 품목일수록 안전재고가 얇아집니다.</li>
        <li><b>목표재고</b>: 보호기간 수요 + 안전재고. 단, 리드타임 + 유통기한 안에 팔 수 있는 양을 넘지 않게 상한을 둡니다(폐기 방지).</li>
        <li><b>발주수량</b>: 목표재고 − 현재고 − 입고예정을 박스입수 단위로 올림하고 MOQ 이상으로 맞춥니다.</li>
        <li><b>결품위험</b>: 현재고 + 입고예정이 리드타임 동안의 예측 수요보다 적으면 이번 발주가 도착하기 전에 떨어집니다. 긴급배송이나 점포 간 이동을 검토하세요.</li>
        <li><b>폐기위험</b>: 이미 가진 재고가 유통기한 안에 팔 수 있는 양을 넘은 경우입니다. 행사나 다른 점포로의 이동을 검토하세요.</li>
      </ol>
      <h3>예측은 이렇게 만듭니다</h3>
      <ol>
        <li>결품일 판매량은 실제 수요보다 작게 찍히므로 학습에서 뺍니다.</li>
        <li>요일 패턴은 점포별로 배우되, 판매량이 적은 품목은 같은 품목의 전 점포 공통 패턴을 더 신뢰합니다.</li>
        <li>공휴일·연휴 전날 효과는 점포별, 행사 효과는 품목별로 과거 실적에서 배웁니다.</li>
        <li>여러 예측 방식 중 점포×품목마다 최근 8주 백테스트에서 가장 잘 맞힌 방식을 자동으로 고릅니다.</li>
      </ol>
      <h3>예측 방식</h3>
      <ol id="models"></ol>
    </div>
  </section>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('data').textContent);
const $ = id => document.getElementById(id);
const fmt0 = n => Math.round(n).toLocaleString('ko-KR');
const fmt1 = n => (Math.round(n*10)/10).toLocaleString('ko-KR',{minimumFractionDigits:1,maximumFractionDigits:1});
const pct = (n,d=1) => (n*100).toFixed(d)+'%';
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const KEY = 'order-console:'+D.asOf;

// 정규분포 역함수 (Acklam 근사) — 엑셀 NORMSINV와 소수 6자리까지 일치
function invN(p){
  const a=[-39.69683028665376,220.9460984245205,-275.9285104469687,138.357751867269,-30.66479806614716,2.506628277459239],
        b=[-54.47609879822406,161.5858368580409,-155.6989798598866,66.80131188771972,-13.28068155288572],
        c=[-0.007784894002430293,-0.3223964580411365,-2.400758277161838,-2.549732539343734,4.374664141464968,2.938163982698783],
        d=[0.007784695709041462,0.3224671290700398,2.445134137142996,3.754408661907416], pl=0.02425;
  let q,r;
  if(p<pl){q=Math.sqrt(-2*Math.log(p));return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}
  if(p>1-pl){q=Math.sqrt(-2*Math.log(1-p));return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1);}
  q=p-0.5;r=q*q;return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
}

// 사용자 입력(현재고·입고예정·서비스수준)은 이 브라우저에만 저장
let saved = {};
try { saved = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch(e) { saved = {}; }
const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch(e) {} };
const SL = Object.assign({}, D.sl, saved.sl || {});
D.rows.forEach((r,i) => {
  r.i = i; r.oh0 = r.oh; r.oo0 = r.oo;
  const s = (saved.inv || {})[r.st+'|'+r.sku];
  if (s) { r.oh = s[0]; r.oo = s[1]; }
});

const sumF = (f,n) => { let s=0; for(let k=0;k<Math.min(n,f.length);k++) s+=f[k]; return s; };
function calc(r){
  const P = r.lt + r.r, dp = sumF(r.f,P), z = invN(SL[r.abc]);
  const ss = z * r.sig * Math.sqrt(P);
  const capDays = r.lt + r.shelf, cap = capDays <= D.H ? sumF(r.f,capDays) : Infinity;
  const target = Math.min(dp + ss, cap);
  const need = Math.max(0, target - r.oh - r.oo);
  const pack = Math.max(r.pack,1);
  const q = need <= 0 ? 0 : Math.max(r.moq, Math.ceil(need/pack)*pack);
  const ltDemand = sumF(r.f, r.lt);
  let st = q>0 ? 'order' : 'none';
  if (isFinite(cap) && r.oh + r.oo > cap) st = 'warn';
  if (r.oh + r.oo < ltDemand) st = 'crit';
  Object.assign(r, {P, dp, z, ss, cap, target, need, q, amt:q*r.cost, ltDemand, status:st});
  return r;
}
const STATUS = {crit:['crit','결품위험'], warn:['warn','폐기위험'], order:['ok','발주'], none:['idle','충분']};
const RANK = {crit:0, warn:1, order:2, none:3};

// ---------- 헤더 · 필터 ----------
const od = D.orderDay;
$('eyebrow').textContent = `발주일 ${od.d} (${od.w})`;
const stores = [...new Set(D.rows.map(r=>r.st))].sort();
$('sub').textContent = `판매 이력 ${D.from} ~ ${D.asOf} · 점포 ${stores.length}곳 × 품목 ${new Set(D.rows.map(r=>r.sku)).size}개 · 앞으로 ${D.H}일 예측`;
$('fStore').innerHTML = '<option value="">전체 점포</option>' + stores.map(s=>`<option>${esc(s)}</option>`).join('');
['A','B','C'].forEach(k => { $('sl'+k).value = (SL[k]*100).toFixed(1); });

let sel = null, limit = 200;
function filtered(){
  const s=$('fStore').value, st=$('fStatus').value, a=$('fAbc').value, q=$('fQ').value.trim().toLowerCase();
  let rows = D.rows.filter(r => (!s||r.st===s) && (!st||r.status===st) && (!a||r.abc===a) &&
    (!q || r.nm.toLowerCase().includes(q) || r.sku.toLowerCase().includes(q)));
  const o = $('fSort').value;
  rows.sort(o==='amt' ? (x,y)=>y.amt-x.amt : o==='store' ? (x,y)=>x.st.localeCompare(y.st)||x.sku.localeCompare(y.sku)
    : (x,y)=>RANK[x.status]-RANK[y.status] || y.amt-x.amt);
  return rows;
}

function kpis(){
  const s=$('fStore').value, rows = D.rows.filter(r=>!s||r.st===s);
  const amt = rows.reduce((t,r)=>t+r.amt,0), n = rows.filter(r=>r.q>0).length;
  $('kAmt').textContent = fmt0(amt);
  $('kAmtD').textContent = (s||'전체 점포') + ' · 원';
  $('kCnt').textContent = n.toLocaleString('ko-KR') + '건';
  $('kCntD').textContent = `${rows.length.toLocaleString('ko-KR')}개 점포×품목 중`;
  $('kRisk').textContent = rows.filter(r=>r.status==='crit').length.toLocaleString('ko-KR') + '건';
}

function rowHtml(r){
  const [cls,lab] = STATUS[r.status];
  return `<tr data-i="${r.i}" class="${sel===r.i?'sel':''}">
    <td>${esc(r.st)}</td><td class="item">${esc(r.nm)}<small>${esc(r.sku)}</small></td>
    <td><span class="grade">${r.abc}</span></td><td><span class="chip ${cls}">${lab}</span></td>
    <td class="n">${fmt1(r.dp)}</td><td class="n">${fmt1(r.ss)}</td><td class="n">${fmt1(r.target)}</td>
    <td class="n"><input type="number" min="0" step="1" id="oh-${r.i}" data-k="oh" data-i="${r.i}" value="${r.oh}" aria-label="${esc(r.nm)} 현재고"></td>
    <td class="n"><input type="number" min="0" step="1" id="oo-${r.i}" data-k="oo" data-i="${r.i}" value="${r.oo}" aria-label="${esc(r.nm)} 입고예정"></td>
    <td class="n q ${r.q?'':'zero'}">${r.q?fmt0(r.q):'–'}</td><td class="n">${r.amt?fmt0(r.amt):'–'}</td></tr>`;
}

function renderTable(){
  const rows = filtered();
  $('tb').innerHTML = rows.slice(0,limit).map(rowHtml).join('') ||
    '<tr><td colspan="11" class="empty">조건에 맞는 품목이 없습니다. 필터를 바꿔 보세요.</td></tr>';
  $('more').innerHTML = rows.length>limit ? `<button class="btn" id="bMore">${limit.toLocaleString('ko-KR')} / ${rows.length.toLocaleString('ko-KR')}건 표시 · 더 보기</button>` : '';
  if ($('bMore')) $('bMore').onclick = () => { limit += 200; renderTable(); };
  if (sel===null && rows.length) sel = rows[0].i;
  renderDetail();
}

function updateRow(r){
  const tr = document.querySelector(`tr[data-i="${r.i}"]`);
  if (!tr) return;
  const [cls,lab] = STATUS[r.status], td = tr.children;
  td[3].innerHTML = `<span class="chip ${cls}">${lab}</span>`;
  td[4].textContent = fmt1(r.dp); td[5].textContent = fmt1(r.ss); td[6].textContent = fmt1(r.target);
  td[9].textContent = r.q?fmt0(r.q):'–'; td[9].className = 'n q '+(r.q?'':'zero');
  td[10].textContent = r.amt?fmt0(r.amt):'–';
}

// ---------- 상세 패널 ----------
function chartSvg(r){
  const W=640, Hh=250, L=40, R=10, T=12, B=30;
  const hist = D.hist, fut = D.fut, n = hist.length + fut.length;
  const band = r.f.map(v => 1.2816*r.sig);   // 일별 80% 구간
  const vals = r.h.filter(v=>v!==null).concat(r.f.map((v,k)=>v+band[k]));
  let ymax = Math.max(1, ...vals); const step = niceStep(ymax/4); ymax = Math.ceil(ymax/step)*step;
  const x = k => L + (W-L-R) * (k + .5) / n, y = v => T + (Hh-T-B) * (1 - v/ymax), cw = (W-L-R)/n;
  let s = `<svg viewBox="0 0 ${W} ${Hh}" role="img" aria-label="${esc(r.nm)} 최근 ${hist.length}일 판매와 ${fut.length}일 예측">`;
  hist.concat(fut).forEach((d,k) => { if (d.hol) s += `<rect x="${(x(k)-cw/2).toFixed(1)}" y="${T}" width="${cw.toFixed(1)}" height="${Hh-T-B}" fill="var(--hol)"/>`; });
  for (let v=0; v<=ymax+1e-9; v+=step) s += `<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line-2)"/><text x="${L-6}" y="${y(v)+3}" text-anchor="end">${fmtTick(v)}</text>`;
  const t0 = hist.length;
  s += `<line x1="${x(t0)-cw/2}" x2="${x(t0)-cw/2}" y1="${T}" y2="${Hh-B}" stroke="var(--muted)" stroke-dasharray="3 3"/>`;
  s += `<text x="${x(t0)-cw/2+4}" y="${T+9}" text-anchor="start">오늘</text>`;
  // 80% 구간
  let up='', lo='';
  r.f.forEach((v,k) => { up += `${k?'L':'M'}${x(t0+k).toFixed(1)},${y(v+band[k]).toFixed(1)}`; });
  for (let k=r.f.length-1;k>=0;k--) lo += `L${x(t0+k).toFixed(1)},${y(Math.max(0,r.f[k]-band[k])).toFixed(1)}`;
  s += `<path d="${up}${lo}Z" fill="var(--band)"/>`;
  // 보호기간 표시
  s += `<line x1="${x(t0)-cw/2}" x2="${x(t0+r.P-1)+cw/2}" y1="${Hh-B+1}" y2="${Hh-B+1}" stroke="var(--fc)" stroke-width="3" stroke-linecap="round"/>`;
  // 실적선 (결측은 끊김)
  let p='', on=false;
  r.h.forEach((v,k) => { if (v===null){on=false;return;} p += `${on?'L':'M'}${x(k).toFixed(1)},${y(v).toFixed(1)}`; on=true; });
  s += `<path d="${p}" fill="none" stroke="var(--ink-2)" stroke-width="1.5" stroke-linejoin="round"/>`;
  r.so.forEach(k => { if (r.h[k]!==null) s += `<circle cx="${x(k)}" cy="${y(r.h[k])}" r="4" fill="var(--crit)" stroke="var(--surface)" stroke-width="2"/>`; });
  let fp=''; r.f.forEach((v,k)=>{ fp += `${k?'L':'M'}${x(t0+k).toFixed(1)},${y(v).toFixed(1)}`; });
  s += `<path d="${fp}" fill="none" stroke="var(--fc)" stroke-width="2" stroke-linejoin="round"/>`;
  // x축 라벨: 7일 간격
  hist.concat(fut).forEach((d,k) => { if ((k - t0) % 7 === 0) s += `<text x="${x(k)}" y="${Hh-B+16}" text-anchor="middle">${d.l}</text>`; });
  s += `<line id="cross" x1="0" x2="0" y1="${T}" y2="${Hh-B}" stroke="var(--muted)" visibility="hidden"/>`;
  s += `<rect id="hit" x="${L}" y="${T}" width="${W-L-R}" height="${Hh-T-B}" fill="transparent"/></svg>`;
  return {svg:s, x, n, L, R, W, t0, band};
}
function niceStep(v){ const e = Math.pow(10, Math.floor(Math.log10(v))), m = v/e; return (m<=1?1:m<=2?2:m<=5?5:10)*e; }
function fmtTick(v){ return v>=1000 ? (v/1000)+'k' : (Math.round(v*10)/10).toString(); }

function renderDetail(){
  const box = $('detail');
  const r = sel===null ? null : D.rows[sel];
  if (!r) { box.innerHTML = '<div class="empty">왼쪽 표에서 품목을 고르면 판매 추이와 발주 계산 근거가 나옵니다.</div>'; return; }
  const [cls,lab] = STATUS[r.status];
  const wape = r.act>0 ? r.ae/r.act : null, bw = r.act>0 ? r.be/r.act : null;
  const c = chartSvg(r);
  const packs = r.q / Math.max(r.pack,1);
  box.innerHTML = `
    <div style="display:grid;gap:6px">
      <div class="eyebrow">${esc(r.st)} · ${esc(r.sku)}</div>
      <h2>${esc(r.nm)}</h2>
      <div class="meta"><span class="chip ${cls}">${lab}</span><span class="tag">${r.abc}등급</span><span class="tag">${esc(r.pat)}</span><span class="tag">${esc(r.mdl)}</span></div>
    </div>
    <div class="legend"><span><i style="background:var(--ink-2)"></i>실제 판매</span><span><i style="background:var(--fc)"></i>예측</span><span><i class="band"></i>80% 범위</span><span><i class="hol"></i>공휴일</span><span><i style="background:var(--crit);height:8px;width:8px;border-radius:50%"></i>결품일</span></div>
    <div class="chart" id="chart">${c.svg}<div class="tip" id="tip" hidden></div></div>
    <div class="facts">
      <div><span>리드타임 + 발주주기</span><b>${r.lt} + ${r.r}일</b></div>
      <div><span>박스입수 · MOQ</span><b>${r.pack} · ${r.moq||'–'}</b></div>
      <div><span>유통기한</span><b>${r.shelf>=365?'1년 이상':r.shelf+'일'}</b></div>
      <div><span>서비스수준</span><b>${pct(SL[r.abc])}</b></div>
      <div><span>예측 오차율</span><b>${wape===null?'–':pct(wape,0)}</b></div>
      <div><span>기존 방식 오차율</span><b>${bw===null?'–':pct(bw,0)}</b></div>
    </div>
    <div class="calc">
      <span>보호기간 ${r.P}일 예측 수요</span><span class="n">${fmt1(r.dp)}</span>
      <span>+ 안전재고 (z ${r.z.toFixed(2)} × σ ${r.sig.toFixed(2)} × √${r.P})</span><span class="n">${fmt1(r.ss)}</span>
      ${isFinite(r.cap)?`<span>유통기한 상한 (${r.lt+r.shelf}일 수요)</span><span class="n">${fmt1(r.cap)}</span>`:''}
      <span>= 목표재고</span><span class="n">${fmt1(r.target)}</span>
      <span>− 현재고 − 입고예정</span><span class="n">${fmt1(r.oh)} · ${fmt1(r.oo)}</span>
      <span>필요량</span><span class="n">${fmt1(r.need)}</span>
      <span class="tot">발주수량 ${r.q?`(${r.pack}개입 × ${fmt0(packs)}박스)`:''}</span><span class="n tot">${fmt0(r.q)}</span>
      ${r.status==='crit'?`<span class="note">리드타임 ${r.lt}일 동안 예상 수요 ${fmt1(r.ltDemand)}개 > 보유 ${fmt1(r.oh+r.oo)}개. 이번 발주가 도착하기 전에 결품이 예상됩니다.</span>`:''}
      ${r.status==='warn'?`<span class="note">보유 재고 ${fmt1(r.oh+r.oo)}개가 유통기한 내 판매 가능량 ${fmt1(r.cap)}개를 넘습니다.</span>`:''}
    </div>`;
  const hit = box.querySelector('#hit'), tip = $('tip'), cross = box.querySelector('#cross'), chart = $('chart');
  const days = D.hist.concat(D.fut);
  const move = ev => {
    const rect = hit.ownerSVGElement.getBoundingClientRect(), sx = c.W / rect.width;
    const px = (ev.clientX - rect.left) * sx;
    const k = Math.max(0, Math.min(c.n-1, Math.round((px - c.L) / ((c.W-c.L-c.R)/c.n) - .5)));
    const d = days[k], isF = k >= c.t0;
    cross.setAttribute('x1', c.x(k)); cross.setAttribute('x2', c.x(k)); cross.setAttribute('visibility','visible');
    let html = `${d.l}(${d.w})${d.hol?' · 공휴일':''}<br>`;
    if (isF) { const v=r.f[k-c.t0], b=c.band[k-c.t0]; html += `예측 <b>${fmt1(v)}</b> <span style="color:var(--muted)">(${fmt1(Math.max(0,v-b))}–${fmt1(v+b)})</span>`; }
    else html += r.h[k]===null ? '판매 기록 없음' : `판매 <b>${fmt0(r.h[k])}</b>${r.so.includes(k)?' · 결품':''}`;
    tip.innerHTML = html; tip.hidden = false;
    const cr = chart.getBoundingClientRect(), left = ev.clientX - cr.left;
    tip.style.top = '8px';
    tip.style.left = (left > cr.width/2 ? left - tip.offsetWidth - 12 : left + 12) + 'px';
  };
  hit.addEventListener('pointermove', move);
  hit.addEventListener('pointerleave', () => { tip.hidden = true; cross.setAttribute('visibility','hidden'); });
}

// ---------- 이벤트 ----------
function recalcAll(){ D.rows.forEach(calc); kpis(); }
['fStore','fStatus','fAbc','fQ','fSort'].forEach(id => $(id).addEventListener('input', () => { limit=200; kpis(); renderTable(); }));
['A','B','C'].forEach(k => $('sl'+k).addEventListener('change', e => {
  const v = Math.min(99.9, Math.max(50, parseFloat(e.target.value)||SL[k]*100));
  e.target.value = v.toFixed(1); SL[k] = v/100; saved.sl = Object.assign({}, saved.sl, {[k]:SL[k]}); persist();
  recalcAll(); renderTable();
}));
$('tb').addEventListener('click', e => {
  if (e.target.tagName === 'INPUT') return;
  const tr = e.target.closest('tr[data-i]'); if (!tr) return;
  document.querySelectorAll('#tb tr.sel').forEach(t=>t.classList.remove('sel'));
  tr.classList.add('sel'); sel = +tr.dataset.i; renderDetail();
});
$('tb').addEventListener('input', e => {
  const el = e.target; if (el.tagName !== 'INPUT') return;
  const r = D.rows[+el.dataset.i]; r[el.dataset.k] = Math.max(0, parseFloat(el.value)||0);
  saved.inv = saved.inv || {}; saved.inv[r.st+'|'+r.sku] = [r.oh, r.oo]; persist();
  calc(r); updateRow(r); kpis(); if (sel===r.i) renderDetail();
});
$('bReset').onclick = () => {
  D.rows.forEach(r => { r.oh = r.oh0; r.oo = r.oo0; });
  Object.assign(SL, D.sl); ['A','B','C'].forEach(k => { $('sl'+k).value = (SL[k]*100).toFixed(1); });
  saved = {}; persist(); recalcAll(); renderTable(); flash('처음 값으로 되돌렸습니다');
};
let tmr; function flash(t){ $('toast').textContent = t; clearTimeout(tmr); tmr = setTimeout(()=>$('toast').textContent='', 2500); }
$('bCopy').onclick = () => {
  const rows = filtered().filter(r=>r.q>0);
  const tsv = ['점포\tSKU\t품목\t발주수량\t박스\t금액(원)'].concat(rows.map(r => [r.st,r.sku,r.nm,r.q,r.q/Math.max(r.pack,1),r.amt].join('\t'))).join('\n');
  const done = () => flash(`${rows.length}건 복사됨 · 엑셀이나 발주 시스템에 붙여넣으세요`);
  const fallback = () => { const ta=document.createElement('textarea'); ta.value=tsv; document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); done(); } catch(e){ flash('복사하지 못했습니다. 다시 눌러 주세요'); } ta.remove(); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(tsv).then(done, fallback); else fallback();
};
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(x => x.setAttribute('aria-selected', x===t));
  ['order','acc','eff','how'].forEach(p => { $('p-'+p).hidden = p !== t.dataset.p; });
  try { localStorage.setItem('order-console:tab', t.dataset.p); } catch(e) {}
}));

// ---------- 정확도 · 특수일 효과 · 방법 ----------
(function(){
  const g = {};
  D.rows.forEach(r => { const k = r.sku; g[k] = g[k] || {nm:r.nm, pat:{}, act:0, ae:0, be:0, bias:0};
    const x = g[k]; x.act += r.act; x.ae += r.ae; x.be += r.be; x.bias += r.bias; x.pat[r.pat] = (x.pat[r.pat]||0)+1; });
  const items = Object.values(g).filter(x=>x.act>0).map(x => Object.assign(x, {w:x.ae/x.act, bw:x.be/x.act,
    p:Object.entries(x.pat).sort((a,b)=>b[1]-a[1])[0][0]})).sort((a,b)=>a.w-b.w);
  const tA = D.rows.reduce((t,r)=>t+r.act,0), tE = D.rows.reduce((t,r)=>t+r.ae,0), tB = D.rows.reduce((t,r)=>t+r.be,0), tBias = D.rows.reduce((t,r)=>t+r.bias,0);
  if (tA > 0) {
    $('kErr').textContent = pct(tE/tA);
    $('kErrD').textContent = `기존 방식 ${pct(tB/tA)} → 오차 ${pct(1-tE/tB,0)} 감소`;
    $('accNote').textContent = `최근 ${D.backtestDays}일 동안 매일을 예측 시점으로 놓고 1~${D.H}일 앞을 예측해 실제와 비교했습니다. 오차율 = Σ|예측−실제| ÷ Σ실제. 전체 편향 ${(tBias/tA*100).toFixed(1)}% (+면 과대, −면 과소).`;
  } else { $('kErr').textContent = '–'; $('kErrD').textContent = '이력이 짧아 검증 생략'; }
  const mx = Math.max(1, ...items.map(x=>Math.max(x.w,x.bw)));
  $('accTb').innerHTML = items.map(x => `<tr><td class="item">${esc(x.nm)}</td><td>${esc(x.p)}</td>
    <td class="n">${pct(x.w,0)}</td><td class="n">${pct(x.bw,0)}</td>
    <td><div class="bar2"><div class="bar"><span style="width:${x.w/mx*100}%;background:var(--fc)"></span></div><div class="bar"><span style="width:${x.bw/mx*100}%;background:var(--bench)"></span></div></div></td>
    <td class="n">${pct(1-x.ae/x.be,0)}</td><td class="n">${(x.bias/x.act*100>=0?'+':'')}${(x.bias/x.act*100).toFixed(1)}%</td></tr>`).join('');
  const divBar = v => { if (v===null) return ''; const d = Math.max(-.7, Math.min(.7, v-1)), w = Math.abs(d)/.7*50;
    return `<div class="div"><span style="left:${d<0?50-w:50}%;width:${w}%;background:var(${d<0?'--down':'--up'})"></span></div>`; };
  const E = D.effects;
  $('effSt').innerHTML = Object.keys(E.holiday).sort().map(s => `<tr><td>${esc(s)}</td><td class="n">${E.holiday[s].toFixed(2)}</td><td>${divBar(E.holiday[s])}</td><td class="n">${E.pre[s].toFixed(2)}</td><td>${divBar(E.pre[s])}</td></tr>`).join('');
  const names = {}; D.rows.forEach(r => names[r.sku] = r.nm);
  const pr = Object.entries(E.promo).filter(([k,v]) => v!==null && Math.abs(v-1)>0.005).sort((a,b)=>b[1]-a[1]);
  $('effPr').innerHTML = pr.length ? pr.map(([k,v]) => `<tr><td class="item">${esc(names[k]||k)}<small>${esc(k)}</small></td><td class="n">${v.toFixed(2)}</td><td>${divBar(v)}</td></tr>`).join('')
    : '<tr><td colspan="3" class="empty">행사 이력이 있는 품목이 없습니다.</td></tr>';
  $('models').innerHTML = Object.entries(D.models).map(([k,v]) => `<li><b>${esc(k)}</b>: ${esc(v.split('–').slice(1).join('–').trim() || v)} <span style="color:var(--muted)">(${esc(v.split('–')[0].trim())})</span></li>`).join('');
})();

if (D.sample) $('sample').hidden = false;
recalcAll(); renderTable();
try { const t = localStorage.getItem('order-console:tab'); if (t && $('t-'+t)) $('t-'+t).click(); } catch(e) {}
})();
</script>
"""
