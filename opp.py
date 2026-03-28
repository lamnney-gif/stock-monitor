import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab Global - 避險監測戰情室", layout="wide")

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

# 3. CSS 樣式 (1600px 寬版佈局與色彩定義)
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
    .adr-tag { background: #e6f7ff; color: #0050b3; border: 1px solid #91d5ff; }
    .risk-tag { background: #fff2f0; color: #cf1322; border: 1px solid #ffccc7; font-weight: bold; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. 指標函數
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

# 5. 主標題
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 全球數據戰術板 V5.5")
with col_r: timer_placeholder = st.empty()

# 標的清單 (已修正台積電連動)
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

with st.spinner('計算全球避險情緒與連動數據中...'):
    # A. 全球風險監測 (VIX & US10Y & SOX)
    vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
    us10y = yf.Ticker("^TNX").history(period="5d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_status = "BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "BEAR"

    # 全球情緒標籤
    risk_level = "😨 恐慌" if vix > 25 else "⚖️ 穩定" if vix > 18 else "😊 樂觀"
    yield_trend = "📈 壓力" if us10y > 4.2 else "📉 寬鬆"

    for ticker, info in tickers.items():
        try:
            name = info['name']
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk")
            if df.empty: continue
            
            # 指標運算
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            # RSI & ATR & 布林帶寬
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
            tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
            atr_val = tr.rolling(14).mean().iloc[-1]
            b_width = ((ma20 + 2*std20) - (ma20 - 2*std20)) / ma20

            # 補回關鍵數據
            chip_floor = get_volume_support(df)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
            
            # ADR 連動修正邏輯
            adr_diff = "N/A"
            if info['adr']:
                adr_data = yf.Ticker(info['adr']).history(period="5d")
                adr_chg = ((adr_data['Close'].iloc[-1] - adr_data['Close'].iloc[-2]) / adr_data['Close'].iloc[-2]) * 100
                adr_diff = f"{adr_chg:+.1f}%"

            # 周線與買點
            w_ma20 = df_w['Close'].rolling(20).mean().iloc[-1]
            week_trend = "UP" if close_val > w_ma20 else "DOWN"
            suggested_buy = min(ma20 - 1.2 * std20, df['Low'].tail(3).min() * 0.99)
            dynamic_stop = close_val - (2.5 * atr_val)
            bias = ((close_val - ma20) / ma20) * 100
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100

            # 診斷邏輯 (加入 VIX 權重)
            if vix > 28: icon, style, status = "☢️", "☢️", f"☢️ 【極度恐慌】VIX 指標破表 ({vix:.1f})，全球資金撤離，不看任何技術買點。"
            elif sox_status == "BEAR": icon, style, status = "⚠️", "⚠️", "⚠️ 【環境預警】費半大盤弱勢。建議觀望，觀察位暫失效。"
            elif b_width < 0.08: icon, style, status = "🌪️", "🔎", f"🌪️ 【變盤預警】帶寬壓縮 ({b_width:.2f})，即將有大動作。"
            elif rsi_val > 72: icon, style, status = "🚨", "🚨", f"🚨 【短線過熱】RSI {rsi_val:.1f}。乖離率 {bias:.1f}%，追高風險大。"
            elif close_val < dynamic_stop: icon, style, status = "☢️", "☢️", f"☢️ 【趨勢破壞】跌破 ATR 底線 {dynamic_stop:.2f}。"
            elif close_val <= suggested_buy * 1.03 and week_trend == "UP":
                icon, style, status = ("✅", "✅", "✅ 【高勝率確信】量價共振回測觀察點。") if vol_ratio > 1.2 else ("🔎", "🔎", "🔎 【數據觀測】觸碰觀察位但動能不足。")
            else: icon, style, status = "🔎", "🔎", f"🔎 【常規運行】週線：{'多頭' if week_trend=='UP' else '偏弱'}。市場情緒：{risk_level}。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2), "stop": round(dynamic_stop, 2),
                "stop_line": round(stop_profit_line, 2), "chip_floor": round(chip_floor, 2),
                "rsi": round(rsi_val, 1), "vol": round(vol_ratio, 1), "adr": adr_diff, "slope": round(slope, 2),
                "bias": round(bias, 2), "sup": round(tech_sup, 2), "pre": round(tech_pre, 2),
                "diag": status, "pe": stock.info.get('forwardPE', "N/A"), "inst": f"{stock.info.get('heldPercentInstitutions', 0)*100:.1f}%"
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 ---
st.sidebar.markdown(f"""
### 📊 全球風險儀表板
- **市場情緒：** {risk_level} (VIX: {vix:.1f})
- **美債利率：** {yield_trend} ({us10y:.2f}%)
- **費半大盤：** {'📈 多頭' if sox_status=='BULL' else '📉 避險'}
""")

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
                <span class="metric-tag">PE: {d['pe']}</span>
                <span class="metric-tag risk-tag">VIX: {vix:.1f}</span>
                <span class="metric-tag">機構: {d['inst']}</span>
            </div>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            斜率: {d['slope']}% | 乖離率: {d['bias']}% | <b>成交量比: {d['vol']}x</b>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🔍 演算執行狀態 (Execution)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控參數模擬 (Risk Simulation)：</b> 
                    <span style="color:#1890ff;">波段高點預警: {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">ATR 演算底線: {d['stop']}</span> <br>
                    <b>密集換手區間: {d['chip_floor']}</b> | 統計支撐下軌: {d['sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參數 (Params)：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 模型觀察點</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預計壓力位</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
                    <div style="grid-column: span 2; height: 1px; background: #ddd; margin: 2px 0;"></div>
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
