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
st.set_page_config(page_title="Beta Lab AI V9.9", layout="wide")

# 2. 安全驗證
if "password_correct" not in st.session_state:
    st.markdown("### 🖥️ 內部開發監測系統 V9.9")
    pwd = st.text_input("存取密碼", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- [核心修正] 絕對啟動邏輯：解決 404 與地區報錯 ---
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        # 嘗試使用最穩定的模型名稱
        return genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        return f"AI 初始化失敗: {e}"

model_engine = init_gemini()

# 3. CSS 戰鬥樣式
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #ddd; background: white; box-shadow: 2px 4px 12px rgba(0,0,0,0.08); }
    .ai-diag-box { background: #f0f5ff; border-left: 6px solid #1890ff; padding: 18px; border-radius: 10px; margin: 15px 0; color: #002766; font-size: 1.05em; }
    .metric-tag { display: inline-block; padding: 4px 12px; background: #f5f5f5; border-radius: 6px; margin-right: 8px; font-weight: bold; }
    .defense-box { background: #fcfcfc; border: 1.5px dashed #595959; padding: 15px; border-radius: 10px; margin-top: 15px; }
    .price-value { font-family: monospace; font-weight: bold; color: #d4380d; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# 4. 數據演算（確保所有權限回歸）
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

# 5. 主分析迴圈
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "2303.TW": "聯電", "2344.TW": "華邦電"}

st.title("🖥️ 全球量化戰鬥系統 V9.9")
timer_placeholder = st.empty()

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # --- 數據計算開始 ---
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        rsi = (df['Close'].diff().where(df['Close'].diff()>0,0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean()*100).iloc[-1]
        
        chip = get_institutional_flow(df)
        swing_high = df['High'].tail(5).max() * 0.97
        defense_line = close - (2.5 * (df['High']-df['Low']).rolling(14).mean().iloc[-1])
        vol_support = get_volume_support(df)
        obs_point = ma20 - 1.2 * std20
        pressure = ma20 + 2 * std20
        # ------------------

        # AI 診斷邏輯
        ai_diag = "AI 診斷啟動中..."
        if isinstance(model_engine, str):
            ai_diag = model_engine
        else:
            try:
                with st.spinner(f'AI 診斷 {name}...'):
                    prompt = f"分析{name}({ticker})：現價{close:.2f}, RSI{rsi:.1f}, 籌碼{chip}。請給100字診斷。"
                    ai_diag = model_engine.generate_content(prompt).text
            except Exception as e:
                ai_diag = f"⚠️ 地區連線受限或 API 異常: {str(e)}"

        # 渲染 UI
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
                        🛡️ <b>關鍵防禦指標：</b><br>
                        波段高點預警: <span class="price-value">{swing_high:.2f}</span> | 
                        ATR 底線(停損): <span class="price-value">{defense_line:.2f}</span> <br>
                        密集換手區(支撐): <span class="price-value">{vol_support:.2f}</span>
                    </div>
                </div>
                <div style="flex: 1; background: #fffbe6; padding: 15px; border-radius: 10px; border: 1px solid #ffe58f;">
                    <b>🧪 量化點位：</b><br>
                    🟢 觀察點: <span style="color:green; font-weight:bold;">{obs_point:.2f}</span><br>
                    🎯 壓力位: <span style="color:red; font-weight:bold;">{pressure:.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

# 刷新
time.sleep(60)
st.rerun()
