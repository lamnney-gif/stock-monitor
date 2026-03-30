import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
import time
from groq import Groq

# 1. 頁面配置 (1600px 寬版)
st.set_page_config(page_title="Beta Lab AI Ultimate - 數據全量版", layout="wide")

# --- 2. AI 核心啟動 (優化錯誤處理) ---
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

# 2. 修改後的私密存取驗證
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

# 3. CSS 樣式
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

# --- 側邊欄：法律防護區 ---
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

# --- 主頁面置頂警告 ---
st.markdown("""
<div class="mobile-warning">
    <b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境 (Beta Lab)</b><br>
    <p style="font-size: 0.9em; color: #595959; margin-top: 5px; margin-bottom: 0;">
    本站僅供個人程式邏輯測試，所有數據與診斷均為<b>自動化實驗產出，非投資建議</b>。
    閱覽者據此操作之<b>盈虧請自行承擔</b>。詳細條款請參閱左側選單。
    </p>
</div>
""", unsafe_allow_html=True)

# 4. 核心演算函數
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

# --- 5. AI 權重診斷腦 ---

@st.cache_data(ttl=14400)
def get_ai_analysis(name, price, rsi, chip_flow, trend, pe, rev):
    prompt = f"分析 {name}: 現價 {price}, RSI {rsi:.1f}, 籌碼 {chip_flow}, 趨勢 {trend}, PE {pe}, 成長 {rev}。130字內給實戰建議。"
    
    if ai_engines["groq"]:
        try:
            completion = ai_engines["groq"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "你是一位專業資深策略分析師。"},
                          {"role": "user", "content": prompt}]
            )
            return "🔥 策略室： " + completion.choices[0].message.content
        except: 
            return "☕ AI 策略師休假中 (量化指標正常運作)"
    return "💡 請確認 API KEY 設定"

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
    
    style = "✅" if score >= 65 else "⚠️" if score >= 45 else "☢️"
    diag_label = "【強力進攻】" if score >= 85 else "【分批佈局】" if score >= 65 else "【觀望等待】" if score >= 45 else "【全面避險】"
    
    return score, f"{style} {diag_label} {ai_report}", style

# 6. 主頁面與清單
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 測試 全數據 AI 版")
with col_r: timer_placeholder = st.empty()

tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
    "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電",
    "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
}

data_list = []

with st.spinner('同步數據與 AI 運算中...'):
    try:
        vix_df = yf.Ticker("^VIX").history(period="5d")
        vix = vix_df['Close'].iloc[-1] if not vix_df.empty else 20.0
        sox = yf.Ticker("^SOX").history(period="1mo")
        sox_status = "📈 BULL" if (not sox.empty and sox['Close'].iloc[-1] > sox['Close'].mean()) else "📉 BEAR"
        us10y_df = yf.Ticker("^TNX").history(period="5d")
        us10y = us10y_df['Close'].iloc[-1] if not us10y_df.empty else 4.0
    except:
        vix, sox_status, us10y = 20.0, "☁️ N/A", 4.0

    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty or len(df) < 20: continue
            
            df_w = stock.history(period="2y", interval="1wk")
            s_info = stock.info
            
            close_val = df['Close'].iloc[-1]
            ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean() if not df['Volume'].iloc[-6:-1].empty else 1.0
            
            pe_val = s_info.get('trailingPE', 0)
            rev_growth = (s_info.get('revenueGrowth', 0) or 0) * 100
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1] if not loss.iloc[-1] == 0 else 50
            atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
            
            chip_flow = get_institutional_flow(df)
            ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
            trend_label = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
            bias = ((close_val - ma20) / ma20) * 100
            
            chip_floor = get_volume_support(df)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
            suggested_buy = ma20 - 1.2 * std20
            dynamic_stop = close_val - (2.5 * atr_val)

            pe_str = f"{pe_val:.1f}" if pe_val else "N/A"
            rev_str = f"{rev_growth:.1f}%"
            ai_score, ai_diag, ai_style = calculate_ai_confidence(
                {'trend': trend_label, 'chip_flow': chip_flow, 'price': close_val, 'rsi': rsi_val, 'pe': pe_str, 'rev': rev_str},
                vix, sox_status, "UP" if (not df_w.empty and close_val > df_w['Close'].mean()) else "DOWN", name
            )

            data_list.append({
                "style": ai_style, "icon": ai_style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "ai_diag": ai_diag, "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2), "pe": pe_str, "rev": rev_str,
                "stop": round(dynamic_stop, 2), "stop_line": round(stop_profit_line, 2), "chip_floor": round(chip_floor, 2),
                "rsi": round(rsi_val, 1), "vol": round(vol_ratio, 1), "bias": round(bias, 2), "sup": round(tech_sup, 2), "pre": round(tech_pre, 2),
                "inst": f"{s_info.get('heldPercentInstitutions', 0)*100:.1f}%", "chip_flow": chip_flow, "trend": trend_label
            })
            time.sleep(0.3) # 降低 Yahoo API 壓力
        except:
            continue

# --- UI 渲染 ---
st.sidebar.markdown(f"📊 **全球風險監控**\n- VIX: {vix:.1f}\n- 10Y Yield: {us10y:.2f}%\n- SOX: {sox_status}")

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span></div>
            <span class="metric-tag">RSI: {d['rsi']} | 籌碼: {d['chip_flow']} | 成交量比: {d['vol']}x</span>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">趨勢: {d['trend']} | 本益比: {d['pe']} | 營收成長: {d['rev']} | 乖離率: {d['bias']}% | 機構: {d['inst']}</div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🧠 智權診斷 (量化版)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['ai_diag']}</span>
                <div class="defense-box">⚙️ <b>風控模擬：</b> 營利防守: {d['stop_line']} | <span style="color:#cf1322;">ATR底線: {d['stop']}</span> | 密集換手區: {d['chip_floor']}</div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 買點</span><br><span class="price-value" style="color:#389e0d;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 壓力</span><br><span class="price-value" style="color:#cf1322;">{d['sell']}</span></div>
                    <div><span class="price-label">📉 支撐</span><br><span class="price-value">{d['sup']}</span></div>
                    <div><span class="price-label">📈 預期</span><br><span class="price-value">{d['pre']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新")
    time.sleep(1)
st.rerun()
