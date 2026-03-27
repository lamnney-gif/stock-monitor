import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 頁面配置
st.set_page_config(page_title="半導體大戶全數據戰情室", layout="wide")

# 強大 CSS 注入：美化卡片與表格
st.markdown("""
    <style>
    .reportview-container .main .block-container { max-width: 95%; }
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .🚨 { background-color: #ffebee; border-left: 10px solid #d32f2f; color: #b71c1c; }
    .⚠️ { background-color: #e1f5fe; border-left: 10px solid #0288d1; color: #01579b; }
    .✅ { background-color: #e8f5e9; border-left: 10px solid #388e3c; color: #1b5e20; }
    .☢️ { background-color: #fff3e0; border-left: 10px solid #f57c00; color: #e65100; }
    .💤 { background-color: #f5f5f5; border-left: 10px solid #9e9e9e; color: #424242; }
    .🔎 { background-color: #ffffff; border-left: 10px solid #455a64; color: #263238; }
    .metric-box { display: inline-block; padding: 2px 8px; background: rgba(0,0,0,0.05); border-radius: 4px; margin-right: 10px; font-family: monospace; }
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

# 標題欄
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🚀 半導體「大戶動向」全數據戰情室")
with col_t2:
    st.write(f"⏱️ 更新時間：{datetime.now().strftime('%H:%M:%S')}")
    if st.button("🔄 手動強制刷新"): st.rerun()

data_list = []
news_sidebar = {}

with st.spinner('正在同步全球籌碼與技術面數據...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            # --- 價格運算 ---
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            t_sup = ma20 - (2 * std20)
            t_press = ma20 + (2 * std20)
            c_floor = get_volume_support(df)
            buy_price = (t_sup + c_floor) / 2
            
            # --- 技術指標 ---
            y = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y.reshape(-1,1)).coef_[0][0] / y.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # --- 籌碼數據 (從 stock.info 抓取) ---
            info = stock.info
            pe = info.get('forwardPE', "N/A")
            inst_own = info.get('heldPercentInstitutions', 0) * 100
            insider_own = info.get('heldPercentInsiders', 0) * 100

            # --- 智慧燈號邏輯 ---
            if vol_ratio > 2.0 and abs(slope) < 0.1 and close > ma20:
                icon, style, status = "🚨", "🚨", f"🚨 【大戶倒貨】爆量 {vol_ratio:.1f} 倍但股價滯漲。疑似高檔出貨，建議大幅減碼。"
            elif close >= t_press * 0.98:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】股價觸及壓力位 {t_press:.2f}。短線過熱，建議收割利潤。"
            elif vol_ratio < 0.8 and abs(slope) < 0.05:
                icon, style, status = "💤", "💤", "💤 【縮量整理】市場觀望，動能不足，建議保留現金等待方向。"
            elif close <= buy_price * 1.02 and slope > -0.1:
                icon, style, status = "✅", "✅", f"✅ 【買入訊號】回測黃金買點 {buy_price:.2f}。支撐強勁，適合佈局。"
            elif close <= t_sup:
                icon, style, status = "☢️", "☢️", f"☢️ 【停損警示】擊穿技術支撐 {t_sup:.2f}。趨勢轉弱，請嚴格執行停損。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【正常整理】於區間內波動。斜率 {slope:.2f}%，量能穩定。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name}({ticker})", "price": round(close, 2),
                "buy": round(buy_price, 2), "sell": round(t_press, 2), "floor": round(c_floor, 2),
                "vol": round(vol_ratio, 2), "slope": f"{slope:.2f}%", "diag": status,
                "pe": pe, "inst": f"{inst_own:.1f}%", "insider": f"{insider_own:.1f}%"
            })
            news_sidebar[name] = get_google_news(name)
        except: pass

# --- 渲染卡片介面 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="font-size: 1.5em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 1.8em; margin-left: 15px; font-family: monospace;">{d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-box">預測本益比: {d['pe']}</span>
                <span class="metric-box">機構持股: {d['inst']}</span>
                <span class="metric-box">內部持股: {d['insider']}</span>
            </div>
        </div>
        <hr style="margin: 10px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between;">
            <div style="flex: 2;">
                <b>智慧診斷：</b> {d['diag']}
            </div>
            <div style="flex: 1; text-align: right; font-size: 0.9em;">
                量比: <b>{d['vol']}</b> | 斜率: <b>{d['slope']}</b><br>
                建議買入: <span style="color:green; font-weight:bold;">{d['buy']}</span> | 
                建議賣出: <span style="color:red; font-weight:bold;">{d['sell']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞與說明
st.sidebar.title("📘 戰情室說明")
st.sidebar.info("本系統每 60 秒自動抓取 Yahoo Finance 最新數據。包含 120 日籌碼分佈計算之地板價。")
for name, news in news_sidebar.items():
    if news:
        with st.sidebar.expander(f"📰 {name} 即時新聞"):
            for n in news: st.markdown(n)

# 自動重新整理邏輯
time.sleep(60)
st.rerun()
