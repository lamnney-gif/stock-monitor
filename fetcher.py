import yfinance as yf
import json
import os
import requests
from datetime import datetime

def fetch_data():
    tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
    final_data = {"update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "stocks": {}}
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker, session=session)
            info = stock.info
            df = stock.history(period="1mo")
            
            # 計算基礎技術面
            close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]
            
            final_data["stocks"][ticker] = {
                "name": name,
                "price": round(close, 2),
                "pe": info.get('trailingPE', "---"),
                "growth": f"{round(info.get('revenueGrowth', 0)*100, 1)}%" if info.get('revenueGrowth') else "---",
                "support": round(ma20 - (1.5 * std20), 2),
                "pressure": round(ma20 + (2.0 * std20), 2)
            }
            print(f"✅ {name} 數據抓取成功")
        except Exception as e:
            print(f"❌ {ticker} 失敗: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch_data()
