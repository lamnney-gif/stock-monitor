import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime, timedelta
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置
st.set_page_config(page_title="半導體大戶戰情室-全防禦版", layout="wide")

# 2. CSS 樣式
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.08); }
    .🚨 { background-color: #ffebee; border-left: 12px solid #d32f2f; color: #b71c1c; }
    .⚠️ { background-color: #fffde7; border-left: 12px solid #fbc02d; color: #827717; }
    .✅ { background-color: #e8f5e9; border-left: 12px solid #388e3c; color: #1b5e20; }
    .☢️ { background-color: #fce4ec; border-left: 12px solid #c2185b; color: #880e4f; }
    .🔎 { background-color: #ffffff; border-left: 12px solid #455a64; color: #263238; }
    .metric-tag { display: inline-block; padding: 4px 10px; background: rgba(0,0,0,0.1); border-radius: 6px; margin-right: 10px; font-size: 0.85em; font-weight: bold; }
    .timer-container { text-align: right; color: #e65100; font-weight: bold; font-size: 1.1em; padding: 8px 15px; border: 1px solid #ffcc80; border-radius: 8px; background: #fff8e1; }
    .defense-box { background: rgba(25, 118, 210, 0.05); border: 1px dashed #1976d2; padding: 10px; border-radius: 8px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "INTC": "英特爾"
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

# 標題與刷新
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🚀 半導體戰情室 - 核心防禦版")
with col_r: timer_placeholder = st.empty()

data_list = []
news_dict = {}

with st.spinner('同步全球大戶籌碼中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            # --- 核心邏輯計算 ---
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 1. 技術防線 (原本的邏輯)
            tech_sup = ma20 - (2 * std20)   # 技術支撐
            tech_press = ma20 + (2 * std20) # 建議停利價
            
            # 2. 停利防線 (近 5 日高點回落 3%)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            
            # 3. 籌碼地板 & 買入建議
            chip_floor = get_volume_support(df)
            buy_price = (tech_sup + chip_floor) / 2
            
            # 4. 賣壓上限 (ATR 2.5倍波幅)
            high_low = df['High'] - df['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            sell_limit = close + (2 * atr) 

            # 指標計算
            bias = ((close - ma20) / ma20) * 100
            y_data = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100

            # 診斷狀態
            if vol_ratio > 2.0 and slope < -0.05:
                icon, style, status = "🚨", "🚨", "🚨 【危險：大戶出貨】爆量下跌，趨勢轉弱。建議大幅減碼。"
            elif close >= tech_press * 0.98:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】已達壓力位 {tech_press:.2f}。建議獲利了結。"
            elif close <= buy_price * 1.03 and slope > -0.15:
                icon, style, status = "✅", "✅", f"✅ 【黃金買點】回測支撐與地板區。適合進場。"
            elif close <= tech_sup:
                icon, style, status = "☢️", "☢️", f"☢️ 【警示：破位】擊穿技術支撐 {tech_sup:.2f}，請嚴格停損。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【正常波動】於壓力 {tech_press:.2f} 與支撐 {tech_sup:.2f} 之間整理。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(tech_press, 2), "stop_line": round(stop_profit_line, 2),
                "sell_limit": round(sell_limit, 2), "pe": pe_val, "vol": round(vol_ratio, 2), 
                "diag": status, "inst": f"{inst_pct:.1f}%", "tech_sup": round(tech_sup, 2), 
                "chip_floor": round(chip_floor, 2), "bias": round(bias, 2)
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 1.8em; margin-left: 20px; font-family: monospace;">${d['price']}</span>
                <div style="color: #666; font-size: 0.85em; margin-top: 5px;">
                    乖離率: {d['bias']}% | 成交量比: {d['vol']}x | 預估 PE: {d['pe']}
                </div>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">法人持股: {d['inst']}</span>
            </div>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.15);">
        <div style="display: flex; gap: 20px;">
            <div style="flex: 2.5;">
                <b>🔍 深度診斷報告：</b><br>{d['diag']}
                <div class="defense-box">
                    🛡️ <b>防禦體系：</b> 
                    停利防線：<span style="color:#1976d2; font-weight:bold;">{d['stop_line']}</span> | 
                    技術支撐：{d['tech_sup']} | 
                    籌碼地板：{d['chip_floor']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 12px; border-radius: 8px; border: 1px dashed #bbb;">
                <b>📊 操作位參考：</b><br>
                🟢 建議買入價：<span style="color:#388e3c; font-weight:bold;">{d['buy']}</span><br>
                🎯 建議停利價：<span style="color:#d32f2f; font-weight:bold;">{d['sell']}</span><br>
                🚫 <span style="color:#b71c1c; font-weight:bold;">⚠️ 強力賣壓區：{d['sell_limit']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞
st.sidebar.title("📰 即時新聞推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
            for n in news: st.markdown(n)

# 刷新邏輯
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
