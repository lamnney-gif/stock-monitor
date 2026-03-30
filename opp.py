import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import json
import time
import random
from datetime import datetime, timedelta
from urllib.parse import quote
from sklearn.linear_model import LinearRegression
from groq import Groq

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 記憶體強化版", layout="wide")

# --- 2. 核心：記憶體緩存機制 (取代實體檔案) ---
if "ai_database" not in st.session_state:
    st.session_state["ai_database"] = {"last_update": "尚未更新", "reports": {}}

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

if not st.session_state["password_correct"]:
    st.markdown("### 🖥️ 內部開發監測系統 V7.6.0 (Cloud Memory)")
    pwd = st.text_input("請輸入存取密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# 4. 全量 CSS 樣式
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .🚨 { background-color: #fff5f5; border-left: 12px solid #ff4d4f; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; } 
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; } 
    .☢️ { background-color: #fff1f0; border-left: 12px solid #f5222d; } 
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.08); border-radius: 8px; margin-right: 12px; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 📜 免責聲明
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("本系統為 AI 自動化實驗產出，非投資建議。")

# --- 5. 核心：分析模式 (直接寫入記憶體) ---
def run_full_analysis(tickers):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    ticker_items = list(tickers.items())
    temp_reports = {}
    
    for idx, (ticker, name) in enumerate(ticker_items):
        status_text.markdown(f"🚀 正在派遣 AI 分析師：**{name}** ({idx+1}/{len(tickers)})")
        progress_bar.progress((idx + 1) / len(tickers))
        
        try:
            # 基本數據抓取
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo")
            if df.empty: continue
            
            close_p = df['Close'].iloc[-1]
            # 呼叫雙 GROQ 引擎
            if groq_pool:
                client = groq_pool[idx % len(groq_pool)]
                # 排隊等待時間 (解決 RPM 限制)
                time.sleep(random.uniform(8, 12)) 
                
                prompt = f"你是投資長。標:{name}, 價:{close_p}. 100字內狠準狂分析。"
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}]
                )
                temp_reports[ticker] = res.choices[0].message.content.strip()
            else:
                temp_reports[ticker] = "❌ 未設定 API Key"
        except Exception as e:
            temp_reports[ticker] = f"⚠️ 分析中斷: {str(e)}"
            
    # 更新到全局記憶體
    st.session_state["ai_database"] = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reports": temp_reports
    }
    status_text.empty()
    progress_bar.empty()
    st.success("✅ 9 檔股票全量分析完畢！數據已存入雲端記憶體。")
    time.sleep(1)
    st.rerun()

# --- 6. 主程序渲染 ---
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

st.title("🖥️ Beta Lab AI Ultimate - 雲端記憶體版")

# 判斷是否需要初始更新
if st.session_state["ai_database"]["last_update"] == "尚未更新":
    if st.button("🔴 點擊啟動首次 AI 全量分析 (需排隊約 2 分鐘)"):
        run_full_analysis(tickers)
else:
    st.info(f"📅 上次更新時間：{st.session_state['ai_database']['last_update']}")
    
    # 顯示 9 檔卡片
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
            
            # 從記憶體抓取報告
            report = st.session_state["ai_database"]["reports"].get(ticker, "尚未分析。")
            
            style = "✅" if rsi_val < 55 else "☢️"
            st.markdown(f"""
            <div class="status-card {style}">
                <div style="display: flex; justify-content: space-between;">
                    <span style="font-size: 1.5em; font-weight: bold;">{name}</span>
                    <span style="font-size: 1.5em; font-family: monospace;">${round(close_val, 2)}</span>
                </div>
                <hr>
                <b>🧠 AI 投資長分析：</b><br>{report}
            </div>
            """, unsafe_allow_html=True)
        except: continue

    if st.button("🚀 手動刷新 AI 分析"):
        run_full_analysis(tickers)

# 每分鐘刷新股價
time.sleep(60)
st.rerun()
