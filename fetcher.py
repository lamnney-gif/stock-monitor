import yfinance as yf
import pandas as pd
import json
import os

# 強制使用台灣時間 (UTC+8)
def get_tw_time():
    return datetime.utcnow() + timedelta(hours=8)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1], 2)

def fetch_stock_data():
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    result = {"stocks": {}}

    for symbol, name in tickers.items():
        try:
            print(f"正在抓取 {name} ({symbol})...")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo") # 抓一個月數據算 RSI
            info = ticker.info

            if hist.empty: continue

            # 1. 基礎數據
            current_price = round(hist['Close'].iloc[-1], 2)
            prev_close = hist['Close'].iloc[-2]
            
            # 2. RSI 計算 (14日)
            rsi_val = calculate_rsi(hist['Close'])

            # 3. 量比計算 (當前量 / 5日均量)
            avg_vol_5d = hist['Volume'].iloc[-6:-1].mean()
            current_vol = hist['Volume'].iloc[-1]
            vol_ratio = round(current_vol / avg_vol_5d, 2) if avg_vol_5d > 0 else 1.0

            # 4. 支撐壓力與 ATR (簡單模擬邏輯)
            std_dev = hist['Close'].rolling(20).std().iloc[-1]
            support = round(current_price - (std_dev * 1.5), 2)
            pressure = round(current_price + (std_dev * 1.5), 2)
            atr = round(std_dev, 2)

            # 5. 籌碼狀態 (模擬邏輯，實際需對接交易所 API)
            chips_status = "🔥 強勢" if rsi_val > 60 else "☁️ 盤整"
            if rsi_val < 30: chips_status = "❄️ 超跌"

            result["stocks"][symbol] = {
                "price": current_price,
                "pe": info.get('trailingPE', '---'),
                "growth": f"{info.get('revenueGrowth', 0)*100:.1f}%",
                "rsi": rsi_val,
                "volume_ratio": vol_ratio,
                "chips": chips_status,
                "support": support,
                "pressure": pressure,
                "atr": atr,
                "turnover_zone": round(current_price * 0.98, 2), # 密集換手區模擬
                "buy_point": round(support * 1.02, 2)
            }
        except Exception as e:
            print(f"{symbol} 抓取失敗: {e}")

    # 寫入 JSON
    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("✅ data_raw.json 更新完成！")

if __name__ == "__main__":
    fetch_stock_data()
