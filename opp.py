import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time

# 1. 頁面配置 (維持寬版)
st.set_page_config(page_title="Beta Lab - 全功能監測環境", layout="wide")

# 2. 【私人存取驗證】
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
        st.text_input("密碼錯誤：", type="password", on_change=password_entered, key="password")
        st.error("😕 身份驗證失敗。")
        return False
    return True

if not check_password():
    st.stop() 

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
    1. 本網頁為個人 <b>Python 量化測試</b>用途。<br><br>
    2. 內文診斷報告皆為<b>演算法實驗產出</b>，非投資建議。<br><br>
    3. <b>盈虧自負</b>，開發者不承擔法律責任。<br><br>
    4. 數據或有延遲，請以官方報價為準。
    </p>
</div>
""", unsafe_allow_html=True)

# --- 主頁面置頂警告 (手機版強制顯示) ---
st.markdown("""
<div class="mobile-warning">
    <b style="color: #cf1322; font-size: 1.1em;">⚠️ 讀前必視：個人實驗開發環境</b><br>
    <p style="font-size: 0.9em; color: #595959; margin-top: 5px; margin-bottom: 0;">
    本站僅供個人程式邏輯測試。所有數據均為<b>自動化實驗產出</b>。
    閱覽者據此操作之<b>盈虧請自行承擔</b>。
    </p>
</div>
""", unsafe_allow_html=True)

# 4. 指標計算函數 (新增 RSI 與 ATR)
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

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

# 5. 主標題與計時器
col_t, col_r = st.columns([3, 1])
with col_t: st.title("🖥️ 半導體量化監測戰術板")
with col_r: timer_placeholder = st.empty()

# 標的清單 (保留你增加的群創、南亞)
tickers = {
    "NVDA": "輝達", "INTC": "英特爾", "MU": "美光", "000660.KS": "海力士", 
    "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
}

data_list, news_dict = [], {}

with st.spinner('同步全球數據與大盤濾網中...'):
    # --- A. 費半大盤濾網 ---
    sox = yf.Ticker("^SOX").history(period="1mo")
    sox_ma20 = sox['Close'].mean()
    sox_current = sox['Close'].iloc[-1]
    sox_status = "BULL" if sox_current > sox_ma20 else "BEAR"

    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            # 原有數據
            close_val = df['Close'].iloc[-1]
            ma10 = df['Close'].rolling(10).mean().iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            tech_support = ma20 - (2 * std20)
            tech_pressure = ma20 + (2 * std20)
            chip_floor = get_volume_support(df)
            
            # 新增 Pro 指標
            rsi_val = calculate_rsi(df['Close']).iloc[-1]
            atr_val = calculate_atr(df).iloc[-1]
            vol_ratio = df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean()
            
            # 買點與動態停損
            y_data = df['Close'].tail(10).values
            slope_pct = (LinearRegression().fit(np.arange(10).reshape(-1,1), y_data.reshape(-1,1)).coef_[0][0] / y_data.mean()) * 100
            bias = ((close_val - ma20) / ma20) * 100
            
            suggested_buy = min((ma10 * 0.7 + tech_support * 0.3), df['Low'].tail(3).min() * 0.99)
            dynamic_stop = close_val - (2.5 * atr_val) # ATR 動態停損

            # --- 綜合診斷邏輯 (勝率優化版) ---
            if sox_status == "BEAR":
                icon, style, status = "⚠️", "⚠️", f"⚠️ 【環境預警】大盤(SOX)弱勢，系統性風險高。觀察位暫時失效，建議觀望。"
            elif rsi_val > 70:
                icon, style, status = "🚨", "🚨", f"🚨 【數據過熱】RSI 達 {rsi_val:.1f}。進入超買區，價格透支，等待回測至 {suggested_buy:.2f}。"
            elif bias < -12 or rsi_val < 35:
                icon, style, status = "🟣", "🟣", f"🟣 【統計極值】RSI {rsi_val:.1f} 低檔。具備技術反彈潛力，觀測成交量是否回溫。"
            elif close_val < dynamic_stop:
                icon, style, status = "☢️", "☢️", f"☢️ 【趨勢潰敗】跌破 ATR 動態底線 {dynamic_stop:.2f}。趨勢轉弱，暫不納入模型觀察。"
            elif close_val <= suggested_buy * 1.03 and slope_pct > -0.15:
                if vol_ratio > 1.2 and rsi_val < 60:
                    icon, style, status = "✅", "✅", f"✅ 【高勝率觸發】大盤穩定、帶量回測且 RSI 健康，邏輯確認強度高。"
                else:
                    icon, style, status = "🔎", "🔎", f"🔎 【數據觀測】價格接近觀察位，但量能僅 {vol_ratio:.1f}x，動能尚待實驗證實。"
            else:
                icon, style, status = "🔎", "🔎", f"🔎 【常規運行】目前各項參數處於穩定區間，成交量比 {vol_ratio:.1f}x。"

            data_list.append({
                "icon": icon, "style": style, "name": f"{name} ({ticker})", "price": round(close_val, 2),
                "buy": round(suggested_buy, 2), "sell": round(tech_pressure, 2), 
                "stop_loss": round(dynamic_stop, 2), "pe": stock.info.get('forwardPE', "N/A"), 
                "vol": round(vol_ratio, 2), "inst": f"{stock.info.get('heldPercentInstitutions', 0)*100:.1f}%",
                "diag": status, "slope": round(slope_pct, 2), "chip_floor": round(chip_floor, 2), 
                "bias": round(bias, 2), "tech_sup": round(tech_support, 2), "tech_pre": round(tech_pressure, 2),
                "rsi": round(rsi_val, 1)
            })
            news_dict[name] = get_google_news(name)
        except: pass

# --- UI 渲染 (維持你原本的 1600px 風格) ---
st.sidebar.markdown(f"📊 **大盤狀態：** {'📈 多頭' if sox_status=='BULL' else '📉 避險'}")
st.sidebar.title("📰 即時情報推播")
for name, news in news_dict.items():
    if news:
        with st.sidebar.expander(f"{name}"):
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
                <span class="metric-tag">PE: {d['pe']}</span>
                <span class="metric-tag">RSI: {d['rsi']}</span>
                <span class="metric-tag">機構持有: {d['inst']}</span>
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
                    <span style="color:#cf1322; font-weight:bold;">ATR 演算底線: {d['stop_loss']}</span> <br>
                    密集換手區間: {d['chip_floor']} | 統計偏離下軌: {d['tech_sup']}
                </div>
            </div>
            <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                <b>🧪 邏輯回測參數 (Params)：</b><br>
                <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div><span class="price-label">🟢 模型觀察點</span><br><span class="price-value" style="color:#389e0d; font-size:1.3em;">{d['buy']}</span></div>
                    <div><span class="price-label">🎯 預計壓力位</span><br><span class="price-value" style="color:#cf1322; font-size:1.3em;">{d['sell']}</span></div>
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
