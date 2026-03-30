import json
import os
import time
from datetime import datetime
from groq import Groq

def run_ai():
    # 讀取剛剛存好的數據
    if not os.path.exists("data_raw.json"): return
    with open("data_raw.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    # 準備雙 Key
    keys = [os.getenv("GROQ_API_KEY_1"), os.getenv("GROQ_API_KEY_2")]
    keys = [k for k in keys if k]
    
    results = {"last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "reports": {}}
    key_idx = 0

    for ticker, data in raw["stocks"].items():
        success = False
        while key_idx < len(keys) and not success:
            try:
                client = Groq(api_key=keys[key_idx])
                # 這裡就是你原本要求的資深策略家人設
                prompt = f"分析{data['name']}：現價{data['price']}、PE{data['pe']}、成長{data['growth']}。需含【一句話死穴】與【最終決斷】。繁體中文。"
                
                chat = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "你是一位洞察地緣政治與資本市場連動關係的資深策略家。"},
                        {"role": "user", "content": prompt}
                    ]
                )
                results["reports"][ticker] = chat.choices[0].message.content
                success = True
                print(f"✅ {ticker} AI 分析成功")
                time.sleep(1)
            except Exception as e:
                print(f"⚠️ Key {key_idx+1} 報錯: {e}")
                key_idx += 1

    # 強制存檔
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    run_ai()
