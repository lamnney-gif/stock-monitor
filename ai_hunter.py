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

def run_advanced_analysis():
    results = {}
    for ticker, name in tickers.items():
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1mo") # 抓一個月數據算指標
            
            # --- 🟢 這裡同步你 opp.py 的核心指標 ---
            last_close = df['Close'].iloc[-1]
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            bias = ((last_close - ma20) / ma20) * 100 # 乖離率
            
            # 簡單 RSI 邏輯 (跟你 opp.py 一致)
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + gain/loss))

            # --- 🤖 把這些「專業數據」塞進 Prompt ---
            prompt = (f"你是專業交易員。分析{name}({ticker})：\n"
                      f"1. 現價：{last_close:.2f}\n"
                      f"2. 月線乖離：{bias:.1f}%\n"
                      f"3. RSI指標：{rsi:.1f}\n"
                      f"請根據以上數據，給出50字內的技術面診斷與操作建議。")
            
            res = model.generate_content(prompt)
            results[name] = {"content": res.text, "time": time.strftime("%Y-%m-%d %H:%M")}
            
            print(f"✅ {name} 分析完成")
            time.sleep(10) 
        except Exception as e:
            print(f"❌ {name} 出錯: {e}")
            
    # 🟢 最終存檔檢查
    if not results:
        print("🚨 警告：所有分析都失敗了，將不更新 JSON 檔案")
        return

    with open("ai_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("🎉 任務完成！ai_report.json 已更新")

if __name__ == "__main__":
    run()
