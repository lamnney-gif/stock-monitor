import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. 頁面配置
st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# 2. 強制 CSS 注入 (確保買入與停利價格垂直並排)
st.markdown("""
    <style>
    .reportview-container .main .block-container { max-width: 95% !important; }
    th { background-color: #212529 !important; color: white !important; text-align: center !important; font-size: 0.9em !important; }
    td { text-align: center !important; vertical-align: middle !important; border: 1px solid #dee2e6 !important; height: 110px !important; }
    
    /* 關鍵欄位樣式 */
    .price-cell { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 8px; }
    .buy-label { color: #198754; font-weight: 800; font-size: 1.25em; }
    .sell-label { color: #d32f2f; font-weight: 800; font-size: 1.25em; border-top: 2px solid #ffcdd2; padding-top: 6px; width: 85%; }
    
    .diag-box { text-align: left !important; min-width: 450px; padding: 15px !important; line-height: 1.6; }
    .timer-display { color: #e65100; font-weight: bold; font-size: 1.4em; text-align: right; border: 2px solid #e65100; padding: 5px 15px; border-radius: 8px; }
    
    /* 背景顏色 */
    .row-alert { background-color: #fff3e0 !important; }
    .row-success { background-color: #e8f5e9 !important; }
    .row-info { background-color: #e3f2fd !important; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", 
    "3481.TW": "群創", "2330.TW": "台積電", "NVDA": "輝達"
}

def get_vol_floor(df):
    try:
        v_hist = np.histogram(df.tail(120)['Close'], bins=10, weights=df.tail(120)['Volume'])
        idx = np.argmax(v_hist[0])
        return (v_hist[1][idx] + v_hist[1][idx+1]) / 2
    except: return 0

# 標題與計時器
c1, c2 = st.columns([3, 1])
with c1: st.title("🚀 半導體「大戶動向」戰情室")
with c2: timer_spot = st.empty()

results = []
with st.spinner('同步全球數據中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 計算核心數值
            target_sell = ma20 + (2 * std20)    # 停利價格 (壓力)
            tech_sup = ma20 - (2 * std20)      # 技術支撐
            floor = get_vol_floor(df)          # 籌碼地板
            buy_in = (tech_sup + floor) / 2    # 建議買入價
            stop_line = df['High'].tail(5).max() * 0.97 # 停利防線
            
            vol_r = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close) * 100

            # 狀態判定
            bg, icon, msg = "", "🔎", f"股價於 {tech_sup:.2f} 支撐與 {target_sell:.2f} 壓力之間震盪。"
            if vol_r > 2.0 and abs(slope) < 0.1: bg, icon, msg = "row-alert", "🚨", "🚨 【大戶倒貨】高檔爆量不漲，建議分批減碼。"
            elif close >= target_sell * 0.98: bg, icon, msg = "row-info", "⚠️", f"⚠️ 【分批停利】接近停利點 {target_sell:.2f}，建議入袋為安。"
            elif close <= buy_in * 1.02: bg, icon, msg = "row-success", "✅", f"✅ 【買入訊號】回測支撐區 {buy_in:.2f}，適合分批佈局。"

            results.append({
                "light": icon, "bg": bg, "name": f"{name}({ticker})", "price": f"{close:.2f}",
                "buy": f"{buy_in:.2f}", "sell": f"{target_sell:.2f}", "sup": f"{tech_sup:.2f}",
                "floor": f"{floor:.2f}", "stop": f"{stop_line:.2f}", "vol": f"{vol_r:.2f}",
                "slope": f"{slope:.2f}%", "diag": msg
            })
        except: pass

# 繪製表格
html = """
<table class="table">
    <thead>
        <tr>
            <th>燈號</th><th>股票</th><th>現價</th>
            <th style="background-color: #fff3e0 !important; color: #e65100 !important;">💡 買入 / 停利點</th>
            <th>技術支撐</th><th>籌碼地板</th><th>停利防線</th><th>量比</th><th>斜率</th><th>智慧診斷</th>
        </tr>
    </thead>
    <tbody>
"""
for r in results:
    html += f"""
    <tr class="{r['bg']}">
        <td style="font-size:1.8em;">{r['light']}</td>
        <td><b>{r['name']}</b></td>
        <td style="font-size:1.4em; font-family:monospace;"><b>{r['price']}</b></td>
        <td>
            <div class="price-cell">
                <div class="buy-label">進：{r['buy']}</div>
                <div class="sell-label">利：{r['sell']}</div>
            </div>
        </td>
        <td>{r['sup']}</td><td>{r['floor']}</td><td>{r['stop']}</td>
        <td>{r['vol']}</td><td>{r['slope']}</td>
        <td class="diag-box"><b>{r['diag']}</b></td>
    </tr>
    """
html += "</tbody></table>"

st.markdown(html, unsafe_allow_html=True)

# 倒數計時與強制刷新
for i in range(60, 0, -1):
    timer_spot.markdown(f"<div class='timer-display'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
