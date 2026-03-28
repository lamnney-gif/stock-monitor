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
st.set_page_config(page_title="半導體大戶戰情室-防炸穩定版", layout="wide")

# 2. 核心 CSS 修復 (修正縮排與卡片溢出問題)
st.markdown("""
    <style>
    .status-card { 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        border: 1px solid #e0e0e0; 
        box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        min-height: 250px;
    }
    .🚨 { border-left: 10px solid #ff4d4f; background-color: #fff1f0; }
    .⚠️ { border-left: 10px solid #faad14; background-color: #fffbe6; }
    .✅ { border-left: 10px solid #52c41a; background-color: #f6ffed; }
    .☢️ { border-left: 10px solid #cf1322; background-color: #fff1f0; }
    .💤 { border-left: 10px solid #bfbfbf; background-color: #f5f5f5; }
    .🔎 { border-left: 10px solid #1890ff; background-color: #ffffff; }
    
    .metric-tag { 
        display: inline-block; 
        padding: 4px 8px; 
        background: #f0f2f5; 
        border-radius: 4px; 
        margin-right: 5px; 
        font-size: 0.85em; 
        color: #595959;
        font-weight: bold;
    }
    .defense-box { 
        background: rgba(255, 255, 255, 0.6); 
        border: 1px dashed #8c8c8c; 
        padding: 10px; 
        border-radius: 8px; 
        margin-top: 10px; 
    }
    .timer-container { 
        text-align: right; 
        color: #d46b08; 
        font-weight: bold; 
        font-size: 1.1em; 
        padding: 8px 15px; 
        border: 1px solid #ffd591; 
        border-radius: 8px; 
        background: #fff7e6; 
    }
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

# 標題
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 半導體大戶動向戰情室")
with col_r: timer_placeholder = st.empty()

data_list = []
news_dict = {}

with st.spinner('校準數據中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            chip_floor = get_volume_support(df)
            suggested_buy = (tech_support + chip_floor) / 2
            
            high_low = df['High'] - df['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            sell_limit = close_val + (2.5 * atr) 

            bias = ((close_val - ma20) / ma20) * 100
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            insider_pct = info.get('heldPercentInsiders', 0) * 100

            # 診斷邏輯
            if vol_ratio > 2.0 and abs(slope_pct) < 0.1 and close_val > ma20:
                icon, style, status = "🚨", "🚨", f"🚨 【大戶倒貨】成交量爆出 {vol_ratio:.2f} 倍但股價幾乎不動 (斜率僅 {slope_pct:.2f}%)。這是典型的高檔換手或大戶出貨，極度危險，建議大幅減碼。"
            elif close_val >= tech_pressure * 0.98:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】現價 {close_val:.2f} 逼近建議賣出價 {tech_pressure:.2f}。目前正乖離率達 {bias:.1f}%，短線過熱，建議分批獲利入袋。"
            elif vol_ratio < 0.8 and abs(slope_pct) < 0.05:
                icon, style, status = "💤", "💤", f"💤 【縮量整理】成交量僅均量 {vol_ratio:.2f} 倍，市場觀望氣氛濃厚，暫無攻擊動能，建議保留現金等待表態。"
            elif close_val <= suggested_buy * 1.02 and slope_pct > -0.1:
                icon, style, status = "✅", "✅", f"✅ 【買入訊號】股價回測建議買入價 {suggested_buy:.2f} 附近。支撐區表現強勁且趨勢開始回穩，適合分批佈局。"
            elif close_val <= tech_support:
                icon, style, status = "☢️", "☢️", f"☢️ 【停損警示】股價已擊穿技術支撐 {tech_support:.2f}。趨勢慣性已被破壞，請嚴格執行停損以保護資金。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【正常整理】於支撐 {tech_support:.2f} 與壓力 {tech_pressure:.2f} 之間波動。量能平穩，暫無明顯轉向訊號。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), "stop_line": round(stop_profit_line, 2),
                "sell_limit": round(sell_limit, 2), "pe": pe_val, "vol": round(vol_ratio, 2), 
                "diag": status, "inst": f"{inst_pct:.1f}%", "insider": f"{insider_pct:.1f}%",
                "tech_sup": round(tech_support, 2), "chip_floor": round(chip_floor, 2), "bias": round(bias, 2), "slope": round(slope_pct, 2)
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <b style="font-size: 1.5em;">{d['icon']} {d['name']}</b>
                <span style="font-size: 1.8em; margin-left: 15px; font-family: monospace;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">PE: {d['pe']}</span>
                <span class="metric-tag">法人: {d['inst']}</span>
            </div>
        </div>
        <div style="margin: 10px 0; font-size: 0.85em; color: #666;">
            乖離: {d['bias']}% | 量比: {d['vol']}x | 斜率: {d['slope']}%
        </div>
        <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
        <div style="display: grid; grid-template-columns: 2fr 1.2fr; gap: 20px;">
            <div>
                <b>💡 戰情診斷：</b><br><span style="font-size: 1em;">{d['diag']}</span>
                <div class="defense-box">
                    🛡️ <b>防禦：</b> 
                    <span style="color:#1890ff;">停利線: {d['stop_line']}</span> | 
                    支撐: {d['tech_sup']} | 地板: {d['chip_floor']}
                </div>
            </div>
            <div style="background: white; padding: 10px; border-radius: 8px; border: 1px solid #ddd;">
                <b>📊 核心位置：</b><br>
                🟢 買入: <span style="color:green;">{d['buy']}</span><br>
                🎯 停利: <span style="color:red;">{d['sell']}</span><br>
                🚫 <span style="color:darkred;">賣壓: {d['sell_limit']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄
st.sidebar.title("📰 即時情報")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
            for n in news: st.markdown(n)

# 刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)
st.rerun()
