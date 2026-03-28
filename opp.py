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
st.set_page_config(page_title="半導體大戶戰情室-邏輯修正版", layout="wide")

# 2. CSS 樣式 (維持專業)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    </style>
    """, unsafe_allow_html=True)

tickers = {"NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "INTC": "英特爾"}

def get_volume_support(df):
    try:
        recent_df = df.tail(60) # 縮短至 60 天，反應更靈敏
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

st.title("🖥️ 半導體大戶戰情室 (邏輯即時校準版)")
timer_placeholder = st.empty()
data_list = []

with st.spinner('AI 正在校對現實股價與支撐位...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)
            local_low_3d = df['Low'].tail(3).min() # 3日低點
            local_low_20d = df['Low'].tail(20).min()
            chip_floor = get_volume_support(df)
            
            # 趨勢斜率
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100

            # --- 邏輯修正核心：防止倒掛 ---
            # 1. 基礎建議買點計算
            if slope_pct > 0.6:
                raw_buy = (ma10 * 0.7) + (tech_support * 0.3)
            else:
                raw_buy = (tech_support * 0.4) + (chip_floor * 0.6)
            
            # 2. 強制現實校驗：建議買點不得高於現價
            # 如果現價已經跌破建議買點，買點應自動下移至 3日低點附近
            suggested_buy = min(raw_buy, local_low_3d * 0.99)
            
            # 3. 停損與停利
            stop_loss = min(local_low_20d, suggested_buy) * 0.95
            stop_profit_line = df['High'].tail(5).max() * 0.97

            # --- 診斷報告 (修正判斷順序) ---
            if close_val < stop_loss:
                icon, style, status = "☢️", "☢️", f"☢️ 【支撐瓦解】現價 {close_val:.2f} 已跌破所有防禦區。目前下墜中，嚴禁接刀，觀望至止跌訊號出現。"
            elif bias > 20:
                icon, style, status = "🚨", "🚨", f"🚨 【瘋狂超漲】乖離率 {bias:.1f}% 過高。目前追入風險極大，建議等回測 {suggested_buy:.2f}。"
            elif slope_pct < -0.2 and close_val < tech_support:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【空頭修正】股價處於破位狀態。原建議買點失效，新防禦位參考 {suggested_buy:.2f}。"
            elif close_val <= suggested_buy * 1.03 and slope_pct > -0.1:
                icon, style, status = "✅", "✅", f"✅ 【買入訊號】回測支撐區且斜率趨於平緩，具備布局價值。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【區間整理】股價在 {suggested_buy:.2f} 支撐與 {tech_pressure:.2f} 壓力間震盪。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), "stop_line": round(stop_profit_line, 2),
                "stop_loss": round(stop_loss, 2), "diag": status, "slope": round(slope_pct, 2), "chip_floor": round(chip_floor, 2)
            })
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between;">
            <div><b style="font-size: 1.5em;">{d['icon']} {d['name']}</b> <span style="font-size: 2em; margin-left: 20px;">${d['price']}</span></div>
            <div style="text-align: right;"><span class="metric-tag">斜率: {d['slope']}%</span></div>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
            <div>
                <b>💡 戰情診斷：</b><br>{d['diag']}
                <div class="defense-box">
                    🛡️ <b>防禦：</b> 停利: {d['stop_line']} | <span style="color:red;">絕對停損: {d['stop_loss']}</span> | 歷史籌碼: {d['chip_floor']}
                </div>
            </div>
            <div style="background: white; padding: 12px; border-radius: 12px; border: 1px solid #ddd;">
                <b>📊 建議參考位：</b><br>
                🟢 建議買入: <span style="color:green; font-weight:bold;">{d['buy']}</span><br>
                🎯 建議停利: <span style="color:red; font-weight:bold;">{d['sell']}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 刷新數據")
    time.sleep(1)
st.rerun()
