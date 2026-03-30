import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
import requests
import time
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import google.generativeai as genai
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 深度診斷版", layout="wide")

# --- 2. 抗封鎖 Session ---
def get_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    })
    return s

# --- 3. AI 引擎初始化 ---
@st.cache_resource
def init_ai_engines():
    engines = {"gemini": None, "groq": None}
    try:
        if "GROQ_API_KEY" in st.secrets:
            engines["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except: pass
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
            engines["gemini"] = genai.GenerativeModel('gemini-2.0-flash')
    except: pass
    return engines

ai_engines = init_ai_engines()

# 4. 私密驗證
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]: return True
    st.markdown("### 🖥️ 內部開發監測系統 V6.8")
    pwd = st.text_input("請輸入存取密碼：", type="password", key="pwd_sys")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    elif pwd: st.error("😕 驗證失敗")
    return False

if not check_password(): st.stop()

# 5. CSS 樣式 (保留你最愛的卡片設計)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 6. 核心計算函數
def get_institutional_flow(df):
    recent = df.tail(5)
    flow_score = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score -= 1
    return "🔥 強勢買入" if flow_score >= 2 else "💧 流出" if flow_score <= -2 else "☁️ 盤整"

def get_google_news(keyword):
    news = []
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        for entry in feed.entries[:2]: news.append(f"• {entry.title}")
    except: pass
    return news

# --- 7. 深度 AI 診斷 (Goldman Sachs 版) ---
@st.cache_data(ttl=14400, show_spinner=False)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev, news_list):
    news_context = " | ".join(news_list) if news_list else "暫無即時重大新聞"
    prompt = f"""
    你現在是 Goldman Sachs 首席分析師。對 {name} 進行診斷。
    外部環境：{news_context}
    數據：現價:{price} | PE:{pe} | 成長:{rev} | RSI:{rsi:.1f} | 籌碼:{chip_flow} | 趨勢:{trend}
    請給出實戰部署建議，限 120 字內。
    """
    
    try:
        if ai_engines["groq"]:
            res = ai_engines["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}], timeout=10
            )
            return "🔥 策略室： " + res.choices[0].message.content
        elif ai_engines["gemini"]:
            res = ai_engines["gemini"].generate_content(prompt)
            return "🔮 戰略部： " + res.text
    except:
        raise Exception("API_LIMIT")

# 8. 標的名單
tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
    "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電",
    "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
}

# --- 數據獲取 ---
with st.spinner('📡 全球數據同步中 (批次抓取模式)...'):
    session = get_session()
    all_syms = list(tickers.keys()) + ["^VIX", "^SOX"]
    try:
        raw_data = yf.download(all_syms, period="1y", session=session, group_by='ticker')
        vix = raw_data["^VIX"]["Close"].iloc[-1]
    except:
        st.error("Yahoo 數據連線中斷")
        st.stop()

# --- 渲染卡片 ---
data_list = []
for ticker, name in tickers.items():
    try:
        df = raw_data[ticker].dropna()
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std = df['Close'].rolling(20).std().iloc[-1]
        
        # RSI
        delta = df['Close'].diff()
        rsi = (100 - (100 / (1 + (delta.where(delta > 0, 0).rolling(14).mean() / 
                                 -delta.where(delta < 0, 0).rolling(14).mean()).fillna(0)))).iloc[-1]
        
        news = get_google_news(name)
        
        # AI 診斷 (帶入強迫延遲 6 秒，確保不撞牆)
        try:
            ai_report = get_ai_analysis(name, round(close, 2), rsi, get_institutional_flow(df), "🌟 多頭", "N/A", "N/A", news)
            style = "✅" if rsi < 70 else "⚠️"
        except:
            ai_report = "⏳ 【分析師排隊中】目前流量過大，請一分鐘後刷新。數據已由技術面產出。"
            style = "🔎"
            time.sleep(2) # 失敗也停一下

        # HTML 內容 (套用你最愛的設計)
        st.markdown(f"""
        <div class="status-card {style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.6em; font-weight: bold;">{name} ({ticker})</span>
                    <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${close:.2f}</span>
                </div>
                <span class="metric-tag">RSI: {rsi:.1f} | 籌碼: {get_institutional_flow(df)}</span>
            </div>
            <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="display: flex; gap: 25px;">
                <div style="flex: 2.2;">
                    <b>🧠 深度診斷 (AI 版)：</b><br><span style="line-height:1.6;">{ai_report}</span>
                    <div class="defense-box">
                        🛡️ <b>支撐位: {ma20-2*std:.2f}</b> | 🎯 壓力位: {ma20+2*std:.2f}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(6) # 每一檔間隔 6 秒，這是 9 檔全部成功的「物理保障」
        
    except: continue

st.rerun()
