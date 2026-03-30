import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta
from string import Template

st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

def load_data():
    r = json.load(open("data_raw.json", "r", encoding="utf-8")) if os.path.exists("data_raw.json") else {"stocks": {}}
    a = json.load(open("analysis_results.json", "r", encoding="utf-8")) if os.path.exists("analysis_results.json") else {"reports": {}, "last_update": "---"}
    return r, a

raw_db, ai_db = load_data()
# 取得目前台北時間
now_tw = datetime.utcnow() + timedelta(hours=8)

# --- 頂部狀態列 ---
c1, c2 = st.columns(2)
with c1:
    refresh_p = st.empty()

with c2:
    last_up = ai_db.get("last_update", "---")
    if last_up != "---":
        # 解析 JSON 裡面的台北時間
        last_dt = datetime.strptime(last_up, "%Y-%m-%d %H:%M:%S")
        next_dt = last_dt + timedelta(hours=4)
        diff = next_dt - now_tw
        sec_left = int(diff.total_seconds())
        
        if sec_left <= 0:
            st.warning("⏳ AI 診斷：新一輪報告正在發布...")
        else:
            st.info(f"⏳ AI 下次大改版倒數：{sec_left//3600}時 {(sec_left%3600)//60}分")
    else:
        st.error("🤖 等待 AI 初次同步數據...")

# 授權
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- HTML 模板 (補回風控與換手區) ---
CARD = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; margin-bottom: 25px;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <h2 style="color:#b71c1c; margin:0;">☢️ $NAME ($TICKER)</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:5px 0;">$$$PRICE</div>
            <div style="font-size:0.9em; color:#555;">PE: $PE | 成長: $GROWTH</div>
        </div>
        <div style="background:#fbe9e7; padding:10px; border-radius:8px; color:#d32f2f;">
            RSI: $RSI | 籌碼: $CHIPS | 量比: $VOL_RATIO
        </div>
    </div>
    <div style="background:white; border-radius:10px; padding:15px; margin:15px 0; border:1px solid #eee;">
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); text-align:center;">
            <div><small>🟢 買點</small><br><b>$BUY_POINT</b></div>
            <div><small>🎯 壓力</small><br><b>$PRESSURE</b></div>
            <div><small>📉 支撐</small><br><b>$SUPPORT</b></div>
            <div><small>📈 密集</small><br><b>$TURNOVER</b></div>
        </div>
        <div style="margin-top:10px; font-size:0.8em; color:#666; border-top:1px solid #f0f0f0; padding-top:10px;">
            ⚙️ 風控防守: $SUPPORT | ATR: $ATR | 📊 密集換手: $TURNOVER
        </div>
    </div>
    <div style="background:rgba(255,255,255,0.7); padding:10px; border-radius:8px;">
        <b style="color:#333;">🧠 AI 診斷：</b><br><span style="font-size:0.95em; color:#444;">$REPORT</span>
    </div>
</div>
""")

# --- 渲染 ---
for tk, d in raw_db.get("stocks", {}).items():
    rep = ai_db.get("reports", {}).get(tk, "同步中...").replace("\n", "<br>")
    st.markdown(CARD.safe_substitute(
        NAME=d.get('name', tk), TICKER=tk, PRICE=d.get('price'),
        PE=d.get('pe'), GROWTH=d.get('growth'), RSI=d.get('rsi'),
        CHIPS=d.get('chips'), VOL_RATIO=d.get('volume_ratio'),
        BUY_POINT=d.get('buy_point'), PRESSURE=d.get('pressure'),
        SUPPORT=d.get('support'), ATR=d.get('atr'),
        TURNOVER=d.get('turnover_zone'), REPORT=rep
    ), unsafe_allow_html=True)

# --- 倒數刷新 ---
for i in range(60, 0, -1):
    refresh_p.metric("🔄 行情即時刷新", f"{i}s")
    time.sleep(1)
st.rerun()
