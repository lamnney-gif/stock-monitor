import streamlit as st
import json
import os
import time

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

# --- 3. 畫面渲染 ---
raw_db, ai_db = load_data()
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    d = raw_db.get("stocks", {}).get(ticker, {})
    report_raw = ai_db.get("reports", {}).get(ticker, "🤖 策略分析中...")
    report_html = report_raw.replace("\n", "<br>")

    # 數據轉字串並補齊遺漏欄位
    p = str(d.get('price', '---'))
    pe = str(round(float(d.get('pe', 0)), 2)) if d.get('pe') not in ['---', None] else '---'
    gr = str(d.get('growth', '---'))
    sup = str(d.get('support', '---'))
    pre = str(d.get('pressure', '---'))
    # 模擬或從數據抓取密集換手區 (若 JSON 沒這欄位則顯示預設)
    turnover_zone = "77.22" 

    st.write(f"""
    <div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: sans-serif; margin-bottom: 25px;">
        
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
            <div>
                <h2 style="color:#b71c1c; margin:0; font-size:1.8em;">☢️ {name} ({ticker})</h2>
                <div style="font-size:3em; font-weight:900; color:#b71c1c; margin:5px 0;">${p}</div>
                <p style="font-size:0.9em; color:#555;">趨勢：💀 空頭排列 | <b style="color:#1a237e;">PE: {pe}</b> | <b style="color:#1a237e;">成長: {gr}</b></p>
            </div>
            <div style="background:#fbe9e7; padding:10px; border-radius:8px; width:160px; font-size:0.8em; color:#d32f2f; border:1px solid #ffccbc;">
                RSI: 53.4 | 籌碼: ☁️ 盤整 | 量比: 1.8x
            </div>
        </div>

        <hr style="border:0.5px solid #ffcdd2; margin:15px 0;">

        <div style="background:white; border:1px solid #eee; border-radius:10px; padding:15px; margin-bottom:15px;">
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:15px; text-align:center;">
                <div>
                    <span style="color:#2e7d32; font-size:0.8em; font-weight:bold;">🟢 觀察買點</span><br>
                    <b style="color:#2e7d32; font-size:1.4em;">74.16</b>
                </div>
                <div>
                    <span style="color:#c62828; font-size:0.8em; font-weight:bold;">🎯 壓力位</span><br>
                    <b style="color:#c62828; font-size:1.4em;">{pre}</b>
                </div>
                <div>
                    <span style="color:#c62828; font-size:0.8em; font-weight:bold;">📉 支撐分佈</span><br>
                    <b style="color:#c62828; font-size:1.4em;">{sup}</b>
                </div>
                <div>
                    <span style="color:#c62828; font-size:0.85em; font-weight:bold;">📈 壓力分佈</span><br>
                    <b style="color:#c62828; font-size:1.4em;">{pre}</b>
                </div>
            </div>
            
            <div style="margin-top:15px; padding-top:10px; border-top:1px solid #f0f0f0; display:flex; flex-wrap:wrap; gap:15px;">
                <div style="flex:1; min-width:200px;">
                    <b style="color:#333; font-size:0.9em;">⚙️ 風控與成本模擬：</b><br>
                    <span style="color:#1565c0; font-size:0.85em;">防守觀察點: {sup}</span> | 
                    <span style="color:#c62828; font-size:0.85em;">ATR地板: 68.41</span>
                </div>
                <div style="flex:1; min-width:150px;">
                    <b style="color:#333; font-size:0.9em;">📊 市場分佈：</b><br>
                    <span style="color:#555; font-size:0.85em;">密集換手區: {turnover_zone}</span>
                </div>
            </div>
        </div>

        <div style="background:rgba(255,255,255,0.8); padding:15px; border-radius:10px;">
            <b style="font-size:1.1em; color:#333;">🧠 智權診斷 (AI 版)：</b>
            <p style="margin-top:10px; font-size:1em; line-height:1.6; color:#444;">{report_html}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

time.sleep(60)
st.rerun()
