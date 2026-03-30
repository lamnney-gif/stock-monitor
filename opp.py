import streamlit as st
import json
import os
import time
from datetime import datetime, timedelta
from string import Template

st.set_page_config(page_title="半導體大戶戰情室", layout="wide")

# --- 1. 數據載入 ---
def load_all():
    r = json.load(open("data_raw.json", "r", encoding="utf-8")) if os.path.exists("data_raw.json") else {"stocks": {}}
    a = json.load(open("analysis_results.json", "r", encoding="utf-8")) if os.path.exists("analysis_results.json") else {"reports": {}, "last_update": "---"}
    return r, a

raw_db, ai_db = load_all()
# 取得目前台灣時間 (基準點)
now_tw = datetime.utcnow() + timedelta(hours=8)

# --- 2. 頂部狀態列 (改回倒數模式) ---
col_time1, col_time2 = st.columns(2)

with col_time1:
    # 網頁即時刷新倒數
    refresh_placeholder = st.empty()

with col_time2:
    # AI 分析倒數邏輯
    last_up_str = ai_db.get("last_update", "---")
    if last_up_str != "---":
        try:
            # 讀取上次更新時間
            last_dt = datetime.strptime(last_up_str, "%Y-%m-%d %H:%M:%S")
            # 設定 4 小時後為下次更新
            next_dt = last_dt + timedelta(hours=4)
            
            # 計算差距
            diff = next_dt - now_tw
            seconds_left = int(diff.total_seconds())
            
            if seconds_left <= 0:
                ai_msg = "⏳ AI 診斷：新一輪分析發布中..."
            else:
                hours = seconds_left // 3600
                mins = (seconds_left % 3600) // 60
                ai_msg = f"⏳ AI 下次大改版倒數：{hours}時 {mins}分"
        except:
            ai_msg = "⚠️ 時間格式解析錯誤"
    else:
        ai_msg = "🤖 等待 AI 初次同步..."
    
    st.info(ai_msg)

# --- 3. 免責聲明 ---
st.markdown("""
<div style="background:#fff3e0; padding:15px; border-radius:10px; border:2px solid #ff9800; margin-bottom:20px;">
    <h3 style="color:#ef6c00; margin:0; font-size:1.1em;">⚠️ 系統使用免責聲明</h3>
    <p style="color:#5d4037; font-size:0.85em; margin:5px 0 0 0;">本平台數據僅供研究參考，台北時間 24H 監控中，投資請自負損益。</p>
</div>
""", unsafe_allow_html=True)

# 授權檢查 (密碼 8888)
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    if st.text_input("授權碼", type="password") == "8888":
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 4. HTML 模板 (卡片樣式) ---
CARD = Template("""
<div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; margin-bottom: 30px; font-family: sans-serif;">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <div>
            <h2 style="color:#b71c1c; margin:0;">☢️ $NAME ($TICKER)</h2>
            <div style="font-size:3.5em; font-weight:900; color:#b71c1c; margin:5px 0;">$$$PRICE</div>
            <div style="font-size:0.9em; color:#555;">PE: $PE | 成長: $GROWTH</div>
        </div>
        <div style="background:#fbe9e7; padding:10px; border-radius:8px; color:#d32f2f; border:1px solid #ffccbc;">
            RSI: $RSI | 籌碼: $CHIPS | 量比: $VOL_RATIO
        </div>
    </div>
    <div style="background:white; border-radius:10px; padding:15px; margin:15px 0; border:1px solid #eee;">
        <div style="display:grid; grid-template-columns: repeat(4, 1fr); text-align:center; gap:10px;">
            <div><span style="color:#2e7d32; font-size:0.8em;">🟢 觀察買點</span><br><b style="font-size:1.2em;">$BUY_POINT</b></div>
            <div><span style="color:#c62828; font-size:0.8em;">🎯 壓力位</span><br><b style="font-size:1.2em;">$PRESSURE</b></div>
            <div><span style="color:#c62828; font-size:0.8em;">📉 支撐分佈</span><br><b style="font-size:1.2em;">$SUPPORT</b></div>
            <div><span style="color:#c62828; font-size:0.8em;">📈 壓力分佈</span><br><b style="font-size:1.2em;">$PRESSURE</b></div>
        </div>
        <div style="margin-top:15px; font-size:0.85em; border-top:1px solid #f0f0f0; padding-top:10px;">
            <b style="color:#333;">⚙️ 風控模擬：</b> 防守 $SUPPORT | ATR: $ATR | <b style="color:#333;">📊 市場分佈：</b> 密集換手 $TURNOVER
        </div>
    </div>
    <div style="background:rgba(255,255,255,0.7); padding:12px; border-radius:8px;">
        <b style="color:#333;">🧠 智權診斷 (AI)：</b><br>
        <div style="color:#444; line-height:1.5;">$REPORT</div>
    </div>
</div>
""")

# --- 5. 渲染卡片 ---
for tk, d in raw_db.get("stocks", {}).items():
    report_raw = ai_db.get("reports", {}).get(tk, "分析同步中...")
    report_html = str(report_raw).replace("\n", "<br>")

    st.markdown(CARD.safe_substitute(
        NAME=d.get('name', tk), TICKER=tk, PRICE=d.get('price', '---'),
        PE=d.get('pe', '---'), GROWTH=d.get('growth', '---'), RSI=d.get('rsi', '---'),
        CHIPS=d.get('chips', '---'), VOL_RATIO=d.get('volume_ratio', '---'),
        BUY_POINT=d.get('buy_point', '---'), PRESSURE=d.get('pressure', '---'),
        SUPPORT=d.get('support', '---'), ATR=d.get('atr', '---'),
        TURNOVER=d.get('turnover_zone', '---'), REPORT=report_html
    ), unsafe_allow_html=True)

# --- 6. 循環倒數刷新 ---
for i in range(60, 0, -1):
    refresh_placeholder.metric("🔄 行情即時刷新", f"{i}s")
    time.sleep(1)

st.rerun()
