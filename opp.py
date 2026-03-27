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
st.set_page_config(page_title="半導體大戶戰情室-數據修復版", layout="wide")

# 2. 注入自定義 CSS (強化右側價格區塊)
st.markdown("""
    <style>
    .status-card { padding: 25px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); background-color: white; }
    .🚨 { border-left: 12px solid #d32f2f; background-color: #fff5f5; }
    .⚠️ { border-left: 12px solid #fbc02d; background-color: #fffdf0; }
    .✅ { border-left: 12px solid #388e3c; background-color: #f0fff4; }
    .☢️ { border-left: 12px solid #ff4444; background-color: #fff0f0; }
    .🔎 { border-left: 12px solid #455a64; }
    
    .metric-tag { display: inline-block; padding: 4px 10px; background: rgba(0,0,0,0.08); border-radius: 6px; margin-right: 8px; font-size: 0.9em; font-weight: bold; color: #333; }
    .price-main { font-size: 2.2em; font-family: monospace; font-weight: 900; color: #1a1a1a; margin: 5px 0; }
    
    /* 核心價格區：強制顯示 */
    .target-container { 
        background: #f8f9fa; 
        padding: 15px; 
        border-radius: 12px; 
        border: 2px solid #eee; 
        min-width: 220px;
        text-align: center;
    }
    .val-buy { color: #1b5e20; font-size: 1.6em; font-weight: 900; }
    .val-sell { color: #c62828; font-size: 1.6em; font-weight: 900; border-top: 2px dashed #ddd; margin-top: 10px; padding-top: 10px; }
    .val-label { font-size: 0.85em; color: #666; font-weight: bold; margin-bottom: 2px; }
    
    .timer-display { color: #ff5722; font-weight: 900; font-size: 1.3em; text-align: right; border: 2px solid #ff5722; padding: 5px 15px; border-radius: 10px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "MU": "美光", "INTC": "英特爾", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", 
    "3481.TW": "群創", "2330.TW": "台積電", "NVDA": "輝達"
}

def get_volume_support(df):
    try:
        v_hist = np.histogram(df.tail(120)['Close'], bins=10, weights=df.tail(120)['Volume'])
        idx = np.argmax(v_hist[0])
        return (v_hist[1][idx] + v_hist[1][idx+1]) / 2
    except: return 0

# 標題與倒數
c1, c2 = st.columns([3, 1])
with c1: st.title("🚀 半導體「大戶動向」數據修復版")
with c2: timer_spot = st.empty()

data_list = []
with st.spinner('同步數據中...'):
    for ticker, name in tickers.items():
        try:
            s = yf.Ticker(ticker)
            df = s.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            tech_sup = ma20 - (2 * std20)   # 技術支撐
            tech_press = ma20 + (2 * std20) # 建議賣出 (停利)
            floor = get_volume_support(df)  # 籌碼地板
            buy_price = (tech_sup + floor) / 2
            bias = ((close - ma20) / ma20) * 100
            vol_r = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            info = s.info
            pe = info.get('forwardPE', "N/A")
            inst = info.get('heldPercentInstitutions', 0) * 100
            insider = info.get('heldPercentInsiders', 0) * 100

            # 狀態
            style, icon, note = "🔎", "🔎", f"於支撐 {tech_sup:.2f} 與壓力 {tech_press:.2f} 間震盪。"
            if vol_r > 2.2: style, icon, note = "🚨", "🚨", "【大戶出貨】爆量不漲，建議立即減碼。"
            elif close >= tech_press * 0.98: style, icon, note = "⚠️", "⚠️", f"【分批停利】已達壓力位 {tech_press:.2f}。"
            elif close <= buy_price * 1.03: style, icon, note = "✅", "✅", f"【買入訊號】回測支撐區 {buy_price:.2f}。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": f"{close:.2f}",
                "buy": f"{buy_price:.2f}", "sell": f"{tech_press:.2f}", "pe": pe, "inst": f"{inst:.1f}%",
                "insider": f"{insider:.1f}%", "bias": f"{bias:.1f}%", "vol": f"{vol_r:.2f}",
                "sup": f"{tech_sup:.2f}", "floor": f"{floor:.2f}", "diag": note
            })
        except: pass

# 渲染卡片
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex: 2;">
                <div style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</div>
                <div class="price-main">${d['price']}</div>
                <div>
                    <span class="metric-tag">本益比: {d['pe']}</span>
                    <span class="metric-tag">法人: {d['inst']}</span>
                    <span class="metric-tag">大戶: {d['insider']}</span>
                </div>
                <div style="margin-top:8px; font-size:0.95em; color:#444;">
                    乖離率: <b>{d['bias']}</b> | 成交量比: <b>{d['vol']}x</b>
                </div>
            </div>
            <div class="target-container">
                <div class="val-label">💡 建議買入價</div>
                <div class="val-buy">{d['buy']}</div>
                <div class="val-label" style="margin-top:10px;">🎯 建議賣出 (停利)</div>
                <div class="val-sell">{d['sell']}</div>
            </div>
        </div>
        <div style="margin-top: 15px; padding: 12px; border-top: 1px solid #eee; line-height: 1.6;">
            <b>📊 深度診斷：</b> {d['diag']} <br>
            <small style="color:#888;">(技術支撐: {d['sup']} | 籌碼地板: {d['floor']})</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 倒數計時
for i in range(60, 0, -1):
    timer_spot.markdown(f"<div class='timer-display'>🔄 {i}s 刷新</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
