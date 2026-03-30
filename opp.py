import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta
from string import Template

st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# --- 數據載入 ---
def load_all():
    r = json.load(open("data_raw.json", "r", encoding="utf-8")) if os.path.exists("data_raw.json") else {"stocks": {}}
    a = json.load(open("analysis_results.json", "r", encoding="utf-8")) if os.path.exists("analysis_results.json") else {"reports": {}, "last_update": "---"}
    return r, a

raw_db, ai_db = load_all()
now_tw = datetime.utcnow() + timedelta(hours=8)

# --- 頂部狀態列 ---
c1, c2 = st.columns(2)
with c1:
    timer_placeholder = st.empty()
with c2:
    last_up = ai_db.get("last_update", "---")
    if last_up != "---":
        next_up = datetime.strptime(last_up, "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)
        msg = f"📅 下次 AI 更新 (台灣時間)：{next_up.strftime('%H:%M')}" if now_tw < next_up else "⏳ AI 正在同步新報告..."
    else: msg = "🤖 等待 AI 數據..."
    st.info(msg)

# 授權檢查
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- HTML 模板 ---
CARD = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; margin-bottom: 30px;">
    <div style="display:flex; justify-content:space-between;">
        <div>
            <h2 style="color:#b71c1c; margin:0;">☢️ $NAME ($TICKER)</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c;">$$$PRICE</div>
            <div style="font-size:0.9em; color:#555;">PE: $PE | 成長: $GROWTH</div>
        </div>
        <div style="background:#fbe9e7; padding:10px; border-radius:8px; height:fit-content; color:#d32f2f;">
            RSI: $RSI | 籌碼: $CHIPS | 量比: $VOL_RATIO
        </div>
    </div>
    <div style="background:white; border-radius:10px; padding:15px; margin:15px 0; border:1px solid #eee;">
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); text-align:center;">
            <div><small>🟢 觀察買點</small><br><b>$BUY_POINT</b></div>
            <div><small>🎯 壓力位</small><br><b>$PRESSURE</b></div>
            <div><small>📉 支撐分佈</small><br><b>$SUPPORT</b></div>
            <div><small>📈 壓力分佈</small><br><b>$PRESSURE</b></div>
        </div>
        <div style="margin-top:15px; font-size:0.85em; border-top:1px solid #f0f0f0; padding-top:10px;">
            <b>⚙️ 風控：</b> 防守 $SUPPORT | ATR: $ATR | <b>📊 市場：</b> 密集換手 $TURNOVER
        </div>
    </div>
    <div style="background:rgba(255,255,255,0.6); padding:10px; border-radius:8px;">
        <b>🧠 AI 診斷：</b><br><small>$REPORT</small>
    </div>
</div>
""")

# --- 渲染卡片 ---
for tk, d in raw_db.get("stocks", {}).items():
    st.markdown(CARD.safe_substitute(
        NAME=d.get('name', tk), TICKER=tk, PRICE=d.get('price'),
        PE=d.get('pe'), GROWTH=d.get('growth'), RSI=d.get('rsi'),
        CHIPS=d.get('chips'), VOL_RATIO=d.get('volume_ratio'),
        BUY_POINT=d.get('buy_point'), PRESSURE=d.get('pressure'),
        SUPPORT=d.get('support'), ATR=d.get('atr'),
        TURNOVER=d.get('turnover_zone'), 
        REPORT=ai_db.get("reports", {}).get(tk, "分析中...").replace("\n", "<br>")
    ), unsafe_allow_html=True)

# --- 倒數刷新 ---
for i in range(60, 0, -1):
    timer_placeholder.metric("🔄 行情即時刷新", f"{i}s")
    time.sleep(1)
st.rerun()
