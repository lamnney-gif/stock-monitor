import yfinance as yf
import json
import numpy as np
import pandas as pd
import time
import random
from datetime import datetime

def fetch_all():
    tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
    final_data = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "stocks": {}}
    
    # 建立一個 Session 並偽裝瀏覽器身份
    import requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })

    for ticker, name in tickers.items():
        try:
            print(f"📡 正在抓取 {name} ({ticker})...")
            stock = yf.Ticker(ticker, session=session) # 使用偽裝過的 session
            
            # 優先抓取歷史價格 (通常比較穩定)
            df = stock.history(period="1y")
            if df.empty:
                print(f"⚠️ {name} 歷史數據為空")
                continue
            
            # 嘗試抓取 Info (本益比等)
            info = stock.info
            
            # 1. 基礎指標計算
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            rsi = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
            
            # 2. 處理 None 值 (如果 info 抓不到，給予預設值或從 df 計算)
            pe_ratio = info.get('trailingPE')
            if pe_ratio is None: pe_ratio = "---"
            
            rev_growth = info.get('revenueGrowth')
            growth_str = f"{round(rev_growth * 100, 1)}%" if rev_growth is not None else "---"
            
            atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
            
            # 3. 支撐壓力演算法
            support = ma20 - (1.5 * std20)
            pressure = ma20 + (2.0 * std20)
            chip_floor = df['Low'].tail(60).min()
            
            final_data["stocks"][ticker] = {
                "name": name,
                "price": round(close_val, 2),
                "rsi": round(rsi, 1),
                "pe": pe_ratio if pe_ratio == "---" else round(pe_ratio, 2),
                "growth": growth_str,
                "atr_floor": round(close_val - (2.5 * atr), 2),
                "buy_point": round(support * 1.02, 2),
                "pressure_point": round(pressure, 2),
                "support_dist": round(chip_floor, 2),
                "defense_line": round(df['High'].tail(5).max() * 0.97, 2)
            }
            print(f"✅ {name} 抓取成功")
            
            # 隨機休眠 3~7 秒，避免被 Yahoo 封鎖
            time.sleep(random.uniform(3, 7))
            
        except Exception as e:
            print(f"❌ {name} 發生錯誤: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_all()
