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
st.set_page_config(page_title="Beta Lab AI Ultimate - Groq 完整對齊版", layout="wide")

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

# 3. CSS 樣式 (絕對不漏字還原)
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

# --- 側邊欄與法律聲明 (完全還原) ---
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px; font-size: 0.85em;">
    <b>【免責聲明】</b><br>
    1. 本網頁為個人 Python 量化模型開發測試用途，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、診斷報告皆為程式演算法之實驗產出，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。任何閱覽者若據此進行交易，盈虧請自負，本站開發者不承擔任何法律責任。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差，請以各交易所官方報價為準。
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mobile-warning">
    <b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境 (Beta Lab)</b><br>
    <p style="font-size: 0.9em; color: #595959; margin-top: 5px; margin-bottom: 0;">
        本站僅供個人程式邏輯測試，所有數據與診斷均為<b>自動化實驗產出，非投資建議</b>。
        閱覽者據此操作之<b>盈虧請自行承擔</b>。詳細條款請參閱左側選單。
    </p>
</div>
""", unsafe_allow_html=True)

# 4. 核心演算函數 (還原所有複雜邏輯)
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
        vh = np.histogram(rdf['Close'], bins=10, weights=rdf['Volume'])
        return (vh[1][np.argmax(vh[0])] + vh[1][np.argmax(vh[0])+1]) / 2
    except: return 0

# --- 5. AI 權重診斷腦 (Groq 唯一核心 / 強化請求延遲防止漏跑) ---
@st.cache_data(ttl=14400)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev, bias):
    if not ai_engines["groq"]: return "❌ Groq 離線"
    
    # 建立備援建議，防止 Groq API 頻率限制 (Rate Limit) 導致空白
    fallback = f"指標提示：RSI {rsi:.1f}，籌碼{chip_flow}，趨勢{trend}。請守住 MA20 支撐。"
    
    prompt = f"標的:{name},價:{price},RSI:{rsi:.1f},籌碼:{chip_flow},趨勢:{trend},PE:{pe},營收:{rev},乖離:{bias}%。請給出『極簡一句話』部署建議。禁廢話，限50字。"
    try:
        # 強制加入微小延遲，防止 Groq 連續請求爆炸
        time.sleep(1.2)
        completion = ai_engines["groq"].chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            timeout=15
        )
        return "🔥 策略室： " + completion.choices[0].message.content.strip()[:85]
    except: 
        return f"📊 數據診斷：{fallback}"

def calculate_ai_confidence(d, vix, sox_s, week_t, name):
    score = 0
    if sox_s == "📈 BULL": score += 20
    if vix < 20: score += 20
    elif vix > 28: score -= 30
    else: score += 10
    if d['trend'] == "🌟 多頭排列": score += 15
    if week_t == "UP": score += 15
    if d['chip_flow'] == "🔥 強勢買入": score += 15
    if d['rsi'] > 75: score -= 20

    ai_report = get_ai_analysis(name, d['price'], d['rsi'], d['chip_flow'], d['trend'], d['pe'], d['rev'], d['bias'])
    
    if score >= 85: return score, f"✅ 【強力進攻】{ai_report}", "✅"
    elif score >= 65: return score, f"🔎 【分批佈局】{ai_report}", "✅"
    elif score >= 45: return score, f"⚠️ 【觀望等待】{ai_report}", "⚠️"
    else: return score, f"☢️ 【全面避險】{ai_report}", "☢️"

# 6. 主頁面與數據清單
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
data_list = []

col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ Beta Lab AI - 全維度數據對齊 (Groq)")
with col_r: timer_placeholder = st.empty()

with st.spinner('清洗全量數據並進行 Groq 隊列運算...'):
    vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_s = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
    us10y = yf.Ticker("^TNX").history(period="1d")['Close'].iloc[-1]

    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk")
            if df.empty: continue
            
            try: s_info = stock.info
            except: s_info = {}

            close = df['Close'].iloc[-1]
            ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / (df['Volume'].iloc[-6:-1].mean() + 1e-9)
            
            # 這些變數一個都沒少
            pe_val = f"{s_info.get('trailingPE', 0):.1f}"
            rev_growth = f"{(s_info.get('revenueGrowth', 0) or 0) * 100:.1f}%"
            inst_hold = f"{s_info.get('heldPercentInstitutions', 0)*100:.1f}%"
            
            delta = df['Close'].diff()
            g = delta.where(delta > 0, 0).rolling(14).mean()
            l = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi = (100 - (100 / (1 + g/(l + 1e-9)))).iloc[-1]
            atr = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
            
            chip = get_institutional_flow(df)
            ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
            trend = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
            bias = round(((close - ma20) / ma20) * 100, 2)
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close) * 100

            score, diag, style = calculate_ai_confidence(
                {'trend': trend, 'chip_flow': chip, 'price': close, 'rsi': rsi, 'pe': pe_val, 'rev': rev_growth, 'bias': bias},
                vix, sox_s, "UP" if close > df_w['Close'].mean() else "DOWN", name
            )

            data_list.append({
                "style": style, "name": f"{name} ({ticker})", "price": round(close, 2),
                "ai_diag": diag, "rsi": round(rsi, 1), "chip": chip, "trend": trend, "bias": bias,
                "buy": round(ma20 - 1.2 * std20, 2), "sell": round(ma20 + 2 * std20, 2),
                "stop": round(close - (2.5 * atr), 2), "stop_line": round(df['High'].tail(5).max() * 0.97, 2),
                "floor": round(get_volume_support(df), 2), "vol": round(vol_ratio, 1), "slope": round(slope, 2),
                "inst": inst_hold, "pe": pe_val, "rev": rev_growth, "sup": round(ma20 - 2 * std20, 2)
            })
        except: continue

# --- 7. UI 渲染 (完全還原) ---
st.sidebar.markdown(f"📊 **全球風險監控**\n- VIX: {vix:.1f}\n- 10Y Yield: {us10y:.2f}%\n- SOX: {sox_s}")

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 1.6em; font-weight: bold;">{d['name']}</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span></div>
            <span class="metric-tag">RSI: {d['rsi']} | 籌碼: {d['chip']} | 成交量比: {d['vol']}x</span>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            趨勢: {d['trend']} | <b>本益比: {d['pe']}</b> | <b>營收成長: {d['rev']}</b> | 乖離率: {d['bias']}% | 機構: {d['inst']}
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🧠 智權診斷 (Groq 全方位分析)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['ai_diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控與成本模擬：</b> 
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
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新數據")
    time.sleep(1)
st.rerun()
