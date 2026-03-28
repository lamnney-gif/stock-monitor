import yfinance as yf
import google.generativeai as genai
import json, os, time

# 🟢 檢查環境變數是否讀取成功
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ 錯誤：找不到 GEMINI_API_KEY，請檢查 GitHub Secrets 設定！")
else:
    print("✅ 成功讀取 API KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# 你的追蹤清單
tickers = {"2330.TW": "台積電", "NVDA": "輝達", "2303.TW": "聯電"}

def run():
    results = {}
    for ticker, name in tickers.items():
        try:
            print(f"正在抓取 {name}({ticker}) 數據...")
            stock = yf.Ticker(ticker)
            # 🟢 確保抓到最新股價
            df = stock.history(period="5d")
            if df.empty:
                print(f"⚠️ {name} 沒抓到數據，跳過")
                continue
                
            price = df['Close'].iloc[-1]
            print(f"💰 {name} 現價: {price:.2f}，正在請求 AI 分析...")

            prompt = f"分析{name}({ticker})現價{price:.2f}。請給出50字診斷。"
            res = model.generate_content(prompt)
            
            if res.text:
                results[name] = {"content": res.text, "time": time.strftime("%Y-%m-%d %H:%M")}
                print(f"✨ {name} 分析成功！")
            
            time.sleep(10) # 避開頻率限制
        except Exception as e:
            print(f"❌ {name} 發生錯誤: {str(e)}")
            
    # 🟢 最終存檔檢查
    if not results:
        print("🚨 警告：所有分析都失敗了，將不更新 JSON 檔案")
        return

    with open("ai_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("🎉 任務完成！ai_report.json 已更新")

if __name__ == "__main__":
    run()
