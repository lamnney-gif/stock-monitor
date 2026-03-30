import streamlit as st
import yfinance as yf
import json
import os
import time

st.set_page_config(page_title="Beta Lab AI - 戰情顯示端", layout="wide")

# 1. 讀取機器人存好的 JSON (這就是你的 A/B 數據中繼)
def load_cached_data():
    results = {"last_update": "尚未更新", "reports": {}}
    raw = {"stocks": {}}
    
    if os.path.exists("analysis_results.json"):
        with open("analysis_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
            
    if os.path.exists("data_raw.json"):
        with open("data_raw.json", "r", encoding="utf-8") as f:
            raw = json.load(f)
    return results, raw

# 2. 密碼驗證 (保持一致)
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    pwd = st.text_input("請輸入密碼：", type="password")
    if pwd == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# 顯示介面
st.title("🖥️ Beta Lab AI - 自動化分析顯示端")
res_db, raw_db = load_cached_data()

st.info(f"📅 AI 最後診斷時間：{res_db.get('last_update')} (每 4 小時自動更新)")

# 3. 渲染卡片
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    # 抓取原始數據 (來自 data_raw.json)
    stock_info = raw_db.get("stocks", {}).get(ticker, {})
    price = stock_info.get("price", "---")
    rsi = stock_info.get("rsi", "---")
    
    # 抓取 AI 報告 (來自 analysis_results.json)
    report = res_db.get("reports", {}).get(ticker, "🤖 機器人正在排隊分析中...")
    
    # UI 渲染 (紫色超跌邏輯保留)
    card_style = "🟣" if (isinstance(rsi, (int, float)) and rsi < 32) else "✅"
    
    st.markdown(f"""
    <div style="padding:20px; border-radius:15px; border-left:10px solid {'#722ed1' if card_style=='🟣' else '#52c41a'}; background:#f9f9f9; margin-bottom:20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05);">
        <div style="display:flex; justify-content:space-between;">
            <span style="font-size:1.5em; font-weight:bold;">{name} ({ticker})</span>
            <span style="font-size:1.8em; font-family:monospace;">${price}</span>
        </div>
        <div style="color:gray; font-size:0.9em; margin-bottom:10px;">RSI 指標: {rsi}</div>
        <hr>
        <b>🧠 存檔分析報告：</b><br>
        <p style="line-height:1.6; font-size:1.1em;">{report}</p>
    </div>
    """, unsafe_allow_html=True)

# 顯示端不需要頻繁重新整理，設定 10 分鐘刷新一次即可
time.sleep(600)
st.rerun()
