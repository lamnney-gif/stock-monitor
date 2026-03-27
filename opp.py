import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置：強制寬螢幕模式
st.set_page_config(page_title="半導體「大戶動向」戰情室", layout="wide")

# 2. 注入自定義 CSS (完全還原你的寬螢幕表格風格)
st.markdown("""
    <style>
    .main .block-container { max-width: 95% !important; padding-top: 2rem; }
    th { background-color: #212529 !important; color: white !important; text-align: center !important; font-size: 0.85em !important; vertical-align: middle !important; }
    td { text-align: center !important; vertical-align: middle !important; font-size: 0.9em !important; border: 1px solid #dee2e6 !important; height: 80px; }
    
    /* 關鍵價格區塊：買入與停利對齊 */
    .price-box { display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 5px; }
    .buy-tag { color: #198754; font-weight: bold; font-size: 1.15em; }
    .sell-tag { color: #d32f2f; font-weight: bold; font-size: 1.15em; border-top: 1px dashed #bbb; padding-top: 4px; width: 80%; }
    
    /* 智慧診斷單元格 */
    .diag-cell { text-align: left !important; min-width: 450px; padding: 12px !important; line-height: 1.5; background-color: #fdfdfd; white-space: normal !important; }
    
    /* 倒數計時器樣式 */
    .timer-text { color: #ff5722; font-weight: bold; font-size: 1.4em; text-align: right; }
    
    /* 燈號背景色 */
    .bg-alert { background-color: #ffccbc !important; } /* 大戶倒貨 */
    .bg-success { background-color: #d1e7dd !important; } /* 買入訊號 */
    .bg-danger { background-color: #f8d7da !important; } /* 破位停損 */
    .bg-info { background-color: #cff4fc !important; } /* 分批停利 */
    </style>
    """, unsafe_allow_html=True)

# 核心追蹤清單
tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", 
    "3481.TW": "群創", "2330.TW": "台積電", "NVDA": "輝達"
}

def get_volume_support(df):
    """計算籌碼地板 (120日大戶成交密集區)"""
    try:
        recent_df = df.tail(120)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        idx = np.argmax(v_hist[0])
        return (v_hist[1][idx] + v_hist[1][idx+1]) / 2
    except: return 0

# --- 介面頂部 ---
col_h, col_t = st.columns([3, 1])
with col_h: 
    st.title("🚀 半導體「大戶動向」深度戰情室")
with col_t: 
    timer_placeholder = st.empty()

# --- 數據運算核心 ---
results = []
with st.spinner('正在分析全球半導體籌碼防線...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 關鍵位計算
            tech_press = ma20 + (2 * std20)    # 停利價格 (壓力)
            tech_sup = ma20 - (2 * std20)      # 技術支撐
            chip_floor = get_volume_support(df) # 籌碼地板
            suggested_buy = (tech_sup + chip_floor) / 2 # 建議買入價
            stop_defense = df['High'].tail(5).max() * 0.97 # 停利防線 (5日高點回測)
            
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            y_val = df['Close'].tail(10).values
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_val.reshape(-1,1)).coef_[0][0] / y_val.mean()) * 100
            bias = ((close - ma20) / ma20) * 100

            # 智慧燈號與背景邏輯
            cls = ""; icon = "🔎"; diag = f"目前於支撐 {tech_sup:.2f} 與壓力 {tech_press:.2f} 之間穩定波動，量能平穩。"
            
            if vol_ratio > 2.0 and abs(slope) < 0.1:
                cls = "bg-alert"; icon = "🚨"; diag = "🚨 【大戶倒貨】爆量但不漲，高檔籌碼換手跡象明顯，建議分批減碼。"
            elif close >= tech_press * 0.98:
                cls = "bg-info"; icon = "⚠️"; diag = f"⚠️ 【分批停利】已達停利目標 {tech_press:.2f}。乖離率 {bias:.1f}%，隨時有回檔風險。"
            elif close <= suggested_buy * 1.02:
                cls = "bg-success"; icon = "✅"; diag = f"✅ 【買入訊號】回測支撐區 {suggested_buy:.2f}。大戶成本有守，適合分批佈局。"
            elif close <= tech_sup:
                cls = "bg-danger"; icon = "☢️"; diag = f"☢️ 【停損警示】跌破關鍵技術位 {tech_sup:.2f}。趨勢轉空，請務必保命停損。"

            results.append({
                "light": icon, "cls": cls, "name": f"{name}({ticker})", "price": f"{close:.2f}",
                "buy": f"{suggested_buy:.2f}", "sell": f"{tech_press:.2f}", "sup": f"{tech_sup:.2f}",
                "floor": f"{chip_floor:.2f}", "stop": f"{stop_defense:.2f}", "vol": f"{vol_ratio:.2f}",
                "slope": f"{slope:.2f}%", "diag": diag, "bias": f"{bias:.1f}%"
            })
        except: pass

# --- 生成大寬屏 HTML 表格 ---
html_table = """
<table class="table">
    <thead>
        <tr>
            <th>燈號</th><th>股票</th><th>目前現價</th>
            <th>💡 買入 / 停利點</th>
            <th>技術支撐</th><th>籌碼地板</th><th>停利防線</th>
            <th>乖離率</th><th>量比</th><th>斜率</th>
            <th>📊 智慧診斷與操作建議</th>
        </tr>
    </thead>
    <tbody>
"""

for r in results:
    html_table += f"""
    <tr class="{r['cls']}">
        <td style="font-size:1.6em;">{r['light']}</td>
        <td><b>{r['name']}</b></td>
        <td style="font-size:1.3em; font-family:monospace;"><b>{r['price']}</b></td>
        <td>
            <div class="price-box">
                <span class="buy-tag">進：{r['buy']}</span>
                <span class="sell-tag">出：{r['sell']}</span>
            </div>
        </td>
        <td>{r['sup']}</td><td>{r['floor']}</td><td>{r['stop']}</td>
        <td>{r['bias']}</td><td>{r['vol']}x</td><td>{r['slope']}</td>
        <td class="diag-cell"><b>{r['diag']}</b></td>
    </tr>
    """
html_table += "</tbody></table>"

st.markdown(html_table, unsafe_allow_html=True)

# --- 側邊欄：備註與新聞 ---
st.sidebar.markdown("### 📘 操作備註")
st.sidebar.info("""
1. **買入點**：技術下軌與大戶成本的平均值。
2. **停利點**：技術上軌壓力位，達標建議減碼。
3. **停利防線**：5日高點回落3%，跌破建議全賣。
""")

# --- 倒數計時與自動重新整理 ---
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-text'>🔄 {i} 秒後自動更新數據</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
