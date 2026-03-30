import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
import time
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI - Groq 高速分析版", layout="wide")

# --- 2. AI 核心啟動 (僅保留 Groq) ---
@st.cache_resource
def init_ai_engines():
    engine = None
    try:
        if "GROQ_API_KEY" in st.secrets:
            engine = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except: pass
    return engine

groq_client = init_ai_engines()

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

# 4. CSS 樣式
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .BULL { border-left: 12px solid #52c41a; background-color: #f6ffed; } 
    .BEAR { border-left: 12px solid #ff4d4f; background-color: #fff5f5; } 
    .NEUTRAL { border-left: 12px solid #ffc53d; background-color: #fffbe6; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. 安全數據抓取 (帶快取) ---
@st.cache_data(ttl=3600)
def get_stock_data_safe(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: return None, None
        time.sleep(1.0) # 強制延遲
        info = stock.info
        return df, info
    except:
        return None, None

# --- 6. Groq 數據分析函式 ---
def analyze_with_groq(name, data_dict):
    if not groq_client:
        return "❌ Groq API 未設定"
    
    prompt = f"""
    你是高盛首席策略師。請分析 {name} 的數據並給出實戰建議（100字內）：
    數據：現價 {data_dict['price']}, RSI {data_dict['rsi']}, 籌碼 {data_dict['flow']}, 趨勢 {data_dict['trend']}, PE {data_dict['pe']}。
    """
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return "🔥 策略建議： " + completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq 忙碌中 ({str(e)[:20]})"

# --- 7. 主程式 ---
tickers = {
    "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
    "000660.KS": "海力士", "2303.TW": "聯電"
}

data_list = []
st.title("🖥️ Beta Lab - Groq 數據流分析")

with st.spinner('正在計算技術指標並調用 Groq AI...'):
    for ticker, name in tickers.items():
        df, s_info = get_stock_data_safe(ticker)
        
        if df is not None:
            # 計算指標
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = round((100 - (100 / (1 + gain/loss))).iloc[-1], 1)
            
            # 籌碼與趨勢
            flow = "買入" if df['Volume'].iloc[-1] > df['Volume'].mean() and df['Close'].iloc[-1] > df['Close'].iloc[-2] else "觀望"
            trend = "多頭" if close > ma20 else "空頭"
            pe = s_info.get('trailingPE', 'N/A')
            
            # 丟給 Groq 分析
            stats = {'price': close, 'rsi': rsi_val, 'flow': flow, 'trend': trend, 'pe': pe}
            ai_diag = analyze_with_groq(name, stats)
            
            data_list.append({
                "name": name, "ticker": ticker, "price": round(close, 2),
                "rsi": rsi_val, "flow": flow, "trend": trend, "ai": ai_diag,
                "status": "BULL" if rsi_val < 70 and trend == "多頭" else "NEUTRAL"
            })

# 渲染結果
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['status']}">
        <h3>{d['name']} ({d['ticker']}) - ${d['price']}</h3>
        <span class="metric-tag">RSI: {d['rsi']}</span>
        <span class="metric-tag">趨勢: {d['trend']}</span>
        <span class="metric-tag">籌碼: {d['flow']}</span>
        <p style="margin-top:15px; font-size:1.1em;">{d['ai']}</p>
    </div>
    """, unsafe_allow_html=True)

if st.button("手動刷新數據"):
    st.cache_data.clear()
    st.rerun()
