import yfinance as yf
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def calculate_rsi(series, period=14):
    """改為 EMA RSI（更接近實戰）"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1], 2) if not pd.isna(rs.iloc[-1]) else 50.0

def calculate_atr(df, period=14):
    """正確 ATR（Wilder）"""
    hl = df['High'] - df['Low']
    hc = np.abs(df['High'] - df['Close'].shift())
    lc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
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
            df = tk.history(period="1mo")
            if df.empty or len(df) < 20:
                continue
            
            price = round(df['Close'].iloc[-1], 2)

            # ✅ RSI
            rsi_val = calculate_rsi(df['Close'], 14)
            
            # ✅ 真 ATR
            df['ATR'] = calculate_atr(df)
            atr_val = df['ATR'].iloc[-1]
            
            # ✅ ATR 壓縮判斷（避免被洗）
            atr_mean = df['ATR'].rolling(20).mean().iloc[-1]
            if atr_val < atr_mean * 0.8:
                atr_effective = atr_val * 1.3
                atr_state = "⚠️ 壓縮"
            else:
                atr_effective = atr_val
                atr_state = "正常"
            
            atr_effective = round(atr_effective, 2)

            # ✅ 保留 std，但改名（不要再當 ATR）
            volatility = df['Close'].rolling(20).std().iloc[-1]

            # ✅ 籌碼
            chips_status = "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整")
            
            # ✅ 量比
            vol_avg = df['Volume'].iloc[-6:-1].mean()
            vol_ratio = round(df['Volume'].iloc[-1] / vol_avg, 2) if vol_avg > 0 else 1.0

            # ✅ 改良支撐壓力（用 ATR，不用 std）
            support = round(price - (atr_effective * 2.0), 2)
            pressure = round(price + (atr_effective * 1.6), 2)
            buy_point = round(price - (atr_effective * 1.3), 2)

            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": tk.info.get('trailingPE', '---'),
                "growth": f"{tk.info.get('revenueGrowth', 0)*100:.1f}%",
                "rsi": rsi_val,
                "volume_ratio": vol_ratio,
                "chips": chips_status,
                "support": support,
                "pressure": pressure,
                "atr": atr_effective,
                "atr_state": atr_state,  # ⭐ 新增
                "volatility": round(volatility, 2),  # ⭐ 保留但分開
                "turnover_zone": round(price * 0.98, 2),
                "buy_point": buy_point
            }

            print(f"✅ {name} | ATR: {atr_effective} ({atr_state})")

        except Exception as e: 
            print(f"❌ {sym} 失敗: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
