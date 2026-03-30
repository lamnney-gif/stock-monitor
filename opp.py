import streamlit as st
import json
import os
import time
from string import Template

st.set_page_config(page_title="Beta Lab AI Ultimate", layout="wide")

# --- 1. 數據載入 (強化的 JSON 讀取) ---
def load_data():
    raw_p, ai_p = "data_raw.json", "analysis_results.json"
    try:
        if os.path.exists(raw_p):
            with open(raw_p, "r", encoding="utf-8") as f:
                r = json.load(f)
        else:
            r = {"stocks": {}}
            
        if os.path.exists(ai_p):
            with open(ai_p, "r", encoding="utf-8") as f:
                a = json.load(f)
        else:
            a = {"reports": {}}
    except:
        r, a = {"stocks": {}}, {"reports": {}}
    return r, a

# --- 2. 免責聲明 ---
st.markdown("""
<div style="background:#fff3e0; padding:15px; border-radius:10px; border:2px solid #ff9800; margin-bottom:25px;">
    <h3 style="color:#ef6c00; margin:0;">⚠️ 系統使用免責聲明</h3>
    <p style="color:#5d4037; font-size:0.9em; margin-top:5px;">本數據僅供參考，不代表投資建議。投資者應自行評估風險。</p>
</div>
""", unsafe_allow_html=True)

if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. HTML 模板 (Template 穩定版) ---
CARD_STYLE = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: sans-serif; margin-bottom: 30px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
        <div>
            <h2 style="color:#b71c1c; margin:0; font-size:1.8em;">☢️ $NAME ($TICKER)</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:5px 0;">$$$PRICE</div>
            <div style="font-size:0.9em; color:#555;">趨勢：💀 空頭排列 | <b>PE: $PE</b> | <b>成長: $GROWTH</b></div>
        </div>
        <div style="background:#fbe9e7; padding:12px; border-radius:8px; width:170px; font-size:0.85em; color:#d32f2f; border:1px solid #ffccbc;">
            RSI: $RSI | 籌碼: $CHIPS | 量比: $VOL_RATIO
        </div>
    </div>
    <hr style="border:0.5px solid #ffcdd2; margin:15px 0;">
    <div style="background:white; border:1px solid #eee; border-radius:10px; padding:15px; margin-bottom:15px;">
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap:15px; text-align:center;">
            <div><span style="color:#2e7d32; font-size:0.8em; font-weight:bold;">🟢 觀察買點</span><br><b style="color:#2e7d32; font-size:1.4em;">$BUY_POINT</b></div>
            <div><span style="color:#c62828; font-size:0.8em; font-weight:bold;">🎯 壓力位</span><br><b style="color:#c62828; font-size:1.4em;">$PRESSURE</b></div>
            <div><span style="color:#c62828; font-size:0.8em; font-weight:bold;">📉 支撐分布</span><br><b style="color:#c62828; font-size:1.4em;">$SUPPORT</b></div>
            <div><span style="color:#c62828; font-size:0.85em; font-weight:bold;">📈 壓力分布</span><br><b style="color:#c62828; font-size:1.4em;">$PRESSURE</b></div>
        </div>
        <div style="margin-top:15px; padding-top:10px; border-top:1px solid #f0f0f0; display:flex; flex-wrap:wrap; gap:15px;">
            <div style="flex:1; min-width:200px;">
                <b style="color:#333; font-size:0.9em;">⚙️ 風控與成本模擬：</b><br>
                <span style="color:#1565c0; font-size:0.85em;">防守點: $SUPPORT</span> | <span style="color:#c62828; font-size:0.85em;">ATR地板: $ATR</span>
            </div>
            <div style="flex:1; min-width:150px;"><b style="color:#333; font-size:0.9em;">📊 市場分佈：</b><br><span style="color:#555; font-size:0.85em;">密集換手區: $TURNOVER</span></div>
        </div>
    </div>
    <div style="background:rgba(255,255,255,0.8); padding:15px; border-radius:10px;">
        <b style="font-size:1.1em; color:#333;">🧠 智權診斷 (AI 版)：</b>
        <div style="margin-top:10px; font-size:1em; line-height:1.6; color:#444;">$REPORT</div>
    </div>
</div>
""")

# --- 4. 數據填充渲染 ---
raw_db, ai_db = load_data()
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    # 獲取個股數據，並統一轉成小寫鍵值方便查詢
    stock_raw = raw_db.get("stocks", {}).get(ticker, {})
    d = {str(k).lower(): v for k, v in stock_raw.items()} # 自動轉小寫保護
    
    report_text = ai_db.get("reports", {}).get(ticker, "🤖 分析同步中...")
    report_clean = str(report_text).replace("\n", "<br>").replace("'", "&apos;")

    # 數據對接：增加多重路徑確保一定抓得到
    card_html = CARD_STYLE.safe_substitute(
        NAME=name,
        TICKER=ticker,
        PRICE=str(d.get('price', '---')),
        PE=str(round(float(d.get('pe', 0)), 2)) if d.get('pe') else '---',
        GROWTH=str(d.get('growth', '---')),
        # 這裡就是關鍵：如果讀不到 RSI 就看大寫，再讀不到就給 50
        RSI=str(d.get('rsi', '50')), 
        CHIPS=str(d.get('chips', d.get('chips_status', '---'))),
        VOL_RATIO=str(d.get('volume_ratio', d.get('vol_ratio', '---'))),
        BUY_POINT=str(d.get('buy_point', '---')),
        SUPPORT=str(d.get('support', '---')),
        PRESSURE=str(d.get('pressure', '---')),
        ATR=str(d.get('atr', '---')),
        TURNOVER=str(d.get('turnover_zone', '---')),
        REPORT=report_clean
    )
    st.markdown(card_html, unsafe_allow_html=True)

# --- 5. 除錯開關 (如果有問題，展開這個看原始 JSON) ---
with st.expander("🛠️ 數據後台診斷器"):
    st.json(raw_db)

time.sleep(60)
st.rerun()
