"""
stock_picker.py — 전문가 종목 선정 시스템
기존 app.py(수급 스캐너)와 독립적으로 동작합니다.
포트: 8502
"""

# ──────────────────────────────────────────
# python stock_picker.py 로 직접 실행 시
# 자동으로 streamlit run 으로 재시작하는 가드
# ──────────────────────────────────────────
import sys as _sys
import os as _os

# "__streamlit_script_run_ctx"가 없으면 Streamlit 없이 실행된 것
_running_in_streamlit = any(
    "streamlit" in arg for arg in _sys.argv[:1]
) or "STREAMLIT_SERVER_PORT" in _os.environ or any(
    "streamlit" in str(v) for v in _sys.modules
)

if not _running_in_streamlit and __name__ == "__main__":
    import subprocess
    import webbrowser
    import threading
    import time as _time

    _port = 8503
    _script = _os.path.abspath(__file__)

    print(f"[자동 실행] 'python {_os.path.basename(_script)}'로 실행 감지됨.")
    print(f"[자동 실행] Streamlit 앱으로 자동 재시작합니다... (포트: {_port})")
    print(f"[자동 실행] 브라우저: http://localhost:{_port}")

    def _open_browser():
        _time.sleep(3)
        webbrowser.open(f"http://localhost:{_port}")

    threading.Thread(target=_open_browser, daemon=True).start()

    proc = subprocess.run([
        _sys.executable, "-m", "streamlit", "run",
        _script,
        "--server.port", str(_port),
        "--server.headless", "true",
        "--global.developmentMode", "false",
    ])
    _sys.exit(proc.returncode)

import time
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import FinanceDataReader as fdr

# ──────────────────────────────────────────
# 페이지 설정
# ──────────────────────────────────────────
st.set_page_config(
    page_title="딴보따리 V1 - 전문가 종목 선정",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# 커스텀 CSS (프리미엄 다크 테마)
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

/* 기본 메뉴 및 푸터 숨기기 (한글화/깔끔한 UI용) */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* 전체 배경 */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0f172a 50%, #0a0e1a 100%);
    color: #e2e8f0;
}

/* 사이드바 배경 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1729 0%, #1a2340 100%);
    border-right: 1px solid rgba(99, 179, 237, 0.2);
}

/* 사이드바 텍스트 — 모든 레이블/본문을 밝은 색으로 */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #e2e8f0 !important;
}

/* 사이드바 마크다운 헤더 */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong {
    color: #7dd3fc !important;
    font-weight: 700 !important;
}

/* 사이드바 입력 위젯 레이블 */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #cbd5e1 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* 사이드바 슬라이더 수치 */
[data-testid="stSidebar"] [data-testid="stSlider"] div {
    color: #93c5fd !important;
}

/* 사이드바 selectbox / number_input 텍스트 */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: #f1f5f9 !important;
    background-color: rgba(30, 41, 59, 0.8) !important;
}

/* 사이드바 체크박스 레이블 */
[data-testid="stSidebar"] [data-testid="stCheckbox"] span {
    color: #cbd5e1 !important;
}

/* 사이드바 info 박스 */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    background: rgba(30, 58, 95, 0.6) !important;
    border: 1px solid rgba(99, 179, 237, 0.3) !important;
}
[data-testid="stSidebar"] [data-testid="stAlert"] p {
    color: #bfdbfe !important;
}

/* 카드 스타일 */
.score-card {
    background: linear-gradient(135deg, rgba(15,23,42,0.9) 0%, rgba(30,41,59,0.9) 100%);
    border: 1px solid rgba(99,179,237,0.25);
    border-radius: 16px;
    padding: 20px;
    margin: 8px 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    transition: all 0.3s ease;
}

.score-card:hover {
    border-color: rgba(99,179,237,0.5);
    box-shadow: 0 8px 32px rgba(99,179,237,0.15);
    transform: translateY(-2px);
}

/* 점수 게이지 배경 */
.gauge-bg {
    background: rgba(15,23,42,0.8);
    border-radius: 50px;
    height: 10px;
    overflow: hidden;
    margin: 6px 0;
}

