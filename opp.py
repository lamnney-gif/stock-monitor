import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import time

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab V11.2 - 終極回歸", layout="wide")

# 2. 安全驗證 (密碼 8888)
if "password_correct" not in st.session_state:
    if st.text_input("存取密碼", type="password") == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# 3. AI 核心初始化
@st.cache_resource
def init_gemini():
    try:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        # 強制指定 models/ 路徑避開 404
        return genai.GenerativeModel('models/gemini-1.5-flash')
    except: return None

ai_model = init_gemini()

# 4. 密集換手區算法 (回歸)
def get_vol_zone(df):
    try:
        v_hist = np.histogram(df['Close'].tail(60), bins=10, weights=df['Volume'].tail(60))
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

# 5. 主面板
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光"}
st.title("🖥️ 全球量化戰鬥系統 V11.2")

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # 指標計算 (數據權限全開)
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        
        swing_h = df['High'].tail(5).max() * 0.97        # 波段高點預警
        atr_val = (df['High']-df['Low']).rolling(14).mean().iloc[-1]
        defense = close - (2.5 * atr_val)                # ATR 底線
        vol_support = get_vol_zone(df)                   # 密集換手區
        obs = ma20 - 1.2 * std20                         # 觀察點
        pres = ma20 + 2 * std20                          # 壓力位

        # UI 渲染
        st.markdown(f"""
        <div style="padding:20px; border:1px solid #ddd; border-radius:15px; margin-bottom:20px; background:white;">
            <h3>{name} ({ticker}) — ${close:.2f}</h3>
            <div style="background:#f0f5ff; padding:15px; border-radius:10px; margin:10px 0;">
                <b>🤖 AI 診斷：</b>{ai_model.generate_content(f"簡析{name}現價{close}").text if ai_model else "⚠️ 請先在 Secrets 更新 Key 並重啟"}
            </div>
            <div style="display:flex; gap:15px;">
                <div style="flex:2; border:1px dashed #666; padding:15px; border-radius:10px;">
                    🛡️ <b>關鍵防禦指標：</b><br>
                    波段高點預警: {swing_h:.2f} | ATR 底線: {defense:.2f} | 密集換手區: {vol_support:.2f}
                </div>
                <div style="flex:1; background:#fffbe6; padding:15px; border-radius:10px;">
                    🧪 <b>量化預測點位：</b><br>
                    🟢 觀察點: {obs:.2f} | 🎯 壓力位: {pres:.2f}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

time.sleep(60)
st.rerun()
