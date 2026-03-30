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
st.set_page_config(page_title="Beta Lab AI Ultimate - 防封鎖穩定版", layout="wide")

# --- 2. AI 核心啟動 ---
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

# 3. 驗證系統
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.markdown("### 🖥️ 內部開發監測系統 V6.8")
    pwd = st.text_input("請輸入存取密碼：", type="password", key="password_input")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    return False

if not check_password(): st.stop()

# 4. CSS 樣式 (維持原樣)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. 核心數據抓取 (關鍵：加入快取與延遲) ---

@st.cache_data(ttl=3600)  # 快取 1 小時，避免頻繁請求導致封鎖
def get_safe_stock_data(ticker):
    """ 安全抓取股票數據，包含防封鎖機制 """
    try:
        stock = yf.Ticker(ticker)
        # 抓取 1 年數據 (足夠計算 MA20, RSI, 週線)
        df = stock.history(period="1y")
        if df.empty: return None, None
        
        # 抓取基本面 (這是最容易被 Yahoo 封鎖的部分，獨立處理)
        s_info = {}
        try:
            # 隨機延遲，防止被偵測為爬蟲
            time.sleep(0.5) 
            s_info = stock.info
        except:
            pass # 即使 info 抓不到，也回傳空字典讓程式繼續跑
            
        return df, s_info
    except:
        return None, None

def get_google_news(keyword):
    news = []
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        for entry in feed.entries[:3]: news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

# --- 6. 診斷與計算邏輯 ---

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

@st.cache_data(ttl=14400)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev, news_list):
    news_context = " | ".join(news_list) if news_list else "暫無即時重大新聞"
    prompt = f"分析 {name} (現價:{price}, PE:{pe}, RSI:{rsi:.1f}, 籌碼:{chip_flow})。考慮新聞:{news_context}。語氣冷靜，130字內給實戰建議。"
    
    if ai_engines["gemini"]:
        try:
            res = ai_engines["gemini"].generate_content(prompt)
            return "🔮 戰略部： " + res.text
        except: return "⚠️ 分析師會議中 (API 忙碌)"
    return "❌ AI 引擎未啟動"

# --- 7. 主程式 UI ---
st.title("🖥️ Beta Lab AI - 全數據穩定版")

tickers = {
    "2330.TW": {"name": "台積電"}, "NVDA": {"name": "輝達"},
    "MU": {"name": "美光"}, "000660.KS": {"name": "海力士"},
    "2303.TW": {"name": "聯電"}, "6770.TW": {"name": "力積電"},
    "2344.TW": {"name": "華邦電"}, "3481.TW": {"name": "群創"}, "1303.TW": {"name": "南亞"}
}

data_list = []
news_dict = {}

with st.spinner('同步全球數據中 (加入防封鎖延遲)...'):
    # 基礎市場數據
    try:
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        sox = yf.Ticker("^SOX").history(period="1mo")
        sox_status = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
    except:
        vix, sox_status = 20.0, "📉 數據延遲"

    for ticker, info in tickers.items():
        # 抓取新聞
        current_news = get_google_news(info['name'])
        news_dict[info['name']] = current_news

        # 使用安全抓取函式 (快取化)
        df, s_info = get_safe_stock_data(ticker)
        
        # 關鍵：每檔股票抓取後強制休息，避免被 Yahoo 封鎖
        time.sleep(1.5)

        if df is None or df.empty:
            st.error(f"無法讀取 {ticker}，可能 Yahoo 伺服器拒絕連線。")
            continue

        # --- 技術指標計算 ---
        close_val = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        # RSI 計算
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
        
        # 其他數據
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
        chip_flow = get_institutional_flow(df)
        ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
        trend_label = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
        
        # 風控位
        tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
        suggested_buy = ma20 - 1.2 * std20
        chip_floor = get_volume_support(df)

        # AI 診斷
        pe_str = f"{s_info.get('trailingPE', 0):.1f}" if s_info.get('trailingPE') else "N/A"
        rev_str = f"{(s_info.get('revenueGrowth', 0) or 0)*100:.1f}%"
        
        ai_report = get_ai_analysis(info['name'], close_val, rsi_val, chip_flow, trend_label, pe_str, rev_str, current_news)

        data_list.append({
            "style": "✅" if rsi_val < 70 else "⚠️", 
            "name": f"{info['name']} ({ticker})", "price": round(close_val, 2),
            "ai_diag": ai_report, "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2),
            "rsi": round(rsi_val, 1), "chip_flow": chip_flow, "trend": trend_label,
            "pe": pe_str, "rev": rev_str, "sup": round(tech_sup, 2), "chip_floor": round(chip_floor, 2)
        })

# --- UI 渲染 ---
st.sidebar.markdown(f"📊 **全球監控**\n- VIX: {vix:.1f}\n- SOX: {sox_status}")
for name, news in news_dict.items():
    with st.sidebar.expander(f"📰 {name} 動態"):
        for n in news: st.markdown(n)

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between;">
            <div><span style="font-size: 1.6em; font-weight: bold;">{d['name']}</span>
            <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace;">${d['price']}</span></div>
            <span class="metric-tag">RSI: {d['rsi']} | {d['chip_flow']}</span>
        </div>
        <div style="margin: 10px 0; color: #666;">趨勢: {d['trend']} | PE: {d['pe']} | 成長: {d['rev']}</div>
        <hr>
        <div>
            <b>🧠 AI 策略診斷：</b><br>{d['ai_diag']}
            <div class="defense-box">
                📍 建議買點: <span style="color:green;">{d['buy']}</span> | 壓力位: <span style="color:red;">{d['sell']}</span> | 密集換手區: {d['chip_floor']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 倒數計時與自動刷新
st.info("💡 數據已快取。若要強制更新，請點擊右上角 Settings -> Clear Cache。")
time.sleep(300)
st.rerun()
