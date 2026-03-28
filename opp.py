import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (1600px 寬版佈局)
st.set_page_config(page_title="Beta Lab Global V6.0 - 籌碼與趨勢戰術板", layout="wide")

# 2. 私人存取驗證
def check_password():
    def password_entered():
        if st.session_state["password"] == "8888": 
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 內部開發監測系統 V6.0")
        st.text_input("請輸入管理員密碼：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 驗證失敗")
        return False
    return True

if not check_password(): st.stop()

# 3. CSS 樣式定義
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

# --- 側邊欄：法律存證區 ---
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px;">
    <p style="font-size: 0.85em; color: #333; line-height: 1.6;">
<b>【免責聲明】</b><br>
    1. 本網頁為個人 <b>Python 量化模型開發測試用途</b>，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、買賣建議、診斷報告皆為<b>程式演算法之實驗產出</b>，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。<b>任何閱覽者若據此進行交易，盈虧請自負</b>，本站開發者不承擔任何法律責任。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差，請以各交易所官方報價為準。
    </p>
</div>
""", unsafe_allow_html=True)

# --- 主頁面置頂警告 (手機版強制顯示) ---
st.markdown("""
<div class="mobile-warning">
<b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境</b><br>
    本站僅供 Python 程式邏輯測試（Beta Lab），內文建議與價格均為演算法實驗產出。
    <b>閱覽者據此操作之盈虧請自行承擔</b>。
    </p>
