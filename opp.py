import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. 頁面配置：設置寬螢幕
st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# 2. CSS 注入：確保表格美觀並解決標籤外露
st.markdown("""
    <style>
    /* 強制寬度 */
    .main .block-container { max-width: 98% !important; padding-top: 1.5rem; }
    
    /* 表格基礎樣式 */
    table { width: 100%; border-collapse: collapse; margin-top: 10px; font-family: sans-serif; }
    th { background-color: #212529 !important; color: white !important; text-align: center !important; font-size: 0.9em !important; padding: 12px !important; border: 1px solid #343a40 !important; }
    td { text-align: center !important; vertical-align: middle !important; border: 1px solid #dee2e6 !important; padding: 8px !important; background: white; }
    
    /* 買入/停利價格垂直排列區塊 */
    .price-container { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
    .buy-text { color: #198754; font-weight: 800; font-size: 1.15em; }
    .sell-text { color: #d32f2f; font-weight: 800; font-size: 1.15em; border-top: 1px dashed #bbb; padding-top: 4px; width: 90px; }
    
    /* 診斷建議文字 */
    .diag-text { text-align: left !important; min-width: 420px; padding: 10px !important; line-height: 1.5; font-size: 0.95em; }
    
    /* 倒數計時器 */
    .timer-box { color: #e65100; font-weight: bold; font-size: 1.3em; text-align: right; border: 2px solid #e65100; padding: 5px 15px; border-radius: 8px; display: inline-block; }
    
    /* 燈號背景色 */
    .row-alert { background-color: #fff3e0 !important; }   /* 橙色：警告 */
    .row-success { background-color: #e8f5e9 !important; } /* 綠色：買入 */
    .row-info { background-color: #e3f2fd !important; }    /* 藍色：停利 */
    .row-danger { background-color: #ffebee !important; }  /* 紅色：停損 */
    </style>
    """, unsafe_allow_html=True)

# 追蹤名單
tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", 
    "3481.TW": "群創", "2330.TW": "台積電", "NVDA": "輝達"
}

def get_chip_floor(df):
    try:
        data = df.tail(120)
        v_hist = np.histogram(data['Close'], bins=10, weights=data['Volume'])
        idx = np.argmax(v_hist[0])
        return (v_hist[1][idx] + v_hist[1][idx+1]) / 2
    except: return 0

# 頂部欄位
c1, c2 = st.columns([3, 1])
with c1: st.title("🚀 半導體「大戶動向」戰情室")
with c2: timer_placeholder = st.empty()

results = []
with st.spinner('同步數據中...'):
    for ticker, name in tickers.items():
        try:
            s = yf.Ticker(ticker)
            df = s.history(period="1y")
            if df.empty: continue
            
            curr = df['Close'].iloc[-1]
            m20 = df['Close'].rolling(20).mean().iloc[-1]
            s20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 關鍵價位
            tp_price = m20 + (2 * s20)   # 停利價格
            supp_tech = m20 - (2 * s20)  # 技術支撐
            floor_chip = get_chip_floor(df) # 籌碼地板
            buy_suggest = (supp_tech + floor_chip) / 2 # 建議買入
            stop_profit = df['High'].tail(5).max() * 0.97 # 停利防線
            
            v_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / curr) * 100

            # 邏輯判定
            style, icon, note = "", "🔎", f"於 {supp_tech:.2f} 支撐與 {tp_price:.2f} 壓力之間震盪。"
            if v_ratio > 2.0 and abs(slope) < 0.1: 
                style, icon, note = "row-alert", "🚨", "🚨 【大戶倒貨】高檔爆量不漲，籌碼換手，建議減碼。"
            elif curr >= tp_price * 0.98: 
                style, icon, note = "row-info", "⚠️", f"⚠️ 【分批停利】接近停利點 {tp_price:.2f}，建議分批獲利。"
            elif curr <= buy_suggest * 1.02: 
                style, icon, note = "row-success", "✅", f"✅ 【買入訊號】回測支撐區 {buy_suggest:.2f}，適合佈局。"
            elif curr < supp_tech:
                style, icon, note = "row-danger", "☢️", f"☢️ 【破位警示】跌穿技術支撐 {supp_tech:.2f}，請嚴格執行停損。"

            results.append({
                "icon": icon, "style": style, "name": f"{name}({ticker})", "price": f"{curr:.2f}",
                "buy": f"{buy_suggest:.2f}", "sell": f"{tp_price:.2f}", "sup": f"{supp_tech:.2f}",
                "floor": f"{floor_chip:.2f}", "stop": f"{stop_profit:.2f}", "vol": f"{v_ratio:.2f}",
                "slope": f"{slope:.2f}%", "diag": note
            })
        except: pass

# --- 核心：構建完整的 HTML 表格字串 ---
table_html = """
<table>
    <thead>
        <tr>
            <th>燈號</th><th>股票名稱</th><th>目前現價</th>
            <th style="background-color: #fff3e0 !important; color: #e65100 !important;">💡 買入 / 停利點</th>
            <th>技術支撐</th><th>籌碼地板</th><th>停利防線</th><th>量比</th><th>斜率</th><th>📊 智慧診斷操作建議</th>
        </tr>
    </thead>
    <tbody>
"""

for r in results:
    table_html += f"""
    <tr class="{r['style']}">
        <td style="font-size:1.7em;">{r['icon']}</td>
        <td><b>{r['name']}</b></td>
        <td style="font-size:1.3em; font-family:monospace;"><b>{r['price']}</b></td>
        <td>
            <div class="price-container">
                <div class="buy-text">進：{r['buy']}</div>
                <div class="sell-text">利：{r['sell']}</div>
            </div>
        </td>
        <td>{r['sup']}</td><td>{r['floor']}</td><td>{r['stop']}</td>
        <td>{r['vol']}</td><td>{r['slope']}</td>
        <td class="diag-text"><b>{r['diag']}</b></td>
    </tr>
    """
table_html += "</tbody></table>"

# 渲染表格
st.markdown(table_html, unsafe_allow_html=True)

# 倒數計時與自動重整
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-box'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
