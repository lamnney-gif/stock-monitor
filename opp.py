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
st.set_page_config(page_title="半導體大戶戰情室-深度強化版", layout="wide")

# 2. 注入自定義 CSS (美化卡片與價格對齊)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 3px 3px 12px rgba(0,0,0,0.1); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #d32f2f; }
    .⚠️ { background-color: #fffdf0; border-left: 12px solid #fbc02d; }
    .✅ { background-color: #f0fff4; border-left: 12px solid #388e3c; }
    .☢️ { background-color: #fff0f0; border-left: 12px solid #ff4444; }
    .💤 { background-color: #f8f9fa; border-left: 12px solid #9e9e9e; }
    .🔎 { background-color: #ffffff; border-left: 12px solid #455a64; }
    
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 8px; font-size: 0.85em; font-weight: 600; color: #444; }
    .price-main { font-size: 2.2em; font-family: 'Courier New', monospace; font-weight: bold; color: #212529; }
    .price-sub-info { font-size: 0.9em; color: #666; margin-top: 4px; font-weight: 500; }
    
    /* 關鍵位方框美化 */
    .target-box { 
        background: rgba(255,255,255,0.7); 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #eee; 
        display: flex; 
        flex-direction: column; 
        justify-content: center;
        min-width: 180px;
    }
    .target-item { margin-bottom: 8px; line-height: 1.2; }
    .target-label { font-size: 0.85em; color: #555; font-weight: bold; }
    .target-price-buy { font-size: 1.4em; color: #1b5e20; font-weight: 900; }
    .target-price-sell { font-size: 1.4em; color: #c62828; font-weight: 900; }
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
        idx = np.argmax(v_hist[0])
        return (v_hist[1][idx] + v_hist[1][idx+1]) / 2
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
st.title("🚀 半導體「大戶動向」戰情室")
st.caption(f"數據自動刷新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (每 60 秒刷新一次)")

data_list = []
news_dict = {}

with st.spinner('同步全球籌碼數據中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # --- 關鍵位運算 ---
            tech_sup = ma20 - (2 * std20)
            tech_press = ma20 + (2 * std20)   # 停利價格
            chip_floor = get_volume_support(df)
            buy_price = (tech_sup + chip_floor) / 2
            bias = ((close - ma20) / ma20) * 100
            
            y_data = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100

            # 診斷邏輯
            if vol_ratio > 2.2 and abs(slope) < 0.1:
                icon, style, status = "🚨", "🚨", "【大戶出貨】爆量不漲。此為典型高檔換手訊號，風險極高，建議減碼。"
            elif close >= tech_press * 0.98:
                icon, style, status = "⚠️", "⚠️", f"【分批停利】已達壓力位 {tech_press:.2f}。過熱訊號明顯，建議獲利了結。"
            elif close <= buy_price * 1.03 and slope > -0.1:
                icon, style, status = "✅", "✅", f"【黃金買點】回測籌碼地板 {chip_floor:.2f}。支撐穩固，適合分批佈局。"
            elif close <= tech_sup:
                icon, style, status = "☢️", "☢️", "【破位重挫】擊穿技術下軌。慣性已破，請嚴格執行停損。"
            else:
                icon, style, status = "🔎", "🔎", "【正常波動】於區間內健康整理，量能穩定，持股續抱。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": f"{close:.2f}",
                "buy": f"{buy_price:.2f}", "sell": f"{tech_press:.2f}", "pe": pe_val,
                "vol": f"{vol_ratio:.2f}", "diag": status, "inst": f"{inst_pct:.1f}%",
                "sup": f"{tech_sup:.2f}", "floor": f"{chip_floor:.2f}", "bias": f"{bias:.1f}%"
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- 卡片渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 2;">
                <span style="font-size: 1.5em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <div class="price-main">${d['price']}</div>
                <div class="price-sub-info">乖離率: {d['bias']} | 量比: {d['vol']}x | 法人持股: {d['inst']}</div>
            </div>
            <div class="target-box" style="flex: 1;">
                <div class="target-item">
                    <div class="target-label">💡 建議買入價</div>
                    <div class="target-price-buy">{d['buy']}</div>
                </div>
                <div class="target-item" style="border-top: 1px dashed #ccc; padding-top: 8px;">
                    <div class="target-label">🎯 建議停利價</div>
                    <div class="target-price-sell">{d['sell']}</div>
                </div>
            </div>
        </div>
        <div style="margin-top: 15px; padding: 12px; background: rgba(255,255,255,0.4); border-radius: 8px;">
            <b style="color: #333;">📊 診斷建議：</b> {d['diag']}
            <div style="font-size: 0.8em; color: #777; margin-top: 5px;">
                (參考數據 - 技術支撐: {d['sup']} | 籌碼地板: {d['floor']} | 預估PE: {d['pe']})
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

# 每分鐘刷新
time.sleep(60)
st.rerun()
