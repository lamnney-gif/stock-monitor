import yfinance as yf
import json
from datetime import datetime

def fetch():
    # 你的核心股清單
    tickers = {"2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"}
    data_to_save = {"stocks": {}}

    for ticker, name in tickers.items():
        try:
            s = yf.Ticker(ticker)
            df = s.history(period="1mo")
            info = s.info
            
            # 計算你要的數據
            current_price = round(df['Close'].iloc[-1], 2)
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            std20 = df['Close'].rolling(20).std().iloc[-1]

            # 存入統一格式
            data_to_save["stocks"][ticker] = {
                "name": name,
                "price": current_price,
                "pe": info.get('trailingPE', "---"),
                "growth": f"{round(info.get('revenueGrowth', 0)*100, 1)}%" if info.get('revenueGrowth') else "---",
                "rsi": 50, # 簡化計算或加入 RSI 邏輯
                "support": round(ma20 - (1.5 * std20), 2),
                "pressure": round(ma20 + (2.0 * std20), 2)
            }
            print(f"✅ {name} 抓取成功")
        except Exception as e:
            print(f"❌ {ticker} 出錯: {e}")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    fetch()
