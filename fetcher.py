import yfinance as yf
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_tw_time():
    return (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")

def calculate_rsi(series, period=14):
    """防錯版 RSI 計算"""
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        val = 100 - (100 / (1 + rs))
        last_val = val.iloc[-1]
        return round(last_val, 2) if not pd.isna(last_val) else 50.0
    except:
        return 50.0

def clean_val(val, default="---"):
    """確保數值不是 NaN，否則轉為預設值"""
    if pd.isna(val) or val is None:
        return default
    return val

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
            # 💡 關鍵修正 1：改抓 3 個月 (3mo)，確保 rolling(20) 有足夠數據計算不產生 NaN
            df = tk.history(period="3mo") 
            if df.empty or len(df) < 20: 
                print(f"⚠️ {name} 數據長度不足")
                continue
            
            # 💡 關鍵修正 2：確保價格抓取最後一個非空值
            price = round(df['Close'].dropna().iloc[-1], 2)
            
            # RSI 計算
            rsi_val = calculate_rsi(df['Close'], 14)
            
            # 計算標準差 (std) 與 ATR 模擬
            # 使用 dropna 確保計算穩定
            std_series = df['Close'].rolling(20).std().dropna()
            std = std_series.iloc[-1] if not std_series.empty else (price * 0.02) # 若失敗則給預設 2% 波動
            
            # 籌碼邏輯
            chips_status = "🔥 強勢" if rsi_val > 60 else ("💀 轉弱" if rsi_val < 40 else "☁️ 盤整")
            
            # 成交量比 (5日平均)
            vol_last = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].iloc[-6:-1].mean()
            vol_ratio = round(vol_last / vol_avg, 2) if (vol_avg and vol_avg > 0) else 1.0

            # 💡 關鍵修正 3：對 info 數據進行安全抓取
            info = tk.info if tk.info else {}
            pe = info.get('trailingPE')
            growth = info.get('revenueGrowth')
            growth_str = f"{growth*100:.1f}%" if (growth is not None and not pd.isna(growth)) else "---"

            # 組合數據並進行最後的 NaN 檢查
            raw_results["stocks"][sym] = {
                "name": name,
                "price": clean_val(price),
                "pe": clean_val(round(pe, 2) if pe else None),
                "growth": growth_str,
                "rsi": clean_val(rsi_val, 50.0),
                "volume_ratio": clean_val(vol_ratio, 1.0),
                "chips": chips_status,
                "support": clean_val(round(price - (std * 1.5), 2)),
                "pressure": clean_val(round(price + (std * 1.5), 2)),
                "atr": clean_val(round(std, 2)),
                "turnover_zone": clean_val(round(price * 0.98, 2)),
                "buy_point": clean_val(round(price - (std * 1.2), 2))
            }
            print(f"✅ {name} 數據處理完成 (Price: {price})")
            
        except Exception as e: 
            print(f"❌ {sym} 執行失敗: {str(e)}")

    # 寫入檔案
    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_market()
