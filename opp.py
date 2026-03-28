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
st.set_page_config(page_title="Beta Lab AI V9.5 - 數據全量體", layout="wide")

# 2. 安全驗證 (密碼 8888)
if "password_correct" not in st.session_state:
    st.markdown("### 🖥️ 內部開發監測系統 V9.5")
    pwd = st.text_input("存取密碼", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- [核心修正] 解決 404 與 數據權限 的配置 ---
@st.cache_resource
def init_gemini():
    try:
        # 確保從 Secrets 讀取 Key
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # 使用雙重相容路徑，優先使用 models/ 前綴
        return genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        st.error(f"❌ AI 配置失敗: {e}")
        return None

model = init_gemini()

# 3. CSS 高密度戰鬥樣式 (確保 UI 不會跑掉)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #ddd; background: white; box-shadow: 2px 4px 12px rgba(0,0,0,0.08); }
    .ai-diag-box { background: #f0f5ff; border-left: 6px solid #1890ff; padding: 18px; border-radius: 10px; margin: 15px 0; color: #002766; font-size: 1.05em; line-height: 1.6; }
    .metric-tag { display: inline-block; padding: 4px 12px; background: #f5f5f5; border-radius: 6px; margin-right: 8px; font-size: 0.9em; font-weight: bold; color: #333; }
    .defense-box { background: #fcfcfc; border: 1.5px dashed #595959; padding: 15px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-family: 'Courier New', monospace; font-weight: bold; color: #d4380d; font-size: 1.1em; }
    .logic-box { background: #fffbe6; padding: 15px; border-radius: 10px; border: 1px solid #ffe58f; }
    </style>
    """, unsafe_allow_html=True)

# 4. 核心數據算法 (找回所有遺失的邏輯)
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

# 5. 主分析流程
tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", 
    "MU": "美光", "2303.TW": "聯電", "2344.TW": "華邦電", "3481.TW": "群創"
}

# 抓取大盤與波動率
try:
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_trend = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
    market_context = f"VIX: {vix:.1f}, 費半狀態: {sox_trend}"
except:
    market_context = "無法取得即時大盤數據"

st.title("🖥️ 全球量化戰鬥系統 V9.5 - AI 數據全回歸")
timer_placeholder = st.empty()

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # --- [數據回歸 1] 核心價格指標 ---
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        rsi = (df['Close'].diff().where(df['Close'].diff()>0,0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean()*100).iloc[-1]
        
        # --- [數據回歸 2] 風控與預警指標 ---
        chip = get_institutional_flow(df)
        swing_high = df['High'].tail(5).max() * 0.97      # 波段高點預警 (原數據)
        atr_val = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        defense_line = close - (2.5 * atr_val)           # ATR 底線 (原數據)
        vol_support = get_volume_support(df)            # 密集換手區 (原數據)
        
        # --- [數據回歸 3] 回測進場點位 ---
        obs_point = ma20 - 1.2 * std20                  # 觀察點 (原數據)
        pressure = ma20 + 2 * std20                     # 壓力位 (原數據)
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].tail(5).mean() # 成交量比
        
        news = get_google_news(name)
        
        # --- AI 診斷執行 ---
        ai_diag = "AI 診斷啟動中..."
        if model:
            with st.spinner(f'AI 診斷 {name}...'):
                prompt = f"分析{name}({ticker})：現價{close:.2f}, RSI{rsi:.1f}, 籌碼{chip}, 支撐{vol_support:.2f}, 壓力{pressure:.2f}。新聞:{news}。給100字內診斷及操作建議。"
                try:
                    response = model.generate_content(prompt)
                    ai_diag = response.text
                except Exception as e:
                    ai_diag = f"⚠️ AI 診斷出錯: {str(e)}"
        else:
            ai_diag = "⚠️ AI 模型未正確啟動，請檢查 Secrets 裡的 GEMINI_API_KEY。"

        # --- UI 渲染：數據全量展示 ---
        st.markdown(f"""
        <div class="status-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.7em; font-weight:bold;">{name} ({ticker}) — <span style="font-family:monospace;">${close:.2f}</span></span>
                <div>
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                    <span class="metric-tag">籌碼: {chip}</span>
                    <span class="metric-tag">PE: {stock.info.get('forwardPE', 'N/A')}</span>
                </div>
            </div>
            
            <div class="ai-diag-box">
                <b>🤖 Gemini AI 市場綜合診斷報告：</b><br>{ai_diag}
            </div>

            <div style="display: flex; gap: 20px;">
                <div style="flex: 2;">
                    <div class="defense-box">
                        🛡️ <b>關鍵防禦與風控指標：</b><br>
                        波段高點預警: <span class="price-value">{swing_high:.2f}</span> | 
                        ATR 演算底線(停損): <span class="price-value">{defense_line:.2f}</span> <br>
                        密集換手區(支撐): <span class="price-value">{vol_support:.2f}</span> | 成交量比: {vol_ratio:.1f}x
                    </div>
                </div>
                <div style="flex: 1;">
                    <div class="logic-box">
                        🧪 <b>量化回測點位：</b><br>
                        🟢 <b>進場觀察點</b>: <span style="color:#389e0d; font-weight:bold; font-size:1.1em;">{obs_point:.2f}</span><br>
                        🎯 <b>預計壓力位</b>: <span style="color:#cf1322; font-weight:bold; font-size:1.1em;">{pressure:.2f}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"解析 {ticker} 出錯: {e}")

# 自動刷新
for i in range(60, 0, -1):
    timer_placeholder.write(f"🔄 系統將於 {i} 秒後自動刷新市場數據與 AI 分析...")
    time.sleep(1)
st.rerun()
