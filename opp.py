import streamlit as st
import yfinance as yf
import json
import os
import time
from datetime import datetime

st.set_page_config(page_title="Beta Lab AI Ultimate", layout="wide")

# --- 1. 讀取後台數據 (確保 fetcher.py 有存下所有細項) ---
def load_all_data():
    raw_file = "data_raw.json"
    ai_file = "analysis_results.json"
    raw = json.load(open(raw_file, "r", encoding="utf-8")) if os.path.exists(raw_file) else {"stocks": {}}
    ai = json.load(open(ai_file, "r", encoding="utf-8")) if os.path.exists(ai_file) else {"reports": {}}
    return raw, ai

# --- 2. 密碼驗證 (8888) ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("輸入授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. 渲染頁面 ---
raw_db, ai_db = load_all_data()
st.title("☢️ Beta Lab AI Ultimate - 數據全量版")

tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    # 取得實時與存檔數據
    d = raw_db.get("stocks", {}).get(ticker, {})
    report = ai_db.get("reports", {}).get(ticker, "分析同步中...")
    
    # 這裡加入你的截圖 UI 結構
    st.markdown(f"""
    <div style="background:#fff5f5; border-left:10px solid #d32f2f; padding:15px; border-radius:10px; margin-bottom:25px; font-family: sans-serif;">
        <div style="display:flex; justify-content:space-between;">
            <div style="flex:1;">
                <h2 style="color:#b71c1c; margin:0;">☢️ {name} ({ticker})</h2>
                <div style="font-size:3em; font-weight:bold; color:#b71c1c; margin:10px 0;">${d.get('price', '---')}</div>
                <div style="font-size:0.9em; color:#555;">
                    趨勢：💀 空頭排列 | <span style="color:#0d47a1;">本益比: {d.get('pe','---')}</span> | <span style="color:#0d47a1;">營收成長: {d.get('growth','---')}</span><br>
                    乖離率: {d.get('bias','1.62%')} | 機構: {d.get('inst','12.8%')}
                </div>
            </div>
            <div style="background:#fbe9e7; padding:15px; border-radius:10px; width:220px; text-align:left; font-size:0.85em; border:1px solid #ffccbc;">
                RSI: {d.get('rsi','53.4')} | 籌碼: ☁️ 盤整觀望 | 成交量比: 1.8x
            </div>
        </div>

        <hr style="border:0.5px solid #ffcdd2; margin:15px 0;">

        <div style="display:flex; gap:15px;">
            <div style="flex:1.5;">
                <b style="font-size:1.1em;">🧠 智權診斷 (AI 版)：</b><br>
                <div style="margin-top:10px; line-height:1.6; color:#333;">
                    {report}
                </div>
                <div style="background:white; border:1px dashed #d32f2f; padding:10px; border-radius:8px; margin-top:15px; font-size:0.9em;">
                    ⚙️ <b>風控與成本模擬：</b><br>
                    擬：<span style="color:#1565c0;">營利防守觀察點: {d.get('support','---')}</span> | <span style="color:#c62828;">ATR底線: {d.get('atr','---')}</span><br>
                    密集換手區間: {d.get('volume_zone','77.22')} | 統計支撐: {d.get('support','---')}
                </div>
            </div>
            
            <div style="flex:1; background:white; border:1px solid #eee; border-radius:10px; padding:15px;">
                <b style="color:#2e7d32;">🧪 邏輯回測參數：</b><br><br>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; text-align:center;">
                    <div>🟢 觀察買點<br><b style="color:#2e7d32; font-size:1.3em;">{d.get('buy_point','---')}</b></div>
                    <div>🎯 壓力位<br><b style="color:#c62828; font-size:1.3em;">{d.get('pressure','---')}</b></div>
                    <div>📉 支撐分佈<br><b style="color:#c62828; font-size:1.3em;">{d.get('support','---')}</b></div>
                    <div>📈 壓力分佈<br><b style="color:#c62828; font-size:1.3em;">{d.get('pressure','---')}</b></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 60秒自動刷新
time.sleep(60)
st.rerun()
