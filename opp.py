import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai
import time

# 1. 頁面配置
st.set_page_config(page_title="Beta Lab V10.5 - 數據全回歸", layout="wide")

# 2. 安全驗證
if "password_correct" not in st.session_state:
    st.markdown("### 🖥️ 內部開發監測系統 V10.5")
    if st.text_input("存取密碼", type="password") == "8888":
        st.session_state["password_correct"] = True
        st.rerun()
    st.stop()

# --- [核心修正] 針對 Free Tier Key 的啟動邏輯 ---
@st.cache_resource
def init_gemini():
    try:
        # 直接從 Secrets 抓取你設定好的 Key
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        # 使用最穩定的模型路徑避免 404
        return genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        return f"AI 啟動失敗: {e}"

ai_model = init_gemini()

# 3. CSS 戰鬥樣式 (確保視覺不跑偏)
st.markdown("""
    <style>
    .status-card { padding: 22px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #ddd; background: white; box-shadow: 2px 4px 12px rgba(0,0,0,0.08); }
    .ai-diag-box { background: #f0f5ff; border-left: 6px solid #1890ff; padding: 18px; border-radius: 10px; margin: 15px 0; color: #002766; font-size: 1.05em; }
    .metric-tag { display: inline-block; padding: 4px 12px; background: #f5f5f5; border-radius: 6px; margin-right: 8px; font-weight: bold; }
    .defense-box { background: #fcfcfc; border: 1.5px dashed #595959; padding: 15px; border-radius: 10px; margin-top: 15px; }
    .price-value { font-family: monospace; font-weight: bold; color: #d4380d; font-size: 1.1em; }
    </style>
    """, unsafe_allow_html=True)

# 4. 數據演算函數
def get_volume_support(df):
    try:
        # 計算密集換手區成本
        v_hist = np.histogram(df['Close'].tail(60), bins=10, weights=df['Volume'].tail(60))
        return (v_hist[1][np.argmax(v_hist[0])] + v_hist[1][np.argmax(v_hist[0])+1]) / 2
    except: return 0

# 5. 監控清單
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", "MU": "美光", "2303.TW": "聯電"}

st.title("🖥️ 全球量化戰鬥系統 V10.5")
timer = st.empty()

for ticker, name in tickers.items():
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        if df.empty: continue
        
        # --- 數據權限全數計算回歸 ---
        close = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        std20 = df['Close'].rolling(20).std().iloc[-1]
        rsi = (df['Close'].diff().where(df['Close'].diff()>0,0).rolling(14).mean() / df['Close'].diff().abs().rolling(14).mean()*100).iloc[-1]
        
        swing_high_warn = df['High'].tail(5).max() * 0.97 # 波段高點預警
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        defense_line = close - (2.5 * atr)               # ATR 演算底線
        vol_support = get_volume_support(df)             # 密集換手區
        obs_point = ma20 - 1.2 * std20                   # 觀察點
        pressure_line = ma20 + 2 * std20                 # 壓力位
        
        # AI 診斷執行
        if isinstance(ai_model, str):
            ai_diag = ai_model
        else:
            try:
                res = ai_model.generate_content(f"分析{name}:價{close},RSI{rsi:.1f}。給100字診斷。")
                ai_diag = res.text
            except Exception as e:
                ai_diag = f"⚠️ AI 診斷連線異常: {e}"

        # 6. UI 渲染 (確保數據權限完整呈現)
        st.markdown(f"""
        <div class="status-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.6em; font-weight:bold;">{name} ({ticker}) — ${close:.2f}</span>
                <div>
                    <span class="metric-tag">RSI: {rsi:.1f}</span>
                    <span class="metric-tag">PE: {stock.info.get('forwardPE', 'N/A')}</span>
                </div>
            </div>
            <div class="ai-diag-box"><b>🤖 Gemini AI 市場報告：</b><br>{ai_diag}</div>
            <div style="display: flex; gap: 20px;">
                <div style="flex: 2;">
                    <div class="defense-box">
                        🛡️ <b>關鍵防禦指標 (數據權限已回歸)：</b><br>
                        波段高點預警: <span class="price-value">{swing_high_warn:.2f}</span> | 
                        ATR 底線(停損): <span class="price-value">{defense_line:.2f}</span> <br>
                        密集換手區(成本支撐): <span class="price-value">{vol_support:.2f}</span>
                    </div>
                </div>
                <div style="flex: 1; background: #fffbe6; padding: 15px; border-radius: 10px; border: 1px solid #ffe58f;">
                    <b>🧪 量化預測點位：</b><br>
                    🟢 觀察點: <span style="color:green; font-weight:bold;">{obs_point:.2f}</span><br>
                    🎯 壓力位: <span style="color:red; font-weight:bold;">{pressure_line:.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except: pass

for i in range(60, 0, -1):
    timer.write(f"🔄 系統將於 {i} 秒後刷新數據與 AI 分析...")
    time.sleep(1)
st.rerun()
