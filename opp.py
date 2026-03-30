import streamlit as st
import yfinance as yf
import json
import os
import time
from datetime import datetime

# 必須放在第一行
st.set_page_config(page_title="Beta Lab AI - 實時監測版", layout="wide")

# --- 1. 讀取 GitHub 上的 AI 存檔分析 ---
def load_ai_reports():
    if os.path.exists("analysis_results.json"):
        try:
            with open("analysis_results.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"last_update": "讀取錯誤", "reports": {}}
    return {"last_update": "尚未同步", "reports": {}}

# --- 2. 密碼驗證 ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.markdown("### 🖥️ 內部開發監測系統 V8.5")
    pwd = st.text_input("請輸入內部密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 3. 畫面渲染 ---
st.title("🚀 Beta Lab 實時數據 + AI 戰略終端")

# 讀取存檔
ai_db = load_ai_reports()
st.sidebar.info(f"🤖 AI 戰略更新時間：\n{ai_db.get('last_update')}")

tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

# 佈局定義
for ticker, name in tickers.items():
    try:
        # 實時抓取價格 (不進分析，只拿價格)
        stock = yf.Ticker(ticker)
        df = stock.history(period="1d")
        if df.empty:
            price = "---"
        else:
            price = round(df['Close'].iloc[-1], 2)
        
        # 抓取 AI 報告
        report = ai_db.get("reports", {}).get(ticker, "🤖 AI 正在後台運算中...")

        # UI 渲染
        st.markdown(f"""
        <div style="background:#fff5f5; border-left:15px solid #d32f2f; padding:20px; border-radius:10px; margin-bottom:20px; border:1px solid #ffcdd2;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:1.8em; font-weight:bold;">{name} ({ticker})</span>
                    <div style="font-size:3em; font-weight:bold; color:#b71c1c;">${price}</div>
                </div>
            </div>
            <hr>
            <b>🧠 智慧診斷 (AI 戰略存檔)：</b><br>
            <p style="font-size:1.1em; line-height:1.6; color:#333;">{report}</p>
            <div style="font-size:0.75em; color:gray; text-align:right;">實時刷新於: {datetime.now().strftime('%H:%M:%S')}</div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"無法加載 {name}: {e}")

# 每 60 秒自動刷新
time.sleep(60)
st.rerun()
