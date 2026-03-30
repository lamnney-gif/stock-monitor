import json
import os
import time
from datetime import datetime, timedelta
from groq import Groq

def get_tw_time():
    return datetime.utcnow() + timedelta(hours=8)

def run_ai_report():
    # 讀取市場數據 (由 fetcher.py 產生)
    if not os.path.exists("data_raw.json"):
        print("❌ 錯誤：找不到 data_raw.json")
        return
    
    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    # 雙鑰匙清單
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    active_keys = [k for k in keys if k] # 過濾掉空值

    ai_results = {
        "last_update": get_tw_time().strftime("%Y-%m-%d %H:%M:%S"),
        "reports": {}
    }

    for ticker, data in raw.get("stocks", {}).items():
        success = False
        for i, api_key in enumerate(active_keys):
            try:
                client = Groq(api_key=api_key)
                prompt = f"分析{data.get('name', ticker)}：現價{data['price']}、RSI{data['rsi']}。給出一句話死穴與最終決斷。繁體中文。"
                
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": "資深策略家"}, {"role": "user", "content": prompt}]
                )
                
                ai_results["reports"][ticker] = chat.choices[0].message.content
                print(f"✅ {ticker} 使用 Key {i+1} 分析成功")
                success = True
                break # 成功就換下一檔股票
            except Exception as e:
                print(f"⚠️ Key {i+1} 失敗: {e}")
                continue # 嘗試下一把鑰匙

        if not success:
            ai_results["reports"][ticker] = "🤖 診斷中斷：所有 AI 密鑰均達到上限。"
        
        time.sleep(1.2)

    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(ai_results, f, ensure_ascii=False, indent=4)
    print("🧠 analyzer.py 執行完畢")

if __name__ == "__main__":
    run_ai_report()
