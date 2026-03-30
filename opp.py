import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time
import random
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 終極全量版", layout="wide")

# --- 2. AI 核心啟動 ---
@st.cache_resource
def init_ai_engines():
    engines = {"groq": None}
    try:
        if "GROQ_API_KEY" in st.secrets:
            engines["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except: pass
    return engines

ai_engines = init_ai_engines()

# 2. 密碼驗證
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.markdown("### 🖥️ 內部開發監測系統 V6.8.5")
    pwd = st.text_input("請輸入存取密碼：", type="password", key="password_input")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    return False

if not check_password(): st.stop()

# 3. CSS 樣式 (一字不漏，包含 🟣 標籤與所有顏色)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    .mobile-warning { background-color: #fff2f0; border: 2px solid #ffccc7; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 10px solid #ff4d4f; }
    .news-link { color: #1890ff; text-decoration: none; font-size: 0.85em; display: block; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 側邊欄 (一字不漏)
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px; font-size: 0.85em;">
    <b>【免責聲明】</b><br>
    1. 本網頁為個人量化模型開發測試用途。<br>
    2. 內文診斷皆為演算法實驗產出，非投資建議。<br>
    3. 投資有風險，過去績效不代表未來表現。
</div>
""", unsafe_allow_html=True)

# RSS 抓取 (一字不漏)
def get_stock_news(q):
    try:
        url = f"https://news.google.com/rss/search?q={quote(q)}+stock&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        return feed.entries[:3]
    except: return []

# 4. AI 診斷 (帶緩存與重試機制)
@st.cache_data(ttl=3600)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev, bias, slope):
    if not ai_engines["groq"]: return "❌ Groq 離線"
    prompt = f"[投資長獵殺] {name}: 價{price}, RSI{rsi:.1f}, 籌碼{chip_flow}, 趨勢{trend}, PE{pe}, 營收{rev}. 120字內分析。"
    try:
        time.sleep(random.uniform(4.0, 6.0)) # 嚴格降頻
        res = ai_engines["groq"].chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "你是語氣狠準狂的傳奇投資長。"},{"role": "user", "content": prompt}],
            timeout=15.0
        )
        return "🦅 巔峰決策： " + res.choices[0].message.content.strip()
    except: return "📊 智庫忙碌 (Rate Limit)，暫觀技術指標。"

# 5. 主程序與數據循環
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

st.title("🖥️ Beta Lab AI Ultimate")
st.markdown('<div class="mobile-warning">⚠️ 個人實驗環境 - 自動化實驗產出，非投資建議。</div>', unsafe_allow_html=True)
timer_placeholder = st.empty()

# 全球指標
v_df = yf.Ticker("^VIX").history(period="1d")
vix = round(v_df['Close'].iloc[-1], 2) if not v_df.empty else 20.0
sox_df = yf.Ticker("^SOX").history(period="1mo")
sox_status = "📈 BULL" if (not sox_df.empty and sox_df['Close'].iloc[-1] > sox_df['Close'].mean()) else "📉 BEAR"
st.sidebar.markdown(f"📊 **全球指標**\n- VIX: {vix}\n- SOX: {sox_status}")

# 核心循環 (強制渲染每一檔)
for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        s_info = stock.info
        close_val = df['Close'].iloc[-1]
        ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
        
        # 數據一字不漏
        pe_val = f"{s_info.get('trailingPE', 0):.1f}"
        rev_growth = f"{(s_info.get('revenueGrowth', 0) or 0) * 100:.1f}%"
        inst_hold = f"{s_info.get('heldPercentInstitutions', 0)*100:.1f}%"
        rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
        atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
        bias = round(((close_val - ma20) / ma20) * 100, 2)
        slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100
        
        # 呼叫 AI
        ai_report = get_ai_analysis(name, close_val, rsi_val, "數據追蹤", "多頭", pe_val, rev_growth, bias, round(slope,2))
        
        # 標籤判定 (🟣、✅、☢️)
        if rsi_val < 30: style = "🟣"
        elif rsi_val > 70: style = "☢️"
        elif sox_status == "📈 BULL": style = "✅"
        else: style = "⚠️"

        news_items = get_stock_news(name)
        news_html = "".join([f'<a class="news-link" href="{n.link}" target="_blank">📰 {n.title[:40]}...</a>' for n in news_items])

        # 渲染 UI (一個字都沒漏，包含斜率、ATR、支撐)
        st.markdown(f"""
        <div class="status-card {style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><span style="font-size: 1.6em; font-weight: bold;">{name} ({ticker})</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${round(close_val, 2)}</span></div>
                <span class="metric-tag">RSI: {round(rsi_val, 1)} | 乖離: {bias}%</span>
            </div>
            <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
                PE: {pe_val} | 營收成長: {rev_growth} | 機構持股: {inst_hold} | 斜率: {round(slope, 2)}%
            </div>
            <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="display: flex; gap: 25px;">
                <div style="flex: 2.2;">
                    <b>🧠 巔峰決策：</b><br><span style="line-height:1.6; font-size:1.1em;">{ai_report}</span>
                    <div class="defense-box">
                        ⚙️ 風控： <span style="color:#1890ff;">止盈防線: {round(df['High'].tail(5).max()*0.97, 2)}</span> | <span style="color:#cf1322; font-weight:bold;">ATR地板: {round(close_val - 2.5*atr_val, 2)}</span> | 斜率: {round(slope, 2)}%
                    </div>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 12px; border-radius: 10px; border: 1px solid #d9d9d9;">
                    <b>🎯 實時速報：</b><br>{news_html if news_html else "暫無新聞"}
                    <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div><span class="price-label">🟢 買點</span><br><span class="price-value" style="color:#389e0d;">{round(ma20-1.2*std20, 2)}</span></div>
                        <div><span class="price-label">🎯 壓力</span><br><span class="price-value" style="color:#cf1322;">{round(ma20+2*std20, 2)}</span></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1.0) # 防止 yfinance 頻率限制
    except Exception as e:
        continue

# 刷新計時
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新")
    time.sleep(1)
st.rerun()
