import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (這行必須在最前面)
st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# 2. 注入自定義 CSS (為了讓燈號有顏色)
st.markdown("""
    <style>
    .🚨 { background-color: #ffccbc; color: #bf360c; padding: 15px; border-radius: 10px; border-left: 10px solid #d84315; margin-bottom: 10px; }
    .⚠️ { background-color: #d1ecf1; color: #0c5460; padding: 15px; border-radius: 10px; border-left: 10px solid #17a2b8; margin-bottom: 10px; }
    .✅ { background-color: #d4edda; color: #155724; padding: 15px; border-radius: 10px; border-left: 10px solid #28a745; margin-bottom: 10px; }
    .☢️ { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 10px; border-left: 10px solid #dc3545; margin-bottom: 10px; }
    .💤 { background-color: #e2e3e5; color: #383d41; padding: 15px; border-radius: 10px; border-left: 10px solid #6c757d; margin-bottom: 10px; }
    .🔎 { background-color: #ffffff; color: #212529; padding: 15px; border-radius: 10px; border-left: 10px solid #212529; border: 1px solid #ddd; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創"
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
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🚀 半導體「大戶動向」雲端戰情室")
with col2:
    st.write(f"⏱️ 最後更新：{datetime.now().strftime('%H:%M:%S')}")
    st.caption("網頁每 60 秒會自動刷新數據")

# 運算邏輯
data_list = []
news_sidebar = {}

with st.spinner('數據計算中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            t_sup = ma20 - (2 * std20)
            t_press = ma20 + (2 * std20)
            c_floor = get_volume_support(df)
            buy_price = (t_sup + c_floor) / 2
            
            # 斜率
            y = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y.reshape(-1,1)).coef_[0][0] / y.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # 判定燈號
            if vol_ratio > 2.0 and abs(slope) < 0.1 and close > ma20:
                icon, style, status = "🚨", "🚨", "【大戶倒貨】成交量爆出但股價不動，極度危險。"
            elif close >= t_press * 0.98:
                icon, style, status = "⚠️", "⚠️", "【分批停利】股價過熱，隨時有回檔風險。"
            elif vol_ratio < 0.8 and abs(slope) < 0.05:
                icon, style, status = "💤", "💤", "【縮量整理】市場觀望，暫無攻擊動能。"
            elif close <= buy_price * 1.02 and slope > -0.1:
                icon, style, status = "✅", "✅", "【買入訊號】回測支撐區且趨勢止穩，適合佈局。"
            elif close <= t_sup:
                icon, style, status = "☢️", "☢️", "【停損警示】擊穿關鍵支撐，請保護資金安全。"
            else:
                icon, style, status = "🔎", "🔎", "【正常整理】於支撐與壓力之間穩定波動。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name}({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(t_press, 2),
                "vol": round(vol_ratio, 2), "slope": f"{slope:.2f}%", "diag": status
            })
            news_sidebar[name] = get_google_news(name)
        except: pass

# 顯示結果
for d in data_list:
    st.markdown(f"""
    <div class="{d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 1.2em; font-weight: bold;">{d['icon']} {d['name']} | 現價: {d['price']}</span>
            <span>量比: {d['vol']} | 斜率: {d['slope']}</span>
        </div>
        <div style="margin-top: 10px;">
            <b>智慧診斷：</b> {d['diag']} | 
            建議買入: <span style="color:green; font-weight:bold;">{d['buy']}</span> | 
            建議賣出: <span style="color:red; font-weight:bold;">{d['sell']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞
for name, news in news_sidebar.items():
    if news:
        with st.sidebar.expander(f"📰 {name} 新聞"):
            for n in news: st.markdown(n)

# 自動重新整理
time.sleep(60)
st.rerun()
