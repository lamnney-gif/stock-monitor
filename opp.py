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
st.set_page_config(page_title="半導體大戶戰情室-進階防守版", layout="wide")

# 2. 注入自定義 CSS
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

# 核心追蹤清單
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

# 頂部抬頭
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
            
            # --- 核心運算 ---
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_sup = ma20 - (2 * std20)   # 技術支撐
            tech_press = ma20 + (2 * std20) # 建議賣出 (停利價格)
            chip_floor = get_volume_support(df) # 籌碼地板
            buy_price = (tech_sup + chip_floor) / 2 # 綜合建議買入價
            
            # 停利防線：近 5 日高點回落 3%
            stop_profit_line = df['High'].tail(5).max() * 0.97
            
            bias = ((close - ma20) / ma20) * 100
            y_data = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            info = stock.info
            pe_val = info.get('forwardPE', "無數據")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            insider_pct = info.get('heldPercentInsiders', 0) * 100

            # 診斷邏輯
            if vol_ratio > 2.2 and abs(slope) < 0.1 and close > ma20:
                icon, style, status = "🚨", "🚨", f"🚨 【危險：大戶出貨】成交量暴增至 {vol_ratio:.1f} 倍但股價停滯。建議減碼。"
            elif close >= tech_press * 0.97:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】已接近壓力位 {tech_press:.2f}，建議將獲利分批落袋。"
            elif close <= buy_price * 1.03 and slope > -0.15:
                icon, style, status = "✅", "✅", f"✅ 【黃金買點】回測支撐區 {buy_price:.2f}。適合分批佈局。"
            elif close <= tech_sup:
                icon, style, status = "☢️", "☢️", f"☢️ 【警示：破位重挫】擊穿技術支撐 {tech_sup:.2f}，請嚴格停損。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【正常波動】於壓力 {tech_press:.2f} 與支撐 {tech_sup:.2f} 之間整理。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(tech_press, 2), "stop_line": round(stop_profit_line, 2),
                "pe": pe_val, "vol": round(vol_ratio, 2), "diag": status, "inst": f"{inst_pct:.1f}%", 
                "insider": f"{insider_pct:.1f}%", "tech_sup": round(tech_sup, 2), "chip_floor": round(chip_floor, 2), "bias": round(bias, 2)
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- 介面渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 1.8em; margin-left: 20px; font-family: monospace; color: #212529;">${d['price']}</span>
                <div class="price-sub">乖離率: {d['bias']}% | 成交量比: {d['vol']}x</div>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">預估本益比: {d['pe']}</span>
                <span class="metric-tag">法人持股: {d['inst']}</span>
                <span class="metric-tag">大戶持股: {d['insider']}</span>
            </div>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.15);">
        <div style="display: flex; gap: 20px;">
            <div style="flex: 3; font-size: 1.1em; line-height: 1.6;">
                <b>🔍 深度診斷報告：</b><br>{d['diag']}
            </div>
            <div style="flex: 1.2; background: rgba(255,255,255,0.6); padding: 12px; border-radius: 8px; border: 1px dashed #bbb;">
                <b>📊 操作位參考：</b><br>
                建議買入價：<span style="color:#388e3c; font-weight:bold;">{d['buy']}</span><br>
                🎯 建議停利價：<span style="color:#d32f2f; font-weight:bold;">{d['sell']}</span><br>
                🛡️ <span style="color:#1976d2; font-weight:bold;">停利防線：{d['stop_line']}</span><br>
                <div style="margin-top: 8px; font-size: 0.8em; color: #666; border-top: 1px solid #ddd; padding-top: 5px;">
                    支撐：{d['tech_sup']} | 地板：{d['chip_floor']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄
st.sidebar.title("📰 即時新聞推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
            for n in news: st.markdown(n)

# 倒數重整邏輯
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
