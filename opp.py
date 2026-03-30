import streamlit as st
import yfinance as yf
import json
import os
import time
from datetime import datetime

st.set_page_config(page_title="Beta Lab AI Ultimate", layout="wide")

# --- 1. 數據載入 ---
def load_data():
    raw_p, ai_p = "data_raw.json", "analysis_results.json"
    r = json.load(open(raw_p, "r", encoding="utf-8")) if os.path.exists(raw_p) else {"stocks": {}}
    a = json.load(open(ai_p, "r", encoding="utf-8")) if os.path.exists(ai_p) else {"reports": {}}
    return r, a

# --- 2. 密碼驗證 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. 渲染戰術介面 ---
raw_db, ai_db = load_data()
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    d = raw_db.get("stocks", {}).get(ticker, {})
    # 關鍵修正：將 AI 報告中的換行符號替換為 HTML 的換行，防止格式崩潰
    report_text = ai_db.get("reports", {}).get(ticker, "🤖 分析同步中...")
    report_html = report_text.replace("\n", "<br>")

    # 數據預處理
    p = str(d.get('price', '---'))
    pe = str(round(float(d.get('pe', 0)), 2)) if d.get('pe') not in ['---', None] else '---'
    gr = str(d.get('growth', '---'))
    sup = str(d.get('support', '---'))
    pre = str(d.get('pressure', '---'))

    # 定義模板 (使用 {{ }} 避開 CSS 大括號衝突)
    template = """
    <div style="background:#fff9f9; border-left:12px solid #e53935; padding:15px; border-radius:12px; margin-bottom:30px; border:1px solid #ffdde0; font-family: sans-serif;">
        
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap: wrap;">
            <div style="min-width: 200px;">
                <h1 style="color:#b71c1c; margin:0; font-size:2em;">☢️ {name} ({ticker})</h1>
                <div style="font-size:3em; font-weight:900; color:#b71c1c; margin:5px 0;">${price}</div>
                <div style="font-size:0.9em; color:#555; margin-bottom:10px;">
                    趨勢：💀 空頭排列 | <b style="color:#1a237e;">PE: {pe}</b> | <b style="color:#1a237e;">成長: {gr}</b>
                </div>
            </div>
            <div style="background:#fbe9e7; padding:10px; border-radius:8px; width:100%; max-width:200px; font-size:0.8em; color:#d32f2f; border:1px solid #ffccbc; margin-bottom:10px;">
                RSI: 53.4 | 籌碼: ☁️ 盤整 | 量比: 1.8x
            </div>
        </div>

        <hr style="border:0.5px solid #ffcdd2; margin:10px 0;">

        <div style="background:white; border:1px solid #eee; border-radius:10px; padding:15px; margin-bottom:15px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap: wrap; gap:10px;">
                <div style="flex:1; min-width:140px; text-align:center; border-right:1px solid #eee;">
                    <span style="color:#2e7d32; font-size:0.85em; font-weight:bold;">🟢 觀察買點</span><br>
                    <b style="color:#2e7d32; font-size:1.4em;">74.16</b>
                </div>
                <div style="flex:1; min-width:140px; text-align:center; border-right:1px solid #eee;">
                    <span style="color:#c62828; font-size:0.85em; font-weight:bold;">🎯 壓力位</span><br>
                    <b style="color:#c62828; font-size:1.4em;">{pressure}</b>
                </div>
                <div style="flex:1.5; min-width:200px; padding-left:10px;">
                    <b style="color:#333; font-size:0.9em;">⚙️ 風控與成本：</b><br>
                    <span style="color:#1565c0; font-size:0.85em;">防守點: {support}</span><br>
                    <span style="color:#c62828; font-size:0.85em;">ATR地板: 68.41</span>
                </div>
            </div>
        </div>

        <div style="background:rgba(255,255,255,0.5); padding:15px; border-radius:10px;">
            <b style="font-size:1.1em; color:#333;">🧠 智權診斷 (AI 版)：</b>
            <div style="margin-top:10px; font-size:1.05em; line-height:1.6; color:#444;">
                {report}
            </div>
        </div>
    </div>
    """

    # 使用 .format() 填充，這樣就不會被 Python f-string 的大括號邏輯干擾
    full_html = template.format(
        name=name, ticker=ticker, price=p, pe=pe, gr=gr, 
        pressure=pre, support=sup, report=report_html
    )
    
    st.markdown(full_html, unsafe_allow_html=True)

# 每 60 秒刷新一次
time.sleep(60)
st.rerun()
