import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
import json
import os
import time
import random
from datetime import datetime, timedelta
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 終極持久化版", layout="wide")

# --- 2. 緩存與引擎初始化 ---
CACHE_FILE = "ai_analysis_data.json"
CACHE_TTL = 4 * 3600  # 4 小時更新一次

@st.cache_resource
def init_groq_engines():
    engines = []
    keys = ["GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY"]
    for k in keys:
        if k in st.secrets:
            engines.append(Groq(api_key=st.secrets[k].strip()))
    return engines

groq_pool = init_groq_engines()

# 3. 密碼驗證 (一字不漏)
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]: return True
    st.markdown("### 🖥️ 內部開發監測系統 V7.5.0 (Persistence Build)")
    pwd = st.text_input("請輸入存取密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    return False

if not check_password(): st.stop()

# 4. 全量 CSS 樣式
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; } 
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.08); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .cache-info { background: #f0f2f5; padding: 10px; border-radius: 8px; font-size: 0.85em; color: #595959; margin-bottom: 20px; border: 1px solid #d9d9d9; }
    .news-link { color: #1890ff; text-decoration: none; font-size: 0.85em; display: block; margin-top: 4px; border-bottom: 1px solid #f0f0f0; padding-bottom: 4px; }
    .footer-disclaimer { font-size: 0.75em; color: #8c8c8c; margin-top: 10px; border-top: 1px dashed #d9d9d9; padding-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 📜 免責聲明 (一字不漏)
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 12px; border-radius: 10px; font-size: 0.85em;">
    <b>【免責聲明】</b><br>
    本網頁為個人開發測試，所有分析均為演算法實驗產出，非投資建議。投資盈虧自負。
</div>
""", unsafe_allow_html=True)

# --- 5. 緩存控制邏輯 ---
def load_ai_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_ai_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 6. 核心分析程序 (階梯式排隊) ---
def perform_full_analysis(tickers):
    new_data = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    progress_text = st.empty()
    bar = st.progress(0)
    
    ticker_items = list(tickers.items())
    for idx, (ticker, name) in enumerate(ticker_items):
        progress_text.markdown(f"正在分析 ({idx+1}/{len(tickers)}): **{name}**...")
        bar.progress((idx + 1) / len(tickers))
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            s_info = stock.info
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
            bias = round(((close_val - ma20) / ma20) * 100, 2)
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100
            
            # 使用雙 Key 輪詢並排隊
            if groq_pool:
                client = groq_pool[idx % len(groq_pool)]
                # 排隊延遲，防止 RPM 報錯 (有存檔機制，等一下沒關係)
                time.sleep(random.uniform(6, 10))
                prompt = f"你是投資長。標:{name}, 價:{price}, RSI:{rsi_val:.1f}, 乖離:{bias}%, 斜率:{slope}%. 100字內分析。"
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                new_data["reports"][ticker] = res.choices[0].message.content.strip()
            else:
                new_data["reports"][ticker] = "API Key 缺失，無法分析。"
        except Exception as e:
            new_data["reports"][ticker] = f"分析失敗: {str(e)}"
            
    save_ai_cache(new_data)
    progress_text.empty()
    bar.empty()
    st.success("✅ 全量分析已存檔，正在刷新頁面...")
    time.sleep(1)
    st.rerun()

# --- 7. 主程序渲染 ---
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
cache = load_ai_cache()

# 檢查是否需要執行分析
last_upd_str = cache.get("last_update", "2000-01-01 00:00:00")
last_upd_dt = datetime.strptime(last_upd_str, "%Y-%m-%d %H:%M:%S")
is_expired = (datetime.now() - last_upd_dt).total_seconds() > CACHE_TTL

st.title("🖥️ Beta Lab AI Ultimate - 終極持久化版")

if is_expired:
    st.warning("⚠️ 數據已過期或不存在，正在啟動 4 小時一次的深度分析任務...")
    perform_full_analysis(tickers)

# 介面渲染
st.markdown(f'<div class="cache-info">📅 數據存檔時間：{last_upd_str} (每 4 小時自動更新一次 AI 分析)</div>', unsafe_allow_html=True)

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        s_info = stock.info
        close_val = df['Close'].iloc[-1]
        ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
        rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
        atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
        
        # 從快取抓取分析
        ai_report = cache.get("reports", {}).get(ticker, "等待下一次排程更新中...")
        
        style = "✅" if rsi_val < 50 else "☢️" if rsi_val > 70 else "⚠️"
        if rsi_val < 32: style = "🟣"

        st.markdown(f"""
        <div class="status-card {style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><span style="font-size: 1.6em; font-weight: bold;">{name} ({ticker})</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${round(close_val, 2)}</span></div>
                <span class="metric-tag">RSI: {round(rsi_val, 1)}</span>
            </div>
            <hr>
            <div style="display: flex; gap: 25px;">
                <div style="flex: 2.2;">
                    <b>🧠 存檔分析報告：</b><br><span style="line-height:1.6; font-size:1.1em;">{ai_report}</span>
                    <div class="defense-box">
                        🛡️ <b>風控參考：</b> 
                        <span style="color:#1890ff;">止盈: {round(df['High'].tail(5).max()*0.97, 2)}</span> | 
                        <span style="color:#cf1322; font-weight:bold;">ATR地板: {round(close_val - 2.5*atr_val, 2)}</span>
                    </div>
                    <div class="footer-disclaimer">※ 本報告為 {last_upd_str} 之存檔數據，非實時投資建議。</div>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                    <b>🎯 關鍵價位：</b><br>
                    <span style="font-size:0.85em; color:#666;">🟢 參考買點：{round(ma20-1.2*std20, 2)}</span><br>
                    <span style="font-size:0.85em; color:#666;">🎯 參考壓力：{round(ma20+2*std20, 2)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: continue

if st.button("🚀 立即手動重跑全量 AI 分析"):
    perform_full_analysis(tickers)

# 刷新計時
timer_placeholder = st.empty()
for i in range(60, 0, -1):
    timer_placeholder.markdown(f"🔄 {i}s 後刷新股價 (AI 分析每 4H 更新)")
    time.sleep(1)
st.rerun()
