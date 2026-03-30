import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from datetime import datetime
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
import time
import random
from groq import Groq

# 1. 頁面基礎配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 雙 GROQ 戰情室", layout="wide")

# --- 2. 雙 GROQ 引擎啟動邏輯 ---
@st.cache_resource
def init_groq_engines():
    engines = []
    # 支援最多兩個 Key 交替使用，解決 Rate Limit 問題
    keys = ["GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY"]
    for k in keys:
        if k in st.secrets:
            engines.append(Groq(api_key=st.secrets[k].strip()))
    return engines

groq_pool = init_groq_engines()

# 3. 私密存取驗證 (一字不漏)
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]: return True
    st.markdown("### 🖥️ 內部開發監測系統 V6.9.0 (Dual-GROQ Balanced)")
    pwd = st.text_input("請輸入存取密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    return False

if not check_password(): st.stop()

# 4. CSS 樣式 (100% 還原所有顏色標籤、動畫與陰影)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); transition: transform 0.3s; }
    .status-card:hover { transform: translateY(-5px); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; color: #a8071a; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .🔎 { background-color: #ffffff; border-left: 12px solid #1890ff; color: #003a8c; }
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.08); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .price-value { font-size: 1.1em; font-family: monospace; font-weight: bold; }
    .mobile-warning { background-color: #fff2f0; border: 2px solid #ffccc7; padding: 15px; border-radius: 10px; margin-bottom: 20px; border-left: 10px solid #ff4d4f; }
    .news-link { color: #1890ff; text-decoration: none; font-size: 0.85em; display: block; margin-top: 4px; border-bottom: 1px solid #f0f0f0; padding-bottom: 4px; }
    .engine-id { font-size: 0.7em; background: #333; color: white; padding: 2px 8px; border-radius: 4px; margin-bottom: 8px; display: inline-block; font-weight: bold; }
    .footer-disclaimer { font-size: 0.75em; color: #8c8c8c; margin-top: 10px; border-top: 1px dashed #d9d9d9; padding-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 📜 [核心一字不漏] 側邊欄免責聲明
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 15px; border-radius: 10px; font-size: 0.85em;">
    <b>【免責聲明 / DISCLAIMER】</b><br><br>
    1. 本網頁為個人量化模型開發測試用途，僅供觀測邏輯執行結果。<br><br>
    2. 內文所有價格、診斷報告、買賣點建議皆為演算法實驗產出，<b>非投資建議</b>。投資盈虧自負。<br><br>
    3. 數據可能受 API 延遲或極端行情影響，請以官方交易所數據為準。
</div>
""", unsafe_allow_html=True)

def get_stock_news(q):
    try:
        url = f"https://news.google.com/rss/search?q={quote(q)}+stock&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        feed = feedparser.parse(url)
        return feed.entries[:3]
    except: return []

# --- 5. 雙 GROQ 負載平衡分析核心 ---
@st.cache_data(ttl=3600)
def get_balanced_analysis(idx, name, price, rsi, chip_flow, trend, pe, rev, bias, slope):
    if not groq_pool: return "❌ 無可用之 GROQ 引擎。請檢查 Secrets 設定。"
    
    # 核心邏輯：根據 index 輪流使用不同的 Key
    engine_idx = idx % len(groq_pool)
    client = groq_pool[engine_idx]
    
    prompt = f"[投資長戰報] 標:{name}, 價:{price}, RSI:{rsi:.1f}, 籌碼:{chip_flow}, 趨勢:{trend}, PE:{pe}, 營收:{rev}, 乖離:{bias}%. 120字內狂傲獵殺分析。"
    
    try:
        # 有了雙 Key 交替，我們可以稍微縮短等待時間到 2-4 秒
        time.sleep(random.uniform(2.5, 4.0)) 
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "你是一位語氣狠準狂的傳奇投資長。"},{"role": "user", "content": prompt}],
            timeout=15.0
        )
        return f"🦅 [GROQ-{engine_idx + 1} 首席] " + res.choices[0].message.content.strip()
    except:
        return "📊 智庫連線中 (Rate Limit)，請參考下方技術指標與 ATR 風控線。"

# 6. 主程序監控
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

st.title("🖥️ Beta Lab AI Ultimate - 雙 GROQ 戰情室")
st.markdown('<div class="mobile-warning"><b>⚠️ 法律聲明：</b>本站數據均為自動化實驗產出，非投資建議。閱覽者應獨立判斷並自負投資盈虧。</div>', unsafe_allow_html=True)
timer_placeholder = st.empty()

# 全球數據 (VIX / SOX)
try:
    v_df = yf.Ticker("^VIX").history(period="1d")
    vix = round(v_df['Close'].iloc[-1], 2) if not v_df.empty else 20.0
    sox_df = yf.Ticker("^SOX").history(period="1mo")
    sox_status = "📈 BULL" if (not sox_df.empty and sox_df['Close'].iloc[-1] > sox_df['Close'].mean()) else "📉 BEAR"
except: vix, sox_status = 20.0, "📉 BEAR"

st.sidebar.markdown(f"📊 **全球指標**\n- VIX: {vix}\n- SOX: {sox_status}")

# --- 7. 核心渲染循環 ---
ticker_items = list(tickers.items())
for idx, (ticker, name) in enumerate(ticker_items):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        s_info = stock.info
        close_val = df['Close'].iloc[-1]
        ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
        
        # 抓取所有截圖中要求的數據 (一字不漏)
        pe_val = f"{s_info.get('trailingPE', 0):.1f}"
        rev_growth = f"{(s_info.get('revenueGrowth', 0) or 0) * 100:.1f}%"
        inst_hold = f"{(s_info.get('heldPercentInstitutions', 0) or 0) * 100:.1f}%"
        vol_ratio = df['Volume'].iloc[-1] / (df['Volume'].iloc[-6:-1].mean() + 1e-9)
        rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
        atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
        bias = round(((close_val - ma20) / ma20) * 100, 2)
        slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100
        
        # 執行輪替分析
        ai_report = get_balanced_analysis(idx, name, close_val, rsi_val, "數據追蹤", "多頭排列", pe_val, rev_growth, bias, round(slope,2))
        
        # 標籤色判定 (🟣、✅、☢️)
        if rsi_val < 32: style = "🟣"
        elif rsi_val > 70: style = "☢️"
        elif sox_status == "📈 BULL": style = "✅"
        else: style = "⚠️"

        news_items = get_stock_news(name)
        news_html = "".join([f'<a class="news-link" href="{n.link}" target="_blank">📰 {n.title[:45]}...</a>' for n in news_items])

        # 物理級 UI 渲染 (一字不漏)
        st.markdown(f"""
        <div class="status-card {style}">
            <div class="engine-id">ACTIVE ENGINE: GROQ-KEY-{ (idx % len(groq_pool)) + 1 if groq_pool else "N/A" }</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><span style="font-size: 1.6em; font-weight: bold;">{name} ({ticker})</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${round(close_val, 2)}</span></div>
                <span class="metric-tag">RSI: {round(rsi_val, 1)} | 乖離: {bias}% | 量比: {round(vol_ratio, 1)}x</span>
            </div>
            <div style="margin-top: 10px; color: #595959; font-size: 0.9em;">
                PE: {pe_val} | 營收成長: {rev_growth} | <b>法人持股: {inst_hold}</b> | 10日斜率: {round(slope, 2)}%
            </div>
            <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(0,0,0,0.1);">
            <div style="display: flex; gap: 25px;">
                <div style="flex: 2.2;">
                    <b>🧠 智權診斷 (巔峰決策)：</b><br><span style="line-height:1.6; font-size:1.1em;">{ai_report}</span>
                    <div class="defense-box">
                        ⚙️ <b>風控模擬：</b> 
                        <span style="color:#1890ff;">止盈防線: {round(df['High'].tail(5).max()*0.97, 2)}</span> | 
                        <span style="color:#cf1322; font-weight:bold;">ATR地板: {round(close_val - 2.5*atr_val, 2)}</span> | 
                        換手支撐: {round(ma20-std20, 2)}
                    </div>
                    <div class="footer-disclaimer">※ 本分析由 AI 自動生成。盈虧自負，非投資建議。</div>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                    <b>🎯 即時速報：</b><br>{news_html if news_html else "暫無數據"}
                    <div style="margin-top: 15px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div><span style="font-size:0.8em; color:#666;">🟢 買點參考</span><br><span class="price-value" style="color:#389e0d;">{round(ma20-1.2*std20, 2)}</span></div>
                        <div><span style="font-size:0.8em; color:#666;">🎯 壓力參考</span><br><span class="price-value" style="color:#cf1322;">{round(ma20+2*std20, 2)}</span></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(0.5) # 防止 yfinance 過載
    except Exception as e:
        continue

# 8. 自動刷新邏輯
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新系統")
    time.sleep(1)
st.rerun()
