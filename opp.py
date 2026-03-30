import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import google.generativeai as genai
import time
from groq import Groq

# 1. 頁面配置 (1600px 寬版)
st.set_page_config(page_title="Beta Lab AI Ultimate - 數據全量版", layout="wide")

# --- 2. AI 核心啟動 (必須放在最前面) ---
@st.cache_resource
def init_ai_engines():
    engines = {"gemini": None, "groq": None}
    try:
        if "GROQ_API_KEY" in st.secrets:
            engines["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except:
        pass
    try:
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
            engines["gemini"] = genai.GenerativeModel('gemini-2.0-flash')
    except:
        pass
    return engines

ai_engines = init_ai_engines()

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

st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px;">
    <p style="font-size: 0.85em; color: #333; line-height: 1.6;">
    <b>【免責聲明】</b><br>
    1. 本網頁為個人 <b>Python 量化模型開發測試用途</b>，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、診斷報告皆為<b>程式演算法之實驗產出</b>，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。<b>任何閱覽者若據此進行交易，盈虧請自負</b>，本站開發者不承擔任何法律責任。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差，請以各交易所官方報價為準。
    </p>
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
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev):
    
    prompt = f"""
    你現在是(Goldman Sachs)全球策略首席分析師。請針對 {name} 進行診斷。

    【市場結構】
    請聚焦資金流、產業趨勢與估值邏輯。

    【個股狀態】
    現價:{price} | PE:{pe} | 成長:{rev} | RSI:{rsi:.1f} | 籌碼:{chip_flow} | 趨勢:{trend}

    【操作建議】
    判斷是否高估或低估，給出實戰策略（加碼/觀望/減碼）。
    限制130字內。
    """
    
    if ai_engines["groq"]:
        try:
            completion = ai_engines["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "你是一位洞察地緣政治與資本市場連動關係的資深策略家。"},
                          {"role": "user", "content": prompt}]
            )
            return "🔥 策略室： " + completion.choices[0].message.content
        except: pass
        
    if ai_engines["gemini"]:
        try:
            res = ai_engines["gemini"].generate_content(prompt)
            return "🔮 戰略部： " + res.text
        except: return "⚠️ 分析師會議中 (API 忙碌)"
    return "❌ 分析引擎未啟動"

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

    ai_report = get_ai_analysis(name, d['price'], d['rsi'], d['chip_flow'], d['trend'], d['pe'], d['rev'])
    
    if score >= 85: return score, f"✅ 【強力進攻】{ai_report}", "✅"
    elif score >= 65: return score, f"🔎 【分批佈局】{ai_report}", "✅"
    elif score >= 45: return score, f"⚠️ 【觀望等待】{ai_report}", "⚠️"
    else: return score, f"☢️ 【全面避險】{ai_report}", "☢️"

col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 測試 全數據 AI 版")
with col_r: timer_placeholder = st.empty()

tickers = {
    "2330.TW": {"name": "台積電", "adr": "TSM"}, "NVDA": {"name": "輝達", "adr": None},
    "MU": {"name": "美光", "adr": None}, "000660.KS": {"name": "海力士", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"}, "6770.TW": {"name": "力積電", "adr": None},
    "2344.TW": {"name": "華邦電", "adr": None}, "3481.TW": {"name": "群創", "adr": None}, "1303.TW": {"name": "南亞", "adr": None}
}

data_list = []

with st.spinner('同步數據與 AI 運算中...'):
    vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_status = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
    us10y = yf.Ticker("^TNX").history(period="5d")['Close'].iloc[-1]

    for ticker, info in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            s_info = stock.info
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            pe_val = s_info.get('trailingPE', 0)
            rev_growth = (s_info.get('revenueGrowth', 0) or 0) * 100
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
            atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
            
            chip_flow = get_institutional_flow(df)
            ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
            trend_label = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
            bias = ((close_val - ma20) / ma20) * 100
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100

            chip_floor = get_volume_support(df)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
            suggested_buy = ma20 - 1.2 * std20
            dynamic_stop = close_val - (2.5 * atr_val)

            pe_str = f"{pe_val:.1f}" if pe_val else "N/A"
            rev_str = f"{rev_growth:.1f}%"
            ai_score, ai_diag, ai_style = calculate_ai_confidence(
                {'trend': trend_label, 'chip_flow': chip_flow, 'price': close_val, 'rsi': rsi_val, 'pe': pe_str, 'rev': rev_str},
                vix, sox_status, "UP" if close_val > df_w['Close'].mean() else "DOWN", info['name']
            )

            data_list.append({
                "style": ai_style, "icon": ai_style, "name": f"{info['name']} ({ticker})", "price": round(close_val, 2),
                "ai_diag": ai_diag, "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2), "pe": pe_str, "rev": rev_str,
                "stop": round(dynamic_stop, 2), "stop_line": round(stop_profit_line, 2), "chip_floor": round(chip_floor, 2),
                "rsi": round(rsi_val, 1), "vol": round(vol_ratio, 1), "slope": round(slope, 2),
                "bias": round(bias, 2), "sup": round(tech_sup, 2), "pre": round(tech_pre, 2),
                "inst": f"{s_info.get('heldPercentInstitutions', 0)*100:.1f}%",
                "chip_flow": chip_flow, "trend": trend_label
            })
        except Exception as e:
            st.warning(f"跳過 {ticker}: {e}")

st.sidebar.markdown(f"📊 **全球風險監控**\n- VIX: {vix:.1f}\n- 10Y Yield: {us10y:.2f}%\n- SOX: {sox_status}")

for d in data_list:
    st.markdown(f"""...""", unsafe_allow_html=True)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新數據 (AI 診斷每4小時更新)")
    time.sleep(1)
st.rerun()
