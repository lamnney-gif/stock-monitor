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
st.set_page_config(page_title="半導體大戶戰情室-深度動態版", layout="wide")

# 2. 注入自定義 CSS (保持原本風格並微調)
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
    </style>
    """, unsafe_allow_html=True)

# 核心追蹤清單
tickers = {
    "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "INTC": "英特爾"
}

def get_enhanced_support(df):
    try:
        # 修正：縮短至 60 天，更貼近近期籌碼重心
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=12, weights=recent_df['Volume'])
        chip_floor = (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
        # 結合 60 日均線（季線）作為大戶防線
        ma60 = df['Close'].rolling(60).mean().iloc[-1]
        return (chip_floor + ma60) / 2
    except: return df['Close'].mean()

def calculate_atr_limit(df, periods=14):
    # 計算 ATR 動態上限 (防止超漲噴發時太早賣)
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(periods).mean().iloc[-1]
    return atr

def get_google_news(keyword):
    news = []
    try:
        url = f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

# 標題區
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 半導體「大戶戰情室」- 2026 深度防守版")
with col_r: timer_placeholder = st.empty()

data_list = []
news_dict = {}

with st.spinner('計算動態 ATR 與籌碼重心...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            # --- 指標運算 ---
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 技術支撐 & 壓力 (布林帶概念)
            tech_sup = ma20 - (2 * std20)
            tech_press = ma20 + (2 * std20)
            
            # 動態上限 (ATR 2.5倍波幅)
            atr = calculate_atr_limit(df)
            upper_limit = close + (1.5 * atr) 
            
            # 籌碼與綜合買點
            chip_floor = get_enhanced_support(df)
            buy_price = (tech_sup + chip_floor) / 2 
            
            # 乖離與趨勢斜率
            bias = ((close - ma20) / ma20) * 100
            y_data = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # 基本面與籌碼面
            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            
            # --- 診斷邏輯升級 ---
            if vol_ratio > 1.8 and slope < -0.05:
                icon, style, status = "🚨", "🚨", "【大戶出貨】量增價跌且斜率轉弱，主力正在撤退，請務必減碼。"
            elif close >= tech_press * 0.98:
                icon, style, status = "⚠️", "⚠️", f"【過熱預警】接近壓力位 {tech_press:.2f}。若未帶量突破，建議分批獲利。"
            elif close <= buy_price * 1.02 and slope > -0.1:
                icon, style, status = "✅", "✅", f"【防守買點】位於籌碼支撐 {chip_floor:.2f} 附近，適合左側分批進場。"
            elif close < tech_sup:
                icon, style, status = "☢️", "☢️", "【破位重挫】跌穿關鍵技術支撐，趨勢已壞，嚴格執行停損。"
            else:
                icon, style, status = "🔎", "🔎", "【區間整理】目前無明確方向，建議觀察支撐與上限之間波動。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(tech_press, 2), "upper": round(upper_limit, 2),
                "pe": pe_val, "vol": round(vol_ratio, 2), "diag": status, "inst": f"{inst_pct:.1f}%", 
                "bias": round(bias, 2), "floor": round(chip_floor, 2)
            })
            news_dict[name] = get_google_news(name)
        except Exception as e:
            st.error(f"Error processing {ticker}: {e}")

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between;">
            <div>
                <span style="font-size: 1.5em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 1.8em; margin-left: 15px; font-family: monospace;">${d['price']}</span>
                <div style="color: #666; font-size: 0.9em; margin-top:5px;">乖離率: {d['bias']}% | 量比: {d['vol']}x</div>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">預估 PE: {d['pe']}</span>
                <span class="metric-tag">法人: {d['inst']}</span>
            </div>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 20px;">
            <div style="flex: 2;">
                <b>💡 戰情診斷：</b><br>{d['diag']}
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.4); padding: 10px; border-radius: 8px;">
                <b>📊 操盤建議位：</b><br>
                🟢 建議買入：<span style="color:#2e7d32; font-weight:bold;">{d['buy']}</span><br>
                🔴 壓力停利：<span style="color:#c62828; font-weight:bold;">{d['sell']}</span><br>
                🚀 <span style="color:#1565c0; font-weight:bold;">噴發上限：{d['upper']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞
st.sidebar.title("📰 產業即時情報")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name} 相關"):
            for n in news: st.markdown(n)

# 倒數 60 秒刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 後數據重載</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
