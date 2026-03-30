import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def run_fetcher():
    # 這是你的監測清單
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電",
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    results = {"last_update": get_tw_time(), "stocks": {}}

    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            # 💡 抓 3 個月數據確保 Rolling 不會 NaN
            df = tk.history(period="3mo")
            if df.empty or len(df) < 20: continue

            price = round(df['Close'].iloc[-1], 2)

            # --- 🚀 重點：真正的 ATR (True Range) 計算邏輯 ---
            # TR1: 今日高低差
            tr1 = df['High'] - df['Low']
            # TR2: 今日高與昨收差
            tr2 = np.abs(df['High'] - df['Close'].shift())
            # TR3: 今日低與昨收差
            tr3 = np.abs(df['Low'] - df['Close'].shift())
            
            # 取三者最大值得到 True Range (TR)
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # 💡 這裡改用 5 日均線 (ATR5)，比 14 日更靈敏，能抓到最近的噴發或重摔
            atr_val = tr.rolling(5).mean().iloc[-1]
            
            # --- 🛡️ 風控邏輯校正 ---
            # 1. 支撐分佈：現價往下跌 2 倍 ATR (這是空頭排列下最安全的防線)
            support_val = round(price - (atr_val * 2.0), 2)
            # 2. 壓力分佈：現價往上加 1.5 倍 ATR
            pressure_val = round(price + (atr_val * 1.5), 2)
            # 3. 觀察買點：現價往下跌 1.2 倍 ATR
            buy_point = round(price - (atr_val * 1.2), 2)
            # 4. ATR 地板 (止損參考點)：現價 - 2.5 倍 ATR
            stop_loss = round(price - (atr_val * 2.5), 2)

            # RSI 計算
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi_val = round(100 - (100 / (1 + rs.iloc[-1])), 2) if not pd.isna(rs.iloc[-1]) else 50.0

            # 存入 JSON
            results["stocks"][sym] = {
                "name": name,
                "price": price,
                "rsi": rsi_val,
                "atr": round(atr_val, 2), # 這是單日真實波動
                "support": support_val,
                "pressure": pressure_val,
                "buy_point": buy_point,
                "stop": stop_loss, # 這是你 UI 上的 ATR 地板
                "vol_ratio": round(df['Volume'].iloc[-1] / df['Volume'].iloc[-6:-1].mean(), 2)
            }
            print(f"✅ {name} 計算完成 (ATR: {round(atr_val, 2)})")

        except Exception as e:
            print(f"❌ {sym} 出錯: {e}")

    # 輸出給 opp.py 讀取的 JSON
    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_fetcher()
