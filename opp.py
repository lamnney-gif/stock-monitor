import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

st.set_page_config(page_title="半導體大戶戰情室-進階防守版", layout="wide")

st.markdown("""
<style>
.status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.08); }
.🚨 { background-color: #ffebee; border-left: 12px solid #d32f2f; color: #b71c1c; }
.⚠️ { background-color: #fffde7; border-left: 12px solid #fbc02d; color: #827717; }
.✅ { background-color: #e8f5e9; border-left: 12px solid #388e3c; color: #1b5e20; }
.☢️ { background-color: #fce4ec; border-left: 12px solid #c2185b; color: #880e4f; }
.💤 { background-color: #f5f5f5; border-left: 12px solid #9e9e9e; color: #424242; }
.🔎 { background-color: #ffffff; border-left: 12px solid #455a64; color: #263238; }
.metric-tag { display: inline-block; padding: 4px 10px; background: rgba(0,0,0,0.06); border-radius: 6px; margin-right: 10px; font-size: 0.9em; font-weight: bold; }
.price-sub { font-size: 0.85em; color: #666; margin-top: 5px; }
.timer-container { text-align: right; color: #e65100; font-weight: bold; font-size: 1.1em; padding: 8px 15px; border: 1px solid #ffcc80; border-radius: 8px; background: #fff8e1; }
</style>
""", unsafe_allow_html=True)

tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創",
    "2330.TW": "台積電", "NVDA": "輝達"
}

def get_volume_support(df):
    try:
        recent_df = df.tail(120)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

def get_google_news(keyword):
    news = []
    try:
        url = f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

col_t, col_r = st.columns([3, 1])
with col_t: st.title("🚀 半導體「大戶動向」全數據戰情室")
with col_r: timer_placeholder = st.empty()

data_list = []
news_dict = {}

with st.spinner('正在分析大戶筹碼與深度技術指標...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_sup = ma20 - (2 * std20)
            tech_press = ma20 + (2 * std20)
            chip_floor = get_volume_support(df)

            # 🔥 原始買點（保留）
            buy_price = (tech_sup + chip_floor) / 2

            # 🔥 新增：安全買點（只用來判斷）
            safe_buy_price = max(tech_sup, chip_floor)

            stop_profit_line = df['High'].tail(5).max() * 0.97
            
            bias = ((close - ma20) / ma20) * 100

            # 🔥 原始 slope（保留）
            y_data = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100

            # 🔥 新增：穩定 slope（判斷用）
            y_data_20 = df['Close'].tail(20).values
            slope_20 = (LinearRegression().fit(np.arange(20).reshape(-1,1), y_data_20.reshape(-1,1)).coef_[0][0] / y_data_20.mean()) * 100

            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # 🔥 新增：量能確認
            volume_confirm = vol_ratio > 1.2

            # 🔥 新增：風報比
            risk_reward = (tech_press - close) / (close - tech_sup) if close > tech_sup else 0

            info = stock.info
            pe_val = info.get('forwardPE', "無數據")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            insider_pct = info.get('heldPercentInsiders', 0) * 100

            # 🔥 強化診斷（但不動顯示數據）
            if vol_ratio > 2 and slope_20 < 0.1 and close < df['High'].tail(5).max():
                icon, style, status = "🚨", "🚨", f"🚨 【危險：主力出貨】放量但無法創高"
            elif close >= tech_press * 0.97:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】接近壓力 {tech_press:.2f}"
            elif close <= safe_buy_price * 1.03 and slope_20 > -0.15 and volume_confirm and risk_reward > 1.5:
                icon, style, status = "✅", "✅", f"✅ 【強化買點】接近支撐區 {buy_price:.2f}"
            elif close <= tech_sup:
                icon, style, status = "☢️", "☢️", f"☢️ 【警示：破位】跌破支撐 {tech_sup:.2f}"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【正常波動】壓力 {tech_press:.2f} / 支撐 {tech_sup:.2f}"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(tech_press, 2), "stop_line": round(stop_profit_line, 2),
                "pe": pe_val, "vol": round(vol_ratio, 2), "diag": status, "inst": f"{inst_pct:.1f}%", 
                "insider": f"{insider_pct:.1f}%", "tech_sup": round(tech_sup, 2), "chip_floor": round(chip_floor, 2), "bias": round(bias, 2)
            })

            news_dict[name] = get_google_news(name)

        except: pass

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <b>{d['icon']} {d['name']}</b> ${d['price']}<br>
                乖離率: {d['bias']}% | 成交量: {d['vol']}x
            </div>
            <div>
                本益比: {d['pe']} | 法人: {d['inst']} | 大戶: {d['insider']}
            </div>
        </div>
        <hr>
        <b>診斷：</b>{d['diag']}<br>
        🟢 買點: {d['buy']} | 🔴 壓力: {d['sell']} | 🛡️ 停利: {d['stop_line']}
    </div>
    """, unsafe_allow_html=True)

st.sidebar.title("📰 即時新聞")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(name):
            for n in news:
                st.markdown(n)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
