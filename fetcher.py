import yfinance as yf
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def calculate_atr(df, period=14):
    """計算真實 ATR (Average True Range)"""
    try:
        high_low = df['High'] - df['Low']
        high_cp = np.abs(df['High'] - df['Close'].shift())
        low_cp = np.abs(df['Low'] - df['Close'].shift())
        
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return round(atr.iloc[-1], 2)
    except:
        return round(df['Close'].iloc[-1] * 0.03, 2) # 失敗則給 3% 預設波幅

def calculate_rsi(series, period=14):
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        val = 100 - (100 / (1 + rs))
        return round(val.iloc[-1], 2)
    except:
        return 50.0

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
            if df.empty or len(df) < 20: continue
            
            price = round(df['Close'].iloc[-1], 2)
            
            # 💡 核心修正：使用真正的 ATR 函數
            real_atr = calculate_atr(df, 14)
            
            # 使用 ATR 來定義支撐與壓力 (比 std 更符合真實交易)
            # 支撐設在 1.5 倍 ATR 處，壓力設在 1.5 倍 ATR 處
            support = round(price - (real_atr * 1.5), 2)
            pressure = round(price + (real_atr * 1.5), 2)
            buy_point = round(price - (real_atr * 1.0), 2)
            
            rsi_val = calculate_rsi(df['Close'], 14)
            info = tk.info if tk.info else {}
            
            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else "---",
                "growth": f"{info.get('revenueGrowth', 0)*100:.1f}%" if info.get('revenueGrowth') else "---",
                "rsi": rsi_val,
                "volume_ratio": round(df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean(), 2),
                "chips": "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整"),
                "support": support,
                "pressure": pressure,
                "atr": real_atr,
                "turnover_zone": round(price * 0.99, 2),
                "buy_point": buy_point
            }
            print(f"✅ {name} ATR 計算完成: {real_atr}")
            
        except Exception as e:
            print(f"❌ {sym} 失敗: {str(e)}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
