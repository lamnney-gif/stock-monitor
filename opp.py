import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time
import random
from groq import Groq

# 1. 頁面配置 (1600px 寬版)
st.set_page_config(page_title="Beta Lab AI Ultimate - 物理級還原完整版", layout="wide")

# --- 2. AI 核心啟動 ---
@st.cache_resource
def init_ai_engines():
    engines = {"groq": None}
    try:
        # 確保 Secrets 存在，否則不崩潰
        if "GROQ_API_KEY" in st.secrets:
            engines["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except:
        pass
    return engines

ai_engines = init_ai_engines()

# 2. 私密存取驗證
def check_password():
    if st.session_state.get("password_correct", False):
        return True
    st.markdown("### 🖥️ 內部開發監測系統 V6.8")
    pwd = st.text_input("請輸入存取密碼：", type="password", key="password_input")
    if pwd:
        if pwd == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("😕 驗證失敗")
            return False
    return False

if not check_password():
    st.stop()

# 3. CSS 樣式 (物理級還原，一個 class 都不准漏)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    .mobile-warning { 
        background-color: #fff2f0; border: 2px solid #ffccc7; padding: 15px; 
        border-radius: 10px; margin-bottom: 20px; border-left: 10px solid #ff4d4f;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 側邊欄：法律防護與 RSS (一字不漏) ---
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px; font-size: 0.85em;">
    <b>【免責聲明】</b><br>
    1. 本網頁為個人 Python 量化模型開發測試用途，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、診斷報告皆為程式演算法之實驗產出，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。任何閱覽者若據此進行交易，盈虧請自負。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差。
</div>
""", unsafe_allow_html=True)

# RSS 新聞功能
def get_stock_news(q):
    try:
        url = f"https://news.google.com/rss/search?q={quote(q)}+stock&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        return feed.entries[:3]
    except: return []

# 主頁警告
st.markdown("""
<div class="mobile-warning">
    <b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境 (Beta Lab)</b><br>
    <p style="font-size: 0.9em; color: #595959; margin-top: 5px;">本站僅供個人程式邏輯測試，所有數據與診斷均為<b>自動化實驗產出，非投資建議</b>。</p>
</div>
""", unsafe_allow_html=True)

# 4. 核心演算
def get_institutional_flow(df):
    recent = df.tail(5)
    flow_score = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score -= 1
    return "🔥 強勢買入" if flow_score >= 2 else "💧 持續流出" if flow_score <= -2 else "☁️ 盤整觀望"

def get_volume_support(df):
    try:
        rdf = df.tail(60)
        v_hist = np.histogram(rdf['Close'], bins=10, weights=rdf['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

# --- 5. AI 權重診斷 (高盛魂 + Groq) ---
@st.cache_data(ttl=3600)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev, bias, slope):
    if not ai_engines["groq"]: return "❌ Groq 引擎離線"
    fallback = f"數據提示：RSI {rsi:.1f}，籌碼{chip_flow}，趨勢{trend}。"
    prompt = f"[高盛策略師] 標的:{name}, 價:{price}, RSI:{rsi:.1f}, 籌碼:{chip_flow}, 趨勢:{trend}, PE:{pe}, 營收:{rev}, 乖離:{bias}%, 斜率:{slope}%. 一句話結論(50字內)。"
    try:
        time.sleep(1.0) # 緩解 API 併發壓力
        res = ai_engines["groq"].chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return "🦅 首席策略： " + res.choices[0].message.content.strip()[:90]
    except: return f"📊 數據診斷：{fallback}"

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
    ai_report = get_ai_analysis(name, d['price'], d['rsi'], d['chip_flow'], d['trend'], d['pe'], d['rev'], d['bias'], d['slope'])
    style = "✅" if score >= 65 else "⚠️" if score >= 45 else "☢️"
    return score, ai_report, style

# 6. 主數據流 (物理還原)
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
data_list = []

col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ Beta Lab AI Ultimate - 穩定修正版")
with col_r: timer_placeholder = st.empty()

# --- 核心抓取邏輯 (增加防崩潰) ---
with st.spinner('同步全球數據中...'):
    # VIX 防爆
    try:
        v_df = yf.Ticker("^VIX").history(period="5d")
        vix = round(v_df['Close'].iloc[-1], 2) if not v_df.empty else 20.0
    except: vix = 20.0

    # SOX 防爆
    try:
        s_df = yf.Ticker("^SOX").history(period="1mo")
        sox_status = "📈 BULL" if (not s_df.empty and s_df['Close'].iloc[-1] > s_df['Close'].mean()) else "📉 BEAR"
    except: sox_status = "📉 BEAR"

    # 10Y Yield 防爆
    try:
        u_df = yf.Ticker("^TNX").history(period="1d")
        us10y = u_df['Close'].iloc[-1] if not u_df.empty else 4.0
    except: us10y = 4.0

    for ticker, name in tickers.items():
        try:
            time.sleep(1.0) # 強制延遲，防止 Yahoo 封鎖 IP
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk")
            if df.empty: continue
            
            s_info = stock.info
            close_val = df['Close'].iloc[-1]
            ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / (df['Volume'].iloc[-6:-1].mean() + 1e-9)
            
            pe_val = f"{s_info.get('trailingPE', 0):.1f}"
            rev_growth = f"{(s_info.get('revenueGrowth', 0) or 0) * 100:.1f}%"
            inst_hold = f"{s_info.get('heldPercentInstitutions', 0)*100:.1f}%"
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/(loss + 1e-9)))).iloc[-1]
            atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
            
            chip_flow = get_institutional_flow(df)
            ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
            trend_label = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
            bias = round(((close_val - ma20) / ma20) * 100, 2)
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100

            chip_floor = get_volume_support(df)
            stop_line = df['High'].tail(5).max() * 0.97
            dynamic_stop = close_val - (2.5 * atr_val)

            ai_score, ai_diag, ai_style = calculate_ai_confidence(
                {'trend': trend_label, 'chip_flow': chip_flow, 'price': close_val, 'rsi': rsi_val, 'pe': pe_val, 'rev': rev_growth, 'bias': bias, 'slope': round(slope,2)},
                vix, sox_status, "UP" if close_val > df_w['Close'].mean() else "DOWN", name
            )

            data_list.append({
                "style": ai_style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "ai_diag": ai_diag, "rsi": round(rsi_val, 1), "chip": chip_flow, "trend": trend_label,
                "buy": round(ma20 - 1.2 * std20, 2), "sell": round(ma20 + 2 * std20, 2),
                "stop": round(dynamic_stop, 2), "stop_line": round(stop_line, 2), "floor": round(chip_floor, 2),
                "vol": round(vol_ratio, 1), "slope": round(slope, 2), "inst": inst_hold, "pe": pe_val, "rev": rev_growth,
                "sup": round(ma20 - 2 * std20, 2), "bias": bias
            })
        except: continue

# --- 7. UI 渲染 (一字不刪) ---
st.sidebar.markdown(f"📊 **全球指標**\n- VIX: {vix:.1f}\n- 10Y Yield: {us10y:.2f}%\n- SOX: {sox_status}")

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 1.6em; font-weight: bold;">{d['name']}</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span></div>
            <span class="metric-tag">RSI: {d['rsi']} | 籌碼: {d['chip']} | 量比: {d['vol']}x</span>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            趨勢: {d['trend']} | <b>本益比: {d['pe']}</b> | <b>營收成長: {d['rev']}</b> | 乖離率: {d['bias']}% | 機構: {d['inst']}
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🧠 智權診斷 (機構核心)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['ai_diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控模擬：</b> 
                    <span style="color:#1890ff;">營利防守: {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">ATR地板: {d['stop']}</span> <br>
                    <b>換手支撐區: {d['floor']}</b> | 統計支撐: {d['sup']} | 斜率: {d['slope']}%
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 交易參考：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 買點</span><br><span class="price-value" style="color:#389e0d;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 壓力</span><br><span class="price-value" style="color:#cf1322;">{d['sell']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新")
    time.sleep(1)
st.rerun()
