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

# --- 2. 密碼驗證與免責聲明 ---
# 免責聲明永遠置頂，不放在循環內，保證效能
st.markdown("""
<div style="background:#fff3e0; padding:15px; border-radius:10px; border:2px solid #ff9800; margin-bottom:25px;">
    <h3 style="color:#ef6c00; margin:0;">⚠️ 讀前必視：系統使用免責聲明</h3>
    <p style="color:#5d4037; font-size:0.9em; margin-top:5px;">
    1. 本網頁為個人 <b>Python 量化模型開發測試用途</b>，僅供開發者本人觀測邏輯執行結果。<br><br>
    2. 內文所載之所有價格、診斷報告皆為<b>程式演算法之實驗產出</b>，非屬任何形式之投資建議。<br><br>
    3. 投資有風險，過去績效不代表未來表現。<b>任何閱覽者若據此進行交易，盈虧請自負</b>，本站開發者不承擔任何法律責任。<br><br>
    4. 數據可能因 API 延遲或計算邏輯而有誤差，請以各交易所官方報價為準。
    </p>
</div>
""", unsafe_allow_html=True)

if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. HTML 模板定義 (確保標籤結構不變) ---
CARD_TEMPLATE = """
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: sans-serif; margin-bottom: 30px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
        <div>
            <h2 style="color:#b71c1c; margin:0; font-size:1.8em;">☢️ {NAME} ({TICKER})</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:5px 0;">${PRICE}</div>
            <div style="font-size:0.9em; color:#555;">趨勢：💀 空頭排列 | <b>PE: {PE}</b> | <b>成長: {GROWTH}</b></div>
        </div>
        <div style="background:#fbe9e7; padding:12px; border-radius:8px; width:160px; font-size:0.85em; color:#d32f2f; border:1px solid #ffccbc;">RSI: 53.4 | 籌碼: ☁️ 盤整 | 量比: 1.8x</div>
    </div>
    <hr style="border:0.5px solid #ffcdd2; margin:15px 0;">
    <div style="background:white; border:1px solid #eee; border-radius:10px; padding:15px; margin-bottom:15px;">
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:15px; text-align:center;">
            <div><span style="color:#2e7d32; font-size:0.8em; font-weight:bold;">🟢 觀察買點</span><br><b style="color:#2e7d32; font-size:1.4em;">74.16</b></div>
            <div><span style="color:#c62828; font-size:0.8em; font-weight:bold;">🎯 壓力位</span><br><b style="color:#c62828; font-size:1.4em;">{PRESSURE}</b></div>
            <div><span style="color:#c62828; font-size:0.8em; font-weight:bold;">📉 支撐分佈</span><br><b style="color:#c62828; font-size:1.4em;">{SUPPORT}</b></div>
            <div><span style="color:#c62828; font-size:0.85em; font-weight:bold;">📈 壓力分佈</span><br><b style="color:#c62828; font-size:1.4em;">{PRESSURE}</b></div>
        </div>
        <div style="margin-top:15px; padding-top:10px; border-top:1px solid #f0f0f0; display:flex; flex-wrap:wrap; gap:15px;">
            <div style="flex:1; min-width:200px;">
                <b style="color:#333; font-size:0.9em;">⚙️ 風控與成本模擬：</b><br>
                <span style="color:#1565c0; font-size:0.85em;">防守觀察點: {SUPPORT}</span> | <span style="color:#c62828; font-size:0.85em;">ATR地板: 68.41</span>
            </div>
            <div style="flex:1; min-width:150px;"><b style="color:#333; font-size:0.9em;">📊 市場分佈：</b><br><span style="color:#555; font-size:0.85em;">密集換手區: {TURNOVER}</span></div>
        </div>
    </div>
    <div style="background:rgba(255,255,255,0.8); padding:15px; border-radius:10px;">
        <b style="font-size:1.1em; color:#333;">🧠 智權診斷 (AI 版)：</b>
        <div style="margin-top:10px; font-size:1em; line-height:1.6; color:#444;">{REPORT}</div>
    </div>
</div>
"""

# --- 4. 數據填充與渲染 ---
raw_db, ai_db = load_data()
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    d = raw_db.get("stocks", {}).get(ticker, {})
    report_text = ai_db.get("reports", {}).get(ticker, "🤖 分析同步中...")
    
    # 手動清理 AI 文本，這是防止噴碼的最重要步驟
    report_clean = str(report_text).replace("\n", "<br>").replace("'", "&apos;").replace('"', "&quot;")

    # 填充模板
    card_html = CARD_TEMPLATE.format(
        NAME=name,
        TICKER=ticker,
        PRICE=str(d.get('price', '---')),
        PE=str(round(float(d.get('pe', 0)), 2)) if d.get('pe') not in ['---', None] else '---',
        GROWTH=str(d.get('growth', '---')),
        SUPPORT=str(d.get('support', '---')),
        PRESSURE=str(d.get('pressure', '---')),
        TURNOVER="77.22",
        REPORT=report_clean
    )

    st.markdown(card_html, unsafe_allow_html=True)

# 60秒自動刷新
time.sleep(60)
st.rerun()
