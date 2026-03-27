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
st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# 2. 樣式美化
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.08); }
    .🚨 { border-left: 12px solid #d32f2f; background-color: #fff5f5; }
    .⚠️ { border-left: 12px solid #fbc02d; background-color: #fffdeb; }
    .✅ { border-left: 12px solid #388e3c; background-color: #f1f8f1; }
    .☢️ { border-left: 12px solid #c2185b; background-color: #fff0f5; }
    .🔎 { border-left: 12px solid #455a64; background-color: #ffffff; }
    .target-price { color: #d32f2f; font-weight: bold; font-size: 1.2em; border: 2px solid #d32f2f; padding: 2px 8px; border-radius: 5px; }
    .support-price { color: #388e3c; font-weight: bold; font-size: 1.2em; border: 2px solid #388e3c; padding: 2px 8px; border-radius: 5px; }
    .timer-box { font-size: 1.5em; color: #ff5722; font-weight: bold; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

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

# 頂部抬頭與倒數
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    st.title("🚀 半導體大戶「停利/支撐」監控站")
with col_t2:
    timer_placeholder = st.empty()

data_list = []
with st.spinner('數據同步中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # --- 關鍵價位 (你要求的數據都在這) ---
            target_sell = ma20 + (2 * std20)    # 停利價格 (壓力)
            tech_sup = ma20 - (2 * std20)      # 技術支撐
            chip_floor = get_volume_support(df) # 籌碼地板
            buy_price = (tech_sup + chip_floor) / 2 # 建議買入價
            
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # 診斷邏輯
            if close >= target_sell * 0.98:
                icon, style, diag = "⚠️", "⚠️", f"已達【停利目標】{target_sell:.2f} 附近，建議分批獲利了結。"
            elif close <= buy_price * 1.02:
                icon, style, diag = "✅", "✅", f"進入【買入支撐區】，大戶成本約 {chip_floor:.2f}，適合佈局。"
            elif close < tech_sup:
                icon, style, diag = "☢️", "☢️", f"破位重挫！跌穿技術支撐 {tech_sup:.2f}，請嚴格執行停損。"
            else:
                icon, style, diag = "🔎", "🔎", "目前區間震盪，量能穩定，持股續抱即可。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name}({ticker})", "price": round(close, 2),
                "target": round(target_sell, 2), "buy": round(buy_price, 2),
                "sup": round(tech_sup, 2), "floor": round(chip_floor, 2),
                "vol": round(vol_ratio, 2), "diag": diag
            })
        except: pass

# 渲染介面
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 1.5em; font-weight: bold;">{d['icon']} {d['name']} | 現價: {d['price']}</div>
            <div>
                <span style="margin-right:15px;">🎯 停利價格: <span class="target-price">{d['target']}</span></span>
                <span>🛡️ 買入支撐: <span class="support-price">{d['buy']}</span></span>
            </div>
        </div>
        <div style="margin: 15px 0;"><b>💡 智慧診斷：</b>{d['diag']}</div>
        <div style="font-size: 0.9em; color: #666; background: #f9f9f9; padding: 8px; border-radius: 5px;">
            技術支撐: {d['sup']} | 籌碼地板(大戶成本): {d['floor']} | 成交量比: {d['vol']}x
        </div>
    </div>
    """, unsafe_allow_html=True)

# 倒數計時器邏輯
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-box'>🔄 {i} 秒後重新整理</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
