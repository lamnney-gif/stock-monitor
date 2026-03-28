import yfinance as yf
import google.generativeai as genai
import json, os, time

# 讀取保險箱的 Key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# 你的追蹤清單
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "TSM": "台積電ADR", "2303.TW": "聯電"}

def run():
    results = {}
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            price = stock.history(period="1d")['Close'].iloc[-1]
            # 這裡可以加入你原本的 RSI 或 籌碼邏輯
            prompt = f"分析{name}({ticker})現價{price:.2f}。請給出50字診斷。"
            res = model.generate_content(prompt)
            results[name] = {"content": res.text, "time": time.strftime("%Y-%m-%d %H:%M")}
            time.sleep(10) # 避開頻率限制
        except: pass
            
    with open("ai_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run()
