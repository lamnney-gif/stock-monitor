import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (標題改為自用性質)
st.set_page_config(page_title="Beta Lab - 私人測試區", layout="wide")

# 2. 【核心密碼鎖】 - 只有通過驗證才會執行後續代碼
def check_password():
    def password_entered():
        # --- 🔒 請在下方引號內設定你的專屬密碼 ---
        if st.session_state["password"] == "8888": 
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🖥️ 開發者私有實驗環境")
        st.text_input("請輸入存取密碼以啟動監測：", type="password", on_change=password_entered, key="password")
        st.info("💡 提醒：本站僅供個人 Python 量化邏輯測試與數據觀測，非公開對外服務。")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("密碼錯誤，請重新輸入：", type="password", on_change=password_entered, key="password")
        st.error("😕 驗證失敗，請聯繫開發者取得授權。")
        return False
    return True

if not check_password():
    st.stop() # 驗證未通過，強制切斷後續所有邏輯執行

# --- 以下代碼僅在密碼正確後才會加載 ---

# 3. CSS 樣式
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

# --- 側邊欄：法律防護區 ---
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px;">
    <p style="font-size: 0.85em; color: #333; line-height: 1.6;">
    <b>【免責聲明】</b><br>
    1. 本網頁為個人 <b>Python 量化模型開發測試用途</b>，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、診斷報告皆為<b>程式演算法之實驗產出</b>，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。<b>任何閱覽者若據此進行交易，盈虧請自負</b>，本站開發者不承擔任何法律責任。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差，請以各交易所官方報價為準。
    </p>
</div>
""", unsafe_allow_html=True)

# --- 主頁面置頂警告 (確保手機版能看到) ---
st.markdown("""
<div class="mobile-warning">
    <b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境 (Beta Lab)</b><br>
    <p style="font-size: 0.9em; color: #595959; margin-top: 5px; margin-bottom: 0;">
    本站僅供個人程式邏輯測試，所有數據與診斷均為<b>自動化實驗產出，非投資建議</b>。
    閱覽者據此操作之<b>盈虧請自行承擔</b>。詳細條款請參閱左側選單。
    </p>
</div>
""", unsafe_allow_html=True)

# --- 數據處理邏輯 ---
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

col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 開發者自用測試區")
with col_r: timer_placeholder = st.empty()

data_list, news_dict = [], {}

with st.spinner('同步全球實驗數據中...'):
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
            local_low_3d = df['Low'].tail(3).min()
            local_low_20d = df['Low'].tail(20).min()
            chip_floor = get_volume_support(df)
            
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            info = stock.info
            pe_val = info.get('forwardPE', "N/A")
            inst_pct = info.get('heldPercentInstitutions', 0) * 100

            if slope_pct > 0.6:
                raw_buy = (ma10 * 0.7) + (tech_support * 0.3)
            else:
                raw_buy = (tech_support * 0.4) + (chip_floor * 0.6)
            
            suggested_buy = min(raw_buy, local_low_3d * 0.99)
            stop_loss = min(local_low_20d, suggested_buy) * 0.95
            stop_profit_line = df['High'].tail(5).max() * 0.97

            # --- 實驗診斷術語替換 ---
            if bias < -12:
                icon, style, status = "🟣", "🟣", f"🟣 【統計極值】負乖離率達 {bias:.1f}%。當前數據偏離常態分佈，模擬顯示具備技術性反彈動能。"
            elif close_val < stop_loss:
                icon, style, status = "☢️", "☢️", f"☢️ 【邏輯觸發】跌破演算底線 {stop_loss:.2f}。趨勢慣性向下，目前非模型觀察區間。"
            elif bias > 20:
                icon, style, status = "🚨", "🚨", f"🚨 【數據過熱】乖離率 {bias:.1f}%。模型顯示目前為風險溢價區，等待回測觀察位 {suggested_buy:.2f}。"
            elif slope_pct < -0.2 and close_val < tech_support:
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【參數修正】統計支撐位失效。演算模型觀察點下移至 {suggested_buy:.2f}。"
            elif close_val <= suggested_buy * 1.03 and slope_pct > -0.15:
                icon, style, status = "✅", "✅", f"✅ 【模型觸發】數據符合回測支撐邏輯，進入演算布局測試位。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【數據觀測】股價於統計支撐與壓力之間運行，暫無明確邏輯觸發。"

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
                <span class="metric-tag">機構持有: {d['inst']}</span>
            </div>
        </div>
        <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
            斜率: {d['slope']}% | 乖離率: {d['bias']}% | 成交量比: {d['vol']}x
        </div>
        <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="display: flex; gap: 25px;">
            <div style="flex: 2.2;">
                <b>🔍 演算執行狀態 (Execution)：</b><br><span style="line-height:1.6; font-size:1.1em;">{d['diag']}</span>
                <div class="defense-box">
                    ⚙️ <b>風控參數模擬 (Risk Simulation)：</b> 
                    <span style="color:#1890ff;">高點預警: {d['stop_line']}</span> | 
                    <span style="color:#cf1322; font-weight:bold;">演算底線 (Baseline): {d['stop_loss']}</span> <br>
                    密集換手區間: {d['chip_floor']} | 統計偏離下軌: {d['tech_sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參數 (Params)：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 模型觀察點</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預計壓力位</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
                    <div style="grid-column: span 2; height: 1px; background: #ddd; margin: 2px 0;"></div>
                    <div><span class="price-label">📉 支撐分佈</span><br><span class="price-value">{d['tech_sup']}</span></div>
                    <div><span class="price-label">📈 壓力分佈</span><br><span class="price-value">{d['tech_pre']}</span></div>
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
    timer_placeholder.markdown(f"🔄 {i}s 後自動重載實驗數據")
    time.sleep(1)
st.rerun()
