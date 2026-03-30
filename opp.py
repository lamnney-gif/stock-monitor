import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import random
import json
from datetime import datetime
from sklearn.linear_model import LinearRegression
from groq import Groq

# 1. 頁面基礎配置
st.set_page_config(page_title="Beta Lab AI Ultimate - 雙核版", layout="wide")

# --- 2. 雙核引擎：故障轉移系統 ---
@st.cache_resource
def get_groq_engines():
    engines = []
    # 這裡會從 Streamlit Secrets 抓取所有 Key
    for k in ["GROQ_API_KEY_1", "GROQ_API_KEY_2", "GROQ_API_KEY"]:
        if k in st.secrets:
            engines.append({"name": k, "client": Groq(api_key=st.secrets[k].strip())})
    return engines

# 3. 密碼驗證 (一字不漏)
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]: return True
    st.markdown("### 🖥️ 內部開發監測系統 V8.0.0 (Failover Edition)")
    pwd = st.text_input("請輸入存取密碼：", type="password", key="login_pwd")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    return False

if not check_password(): st.stop()

# 4. 全量 CSS 樣式 (100% 物理還原)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .✅ { background-color: #f6ffed; border-left: 12px solid #52c41a; color: #135200; } 
    .🚨 { background-color: #fff1f0; border-left: 12px solid #f5222d; color: #820014; } 
    .⚠️ { background-color: #fffbe6; border-left: 12px solid #ffc53d; color: #874d00; } 
    .🟣 { background-color: #f9f0ff; border-left: 12px solid #722ed1; color: #531dab; } 
    .metric-tag { display: inline-block; padding: 5px 12px; background: rgba(0,0,0,0.08); border-radius: 8px; margin-right: 12px; font-size: 0.9em; font-weight: 600; }
    .defense-box { background: rgba(255, 255, 255, 0.8); border: 1.5px dashed #434343; padding: 12px; border-radius: 10px; margin-top: 15px; font-size: 0.95em; }
    .engine-label { font-size: 0.7em; background: #333; color: white; padding: 2px 8px; border-radius: 4px; margin-bottom: 8px; display: inline-block; }
    .footer-disclaimer { font-size: 0.75em; color: #8c8c8c; margin-top: 10px; border-top: 1px dashed #d9d9d9; padding-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 📜 免責聲明
st.sidebar.error("⚠️ 【開發者自用測試區】")
st.sidebar.markdown("""
<div style="background-color: #ffffff; border: 2px solid #ff4b4b; padding: 12px; border-radius: 10px; font-size: 0.85em;">
    <b>【免責聲明】</b><br>
    本網頁為個人開發測試，診斷報告非投資建議。投資盈虧自負。
</div>
""", unsafe_allow_html=True)

# --- 5. 核心分析邏輯：智慧換 Key 機制 ---
def perform_smart_analysis(idx, name, price, rsi, bias, slope):
    engines = get_groq_engines()
    if not engines: return "❌ 找不到 API Key"
    
    # 嘗試順序：優先使用輪到的 Key，若失敗則嘗試下一個
    primary_idx = idx % len(engines)
    attempt_list = [engines[i % len(engines)] for i in range(primary_idx, primary_idx + len(engines))]
    
    prompt = f"你是投資長。標:{name}, 價:{price}, RSI:{rsi:.1f}, 乖離:{bias}%, 斜率:{slope}%. 100字內分析。"
    
    last_err = ""
    for eng in attempt_list:
        try:
            # 即使換 Key 也強制延遲，防止併發報錯
            time.sleep(random.uniform(5, 8))
            res = eng["client"].chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            return f"🦅 [{eng['name']}] " + res.choices[0].message.content.strip()
        except Exception as e:
            last_err = str(e)
            if "429" in last_err: # 偵測到 Token 額度上限
                continue # 自動跳到下一個引擎
            return f"❌ 系統錯誤: {last_err}"
            
    return f"🚨 今日額度已全數耗盡 (429 Error)。最後錯誤: {last_err}"

# --- 6. 數據持久化區 (記憶體) ---
if "ai_db" not in st.session_state:
    st.session_state["ai_db"] = {"last_upd": "尚未更新", "reports": {}}

# --- 7. 主程序 ---
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

st.title("🖥️ Beta Lab AI Ultimate - 雙核防崩潰版")

# 分析執行按鈕
if st.button("🚀 啟動全量 AI 診斷 (雙 Key 自動切換模式)"):
    progress_bar = st.progress(0)
    status_msg = st.empty()
    new_reports = {}
    
    ticker_items = list(tickers.items())
    for i, (ticker, name) in enumerate(ticker_items):
        status_msg.markdown(f"🔍 正在診斷: **{name}** ({i+1}/{len(tickers)})")
        progress_bar.progress((i + 1) / len(tickers))
        
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
            bias = round(((close_val - ma20) / ma20) * 100, 2)
            slope = (LinearRegression().fit(np.arange(10).reshape(-1,1), df['Close'].tail(10).values.reshape(-1,1)).coef_[0][0] / close_val) * 100
            
            # 執行智慧分析
            report = perform_smart_analysis(i, name, round(close_val, 2), rsi_val, bias, round(slope, 2))
            new_reports[ticker] = report
        except Exception as e:
            new_reports[ticker] = f"數據抓取失敗: {str(e)}"
            
    st.session_state["ai_db"] = {
        "last_upd": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reports": new_reports
    }
    status_msg.empty()
    progress_bar.empty()
    st.rerun()

# --- 8. 顯示結果卡片 ---
st.info(f"📅 上次 AI 全量更新時間：{st.session_state['ai_db']['last_upd']}")

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        close_val = df['Close'].iloc[-1]
        ma20, std20 = df['Close'].rolling(20).mean().iloc[-1], df['Close'].rolling(20).std().iloc[-1]
        rsi_val = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
        atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
        
        # 從記憶體抓取報告
        ai_report = st.session_state["ai_db"]["reports"].get(ticker, "尚未執行診斷。請點擊上方按鈕。")
        
        # 狀態標籤判定
        style = "✅" if "🦅" in ai_report else "🚨"
        if rsi_val < 32: style = "🟣"
        elif rsi_val > 70: style = "⚠️"

        st.markdown(f"""
        <div class="status-card {style}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div><span style="font-size: 1.6em; font-weight: bold;">{name} ({ticker})</span><span style="font-size: 2.2em; margin-left: 20px; font-family: monospace; font-weight: bold;">${round(close_val, 2)}</span></div>
                <span class="metric-tag">RSI: {round(rsi_val, 1)}</span>
            </div>
            <hr>
            <div style="display: flex; gap: 25px;">
                <div style="flex: 2.2;">
                    <b>🧠 智慧診斷報告：</b><br>
                    <span style="line-height:1.6; font-size:1.1em;">{ai_report}</span>
                    <div class="defense-box">
                        ⚙️ 風控地板： <span style="color:#cf1322; font-weight:bold;">${round(close_val - 2.5*atr_val, 2)}</span> | 
                        止盈線： <span style="color:#1890ff;">${round(df['High'].tail(5).max()*0.97, 2)}</span>
                    </div>
                </div>
                <div style="flex: 1; background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; border: 1px solid #d9d9d9;">
                    <b>🎯 關鍵參考價：</b><br>
                    <span style="font-size:0.85em; color:#666;">🟢 買點：{round(ma20-1.2*std20, 2)}</span><br>
                    <span style="font-size:0.85em; color:#666;">🎯 壓力：{round(ma20+2*std20, 2)}</span>
                </div>
            </div>
            <div class="footer-disclaimer">※ 數據來源: Yahoo Finance | 診斷引擎: GROQ Llama-3.3</div>
        </div>
        """, unsafe_allow_html=True)
    except: continue

# 每 60 秒刷新股價 (不刷新 AI)
time.sleep(60)
st.rerun()
