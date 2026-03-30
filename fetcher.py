import yfinance as yf
import json
import os
import pandas as pd
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def calculate_rsi(series, period=14):
    """精準版 RSI 計算"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1], 2) if not pd.isna(rs.iloc[-1]) else 50.0

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
            # 抓 1 個月數據確保 RSI 與 ATR 計算精準
            df = tk.history(period="1mo")
            if df.empty: continue
            
            price = round(df['Close'].iloc[-1], 2)
            # 修正 RSI：取 14 日標準週期
            rsi_val = calculate_rsi(df['Close'], 14)
            
            # 計算 ATR (波動率) 與標準差
            std = df['Close'].rolling(20).std().iloc[-1]
            
            # 籌碼邏輯 (簡單模擬)
            chips_status = "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整")
            
            # 成交量比 (5日平均)
            vol_avg = df['Volume'].iloc[-6:-1].mean()
            vol_ratio = round(df['Volume'].iloc[-1] / vol_avg, 2) if vol_avg > 0 else 1.0

            # 補回所有消失的數據欄位
            raw_results["stocks"][sym] = {
                "name": name,
                "price": price,
                "pe": tk.info.get('trailingPE', '---'),
                "growth": f"{tk.info.get('revenueGrowth', 0)*100:.1f}%", # 補回成長率
                "rsi": rsi_val,
                "volume_ratio": vol_ratio,
                "chips": chips_status, # 補回籌碼標籤
                "support": round(price - (std * 1.5), 2),
                "pressure": round(price + (std * 1.5), 2),
                "atr": round(std, 2), # 補回 ATR
                "turnover_zone": round(price * 0.98, 2),
                "buy_point": round(price - (std * 1.2), 2) # 補回觀察買點
            }
            print(f"✅ {name} 數據修復完成")
        except Exception as e: 
            print(f"❌ {sym} 失敗: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
