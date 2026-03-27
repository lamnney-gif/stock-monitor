import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

st.set_page_config(page_title="半導體大戶戰情室-Pro版", layout="wide")

# CSS
st.markdown("""
<style>
.status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.08); }
.🚨 { background-color: #ffebee; border-left: 12px solid #d32f2f; }
.⚠️ { background-color: #fffde7; border-left: 12px solid #fbc02d; }
.✅ { background-color: #e8f5e9; border-left: 12px solid #388e3c; }
.☢️ { background-color: #fce4ec; border-left: 12px solid #c2185b; }
.🔎 { background-color: #ffffff; border-left: 12px solid #455a64; }
.metric-tag { padding: 4px 10px; background: rgba(0,0,0,0.06); border-radius: 6px; margin-right: 10px; font-size: 0.9em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

tickers = {
    "NVDA": "輝達",
    "MU": "美光",
    "2330.TW": "台積電",
    "2303.TW": "聯電",
    "6770.TW": "力積電"
}

def get_volume_support(df):
    try:
        recent_df = df.tail(120)
        v_hist = np.histogram(recent_df['Close'], bins=12, weights=recent_df['Volume'])
        idx = np.argmax(v_hist[0])
        return (v_hist[1][idx] + v_hist[1][idx+1]) / 2
    except:
        return 0

def get_google_news(keyword):
    news = []
    try:
        url = f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append(f"• [{entry.title}]({entry.link})")
    except:
        pass
    return news

st.title("🚀 半導體戰情室 Pro（策略升級版）")

data_list = []
news_dict = {}

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")

        if df.empty:
            continue

        close = df['Close'].iloc[-1]

        # === 技術指標 ===
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]

        tech_sup = ma20 - 2 * std20
        tech_press = ma20 + 2 * std20

        chip_floor = get_volume_support(df)

        # ✅ 修正買點（取強支撐）
        base_buy = max(tech_sup, chip_floor)

        # === 趨勢判斷 ===
        trend_strength = (close - df['Close'].iloc[-60]) / df['Close'].iloc[-60] * 100

        if trend_strength > 20:
            market_type = "trend"
        elif trend_strength < -20:
            market_type = "down"
        else:
            market_type = "range"

        # === 買點依市場類型 ===
        if market_type == "trend":
            buy_price = ma20
        elif market_type == "range":
            buy_price = base_buy
        else:
            buy_price = tech_sup * 0.97

        # === 趨勢斜率（20日）===
        y_data = df['Close'].tail(20).values
        slope = (LinearRegression().fit(np.arange(20).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100

        # === 量能 ===
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-5:-1].mean()
        volume_confirm = vol_ratio > 1.2

        # === 停利線 ===
        stop_profit = df['High'].tail(5).max() * 0.97

        # === 風報比 ===
        risk_reward = (tech_press - close) / (close - tech_sup) if close > tech_sup else 0

        # === 診斷邏輯 ===
        if vol_ratio > 2 and slope < 0.1 and close < df['High'].tail(5).max():
            icon, style, msg = "🚨", "🚨", "【主力出貨】放量卻不創高"
        elif close <= buy_price * 1.03 and volume_confirm and slope > -0.2 and risk_reward > 1.5:
            icon, style, msg = "✅", "✅", f"【可布局】接近支撐 {buy_price:.2f}"
        elif close <= tech_sup:
            icon, style, msg = "☢️", "☢️", "【破位】跌破支撐需停損"
        elif close >= tech_press * 0.97:
            icon, style, msg = "⚠️", "⚠️", "【壓力區】建議減碼"
        else:
            icon, style, msg = "🔎", "🔎", "【觀望】等待方向"

        data_list.append({
            "name": f"{name} ({ticker})",
            "price": round(close,2),
            "buy": round(buy_price,2),
            "sell": round(tech_press,2),
            "stop": round(stop_profit,2),
            "vol": round(vol_ratio,2),
            "trend": market_type,
            "rr": round(risk_reward,2),
            "msg": msg,
            "icon": icon,
            "style": style
        })

        news_dict[name] = get_google_news(name)

    except:
        pass

# === 顯示 ===
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <h3>{d['icon']} {d['name']} - ${d['price']}</h3>
        <p>{d['msg']}</p>
        <p>📈 趨勢: {d['trend']} | 成交量: {d['vol']}x | 風報比: {d['rr']}</p>
        <p>🟢 買點: {d['buy']} | 🔴 壓力: {d['sell']} | 🛡️ 停利線: {d['stop']}</p>
    </div>
    """, unsafe_allow_html=True)

# === 側邊新聞 ===
st.sidebar.title("📰 新聞")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(name):
            for n in news:
                st.markdown(n)

# === 自動刷新 ===
for i in range(60, 0, -1):
    st.sidebar.markdown(f"⏱ {i}s refresh")
    time.sleep(1)

st.rerun()
