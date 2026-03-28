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
st.set_page_config(page_title="Beta Lab AI V9.8 - 數據全量體", layout="wide")

# 2. 安全驗證 (密碼 8888)
if "password_correct" not in st.session_state:
    st.markdown("### 🖥️ 內部開發監測系統 V9.8")
    pwd = st.text_input("存取密碼", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- [核心修正] 解決 404 與地區限制的自動切換邏輯 ---
@st.cache_resource
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        return None
    
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    # 嘗試多種模型路徑，解決不同地區的 404 問題
    model_names = ['models/gemini-1.5-flash', 'gemini-1.5-flash', 'models/gemini-pro']
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # 測試是否真的能跑
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

model = init_gemini()

# 3. CSS 戰鬥樣式 (確保數據權限視覺回歸)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #ddd; background: white; }
    .ai-diag-box { background: #f0f5ff; border-left: 6px solid #1890ff; padding: 18px; border-radius: 10px; margin: 15px 0; color: #002766; }
    .metric-tag { display: inline-block; padding: 4px 12px; background: #f5f5f5; border-radius: 6px; margin-right: 8px; font-weight: bold; }
    .defense-box { background: #fcfcfc; border: 1.5px dashed #595959; padding: 15px; border-radius: 10px; margin-top: 15px; }
    .price-value { font-family: monospace; font-weight: bold; color: #d4380d; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# 4. 數據演算函數 (數據權全數歸位)
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

# 5. 監控清單
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "2303.TW": "聯電"}

# 大盤數據
try:
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_trend = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
except: sox_trend = "無法取得"

st.title("🖥️ 全球量化戰鬥系統 V9.8 — AI 診斷版")
timer = st.empty()

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # 核心數據計算
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        rsi = (df['Close'].diff().where(df['Close'].diff()>0,0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean()*100).iloc[-1]
        
        # 你的專屬指標全部弄回來了
        chip = get_institutional_flow(df)
        swing_high = df['High'].tail(5).max() * 0.97 
        atr = 2.5 * (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        defense_line = close - atr
        vol_support = get_volume_support(df)
        obs_point = ma20 - 1.2 * std20
        pressure = ma20 + 2 * std20
        
        # AI 診斷
        if model:
            with st.spinner(f'AI 分析 {name}...'):
                try:
                    p = f"分析{name}({ticker}): 現價{close}, RSI{rsi:.1f}, 籌碼{chip}, 支撐{vol_support:.2f}。給100字內精準診斷。"
                    ai_diag = model.generate_content(p).text
                except: ai_diag = "⚠️ 該模型在當前地區受限，請檢查 Secrets 設定。"
        else:
            ai_diag = "❌ API Key 讀取失敗或模型無法啟動，請重新 Reboot App。"

        # UI 渲染
        st.markdown(f"""
        <div class="status-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.6em; font-weight:bold;">{name} ({ticker}) — ${close:.2f}</span>
                <div>
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                    <span class="metric-tag">籌碼: {chip}</span>
                </div>
            </div>
            <div class="ai-diag-box"><b>🤖 Gemini AI 市場報告：</b><br>{ai_diag}</div>
            <div style="display: flex; gap: 20px;">
                <div style="flex: 2;">
                    <div class="defense-box">
                        🛡️ <b>風控指標：</b><br>
                        波段高點預警: <span class="price-value">{swing_high:.2f}</span> | 
                        ATR 底線(停損): <span class="price-value">{defense_line:.2f}</span> <br>
                        密集換手區(支撐): <span class="price-value">{vol_support:.2f}</span>
                    </div>
                </div>
                <div style="flex: 1; background: #fffbe6; padding: 12px; border-radius: 10px;">
                    <b>🧪 量化點位：</b><br>
                    🟢 觀察點: <span style="color:green; font-weight:bold;">{obs_point:.2f}</span><br>
                    🎯 壓力位: <span style="color:red; font-weight:bold;">{pressure:.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

time.sleep(60)
st.rerun()
