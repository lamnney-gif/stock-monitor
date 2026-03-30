import yfinance as yf
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

# ✅ Wilder ATR（正確版本）
def calculate_atr(df, period=14):
    hl = df['High'] - df['Low']
    hc = np.abs(df['High'] - df['Close'].shift())
    lc = np.abs(df['Low'] - df['Close'].shift())
    
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    
    # Wilder smoothing
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def run_market():
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    raw_results = {"last_update": get_tw_time(), "stocks": {}}
    
    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="3mo")
            if df.empty: continue
            
            price = round(df['Close'].iloc[-1], 2)
            
            # ✅ 正確 ATR
            df['ATR'] = calculate_atr(df)
            atr_val = df['ATR'].iloc[-1]
            
            # ✅ ATR 壓縮偵測（關鍵）
            atr_mean = df['ATR'].rolling(20).mean().iloc[-1]
            
            # 如果 ATR 過低 → 視為盤整壓縮（避免被洗）
            if atr_val < atr_mean * 0.8:
                atr_effective = atr_val * 1.3   # 放大避免洗盤
                atr_state = "⚠️ 壓縮"
            else:
                atr_effective = atr_val
                atr_state = "正常"
            
            atr_effective = round(atr_effective, 2)
            
            # ✅ 支撐壓力（改良版）
            support = round(price - (atr_effective * 2.2), 2)
            pressure = round(price + (atr_effective * 1.8), 2)
            buy_point = round(price - (atr_effective * 1.5), 2)
            
            # RSI
            rsi_val = 50.0
            if len(df) >= 14:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14).mean()
                loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
                rs = gain / loss
                rsi_val = round(100 - (100 / (1 + rs.iloc[-1])), 2)

            info = tk.info if tk.info else {}
            
            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "---",
                "growth": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "---",
                "rsi": rsi_val,
                "atr": atr_effective,
                "atr_state": atr_state,  # ⭐ 新增
                "support": support,
                "pressure": pressure,
                "buy_point": buy_point,
                "volume_ratio": round(df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean(), 2),
                "chips": "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整"),
                "turnover_zone": round(price * 0.99, 2),
            }
            
            print(f"✅ {name} | ATR: {atr_effective} ({atr_state})")
            
        except Exception as e:
            print(f"❌ {sym} 錯誤: {str(e)}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
