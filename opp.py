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
st.set_page_config(page_title="半導體大戶戰情室-數據全開版", layout="wide")

# 2. CSS 樣式優化
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 15px solid #ff4d4f; color: #a8071a; }
    .⚠️ { background-color: #fffbe6; border-left: 15px solid #ffc53d; color: #874d00; }
    .✅ { background-color: #f6ffed; border-left: 15px solid #52c41a; color: #135200; }
    .☢️ { background-color: #fff1f0; border-left: 15px solid #f5222d; color: #820014; }
    .💤 { background-color: #f5f5f5; border-left: 15px solid #8c8c8c; color: #262626; }
    .🔎 { background-color: #ffffff; border-left: 15px solid #1890ff; color: #003a8c; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.07); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.7); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .timer-container { text-align: right; color: #fa8c16; font-weight: bold; font-size: 1.1em; padding: 10px 20px; border: 1px solid #ffd591; border-radius: 10px; background: #fff7e6; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "INTC": "英特爾"
}

def get_volume_support(df):
    try:
        recent_df = df.tail(120)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

# 頂部抬頭
col_t, col_r = st.columns([3, 1])
with col_t: st.title("📊 半導體「大戶動向」深度數據戰情室")
with col_r: timer_placeholder = st.empty()

data_list = []
news_dict = {}

with st.spinner('正在精準計算斜率、乖離與籌碼分佈...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            # --- 核心數據計算 ---
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 支撐與壓力
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)
            
            # 停利防線 (5日高點回落3%)
            stop_profit_line = df['High'].tail(5).max() * 0.97
            
            # 籌碼地板與建議買入
            chip_floor = get_volume_support(df)
            suggested_buy = (tech_support + chip_floor) / 2
            
            # 強力賣壓區 (ATR 2.5倍)
            high_low = df['High'] - df['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            sell_limit = close_val + (2.5 * atr) 

            # 精準指標
            bias = ((close_val - ma20) / ma20) * 100
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()

            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100

            # --- 深度診斷邏輯 (恢復完整版) ---
            if vol_ratio > 2.0 and abs(slope_pct) < 0.1 and close_val > ma20:
                icon, style, status = "🚨", "🚨", f"🚨 【大戶倒貨】成交量爆出 {vol_ratio:.2f} 倍但股價幾乎不動 (斜率僅 {slope_pct:.2f}%)。這是典型的高檔換手或大戶出貨，極度危險，建議大幅減碼防禦。"
            elif close_val >= tech_pressure * 0.98:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【分批停利】現價 {close_val:.2f} 已逼近建議賣出價 {tech_pressure:.2f}。目前正乖離率達 {bias:.1f}%，短線過熱，隨時有回檔風險，建議先將獲利分批入袋。"
            elif vol_ratio < 0.8 and abs(slope_pct) < 0.05:
                icon, style, status = "💤", "💤", f"💤 【縮量整理】成交量僅均量 {vol_ratio:.2f} 倍，且趨勢斜率極平緩 ({slope_pct:.2f}%)。市場目前觀望氣氛濃厚，暫無攻擊動能，建議保留現金等待表態。"
            elif close_val <= suggested_buy * 1.02 and slope_pct > -0.1:
                icon, style, status = "✅", "✅", f"✅ 【買入訊號】股價回測建議買入價 {suggested_buy:.2f} 附近。支撐區表現強勁且趨勢開始回穩 ({slope_pct:.2f}%)，適合在此分批佈局中長線部位。"
            elif close_val <= tech_support:
                icon, style, status = "☢️", "☢️", f"☢️ 【停損警示】股價已擊穿技術支撐 {tech_support:.2f}。目前趨勢慣性已被破壞，斜率急跌至 {slope_pct:.2f}%，請嚴格執行停損以保護資金安全。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【正常整理】目前在支撐 {tech_support:.2f} 與壓力 {tech_pressure:.2f} 之間穩定波動。量能平穩且斜率為 {slope_pct:.2f}%，無明顯轉向訊號，維持原有部位即可。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), "stop_line": round(stop_profit_line, 2),
                "sell_limit": round(sell_limit, 2), "pe": pe_val, "vol": round(vol_ratio, 2), 
                "diag": status, "inst": f"{inst_pct:.1f}%", "tech_sup": round(tech_support, 2), 
                "chip_floor": round(chip_floor, 2), "bias": round(bias, 2), "slope": round(slope_pct, 2)
            })
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.7em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2em; margin-left: 25px; font-family: monospace; color: #1f1f1f;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">預估 PE: {d['pe']}</span>
                <span class="metric-tag">法人持股: {d['inst']}</span>
            </div>
        </div>
        
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            <b>即時數據指標：</b> 
            乖離率: <span style="color:{'#cf1322' if d['bias']>0 else '#389e0d'};">{d['bias']}%</span> | 
            成交量比: {d['vol']}x | 
            趨勢斜率: {d['slope']}%
        </div>

        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.5;">
                <div style="font-size: 1.1em; line-height: 1.6; color: #262626;">
                    <b>💡 戰情診斷報告：</b><br>{d['diag']}
                </div>
                <div class="defense-box">
                    🛡️ <b>大戶防禦體系：</b> 
                    <span style="color:#1890ff; font-weight:bold;">停利防線：{d['stop_line']}</span> (高點回落3%) | 
                    技術支撐：{d['tech_sup']} | 
                    籌碼地板：{d['chip_floor']}
                </div>
            </div>
            <div style="flex: 1.2; background: rgba(255,255,255,0.5); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>📊 核心操作位參考：</b><br>
                <div style="margin-top: 8px;">
                    🟢 建議買入價：<span style="color:#389e0d; font-weight:bold;">{d['buy']}</span><br>
                    🎯 建議停利價：<span style="color:#d4380d; font-weight:bold;">{d['sell']}</span><br>
                    🚫 <span style="color:#cf1322; font-weight:bold;">⚠️ 強利賣壓區：{d['sell_limit']}</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 刷新邏輯
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 後自動重載數據</div>", unsafe_allow_html=True)
    time.sleep(1)

st.rerun()
