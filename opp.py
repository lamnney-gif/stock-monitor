import streamlit as st
import yfinance as yf
import json
import os
import time
from datetime import datetime

st.set_page_config(page_title="Beta Lab AI - 實時終端", layout="wide")

# 1. 讀取 AI 存檔
def get_ai_data():
    if os.path.exists("analysis_results.json"):
        with open("analysis_results.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_update": "尚未同步", "reports": {}}

# 2. 密碼驗證
if "pwd" not in st.session_state: st.session_state["pwd"] = False
if not st.session_state["pwd"]:
    if st.text_input("密碼", type="password") == "8888":
        st.session_state["pwd"] = True
        st.rerun()
    st.stop()

# 3. 顯示介面
st.title("🖥️ 半導體大戶實時戰情室")
ai_db = get_ai_data()
st.sidebar.info(f"📅 AI 戰略更新：{ai_db.get('last_update')}")

tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    # 現場抓最新價格 (保證 60 秒更新)
    try:
        df = yf.Ticker(ticker).history(period="1d")
        real_price = round(df['Close'].iloc[-1], 2) if not df.empty else "---"
    except:
        real_price = "---"
    
    report = ai_db.get("reports", {}).get(ticker, "🤖 分析同步中...")

    st.markdown(f"""
    <div style="background:#fff5f5; border-left:15px solid #d32f2f; padding:20px; border-radius:10px; margin-bottom:20px; border:1px solid #ffcdd2;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div><span style="font-size:1.5em; font-weight:bold;">{name}</span></div>
            <div style="font-size:2.5em; font-weight:bold; color:#b71c1c;">${real_price}</div>
        </div>
        <hr>
        <b>🧠 AI 戰略報告：</b><br>
        <p>{report}</p>
        <div style="font-size:0.8em; color:gray; text-align:right;">價格更新時間：{datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

# 4. 60 秒自動刷新
time.sleep(60)
st.rerun()
