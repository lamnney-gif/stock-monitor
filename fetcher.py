import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta
from groq import Groq

# --- 核心：強制台北時間 ---
def get_taiwan_now():
    # 取得 UTC 時間並強制 +8 小時
    return datetime.utcnow() + timedelta(hours=8)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return round(100 - (100 / (1 + rs)).iloc[-1], 2)

def run_pipeline():
    tickers = {
        "2330.TW": "台積電", "NVDA": "輝達", "MU": "美光", 
        "000660.KS": "海力士", "2303.TW": "聯電", "6770.TW": "力積電", 
        "2344.TW": "華邦電", "3481.TW": "群創", "1303.TW": "南亞"
    }
    
    # 1. 抓取行情數據
    raw_data = {"stocks": {}}
    for sym, name in tickers.items():
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="1mo")
            if df.empty: continue
            
            cur_price = round(df['Close'].iloc[-1], 2)
            rsi = calculate_rsi(df['Close'])
            vol_avg = df['Volume'].iloc[-6:-1].mean()
            v_ratio = round(df['Volume'].iloc[-1] / vol_avg, 2) if vol_avg > 0 else 1.0
            std = df['Close'].rolling(20).std().iloc[-1]
            
            raw_data["stocks"][sym] = {
                "name": name, "price": cur_price, "rsi": rsi,
                "volume_ratio": v_ratio, "pe": tk.info.get('trailingPE', '---'),
                "growth": f"{tk.info.get('revenueGrowth', 0)*100:.1f}%",
                "chips": "🔥 強勢" if rsi > 60 else "☁️ 盤整",
                "support": round(cur_price - (std * 1.5), 2),
                "pressure": round(cur_price + (std * 1.5), 2),
                "atr": round(std, 2),
                "turnover_zone": round(cur_price * 0.98, 2), # 密集換手區
                "buy_point": round(cur_price - (std * 1.3), 2)
            }
            print(f"✅ {name} 數據 OK")
        except: print(f"❌ {sym} 失敗")

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=4)

    # 2. AI 診斷 (同步存入台北時間)
    tw_now = get_taiwan_now()
    ai_results = {"last_update": tw_now.strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    
    api_key = os.getenv("GROQ_API_KEY_1")
    if api_key:
        client = Groq(api_key=api_key)
        for ticker, data in raw_data["stocks"].items():
            try:
                prompt = f"分析{data['name']}：現價{data['price']}、RSI{data['rsi']}。含【一句話死穴】與【最終決斷】。繁體中文。"
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "資深策略家"}, {"role": "user", "content": prompt}]
                )
                ai_results["reports"][ticker] = res.choices[0].message.content
                time.sleep(1)
            except: pass
            
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(ai_results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_pipeline()
