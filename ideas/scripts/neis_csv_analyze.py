# 1단계: NEIS 다운로드 CSV(cp949)를 utf-8 all.csv로 변환한 뒤 실행 → df.pkl 생성
import pandas as pd, re, numpy as np
df=pd.read_csv('all.csv',dtype=str)
df['dong']=df['도로명상세주소'].fillna('').str.extract(r'\(([^,()]+?동)')[0].str.strip()
gu=df['도로명주소'].fillna('')
R={'목동':('양천구',['목동','신정동']),'상계·중계':('노원구',['상계동','중계동']),'대치':('강남구',['대치동']),
   '분당 정자':('분당구',['정자동']),'분당 수내':('분당구',['수내동']),'분당 서현':('분당구',['서현동'])}
def region(i):
    pass
df['region']=None
for k,(g,ds) in R.items():
    m=gu.str.contains(g)&df['dong'].isin(ds)
    df.loc[m,'region']=k
est=pd.to_datetime(df['개설일자'],format='%Y%m%d',errors='coerce')
df['age']=(pd.Timestamp('2026-03-31')-est).dt.days/365.25
df['cap']=pd.to_numeric(df['일시수용능력인원합계'],errors='coerce')
hs=df['휴원시작일자'].str.strip(); he=df['휴원종료일자'].str.strip()
df['on_leave']=(hs!='')&(hs<='20260331')&(he>='20260301')&(he!='99991231')
df['보습']=df['분야명'].eq('입시.검정 및 보습')
df['est_year']=est.dt.year
df.to_pickle('df.pkl')
sub=df[df.region.notna()]
print(sub.region.value_counts())
print('dong parse rate', df['dong'].notna().mean().round(3))
rows=[]
def stats(name,d):
    a=d[d['학원교습소명']=='학원']
    return dict(지역=name,전체=len(d),학원=(d['학원교습소명']=='학원').sum(),교습소=(d['학원교습소명']=='교습소').sum(),
      보습비중=round(d['보습'].mean()*100,1),업력중앙값=round(d['age'].median(),1),
      업력10년이상=round((d['age']>=10).mean()*100,1),업력3년미만=round((d['age']<3).mean()*100,1),
      학원수용중앙값=a['cap'].clip(upper=2000).median(),현재휴원=int(d['on_leave'].sum()))
for k in R: rows.append(stats(k,sub[sub.region==k]))
rows.append(stats('서울 전체',df[df['시도교육청코드']=='B10']))
rows.append(stats('전국',df))
t=pd.DataFrame(rows); print(t.to_string())
# openings per year (survivors)
p=sub[sub.est_year>=2016].pivot_table(index='region',columns='est_year',values='학원명',aggfunc='count',fill_value=0)
print(p)
print(sub.groupby('region')['분야명'].value_counts().groupby(level=0).head(3))
print(sub[sub['학원교습소명']=='학원'].groupby('region')['cap'].describe(percentiles=[.25,.5,.75]).round(0))
