import streamlit as st
import json
import os
import time

st.set_page_config(page_title="Beta Lab AI Ultimate - 數據全量版", layout="wide")

# 1. 數據加載
def load_all_data():
    res, raw = {"reports": {}}, {"stocks": {}}
    if os.path.exists("analysis_results.json"):
        with open("analysis_results.json", "r", encoding="utf-8") as f: res = json.load(f)
    if os.path.exists("data_raw.json"):
        with open("data_raw.json", "r", encoding="utf-8") as f: raw = json.load(f)
    return res, raw

# 2. 密碼驗證
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False
if not st.session_state["password_correct"]:
    if st.text_input("請輸入密碼", type="password") == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# 3. 介面渲染
st.title("☢️ Beta Lab AI Ultimate - 數據全量顯示端")
res_db, raw_db = load_all_data()

# 自定義 CSS 還原截圖質感
st.markdown("""
<style>
    .stock-card { background: #fff5f5; border-left: 15px solid #d32f2f; padding: 25px; border-radius: 10px; margin-bottom: 30px; border: 1px solid #ffcdd2; }
    .metric-row { display: flex; gap: 15px; margin-top: 10px; color: #555; font-size: 0.9em; }
    .side-box { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; }
    .price-big { font-size: 3.5em; font-weight: bold; color: #b71c1c; font-family: 'Courier New'; }
    .defense-section { background: #ffffff; border: 1.5px dashed #444; padding: 15px; border-radius: 10px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    s = raw_db.get("stocks", {}).get(ticker, {})
    report = res_db.get("reports", {}).get(ticker, "🤖 分析生成中...")
    
    # 建立與截圖一致的佈局
    col1, col2 = st.columns([2.5, 1])
    
    with col1:
        st.markdown(f"""
        <div class="stock-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-size:2em; font-weight:bold;">☢️ {name} ({ticker})</span>
                    <div class="price-big">${s.get('price', '---')}</div>
                </div>
                <div style="text-align:right; background:rgba(255,255,255,0.5); padding:10px; border-radius:8px;">
                    <span style="color:#d32f2f; font-weight:bold;">RSI: {s.get('rsi')} | 籌碼：盤整</span><br>
                    成交量比: 1.8x
                </div>
            </div>
            <div class="metric-row">
                <b>趨勢: 💀 空頭排列</b> | <b>本益比: {s.get('pe')}</b> | <b style="color:#1890ff;">營收成長: {s.get('growth')}</b>
            </div>
            <hr>
            <div>
                <b>🧠 智權診斷 (AI 版)：</b><br>
                <p style="font-size:1.1em; line-height:1.6;">{report}</p>
            </div>
            <div class="defense-section">
                ⚙️ <b>風控與成本模組</b><br>
                擬：營利防守點：<span style="color:#1890ff;">{s.get('defense_line')}</span> | 
                <span style="color:#d32f2f; font-weight:bold;">ATR地板：{s.get('atr_floor')}</span><br>
                統計支撐：{s.get('support_dist')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="side-box">
            <b>🧪 邏輯回測參數：</b><br><br>
            🟢 觀察買點：<br><span style="font-size:1.5em; color:#388e3c; font-weight:bold;">{s.get('buy_point')}</span><br><br>
            🎯 壓力位：<br><span style="font-size:1.5em; color:#d32f2f; font-weight:bold;">{s.get('pressure_point')}</span>
            <hr>
            📉 支撐分佈：<br><span style="color:#b71c1c; font-weight:bold;">{s.get('support_dist')}</span><br><br>
            📈 壓力分佈：<br><span style="color:#b71c1c; font-weight:bold;">{s.get('pressure_point')}</span>
        </div>
        """, unsafe_allow_html=True)

time.sleep(60)
st.rerun()
