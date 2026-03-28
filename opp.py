import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI V8.5", layout="wide")

# 2. 私人存取驗證
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 內部開發監測系統 V8.5")
        pwd = st.text_input("請輸入存取密碼：", type="password")
        if pwd == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password(): st.stop()

# --- [關鍵] Gemini AI 配置與安全檢查 ---
@st.cache_resource
def init_gemini():
    try:
        # 優先從 Streamlit Cloud Secrets 讀取
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"❌ AI 配置失敗: {e}")
        return None

model = init_gemini()

# 3. CSS 樣式定義
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e0e0e0; }
    .ai-diag-box { background: #f0f5ff; border-left: 5px solid #1890ff; padding: 15px; border-radius: 8px; margin: 12px 0; color: #002766; font-size: 1.05em; }
    .metric-tag { display: inline-block; padding: 3px 8px; background: rgba(0,0,0,0.05); border-radius: 4px; margin-right: 5px; font-size: 0.85em; font-weight: bold; }
    .defense-box { background: rgba(0,0,0,0.02); border: 1px dashed #666; padding: 10px; border-radius: 8px; margin-top: 10px; font-size: 0.9em; }
    </style>
    """, unsafe_allow_html=True)

# 4. 數據工具函數
def get_institutional_flow(df):
    recent = df.tail(5)
    score = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: score += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: score -= 1
    return "🔥 強勢買入" if score >= 2 else "💧 持續流出" if score <= -2 else "☁️ 盤整觀望"

def get_volume_support(df):
    try:
        v_hist = np.histogram(df['Close'].tail(60), bins=10, weights=df['Volume'].tail(60))
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

def get_google_news(name):
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={quote(name + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        return [e.title for e in feed.entries[:3]]
    except: return []

# 5. AI 分析執行
def run_ai_analysis(name, data, news, market):
    if not model: return "❌ AI 模型未就緒"
    prompt = f"你是專業分析師。分析{name}：數據{data}、新聞{news}、大盤{market}。請給出100字內精準診斷與操作建議。"
    try:
        return model.generate_content(prompt).text
    except Exception as e:
        return f"⚠️ AI 診斷出錯: {str(e)}"

# 6. 主程式渲染
tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", 
    "MU": "美光", "2303.TW": "聯電", "2344.TW": "華邦電"
}

# 抓取市場環境
vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
sox = yf.Ticker("^SOX").history(period="1mo")
sox_trend = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
market_context = f"VIX: {vix:.1f}, 費半: {sox_trend}"

st.title("🖥️ 全球量化戰鬥系統 V8.5")
timer_place = st.empty()

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        rsi = (df['Close'].diff().where(df['Close'].diff()>0,0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean()*100).iloc[-1]
        chip = get_institutional_flow(df)
        news = get_google_news(name)
        
        # 執行 AI 診斷
        with st.spinner(f'AI 診斷 {name}...'):
            diag = run_ai_analysis(name, {"價":close, "RSI":rsi, "籌碼":chip}, news, market_context)

        # UI 渲染
        st.markdown(f"""
        <div class="status-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.5em; font-weight: bold;">{name} ({ticker}) - ${close:.2f}</span>
                <div>
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                    <span class="metric-tag">籌碼: {chip}</span>
                </div>
            </div>
            <div class="ai-diag-box"><b>🤖 Gemini AI 診斷：</b><br>{diag}</div>
            <div class="defense-box">
                ⚙️ 風控：波段預警 {df['High'].tail(5).max()*0.97:.2f} | 
                ATR 底線 {close - 2.5*(df['High']-df['Low']).rolling(14).mean().iloc[-1]:.2f} | 
                換手區 {get_volume_support(df):.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

for i in range(60, 0, -1):
    timer_place.write(f"🔄 {i}s 後刷新數據與 AI 分析")
    time.sleep(1)
st.rerun()
