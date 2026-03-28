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
st.set_page_config(page_title="Beta Lab AI Ultimate V8.2", layout="wide")

# 2. 安全驗證與 AI 配置
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 內部開發監測系統 V8.2")
        pwd = st.text_input("請輸入存取密碼：", type="password", key="password_input")
        if pwd == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password(): st.stop()

# --- 配置 Gemini AI (從 Secrets 讀取) ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ API Key 配置錯誤，請檢查 .streamlit/secrets.toml。錯誤訊息: {e}")
    st.stop()

# 3. CSS 樣式定義 (1600px 高密度版)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .ai-diag-box { background: #f0f5ff; border: 1px solid #adc6ff; padding: 15px; border-radius: 10px; margin: 15px 0; border-left: 6px solid #1890ff; font-size: 1.05em; line-height: 1.6; color: #002766; }
    .metric-tag { display: inline-block; padding: 4px 10px; background: rgba(0,0,0,0.05); border-radius: 6px; margin-right: 8px; font-size: 0.85em; font-weight: bold; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. 核心演算函數
def get_institutional_flow(df):
    recent = df.tail(5)
    score = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: score += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: score -= 1
    return "🔥 強勢買入" if score >= 2 else "💧 持續流出" if score <= -2 else "☁️ 盤整觀望"

def get_volume_support(df):
    try:
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

def get_google_news(name):
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={quote(name + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        return [e.title for e in feed.entries[:3]]
    except: return []

# 5. 【核心】Gemini AI 診斷引擎
def ask_gemini_analysis(stock_data, news, market_context):
    prompt = f"""
    你是一位專業的股市量化交易分析師。請根據以下數據，提供一段 120 字以內的精準市場診斷。
    
    【個股數據】: {stock_data}
    【近期新聞】: {news}
    【大盤環境】: {market_context}
    
    分析要求：
    1. 直接給出結論（多頭/空頭/觀望）。
    2. 結合新聞與籌碼流向給出點評。
    3. 給出具體的風控建議（例如：破底停損或壓力調節）。
    不要廢話，口吻要專業。
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "⚠️ Gemini AI 診斷暫時不可用，請檢查網路或 API 額度。"

# 6. 主程式迴圈
tickers = {
    "2330.TW": {"name": "台積電", "adr": "TSM"},
    "NVDA": {"name": "輝達", "adr": None},
    "TSM": {"name": "台積電ADR", "adr": None},
    "MU": {"name": "美光", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"},
    "2344.TW": {"name": "華邦電", "adr": None},
    "3481.TW": {"name": "群創", "adr": None}
}

# 抓取全球環境數據
vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
sox = yf.Ticker("^SOX").history(period="1mo")
sox_status = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
market_context = f"VIX: {vix:.1f}, 費半狀態: {sox_status}"

st.title("🖥️ 全球量化戰鬥系統 V8.2 - Gemini AI 診斷版")
timer_placeholder = st.empty()

for ticker, info in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
        rsi = (df['Close'].diff().where(df['Close'].diff()>0, 0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean() * 100).iloc[-1]
        
        # 數據標籤與新聞
        chip = get_institutional_flow(df)
        news_list = get_google_news(info['name'])
        
        # 準備 AI 輸入
        raw_data = {
            "價格": round(close, 2), "RSI": round(rsi, 1), 
            "籌碼流向": chip, "量能比": round(vol_ratio, 1)
        }
        
        # 調用 AI 診斷
        with st.spinner(f'AI 正在診斷 {info["name"]}...'):
            ai_diag = ask_gemini_analysis(raw_data, news_list, market_context)
        
        # UI 渲染
        style = "✅" if (sox_status=="📈 BULL" and chip=="🔥 強勢買入") else ("☢️" if sox_status=="📉 BEAR" else "🔎")
        
        st.markdown(f"""
        <div class="status-card {style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.6em; font-weight: bold;">{style} {info['name']} ({ticker})</span>
                    <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${close:.2f}</span>
                </div>
                <div style="text-align: right;">
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                    <span class="metric-tag">籌碼: {chip}</span>
                    <span class="metric-tag">PE: {stock.info.get('forwardPE', 'N/A')}</span>
                </div>
            </div>
            
            <div class="ai-diag-box">
                <b>🤖 Gemini AI 市場綜合診斷：</b><br>{ai_diag}
            </div>

            <div style="display: flex; gap: 20px;">
                <div style="flex: 2;">
                    <div class="defense-box">
                        ⚙️ <b>風控與成本模擬：</b><br>
                        波段高點預警: {df['High'].tail(5).max()*0.97:.2f} | 
                        ATR 演算底線: {close - (2.5 * (df['High']-df['Low']).rolling(14).mean().iloc[-1]):.2f} <br>
                        密集換手區: {get_volume_support(df):.2f} | 成交量比: {vol_ratio:.1f}x
                    </div>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 12px; border-radius: 10px; border: 1px solid #d9d9d9;">
                    <b>🧪 邏輯回測參數：</b>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 5px;">
                        <div><span class="price-label">🟢 觀察點</span><br><span class="price-value" style="color:#389e0d;">{ma20 - 1.2*std20:.2f}</span></div>
                        <div><span class="price-label">🎯 壓力位</span><br><span class="price-value" style="color:#cf1322;">{ma20 + 2*std20:.2f}</span></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"解析 {ticker} 出錯: {e}")

# 自動刷新計時
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後更新數據與 AI 診斷")
    time.sleep(1)
st.rerun()
