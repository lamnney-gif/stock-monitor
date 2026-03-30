import json
import os
import time
from datetime import datetime
from groq import Groq

def get_ai_response(client, ticker, data):
    # 這裡就是你原本要求的人設
    prompt = f"請針對{data['name']}({ticker})現價{data['price']}、RSI{data.get('rsi','N/A')}進行深度診斷。包含【一句話死穴】與【最終決斷】。繁體中文。"
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "你是一位洞察地緣政治與資本市場連動關係的資深策略家。"},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

def run():
    # 確保抓得到 fetcher 存的檔案
    if not os.path.exists("data_raw.json"):
        print("❌ 錯誤：找不到 data_raw.json")
        return

    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    # 讀取環境變數
    k1 = os.getenv("GROQ_API_KEY_1")
    k2 = os.getenv("GROQ_API_KEY_2")
    keys = [k for k in [k1, k2] if k]
    
    if not keys:
        print("❌ 錯誤：Python 完全沒抓到 API Key，請檢查 main.yml 的 env 設定")
        return

    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    
    key_idx = 0
    for ticker, data in raw_data.get("stocks", {}).items():
        success = False
        while key_idx < len(keys) and not success:
            try:
                client = Groq(api_key=keys[key_idx])
                results[ticker] = get_ai_response(client, ticker, data) # 修正這裡的存值邏輯
                results["reports"][ticker] = results[ticker] 
                success = True
                print(f"✅ {ticker} 分析成功 (使用 Key {key_idx+1})")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ {ticker} 失敗 (Key {key_idx+1}): {e}")
                key_idx += 1

    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run()
