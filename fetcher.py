import yfinance as yf
import json
import os
from datetime import datetime, timedelta

def get_tw_time():
    return datetime.utcnow() + timedelta(hours=8)

def run_market_data():
    tickers = ["2330.TW", "NVDA", "MU", "000660.KS", "2303.TW", "6770.TW", "2344.TW", "3481.TW", "1303.TW"]
    raw_results = {"last_update": get_tw_time().strftime("%Y-%m-%d %H:%M:%S"), "stocks": {}}
    
    for symbol in tickers:
        try:
            tk = yf.Ticker(symbol)
            hist = tk.history(period="5d") # 抓5天夠算指標了
            if hist.empty: continue
            
            price = round(hist['Close'].iloc[-1], 2)
            # 簡單 RSI 邏輯
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=3).mean() # 短週期快搜
            loss = (-delta.where(delta < 0, 0)).rolling(window=3).mean()
            rsi = round(100 - (100 / (1 + (gain/loss))).iloc[-1], 2)
            
            raw_results["stocks"][symbol] = {
                "price": price, "rsi": rsi,
                "pe": tk.info.get('trailingPE', '---'),
                "volume_ratio": round(hist['Volume'].iloc[-1] / hist['Volume'].mean(), 2),
                "support": round(price * 0.95, 2), # 支撐位
                "pressure": round(price * 1.05, 2), # 壓力位
                "turnover_zone": round(price * 0.98, 2) # 密集換手
            }
        except: continue

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)
    print("✅ 行情數據更新完成")

if __name__ == "__main__":
    run_market_data()
