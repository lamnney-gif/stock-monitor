import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time
from groq import Groq

# 1. 頁面配置 (1600px 寬版)
st.set_page_config(page_title="Beta Lab AI Ultimate - Groq 數據全量版", layout="wide")

# --- 2. AI 核心啟動 (僅保留 Groq) ---
@st.cache_resource
def init_ai_engines():
    engines = {"groq": None}
    try:
        if "GROQ_API_KEY" in st.secrets:
            engines["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except:
        pass
    return engines

ai_engines = init_ai_engines()

# 2. 修改後的私密存取驗證 (加入防呆)
def check_password():
    if st.session_state.get("password_correct", False):
        return True
    st.markdown("### 🖥️ 內部開發監測系統 V6.8")
    pwd = st.text_input("請輸入存取密碼：", type="password", key="password_input")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    return False

if not check_password():
    st.stop()

# 3. CSS 樣式
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
    .mobile-warning { background-color: #fff2f0; border: 2px solid #ffccc7; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 10px solid #ff4d4f; }
    </style>
    """, unsafe_allow_html=True)

# --- 側邊欄：法律防護區 ---
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px;">
    <p style="font-size: 0.85em; color: #333; line-height: 1.6;">
    <b>【免責聲明】</b><br>
    1. 本網頁為個人 <b>Python 量化模型開發測試用途</b>。<br><br>
    2. 內文所載之所有價格皆為<b>程式演算法之實驗產出</b>，非屬投資建議。<br><br>
    3. 投資有風險，<b>盈虧請自負</b>。
    </p>
</div>
""", unsafe_allow_html=True)

# 4. 核心演算函數
def get_institutional_flow(df):
    try:
        recent = df.tail(5)
        flow_score = 0
        for i in range(1, len(recent)):
            if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score += 1
            if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score -= 1
        return "🔥 強勢買入" if flow_score >= 2 else "💧 持續流出" if flow_score <= -2 else "☁️ 盤整觀望"
    except: return "☁️ 數據缺失"

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

# --- 5. Groq 數據純化診斷腦 ---
@st.cache_data(ttl=14400)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev):
    prompt = f"""
    你是高盛首席策略師。針對 {name} 進行『純數據量化診斷』。
    數據：現價:{price} | PE:{pe} | 營收成長:{rev} | RSI:{rsi:.1f} | 籌碼流向:{chip_flow} | 趨勢形態:{trend}
    分析：1.背離或共振狀態 2.估值空間判斷 3.實戰部署（加碼、了結、觀望）。限制 120 字內，不要提到新聞。
    """
    if ai_engines["groq"]:
        try:
            res = ai_engines["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "你是一位量化數據家。"}, {"role": "user", "content": prompt}]
            )
            return "🔥 策略室(Groq)： " + res.choices[0].message.content
        except: return "⚠️ 分析暫停 (Groq 繁忙)"
    return "❌ 未啟動"

def calculate_ai_confidence(d, vix, sox_status, name):
    score = 0
    if sox_status == "📈 BULL": score += 20
    if vix < 20: score += 20
    elif vix > 28: score -= 30
    else: score += 10
    if d['trend'] == "🌟 多頭排列": score += 15
    if d['chip_flow'] == "🔥 強勢買入": score += 15
    if d['rsi'] > 75: score -= 20

    ai_report = get_ai_analysis(name, d['price'], d['rsi'], d['chip_flow'], d['trend'], d['pe'], d['rev'])
    
    if score >= 80: return f"✅ 【強力進攻】{ai_report}", "✅"
    elif score >= 60: return f"🔎 【分批佈局】{ai_report}", "✅"
    elif score >= 40: return f"⚠️ 【觀望等待】{ai_report}", "⚠️"
    else: return f"☢️ 【全面避險】{ai_report}", "☢️"

# 6. 主頁面
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 測試 全數據 AI 版")
with col_r: timer_placeholder = st.empty()

tickers = {
    "2330.TW": {"name": "台積電"}, "NVDA": {"name": "輝達"}, "MU": {"name": "美光"}, 
    "000660.KS": {"name": "海力士"}, "2303.TW": {"name": "聯電"}, "6770.TW": {"name": "力積電"},
    "2344.TW": {"name": "華邦電"}, "3481.TW": {"name": "群創"}, "1303.TW": {"name": "南亞"}
}

data_list, news_dict = [], {}

with st.spinner('同步數據運算中...'):
    try:
        vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
        sox = yf.Ticker("^SOX").history(period="1mo")
        sox_status = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
        us10y = yf.Ticker("^TNX").history(period="5d")['Close'].iloc[-1]
    except:
        vix, sox_status, us10y = 20, "☁️ UNKNOWN", 4.0

    for ticker, info in tickers.items():
        try:
            news_dict[info['name']] = get_google_news(info['name'])
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            s_info = stock.info
            close_val = df['Close'].iloc[-1]
            ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
            pe_str = f"{s_info.get('trailingPE', 0):.1f}" if s_info.get('trailingPE') else "N/A"
            rev_str = f"{(s_info.get('revenueGrowth', 0) or 0)*100:.1f}%"
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
            
            flow = get_institutional_flow(df)
            trend = "🌟 多頭排列" if df['Close'].rolling(5).mean().iloc[-1] > df['Close'].rolling(20).mean().iloc[-1] else "🌀 趨勢不明"
            
            ai_diag, ai_style = calculate_ai_confidence(
                {'trend': trend, 'chip_flow': flow, 'price': close_val, 'rsi': rsi_val, 'pe': pe_str, 'rev': rev_str},
                vix, sox_status, info['name']
            )

            data_list.append({
                "style": ai_style, "icon": ai_style, "name": f"{info['name']} ({ticker})", "price": round(close_val, 2),
                "ai_diag": ai_diag, "pe": pe_str, "rev": rev_str, "rsi": round(rsi_val, 1),
                "stop": round(close_val - (2.5 * (df['High']-df['Low']).rolling(14).mean().iloc[-1]), 2),
                "stop_line": round(df['High'].tail(5).max() * 0.97, 2), "chip_floor": round(get_volume_support(df), 2),
                "buy": round(ma20 - 1.2 * std20, 2), "sell": round(ma20 + 2 * std20, 2), "flow": flow, "trend": trend
            })
        except: continue

# --- UI 渲染 ---
st.sidebar.markdown(f"📊 **全球風險監控**\n- VIX: {vix:.1f}\n- 10Y Yield: {us10y:.2f}%\n- SOX: {sox_status}")
for name, news in news_dict.items():
    with st.sidebar.expander(f"📰 {name} 相關動態"):
        for n in news: st.markdown(n)

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
            <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span></div>
            <span class="metric-tag">RSI: {d['rsi']} | 籌碼: {d['flow']}</span>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            趨勢: {d['trend']} | <b>本益比: {d['pe']}</b> | <b>營收成長: {d['rev']}</b>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🧠 智權診斷 (Groq 數據版)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['ai_diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控與成本模擬：</b> 
                    <span style="color:#1890ff;">營利防守觀察點(上限): {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">ATR底線: {d['stop']}</span> <br>
                    <b>密集換手區間: {d['chip_floor']}</b>
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參數：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span style="font-size: 0.85em; color: #666;">🟢 觀察買點</span><br><span class="price-value" style="color:#389e0d;">{d['buy']}</span></div>
                    <div><span style="font-size: 0.85em; color: #666;">🎯 壓力位(上限)</span><br><span class="price-value" style="color:#cf1322;">{d['sell']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新")
    time.sleep(1)
st.rerun()
