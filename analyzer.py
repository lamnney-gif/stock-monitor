import json
import os
import time
from groq import Groq
from datetime import datetime

def run_analysis():
    # 1. 讀取原始數據
    try:
        with open("data_raw.json", "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"❌ 讀取 data_raw.json 失敗: {e}")
        return

    # 2. 初始化 Groq (從環境變數抓 Key，GitHub Actions 會傳進來)
    api_key = os.getenv("GROQ_API_KEY_1")
    if not api_key:
        print("❌ 找不到 GROQ_API_KEY_1")
        return
    client = Groq(api_key=api_key)

    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    
    # 3. 循環分析每一檔股票
    for ticker, info in raw_data.get("stocks", {}).items():
        print(f"🧠 正在分析: {info['name']}...")
        
        prompt = f"你是投資長。標:{info['name']}, 價:{info['price']}, RSI:{info['rsi']}。100字內狠準狂分析(請用繁體中文)。"
        
        try:
            # 這裡可以稍微延遲，確保不撞 RPM
            time.sleep(10) 
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            results["reports"][ticker] = res.choices[0].message.content.strip()
            print(f"✅ {info['name']} 分析完成")
        except Exception as e:
            results["reports"][ticker] = f"分析暫時中斷: {str(e)}"
            print(f"❌ {info['name']} 失敗: {e}")

    # 4. 寫回分析結果檔
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print("🎉 所有分析已存入 analysis_results.json")

if __name__ == "__main__":
    run_analysis()
