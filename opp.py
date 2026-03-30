# app.py
import streamlit as st
import json, os
from datetime import datetime, timedelta
from string import Template

st.set_page_config(page_title="測試戰情室v.1", layout="wide")

# --- 1. 載入資料 ---
def load_data():
    raw_p, ai_p = "data_raw.json", "analysis_results.json"
    r = json.load(open(raw_p, "r", encoding="utf-8")) if os.path.exists(raw_p) else {"stocks": {}, "last_update": "---"}
    a = json.load(open(ai_p, "r", encoding="utf-8")) if os.path.exists(ai_p) else {"reports": {}, "last_update": "---"}
    return r, a

raw_db, ai_db = load_data()

# --- 2. 頂部狀態列 ---
col_refresh, col_ai, col_market = st.columns(3)

def next_cron_run(interval_min=5):
    """計算下一次 cron 執行秒數"""
    now = datetime.utcnow()
    next_min = (now.minute // interval_min + 1) * interval_min
    next_hour = now.hour
    if next_min >= 60:
        next_min -= 60
        next_hour += 1
    next_run = now.replace(hour=next_hour % 24, minute=next_min, second=0, microsecond=0)
    return (next_run - now).total_seconds()

seconds_left = int(next_cron_run(5))
minutes, seconds = divmod(seconds_left, 60)
col_market.metric("📈 行情更新倒數", f"{minutes} 分 {seconds} 秒")

# AI 倒數 4 小時
ai_rem_sec = int(next_cron_run(240))
ai_minutes, ai_seconds = divmod(ai_rem_sec, 60)
col_ai.info(f"🤖 AI 下次改版：{ai_minutes//60}時 {ai_minutes%60}分後")

# --- 3. 授權 ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 4. HTML 卡片模板 ---
CARD_STYLE = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: sans-serif; margin-bottom: 30px;">
    <h2 style="color:#b71c1c;">☢️ $NAME ($TICKER)</h2>
    <div style="font-size:2em;">$$$PRICE</div>
    <div>趨勢：💀 空頭排列 | <b>本益比: $PE</b> | <b>營收增長率: $GROWTH</b></div>
    <div>RSI: $RSI | 籌碼: $CHIPS | 量比: $VOL_RATIO</div>
    <div>觀察買點: $BUY_POINT | 壓力: $PRESSURE | 支撐: $SUPPORT | ATR地板: $ATR</div>
    <div>密集換手區: $TURNOVER</div>
    <div>防守觀察點: $STOP_PROFIT_LINE</div>
    <div>AI報告: $REPORT</div>
</div>
""")

# --- 5. 數據渲染 ---
ticker_list = ["2330.TW","NVDA","MU","000660.KS","2303.TW","6770.TW","2344.TW","3481.TW","1303.TW"]
names = {"2330.TW":"台積電","NVDA":"輝達","MU":"美光","000660.KS":"海力士","2303.TW":"聯電",
         "6770.TW":"力積電","2344.TW":"華邦電","3481.TW":"群創","1303.TW":"南亞"}

for tk in ticker_list:
    d = raw_db.get("stocks", {}).get(tk, {})
    report = ai_db.get("reports", {}).get(tk, "🤖 分析同步中...")
    html_output = CARD_STYLE.safe_substitute(
        NAME=names.get(tk, tk),
        TICKER=tk,
        PRICE=d.get('price','---'),
        PE=d.get('pe','---'),
        GROWTH=d.get('growth','---'),
        RSI=d.get('rsi','---'),
        CHIPS=d.get('chips','---'),
        VOL_RATIO=d.get('volume_ratio','---'),
        BUY_POINT=d.get('buy_point','---'),
        SUPPORT=d.get('stop_profit_line','---'),
        PRESSURE=d.get('pressure','---'),
        ATR=d.get('dynamic_stop','---'),
        TURNOVER=d.get('turnover_zone','---'),
        STOP_PROFIT_LINE=d.get('stop_profit_line','---'),
        REPORT=str(report).replace("\n","<br>")
    )
    st.markdown(html_output, unsafe_allow_html=True)

# --- 6. 自動刷新 (60秒) ---
import time
for i in range(60,0,-1):
    col_refresh.metric("🔄 頁面即時刷新倒數", f"{i} 秒")
    time.sleep(1)
st.experimental_rerun()
