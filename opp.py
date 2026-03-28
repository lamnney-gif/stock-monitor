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
st.set_page_config(page_title="半導體大戶戰情室-超跌紫色版", layout="wide")

# 2. CSS 樣式擴充 (加入紫色樣式)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } /* 超漲 */
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } /* 警示 */
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } /* 買入 */
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } /* 崩壞 */
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; } /* 整理 */
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } /* 超跌紫色 */
    
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    .timer-container { text-align: right; color: #fa8c16; font-weight: bold; font-size: 1.1em; padding: 10px 20px; border: 1px solid #ffd591; border-radius: 10px; background: #fff7e6; }
    </style>
    """, unsafe_allow_html=True)

tickers = {
    "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "INTC": "英特爾"
}

def get_volume_support(df):
    try:
        recent_df = df.tail(60)
        v_hist = np.histogram(recent_df['Close'], bins=10, weights=recent_df['Volume'])
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

def get_google_news(keyword):
    news = []
    try:
        url = f"https://news.google.com/rss/search?q={quote(keyword + ' 股價')}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

# 頂部抬頭
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 半導體大戶戰情室 - 邏輯全功能版")
with col_r: timer_placeholder = st.empty()

data_list, news_dict = [], {}

with st.spinner('同步全球數據中...'):
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            # 支撐/壓力/籌碼
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)
            local_low_3d = df['Low'].tail(3).min()
            local_low_20d = df['Low'].tail(20).min()
            chip_floor = get_volume_support(df)
            
            # 指標計算
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100

            # --- 邏輯修正：買點不倒掛 ---
            if slope_pct > 0.6:
                raw_buy = (ma10 * 0.7) + (tech_support * 0.3)
            else:
                raw_buy = (tech_support * 0.4) + (chip_floor * 0.6)
            
            suggested_buy = min(raw_buy, local_low_3d * 0.99)
            stop_loss = min(local_low_20d, suggested_buy) * 0.95
            stop_profit_line = df['High'].tail(5).max() * 0.97

            # --- 診斷報告 (優先權順序) ---
            if bias < -12: # 超跌紫色優先
                icon, style, status = "🟣", "🟣", f"🟣 【極度超跌】負乖離率達 {bias:.1f}%。股價偏離常軌，技術性反彈機率高，不建議在此殺低。"
            elif close_val < stop_loss:
                icon, style, status = "☢️", "☢️", f"☢️ 【支撐瓦解】跌破絕對停損線 {stop_loss:.2f}。趨勢全面轉空，嚴禁接刀。"
            elif bias > 20:
                icon, style, status = "🚨", "🚨", f"🚨 【嚴重超漲】乖離率 {bias:.1f}%。目前是幫人抬轎區，等回測 {suggested_buy:.2f}。"
            elif slope_pct < -0.2 and close_val < tech_support:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【空頭修正】原技術支撐已失效。建議觀察點下移至 {suggested_buy:.2f}。"
            elif close_val <= suggested_buy * 1.03 and slope_pct > -0.15:
                icon, style, status = "✅", "✅", f"✅ 【買入訊號】回測支撐區且斜率走平，適合分批佈局。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【區間整理】股價在支撐與壓力之間震盪尋找方向。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), "stop_line": round(stop_profit_line, 2),
                "stop_loss": round(stop_loss, 2), "pe": pe_val, "vol": round(vol_ratio, 2), "inst": f"{inst_pct:.1f}%",
                "diag": status, "slope": round(slope_pct, 2), "chip_floor": round(chip_floor, 2), 
                "bias": round(bias, 2), "tech_sup": round(tech_support, 2), "tech_pre": round(tech_pressure, 2)
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 ---
for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag">PE: {d['pe']}</span>
                <span class="metric-tag">法人: {d['inst']}</span>
            </div>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            斜率: {d['slope']}% | 乖離率: {d['bias']}% | 成交量比: {d['vol']}x
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>💡 戰術診斷：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['diag']}</span>
                <div class="defense-box">
                    🛡️ <b>防禦體系：</b> 
                    <span style="color:#1890ff;">短期停利參考: {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">絕對停損: {d['stop_loss']}</span> <br>
                    歷史籌碼地板: {d['chip_floor']} | 布林支撐底線: {d['tech_sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>📊 核心參考價位：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 建議買入</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預期停利</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
                    <div style="grid-column: span 2; height: 1px; background: #ddd; margin: 2px 0;"></div>
                    <div><span class="price-label">📉 波段支撐</span><br><span class="price-value">{d['tech_sup']}</span></div>
                    <div><span class="price-label">📈 波段壓力</span><br><span class="price-value">{d['tech_pre']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 側邊欄新聞
st.sidebar.title("📰 即時情報推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
            for n in news: st.markdown(n)

# 刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"<div class='timer-container'>🔄 {i}s 後自動重載數據</div>", unsafe_allow_html=True)
    time.sleep(1)
st.rerun()
