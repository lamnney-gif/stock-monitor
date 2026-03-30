import streamlit as st
import streamlit.components.v1 as components
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

# --- 3. 渲染戰術介面 ---
raw_db, ai_db = load_data()
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}

for ticker, name in tickers.items():
    d = raw_db.get("stocks", {}).get(ticker, {})
    report_text = ai_db.get("reports", {}).get(ticker, "🤖 分析同步中...").replace("\n", "<br>")

    # 數據整理
    price = str(d.get('price', '---'))
    pe = str(round(float(d.get('pe', 0)), 2)) if d.get('pe') not in ['---', None] else '---'
    gr = str(d.get('growth', '---'))
    sup = str(d.get('support', '---'))
    pre = str(d.get('pressure', '---'))

    # 使用 Python 的多行字串，這次不放在 st.markdown，改放在 components.html
    html_content = f"""
    <div style="background:#fff9f9; border-left:12px solid #e53935; padding:20px; border-radius:12px; border:1px solid #ffdde0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin-bottom: 20px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap: wrap;">
            <div>
                <h1 style="color:#b71c1c; margin:0; font-size:24px;">☢️ {name} ({ticker})</h1>
                <div style="font-size:42px; font-weight:900; color:#b71c1c; margin:5px 0;">${price}</div>
                <div style="font-size:14px; color:#555;">
                    趨勢：💀 空頭排列 | <b>PE: {pe}</b> | <b>成長: {gr}</b><br>
                    乖離率: 1.62% | 機構: 12.8%
                </div>
            </div>
            <div style="background:#fbe9e7; padding:10px; border-radius:8px; width:160px; font-size:12px; color:#d32f2f; border:1px solid #ffccbc;">
                RSI: 53.4 | 籌碼: ☁️ 盤整 | 量比: 1.8x
            </div>
        </div>

        <hr style="border:0.5px solid #ffcdd2; margin:15px 0;">

        <div style="background:white; border:1px solid #eee; border-radius:10px; padding:15px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center; flex-wrap: wrap; gap:10px;">
            <div style="flex:1; min-width:100px; text-align:center; border-right:1px solid #eee;">
                <span style="color:#2e7d32; font-size:12px; font-weight:bold;">🟢 觀察買點</span><br>
                <b style="color:#2e7d32; font-size:20px;">74.16</b>
            </div>
            <div style="flex:1; min-width:100px; text-align:center; border-right:1px solid #eee;">
                <span style="color:#c62828; font-size:12px; font-weight:bold;">🎯 壓力位</span><br>
                <b style="color:#c62828; font-size:20px;">{pre}</b>
            </div>
            <div style="flex:1.5; min-width:150px; padding-left:10px;">
                <b style="color:#333; font-size:14px;">⚙️ 風控與成本：</b><br>
                <span style="color:#1565c0; font-size:13px;">防守點: {sup}</span><br>
                <span style="color:#c62828; font-size:13px;">ATR地板: 68.41</span>
            </div>
        </div>

        <div style="background:rgba(255,255,255,0.8); padding:15px; border-radius:10px;">
            <b style="font-size:16px; color:#333;">🧠 智權診斷 (AI 版)：</b>
            <div style="margin-top:8px; font-size:15px; line-height:1.6; color:#444;">
                {report_html}
            </div>
        </div>
    </div>
    """
    # 關鍵：使用 components.html 確保 HTML 獨立渲染，不被 Streamlit 破壞
    components.html(html_content, height=450, scrolling=True)

# 60秒自動刷新
time.sleep(60)
st.rerun()
