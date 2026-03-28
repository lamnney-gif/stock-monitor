import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI V7.0 - 真數據分析版", layout="wide")

# 2. 私人存取驗證
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🤖 真·AI 數據分析系統")
        pwd = st.text_input("請輸入內部密碼：", type="password")
        if pwd == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password(): st.stop()

# 3. CSS 樣式 (極簡資訊排版)
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #ddd; }
    .ai-box { background: #f0f5ff; border: 1px solid #adc6ff; padding: 12px; border-radius: 8px; margin-top: 10px; border-left: 5px solid #1890ff; }
    .metric-tag { display: inline-block; padding: 3px 10px; background: #f0f0f0; border-radius: 5px; margin-right: 8px; font-size: 0.85em; font-weight: bold; }
    .tag-danger { color: #cf1322; background: #fff1f0; }
    .tag-success { color: #389e0d; background: #f6ffed; }
    </style>
    """, unsafe_allow_html=True)

# 4. 【核心】真·AI 數據分析引擎
def get_ai_reasoning(d, vix, sox_status):
    """
    將所有硬數據丟入此函數，模擬 AI 分析師進行多維度解讀
    """
    analysis = []
    
    # 邏輯 A：環境與大盤 (SOX & VIX)
    if sox_status == "BEAR": analysis.append("大盤環境(SOX)偏弱，壓制個股表現。")
    if vix > 22: analysis.append(f"全球恐慌感上升(VIX:{vix:.1f})，資金避險情緒濃。")
    
    # 邏輯 B：籌碼與趨勢 (Chip Flow & Trend)
    if d['chip_flow'] == "🔥 強勢買入": analysis.append("法人資金逆勢進駐。")
    elif d['chip_flow'] == "💧 持續流出": analysis.append("主力資金持續撤離，小心支撐被打穿。")
    
    if d['trend'] == "🌟 多頭排列": analysis.append("均線結構極佳，具備上攻動能。")
    
    # 邏輯 C：ADR 連動與溢價
    if d['adr'] != "N/A":
        val = float(d['adr'].strip('%'))
        if val > 1.5: analysis.append(f"ADR強勢領漲({d['adr']})，具備溢價優勢。")
        elif val < -1.5: analysis.append(f"ADR重挫跌勢未止，台股壓力沉重。")

    # 邏輯 D：綜合戰術結論 (精簡回傳)
    score = 50
    if sox_status == "BULL": score += 20
    if d['chip_flow'] == "🔥 強勢買入": score += 20
    if d['trend'] == "🌟 多頭排列": score += 10
    if vix > 25: score -= 30

    final_msg = " / ".join(analysis) if analysis else "數據處於平衡區，暫無明顯多空導向。"
    
    return score, final_msg

# 5. 指標運算函數
def get_institutional_flow(df):
    recent = df.tail(5)
    flow = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow -= 1
    return "🔥 強勢買入" if flow >= 2 else "💧 持續流出" if flow <= -2 else "☁️ 盤整觀望"

# 6. 主程式迴圈
tickers = {
    "2330.TW": {"name": "台積電", "adr": "TSM"},
    "NVDA": {"name": "輝達", "adr": None},
    "TSM": {"name": "台積電ADR", "adr": None},
    "MU": {"name": "美光", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"},
    "2344.TW": {"name": "華邦電", "adr": None}
}

st.sidebar.title("📊 全球數據中心")
vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
sox = yf.Ticker("^SOX").history(period="1mo")
sox_status = "BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "BEAR"

st.sidebar.metric("VIX 恐慌指數", f"{vix:.1f}", delta="-避險中" if vix > 22 else "樂觀", delta_color="inverse")
st.sidebar.metric("SOX 費半趨勢", sox_status)

for ticker, info in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # 準備 AI 餵入數據
        chip_flow = get_institutional_flow(df)
        ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
        trend = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
        
        adr_diff = "N/A"
        if info['adr']:
            adr_px = yf.Ticker(info['adr']).history(period="5d")['Close']
            adr_diff = f"{( (adr_px.iloc[-1] - adr_px.iloc[-2]) / adr_px.iloc[-2] * 100):+.1f}%"

        # --- 調用 AI 診斷引擎 ---
        ai_score, ai_result = get_ai_reasoning(
            {'chip_flow': chip_flow, 'trend': trend, 'adr': adr_diff}, vix, sox_status
        )

        # UI 顯示
        st.markdown(f"""
        <div class="status-card">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-size: 1.5em; font-weight: bold;">{info['name']} ({ticker}) <span style="font-family:monospace;">${close:.2f}</span></span>
                <span style="font-size: 1.2em; color: {'#389e0d' if ai_score > 60 else '#cf1322'};">勝率評估: {ai_score}%</span>
            </div>
            <div style="margin-top: 8px;">
                <span class="metric-tag">ADR連動: {adr_diff}</span>
                <span class="metric-tag">籌碼: {chip_flow}</span>
                <span class="metric-tag">趨勢: {trend}</span>
                <span class="metric-tag">RSI: {int((df['Close'].diff().where(df['Close'].diff()>0, 0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean() * 100).iloc[-1])}</span>
            </div>
            <div class="ai-box">
                <b>🤖 AI 分析診斷：</b><br>{ai_result}
            </div>
            <div style="margin-top: 10px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.85em; color: #666;">
                <div>波段高點: {df['High'].tail(5).max()*0.97:.2f}</div>
                <div>ATR底線: {close - (2.5 * (df['High']-df['Low']).rolling(14).mean().iloc[-1]):.2f}</div>
                <div>模型觀察點: {ma20 - 1.2*std20:.2f}</div>
                <div>預計壓力: {ma20 + 2*std20:.2f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

time.sleep(60)
st.rerun()
