import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import feedparser
from datetime import datetime
from urllib.parse import quote
import time

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI V8.8 - 數據全量回歸", layout="wide")

# 2. 安全驗證
if "password_correct" not in st.session_state:
    st.markdown("### 🖥️ 內部開發監測系統 V8.8")
    if st.text_input("密碼", type="password") == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- [關鍵] Gemini AI 穩定配置 ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 使用最通用的模型名稱以避免 404
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ AI 配置錯誤: {e}")
    st.stop()

# 3. CSS 高密度樣式 (保留所有視覺標籤)
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #ddd; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .ai-diag-box { background: #f0f5ff; border-left: 6px solid #1890ff; padding: 15px; border-radius: 8px; margin: 12px 0; color: #002766; font-size: 1.05em; }
    .metric-tag { display: inline-block; padding: 3px 8px; background: #f0f0f0; border-radius: 4px; margin-right: 5px; font-size: 0.85em; font-weight: bold; }
    .defense-box { background: #fafafa; border: 1px dashed #666; padding: 12px; border-radius: 8px; margin-top: 10px; font-size: 0.95em; }
    .price-value { font-family: monospace; font-weight: bold; color: #111; }
    </style>
    """, unsafe_allow_html=True)

# 4. 核心數據算法 (找回所有遺失邏輯)
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

# 5. 主程式
tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", 
    "MU": "美光", "2303.TW": "聯電", "2344.TW": "華邦電", "3481.TW": "群創"
}

# 全球環境
vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
sox = yf.Ticker("^SOX").history(period="1mo")
sox_trend = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
market_context = f"VIX: {vix:.1f}, 費半狀態: {sox_trend}"

st.title("🖥️ 全球量化戰鬥系統 V8.8 - 數據完全體")
placeholder = st.empty()

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # 1. 基礎數據
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        rsi = (df['Close'].diff().where(df['Close'].diff()>0,0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean()*100).iloc[-1]
        
        # 2. 找回你的核心指標
        chip = get_institutional_flow(df)
        swing_high = df['High'].tail(5).max() * 0.97  # 波段高點預警
        atr = 2.5 * (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        defense_line = close - atr                  # ATR 底線
        vol_support = get_volume_support(df)        # 密集換手區
        obs_point = ma20 - 1.2 * std20              # 觀察點
        pressure = ma20 + 2 * std20                 # 壓力位
        news = get_google_news(name)
        
        # 3. AI 診斷
        with st.spinner(f'AI 正在診斷 {name}...'):
            prompt = f"分析{name}({ticker})：價{close}, RSI{rsi:.1f}, 籌碼{chip}, 大盤{market_context}。新聞：{news}。請給100字診斷與具體支撐壓力建議。"
            try:
                ai_diag = model.generate_content(prompt).text
            except Exception as e:
                ai_diag = f"⚠️ AI 診斷不可用: {str(e)}"

        # 4. UI 渲染 (所有欄位全數回歸)
        st.markdown(f"""
        <div class="status-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.6em; font-weight:bold;">{name} ({ticker}) - <span style="font-family:monospace;">${close:.2f}</span></span>
                <div>
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                    <span class="metric-tag">籌碼: {chip}</span>
                    <span class="metric-tag">PE: {stock.info.get('forwardPE', 'N/A')}</span>
                </div>
            </div>
            
            <div class="ai-diag-box">
                <b>🤖 Gemini AI 市場綜合診斷：</b><br>{ai_diag}
            </div>

            <div style="display: flex; gap: 15px;">
                <div style="flex: 2;">
                    <div class="defense-box">
                        ⚙️ <b>風控與成本模擬：</b><br>
                        波段高點預警: <span class="price-value">{swing_high:.2f}</span> | 
                        ATR 演算底線: <span class="price-value">{defense_line:.2f}</span> <br>
                        密集換手區: <span class="price-value">{vol_support:.2f}</span> | 成交量比: {df['Volume'].iloc[-1]/df['Volume'].tail(5).mean():.1f}x
                    </div>
                </div>
                <div style="flex: 1; background: rgba(0,0,0,0.03); padding: 12px; border-radius: 8px;">
                    <b>🧪 邏輯回測參數：</b><br>
                    🟢 觀察點: <span style="color:green; font-weight:bold;">{obs_point:.2f}</span><br>
                    🎯 壓力位: <span style="color:red; font-weight:bold;">{pressure:.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

time.sleep(60)
st.rerun()
