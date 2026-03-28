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
st.set_page_config(page_title="Beta Lab Ultimate - 全數據監測環境", layout="wide")

# 2. 私人存取驗證
def check_password():
    def password_entered():
        if st.session_state["password"] == "8888": 
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 內部開發監測系統")
        st.text_input("請輸入存取密碼以解鎖數據：", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.error("😕 驗證失敗。")
        return False
    return True

if not check_password(): st.stop()

# 3. CSS 樣式定義
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-label { font-size: 0.85em; color: #666; font-weight: bold; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    .mobile-warning { 
        background-color: #fff2f0; border: 2px solid #ffccc7; padding: 15px; 
        border-radius: 10px; margin-bottom: 20px; border-left: 10px solid #ff4d4f;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 側邊欄：法律存證區 ---
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px;">
    <p style="font-size: 0.85em; color: #333; line-height: 1.6;">
<b>【免責聲明】</b><br>
    1. 本網頁為個人 <b>Python 量化模型開發測試用途</b>，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、買賣建議、診斷報告皆為<b>程式演算法之實驗產出</b>，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。<b>任何閱覽者若據此進行交易，盈虧請自負</b>，本站開發者不承擔任何法律責任。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差，請以各交易所官方報價為準。
    </p>
</div>
""", unsafe_allow_html=True)

# --- 主頁面置頂警告 (手機版強制顯示) ---
st.markdown("""
<div class="mobile-warning">
<b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境</b><br>
    本站僅供 Python 程式邏輯測試（Beta Lab），內文建議與價格均為演算法實驗產出。
    <b>閱覽者據此操作之盈虧請自行承擔</b>。
    </p>
</div>
""", unsafe_allow_html=True)

# 4. 核心演算法函數
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
        for entry in feed.entries[:3]: news.append(f"• [{entry.title}]({entry.link})")
    except: pass
    return news

# 5. 主標題與計時器
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 全球半導體量化監測戰術板")
with col_r: timer_placeholder = st.empty()

# 標的清單與 ADR 對應
tickers = {
    "NVDA": {"name": "輝達", "adr": None},
    "2330.TW": {"name": "台積電", "adr": "TSM"},
    "MU": {"name": "美光", "adr": None},
    "000660.KS": {"name": "海力士", "adr": None},
    "2303.TW": {"name": "聯電", "adr": "UMC"},
    "6770.TW": {"name": "力積電", "adr": None},
    "2344.TW": {"name": "華邦電", "adr": None},
    "3481.TW": {"name": "群創", "adr": None},
    "1303.TW": {"name": "南亞", "adr": None}
}

data_list, news_dict = [], {}

with st.spinner('正在同步全球量價、新聞與大戶成本數據...'):
    # A. 費半濾網
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_ma20 = sox['Close'].mean()
    sox_status = "BULL" if sox['Close'].iloc[-1] > sox_ma20 else "BEAR"

    for ticker, info in tickers.items():
        try:
            name = info['name']
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            df_w = stock.history(period="2y", interval="1wk") # 周線
            if df.empty: continue
            
            # --- 指標運算 ---
            close_val = df['Close'].iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            # RSI & ATR
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rsi_val = (100 - (100 / (1 + gain/loss))).iloc[-1]
            tr = pd.concat([df['High']-df['Low'], abs(df['High']-df['Close'].shift()), abs(df['Low']-df['Close'].shift())], axis=1).max(axis=1)
            atr_val = tr.rolling(14).mean().iloc[-1]
            
            # 布林帶寬 & 乖離 & 斜率
            b_width = ((ma20 + 2*std20) - (ma20 - 2*std20)) / ma20
            bias = ((close_val - ma20) / ma20) * 100
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100
            
            # --- 核心關鍵數據回歸 ---
            chip_floor = get_volume_support(df) # 密集換手區
            stop_profit_line = df['High'].tail(5).max() * 0.97 # 波段高點預警
            tech_sup, tech_pre = ma20 - 2 * std20, ma20 + 2 * std20
            
            # 周線與 ADR
            w_ma20 = df_w['Close'].rolling(20).mean().iloc[-1]
            week_trend = "UP" if close_val > w_ma20 else "DOWN"
            adr_diff = "N/A"
            if info['adr']:
                adr_data = yf.Ticker(info['adr']).history(period="5d")
                adr_change = ((adr_data['Close'].iloc[-1] - adr_data['Close'].iloc[-2]) / adr_data['Close'].iloc[-2]) * 100
                adr_diff = f"{adr_change:+.1f}%"

            # 觀察位與動態停損
            suggested_buy = min(ma20 - 1.2 * std20, df['Low'].tail(3).min() * 0.99)
            dynamic_stop = close_val - (2.5 * atr_val)

            # --- 診斷邏輯 ---
            if sox_status == "BEAR": icon, style, status = "⚠️", "⚠️", f"⚠️ 【環境預警】SOX 濾網顯示大盤弱勢。建議提高現金水位，觀察位暫失效。"
            elif b_width < 0.08: icon, style, status = "🌪️", "🔎", f"🌪️ 【變盤預警】帶寬極窄 {b_width:.2f}。能量高度壓縮，觀測變盤突破方向。"
            elif rsi_val > 72: icon, style, status = "🚨", "🚨", f"🚨 【數據過熱】RSI {rsi_val:.1f}。進入超買，短線風險極高，等待回測。"
            elif close_val < dynamic_stop: icon, style, status = "☢️", "☢️", f"☢️ 【趨勢破壞】跌破 ATR 動態底線 {dynamic_stop:.2f}。慣性向下，模型停止追蹤。"
            elif close_val <= suggested_buy * 1.03 and week_trend == "UP":
                icon, style, status = ("✅", "✅", "✅ 【高勝率確認】量價與週線多頭共振。邏輯確信度高。") if vol_ratio > 1.2 else ("🔎", "🔎", "🔎 【數據觀測】接近觀察位但成交量不足。")
            else: icon, style, status = "🔎", "🔎", f"🔎 【常規運行】週線：{'偏多' if week_trend=='UP' else '偏空'}。觀察成交量與籌碼變化。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pre, 2), "stop": round(dynamic_stop, 2),
                "stop_line": round(stop_profit_line, 2), "chip_floor": round(chip_floor, 2),
                "rsi": round(rsi_val, 1), "vol": round(vol_ratio, 1), "adr": adr_diff, "slope": round(slope, 2),
                "bias": round(bias, 2), "sup": round(tech_sup, 2), "pre": round(tech_pre, 2),
                "diag": status, "pe": stock.info.get('forwardPE', "N/A"), "inst": f"{stock.info.get('heldPercentInstitutions', 0)*100:.1f}%"
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 (1600px 全數據排列) ---
st.sidebar.markdown(f"📊 **大盤狀態 (SOX)：** {'📈 多頭' if sox_status=='BULL' else '📉 避險'}")
st.sidebar.title("📰 即時情報推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(name):
            for n in news: st.markdown(n)

for d in data_list:
    st.markdown(f"""
    <div class="status-card {d['style']}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.6em; font-weight: bold;">{d['icon']} {d['name']}</span>
                <span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${d['price']}</span>
            </div>
            <div style="text-align: right;">
                <span class="metric-tag adr-tag">ADR連動: {d['adr']}</span>
                <span class="metric-tag">PE: {d['pe']}</span>
                <span class="metric-tag">RSI: {d['rsi']}</span>
                <span class="metric-tag">機構: {d['inst']}</span>
            </div>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            斜率: {d['slope']}% | 乖離率: {d['bias']}% | <b>成交量比: {d['vol']}x</b>
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🔍 演算執行狀態 (Execution)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控參數模擬 (Risk Simulation)：</b> 
                    <span style="color:#1890ff;">波段高點預警: {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">ATR 演算底線: {d['stop']}</span> <br>
                    <b>密集換手區間: {d['chip_floor']}</b> | 統計支撐下軌: {d['sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參數 (Params)：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 模型觀察點</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預計壓力位</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
                    <div style="grid-column: span 2; height: 1px; background: #ddd; margin: 2px 0;"></div>
                    <div><span class="price-label">📉 支撐分佈</span><br><span class="price-value">{d['sup']}</span></div>
                    <div><span class="price-label">📈 壓力分佈</span><br><span class="price-value">{d['pre']}</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 刷新
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新數據")
    time.sleep(1)
st.rerun()
