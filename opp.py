import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (寬螢幕佈局)
st.set_page_config(page_title="半導體大戶戰情室-雙邏輯核心版", layout="wide")

# 2. CSS 強化 (增加動態陰影與邊框感)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } /* 危險/乖離過大 */
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } /* 警示/停利 */
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } /* 買入訊號 */
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } /* 破線停損 */
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; } /* 穩定/觀察 */
    
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .timer-container { text-align: right; color: #fa8c16; font-weight: bold; font-size: 1.1em; padding: 10px 20px; border: 1px solid #ffd591; border-radius: 10px; background: #fff7e6; }
    </style>
    """, unsafe_allow_html=True)

# 股票清單
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
with col_t: st.title("🖥️ 半導體大戶戰情室 (妖股/績優雙模版)")
with col_r: timer_placeholder = st.empty()

data_list = []

with st.spinner('AI 正在判斷個股屬性並校準支撐...'):
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
            
            # 計算斜率 (趨勢強度)
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            
            # 籌碼與低點
            chip_floor = get_volume_support(df)
            local_low = df['Low'].tail(20).min()
            bias = ((close_val - ma20) / ma20) * 100

            # --- 終極核心：雙軌買入邏輯 ---
            if slope_pct > 0.6:  # A. 強勢噴發型 (如現在的力積電或飆漲時的NVDA)
                suggested_buy = ma10 * 0.98  # 參考10日線，因為它跌不回MA20或籌碼地板
                logic_type = "🔥 強勢攻擊模式"
                
                if bias > 22: # 乖離過大預警
                    icon, style, status = "🚨", "🚨", f"🚨 【嚴重超漲】目前乖離率 {bias:.1f}%。消息面拉抬過猛，隨時面臨垂直回檔，此時追入極度危險！"
                elif close_val <= suggested_buy * 1.02:
                    icon, style, status = "✅", "✅", f"✅ 【強勢上車點】股價回測 10 日攻擊線 {ma10:.2f} 附近，適合短線切入。"
                else:
                    icon, style, status = "🔎", "🔎", f"🔎 【噴發中】股價貼著攻擊線向上，暫無買點。建議等回測 {suggested_buy:.2f}。"

            else:  # B. 穩健震盪型
                # 下跌時參考籌碼地板與近期低點，多頭時參考技術支撐
                if slope_pct > 0:
                    suggested_buy = (tech_support * 0.7) + (chip_floor * 0.3)
                else:
                    suggested_buy = (local_low * 0.7) + (chip_floor * 0.3)
                
                logic_type = "📈 穩健趨勢模式"
                if close_val < (local_low * 0.95): # 跌破近期支撐
                    icon, style, status = "☢️", "☢️", f"☢️ 【趨勢走空】已擊穿近期支撐位 {local_low:.2f}。下方支撐虛空，請嚴格執行避險。"
                elif close_val <= suggested_buy * 1.02 and slope_pct > -0.15:
                    icon, style, status = "✅", "✅", f"✅ 【分批進場】股價回測加權支撐點 {suggested_buy:.2f}，斜率穩定，具備布局價值。"
                else:
                    icon, style, status = "🔎", "🔎", f"🔎 【區間整理】目前在支撐 {suggested_buy:.2f} 與壓力 {tech_pressure:.2f} 之間運行。"

            # 輔助指標
            stop_loss = min(local_low, suggested_buy) * 0.95
            stop_profit_line = df['High'].tail(5).max() * 0.97
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            info = stock.info
            pe_val = info.get('forwardPE', "N/A")

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), "stop_line": round(stop_profit_line, 2),
                "stop_loss": round(stop_loss, 2), "pe": pe_val, "vol": round(vol_ratio, 2), "logic": logic_type,
                "diag": status, "tech_sup": round(tech_support, 2), "chip_floor": round(chip_floor, 2), "slope": round(slope_pct, 2)
            })
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">模式: {d['logic']}</span>
                <span class="metric-tag">預估 PE: {d['pe']}</span>
            </div>
        </div>
        
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            <b>即時指標：</b> 趨勢斜率: {d['slope']}% | 交易量比: {d['vol']}x
        </div>

        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2;">
                <div style="font-size: 1.1em; line-height: 1.6;">
                    <b>💡 戰情診斷：</b><br>{d['diag']}
                </div>
                <div class="defense-box">
                    🛡️ <b>核心防線：</b> 
                    <span style="color:#1890ff; font-weight:bold;">停利參考：{d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">絕對停損：{d['stop_loss']}</span> <br>
                    歷史籌碼地板：{d['chip_floor']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.5); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b style="font-size: 1.1em;">📊 建議操作位：</b><br>
                <div style="margin-top: 12px; font-size: 1.05em;">
                    🟢 建議買入價：<span style="color:#389e0d; font-weight:bold;">{d['buy']}</span><br>
                    🎯 預期停利價：<span style="color:#d4380d; font-weight:bold;">{d['sell']}</span>
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