/* 전문가 의견 뱃지 */
.badge-buy {
    background: linear-gradient(135deg, #065f46, #10b981);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
}
.badge-hold {
    background: linear-gradient(135deg, #78350f, #f59e0b);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
}
.badge-sell {
    background: linear-gradient(135deg, #7f1d1d, #ef4444);
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
}

/* 메트릭 숫자 */
.metric-value {
    font-size: 28px;
    font-weight: 900;
    background: linear-gradient(135deg, #63b3ed, #9f7aea);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* 헤더 타이틀 */
.main-title {
    font-size: 36px;
    font-weight: 900;
    background: linear-gradient(135deg, #63b3ed 0%, #9f7aea 50%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    padding: 20px 0 5px;
}

.sub-title {
    text-align: center;
    color: #94a3b8;
    font-size: 14px;
    margin-bottom: 30px;
}

/* 섹션 헤더 */
.section-header {
    font-size: 18px;
    font-weight: 700;
    color: #63b3ed;
    border-left: 4px solid #63b3ed;
    padding-left: 12px;
    margin: 20px 0 12px;
}

/* 구분선 */
hr {
    border-color: rgba(99,179,237,0.15) !important;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)


########################################
# 유틸리티
########################################

@st.cache_data(ttl=600)
def get_latest_valid_date():
    try:
        now = datetime.now()
        df = fdr.DataReader("005930",
                            (now - timedelta(days=10)).strftime('%Y-%m-%d'),
                            now.strftime('%Y-%m-%d'))
        if not df.empty:
            return df.index[-1].strftime('%Y%m%d')
    except:
        pass
    return (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')


########################################
# 데이터 수집
########################################

@st.cache_data(ttl=1800)
def get_stock_universe(market="전체", min_mktcap=500, min_trade=10, full_scan=False):
    """KRX 전 종목 리스트에서 기본 필터링.
    1차: FinanceDataReader
    2차: 네이버 모바일 API
    """
    errors = []
    final_df = None

    # ── 1차 시도: FinanceDataReader ──
    try:
        df = fdr.StockListing('KRX')
        if df is not None and not df.empty:
            df['시가총액(억)'] = df['Marcap'] / 1e8
            df['거래대금(억)'] = df['Amount'] / 1e8
            if market == "KOSPI":
                df = df[df['Market'] == 'KOSPI']
            elif market == "KOSDAQ":
                df = df[df['Market'] == 'KOSDAQ']

            df = df[
                (df['시가총액(억)'] >= min_mktcap) &
                (df['거래대금(억)'] >= min_trade) &
                (df['Close'] > 0)
            ].copy()
            if not df.empty:
                final_df = df
    except Exception as e:
        errors.append(f"FDR: {e}")

    # ── 2차 폴백: 네이버 모바일 API ──
    if final_df is None:
        try:
            import requests as _req
            mkts = []
            if market in ("전체", "KOSPI"):  mkts.append("KOSPI")
            if market in ("전체", "KOSDAQ"): mkts.append("KOSDAQ")

            frames = []
            for mkt in mkts:
                for page in range(1, 25 if full_scan else 6):
                    try:
                        url = (
                            f"https://m.stock.naver.com/api/stocks/marketValue/{mkt}"
                            f"?page={page}&pageSize=100"
                        )
                        res = _req.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                        data = res.json()
                        stocks = data.get('stocks', [])
                        if not stocks:
                            break

                        for s in stocks:
                            try:
                                close = float(s.get('closePriceRaw') or 0)
                                mktcap = float(s.get('marketValueRaw') or 0) / 1e8
                                trade = float(s.get('accumulatedTradingValueRaw') or 0) / 1e8
                                if close <= 0 or mktcap <= 0:
                                    continue
                                frames.append({
                                    'Code': s.get('itemCode', ''),
                                    'Name': s.get('stockName', ''),
                                    'Market': mkt,
                                    'Close': close,
                                    '시가총액(억)': mktcap,
                                    '거래대금(억)': trade,
                                })
                            except Exception:
                                continue
                    except Exception as pe:
                        errors.append(f"Naver {mkt} p{page}: {pe}")
                        break

            if frames:
                combined = pd.DataFrame(frames)
                if combined['거래대금(억)'].max() == 0:
                    combined = combined[
                        (combined['시가총액(억)'] >= min_mktcap) &
                        (combined['Close'] > 0)
                    ].copy()
                    if not combined.empty:
                        final_df = combined.sort_values('시가총액(억)', ascending=False)
                        if not full_scan: final_df = final_df.head(300)
                else:
                    combined = combined[
                        (combined['시가총액(억)'] >= min_mktcap) &
                        (combined['거래대금(억)'] >= min_trade) &
                        (combined['Close'] > 0)
                    ].copy()
                    if not combined.empty:
                        final_df = combined.sort_values('거래대금(억)', ascending=False)
                        if not full_scan: final_df = final_df.head(300)
            if final_df is None:
                errors.append("Naver: 수집된 종목 없음")
        except Exception as e:
            errors.append(f"Naver: {e}")

    # ── 공통: 섹터 매핑 적용 ──
    if final_df is not None and not final_df.empty:
        try:
            df_desc = fdr.StockListing('KRX-DESC')
            # KOSDAQ의 경우 Sector가 '우량기업부' 등으로 나오는 경우가 있으므로 Industry 컬럼 우선 사용
            if 'Industry' in df_desc.columns:
                df_desc['Sector'] = df_desc.apply(lambda x: x['Industry'] if pd.notnull(x.get('Industry')) and str(x.get('Industry')).strip() != '' else x.get('Sector', '기타'), axis=1)
            
            # '기업부' 글자가 포함된 경우 기타로 처리
            df_desc['Sector'] = df_desc['Sector'].apply(lambda x: '기타' if '기업부' in str(x) else x)
            
            df_desc = df_desc[['Code', 'Sector']]
            final_df = pd.merge(final_df, df_desc, on='Code', how='left')
            final_df['Sector'] = final_df['Sector'].fillna('기타')
        except:
            final_df['Sector'] = '기타'
        return final_df

    st.error(f"종목을 가져오는데 실패했습니다. (사유: {errors})")
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_recent_disclosures(ticker, days=7):
    """네이버 금융 API에서 최근 공시 가져오기"""
    import requests
    from datetime import datetime, timedelta
    try:
        url = f"https://m.stock.naver.com/api/stock/{ticker}/disclosure?page=1&pageSize=10"
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        data = r.json()
        
        limit_date = datetime.now() - timedelta(days=days)
        results = []
        for item in data:
            dt_str = item.get('datetime', '')
            if not dt_str: continue
            dt_obj = datetime.fromisoformat(dt_str)
            if dt_obj >= limit_date:
                results.append({
                    'title': item.get('title'),
                    'date': dt_str[:10],
                    'id': item.get('disclosureId')
                })
        return results
    except:
        return []

def analyze_disclosure(title, ticker, disclosure_id):
    """키워드 기반 공시 영향 분석기"""
    link = f"https://finance.naver.com/item/news_notice_read.naver?no={disclosure_id}&code={ticker}"
    link_md = f"[원문 보기 클릭]({link})"
    
    analysis = {
        'type': '🔍 특이',
        'impact': '알 수 없음 (원문 확인 필요)',
        'reason': f"일반적인 패턴으로 자동 분류하기 어려운 특이 공시이거나 복잡한 내용입니다. 우측 링크를 클릭하여 공시 원문을 꼭 확인해 보세요. {link_md}"
    }
    
    # 키워드 검사 (단순 휴리스틱)
    if '유상증자' in title:
        analysis['type'] = '⚠️ 악재성 (희석)'
        analysis['impact'] = '주가 하락 압력'
        analysis['reason'] = '새로운 주식을 발행하여 자금을 조달하므로, 기존 주주들의 주식 가치가 희석될 우려가 커 단기 악재로 작용할 가능성이 높습니다.'
    elif '무상증자' in title:
        analysis['type'] = '🔥 호재성 (유동성)'
        analysis['impact'] = '단기 주가 상승 기대'
        analysis['reason'] = '자본잉여금을 자본금으로 전입해 주주들에게 무료로 주식을 나누어주는 것으로, 유동성 증가로 인한 호재로 받아들여집니다.'
    elif '단일판매' in title or '공급계약' in title or '수주' in title:
        analysis['type'] = '🚀 호재성 (매출)'
        analysis['impact'] = '주가 상승 압력'
        analysis['reason'] = '대규모 매출처를 확보했다는 긍정적 신호입니다. 계약금액이 전년매출 대비 클수록 강력한 호재입니다.'
    elif '자사주' in title and ('취득' in title or '매입' in title or '소각' in title):
        analysis['type'] = '🛡️ 호재성 (주주환원)'
        analysis['impact'] = '주가 하방 지지 및 상승'
        analysis['reason'] = '유통 주식 수가 줄어들어 1주당 가치가 상승하므로 주주친화적인 강력한 호재입니다.'
    elif '전환사채' in title or 'CB발행' in title or '신주인수권' in title or 'BW발행' in title:
        analysis['type'] = '⚠️ 악재/중립 (오버행)'
        analysis['impact'] = '잠재적 매도 물량 부담'
        analysis['reason'] = '미래에 주식으로 전환될 수 있는 채권 등을 발행한 것으로, 나중에 대량 매물이 나올 수 있는 잠재적 리스크(오버행)가 존재합니다.'
    elif '횡령' in title or '배임' in title or '감자' in title or '관리종목' in title:
        analysis['type'] = '🚨 초특급 악재'
        analysis['impact'] = '급락 및 거래정지 위험'
        analysis['reason'] = '기업 존속에 치명적인 영향을 미치는 공시입니다. 매매에 극도로 유의해야 합니다.'
    elif '영업실적' in title or '결산실적' in title or '매출액' in title:
        analysis['type'] = '📊 실적 (확인필요)'
        analysis['impact'] = '실적에 따라 상이'
        analysis['reason'] = '실적 관련 공시입니다. 컨센서스(시장 기대치)를 상회했는지 하회했는지 본문을 꼭 확인해야 합니다.'
    elif '주주총회' in title or '임원' in title or '변경' in title:
        analysis['type'] = 'ℹ️ 중립 (일상적)'
        analysis['impact'] = '영향 미미'
        analysis['reason'] = '일상적인 기업 운영 관련 공시로 주가에 미치는 단기적 영향은 제한적입니다.'

    if '특이' not in analysis['type']:
        analysis['reason'] += f" {link_md}"

    return analysis


@st.cache_data(ttl=3600, max_entries=500)
def get_ohlcv(ticker, base_date, days=300):
    """OHLCV 데이터 로드 (고속 JSON API)"""
    try:
        import requests
        import json
        from datetime import datetime, timedelta
        import pandas as pd
        
        end_time = datetime.strptime(base_date, '%Y%m%d')
        start_time = end_time - timedelta(days=days + 150) # 휴일 감안하여 넉넉히
        
        url = f"https://api.finance.naver.com/siseJson.naver?symbol={ticker}&requestType=1&startTime={start_time.strftime('%Y%m%d')}&endTime={end_time.strftime('%Y%m%d')}&timeframe=day"
        r = requests.get(url, timeout=5)
        
        text = r.text.strip()
        text = text.replace("'", '"').replace('\\n', '').replace('\\t', '')
        data = json.loads(text)
        
        columns = data[0]
        rows = data[1:]
        df = pd.DataFrame(rows, columns=columns)
        df.rename(columns={'날짜': '날짜', '시가': '시가', '고가': '고가', '저가': '저가', '종가': '종가', '거래량': '거래량'}, inplace=True)
        df['날짜'] = pd.to_datetime(df['날짜'])
        df = df.set_index('날짜')
        for col in ['시가', '고가', '저가', '종가', '거래량']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        end_date = pd.to_datetime(base_date, format='%Y%m%d')
        df = df[df.index <= end_date]
        return df.tail(days)
    except Exception as e:
        return pd.DataFrame()



@st.cache_data(ttl=3600, max_entries=500)
def get_investor_flow(ticker, base_date, days=20):
    """투자자별 순매수 데이터"""
    # ── 1차 시도: pykrx ──
    try:
        
        end = datetime.strptime(base_date, '%Y%m%d')
        start = end - timedelta(days=days * 2)
        df = stock.get_market_trading_value_by_date(
            start.strftime('%Y%m%d'), end.strftime('%Y%m%d'), ticker)
        if not df.empty and ('기관합계' in df.columns or '외국인합계' in df.columns):
            return df.tail(days)
    except:
        pass

    # ── 2차 우회: 네이버 증권 frgn.naver HTML 파싱 ──
    # pykrx 서버 장애 시 순매수 주수 데이터를 통해 순매수 대금을 추정합니다.
    try:
        import requests
        from io import StringIO
        import pandas as pd
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://finance.naver.com'
        }
        url = f'https://finance.naver.com/item/frgn.naver?code={ticker}'
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'euc-kr'
        
        dfs = pd.read_html(StringIO(r.text), encoding='euc-kr')
        df3 = dfs[3]  # 테이블[3]에 날짜별 순매매량 정보 위치
        
        # 다중 인덱스 컬럼 평탄화
        df3.columns = ['_'.join(str(c) for c in col).strip() if isinstance(col, tuple) else col for col in df3.columns]
        
        # 빈 데이터 제거
        dfclean = df3.dropna(subset=['날짜_날짜', '기관_순매매량', '외국인_순매매량']).copy()
        
        # 데이터 클렌징
        dfclean['날짜'] = pd.to_datetime(dfclean['날짜_날짜'], format='%Y.%m.%d', errors='coerce')
        dfclean['종가_종가'] = pd.to_numeric(dfclean['종가_종가'], errors='coerce')
        dfclean['기관_순매매량'] = pd.to_numeric(dfclean['기관_순매매량'], errors='coerce')
        dfclean['외국인_순매매량'] = pd.to_numeric(dfclean['외국인_순매매량'], errors='coerce')
        
        dfclean = dfclean.dropna(subset=['날짜'])
        
        # (임시) 금액 계산: 거래량 * 해당일 종가
        dfclean['기관합계'] = dfclean['기관_순매매량'] * dfclean['종가_종가']
        dfclean['외국인합계'] = dfclean['외국인_순매매량'] * dfclean['종가_종가']
        
        dfclean = dfclean.set_index('날짜').sort_index()
        return dfclean.tail(days)
        
    except Exception as e:
        print(f"네이버 수급 파싱 에러: {e}")
        return pd.DataFrame()


########################################
# 지표 계산 엔진
########################################


@st.cache_data(ttl=3600)
def get_market_condition(base_date):
    """
    1단계: 장세 판별
    - 💀 폭락장: 당일 -2% 이하 또는 연속 -1%
    - 💚 상승장: 20일선 근접 + 기울기 +0.3%↑
    - 🟡 보합장: 그 외
    """
    try:
        from pykrx import stock
        end = datetime.strptime(base_date, '%Y%m%d')
        start = end - timedelta(days=60)
        df_kospi = stock.get_index_ohlcv(start.strftime('%Y%m%d'), end.strftime('%Y%m%d'), "1001")
        if df_kospi.empty or len(df_kospi) < 20:
            raise Exception("Fallback to Naver")
    except:
        try:
            import requests
            import pandas as pd
            from io import StringIO
            url = "https://finance.naver.com/sise/sise_index_day.naver?code=KOSPI"
            headers = {'User-Agent': 'Mozilla/5.0'}
            dfs = []
            for page in range(1, 15):
                r = requests.get(f"{url}&page={page}", headers=headers, timeout=5)
                df = pd.read_html(StringIO(r.text), encoding='euc-kr')[0].dropna()
                dfs.append(df)
            df = pd.concat(dfs, ignore_index=True)
            df['날짜'] = pd.to_datetime(df['날짜'])
            df['종가'] = df['체결가'].astype(float)
            df_kospi = df.set_index('날짜').sort_index()
            end_dt = pd.to_datetime(base_date, format='%Y%m%d')
            df_kospi = df_kospi[df_kospi.index <= end_dt]
        except:
            return "보합장"
            
    try:
        close = df_kospi['종가']
        pct_change = close.pct_change() * 100
        
        # 폭락장
        if len(pct_change) >= 2:
            if pct_change.iloc[-1] <= -2.0 or (pct_change.iloc[-1] <= -1.0 and pct_change.iloc[-2] <= -1.0):
                return "폭락장"
        
        # 상승장
        ma20 = close.rolling(20).mean()
        if len(ma20) >= 2 and not pd.isna(ma20.iloc[-1]) and not pd.isna(ma20.iloc[-2]):
            cur_ma20 = ma20.iloc[-1]
            prev_ma20 = ma20.iloc[-2]
            slope = (cur_ma20 - prev_ma20) / prev_ma20 * 100
            
            if close.iloc[-1] >= cur_ma20 * 0.99 and slope >= 0.3:
                return "상승장"
                
        return "보합장"
    except:
        return "보합장"


@st.cache_data(ttl=3600)
def get_sector_dict():
    """네이버 API 또는 pykrx를 이용해 섹터 매핑 정보를 가져옵니다"""
    try:
        # 간단하게 pykrx 업종 정보를 쓸 수 없으므로 네이버를 크롤링하거나 생략
        # 빠른 속도를 위해 현재는 빈 딕셔너리 리턴 후 엑셀 등 외부 데이터를 추후 적용
        return {}
    except:
        return {}

def get_matrix_opinion(market_cond, swing_period, indicators, final_score):
    """3x3 매트릭스 필터 및 스나이퍼톡 생성 (V51 룰베이스)"""
    rsi = indicators.get('모멘텀지표', {}).get('rsi', 50)
    
    sniper_talk = "[관망] 조건 미달. 지켜보세요."
    tag = "[일반]"
    passed = False
    
    # 0단계 절대 방어선 (가짜수급/경고/위험) -> 기초 필터에서 걸러진 상태이므로 여기서 기본 통과
    
    if market_cond == "폭락장":
        # 폭락장 확정 전략: 역행 주도주 단일 트랙 (RSI 50~70만 수익)
        if 50 <= rsi <= 70 and final_score >= 200:
            passed = True
            sniper_talk = "[역행 주도주] 하락장을 이기는 강한 시세 유지. 분기신고가 돌파 기대."
            tag = "[역행 주도주]"
    elif market_cond == "보합장":
        if "3일" in swing_period:
            if 45 <= rsi <= 56 and final_score >= 200:
                passed = True
                sniper_talk = "[핀셋 눌림목] S등급 분기신고가 패턴. 단기 반등 타점."
                tag = "[핀셋 눌림목]"
        elif "5일" in swing_period:
            if 40 <= rsi <= 55 and final_score >= 200:
                passed = True
                sniper_talk = "[박스권 하단] 박스권 하단 지지. S등급 스나이퍼 매수 유효."
                tag = "[박스권 하단]"
        else: # 10일
            if 40 <= rsi <= 60 and final_score >= 200:
                passed = True
                sniper_talk = "[긴 호흡 매집] 장기 매집 확인. S등급 분할 매수."
                tag = "[긴 호흡 매집]"
    else: # 상승장
        if "3일" in swing_period:
            if 60 <= rsi <= 70 and final_score >= 200:
                passed = True
                sniper_talk = "[모멘텀 돌파] 주도 모멘텀 돌파 진입. S등급 분기신고가."
                tag = "[모멘텀 돌파]"
        elif "5일" in swing_period:
            if 55 <= rsi <= 65 and final_score >= 200:
                passed = True
                sniper_talk = "[중기 눌림목] 상승 추세 속 건전한 조정. 진입 유효."
                tag = "[중기 눌림목]"
        else: # 10일
            if 50 <= rsi <= 70 and final_score >= 150:
                passed = True
                sniper_talk = "[추세 팔로잉] 강력한 상승 추세 동참. 홀딩 권장."
                tag = "[추세 팔로잉]"
                
    return passed, tag, sniper_talk


def calc_indicators(df, inv_df=None):
    """
    전문가 8가지 지표를 계산합니다.
    반환: dict { 지표명: { 'score': 0~100, 'value': 실제값, 'label': 설명 } }
    """
    result = {}
    if df.empty or len(df) < 60:
        return None

    close = df['종가']
    volume = df['거래량']

    # ── 이동평균선 ──
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    ma120 = close.rolling(120).mean() if len(df) >= 120 else close.rolling(len(df)).mean()

    cur = close.iloc[-1]
    cur_ma5 = ma5.iloc[-1]
    cur_ma20 = ma20.iloc[-1]
    cur_ma60 = ma60.iloc[-1]
    cur_ma120 = ma120.iloc[-1]

    # ── RSI(14) ──
    delta = close.diff()
    up = delta.clip(lower=0)
    dn = (-delta).clip(lower=0)
    rs = up.ewm(com=13, adjust=False).mean() / dn.ewm(com=13, adjust=False).mean()
    rsi_series = 100 - (100 / (1 + rs))
    rsi = float(rsi_series.iloc[-1])

    # ── MACD ──
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - macd_signal
    macd_cur = float(macd_line.iloc[-1])
    macd_sig = float(macd_signal.iloc[-1])
    macd_h = float(macd_hist.iloc[-1])
    macd_h_prev = float(macd_hist.iloc[-2]) if len(macd_hist) > 1 else 0

    # ── 볼린저 밴드 ──
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_pct = (cur - float(bb_lower.iloc[-1])) / (float(bb_upper.iloc[-1]) - float(bb_lower.iloc[-1]) + 1e-9)

    # ── 52주 고저 ──
    period_52w = close.tail(252)
    high_52w = float(period_52w.max())
    low_52w = float(period_52w.min())
    pct_from_high = (cur - high_52w) / high_52w * 100
    pct_from_low = (cur - low_52w) / low_52w * 100

    # ── 거래량 모멘텀 ──
    vol_ma20 = float(volume.rolling(20).mean().iloc[-1])
    vol_cur = float(volume.iloc[-1])
    vol_ratio = vol_cur / (vol_ma20 + 1e-9)

    # OBV
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    obv_ma = obv.rolling(20).mean()
    obv_trend = (float(obv.iloc[-1]) > float(obv_ma.iloc[-1]))

    # ── 1. 추세 강도 (이평선 배열) ──
    # 정배열: MA5 > MA20 > MA60 > MA120
    arr_score = 0
    if cur > cur_ma5: arr_score += 15
    if cur_ma5 > cur_ma20: arr_score += 25
    if cur_ma20 > cur_ma60: arr_score += 35
    if cur_ma60 > cur_ma120: arr_score += 25

    # 골든크로스 보너스 (최근 5일 내 MA20이 MA60 돌파)
    recent_cross = False
    if len(df) >= 6:
        prev_ma20 = float(ma20.iloc[-6])
        prev_ma60 = float(ma60.iloc[-6])
        if prev_ma20 <= prev_ma60 and cur_ma20 > cur_ma60:
            recent_cross = True
            arr_score = min(arr_score + 15, 100)

    if cur_ma5 > cur_ma20 and cur_ma20 > cur_ma60 and cur_ma60 > cur_ma120:
        trend_label = "🔥 완전 정배열"
    elif cur_ma20 > cur_ma60:
        trend_label = "📈 부분 정배열"
    else:
        trend_label = "❄️ 역배열"

    result['추세강도'] = {
        'score': arr_score,
        'value': f"MA5>{cur_ma5:.0f} / MA20>{cur_ma20:.0f}",
        'label': trend_label + (" (+골든크로스!)" if recent_cross else ""),
        'icon': '📊'
    }

    # ── 2. 모멘텀 지표 (RSI + MACD + BB) ──
    # RSI 점수
    if 45 <= rsi <= 60:
        rsi_score = 100
    elif 35 <= rsi < 45 or 60 < rsi <= 70:
        rsi_score = 70
    elif 25 <= rsi < 35:
        rsi_score = 50
    elif rsi > 70:
        rsi_score = 20
    else:
        rsi_score = 30

    # MACD 점수
    macd_score = 0
    if macd_cur > macd_sig: macd_score += 50   # 매수 시그널
    if macd_h > 0: macd_score += 25             # 히스토그램 양
    if macd_h > macd_h_prev: macd_score += 25   # 히스토그램 증가

    mom_score = int(rsi_score * 0.5 + macd_score * 0.5)

    rsi_label = "과매수 주의" if rsi > 70 else ("과매도 반등 기대" if rsi < 30 else "적정 구간")

    result['모멘텀지표'] = {
        'score': mom_score,
        'value': f"RSI {rsi:.1f} | MACD {'▲' if macd_h > 0 else '▼'}",
        'label': f"RSI: {rsi_label} | BB위치: {bb_pct*100:.0f}%",
        'icon': '⚡',
        'rsi': rsi,
        'macd_h': macd_h,
    }

    # ── 3. 기관 수급 ──
    inst_score = 50  # 기본값
    inst_label = "데이터 없음"
    inst_value = "N/A"
    if inv_df is not None and not inv_df.empty and '기관합계' in inv_df.columns:
        inst_series = inv_df['기관합계'] / 1e8
        inst_sum = float(inst_series.sum())
        inst_recent5 = float(inst_series.tail(5).sum())
        pos_days = int((inst_series > 0).sum())
        total_days = len(inst_series)

        # 연속 순매수 체크
        consecutive = 0
        for v in reversed(inst_series.values):
            if v > 0: consecutive += 1
            else: break

        inst_score = min(100, int(
            (pos_days / total_days) * 40 +
            (min(abs(inst_sum), 500) / 500) * 30 +
            (min(consecutive, 10) / 10) * 30
        ))

        inst_value = f"{inst_sum:+.0f}억 (연속{consecutive}일)"
        if inst_sum > 0 and consecutive >= 3:
            inst_label = f"📈 기관 매수세 강함 (연속 {consecutive}일)"
        elif inst_sum > 0:
            inst_label = "🟢 기관 순매수 우위"
        elif inst_sum < 0:
            inst_label = "🔴 기관 순매도 우위"
        else:
            inst_label = "⚖️ 기관 중립"

    result['기관수급'] = {
        'score': inst_score,
        'value': inst_value,
        'label': inst_label,
        'icon': '🏢'
    }

    # ── 4. 외국인 수급 ──
    fore_score = 50
    fore_label = "데이터 없음"
    fore_value = "N/A"
    if inv_df is not None and not inv_df.empty and '외국인합계' in inv_df.columns:
        fore_series = inv_df['외국인합계'] / 1e8
        fore_sum = float(fore_series.sum())
        fore_recent5 = float(fore_series.tail(5).sum())
        pos_days = int((fore_series > 0).sum())
        total_days = len(fore_series)

        consecutive_f = 0
        for v in reversed(fore_series.values):
            if v > 0: consecutive_f += 1
            else: break

        fore_score = min(100, int(
            (pos_days / total_days) * 40 +
            (min(abs(fore_sum), 500) / 500) * 30 +
            (min(consecutive_f, 10) / 10) * 30
        ))

        fore_value = f"{fore_sum:+.0f}억 (연속{consecutive_f}일)"
        if fore_sum > 0 and consecutive_f >= 3:
            fore_label = f"🌍 외국인 강한 매수 (연속 {consecutive_f}일)"
        elif fore_sum > 0:
            fore_label = "🟢 외국인 순매수 우위"
        elif fore_sum < 0:
            fore_label = "🔴 외국인 순매도 우위"
        else:
            fore_label = "⚖️ 외국인 중립"

    result['외국인수급'] = {
        'score': fore_score,
        'value': fore_value,
        'label': fore_label,
        'icon': '🌏'
    }

    # ── 5. 가격 모멘텀 (52주) ──
    # 52주 고점 대비 -10% 이내 = 강세, -30% 이내 = 보통, 그 이하 = 약세
    if pct_from_high >= -10:
        price_mom_score = 90
        price_mom_label = "🚀 52주 신고가 권역 (강한 상승 추세)"
    elif pct_from_high >= -20:
        price_mom_score = 70
        price_mom_label = "📈 52주 고점 근접 (상승 모멘텀)"
    elif pct_from_high >= -30:
        price_mom_score = 50
        price_mom_label = "➡️ 중간 구간 (눌림목 가능)"
    elif pct_from_high >= -50:
        price_mom_score = 30
        price_mom_label = "📉 고점 대비 조정 (반등 관찰 필요)"
    else:
        price_mom_score = 10
        price_mom_label = "⚠️ 고점 대비 급락 (하락 추세 유의)"

    result['가격모멘텀'] = {
        'score': price_mom_score,
        'value': f"52주 고점비 {pct_from_high:+.1f}%",
        'label': price_mom_label,
        'icon': '📉'
    }

    # ── 6. 거래량 모멘텀 ──
    if vol_ratio >= 3.0:
        vol_score = 95
        vol_label = "🔥 거래량 폭발 (세력/기관 유입 가능성)"
    elif vol_ratio >= 2.0:
        vol_score = 80
        vol_label = "📊 거래량 급증 (관심 급상승)"
    elif vol_ratio >= 1.5:
        vol_score = 65
        vol_label = "📈 거래량 증가 (모멘텀 형성 중)"
    elif vol_ratio >= 0.8:
        vol_score = 45
        vol_label = "⚖️ 거래량 보통"
    else:
        vol_score = 20
        vol_label = "😴 거래량 부진 (관심 저조)"

    if obv_trend: vol_score = min(vol_score + 10, 100)

    result['거래량모멘텀'] = {
        'score': vol_score,
        'value': f"거래량 평균比 {vol_ratio:.1f}배 | OBV {'↑' if obv_trend else '↓'}",
        'label': vol_label,
        'icon': '📦'
    }

    # ── 7. 변동성 리스크 ──
    # 최근 20일 일일 수익률의 표준편차 (낮을수록 안정적)
    ret = close.pct_change().tail(20)
    volatility = float(ret.std()) * 100  # %
    if volatility < 1.5:
        vol_risk_score = 90
        vol_risk_label = "🟢 변동성 낮음 (안정적)"
    elif volatility < 2.5:
        vol_risk_score = 70
        vol_risk_label = "🟡 변동성 보통"
    elif volatility < 4.0:
        vol_risk_score = 45
        vol_risk_label = "🟠 변동성 높음 (단기 트레이딩 주의)"
    else:
        vol_risk_score = 20
        vol_risk_label = "🔴 변동성 매우 높음 (고위험)"

    result['변동성리스크'] = {
        'score': vol_risk_score,
        'value': f"일간 변동성 {volatility:.2f}%",
        'label': vol_risk_label,
        'icon': '🎯'
    }

    # ── 8. 시장 포지션 (시가총액 + 유동성) ──
    # 이 지표는 외부에서 주입 (기본 50)
    result['시장포지션'] = {
        'score': 50,
        'value': "계산 중",
        'label': "대형주 우위",
        'icon': '🏛️'
    }

    return result


def calc_market_position_score(mktcap_bil, trade_bil):
    """시가총액과 거래대금으로 시장 포지션 점수 계산"""
    cap_score = 0
    if mktcap_bil >= 10000:
        cap_score = 80  # 대형주
        label = "🏛️ 대형주 (안정성 우수)"
    elif mktcap_bil >= 3000:
        cap_score = 70
        label = "🏢 중형주 (성장+안정 균형)"
    elif mktcap_bil >= 1000:
        cap_score = 60
        label = "🏠 중소형주"
    else:
        cap_score = 40
        label = "🌱 소형주 (고위험 고수익)"

    # 거래대금 유동성 가점
    if trade_bil >= 500:
        cap_score = min(cap_score + 20, 100)
    elif trade_bil >= 100:
        cap_score = min(cap_score + 10, 100)

    return cap_score, label


def compute_final_score(indicators):
    """
    전문가 가중치로 종합 점수 계산
    기술적 분석 40%, 수급 분석 30%, 모멘텀 20%, 기본 조건 10%
    """
    weights = {
        '추세강도':     0.20,
        '모멘텀지표':   0.20,
        '기관수급':     0.15,
        '외국인수급':   0.15,
        '가격모멘텀':   0.10,
        '거래량모멘텀': 0.10,
        '변동성리스크': 0.05,
        '시장포지션':   0.05,
    }
    total = sum(indicators[k]['score'] * w for k, w in weights.items() if k in indicators)
    return round(total, 1)


def get_expert_opinion(score, indicators):
    """점수 기반 전문가 의견 생성"""
    trend_label = indicators.get('추세강도', {}).get('label', '')
    inst_label = indicators.get('기관수급', {}).get('label', '')
    fore_label = indicators.get('외국인수급', {}).get('label', '')
    rsi = indicators.get('모멘텀지표', {}).get('rsi', 50)
    vol_label = indicators.get('거래량모멘텀', {}).get('label', '')

    opinion_parts = []

    # 추세 의견
    if '정배열' in trend_label:
        opinion_parts.append("이평선 정배열 상태로 상승 추세가 유지되고 있습니다.")
    else:
        opinion_parts.append("이평선 역배열 구간으로 추세 전환 확인이 필요합니다.")

    # 수급 의견
    if '매수세 강함' in inst_label or '강한 매수' in fore_label:
        opinion_parts.append("기관·외국인 동반 매수세가 강하여 수급 면에서 우수합니다.")
    elif '순매수' in inst_label or '순매수' in fore_label:
        opinion_parts.append("기관 또는 외국인 중 한 주체가 순매수 중입니다.")
    else:
        opinion_parts.append("현재 수급 주체의 매수 의지가 약한 편입니다.")

    # RSI 의견
    if rsi > 70:
        opinion_parts.append(f"RSI {rsi:.0f}로 과매수권 진입 — 단기 차익실현 압력에 주의하세요.")
    elif rsi < 30:
        opinion_parts.append(f"RSI {rsi:.0f}로 과매도권 — 기술적 반등 가능성을 주목하세요.")
    else:
        opinion_parts.append(f"RSI {rsi:.0f}로 적정 구간을 유지 중입니다.")

    # 거래량 의견
    if '폭발' in vol_label or '급증' in vol_label:
        opinion_parts.append("거래량이 급증하여 세력 또는 기관의 유입 가능성이 높습니다.")

    opinion = " ".join(opinion_parts)

    # 최종 판단
    if score >= 72:
        judgment = "매수 검토"
        badge = "badge-buy"
        judgment_detail = "전반적인 지표가 양호합니다. 리스크 관리하에 매수 진입을 검토할 수 있습니다."
    elif score >= 55:
        judgment = "중립 관망"
        badge = "badge-hold"
        judgment_detail = "혼조세입니다. 추세 확인 후 진입을 권장합니다."
    else:
        judgment = "신중 접근"
        badge = "badge-sell"
        judgment_detail = "현재 지표가 부진합니다. 추가 하락 가능성을 고려해 신중하게 접근하세요."

    return opinion, judgment, badge, judgment_detail


########################################
# UI 컴포넌트
########################################

def render_score_bar(name, score, icon, label, value):
    """점수 바 시각화"""
    color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 45 else "#ef4444")
    st.markdown(f"""
    <div class="score-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:15px; font-weight:700; color:#e2e8f0;">{icon} {name}</span>
            <span style="font-size:20px; font-weight:900; color:{color};">{score}점</span>
        </div>
        <div class="gauge-bg">
            <div style="height:100%; width:{score}%; background:linear-gradient(90deg, {color}88, {color}); border-radius:50px; transition:width 0.5s ease;"></div>
        </div>
        <div style="margin-top:8px;">
            <span style="font-size:13px; color:#94a3b8;">{label}</span><br>
            <span style="font-size:12px; color:#64748b;">📌 {value}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_radar_chart(indicators, ticker_name):
    """레이더 차트 (8가지 지표)"""
    categories = list(indicators.keys())
    scores = [indicators[k]['score'] for k in categories]
    categories_display = [f"{indicators[k]['icon']} {k}" for k in categories]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories_display + [categories_display[0]],
        fill='toself',
        fillcolor='rgba(99, 179, 237, 0.15)',
        line=dict(color='#63b3ed', width=2),
        name=ticker_name,
        hovertemplate='%{theta}: %{r:.0f}점<extra></extra>'
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='rgba(15,23,42,0.8)',
            angularaxis=dict(
                linecolor='rgba(99,179,237,0.3)',
                gridcolor='rgba(99,179,237,0.1)',
                tickfont=dict(color='#94a3b8', size=11)
            ),
            radialaxis=dict(
                range=[0, 100],
                linecolor='rgba(99,179,237,0.2)',
                gridcolor='rgba(99,179,237,0.1)',
                tickfont=dict(color='#64748b', size=9),
                tickvals=[20, 40, 60, 80, 100]
            ),
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8'),
        showlegend=False,
        height=380,
        margin=dict(l=60, r=60, t=20, b=20),
    )
    return fig


def render_candle_chart(df, ticker_name, ticker):
    """캔들 차트 + 이평선"""
    if df.empty:
        return None

    close = df['종가']
    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    ma60 = close.rolling(60).mean()
    ma120 = close.rolling(120).mean()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['시가'], high=df['고가'],
        low=df['저가'], close=df['종가'], name='캔들',
        increasing_line_color='#ef4444', decreasing_line_color='#3b82f6',
        increasing_fillcolor='#ef4444', decreasing_fillcolor='#3b82f6',
    ))

    ma_styles = [
        (ma5, '#fbbf24', '5일'),
        (ma20, '#f97316', '20일'),
        (ma60, '#60a5fa', '60일'),
        (ma120, '#a78bfa', '120일'),
    ]
    for ma_data, color, name in ma_styles:
        fig.add_trace(go.Scatter(
            x=df.index, y=ma_data, mode='lines',
            line=dict(color=color, width=1.5), name=name
        ))

    fig.update_layout(
        title=dict(text=f"📈 {ticker_name} ({ticker})", font=dict(color='#e2e8f0', size=16)),
        paper_bgcolor='rgba(15,23,42,0.9)',
        plot_bgcolor='rgba(10,14,26,0.9)',
        font=dict(color='#94a3b8'),
        xaxis=dict(
            type='category',
            showgrid=False,
            color='#64748b',
            rangeslider=dict(visible=False),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(99,179,237,0.08)',
            color='#64748b',
            fixedrange=False,
        ),
        height=420,
        margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation='h', y=1.05, x=0, font=dict(color='#94a3b8')),
        dragmode='zoom',
    )
    return fig


########################################
# 메인 UI
########################################

# ── 헤더 ──
st.markdown('<div class="main-title">🎯 전문가 종목 선정 시스템</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">딴보따리 AI 톱다운 시황 및 3x3 매트릭스 필터링 엔진</div>', unsafe_allow_html=True)

# ── 사이드바 필터 ──
with st.sidebar:
    st.markdown("## ⚙️ 검색 조건 설정")
    st.markdown("---")

    market_choice = st.selectbox("📌 시장 선택", ["전체", "KOSPI", "KOSDAQ"])

    st.markdown("**💰 재무 조건**")
    min_mktcap = st.number_input("최소 시가총액 (억)", value=1000, step=500, min_value=100)
    min_trade = st.number_input("최소 거래대금 (억)", value=20, step=10, min_value=1)

    st.markdown("---")
    st.markdown("**🔬 기술적 필터**")
    filter_trend = st.checkbox("정배열 종목만", value=False)
    filter_rsi_min = st.slider("RSI 최솟값", 0, 100, 20)
    filter_rsi_max = st.slider("RSI 최댓값", 0, 100, 75)

    st.markdown("---")
    st.markdown("**📊 결과 설정**")
    top_n = st.slider("상위 종목 수", 5, 50, 20)
    analysis_days = st.selectbox("수급 분석 기간", [10, 20, 30], index=1)
    full_scan = st.checkbox("🔥 전 종목 스캔 (약 10~20분 소요)", value=False, help="체크 시 코스피/코스닥 전 종목을 스캔합니다. 네트워크 요청이 많아 매우 오래 걸릴 수 있습니다.")

    st.markdown("---")
    st.markdown("**⏳ 스윙 기간 선택**")
    swing_period = st.radio("목표 보유 기간", ["3일 (초단기)", "5일 (표준)", "10일 (중기)"])

    # 필터 강도는 "강"으로 고정, 가중치 삭제하고 내부 고정값 사용
    w_norm = None


    st.markdown("---")
    st.info("💡 **사용법**\n1. 검색 조건 설정\n2. '종목 분석 시작' 클릭\n3. 결과에서 종목 선택\n4. 상세 분석 확인")

# ── 세션 상태 초기화 ──
if 'picker_result' not in st.session_state:
    st.session_state.picker_result = None
    st.session_state.picker_base_date = ''
    st.session_state.watchlist = []

# ── 스캔 버튼 ──
col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
with col_btn1:
    run_scan = st.button('🚀 종목 분석 시작', type='primary', use_container_width=True)
with col_btn2:
    if st.button('🔄 캐시 초기화', use_container_width=True):
        st.cache_data.clear()
        st.session_state.picker_result = None
        st.success("캐시를 초기화했습니다.")
with col_btn3:
    st.metric("관심 종목", f"{len(st.session_state.watchlist)}개")

# ── 스캔 실행 ──
if run_scan:
    base_date = get_latest_valid_date()
    st.session_state.picker_base_date = base_date
    
    market_cond = get_market_condition(base_date)
    st.info(f"📊 **현재 KOSPI 장세 판별:** {market_cond}")

    with st.spinner('📡 종목 유니버스 로딩 중...'):
        universe = get_stock_universe(market_choice, min_mktcap, min_trade, full_scan)

    if universe.empty:
        st.error("종목 데이터를 불러올 수 없습니다.")
    else:
        progress_text = st.empty()
        prog_bar = st.progress(0)
        results = []
        total = len(universe) if full_scan else min(len(universe), top_n * 3)

        for i, (_, row) in enumerate(universe.head(total).iterrows()):
            ticker = row['Code']
            name = row['Name']
            mktcap = row['시가총액(억)']
            trade = row['거래대금(억)']
            price = int(row['Close'])

            if i % 3 == 0:
                progress_text.text(f"🔬 분석 중... {name} ({i+1}/{total})")
                prog_bar.progress((i + 1) / total)

            try:
                df_ohlcv = get_ohlcv(ticker, base_date, days=300)
                if df_ohlcv.empty or len(df_ohlcv) < 60:
                    continue

                inv_df = get_investor_flow(ticker, base_date, days=analysis_days)
                indicators = calc_indicators(df_ohlcv, inv_df)
                if indicators is None:
                    continue

                # RSI 필터
                rsi_val = indicators.get('모멘텀지표', {}).get('rsi', 50)
                if not (filter_rsi_min <= rsi_val <= filter_rsi_max):
                    continue

                # 추세 필터
                if filter_trend and '정배열' not in indicators.get('추세강도', {}).get('label', ''):
                    continue

                # 시장 포지션 점수 업데이트
                pos_score, pos_label = calc_market_position_score(mktcap, trade)
                indicators['시장포지션'] = {
                    'score': pos_score,
                    'value': f"시총 {mktcap:.0f}억 | 거래대금 {trade:.0f}억",
                    'label': pos_label,
                    'icon': '🏛️'
                }

                # SmartScore (가중치 없는 원점수 총합)
                smart_score = sum(indicators[k]['score'] for k in indicators)
                
                # 매트릭스 필터 (장세 x 스윙기간) 적용
                passed, tag, sniper_talk = get_matrix_opinion(market_cond, swing_period, indicators, smart_score)
                if not passed:
                    continue
                    
                # 공시 데이터 로드 및 태그 부착
                disclosures = get_recent_disclosures(ticker, days=7)
                if disclosures:
                    tag += " [공시이슈]"
                    
                # 매수밴드 및 손절선 계산
                cur_ma5 = df_ohlcv['종가'].rolling(5).mean().iloc[-1]
                cur_ma20 = df_ohlcv['종가'].rolling(20).mean().iloc[-1]
                buy_band_high = price
                buy_band_low = min(price, cur_ma5 * 0.99)
                stop_loss = cur_ma20 * 0.98
                
                # 추세 방향
                trend_dir = "↑상승" if price > cur_ma20 else "↓하락"

                results.append({

                    '티커': ticker,
                    '종목명': name,
                    '섹터': row.get('Sector', '기타'),
                    '현재가': price,
                    '시가총액(억)': round(mktcap),
                    '거래대금(억)': round(trade, 1),
                    'SmartScore': smart_score,
                    'AI Tag': tag,
                    '매수밴드': f"{int(buy_band_low):,}~{int(buy_band_high):,}",
                    '손절선': f"{int(stop_loss):,}",
                    '추세': trend_dir,
                    '스나이퍼 톡': sniper_talk,
                    '_indicators': indicators,
                    '_disclosures': disclosures,
                })
            except:
                continue

        prog_bar.empty()
        progress_text.empty()

        results.sort(key=lambda x: x['SmartScore'], reverse=True)
        top_results = results[:top_n]
        
        # 히스토리 로드 및 업데이트 (출현빈도, 최초점수 계산)
        import pandas as pd
        
        # 1. Supabase 연동 시도
        use_supabase = False
        supabase_client = None
        try:
            if "supabase" in st.secrets:
                from supabase import create_client, Client
                url: str = st.secrets["supabase"]["url"]
                key: str = st.secrets["supabase"]["key"]
                supabase_client: Client = create_client(url, key)
                use_supabase = True
        except Exception as e:
            pass # Secrets가 없거나 모듈이 없으면 로컬 CSV 폴백 유지
            
        today_str = base_date
        history_df = pd.DataFrame(columns=['Date', 'Ticker', 'Score'])
        
        if use_supabase:
            try:
                # Supabase에서 데이터 가져오기
                response = supabase_client.table("v51_history").select("*").execute()
                if response.data:
                    history_df = pd.DataFrame(response.data)
                    history_df.rename(columns={'date': 'Date', 'ticker': 'Ticker', 'score': 'Score'}, inplace=True)
                
                # 새로운 종목들을 DB에 삽입 (동일 날짜/종목 중복 방지 로직 포함)
                new_records = []
                for r in top_results:
                    # 오늘 날짜에 이미 추가된 기록인지 확인
                    if not history_df.empty and len(history_df[(history_df['Date'] == today_str) & (history_df['Ticker'] == r['티커'])]) > 0:
                        continue
                    new_records.append({'date': today_str, 'ticker': r['티커'], 'score': r['SmartScore']})
                
                if new_records:
                    supabase_client.table("v51_history").insert(new_records).execute()
                    
                    # 방금 넣은 데이터까지 포함하도록 데이터프레임 업데이트
                    new_df = pd.DataFrame(new_records)
                    new_df.rename(columns={'date': 'Date', 'ticker': 'Ticker', 'score': 'Score'}, inplace=True)
                    history_df = pd.concat([history_df, new_df], ignore_index=True)
            except Exception as e:
                st.warning(f"Supabase 연동 오류 (로컬 모드로 전환됩니다): {e}")
                use_supabase = False

        if not use_supabase:
            # 2. 로컬 CSV 폴백
            history_file = "v51_history.csv"
            import os
            if os.path.exists(history_file):
                history_df = pd.read_csv(history_file)
            
            new_rows = [{'Date': today_str, 'Ticker': r['티커'], 'Score': r['SmartScore']} for r in top_results]
            history_df = pd.concat([history_df, pd.DataFrame(new_rows)], ignore_index=True)
            history_df.drop_duplicates(subset=['Date', 'Ticker'], keep='last', inplace=True)
            history_df.to_csv(history_file, index=False)
        
        # 출현빈도, 최초점수 산출
        for r in top_results:
            ticker_hist = history_df[history_df['Ticker'] == r['티커']]
            r['출현빈도'] = len(ticker_hist)
            r['최초점수'] = int(ticker_hist.iloc[0]['Score']) if len(ticker_hist) > 0 else int(r['SmartScore'])
            # 가중치는 임의 로직 (출현빈도 * 1.5 + SmartScore / 50)
            r['가중치'] = round((r['출현빈도'] * 1.5) + (r['SmartScore'] / 50), 2)
            
        st.session_state.picker_result = top_results
        st.success(f"✅ 분석 완료! {len(results)}개 종목 중 상위 {min(top_n, len(results))}개 선별")

# ── 결과 표시 ──
if st.session_state.picker_result:
    results_list = st.session_state.picker_result
    base_date = st.session_state.picker_base_date
    market_cond = get_market_condition(base_date)

    st.markdown("---")

    # ── 요약 테이블 ──
    st.markdown('<div class="section-header">📋 종목 선정 결과 — 장세 맞춤형 추천</div>', unsafe_allow_html=True)
    
    # 상단 요약 텍스트
    top_picks = [f"📌{r['종목명']}({r['섹터']})" for r in results_list[:3]]
    top_picks_str = ", ".join(top_picks)
    st.markdown(f"**AI 딴주머니 시황 브리핑:** [{len(results_list)}개 완료] 🏆 [{swing_period} Top-Pick] {top_picks_str}")
    st.markdown(f"**현재 시장은 '{market_cond}' 특성 속에서 선별적인 움직임을 보이고 있습니다. 상위 추출 종목들은 수급과 모멘텀이 검증된 '딴주머니' 타점입니다.**")

    rank_icons = {1: '🥇', 2: '🥈', 3: '🥉'}
    table_data = []
    for i, r in enumerate(results_list, 1):
        price_str = f"{r['현재가']:,}"
        table_data.append({
            '순위': rank_icons.get(i, f"{i}위"),
            '유형': "S등급" if r['SmartScore'] >= 600 else ("A등급" if r['SmartScore'] >= 500 else "순수보따리"),
            '코드': r['티커'],
            '종목명': r['종목명'],
            '섹터': r['섹터'],
            '현재가': price_str,
            'SmartScore': int(r['SmartScore']),
            '출현빈도': r.get('출현빈도', 1),
            '가중치': r.get('가중치', 5.0),
            '최초점수': r.get('최초점수', int(r['SmartScore'])),
            'AI Tag': r['AI Tag'],
        })

    df_table = pd.DataFrame(table_data)

    event = st.dataframe(
        df_table,
        use_container_width=True,
        height=min(60 + len(table_data) * 35, 600),
        selection_mode="single-row",
        on_select="rerun",
        hide_index=True
    )
    
    st.info("💡 행(Row)의 왼쪽 체크박스를 선택하면 상세 분석 차트와 수급 동향이 팝업으로 나타납니다.")

    # ── 상세 분석 팝업 기능 ──
    @st.dialog("딴보따리 V1 - 정밀 종목 분석", width="large")
    def show_detail_dialog(sel, base_date):
        sel_ind = sel['_indicators']
        final_sc = sel['SmartScore']

        col_h1, col_h2 = st.columns([3, 1])
        with col_h1:
            st.markdown(f"### 📢 {sel['종목명']} ({sel['티커']})")
            st.markdown(f"**섹터:** {sel['섹터']} | **현재가:** {sel['현재가']:,}원")
            st.markdown(f"**핵심 지표:** SmartScore {final_sc} | {sel['AI Tag']}")
            st.markdown(f"**매수 타점 & 리스크:** 매수밴드 {sel['매수밴드']} | 손절선 {sel['손절선']}")
        with col_h2:
            opinion, judgment, badge, judgment_detail = get_expert_opinion(final_sc, sel_ind)
            st.markdown(f"<span class='{badge}'>{judgment}</span>", unsafe_allow_html=True)

        st.markdown("---")
        
        # ── AI Tag 및 공시이슈 분석 ──
        st.markdown("### 🤖 AI Tag 및 공시이슈 분석")
        tag_explain = ""
        if "역행 주도주" in sel['AI Tag']:
            tag_explain += "✅ **[역행 주도주]**: 현재 시장 상황(하락장 또는 혼조세)에도 불구하고 지수를 역행하며 강하게 상승하는 종목으로, 세력의 수급이 몰려있을 확률이 높습니다.\n\n"
        if "핀셋 눌림목" in sel['AI Tag']:
            tag_explain += "✅ **[핀셋 눌림목]**: 강한 상승 후 거래량 없이 예쁘게 조정을 받고 있는 급소 타점입니다. 반등이 임박했을 가능성이 매우 높습니다.\n\n"
        if "안전마진" in sel['AI Tag']:
            tag_explain += "✅ **[안전마진]**: 펀더멘털 대비 주가가 바닥권에 있으며 변동성이 낮아, 매수 시 하방 리스크(손실 위험)가 매우 적은 종목입니다.\n\n"
        if "모멘텀 급소" in sel['AI Tag'] or "수급" in sel['AI Tag'] or "불기둥" in sel['AI Tag']:
            tag_explain += "✅ **[수급 집중/모멘텀]**: 기관과 외국인의 강력한 양매수가 터지며 추세 상승 모멘텀을 막 형성하기 시작한 초입 구간입니다.\n\n"
        
        if tag_explain:
            st.info(tag_explain)
        else:
            st.info("우량한 필터 조건을 모두 통과한 선별 종목입니다.")
            
        disclosures = sel.get('_disclosures', [])
        if disclosures:
            for d in disclosures:
                ana = analyze_disclosure(d['title'], sel['티커'], d['id'])
                is_expanded = ('특이' in ana['type'] or '악재' in ana['type'] or '호재' in ana['type'])
                with st.expander(f"{ana['type']} | {d['date']} | {d['title']}", expanded=is_expanded):
                    st.markdown(f"**💡 AI 분석 요약:** {ana['reason']}")
                    st.markdown(f"**📈 주가 영향력 예측:** `{ana['impact']}`")
        else:
            st.markdown("<span style='color:#64748b; font-size:13px;'>최근 7일 이내에 발생한 주요 공시가 없습니다.</span>", unsafe_allow_html=True)

        st.markdown("---")

        df_ohlcv = get_ohlcv(sel['티커'], base_date, days=150)
        candle_fig = render_candle_chart(df_ohlcv, sel['종목명'], sel['티커'])
        if candle_fig:
            st.plotly_chart(candle_fig, use_container_width=True)

        st.markdown("**💰 이전 30영업일 수급 동향**")
        inv_df = get_investor_flow(sel['티커'], base_date, days=30)
        if not inv_df.empty:
            inv_disp = inv_df.copy()
            if '개인' not in inv_disp: inv_disp['개인'] = 0
            if '금융투자' not in inv_disp: inv_disp['금융투자'] = 0
            
            inv_disp['외인+기관'] = inv_disp['외국인합계'] + inv_disp['기관합계']
            inv_disp['수급상태'] = inv_disp.apply(lambda x: '🔥 쌍끌이 매수' if x['외국인합계']>0 and x['기관합계']>0 else ('🔴 개미털기(매도)' if x['개인']>0 and x['외인+기관']<0 else '관망'), axis=1)
            
            show_cols = ['종가', '개인', '외국인합계', '기관합계', '외인+기관', '수급상태', '금융투자']
            exist_cols = [c for c in show_cols if c in inv_disp.columns]
            
            inv_disp = inv_disp[exist_cols].sort_index(ascending=False).head(30)
            
            # 숫자 포맷
            for c in ['종가', '개인', '외국인합계', '기관합계', '외인+기관', '금융투자']:
                if c in inv_disp:
                    inv_disp[c] = inv_disp[c].apply(lambda x: f"{x:,.0f}" if pd.notnull(x) else "0")
            
            st.dataframe(inv_disp, use_container_width=True)

    if "last_selection" not in st.session_state:
        st.session_state.last_selection = []

    current_selection = event.selection.rows if event else []
    
    if current_selection != st.session_state.last_selection:
        st.session_state.last_selection = current_selection
        if len(current_selection) > 0:
            sel_idx = current_selection[0]
            selected_row = results_list[sel_idx]
            show_detail_dialog(selected_row, base_date)

else:
    # 초기 화면
    st.markdown("---")
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("""
        <div class="score-card">
            <div style="font-size:36px; text-align:center; margin-bottom:10px;">📊</div>
            <div style="font-weight:700; color:#e2e8f0; text-align:center; margin-bottom:8px;">8가지 전문가 지표</div>
            <div style="color:#94a3b8; font-size:13px; line-height:1.7;">
                추세강도, 모멘텀, 기관수급, 외국인수급, 가격모멘텀, 거래량모멘텀, 변동성리스크, 시장포지션을 종합 평가합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_g2:
        st.markdown("""
        <div class="score-card">
            <div style="font-size:36px; text-align:center; margin-bottom:10px;">🤖</div>
            <div style="font-weight:700; color:#e2e8f0; text-align:center; margin-bottom:8px;">AI 전문가 의견</div>
            <div style="color:#94a3b8; font-size:13px; line-height:1.7;">
                각 지표를 종합하여 매수·중립·신중 판단과 전문가급 텍스트 의견을 자동 생성합니다.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_g3:
        st.markdown("""
        <div class="score-card">
            <div style="font-size:36px; text-align:center; margin-bottom:10px;">⚙️</div>
            <div style="font-weight:700; color:#e2e8f0; text-align:center; margin-bottom:8px;">맞춤형 가중치</div>
            <div style="color:#94a3b8; font-size:13px; line-height:1.7;">
                투자 성향에 맞게 가중치를 직접 조절할 수 있습니다. 기술·수급·모멘텀 비중을 자유롭게 설정하세요.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; color:#64748b; font-size:13px; padding:20px;">
        ⚠️ 본 프로그램은 투자 참고용입니다. 실제 투자 결정은 본인의 판단과 책임 하에 이루어져야 합니다.
    </div>
    """, unsafe_allow_html=True)
