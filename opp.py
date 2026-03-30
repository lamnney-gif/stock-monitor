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

# --- 2. AI 核心啟動 (移除 Gemini，專注 Groq) ---
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

# 3. CSS 樣式 (完整保留)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
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
    本網頁為個人 Python 量化開發測試，非投資建議。閱覽者據此操作盈虧自負。
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
        return "🔥 強勢買入" if flow_score >= 1 else "💧 持續流出" if flow_score <= -1 else "☁️ 盤整觀望"
    except: return "☁️ 盤整觀望"

def get_volume_support(df):
    try:
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

@st.cache_data(ttl=14400)
def get_ai_analysis(name, price, rsi, chip_flow, trend):
    if not ai_engines["groq"]: return "💡 AI 模組未啟動，請檢查 API Key"
    try:
        prompt = f"分析 {name}: 現價 {price}, RSI {rsi:.1f}, 籌碼 {chip_flow}, 趨勢 {trend}。請給專業佈署建議(100字內)。"
        completion = ai_engines["groq"].chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return "🔥 策略室： " + completion.choices[0].message.content
    except:
        return "☕ AI 暫時連線逾時，量化數據顯示中。"

# 6. 主頁面與清單
st.title("🖥️ Beta Lab AI Ultimate - 穩定全量版")
timer_placeholder = st.empty()

# 確保這 9 檔代碼一字不漏
tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
    "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電",
    "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
}

data_list = []

with st.spinner('同步市場數據中...'):
    for ticker, name in tickers.items():
        try:
            # 獲取股價歷史 (最穩定的 API)
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty or len(df) < 20: continue
            
            # 1. 價格與均線
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 2. 技術指標
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rsi_val = (100 - (100 / (1 + gain/loss))) if loss != 0 else 50
            
            chip_flow = get_institutional_flow(df)
            trend_label = "🌟 多頭排列" if close_val > ma20 else "💀 空頭排列"
            bias = ((close_val - ma20) / ma20) * 100
            
            # 3. AI 診斷 (帶入 try 防止 Groq 報錯導致整檔消失)
            ai_diag = get_ai_analysis(name, close_val, rsi_val, chip_flow, trend_label)
            
            # 4. 風控區
            chip_floor = get_volume_support(df)
            stop_line = close_val * 0.96  # 預設 4% 止損
            
            # 5. 樣式判斷
            style = "✅" if (close_val > ma20 and rsi_val < 70) else "☢️" if rsi_val > 75 else "⚠️"

            data_list.append({
                "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "rsi": round(rsi_val, 1), "chip_flow": chip_flow, "trend": trend_label,
                "ai_diag": ai_diag, "stop_line": round(stop_line, 2), "chip_floor": round(chip_floor, 2),
                "bias": round(bias, 2)
            })
            time.sleep(0.3) # 避免 Yahoo 封鎖 IP
        except Exception as e:
            st.sidebar.warning(f"跳過 {ticker}: 數據源暫不穩定")

# UI 渲染
if not data_list:
    st.error("目前所有數據源均無法連線，請檢查 API 限制。")
else:
    for d in data_list:
        st.markdown(f"""
        <div class="status-card {d['style']}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.6em; font-weight: bold;">{d['style']} {d['name']}</span>
                    <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span>
                </div>
                <span class="metric-tag">RSI: {d['rsi']} | {d['chip_flow']}</span>
            </div>
            <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
                趨勢: {d['trend']} | 乖離率: {d['bias']}% | 密集成交區: {d['chip_floor']}
            </div>
            <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="display: flex; gap: 25px;">
                <div style="flex: 2;">
                    <b>🧠 核心診斷：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['ai_diag']}</span>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                    <b>⚙️ 風控觀察：</b><br>
                    止損參考: <span style="color:#cf1322; font-weight:bold;">{d['stop_line']}</span><br>
                    成本地板: {d['chip_floor']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 自動重整
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新數據")
    time.sleep(1)
st.rerun()
