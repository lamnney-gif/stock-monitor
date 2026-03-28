import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import google.generativeai as genai
import time
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 數據全量版", layout="wide")

# --- 2. AI 核心啟動 (必須放在最前面) ---
@st.cache_resource
def init_ai_engines():
    engines = {"gemini": None, "groq": None}
    # 初始化 Groq
    try:
        if "GROQ_API_KEY" in st.secrets:
            engines["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except:
        pass
    # 初始化 Gemini
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
            engines["gemini"] = genai.GenerativeModel('gemini-2.0-flash')
    except:
        pass
    return engines

# 呼叫初始化
ai_engines = init_ai_engines()

# --- 3. 核心運算函數 ---

@st.cache_data(ttl=43200) # AI 診斷12小時更新一次
def get_ai_analysis(name, price, rsi, chip_flow, trend):
    prompt = f"你是量化分析師，分析{name}：現價{price}, RSI{rsi:.1f}, 籌碼{chip_flow}, 趨勢{trend}。請給出80字內精闢診斷。"
    
    # 優先嘗試 Groq (因為剛才測試最穩)
    if ai_engines["groq"]:
        try:
            completion = ai_engines["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            return " (Groq 備援) " + completion.choices[0].message.content
        except:
            pass
            
    # 備援嘗試 Gemini
    if ai_engines["gemini"]:
        try:
            res = ai_engines["gemini"].generate_content(prompt)
            return res.text
        except:
            return "⚠️ AI 引擎暫時忙碌中"
            
    return "❌ AI 未啟動 (請檢查 Secrets)"

def get_institutional_flow(df):
    recent = df.tail(5)
    flow_score = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score -= 1
    return "🔥 強勢買入" if flow_score >= 2 else "💧 持續流出" if flow_score <= -2 else "☁️ 盤整觀望"

def get_volume_support(df):
    try:
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

def get_google_news(keyword):
    news = []
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        for entry in feed.entries[:3]: news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

def calculate_ai_confidence(d, vix, sox_status, week_trend, name):
    score = 0
    if sox_status == "📈 BULL": score += 20
    if vix < 20: score += 20
    elif vix > 28: score -= 30
    else: score += 10
    if d['trend'] == "🌟 多頭排列": score += 15
    if week_trend == "UP": score += 15
    if d['chip_flow'] == "🔥 強勢買入": score += 15
    if d['rsi'] > 75: score -= 20

    ai_report = get_ai_analysis(name, d['price'], d['rsi'], d['chip_flow'], d['trend'])
    
    if score >= 85: return score, f"✅ 【強力進攻】{ai_report}", "✅"
    elif score >= 65: return score, f"🔎 【分批佈局】{ai_report}", "✅"
    elif score >= 45: return score, f"⚠️ 【觀望等待】{ai_report}", "⚠️"
    else: return score, f"☢️ 【全面避險】{ai_report}", "☢️"

# --- 4. 密碼驗證 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 內部開發監測系統 V6.8")
        pwd = st.text_input("請輸入存取密碼：", type="password")
        if pwd == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password(): st.stop()

# --- 5. CSS 樣式 ---
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨, .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 6. 數據抓取與渲染 ---
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 半導體戰情室 - Groq 極速版")
with col_r: timer_placeholder = st.empty()

tickers = {
    "2330.TW": {"name": "台積電"}, "NVDA": {"name": "輝達"},
    "MU": {"name": "美光"}, "2303.TW": {"name": "聯電"}, 
    "6770.TW": {"name": "力積電"}, "2344.TW": {"name": "華邦電"}
}

data_list, news_dict = [], {}

with st.spinner('同步數據中...'):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_status = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
    us10y = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]

    for ticker, info in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 技術指標
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
            
            chip_flow = get_institutional_flow(df)
            trend_label = "🌟 多頭排列" if close_val > ma20 else "🌀 趨勢不明"
            
            # AI 診斷 (帶入快取邏輯)
            ai_score, ai_diag, ai_style = calculate_ai_confidence(
                {'trend': trend_label, 'chip_flow': chip_flow, 'price': int(close_val), 'rsi': round(rsi_val, 0)},
                vix, sox_status, "UP", info['name']
            )

            data_list.append({
                "style": ai_style, "icon": ai_style, "name": info['name'], "price": round(close_val, 1),
                "ai_diag": ai_diag, "rsi": round(rsi_val, 1), "chip_flow": chip_flow, "trend": trend_label
            })
        except: continue

# 渲染卡片
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between;">
            <span style="font-size: 1.5em; font-weight: bold;">{d['icon']} {d['name']} (${d['price']})</span>
            <span class="metric-tag">RSI: {d['rsi']} | {d['chip_flow']}</span>
        </div>
        <div style="margin-top: 15px;">
            <b>🧠 AI 診斷：</b><br>{d['ai_diag']}
        </div>
    </div>
    """, unsafe_allow_html=True)

# 自動倒數
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新")
    time.sleep(1)
st.rerun()
