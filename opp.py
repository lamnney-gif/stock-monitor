import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
from sklearn.linear_model import LinearRegression

# 1. 頁面設置
st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# 2. 定義 CSS 與 HTML 模板 (確保垂直排列與寬大螢幕)
def generate_html(results, last_update):
    table_rows = ""
    for r in results:
        table_rows += f"""
        <tr class="{r['style']}">
            <td style="font-size:24px; text-align:center;">{r['icon']}</td>
            <td style="font-weight:bold; text-align:center;">{r['name']}</td>
            <td style="font-size:18px; font-family:monospace; font-weight:bold; text-align:center;">{r['price']}</td>
            <td>
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <div style="color:#198754; font-weight:bold; font-size:1.1em;">進：{r['buy']}</div>
                    <div style="color:#d32f2f; font-weight:bold; font-size:1.1em; border-top:1px dashed #bbb; margin-top:4px; padding-top:4px; width:90px; text-align:center;">利：{r['sell']}</div>
                </div>
            </td>
            <td style="text-align:center;">{r['sup']}</td>
            <td style="text-align:center;">{r['floor']}</td>
            <td style="text-align:center;">{r['stop']}</td>
            <td style="text-align:center;">{r['vol']}x</td>
            <td style="text-align:center;">{r['slope']}</td>
            <td style="padding:10px; line-height:1.5;"><b>{r['diag']}</b></td>
        </tr>
        """

    return f"""
    <style>
        table {{ width: 100%; border-collapse: collapse; font-family: "Microsoft JhengHei", sans-serif; }}
        th {{ background-color: #212529; color: white; padding: 12px; font-size: 14px; border: 1px solid #444; }}
        td {{ border: 1px solid #dee2e6; padding: 8px; font-size: 14px; }}
        .row-alert {{ background-color: #fff3e0; }}
        .row-success {{ background-color: #e8f5e9; }}
        .row-info {{ background-color: #e3f2fd; }}
        .row-danger {{ background-color: #ffebee; }}
    </style>
    <table>
        <thead>
            <tr>
                <th>燈號</th><th>股票名稱</th><th>目前現價</th>
                <th style="background-color: #fff3e0; color: #e65100;">💡 買入 / 停利點</th>
                <th>技術支撐</th><th>籌碼地板</th><th>停利防線</th><th>量比</th><th>斜率</th><th>📊 智慧診斷建議</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    <div style="text-align:right; color:#666; font-size:12px; margin-top:10px;">最後更新：{last_update}</div>
    """

# --- 主程式邏輯 ---
st.title("🚀 半導體「大戶動向」戰情室")
timer_placeholder = st.sidebar.empty()

# 追蹤清單
tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", 
    "3481.TW": "群創", "2330.TW": "台積電", "NVDA": "輝達"
}

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
            
            tp_price = m20 + (2 * s20)
            supp_tech = m20 - (2 * s20)
            
            # 籌碼地板
            v_hist = np.histogram(df.tail(120)['Close'], bins=10, weights=df.tail(120)['Volume'])
            idx = np.argmax(v_hist[0])
            floor_chip = (v_hist[1][idx] + v_hist[1][idx+1]) / 2
            
            buy_suggest = (supp_tech + floor_chip) / 2
            stop_profit = df['High'].tail(5).max() * 0.97
            vol_r = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / curr) * 100

            style, icon, note = "", "🔎", f"於 {supp_tech:.2f} 支撐與 {tp_price:.2f} 壓力之間震盪。"
            if vol_r > 2.0 and abs(slope) < 0.1: style, icon, note = "row-alert", "🚨", "🚨 【大戶倒貨】高檔爆量不漲，建議減碼。"
            elif curr >= tp_price * 0.98: style, icon, note = "row-info", "⚠️", f"⚠️ 【分批停利】接近停利點 {tp_price:.2f}。"
            elif curr <= buy_suggest * 1.02: style, icon, note = "row-success", "✅", f"✅ 【買入訊號】回測支撐區 {buy_suggest:.2f}。"
            elif curr < supp_tech: style, icon, note = "row-danger", "☢️", f"☢️ 【破位警示】跌穿技術支撐 {supp_tech:.2f}。"

            results.append({
                "icon": icon, "style": style, "name": f"{name}({ticker})", "price": f"{curr:.2f}",
                "buy": f"{buy_suggest:.2f}", "sell": f"{tp_price:.2f}", "sup": f"{supp_tech:.2f}",
                "floor": f"{floor_chip:.2f}", "stop": f"{stop_profit:.2f}", "vol": f"{vol_r:.2f}",
                "slope": f"{slope:.2f}%", "diag": note
            })
        except: pass

# 渲染 HTML 組件 (設置高度為 800px 確保不被切掉)
last_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
components.html(generate_html(results, last_time), height=800, scrolling=True)

# 倒數計時與重整
for i in range(60, 0, -1):
    timer_placeholder.metric("🔄 刷新倒數", f"{i}s")
    time.sleep(1)

st.rerun()
