import streamlit as st
import yfinance as yf
import json
import os
import time
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Beta Lab AI - 實時監測版", layout="wide")

# --- 1. 讀取 GitHub 上的 AI 存檔分析 ---
def load_ai_reports():
    if os.path.exists("analysis_results.json"):
        with open("analysis_results.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_update": "尚未同步", "reports": {}}

# --- 2. 實時抓取數據 (每 60 秒跑一次) ---
def get_realtime_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 抓取最近 5 天數據來計算 RSI 和 MA
        df = stock.history(period="5d") 
        if df.empty: return None
        
        info = stock.info
        close_val = df['Close'].iloc[-1]
        
        # 這裡計算最即時的指標
        return {
            "price": round(close_val, 2),
            "pe": info.get('trailingPE', "---"),
            "growth": f"{round(info.get('revenueGrowth', 0)*100, 1)}%" if info.get('revenueGrowth') else "---",
        }
    except:
        return None

# --- 3. 密碼驗證 ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    pwd = st.text_input("請輸入內部密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 4. 畫面渲染 ---
st.title("🚀 Beta Lab 實時數據 + AI 戰略終端")

# 讀取 AI 存檔 (這部分是 4 小時更新一次的內容)
ai_db = load_ai_reports()
st.sidebar.info(f"🤖 AI 戰略更新時間：\n{ai_db.get('last_update')}")
st.sidebar.write("📈 股價數據：每 60 秒自動刷新")

tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    # A. 抓取實時數據 (現場抓)
    s = get_realtime_data(ticker)
    if not s: continue
    
    # B. 抓取 AI 分析 (從檔案讀)
    report = ai_db.get("reports", {}).get(ticker, "🤖 AI 正在後台運算中...")

    # UI 渲染 (還原你的專業紅框版)
    st.markdown(f"""
    <div style="background:#fff5f5; border-left:15px solid #d32f2f; padding:20px; border-radius:10px; margin-bottom:20px; border:1px solid #ffcdd2;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:1.8em; font-weight:bold;">{name} ({ticker})</span>
                <div style="font-size:3em; font-weight:bold; color:#b71c1c;">${s['price']}</div>
            </div>
            <div style="text-align:right;">
                <span style="background:white; padding:5px 10px; border-radius:5px; border:1px solid #ddd;">
                    本益比: {s['pe']} | 營收成長: {s['growth']}
                </span>
            </div>
        </div>
        <hr>
        <b>🧠 智慧診斷 (AI 戰略存檔)：</b><br>
        <p style="font-size:1.1em; line-height:1.6; color:#333;">{report}</p>
        <div style="font-size:0.75em; color:gray; text-align:right;">數據實時更新於: {datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. 60 秒自動刷新機制 ---
time.sleep(60)
st.rerun()
