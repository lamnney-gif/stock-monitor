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
st.set_page_config(page_title="半導體大戶戰情室-全能版", layout="wide")

# 2. CSS 樣式
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .timer-container { text-align: right; color: #fa8c16; font-weight: bold; font-size: 1.1em; padding: 10px 20px; border: 1px solid #ffd591; border-radius: 10px; background: #fff7e6; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "INTC": "英特爾"
}

def get_volume_support(df):
    try:
        recent_df = df.tail(60) # 反應靈敏度調高
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

# 頂部
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 半導體大戶戰情室 - 核心功能回歸版")
with col_r: timer_placeholder = st.empty()

data_list = []
news_dict = {}

with st.spinner('正在同步全球新聞與籌碼數據...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)
            local_low_3d = df['Low'].tail(3).min()
            local_low_20d = df['Low'].tail(20).min()
            chip_floor = get_volume_support(df)
            
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100

            # --- 核心邏輯：防倒掛買入計算 ---
            if slope_pct > 0.6:
                raw_buy = (ma10 * 0.7) + (tech_support * 0.3)
            else:
                raw_buy = (tech_support * 0.4) + (chip_floor * 0.6)
            
            # 強制校準：買點不得高於現價
            suggested_buy = min(raw_buy, local_low_3d * 0.99)
            stop_loss = min(local_low_20d, suggested_buy) * 0.95
            stop_profit_line = df['High'].tail(5).max() * 0.97

            # --- 診斷報告 ---
            if close_val < stop_loss:
                icon, style, status = "☢️", "☢️", f"☢️ 【支撐瓦解】現價已跌破所有防線。下墜慣性強，切勿接刀，請靜待 3 日不破底再觀察。"
            elif bias > 20:
                icon, style, status = "🚨", "🚨", f"🚨 【嚴重超漲】乖離率 {bias:.1f}% 過高。目前追高風險極大，建議等回測 {suggested_buy:.2f}。"
            elif slope_pct < -0.2 and close_val < tech_support:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【空頭修正】原技術支撐已轉壓力。新佈局點下移至 {suggested_buy:.2f}，量縮再進。"
            elif close_val <= suggested_buy * 1.03 and slope_pct > -0.1:
                icon, style, status = "✅", "✅", f"✅ 【買入訊號】回測支撐且斜率走平，具備中長線布局價值。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【區間整理】股價於支撐 {suggested_buy:.2f} 與壓力 {tech_pressure:.2f} 間震盪。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), "stop_line": round(stop_profit_line, 2),
                "stop_loss": round(stop_loss, 2), "pe": pe_val, "vol": round(vol_ratio, 2), "inst": f"{inst_pct:.1f}%",
                "diag": status, "slope": round(slope_pct, 2), "chip_floor": round(chip_floor, 2), "bias": round(bias, 2)
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2.1em; margin-left: 20px; font-family: monospace;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">PE: {d['pe']}</span>
                <span class="metric-tag">法人: {d['inst']}</span>
            </div>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            趨勢斜率: {d['slope']}% | 乖離率: {d['bias']}% | 量比: {d['vol']}x
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2;">
                <b>💡 戰情診斷：</b><br><span style="line-height:1.6;">{d['diag']}</span>
                <div class="defense-box">
                    🛡️ <b>防禦體系：</b> 
                    停利參考: {d['stop_line']} | <span style="color:#cf1322; font-weight:bold;">絕對停損: {d['stop_loss']}</span> | 籌碼地板: {d['chip_floor']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.5); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>📊 建議參考位：</b><br>
                <div style="margin-top: 10px;">
                    🟢 建議買入: <span style="color:#389e0d; font-weight:bold;">{d['buy']}</span><br>
                    🎯 建議停利: <span style="color:#cf1322; font-weight:bold;">{d['sell']}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞回歸
st.sidebar.title("📰 即時情報推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
            for n in news: st.markdown(n)

# 刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 後自動重載</div>", unsafe_allow_html=True)
    time.sleep(1)
st.rerun()
