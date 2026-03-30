import yfinance as yf
import json
import numpy as np
import pandas as pd
from datetime import datetime

def fetch_all():
    tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
    final_data = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "stocks": {}}
    
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            if df.empty: continue
            
            # 1. 基礎指標
            info = stock.info
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            rsi = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
            
            # 2. 進階指標 (截圖要求)
            pe_ratio = info.get('trailingPE', 0)
            rev_growth = info.get('revenueGrowth', 0) * 100 # 轉百分比
            atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
            
            # 3. 支撐壓力與回測參數 (演算法模擬)
            support = ma20 - (1.5 * std20)
            pressure = ma20 + (2.0 * std20)
            chip_floor = df['Low'].tail(60).min() # 近三個月低點作為支撐分布
            
            final_data["stocks"][ticker] = {
                "name": name,
                "price": round(close_val, 2),
                "rsi": round(rsi, 1),
                "pe": round(pe_ratio, 2) if pe_ratio else "---",
                "growth": f"{round(rev_growth, 1)}%" if rev_growth else "---",
                "atr_floor": round(close_val - (2.5 * atr), 2),
                "buy_point": round(support * 1.02, 2),
                "pressure_point": round(pressure, 2),
                "support_dist": round(chip_floor, 2),
                "defense_line": round(df['High'].tail(5).max() * 0.97, 2)
            }
            print(f"✅ {name} 數據全量抓取成功")
        except Exception as e:
            print(f"❌ {name} 失敗: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_all()
