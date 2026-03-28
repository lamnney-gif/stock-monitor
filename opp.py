import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (1600px 寬版佈局)
st.set_page_config(page_title="Beta Lab AI V7.2 - 終極全數據版", layout="wide")

# 2. 私人存取驗證
def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 終極量化數據戰情室 V7.2")
        pwd = st.text_input("請輸入存取密碼：", type="password")
        if pwd == "8888":
            st.session_state["password_correct"] = True
            st.rerun()
        return False
    return True

if not check_password(): st.stop()

# 3. CSS 樣式 (回復所有豐富標籤顏色)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .ai-diag-box { background: #f0f5ff; border: 1px solid #adc6ff; padding: 15px; border-radius: 10px; margin-top: 15px; border-left: 6px solid #1890ff; font-size: 1.05em; }
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .adr-tag { background: #e6f7ff; color: #0050b3; border: 1px solid #91d5ff; }
    .chip-tag { background: #fff7e6; color: #d46b08; border: 1px solid #ffd591; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.15em; font-family: monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. 數據演算函數
def get_institutional_flow(df):
    recent = df.tail(5)
    flow = 0
    for i in range(1, len(recent)):
        if recent['Close'].iloc[i] > recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow += 1
        if recent['Close'].iloc[i] < recent['Close'].iloc[i-1] and recent['Volume'].iloc[i] > recent['Volume'].iloc[i-1]: flow -= 1
    return "🔥 強勢買入" if flow >= 2 else "💧 持續流出" if flow <= -2 else "☁️ 盤整觀望"

def get_volume_support(df):
    try:
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

# 5. AI 分析診斷引擎 (無勝率版)
def get_ai_diagnostic_text(d, vix, sox_status):
    analysis = []
    if sox_status == "BEAR": analysis.append("⚠️ 費半大盤(SOX)處於空頭壓制，市場情緒保守。")
    if vix > 22: analysis.append(f"😨 全球避險情緒上升(VIX:{vix:.1f})，資金傾向撤出高風險資產。")
    if d['chip_flow'] == "🔥 強勢買入": analysis.append("💰 法人資金逆勢進場，籌碼面具備支撐。")
    elif d['chip_flow'] == "💧 持續流出": analysis.append("🚨 主力正在調節倉位，股價短線承壓。")
    if d['trend'] == "🌟 多頭排列": analysis.append("📈 技術面呈現多頭排列，趨勢慣性向上。")
    if d['adr'] != "N/A" and float(d['adr'].strip('%')) > 1.2: analysis.append(f"🔋 ADR 領漲帶動({d['adr']})，有利於現貨開盤表現。")
    
    return " / ".join(analysis) if analysis else "目前數據處於平衡整理區，建議觀察關鍵價位支撐。"

# 6. 主程式
tickers = {
    "2330.TW": {"name": "台積電", "adr": "TSM"},
    "NVDA": {"name": "輝達", "adr": None},
    "TSM": {"name": "台積電ADR", "adr": None},
    "MU": {"name": "美光", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"},
    "2344.TW": {"name": "華邦電", "adr": None},
    "3481.TW": {"name": "群創", "adr": None}
}

st.sidebar.title("📊 全球監控儀表板")
vix = yf.Ticker("^VIX").history(period="5d")['Close'].iloc[-1]
sox = yf.Ticker("^SOX").history(period="1mo")
sox_status = "BULL" if sox['Close'].iloc[-1] > sox['Close'].mean() else "BEAR"
st.sidebar.metric("VIX 恐慌指數", f"{vix:.1f}")
st.sidebar.metric("SOX 趨勢狀態", sox_status)

for ticker, info in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # --- 補齊所有技術數據 ---
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
        rsi = (df['Close'].diff().where(df['Close'].diff()>0, 0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean() * 100).iloc[-1]
        slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close) * 100
        bias = ((close - ma20) / ma20) * 100
        atr = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
        
        # 籌碼與均線排列
        chip_flow = get_institutional_flow(df)
        ma5, ma10 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(10).mean().iloc[-1]
        trend = "🌟 多頭排列" if ma5 > ma10 > ma20 else "💀 空頭排列" if ma5 < ma10 < ma20 else "🌀 趨勢不明"
        
        # 補齊：波段高點、換手區、支撐壓力
        chip_floor = get_volume_support(df)
        stop_line = df['High'].tail(5).max() * 0.97
        tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
        suggested_buy = min(ma20 - 1.2 * std20, df['Low'].tail(3).min() * 0.99)
        
        # ADR 連動
        adr_diff = "N/A"
        if info['adr']:
            adr_px = yf.Ticker(info['adr']).history(period="5d")['Close']
            adr_diff = f"{( (adr_px.iloc[-1] - adr_px.iloc[-2]) / adr_px.iloc[-2] * 100):+.1f}%"

        # AI 診斷分析文字
        ai_diag = get_ai_diagnostic_text({'chip_flow': chip_flow, 'trend': trend, 'adr': adr_diff}, vix, sox_status)
        style = "✅" if (sox_status=="BULL" and chip_flow=="🔥 強勢買入") else ("☢️" if sox_status=="BEAR" else "🔎")

        # --- UI 渲染 (所有數據全數回歸) ---
        st.markdown(f"""
        <div class="status-card {style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.6em; font-weight: bold;">{style} {info['name']} ({ticker})</span>
                    <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${close:.2f}</span>
                </div>
                <div style="text-align: right;">
                    <span class="metric-tag adr-tag">ADR連動: {adr_diff}</span>
                    <span class="metric-tag chip-tag">籌碼: {chip_flow}</span>
                    <span class="metric-tag">PE: {stock.info.get('forwardPE', 'N/A')}</span>
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                </div>
            </div>
            <div style="margin-top: 10px; color: #595959; font-size: 0.95em;">
                趨勢: {trend} | 斜率: {slope:.2f}% | 乖離率: {bias:.2f}% | <b>成交量比: {vol_ratio:.1f}x</b> | 機構: {stock.info.get('heldPercentInstitutions', 0)*100:.1f}%
            </div>
            <div class="ai-diag-box">
                <b>🤖 AI 數據綜合分析 (Diagnostic)：</b><br>{ai_diag}
            </div>
            <div style="display: flex; gap: 25px; margin-top: 15px;">
                <div style="flex: 2.2;">
                    <div class="defense-box">
                        ⚙️ <b>風控與成本模擬 (Risk Control)：</b><br>
                        <span style="color:#1890ff;">波段高點預警: {stop_line:.2f}</span> | 
                        <span style="color:#cf1322; font-weight:bold;">ATR 演算底線: {close - (2.5 * atr):.2f}</span> <br>
                        <b>密集換手區間: {chip_floor:.2f}</b> | 統計支撐下軌: {tech_sup:.2f}
                    </div>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                    <b>🧪 邏輯回測參數：</b><br>
                    <div style="margin-top: 8px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div><span style="font-size:0.8em; color:#666;">🟢 觀察點</span><br><span class="price-value" style="color:#389e0d;">{suggested_buy:.2f}</span></div>
                        <div><span style="font-size:0.8em; color:#666;">🎯 壓力位</span><br><span class="price-value" style="color:#cf1322;">{tech_pre:.2f}</span></div>
                        <div style="grid-column: span 2; height:1px; background:#ddd;"></div>
                        <div><span style="font-size:0.8em; color:#666;">📉 支撐分佈</span><br><span class="price-value">{tech_sup:.2f}</span></div>
                        <div><span style="font-size:0.8em; color:#666;">📈 壓力分佈</span><br><span class="price-value">{tech_pre:.2f}</span></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

time.sleep(60)
st.rerun()
