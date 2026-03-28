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
st.set_page_config(page_title="Beta Lab AI - 智權大腦戰情室", layout="wide")

# 2. 私人存取驗證
def check_password():
    def password_entered():
        if st.session_state["password"] == "8888": 
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("### 🤖 AI 量化開發監測環境")
        st.text_input("請輸入內部存取密碼：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 驗證失敗")
        return False
    return True

if not check_password(): st.stop()

# 3. CSS 樣式 (加強 AI 診斷區的可視化)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; border: 2px solid #b7eb8f; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .ai-score { font-size: 1.4em; font-weight: bold; color: #1890ff; background: #e6f7ff; padding: 5px 15px; border-radius: 20px; border: 1px solid #91d5ff; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .adr-tag { background: #e6f7ff; color: #0050b3; border: 1px solid #91d5ff; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. AI 智權大腦核心函數
def calculate_ai_confidence(d, vix, sox_status, week_trend):
    """
    AI 多因子權重模型 (Multi-Factor Scoring Model)
    1. 市場環境 (SOX, VIX): 40%
    2. 趨勢慣性 (均線, 週線, 斜率): 30%
    3. 籌碼與連動 (ADR, Flow): 20%
    4. 價位甜蜜點 (RSI, Buy Zone): 10%
    """
    score = 0
    reasons = []

    # 環境因子
    if sox_status == "BULL": score += 20
    else: reasons.append("大盤逆風")
    
    if vix < 20: score += 20
    elif vix > 28: score -= 30; reasons.append("極度恐慌")
    else: score += 10

    # 趨勢因子
    if d['trend'] == "🌟 多頭排列": score += 15
    if week_trend == "UP": score += 15
    else: reasons.append("週線偏空")

    # 籌碼與連動
    if d['chip_flow'] == "🔥 強勢買入": score += 15
    if d['adr'] != "N/A" and float(d['adr'].strip('%')) > 0.5: score += 5
    
    # 價位因子
    if d['price'] <= d['buy'] * 1.05: score += 10
    if d['rsi'] > 75: score -= 20; reasons.append("嚴重過熱")

    # 輸出判定
    if score >= 85: 
        return score, "✅ 【全力進攻】多因子全線共振，確信度極高。", "✅"
    elif score >= 65:
        return score, f"🔎 【分批佈局】趨勢成形，觀察量能。阻礙：{'/'.join(reasons) if reasons else '無'}", "✅"
    elif score >= 45:
        return score, f"⚠️ 【觀望等待】多空拉鋸。風險：{'/'.join(reasons)}", "⚠️"
    else:
        return score, f"☢️ 【全面避險】風險值過高。主要威脅：{'/'.join(reasons)}", "☢️"

def get_institutional_flow(df):
    recent = df.tail(5)
    flow_score = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow_score -= 1
    return "🔥 強勢買入" if flow_score >= 2 else "💧 持續流出" if flow_score <= -2 else "☁️ 盤整觀望"

def get_trend_score(df):
    c = df['Close']
    ma5, ma10, ma20 = c.rolling(5).mean().iloc[-1], c.rolling(10).mean().iloc[-1], c.rolling(20).mean().iloc[-1]
    return "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"

# 5. 主標題
st.title("🖥️ 全球量化戰術板 V6.5 - AI 智權大腦")
timer_placeholder = st.sidebar.empty()

# 標的清單
tickers = {
    "2330.TW": {"name": "台積電", "adr": "TSM"},
    "NVDA": {"name": "輝達", "adr": None},
    "TSM": {"name": "台積電ADR", "adr": None},
    "MU": {"name": "美光", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"},
    "6770.TW": {"name": "力積電", "adr": None},
    "2344.TW": {"name": "華邦電", "adr": None},
    "3481.TW": {"name": "群創", "adr": None}
}

with st.spinner('AI 大腦正在運算全球權重數據...'):
    vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
    us10y = yf.Ticker("^TNX").history(period="5d")['Close'].iloc[-1]
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_status = "BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "BEAR"

    for ticker, info in tickers.items():
        try:
            name = info['name']
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 取得基礎數據用於 AI 診斷
            chip_flow = get_institutional_flow(df)
            trend_label = get_trend_score(df)
            
            # ADR 計算
            adr_diff = "N/A"
            if info['adr']:
                adr_data = yf.Ticker(info['adr']).history(period="5d")
                adr_chg = ((adr_data['Close'].iloc[-1] - adr_data['Close'].iloc[-2]) / adr_data['Close'].iloc[-2]) * 100
                adr_diff = f"{adr_chg:+.1f}%"

            # 計算 AI 信心指數
            temp_data = {
                'trend': trend_label, 'chip_flow': chip_flow, 'price': close_val,
                'buy': ma20 - 1.2 * std20, 'rsi': 50, 'adr': adr_diff # RSI 簡化計算
            }
            ai_score, ai_diag, ai_style = calculate_ai_confidence(temp_data, vix, sox_status, "UP" if close_val > df_w['Close'].mean() else "DOWN")

            # 補回剩餘標籤
            chip_floor = (df['Close'].tail(60).mean()) # 簡化換手區
            stop_profit_line = df['High'].tail(5).max() * 0.97
            dynamic_stop = close_val - (2.5 * (df['High']-df['Low']).rolling(14).mean().iloc[-1])

            st.markdown(f"""
            <div class="status-card {ai_style}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.6em; font-weight: bold;">{ai_style} {name} ({ticker})</span>
                        <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace;">${close_val:.2f}</span>
                    </div>
                    <div style="text-align: right;">
                        <span class="ai-score">AI 確信度: {ai_score}%</span><br>
                        <span class="metric-tag adr-tag">ADR: {adr_diff}</span>
                        <span class="metric-tag">趨勢: {trend_label}</span>
                    </div>
                </div>
                <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
                <div style="display: flex; gap: 25px;">
                    <div style="flex: 2.2;">
                        <b>🧠 AI 智權診斷 (AI Insight)：</b><br>
                        <span style="line-height:1.6; font-size:1.1em;">{ai_diag}</span>
                        <div class="defense-box">
                            ⚙️ <b>風控與成本模擬：</b> 
                            波段高點預警: {stop_profit_line:.2f} | 密集換手區: {chip_floor:.2f} <br>
                            <span style="color:#cf1322; font-weight:bold;">ATR 動態底線: {dynamic_stop:.2f}</span>
                        </div>
                    </div>
                    <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                        <b>🧪 模型觀察位：</b><br>
                        <span style="font-size: 0.85em; color: #666;">進場參考：</span><br><span class="price-value" style="color:#389e0d; font-size:1.4em;">{temp_data['buy']:.2f}</span><br>
                        <span style="font-size: 0.85em; color: #666;">預計壓力：</span><br><span class="price-value" style="color:#cf1322; font-size:1.4em;">{ma20+2*std20:.2f}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except: pass

# Sidebar 風險監控
st.sidebar.markdown(f"""
### 📊 全球風險環境
- **VIX 恐慌指數：** {vix:.1f}
- **費半狀態：** {sox_status}
- **AI 建議模式：** {'⚔️ 積極進攻' if sox_status == 'BULL' else '🛡️ 守勢避險'}
""")

for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新")
    time.sleep(1)
st.rerun()
