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
st.set_page_config(page_title="半導體大戶全中文戰情室", layout="wide")

# 2. 自定義樣式 (美化卡片)
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .🚨 { background-color: #ffebee; border-left: 10px solid #d32f2f; color: #b71c1c; }
    .⚠️ { background-color: #e1f5fe; border-left: 10px solid #0288d1; color: #01579b; }
    .✅ { background-color: #e8f5e9; border-left: 10px solid #388e3c; color: #1b5e20; }
    .☢️ { background-color: #fff3e0; border-left: 10px solid #f57c00; color: #e65100; }
    .💤 { background-color: #f5f5f5; border-left: 10px solid #9e9e9e; color: #424242; }
    .🔎 { background-color: #ffffff; border-left: 10px solid #455a64; color: #263238; }
    .metric-tag { display: inline-block; padding: 2px 8px; background: rgba(0,0,0,0.08); border-radius: 4px; margin-right: 8px; font-size: 0.85em; font-family: monospace; }
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
st.title("🚀 半導體「大戶動向」全中文戰情室")
st.caption(f"最後更新時間：{datetime.now().strftime('%H:%M:%S')} (每 60 秒自動刷新)")

data_list = []
news_dict = {}

# 數據運算
with st.spinner('正在分析籌碼與支撐壓力指標...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_sup = ma20 - (2 * std20) # 技術支撐
            tech_press = ma20 + (2 * std20) # 壓力位
            chip_floor = get_volume_support(df) # 籌碼地板
            buy_price = (tech_sup + chip_floor) / 2 # 建議買入價
            
            # 斜率
            y = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y.reshape(-1,1)).coef_[0][0] / y.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # 籌碼數據
            info = stock.info
            pe_val = info.get('forwardPE', "無數據")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            insider_pct = info.get('heldPercentInsiders', 0) * 100

            # 診斷邏輯
            if vol_ratio > 2.0 and abs(slope) < 0.1 and close > ma20:
                icon, style, status = "🚨", "🚨", "【大戶倒貨】爆量但股價不漲，疑似大戶正在高檔出貨，請小心。"
            elif close >= tech_press * 0.98:
                icon, style, status = "⚠️", "⚠️", f"【分批停利】逼近壓力位 {tech_press:.2f}。股價過熱，建議先獲利了結。"
            elif vol_ratio < 0.8 and abs(slope) < 0.05:
                icon, style, status = "💤", "💤", "【縮量整理】交易清淡且股價橫盤，暫無大行情，建議觀望。"
            elif close <= buy_price * 1.02 and slope > -0.1:
                icon, style, status = "✅", "✅", f"【買入訊號】回測支撐點 {buy_price:.2f}。大戶成本區有守，適合佈局。"
            elif close <= tech_sup:
                icon, style, status = "☢️", "☢️", f"【停損警示】股價跌穿技術支撐 {tech_sup:.2f}。趨勢走空，請保命停損。"
            else:
                icon, style, status = "🔎", "🔎", f"【正常波動】於區間內整理。目前斜率為 {slope:.2f}%，量能穩定。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name}({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(tech_press, 2), "pe": pe_val,
                "vol": round(vol_ratio, 2), "slope": f"{slope:.2f}%", "diag": status,
                "inst": f"{inst_pct:.1f}%", "insider": f"{insider_pct:.1f}%"
            })
            news_dict[name] = get_google_news(name)
        except: pass

# 渲染卡片介面
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 1.4em; font-weight: bold;">{d['icon']} {d['name']} | 現價: {d['price']}</div>
            <div>
                <span class="metric-tag">本益比: {d['pe']}</span>
                <span class="metric-tag">法人持股: {d['inst']}</span>
                <span class="metric-tag">大戶持股: {d['insider']}</span>
            </div>
        </div>
        <div style="margin: 12px 0; font-size: 1.05em;"><b>智慧診斷：</b> {d['diag']}</div>
        <div style="font-size: 0.9em; color: #666;">
            成交量比: {d['vol']} | 趨勢斜率: {d['slope']} | 
            建議買入價: <span style="color:green; font-weight:bold;">{d['buy']}</span> | 
            建議賣出價: <span style="color:red; font-weight:bold;">{d['sell']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞
st.sidebar.title("📰 即時新聞")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
            for n in news: st.markdown(n)

# 每 60 秒刷新一次
time.sleep(60)
st.rerun()
