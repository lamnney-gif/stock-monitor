import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 設置寬螢幕模式 (對應你原本的 1750px 邏輯)
st.set_page_config(page_title="半導體「大戶動向」戰情室", layout="wide")

# 2. 注入你原本的 CSS 樣式 (讓 Streamlit 表格看起來像你的 HTML 版)
st.markdown("""
    <style>
    .reportview-container .main .block-container { max-width: 95%; }
    th { background-color: #212529 !important; color: white !important; text-align: center !important; font-size: 0.85em !important; }
    td { text-align: center !important; vertical-align: middle !important; font-size: 0.9em !important; }
    .diag-cell { text-align: left !important; min-width: 400px; line-height: 1.5; padding: 10px !important; }
    .badge-buy { background-color: #198754; color: white; padding: 3px 6px; border-radius: 4px; font-weight: bold; }
    .badge-sell { background-color: #ffc107; color: black; padding: 3px 6px; border-radius: 4px; font-weight: bold; }
    .timer-text { color: #ff5722; font-weight: bold; font-size: 1.2em; }
    /* 燈號顏色對應 */
    .color-alert-orange { background-color: #ffccbc !important; }
    .table-success { background-color: #d1e7dd !important; }
    .table-danger { background-color: #f8d7da !important; }
    .table-info { background-color: #cff4fc !important; }
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
        max_vol_idx = np.argmax(v_hist[0])
        return (v_hist[1][max_vol_idx] + v_hist[1][max_vol_idx+1]) / 2
    except: return 0

def get_google_news(keyword):
    news_items = ""
    try:
        encoded_key = quote(f"{keyword} 股價 新聞")
        rss_url = f"https://news.google.com/rss/search?q={encoded_key}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:3]:
            news_items += f"• <a href='{entry.link}' target='_blank'>{entry.title}</a><br>"
    except: pass
    return news_items

# --- 頂部標題與計時器 ---
col_head, col_timer = st.columns([4, 1])
with col_head:
    st.title("🚀 半導體「大戶動向」戰情室")
with col_timer:
    timer_place = st.empty()

# --- 數據抓取與處理 ---
results = []
news_html = ""

with st.spinner('正在同步數據...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # --- 關鍵價位 ---
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)   # 這就是停利目標
            chip_floor = get_volume_support(df)
            suggested_buy = (tech_support + chip_floor) / 2
            stop_profit_price = df['High'].tail(5).max() * 0.97 # 停利防線
            
            # 技術指標
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1, 1), y_data.reshape(-1, 1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100
            
            # 籌碼數據
            info = stock.info
            f_pe = info.get('forwardPE', "無")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100
            insider_pct = info.get('heldPercentInsiders', 0) * 100

            # 智慧燈號邏輯
            bg_color = ""
            icon = "🔎"
            if vol_ratio > 2.0 and abs(slope_pct) < 0.1 and close_val > ma20:
                bg_color = "color-alert-orange"; icon = "🚨"
                status = f"🚨 【大戶倒貨】爆量但股價不動。高檔換手訊號，建議減碼。"
            elif close_val >= tech_pressure * 0.98:
                bg_color = "table-info"; icon = "⚠️"
                status = f"⚠️ 【分批停利】逼近停利價 {tech_pressure:.2f}。過熱建議先入袋為安。"
            elif close_val <= suggested_buy * 1.02:
                bg_color = "table-success"; icon = "✅"
                status = f"✅ 【買入訊號】回測支撐區 {suggested_buy:.2f}。適合分批佈局。"
            elif close_val <= tech_support:
                bg_color = "table-danger"; icon = "☢️"
                status = f"☢️ 【停損警示】跌穿支撐 {tech_support:.2f}。趨勢轉空，請保命。"
            else:
                status = f"🔎 【正常整理】於支撐 {tech_support:.2f} 與壓力 {tech_pressure:.2f} 之間波動。"

            results.append({
                "light": icon, "cls": bg_color, "name": f"{name}({ticker})", "price": f"{close_val:.2f}",
                "sup": f"{tech_support:.2f}", "buy": f"{suggested_buy:.2f}", "floor": f"{chip_floor:.2f}",
                "sell": f"{tech_pressure:.2f}", "stop": f"{stop_profit_price:.2f}", "pe": f_pe,
                "inst": f"{inst_pct:.1f}%", "insider": f"{insider_pct:.1f}%", "vol": f"{vol_ratio:.2f}",
                "slope": f"{slope_pct:.2f}%", "diag": status
            })
            news_html += f"<b>{name}:</b><br>{get_google_news(name)}<hr>"
        except: pass

# --- 顯示大表格 ---
df_html = f"""
<table class="table table-bordered">
    <thead>
        <tr>
            <th>燈號</th><th>股票</th><th>現價</th><th>技術支撐</th>
            <th><span class="badge-buy">建議買入</span></th><th>籌碼地板</th>
            <th><span class="badge-sell">停利目標</span></th><th>停利防線</th>
            <th>本益比</th><th>法人</th><th>大戶</th><th>量比</th><th>斜率</th>
            <th>📊 智慧診斷與操作建議</th>
        </tr>
    </thead>
    <tbody>
"""
for r in results:
    df_html += f"""
    <tr class="{r['cls']}">
        <td style="font-size:1.5em;">{r['light']}</td>
        <td><b>{r['name']}</b></td><td>{r['price']}</td><td>{r['sup']}</td>
        <td><b>{r['buy']}</b></td><td>{r['floor']}</td>
        <td><b>{r['sell']}</b></td><td>{r['stop']}</td>
        <td>{r['pe']}</td><td>{r['inst']}</td><td>{r['insider']}</td>
        <td>{r['vol']}</td><td>{r['slope']}</td>
        <td class="diag-cell">{r['diag']}</td>
    </tr>
    """
df_html += "</tbody></table>"

st.markdown(df_html, unsafe_allow_html=True)

# --- 側邊欄新聞 ---
st.sidebar.title("📰 即時新聞")
st.sidebar.markdown(news_html, unsafe_allow_html=True)

# --- 倒數計時與自動刷新 ---
for i in range(60, 0, -1):
    timer_place.markdown(f"<div class='timer-text'>🔄 {i} 秒後自動更新數據</div>", unsafe_allow_html=True)
    time.sleep(1)
st.rerun()
