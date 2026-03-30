import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
import time
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI - Groq 數據流版", layout="wide")

# --- 2. AI 核心啟動 (聚焦 Groq) ---
@st.cache_resource
def init_ai_engines():
    engine = None
    try:
        if "GROQ_API_KEY" in st.secrets:
            # 優先使用 Groq，因為它比 Gemini 快得多，且不易出現 API 忙碌
            engine = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())
    except:
        pass
    return engine

groq_client = init_ai_engines()

# 2. 驗證系統
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

# 3. CSS 樣式 (維持專業面板風)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. 核心演算函數 (移除新聞抓取)
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

# --- 5. Groq 數據深度診斷 (完全取代原本的新聞分析) ---

@st.cache_data(ttl=14400)
def get_groq_analysis(name, stats):
    if not groq_client:
        return "❌ Groq API 未啟動，請檢查 Secrets 設定。"
    
    # 將數據結構化，讓 Groq 快速理解
    prompt = f"""
    你是 Goldman Sachs 策略師。針對 {name} 提供『數據穿透診斷』。
    數據包：
    - 現價: {stats['price']}
    - PE: {stats['pe']}
    - RSI: {stats['rsi']}
    - 籌碼流向: {stats['flow']}
    - 趨勢狀態: {stats['trend']}
    - 營收成長: {stats['rev']}

    請直接給出實戰建議（合理溢價、避險、或回測加碼）。語氣冷靜，限制 110 字內。
    """
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "你是一位專注於量化指標與資本市場的資深策略分析師。"},
                      {"role": "user", "content": prompt}]
        )
        return "🔥 策略室： " + completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Groq 服務過載，暫由數據模型代管。"

# 6. 主頁面與清單
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ Beta Lab - Groq 數據自動化版")
with col_r: timer_placeholder = st.empty()

tickers = {
    "2330.TW": {"name": "台積電"}, "NVDA": {"name": "輝達"},
    "MU": {"name": "美光"}, "000660.KS": {"name": "海力士"},
    "2303.TW": {"name": "聯電"}, "6770.TW": {"name": "力積電"},
    "2344.TW": {"name": "華邦電"}, "3481.TW": {"name": "群創"}, "1303.TW": {"name": "南亞"}
}

data_list = []

with st.spinner('同步市場數據與 Groq 運算中...'):
    # 全局指標
    try:
        vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        sox = yf.Ticker("^SOX").history(period="1mo")
        sox_status = "📈 BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "📉 BEAR"
    except:
        vix, sox_status = 20.0, "📉 BEAR"

    for ticker, info in tickers.items():
        try:
            # 抓取行情 (移除所有新聞相關代碼)
            stock = yf.Ticker(ticker)
            s_info = stock.info
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            # 技術指標
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
            
            chip_flow = get_institutional_flow(df)
            ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
            trend_label = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
            
            # 風控參數
            chip_floor = get_volume_support(df)
            tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
            suggested_buy = ma20 - 1.2 * std20
            
            # 基本面文字化
            pe_str = f"{s_info.get('trailingPE', 0):.1f}" if s_info.get('trailingPE') else "N/A"
            rev_str = f"{(s_info.get('revenueGrowth', 0) or 0)*100:.1f}%"

            # 調用 Groq 分析 (直接餵數據)
            stats_bundle = {
                'price': close_val, 'pe': pe_str, 'rsi': f"{rsi_val:.1f}",
                'flow': chip_flow, 'trend': trend_label, 'rev': rev_str
            }
            ai_diag = get_groq_analysis(info['name'], stats_bundle)

            data_list.append({
                "style": "✅" if rsi_val < 70 else "⚠️", 
                "icon": "✅" if rsi_val < 70 else "⚠️",
                "name": f"{info['name']} ({ticker})", "price": round(close_val, 2),
                "ai_diag": ai_diag, "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2),
                "pe": pe_str, "rev": rev_str, "rsi": round(rsi_val, 1), "vol": round(vol_ratio, 1),
                "sup": round(tech_sup, 2), "chip_floor": round(chip_floor, 2),
                "chip_flow": chip_flow, "trend": trend_label
            })
            # 稍微延遲防止 Yahoo 封鎖
            time.sleep(0.5)
        except:
            continue

# --- UI 渲染 ---
st.sidebar.markdown(f"📊 **全球監控**\n- VIX: {vix:.1f}\n- SOX: {sox_status}")

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span>
            </div>
            <span class="metric-tag">RSI: {d['rsi']} | 籌碼: {d['chip_flow']}</span>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            趨勢: {d['trend']} | <b>本益比: {d['pe']}</b> | <b>營收成長: {d['rev']}</b> | 成交量比: {d['vol']}x
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2;">
                <b>🧠 Groq 策略診斷：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['ai_diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>成本觀察位：</b> 
                    密集換手區間: {d['chip_floor']} | 統計支撐: {d['sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參考：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span style="color:#666; font-size:0.8em;">🟢 觀察買點</span><br><span class="price-value" style="color:#389e0d;">{d['buy']}</span></div>
                    <div><span style="color:#666; font-size:0.8em;">🎯 壓力位</span><br><span class="price-value" style="color:#cf1322;">{d['sell']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 倒數 60 秒刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新數據")
    time.sleep(1)
st.rerun()
