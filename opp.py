import streamlit as st
import json
import os
import time

# 頁面基本配置
st.set_page_config(page_title="Beta Lab AI - 終極顯示端", layout="wide")

# --- 1. 讀取機器人存好的數據 ---
def load_github_data():
    analysis = {"last_update": "未更新", "reports": {}}
    raw = {"stocks": {}}
    
    # 讀取 AI 分析結果
    if os.path.exists("analysis_results.json"):
        with open("analysis_results.json", "r", encoding="utf-8") as f:
            analysis = json.load(f)
            
    # 讀取原始股價數據
    if os.path.exists("data_raw.json"):
        with open("data_raw.json", "r", encoding="utf-8") as f:
            raw = json.load(f)
            
    return analysis, raw

# --- 2. 密碼驗證 ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.markdown("### 🖥️ 內部開發監測系統 V8.5 (Cloud Sync)")
    pwd = st.text_input("請輸入密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- 3. 畫面渲染 ---
st.title("🖥️ Beta Lab AI - 自動化分析顯示端")
res_db, raw_db = load_github_data()

st.info(f"📅 AI 最後診斷時間：{res_db.get('last_update')} (系統每 4 小時自動更新)")

tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    # 抓取數據與分析
    stock_info = raw_db.get("stocks", {}).get(ticker, {})
    price = stock_info.get("price", "---")
    rsi = stock_info.get("rsi", 0)
    report = res_db.get("reports", {}).get(ticker, "🤖 機器人正在排隊分析中...")
    
    # UI 顏色邏輯 (紫色超跌)
    color = "#722ed1" if (isinstance(rsi, (int, float)) and rsi < 32) else "#52c41a"

    st.markdown(f"""
    <div style="padding:22px; border-radius:15px; border-left:12px solid {color}; background:#fcfcfc; margin-bottom:25px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #eee;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:1.6em; font-weight:bold;">{name}</span>
                <span style="font-size:0.9em; color:gray; margin-left:10px;">{ticker}</span>
            </div>
            <span style="font-size:2.2em; font-family:monospace; font-weight:bold;">${price}</span>
        </div>
        <div style="color:gray; font-size:0.85em; margin: 10px 0;">RSI 強弱指標: {rsi}</div>
        <hr style="border:0.5px solid #eee;">
        <div style="margin-top:15px;">
            <b style="font-size:1.1em; color:#333;">🧠 AI 投資長診斷：</b><br>
            <p style="line-height:1.7; font-size:1.15em; color:#444; margin-top:8px;">{report}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 顯示端只需要 10 分鐘同步一次即可
time.sleep(600)
st.rerun()
