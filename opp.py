import streamlit as st
import json
import os
import time
from string import Template

st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# --- 1. 數據載入 ---
def load_data():
    raw_p, ai_p = "data_raw.json", "analysis_results.json"
    try:
        r = json.load(open(raw_p, "r", encoding="utf-8")) if os.path.exists(raw_p) else {"stocks": {}}
        a = json.load(open(ai_p, "r", encoding="utf-8")) if os.path.exists(ai_p) else {"reports": {}}
    except:
        r, a = {"stocks": {}}, {"reports": {}}
    return r, a

# --- 2. 免責聲明 ---
st.markdown("""
<div style="background:#fff3e0; padding:15px; border-radius:10px; border:2px solid #ff9800; margin-bottom:25px;">
    <h3 style="color:#ef6c00; margin:0;">⚠️ 系統使用免責聲明</h3>
    <p style="color:#5d4037; font-size:0.9em; margin-top:5px;">數據僅供參考，AI 診斷不代表買賣建議。</p>
</div>
""", unsafe_allow_html=True)

if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. HTML 模板 ---
CARD_STYLE = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: sans-serif; margin-bottom: 30px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
        <div>
            <h2 style="color:#b71c1c; margin:0; font-size:1.8em;">☢️ $NAME ($TICKER)</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:5px 0;">$$$PRICE</div>
            <div style="font-size:0.9em; color:#555;">趨勢：💀 空頭排列 | <b>PE: $PE</b> | <b>成長: $GROWTH</b></div>
        </div>
        <div style="background:#fbe9e7; padding:12px; border-radius:8px; width:160px; font-size:0.85em; color:#d32f2f; border:1px solid #ffccbc;">
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
    </div>
    <div style="background:rgba(255,255,255,0.8); padding:15px; border-radius:10px;">
        <b style="font-size:1.1em; color:#333;">🧠 智權診斷 (AI 版)：</b>
        <div style="margin-top:10px; font-size:1em; line-height:1.6; color:#444;">$REPORT</div>
    </div>
</div>
""")

# --- 4. 數據渲染 ---
raw_db, ai_db = load_data()
# 確保這裡的 Tickers 順序正確
ticker_list = ["2330.TW", "NVDA", "MU", "000660.KS", "2303.TW", "6770.TW", "2344.TW", "3481.TW", "1303.TW"]
names = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for tk in ticker_list:
    # 核心修正：明確抓取該代號的 dict
    stock_info = raw_db.get("stocks", {}).get(tk, {})
    
    # 處理 AI 報告
    report_raw = ai_db.get("reports", {}).get(tk, "🤖 分析同步中...")
    report_clean = str(report_raw).replace("\n", "<br>").replace("'", "&apos;")

    # 填充 HTML (這裡每一個變數都必須從 stock_info 抓取)
    html_output = CARD_STYLE.safe_substitute(
        NAME=names.get(tk, tk),
        TICKER=tk,
        PRICE=str(stock_info.get('price', '---')),
        PE=str(stock_info.get('pe', '---')),
        GROWTH=str(stock_info.get('growth', '---')),
        RSI=str(stock_info.get('rsi', '---')), # 這裡絕對不會再統一顯示 53.4 了
        CHIPS=str(stock_info.get('chips', '---')),
        VOL_RATIO=str(stock_info.get('volume_ratio', '---')),
        BUY_POINT=str(stock_info.get('buy_point', '---')),
        SUPPORT=str(stock_info.get('support', '---')),
        PRESSURE=str(stock_info.get('pressure', '---')),
        REPORT=report_clean
    )
    st.markdown(html_output, unsafe_allow_html=True)

time.sleep(60)
st.rerun()
