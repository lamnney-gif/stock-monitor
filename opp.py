import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (1600px 寬版)
st.set_page_config(page_title="Beta Lab Ultimate - 全球量化環境", layout="wide")

# 2. 私人存取驗證
def check_password():
    def password_entered():
        if st.session_state["password"] == "8888": 
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 內部開發監測系統")
        st.text_input("請輸入存取密碼：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 驗證失敗")
        return False
    return True

if not check_password(): st.stop()

# 3. CSS 樣式 (完整配色與 1600px 優化)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } 
    .metric-tag { display: inline-block; padding: 4px 10px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 8px; font-size: 0.85em; font-weight: 600; }
    .adr-tag { background: #e6f7ff; color: #0050b3; border: 1px solid #91d5ff; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. 指標函數
def get_indicators(df):
    close = df['Close']
    ma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    # ATR
    tr = pd.concat([df['High']-df['Low'], abs(df['High']-close.shift()), abs(df['Low']-close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    # 布林帶寬 (變盤偵測)
    bandwidth = ((ma20 + 2*std20) - (ma20 - 2*std20)) / ma20
    return ma20.iloc[-1], std20.iloc[-1], rsi.iloc[-1], atr.iloc[-1], bandwidth.iloc[-1]

def get_google_news(keyword):
    news = []
    try:
        feed = feedparser.parse(f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant")
        for entry in feed.entries[:3]: news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

# 5. 主標題
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 全球半導體量化戰術板 V4.0")
with col_r: timer_placeholder = st.empty()

# 標的清單與 ADR 對應
tickers = {
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

with st.spinner('掃描全球連動數據中...'):
    # A. 大盤濾網 (SOX)
    sox = yf.Ticker("^SOX").history(period="2mo")
    sox_ma20 = sox['Close'].mean()
    sox_current = sox['Close'].iloc[-1]
    sox_status = "BULL" if sox_current > sox_ma20 else "BEAR"

    for ticker, info in tickers.items():
        try:
            name = info['name']
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk") # 周線數據
            
            if df.empty: continue
            
            # 獲取指標
            ma20, std20, rsi, atr, b_width = get_indicators(df)
            close_val = df['Close'].iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            # 周線趨勢確認 (Multi-Timeframe)
            w_ma20 = df_w['Close'].rolling(20).mean().iloc[-1]
            week_trend = "UP" if close_val > w_ma20 else "DOWN"
            
            # ADR 溢價/連動 (美股領先訊號)
            adr_diff = "N/A"
            if info['adr']:
                adr_data = yf.Ticker(info['adr']).history(period="5d")
                adr_change = ((adr_data['Close'].iloc[-1] - adr_data['Close'].iloc[-2]) / adr_data['Close'].iloc[-2]) * 100
                adr_diff = f"{adr_change:+.1f}%"

            # 支撐壓力與停損
            tech_sup = ma20 - 2 * std20
            tech_pre = ma20 + 2 * std20
            suggested_buy = min(ma20 - 1.2 * std20, df['Low'].tail(3).min() * 0.99)
            dynamic_stop = close_val - (2.5 * atr)
            
            # 斜率與乖離
            y_data = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100

            # --- 終極勝率診斷邏輯 ---
            if sox_status == "BEAR":
                icon, style, status = "⚠️", "⚠️", "⚠️ 【大盤系統風險】費半弱勢。環境不穩，建議提高現金水位，暫緩所有實驗。"
            elif b_width < 0.08:
                icon, style, status = "🌪️", "🔎", f"🌪️ 【變盤預警】帶寬極窄 ({b_width:.2f})，能量高度壓縮。觀測方向突破，勝率通常較高。"
            elif rsi > 72:
                icon, style, status = "🚨", "🚨", f"🚨 【數據過熱】RSI {rsi:.1f}。進入超買，且乖離率 {bias:.1f}%，建議等待回測。"
            elif rsi < 35 or bias < -12:
                icon, style, status = "🟣", "🟣", "🟣 【統計極值】超賣訊號出現。周線趨勢為 " + ("支撐" if week_trend=="UP" else "偏弱") + "，觀測反彈動能。"
            elif close_val < dynamic_stop:
                icon, style, status = "☢️", "☢️", f"☢️ 【趨勢破壞】跌破 ATR 動態底線 {dynamic_stop:.2f}，模型停止追蹤。"
            elif close_val <= suggested_buy * 1.03 and week_trend == "UP":
                if vol_ratio > 1.2 and rsi < 60:
                    icon, style, status = "✅", "✅", "✅ 【高勝率確認】大盤+周線多頭共振，且帶量回測觀察位，邏輯確信度極高。"
                else:
                    icon, style, status = "🔎", "🔎", "🔎 【數據觀測】接近觀察位，但成交量不足，等待動能確認。"
            else:
                icon, style, status = "🔎", "🔎", "🔎 【常規運行】參數穩定。週線趨勢：" + ("偏多" if week_trend=="UP" else "偏空")

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2), "stop": round(dynamic_stop, 2),
                "rsi": round(rsi, 1), "vol": round(vol_ratio, 1), "adr": adr_diff, "slope": round(slope, 2),
                "bias": round(bias, 2), "sup": round(tech_sup, 2), "pre": round(tech_pre, 2),
                "diag": status, "inst": f"{stock.info.get('heldPercentInstitutions', 0)*100:.1f}%"
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 ---
st.sidebar.markdown(f"📊 **大盤濾網 (SOX)：** {'📈 多頭' if sox_status=='BULL' else '📉 避險'}")
st.sidebar.title("📰 即時情報推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(name):
            for n in news: st.markdown(n)

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
                <span class="metric-tag">RSI: {d['rsi']}</span>
                <span class="metric-tag">機構: {d['inst']}</span>
            </div>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            斜率: {d['slope']}% | 乖離: {d['bias']}% | <b>成交量比: {d['vol']}x</b>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🔍 演算執行狀態 (Execution)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控參數模擬：</b> 
                    <span style="color:#cf1322; font-weight:bold;">ATR 演算底線: {d['stop']}</span> | 
                    統計支撐下軌: {d['sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參數：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 模型觀察點</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預計壓力位</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
                    <div style="grid-column: span 2; height: 1px; background: #ddd;"></div>
                    <div><span class="price-label">📉 支撐分佈</span><br><span class="price-value">{d['sup']}</span></div>
                    <div><span class="price-label">📈 壓力分佈</span><br><span class="price-value">{d['pre']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後自動刷新")
    time.sleep(1)
st.rerun()
