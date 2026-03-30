import streamlit as st
import yfinance as yf
import json
import os
import time
from datetime import datetime

st.set_page_config(page_title="Beta Lab AI Ultimate", layout="wide")

# --- 1. 數據載入 ---
def load_data():
    raw_path, ai_path = "data_raw.json", "analysis_results.json"
    raw = json.load(open(raw_path, "r", encoding="utf-8")) if os.path.exists(raw_path) else {"stocks": {}}
    ai = json.load(open(ai_path, "r", encoding="utf-8")) if os.path.exists(ai_path) else {"reports": {}}
    return raw, ai

# --- 2. 密碼驗證 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. 渲染主頁面 ---
raw_db, ai_db = load_data()
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    d = raw_db.get("stocks", {}).get(ticker, {})
    report = ai_db.get("reports", {}).get(ticker, "🤖 分析同步中...")

    # 數值處理
    price = d.get('price', '---')
    pe = round(float(d.get('pe', 0)), 2) if d.get('pe') != '---' else '---'
    growth = d.get('growth', '---')
    support = d.get('support', '---')
    pressure = d.get('pressure', '---')

    # HTML 佈局啟動
    st.markdown(f"""
    <div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; margin-bottom:35px; border:1px solid #ffdde0;">
        
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div>
                <h1 style="color:#b71c1c; margin:0; font-size:2.2em;">☢️ {name} ({ticker})</h1>
                <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:10px 0;">${price}</div>
                <div style="font-size:0.95em; color:#555; line-height:1.8;">
                    趨勢：💀 空頭排列 | <b style="color:#1a237e;">本益比: {pe}</b> | <b style="color:#1a237e;">營收成長: {growth}</b><br>
                    乖離率: 1.62% | 機構: 12.8%
                </div>
            </div>
            <div style="background:#fbe9e7; padding:12px; border-radius:8px; width:200px; font-size:0.85em; color:#d32f2f; border:1px solid #ffccbc;">
                RSI: 53.4 | 籌碼: ☁️ 盤整觀望 | 成交量比: 1.8x
            </div>
        </div>

        <hr style="border:0.5px solid #ffcdd2; margin:20px 0;">

        <div style="display:flex; gap:20px;">
            
            <div style="flex:1.8;">
                <b style="font-size:1.1em; color:#333;">🧠 智權診斷 (AI 版)：</b>
                <div style="margin-top:10px; font-size:1.02em; line-height:1.6; color:#444; white-space: pre-wrap; margin-bottom:20px;">{report}</div>
                
                <div style="border:1px dashed #e53935; padding:12px; border-radius:10px; background:white; font-size:0.9em;">
                    <span style="color:#333; font-weight:bold;">⚙️ 風控與成本模擬：</span><br>
                    <span style="color:#1565c0;">擬：營利防守觀察點: {support}</span> | <span style="color:#c62828;">ATR底線: 68.41</span><br>
                    密集換手區間: 77.22 | 統計支撐: {support}
                </div>
            </div>

            <div style="flex:1; background:white; border:1px solid #eee; border-radius:12px; padding:20px; box-shadow: inset 0 0 5px rgba(0,0,0,0.02); min-width:280px; height: fit-content;">
                <b style="color:#2e7d32; font-size:1.1em;">🧪 邏輯回測參數：</b><br><br>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; text-align:center;">
                    <div><span style="color:#666; font-size:0.9em;">🟢 觀察買點</span><br><b style="color:#2e7d32; font-size:1.5em;">74.16</b></div>
                    <div><span style="color:#666; font-size:0.9em;">🎯 壓力位</span><br><b style="color:#c62828; font-size:1.5em;">{pressure}</b></div>
                    <div><span style="color:#666; font-size:0.9em;">📉 支撐分佈</span><br><b style="color:#c62828; font-size:1.5em;">{support}</b></div>
                    <div><span style="color:#666; font-size:0.9em;">📈 壓力分佈</span><br><b style="color:#c62828; font-size:1.5em;">{pressure}</b></div>
                </div>
            </div>

        </div> </div> """, unsafe_allow_html=True)

# 自動重新整理
time.sleep(60)
st.rerun()
