import yfinance as yf
import json
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
            
            close_val = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            rsi = (100 - (100 / (1 + df['Close'].diff().where(lambda x: x>0, 0).rolling(14).mean() / (df['Close'].diff().where(lambda x: x<0, 0).abs().rolling(14).mean() + 1e-9)))).iloc[-1]
            
            final_data["stocks"][ticker] = {
                "name": name,
                "price": round(close_val, 2),
                "rsi": round(rsi, 1),
                "ma20": round(ma20, 2)
            }
            print(f"✅ 抓取成功: {name}")
        except Exception as e:
            print(f"❌ 抓取失敗 {name}: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_all()