</div>
""", unsafe_allow_html=True)

# 4. 關鍵演算函數
def get_institutional_flow(df):
    """模擬籌碼力道：結合量價關係推算法人動向"""
    recent = df.tail(5)
    # 價漲量增 + 1, 價跌量增 - 1
    flow_score = 0
    for i in range(1, len(recent)):
        price_change = recent['Close'].iloc[i] - recent['Close'].iloc[i-1]
        vol_change = recent['Volume'].iloc[i] / recent['Volume'].iloc[i-1]
        if price_change > 0 and vol_change > 1.1: flow_score += 1
        if price_change < 0 and vol_change > 1.1: flow_score -= 1
    return "🔥 強勢買入" if flow_score >= 2 else "💧 持續流出" if flow_score <= -2 else "☁️ 盤整觀望"

def get_trend_score(df):
    """計算均線多頭排列強度"""
    c = df['Close']
    ma5, ma10, ma20 = c.rolling(5).mean().iloc[-1], c.rolling(10).mean().iloc[-1], c.rolling(20).mean().iloc[-1]
    if ma5 > ma10 > ma20: return "🌟 多頭排列", "#52c41a"
    if ma5 < ma10 < ma20: return "💀 空頭排列", "#f5222d"
    return "🌀 趨勢不明", "#8c8c8c"

def get_volume_support(df):
    try:
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

# 5. 主標題
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 全球半導體量化戰術板 V6.0")
with col_r: timer_placeholder = st.empty()

# 標的清單 (完整連動配置)
tickers = {
    "2330.TW": {"name": "台積電", "adr": "TSM"},
    "NVDA": {"name": "輝達", "adr": None},
    "TSM": {"name": "台積電ADR", "adr": None},
    "MU": {"name": "美光", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"},
    "6770.TW": {"name": "力積電", "adr": None},
    "2344.TW": {"name": "華邦電", "adr": None},
    "3481.TW": {"name": "群創", "adr": None},
    "1303.TW": {"name": "南亞", "adr": None}
}

data_list, news_dict = [], {}

with st.spinner('同步全球籌碼、風險與均線排列數據中...'):
    # A. 全球宏觀指標
    vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
    us10y = yf.Ticker("^TNX").history(period="5d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_status = "BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "BEAR"

    for ticker, info in tickers.items():
        try:
            name = info['name']
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk")
            if df.empty: continue
            
            # --- 核心運算 ---
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            # 籌碼與趨勢 (V6.0 新增)
            chip_flow = get_institutional_flow(df)
            trend_label, trend_color = get_trend_score(df)
            
            # 補回所有標籤數據
            chip_floor = get_volume_support(df)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
            
            # ADR 與風險指標
            adr_diff = "N/A"
            if info['adr']:
                adr_data = yf.Ticker(info['adr']).history(period="5d")
                adr_chg = ((adr_data['Close'].iloc[-1] - adr_data['Close'].iloc[-2]) / adr_data['Close'].iloc[-2]) * 100
                adr_diff = f"{adr_chg:+.1f}%"

            # 策略點位
            w_ma20 = df_w['Close'].rolling(20).mean().iloc[-1]
            week_trend = "UP" if close_val > w_ma20 else "DOWN"
            suggested_buy = min(ma20 - 1.2 * std20, df['Low'].tail(3).min() * 0.99)
            dynamic_stop = close_val - (2.5 * df['High'].sub(df['Low']).rolling(14).mean().iloc[-1])
            bias = ((close_val - ma20) / ma20) * 100

            # --- V6.0 診斷邏輯 ---
            if vix > 28: icon, style, status = "☢️", "☢️", f"☢️ 【極度恐慌】VIX {vix:.1f}，全球資金撤離，不建議任何操作。"
            elif sox_status == "BEAR": icon, style, status = "⚠️", "⚠️", "⚠️ 【大盤壓制】費半濾網為空頭，個股技術面暫時失效。"
            elif chip_flow == "💧 持續流出": icon, style, status = "🚨", "🚨", "🚨 【籌碼警告】法人資金大舉流出，下方支撐可能被打穿。"
            elif close_val <= suggested_buy * 1.03 and week_trend == "UP" and trend_label == "🌟 多頭排列":
                icon, style, status = "✅", "✅", "✅ 【終極確認】籌碼、均線、週線三者多頭共振，高勝率進場點。"
            else: icon, style, status = "🔎", "🔎", f"🔎 【狀態觀測】均線：{trend_label}。籌碼：{chip_flow}。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2), "stop": round(dynamic_stop, 2),
                "stop_line": round(stop_profit_line, 2), "chip_floor": round(chip_floor, 2),
                "vol": round(vol_ratio, 1), "adr": adr_diff, "bias": round(bias, 2), "sup": round(tech_sup, 2), "pre": round(tech_pre, 2),
                "diag": status, "pe": stock.info.get('forwardPE', "N/A"), "chip_flow": chip_flow, "trend": trend_label, "t_color": trend_color
            })
        except: pass

# --- UI 渲染 ---
st.sidebar.markdown(f"""
### 📊 全球宏觀數據 V6.0
- **市場情緒：** {vix:.1f} ({'😱 恐慌' if vix > 22 else '😊 樂觀'})
- **美債 10Y：** {us10y:.2f}%
- **費半大盤：** {'📈 多頭' if sox_status=='BULL' else '📉 避險'}
""")

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag adr-tag">ADR連動: {d['adr']}</span>
                <span class="metric-tag chip-tag">籌碼: {d['chip_flow']}</span>
                <span class="metric-tag" style="background:{d['t_color']}; color:white;">{d['trend']}</span>
                <span class="metric-tag">PE: {d['pe']}</span>
            </div>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🔍 演算診斷 (Diagnostics)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控與籌碼模擬：</b> 
                    <span style="color:#1890ff;">波段高點預警: {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">ATR 演算底線: {d['stop']}</span> <br>
                    <b>密集換手區間: {d['chip_floor']}</b> | 乖離率: {d['bias']}% | <b>成交量比: {d['vol']}x</b>
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯觀察點：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 模型觀察點</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預計壓力位</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
                    <div><span class="price-label">📉 支撐分佈</span><br><span class="price-value">{d['sup']}</span></div>
                    <div><span class="price-label">📈 壓力分佈</span><br><span class="price-value">{d['pre']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 自動刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新")
    time.sleep(1)
st.rerun()
