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
st.set_page_config(page_title="半導體大戶戰情室-防線強化版", layout="wide")

# 2. 注入自定義 CSS
st.markdown("""
    <style>
    .status-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.08); }
    .🚨 { background-color: #ffebee; border-left: 12px solid #d32f2f; color: #b71c1c; }
    .⚠️ { background-color: #fffde7; border-left: 12px solid #fbc02d; color: #827717; }
    .✅ { background-color: #e8f5e9; border-left: 12px solid #388e3c; color: #1b5e20; }
    .☢️ { background-color: #fce4ec; border-left: 12px solid #c2185b; color: #880e4f; }
    .💤 { background-color: #f5f5f5; border-left: 12px solid #9e9e9e; color: #424242; }
    .🔎 { background-color: #ffffff; border-left: 12px solid #455a64; color: #263238; }
    .metric-tag { display: inline-block; padding: 4px 10px; background: rgba(0,0,0,0.06); border-radius: 6px; margin-right: 10px; font-size: 0.9em; font-weight: bold; }
    .profit-line { background-color: #fff3e0; color: #e65100; padding: 5px 10px; border-radius: 5px; font-weight: bold; border: 1px dashed #e65100; }
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

st.title("🚀 半導體「大戶動向」防線監控站")
st.caption(f"數據自動刷新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

data_list = []

with st.spinner('正在掃描全球籌碼防線...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close = df['Close'].iloc[-1]
            high_5d = df['High'].tail(5).max() # 近5日最高點
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # --- 防線運算 ---
            tech_sup = ma20 - (2 * std20)   # 技術支撐 (下軌)
            tech_press = ma20 + (2 * std20) # 建議預期賣價 (上軌)
            chip_floor = get_volume_support(df) # 籌碼地板 (大戶成本)
            
            # 停利防線：取「近5日高點打95折」或「月線(MA20)」的較高者
            # 這能確保股價衝高回落 5% 或跌破月線時提醒你
            profit_defense = max(high_5d * 0.95, ma20) 
            
            bias = ((close - ma20) / ma20) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            # --- 智慧診斷與防線狀態 ---
            if close < profit_defense:
                icon, style, status = "☢️", "☢️", f"☢️ 【防線失守】股價已跌破停利防線 {profit_defense:.2f}。目前趨勢走弱，建議「獲利了結」或「減碼觀望」，守住現有戰果！"
            elif close >= tech_press * 0.97:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】股價衝向壓力位 {tech_press:.2f}。目前正乖離 {bias:.1f}%。雖然還在防線上，但已過熱，建議先收割一部分獲利。"
            elif close <= (tech_sup + chip_floor)/2 * 1.03:
                icon, style, status = "✅", "✅", f"✅ 【支撐區】股價回測籌碼地板 {chip_floor:.2f} 附近。這裡是大戶的防線，只要不破，就是長線佈局的好時機。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【防線安全】目前股價穩守在防線 {profit_defense:.2f} 之上。只要沒跌破，就繼續抱著讓獲利奔跑。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close, 2),
                "profit_line": round(profit_defense, 2), "sell": round(tech_press, 2),
                "vol": round(vol_ratio, 2), "diag": status, "bias": round(bias, 2),
                "tech_sup": round(tech_sup, 2), "chip_floor": round(chip_floor, 2)
            })
        except: pass

# --- 介面渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 1.8em; margin-left: 20px; font-family: monospace;">${d['price']}</span>
                <div style="margin-top:8px;">
                    <span class="profit-line">🛡️ 停利防線：{d['profit_line']}</span>
                    <span style="font-size: 0.85em; color: #666; margin-left:10px;">(跌破請考慮離場)</span>
                </div>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">乖離率: {d['bias']}%</span>
                <span class="metric-tag">量比: {d['vol']}x</span>
            </div>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 20px;">
            <div style="flex: 2; font-size: 1.1em;">
                <b>💡 戰報分析：</b><br>{d['diag']}
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.4); padding: 10px; border-radius: 8px; border: 1px solid #ddd; font-size: 0.9em;">
                <b>📊 參考水位：</b><br>
                預期賣價：<span style="color:#d32f2f; font-weight:bold;">{d['sell']}</span><br>
                技術支撐：{d['tech_sup']}<br>
                籌碼地板：{d['chip_floor']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

time.sleep(60)
st.rerun()
