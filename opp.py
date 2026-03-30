import streamlit as st
import json
import os
from datetime import datetime
from string import Template
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="測試戰情室v.1", layout="wide")

# --- 1. 數據載入 ---
def load_data():
    raw_p, ai_p = "data_raw.json", "analysis_results.json"
    r = json.load(open(raw_p, "r", encoding="utf-8")) if os.path.exists(raw_p) else {"stocks": {}, "last_update": "---"}
    a = json.load(open(ai_p, "r", encoding="utf-8")) if os.path.exists(ai_p) else {"reports": {}, "last_update": "---"}
    return r, a

raw_db, ai_db = load_data()

# --- 2. 頂部狀態列 ---
col_refresh, col_ai, col_market = st.columns(3)

def get_countdown(time_str, limit_mins):
    if time_str == "---" or not time_str: return None
    try:
        target_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        diff_total_sec = abs(int((datetime.now() - target_dt).total_seconds()))
        limit_sec = limit_mins * 60
        passed_sec = diff_total_sec % limit_sec
        return limit_sec - passed_sec
    except:
        return None

with col_ai:
    ai_rem = get_countdown(ai_db.get("last_update", ""), 240)  # 4 小時
    if ai_rem:
        st.info(f"🤖 AI 下次改版：{ai_rem // 3600}時 {(ai_rem % 3600) // 60}分後")
    else:
        st.info("🤖 AI 診斷同步中")

with col_market:
    raw_rem = get_countdown(raw_db.get("last_update", ""), 15)  # 15 分鐘
    if raw_rem:
        st.success(f"📈 行情更新倒數：{raw_rem // 60} 分 {raw_rem % 60} 秒")
    else:
        st.success("📈 行情更新中")

with col_refresh:
    refresh_timer = st.empty()

# --- 3. 授權檢查 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 4. HTML 卡片模板 ---
CARD_STYLE = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: sans-serif; margin-bottom: 30px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:10px;">
        <div>
            <h2 style="color:#b71c1c; margin:0; font-size:1.8em;">☢️ $NAME ($TICKER)</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:5px 0;">$$$PRICE</div>
            <div style="font-size:0.9em; color:#555;">趨勢：💀 空頭排列 | <b>本益比: $PE</b> | <b>營收增長率: $GROWTH</b></div>
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
            <div><span style="color:#c62828; font-size:0.8em; font-weight:bold;">📉 支撐分佈</span><br><b style="color:#c62828; font-size:1.4em;">$SUPPORT</b></div>
            <div><span style="color:#c62828; font-size:0.85em; font-weight:bold;">📈 壓力分佈</span><br><b style="color:#c62828; font-size:1.4em;">$PRESSURE</b></div>
        </div>
        <div style="margin-top:15px; padding-top:10px; border-top:1px solid #f0f0f0; display:flex; flex-wrap:wrap; gap:15px;">
            <div style="flex:1; min-width:200px;">
                <b style="color:#333; font-size:0.9em;">⚙️ 風控與成本模擬：</b><br>
                <span style="color:#1565c0; font-size:0.85em;">防守觀察點: $SUPPORT</span> | <span style="color:#c62828; font-size:0.85em;">ATR地板: $ATR</span>
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

# --- 5. 數據渲染 ---
ticker_list = ["2330.TW", "NVDA", "MU", "000660.KS", "2303.TW", "6770.TW", "2344.TW", "3481.TW", "1303.TW"]
names = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for tk in ticker_list:
    d = raw_db.get("stocks", {}).get(tk, {})
    report_content = ai_db.get("reports", {}).get(tk, "🤖 分析同步中...")
    report_clean = str(report_content).replace("\n", "<br>").replace("'", "&apos;")

    html_output = CARD_STYLE.safe_substitute(
        NAME=names.get(tk, tk), TICKER=tk,
        PRICE=str(d.get('price', '---')), PE=str(d.get('pe', '---')),
        GROWTH=str(d.get('growth', '---')), RSI=str(d.get('rsi', '---')),
        CHIPS=str(d.get('chips', '---')), VOL_RATIO=str(d.get('volume_ratio', '---')),
        BUY_POINT=str(d.get('buy_point', '---')), SUPPORT=str(d.get('stop_profit_line', '---')),
        PRESSURE=str(d.get('pressure', '---')), ATR=str(d.get('dynamic_stop', '---')),
        TURNOVER=str(d.get('turnover_zone', '---')), REPORT=report_clean
    )
    st.markdown(html_output, unsafe_allow_html=True)

# --- 6. 自動刷新 ---
# 每 60 秒刷新一次頁面
count = st_autorefresh(interval=60*1000, limit=None, key="auto_refresh")
seconds_left = 60 - (count % 60)
refresh_timer.metric("🔄 頁面即時行情刷新倒數", f"{seconds_left} 秒")
